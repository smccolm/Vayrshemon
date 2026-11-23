"""Build the dictionary ledger and the index of attested word spellings."""
from collections import Counter, defaultdict
from hashlib import sha256
from itertools import groupby
from functools import lru_cache
import re

from tools.dictionary_corpus import ALPHABET, ROOT, WORK, TOKENIZATION, connect, normalize, read, written
from tools.dictionary_definitions import Definer, part_of_speech
from tools.dictionary_lexicon import load_gzip, numeric, save_gzip
from tools.dictionary_manuscripts import ManuscriptReadings
from tools.dictionary_place_words import chart_reading, index_place_words, place_words
from tools.dictionary_scope import citation_exclusions, word_readings, word_senses
from tools.dictionary_usages import sense_divisions

CHART=read(ROOT/'data/orthography/chart-transcription.json')['letters']
ORDER={chr(row[2]):row[0]+20 for row in CHART}
ORDER.update({ch:i for i,ch in enumerate('0123456789ÀÁ')})
ORDER[' ']=-1  # File a phrase with its first word before longer words sharing that prefix.
# Some manuscript names mix native font slots with literal Roman letters.
# Map only literal characters outside the native alphabet; a slot such as
# Ñ already denotes one Thimfora letter. Preserve the original printed form.
LITERAL_SLOTS={r[5]:chr(r[2]) for r in CHART if r[5] and len(r[5])==1 and r[5] not in ALPHABET}
LITERAL_SLOTS.update({'č':'Ñ','š':'Û','ŧ':'Õ','ñ':'n','í':'i','ï':'i','ó':'o'})
FILING_SLOTS=str.maketrans({**LITERAL_SLOTS,'’':None,'-':None,',':None})


def filing_initial(form):
    return normalize(form).translate(FILING_SLOTS)[0]


def collate(form):
    spelling=normalize(form)
    letters=spelling.translate(FILING_SLOTS)
    # Compare every letter first. Only otherwise identical sequences reach
    # the spelling tie-break, keeping distinct manuscript spellings together.
    return tuple(ORDER[ch] for ch in letters),letters!=spelling,spelling


def pointer(ref):
    return sha256(ref.encode()).hexdigest()[:18]


@lru_cache(maxsize=1)
def native_letter_names():
    pieces={k.casefold():chr(slot) for _,_,slot,_,_,k in CHART if k}
    by_length=sorted(pieces,key=len,reverse=True)
    names={}
    for _,_,slot,name,*_ in CHART:
        rem=name
        native=''
        while rem:
            q=next(k for k in by_length if rem.startswith(k))
            native+=pieces[q];rem=rem[len(q):]
        names[chr(slot)]=(name,native)
    return names


def citation(s,context):
    ref=str(context['reference'])
    book=context['book'].split(' - Four-Column')[0]
    if re.fullmatch(r'\d+[a-z]?',ref):
        return f'{book}, passage {ref}'
    if book=='King James Bible' or ref.startswith(book):
        return ref
    ref=ref.replace(' · ', ', ')
    return book+', '+ref


def usage_excerpt(s,context):
    """Quote only a contiguous, matched native/gloss segment around the actual word."""
    parts=context['text'].split()
    gloss=context['gloss'].split(' · ')
    if len(parts)!=len(gloss):return None
    stem=normalize(s['form'])
    pos=next((i for i,x in enumerate(parts) if stem in normalize(x)),None)
    if pos is None:return None
    lo=max(0,pos-3);hi=min(len(parts),pos+4)
    return ' '.join(parts[lo:hi]),' · '.join(gloss[lo:hi])


def build_rows(draft=False,output=None):
    c=load_gzip(WORK/'attestations.json.gz')
    raw=load_gzip(WORK/'manuscript-readings.json.gz')
    lexical=word_senses(c)
    d=Definer(c)
    places=place_words(c,lexical)
    entries=dict(lexical)
    for identity,word in places.items():
        if identity not in entries:
            witness=c['senses'].get(identity,{})
            entries[identity]=dict(form=word.form,reading=chart_reading(word.form,d.lang),pos='numeral',
                                   label=word.label,contemporary=witness.get('contemporary',0),
                                   citations=witness.get('citations',[]))
    from tools.dictionary_articles import Articles
    editor=Articles(c,d)
    from tools.dictionary_sense_revision import Revision
    revision=Revision(editor)
    manuscript=ManuscriptReadings(c,d)
    extensions=sense_divisions(c,d)
    printed_labels={}
    for s in c['senses'].values():
        key=s['key']
        if key.startswith(('kjv_','drama_native_','unta_')):
            name=key.replace('_','-')
            if name in printed_labels:continue
            if q:=numeric(key):
                label=q['label']
            else:
                label=s['label'].split('{')[0].strip()
                if label==name:
                    label=key.removeprefix('kjv_').removeprefix('drama_native_').replace('_','-')
            if label!=name:printed_labels[name]=label
    internal=re.compile(r'\b(?:kjv|drama-native|unta)-[a-z0-9]+(?:-[a-z0-9]+)*')
    printed_labels.update({
        'kjv-back-body':'back of the body','kjv-scorpion-sign':'sign of the Scorpion',
        'kjv-ashtaroth-deities-general':'Ashtaroth deities','kjv-domestic-hall-door':'house-hall-door',
        'kjv-michael-revelation-sword':'Michael’s sword','kjv-moloch-amos-furious':'Moloch-furious'})
    def readable(value):
        return internal.sub(lambda m:printed_labels.get(m[0],m[0]),value)
    metrics=Counter()
    rows=[]
    def row(uid,section,label,native,gloss,english):
        if not all((uid,section,label,native,gloss,english)):raise ValueError(uid)
        rows.append(dict(id=uid,section=section,reference=label,text=native,gloss=readable(gloss),source=readable(english)))
    for key,analysis,en in [
        ('title','book of word:pl and meaning:pl','Vayrshemon Dictionary'),
        ('definitions','word:pl in order. meaning:pl and example:pl.','Headwords follow the traditional letter order. Read across the spread for native definitions, transliteration, construction glosses and English readings.'),
        ('forms','written:m form:pl. to word:pl return:inf.','Look up an inflection or a word with clitics by its own spelling in the final section. Read across for its headword. The letter directory gives native page ranges. The concordance records individual manuscript pages.')
    ]:
        n,g=d.phrase(analysis)
        row('intro-'+key,'opening','Dictionary',d.lang.maxima(n),g,en)
    ordered=sorted(entries.items(),key=lambda pair:(collate(pair[1]['form']),not pair[1]['contemporary'],pair[1]['pos']=='proper',pair[1]['label'],pair[0]))
    headwords=0
    for form,gg in groupby(ordered,key=lambda pair:normalize(pair[1]['form'])):
        senses=list(gg);headwords+=1
        total=len(senses)+sum(len(extensions.get(identity,[])) for identity,_ in senses)
        seq=0
        for identity,s in senses:
            approved=editor.approved.get(identity)
            if approved and identity!=approved['readings'][0]:continue
            seq+=1
            ctx=c['contexts'][s['citations'][0]] if s['citations'] else None
            place=places.get(identity)
            if identity in lexical:
                n,g,e,method=d.define(s,ctx)
                if place:e=e.rstrip('.')+'. '+place.description()
            else:
                n,g=place.definition(d)
                e,method=place.description(),'Unta place word'
            if not n and not draft:raise ValueError('Native paraphrase required: '+identity)
            if not n:n,g=d.phrase('example');e+=' [Definition in preparation.]'
            metrics[method]+=1
            if approved:
                n,g,e,ex=editor.approved_item(approved)
            else:
                n,g=editor.definition(s,ctx,n,g,method)
                ex=editor.example(identity,s,ctx,place)
            ex,nd,gd=revision.select({'untaPlaces':True} if place else {},s,ctx,ex,identity,total>1)
            if nd:n,g=nd,gd
            if s.get('key') in revision.definitions:
                n,g,e=revision.authored(*revision.definitions[s['key']],s,ctx,definition=True)
            citation_label=citation(s,ctx) if ctx else ''
            if place:
                if place.variants:
                    e+=' Also written '+', '.join(d.lang.reading(v) for v in place.variants)+'.'
                constructed=place.places[0][1]==2 and place.places[0][0]>1
                source='Formed on the Unta chart’s coefficient + nōrum pattern' if constructed else 'Unta chart'
                citation_label=(citation_label+'. ' if citation_label else '')+source
            num=f'{seq}. ' if total>1 else ''
            head=s['form']
            if s['pos']=='proper':head=d.lang.maxima(head)
            label=s['label'].split('{')[0]
            reading=s['reading']
            en=e.rstrip(' .')
            # Long inherited editorial comments stay in the attestation record.
            if len(en)>440:
                first=re.split(r'(?<=[.?!])\s+',en)
                en=first[0] if len(first[0])<440 else en
            pos=part_of_speech(s['pos'])
            reg='Earlier witness. ' if not s['contemporary'] and not place else ''
            row('sense-'+pointer(identity),'headwords-'+filing_initial(form),reading,
                head+'. '+n.rstrip('.')+'.',
                label+'. '+g.rstrip('.')+'.',
                num+reg+(pos.capitalize()+'. ' if pos and pos!='proper' else '')+en+'. '+citation_label+'.')
            supporting=[citation_label]
            if approved:
                for rid in approved['readings']:
                    supporting.extend(citation(s,c['contexts'][ck]) for ck in c['senses'][rid]['citations'])
            editor.add(rows[-1],n,g,reg+(pos.capitalize()+'. ' if pos and pos!='proper' else '')+en,ex,
                       supporting,approved['readings'] if approved else [identity])
            if place:
                rows[-1].update(untaPlaces=place.places,partOfSpeech='numeral',
                                evidenceStatus='draft' if constructed and not ctx else 'attested')
            for sub,subgl,reading_en,ref in extensions.get(identity,[]):
                seq+=1
                row('usage-'+pointer(identity+'|'+ref),'headwords-'+filing_initial(form),reading,
                    head+'. '+sub.rstrip('.')+'.',label+'. '+subgl.rstrip('.')+'.',
                    f'{seq}. '+reading_en+' '+ref+'.')
                editor.subject(s)
                syntax,english=editor.sub[s['key'],reading_en]
                example=editor.compile(syntax,english)
                editor.add(rows[-1],sub,subgl,reading_en,example,[ref])
    # An individual word of a longer expression may occur in hundreds of
    # compound entries. Prefer independent word analyses at that spelling.
    with connect() as db:
        spellings={r[0] for r in db.execute('SELECT DISTINCT form FROM written')}
        manuscripts,pages,tokens=db.execute('SELECT count(*),sum(pages),sum(tokens) FROM manuscripts').fetchone()
    finder=[]
    supplemental=[]
    for f in spellings:
        analyses,v=word_readings(f,c,raw,lexical)
        if analyses:
            ranked=sorted(analyses,key=lambda r:(bool(r[2]),r[2],r[3]),reverse=True)
            # Each token of a multiword expression inherits ALL of its keys in
            # the source ledger. E.g. the word for king also occurs inside a
            # compound meaning princely favour. Favour is not a reading of king.
            single=[a for a in ranked if len(a[1])==1 and ' ' not in c['senses'][a[1][0]]['form']]
            choices=single or ranked[:1]
            gloss=choices[0][0]
            heads={}
            for _,ids,*_ in choices:
                for ident in ids:
                    if ident not in lexical:continue
                    host=lexical[ident]
                    heads.setdefault(normalize(host['form']),(host['reading'],host['label'].split('{')[0]))
            label=' / '.join(v[0]+' — '+v[1] for v in heads.values())
            if not single:
                if any(i not in lexical for i in choices[0][1]):
                    label=gloss+' — see '+label
                else:
                    label=('Components of '+gloss+': ' if len(choices[0][1])>1 else 'In the expression ')+label
            elif len(heads)>1:
                one_per_head={}
                for g,ids,*_ in choices:
                    one_per_head.setdefault(normalize(c['senses'][ids[0]]['form']),g)
                gloss=' / '.join(one_per_head.values())
            finder.append((f,gloss,label))
        elif v is not None:
            if v.get('analyses') and f not in manuscript.notes:
                host=c['senses'][v['analyses'][0][0]]
                finder.append((f,v['gloss'],host['reading']+' — '+host['label'].split('{')[0]))
            else:
                item=manuscript.read(f,v)
                if not item:raise ValueError('Unexplained written form: '+f)
                n,g,e=item
                label=manuscript.notes[f][0] if f in manuscript.notes else v.get('gloss',str(v.get('value','')))
                rr=d.lang.reading(f)
                cite=''
                if v.get('manuscript'):
                    source=v['manuscript'].rsplit('/',1)[-1].removesuffix('.vay')
                    cite=f" {source}, p. {v['page']}."
                supplemental.append((f,rr,n,g,label,e,cite.strip(' .')))
                finder.append((f,label,rr+' — '+label))
    for f,reading,n,g,label,e,cite in sorted(supplemental,key=lambda a:collate(a[0])):
        row('written-'+pointer(f),'headwords-'+filing_initial(f),reading,
            f+'. '+n.rstrip('.')+'.',label+'. '+g.rstrip('.')+'.',e)
        editor.add(rows[-1],n,g,e,editor.manuscript(f,label),[cite])
    entries_end=[r for r in rows if 'article' in r]
    entries_end.sort(key=lambda r:collate(r['text'].partition('. ')[0]))
    from tools.dictionary_sense_revision import consolidate
    entries_end=consolidate(entries_end,c)
    for r in entries_end:
        r['gloss']=readable(r['gloss'])
    rows=[r for r in rows if 'article' not in r]+entries_end
    for _,grp in groupby(entries_end,key=lambda r:normalize(r['text'].partition('. ')[0])):
        group=list(grp)
        if len(group)>1:
            for no,r in enumerate(group,1):r['source']=f'{no}. '+r['source']
    finder=sorted(index_place_words(finder,places,d.lang),key=lambda item:collate(item[0]))
    for (letter,label),group in groupby(finder,key=lambda x:(filing_initial(x[0]),x[2])):
        spellings_for_label=list(group)
        for start in range(0,len(spellings_for_label),5):
            part=spellings_for_label[start:start+5]
            spell,gloss,_=zip(*part)
            row('forms-'+pointer('|'.join(spell)),'forms-'+letter,chart_reading(spell[0],d.lang),
                ', '.join(spell),', '.join(gloss),label+'.')
    omitted=spellings-{f for f,_,_ in finder}
    citation_ids,citation_forms=citation_exclusions(c,raw,omitted)
    from tools.dictionary_scope import nonword_exclusions
    rejected,excluded_forms=nonword_exclusions(c,raw,omitted)
    counts=dict(editorialChecks=dict(revision.audit),headwords=len({normalize(r['text'].partition('. ')[0]) for r in entries_end}),
                examples=len(entries_end),exampleMethods=dict(Counter(r['article']['exampleMethod'] for r in entries_end)),
                excludedNonwordReadings=sorted(rejected),excludedNonwordSpellings=sorted(excluded_forms),attestedReadings=len(c['senses'].keys() & entries.keys()),writtenForms=len(finder),
                placeWords=len(places),placeCombinations=sum(len(p.places) for p in places.values()),
                corpusWrittenForms=len(spellings),excludedNumericalSpellings=len(omitted-citation_forms-excluded_forms),
                excludedNumericalReadings=len(c['senses'].keys()-entries.keys()-citation_ids-rejected),
                excludedCitationReadings=sorted(citation_ids),excludedCitationSpellings=sorted(citation_forms),
                wordBoundaryConvention=TOKENIZATION,
                manuscripts=manuscripts,witnessPages=pages,witnessTokens=tokens,
                manuscriptReadings=len(supplemental),additionalCitedSenses=sum(len(extensions[i]) for i in lexical if i in extensions),
                definitionMethods=dict(metrics),currentLedgerPassages=sum(s['units'] for s in c['catalog'] if s.get('current')))
    ids=[r['id'] for r in rows]
    if len(set(ids))!=len(ids):raise ValueError('Dictionary entry IDs collided')
    from tools.dictionary_reference_books import BATCH, apply_batch
    ledger=dict(counts=counts,rows=rows)
    if BATCH.exists():
        ledger=apply_batch(ledger,load_gzip(BATCH))
        counts=ledger['counts']
    save_gzip(output or WORK/'dictionary-rows.json.gz',ledger)
    print(counts,flush=True)
    return counts


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--draft',action='store_true')
    build_rows(parser.parse_args().draft)
