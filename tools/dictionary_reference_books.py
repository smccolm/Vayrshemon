"""Periodically incorporate the vocabulary of the three native reference works."""
from collections import Counter, defaultdict
from itertools import groupby
import re

from tools.compose_historical_book import texts
from tools.dictionary_corpus import ROOT, WORK, normalize, page_stream, read, sha, written
from tools.dictionary_lexicon import language_set, load_gzip, save_gzip
from tools.dictionary_rows import CHART, collate, filing_initial, native_letter_names, pointer

BATCH = WORK / 'reference-book-entries.json.gz'
STAGE = ROOT / '.local/dictionary-reference-update'
BOOKS = ('Vayrshemon Idiom Inventory', 'Comprehensive Vayrshemon Grammar', 'Vayrshemon Thesaurus')


def complete(text):
    text = text.strip()
    return text if text.endswith(('.', '!', '?')) else text + '.'


class Witness:
    def __init__(self, title):
        self.title = title
        folder = ROOT / 'Saves' / (title + ' - Four-Column Progressive Edition')
        self.working = folder / 'Working'
        self.file, = folder.glob('*.vay')
        self.pages = {}
        pages = iter(page_stream(self.file))
        for i, (left, right) in enumerate(zip(pages, pages, strict=True)):
            cols = [texts(f) for p in (left, right) for f in sorted(p['frames'], key=lambda f: int(f['x']))]
            assert cols[0] == cols[1]
            self.pages[2*i+1] = list(zip(cols[0], cols[2], cols[3], strict=True))

    def cite(self, *folios):
        a, b = min(folios), max(folios)+1
        return f'{self.title}, pp. {a}–{b}'


def harvest(*, persist=True):
    lang, bible = language_set()
    for k,v in bible.lexicon.items():
        if k not in lang.lexicon:
            lang.lexicon[k] = v
            lang.glosses[k] = bible.glosses.get(k, k)
    rows, forms, witnesses = [], defaultdict(dict), {}
    idiom, grammar, thes = (Witness(t) for t in BOOKS)
    for w in (idiom,grammar,thes):
        witnesses[w.title] = dict(path=w.file.relative_to(ROOT).as_posix(),sha256=sha(w.file), pages=2*len(w.pages))

    def add(key, head, reading, pos, label, meaning, definition, definition_gloss, example, gloss, english, ref, method, **meta):
        identity = key+'@'+normalize(head)
        article = dict(definition=complete(definition),example=example,exampleMethod=method,exampleEnglish=english,
                       readingIds=[identity],references=[ref], **meta)
        rows.append(dict(id='sense-'+pointer(identity),section='headwords-'+filing_initial(head),reference=reading,
                         text=head+'. '+article['definition']+' '+example,gloss=label+'. '+complete(definition_gloss)+' '+gloss,
                         source=complete(label+' — '+meaning)+' Example: '+complete(english)+' '+ref+'.',
                         partOfSpeech=pos,article=article))
        if len(written(head)) == 1:
            stem=normalize(head)
            # Only forms tied to this lemma by its occurrence in its own example.
            for form in {stem, *(normalize(t) for t in written(example) if normalize(t).startswith(stem))}:
                forms[form][stem] = (reading,label)

    for e in read(idiom.working/'entries.json'):
        h,d,ex,p=e['native'],e['definition'],e['examples'][0],e['leftPage']
        definition_row=next(r for r in idiom.pages[p] if r[0]==h+': '+d['native'])
        assert d['english'] in definition_row[2]
        ep,r=next((page,r) for page in (p,p+2) for r in idiom.pages.get(page,[]) if r[0]==ex['native'] and r[2]==ex['english'])
        key='ultimate_grief' if e['transliteration']=='stēv' else 'inventory_'+e['id']
        add(key,h,e['transliteration'],'idiom',e['label'],d['english'],d['native'],d['gloss'],ex['native'],r[1],ex['english'],
            idiom.cite(p,ep),'published idiom example',referenceId=e['id'],sourceExamplePage=ep)
        if e.get('witness'):
            ref=e['witness']['reference']
            rows[-1]['source']+=' '+ref+'.'
            rows[-1]['article']['references'].append(ref)
    register=read(thes.working/'sense-register.json')
    additions=read(thes.working/'dictionary-additions.json')['entries']
    for key,e in additions.items():
        s=register[key];p=s['leftPage']
        n,g,en=next(r for r in thes.pages[p] if r[0].startswith(e['form']+': ') and r[0].endswith(s['example']))
        assert en.endswith(s['exampleEnglish']) and g.endswith(s['exampleGloss'])
        add(key,e['form'],e['roman'],e['pos'],e['label'],e['meaning'],n.partition(': ')[2].removesuffix(s['example']).strip(),
            g.partition(': ')[2].removesuffix(s['exampleGloss']).strip(),s['example'],s['exampleGloss'],s['exampleEnglish'],
            thes.cite(p),'published thesaurus example',relatedKey=e['nearKey'],referenceId=key)

    for key, glosskey, label, meaning, analysis in [
        ('delay','delay_external','Delay by hindrance','To cause something to happen later through an obstacle or adverse conditions. The person delayed need have made no decision to wait','by thing which hinder:pr time of arrive:ev late:m make:inf'),
        ('repay','repay_loan','Repay a loan','To return what was advanced, discharging an obligation to the lender in money or in kind','what borrow:psv:pa to person who lend:pa return:inf')]:
        s=register[key];p=s['leftPage']
        n,g,en=next(r for r in thes.pages[p] if r[0].endswith(s['example']) and r[2].endswith(s['exampleEnglish']))
        exg=g.split('. ',1)[1];d=lang.compile(analysis,initial=False)
        add(glosskey,s['form'],s['transliteration'],'verb',label,meaning,d['text'],d['gloss'],s['example'],exg,s['exampleEnglish'],
            thes.cite(p),'published thesaurus example',referenceId=key)
    additions=read(grammar.working/'dictionary-additions.json')['entries']
    notes=(WORK/'reference-grammar-readings.txt').read_text(encoding='utf-8-sig').splitlines()
    assert {x.split(' | ')[0] for x in notes}==set(additions)|{'borrowing'}
    for ln in notes:
        key,term,definition,sentence,english=ln.split(' | ')
        e=additions.get(key) or dict(form=lang.lexicon[key]['form'],label='Textual borrowing',pos='noun',
                                     meaning='Taking recognizable wording from another speaker, work or language. Resemblance alone does not establish the direction of borrowing')
        h=e['form']; root=normalize(h)
        candidates=[(page,n,en) for page,rows_ in grammar.pages.items() for n,g,en in rows_
                    if root in normalize(n) and page>=23]
        if key=='borrowing': candidates=[x for x in candidates if x[0]==347 and 'dependence' in x[2].lower()]
        preferred=[x for x in candidates if e['label'].lower() in x[2].lower() and not x[2].startswith('See ')]
        p,n,en=(preferred or candidates)[0]
        d=lang.compile(definition,initial=False);ex=lang.compile(sentence)
        add(key,h,lang.reading(h),e['pos'],e['label'],e['meaning'],d['text'],d['gloss'],ex['text'],ex['gloss'],english,
            grammar.cite(p),'composed grammar example',referenceId=key,witnessNative=n,witnessEnglish=en)

    chart_entries=(WORK/'reference-letter-examples.txt').read_text(encoding='utf-8').splitlines()
    names=native_letter_names()
    root_definition=lang.compile('name of chart_letter with two written:m form:pl',initial=False)
    for chart,example_line in zip(CHART,chart_entries,strict=True):
        index,upper,lower,name,*_=chart
        number,sample_key,syntax,english=example_line.split(' | ')
        assert int(number)==index
        pair=chr(upper)+' '+chr(lower)
        page,gloss=next((p,g) for p,items in grammar.pages.items() for n,g,en in items
                        if n==pair and g==name+' (Maxima, Minima)')
        roman,head=names[chr(lower)]
        lang.lexicon['lettername']=dict(form=head,pos='noun',meaning=name)
        lang.glosses['lettername']=name
        lang.lexicon['lettername_t']=dict(form=names['t'][1],pos='noun',meaning=names['t'][0])
        lang.glosses['lettername_t']=names['t'][0]
        if sample_key!='-':
            specimen=lang.lexicon[sample_key]['form']
            assert chr(lower) in normalize(specimen),(sample_key,lower)
            lang.lexicon['spec']=dict(form=specimen,pos='noun',meaning=sample_key)
            lang.glosses['spec']=lang.reading(specimen)
        ex=lang.compile(syntax)
        english=english.format(name=name,Name=name[:1].upper()+name[1:],word=lang.reading(specimen) if sample_key!='-' else '')
        add('thimfora_letter_'+str(index),head,roman,'noun','Letter name '+name,
            f'Name of Thimfora letter {index} in chart order, in both its maxima and minima forms',
            root_definition['text']+' '+pair,root_definition['gloss']+' · '+gloss,
            ex['text'],ex['gloss'],english,grammar.cite(page),'composed spelling example',
            referenceId='chart-letter-'+str(index),chartPair=pair)

    matches={}
    for k,v in register.items():
        if not v['dictionaryRows']:continue
        page=v['leftPage']
        assert any(n.endswith(v['example']) and english.endswith(v['exampleEnglish'])
                   for n,gloss,english in thes.pages[page]), k
        matches[k]=dict(ids=v['dictionaryRows'],example=v['example'],page=page)
    batch=dict(books=witnesses,entries=rows,forms=forms,existingThesaurusReadings=matches)
    if persist:
        save_gzip(BATCH,batch)
    return batch


def apply_batch(ledger,batch):
    """Merge on stable IDs; each sense belongs to exactly one alphabetical entry."""
    from tools.dictionary_place_words import chart_reading
    lang,_=language_set()
    original=ledger['rows']; counts=dict(ledger['counts'])
    all_rows={r['id']:r for r in original if 'article' in r}
    for term,match in batch['existingThesaurusReadings'].items():
        if not set(match['ids'])<=all_rows.keys():raise ValueError(('Unresolved thesaurus reading',term))
    for row in batch['entries']:
        all_rows[row['id']]=row.copy()
    ordered=sorted(all_rows.values(),key=lambda r:collate(r['text'].partition('. ')[0]))
    for _,group in groupby(ordered,key=lambda r:normalize(r['text'].partition('. ')[0])):
        siblings=list(group)
        for i,r in enumerate(siblings,1):
            r['source']=(f'{i}. ' if len(siblings)>1 else '')+re.sub(r'^\d+\. ','',r['source'])
    incoming=dict(batch['forms']); formsrows=[]
    existing_targets={}
    for r in original:
        if not r['section'].startswith('forms-'):continue
        for f in r['text'].split(', '):
            if f in incoming:existing_targets[f]=incoming.pop(f)
        formsrows.append(r)
    # Retain grouped rows where possible. An indexed new spelling may file
    # between two forms in an existing group.
    from bisect import bisect_right
    new_keys=sorted(collate(f) for f in incoming)
    result=[]
    for r in formsrows:
        forms=r['text'].split(', ')
        if any(f in existing_targets for f in forms) or (len(forms)>1 and
                bisect_right(new_keys,collate(forms[0]))!=bisect_right(new_keys,collate(forms[-1]))):
            glosses=r['gloss'].split(', ')
            if len(glosses)!=len(forms):raise ValueError(('Ambiguous form group',r))
            for f,g in zip(forms,glosses):
                extra=existing_targets.get(f,{})
                labels=[gl for roman,gl in extra.values() if gl not in g.split(' / ')]
                links=[roman+' — '+gl for roman,gl in extra.values() if roman+' — '+gl not in r['source']]
                result.append(dict(r,id='forms-'+pointer(f),text=f,gloss=' / '.join([g,*labels]),
                                   source=' / '.join([r['source'].rstrip('.'),*links])+'.',reference=chart_reading(f,lang)))
        else:result.append(r)
    for f,targets in incoming.items():
        v=list(targets.values());label=' / '.join(roman+' — '+gl for roman,gl in v)
        result.append(dict(id='forms-'+pointer(f),section='forms-'+filing_initial(f),reference=chart_reading(f,lang),
                           text=f,gloss=' / '.join(gl for roman,gl in v),source=label+'.'))
    result.sort(key=lambda r:collate(r['text'].split(', ')[0]))
    rows=[r for r in original if r['section']=='opening']+ordered+result
    assert len({r['id'] for r in rows})==len(rows)
    counts.update(headwords=len({normalize(r['text'].partition('. ')[0]) for r in ordered}),examples=len(ordered),
                  writtenForms=sum(len(r['text'].split(', ')) for r in result),
                  exampleMethods=dict(Counter(r['article']['exampleMethod'] for r in ordered)),
                  referenceBooks=batch['books'],referenceBookSenses=len(batch['entries']))
    return dict(counts=counts,rows=rows)


if __name__=='__main__':
    batch=harvest()
    print(f"Prepared {len(batch['entries'])} reference-book senses from {len(batch['books'])} publications.")

