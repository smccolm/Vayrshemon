"""Compile, collate, paginate and proof the four-column reference grammar."""
from collections import Counter
from fractions import Fraction
from functools import lru_cache
from itertools import groupby, islice
import hashlib
import json
import re
import sys

from tools.compose_historical_book import texts
from tools.dictionary_corpus import ROOT, page_stream, sha
from tools.dictionary_layout import FIELDS
from tools.dictionary_lexicon import language_set
from tools.editorial_language import TOKEN, WORD
from tools.unta_language import quantity
from tools.vayrshemon_idioms import InventoryLayout, subject_guide, manuscript as idiom_manuscript
from tools.vayrshemon_thesaurus import COLUMNS, row
from vayrshemon import pages, reading
from vayrshemon.file_api import FileSession
from vayrshemon.json_stream import write_atomic

NAME = 'Comprehensive Vayrshemon Grammar'
TITLE = NAME + ' - Four-Column Progressive Edition'
FOLDER = ROOT / 'Saves' / TITLE
WORK = FOLDER / 'Working'
STAGE = ROOT / '.local/grammar-first'
BOOKS = dict(prince='The Prince', locke='Two Treatises of Government', hobbes='Leviathan',
             milton='Paradise Lost', boyle='The Sceptical Chymist', dampier='A New Voyage Round the World')
IDIOMS = ROOT / 'Saves/Vayrshemon Idiom Inventory - Four-Column Progressive Edition/Working'
LETTER_FILE = ROOT / 'data/orthography/chart-transcription.json'
SOURCES = {k: ROOT/'Saves'/(name+' - Four-Column Progressive Edition')/'Working/ledger.json'
           for k,name in BOOKS.items()}
SOURCES.update(bible=ROOT/'data/language/archaic-kjv-285/flow-cases.json',
               hamlet=ROOT/'Saves/Archive/Shakespeare Project 0.13/Ledgers/hamlet.json',
               drama=ROOT/'data/language/later-dramatic-0.13/flow-cases.json')
SOURCE_NAMES = dict(BOOKS, bible='Historical KJV', hamlet='Hamlet', drama="All’s Well That Ends Well")
for key, filename, label in [('sonnets','shakespeares-sonnets','Shakespeare’s Sonnets'),
                             ('macbeth','macbeth','Macbeth'),
                             ('phoenix','the-phoenix-and-turtle','The Phoenix and Turtle')]:
    SOURCES[key] = SOURCES['hamlet'].with_name(filename+'.json')
    SOURCE_NAMES[key] = label
SOURCES['kjv'] = ROOT/'Saves/KJV Bible v0.10-kjv.285/complete-translation-ledger.json'
SOURCE_NAMES['kjv'] = 'KJV'
SPECIALIST = ('scientific-register','mathematical-register','craft-register',
              'cryptic-register','astronomical-register','biological-register')
SUPPLEMENTS = ('poetics','sacred-and-oral','prosody','prose','histories','contact',*SPECIALIST)
LANG_DATA = ROOT/'data/language'


class GrammarLayout(InventoryLayout):
    def measured(self,group):
        count,state,error=super().measured(group)
        last=group[count-1]
        if last.get('verseLine',0) < last.get('verseLength',0):
            start=count-last['verseLine']
            if start>0:
                return super().measured(group[:start])
        return count,state,error


def collate_literary_witnesses(lines):
    # A single streaming read per book also works for the 22,130-page KJV.
    names = dict(hamlet='Hamlet',macbeth='Macbeth',sonnets='Sonnets',phoenix='The Phoenix and Turtle')
    folders={book:ROOT/'Saves/Archive'/(title+' v0.14') for book,title in names.items()}
    folders['kjv']=SOURCES['kjv'].parent
    references={}
    for book,folder in folders.items():
        keys={line.split(' | ')[2] for line in lines if line.startswith(f'W | {book} | ')}
        spreads=json.loads((folder/'page-index.json').read_bytes())['spreads']
        wanted={}
        for spread in spreads:
            for idx,key in enumerate(spread['unitIds']):
                if key in keys:
                    references[book,key]=spread['leftPage']
                    wanted.setdefault(spread['leftPage'],[]).append((idx,key))
        if keys!={key for source,key in references if source==book}:
            raise ValueError('Missing literary citations for '+book)
        if not wanted: continue
        bookfile=next(folder.glob('*.vay'))
        for number,page in enumerate(islice(page_stream(bookfile),max(wanted)+1),1):
            left=number if number%2 else number-1
            if left not in wanted: continue
            fields=('Vayrshemon','Transliteration 7') if number==left else ('Construction gloss','KJV source' if book=='kjv' else 'Shakespeare source')
            lookup={frame['name']:frame for frame in page['frames']}
            for column,field in zip(fields,('text','text') if number==left else ('gloss','source'),strict=True):
                actual=texts(lookup[column])
                for idx,key in wanted[left]:
                    if actual[idx]!=units(book)[key][field]:
                        raise ValueError(f'{book} {key} differs on published page {number} in {field}')
    return references


@lru_cache(maxsize=None)
def edition_lexicon(edition):
    return json.loads((LANG_DATA/edition/'lexicon.json').read_bytes())['entries']


@lru_cache(maxsize=None)
def lexical_citations(book):
    from collections import defaultdict
    index = defaultdict(list)
    for unit in units(book).values():
        keys = {key for token in TOKEN.findall(unit['analysis']) if WORD.fullmatch(token)
                for part in token.rstrip(':').split('/') for key in part.split(':')[0].split('+')}
        for key in keys:
            index[key].append(unit['id'])
    return index


@lru_cache(maxsize=None)
def book_spread_index(book):
    spreads = json.loads(SOURCES[book].with_name('page-index.json').read_bytes())['spreads']
    return {key:s for s in spreads for key in s['unitIds']}


@lru_cache(maxsize=None)
def units(key):
    doc = json.loads(SOURCES[key].read_bytes())
    return {u['id']:u for u in (doc if isinstance(doc,list) else doc['units'])}


@lru_cache(maxsize=None)
def head_counts(book):
    """One observation per lexical token, on the last host of a bound chain."""
    heads, features = Counter(), Counter()
    for unit in units(book).values():
        for token in TOKEN.findall(unit['analysis']):
            if WORD.fullmatch(token):
                head, *ending = token.rstrip(':').split('/')[-1].split(':')
                heads[head] += 1
                features.update(set(ending))
    return heads, features


@lru_cache(maxsize=12)
def published_spread(path, left):
    pair = islice(page_stream(path),left-1,left+1)
    return [texts(f) for p in pair for f in sorted(p['frames'],key=lambda f:int(f['x']))]


def chapter_studies(lines):
    studies = {}
    for path in sorted(WORK.glob('depth-*.txt')):
        block = None
        for number, line in enumerate(path.read_text(encoding='utf8').splitlines(), 1):
            if line.startswith('@@ '):
                chapter = int(line[3:])
                if chapter in studies:
                    raise ValueError(f'Duplicate study for chapter {chapter} in {path.name}')
                block = studies[chapter] = []
            elif line.strip():
                if block is None:
                    raise ValueError(f'{path.name}:{number}: missing chapter number')
                block.append(line)
    chapters = sum(line.startswith('# ') for line in lines)
    if set(studies) != set(range(1, chapters + 1)) or not all(studies.values()):
        raise ValueError(f'Incomplete chapter studies: {sorted(set(range(1, chapters+1)) - set(studies))}')
    chapter = 0
    for line in lines:
        if line.startswith('# '):
            if chapter:
                yield '@ study'
                yield from studies[chapter]
            chapter += 1
        yield line
    yield '@ study'
    yield from studies[chapter]


def compile_book():
    lang, historical = language_set()
    lang.lexicon = historical.lexicon | lang.lexicon
    for key in ('kjv_number','kjv_rope','kjv_cord','kjv_tribe','kjv_loaf','kjv_broth','kjv_ferryboat','kjv_place_site','kjv_dragnet'):
        if key in lang.lexicon:
            lang.glosses[key] = {'kjv_number':'enumerate','kjv_place_site':'place','kjv_dragnet':'fishing-net'}.get(key,key[4:])
    rows, witnesses, corpus = [], [], {}
    section = 'directory'
    name = NAME
    chapter = 0
    study = False
    ordinal = 0
    def direct(kind,native,gloss,english,identifier=None):
        nonlocal ordinal
        ordinal += 1
        identifier = identifier or f'{section}.{ordinal:03d}'
        rows.append(row(identifier,kind,name,native,gloss,english,section))
        if study:
            rows[-1]['chapterStudy'] = True
        return identifier
    def authored(kind,analysis,english,identifier=None,initial=True):
        try:
            result = lang.compile(analysis,initial=initial)
        except ValueError as exc:
            raise ValueError(f'{name}: {analysis}: {exc}') from exc
        return direct(kind,result['text'],result['gloss'],english,identifier)
    def series(name,forms,labels,explanation):
        direct(name,' · '.join(forms),' · '.join(labels),explanation)

    authored('title','whole:m chart_grammar of chart_self_name',NAME,'title')
    authored('guide','first book_leaf of each part in list seek:imp. example and old:m word apart know:imp. in each part different:m read:ev:pl compare:imp. what from gram_ending know:pr and what from story know:pr apart judge:imp.',
             'Each chapter opens on the left page listed below. Read the script and Transliteration 7 on the left, then the construction gloss and English on the right. A named source identifies a quotation. The other examples are constructed. Compare the readings and distinguish what the endings establish from what the situation supplies.','guide')
    idiom_records = {r['label']:r for r in json.loads((IDIOMS/'entries.json').read_bytes())}
    idiom_source = {e['label']:e for group in idiom_manuscript() for e in group['entries']}
    def census():
        features = ['psv','cv','cvds','rep','app']
        for i,(key,book) in enumerate(BOOKS.items(),1):
            counts = Counter()
            for u in units(key).values():
                used = {f for t in TOKEN.findall(u['analysis']) if WORD.fullmatch(t)
                        for f in t.rstrip(':').split('/')[-1].split(':')[1:]}
                counts.update(used.intersection(features))
            values = [len(units(key)),*[counts[f] for f in features]]
            labels = ['passages','passive','same-subject converb','different-subject converb','reportative','apparent']
            corpus[key] = dict(book=book,passages=values[0],counts={f:counts[f] for f in features})
            head = lang.compile('book')['text']+' '+quantity(i,notation='digits')['form']
            native = head+' · '+' · '.join(quantity(v,notation='digits')['form'] for v in values)
            direct('census',native,'book '+str(i)+' · '+' · '.join(f'{label} {v}' for label,v in zip(labels,values)),
                   f'{book}. '+', '.join(f'{v:,} {label}' for v,label in zip(values,labels))+'.')
    def letters():
        for idx,upper,lower,name_,up,low in json.loads(LETTER_FILE.read_bytes())['letters']:
            description = f'{idx}. {name_}. '
            if up:
                description += f'Chart reading {up}, {low}.'
            elif idx==21:
                description += 'The chart distinguishes this second th sign. The later mapping reads Ŧh, ŧh.'
            else:
                description += 'The native pair is identified. The exact Unicode equivalent of the chart reading is unsettled.'
            direct('letter',chr(upper)+' '+chr(lower),name_+' (Maxima, Minima)',description)
    def charts():
        i = lang.maxima(lang.word('i')[0])+' '
        be = lang.word('be')[0]
        for suffix,label,english in [('diz','distant past','I was, in the distant past.'),
                ('riz','immediate past','I was, in the immediate past.'),('iz','general past','I was.'),
                ('ow','present','I am.'),('at','general future','I will be.'),
                ('rat','immediate future','I will be, in the immediate future.'),
                ('dat','distant future','I will be, in the distant future.')]:
            direct('tense-chart',i+be+suffix,'I · be('+label+')','Origins 5. '+english)
        stem = lang.word('attack')[0]
        assert lang.reading(stem)=='nouch'
        for tense,anchor,verbs in [
            ('present','ow',['attack','am attacking','have attacked','have been attacking','have been attacked','am being attacked']),
            ('past','iz',['attacked','was attacking','had attacked','had been attacking','had been attacked','was being attacked']),
            ('future','at',['will attack','will be attacking','will have attacked','will have been attacking','will have been attacked','will be being attacked'])]:
            for ending,full,label,v in zip(['ya','am','fu','Óë','fÅ','Ým'],['ya','am','fu','fuam','fufu','amfu'],
                        ['simple','progressive','perfect','perfect progressive','perfect perfect','progressive perfect'],verbs,strict=True):
                english = f'Origins 8. {tense.capitalize()} {label}. I {v}.'
                if full!=ending:
                    english += f' The chart gives full -{anchor+full} and contracted -{lang.reading(anchor+ending)}.'
                direct('aspect-chart',i+stem+anchor+ending,f'I · attack({tense}, {label})',english)
        direct('aspect-chart',stem,'attack(infinitive)','Origins 8. To attack. The chart gives a bare infinitive.')
        direct('aspect-chart',stem+'ya','attack(simple)','Origins 8. Attack. Aspect is present without an independent tense.')
    def correlatives():
        for root,domain,question in [('ËÝb','action','What was done?'),('not','quality','What kind?'),('hor','reason','Why?'),
                    ('vint','time','When?'),('kÉn','location','Where?'),('kãn','manner','How?'),('gÉÛ','quantity','How much?'),
                    ('fol','human identity and association','Who or whose?'),('Ñet','thing identification','What is this?'),('lom','truth','Is it so?')]:
            direct('correlative-chart',root+' · ib',domain+' · interrogative',
                f'Origins 7. {lang.reading(root)} … ib. {question} The two parts illustrate the printed template.')
            direct('correlative-forms',' · '.join([root,root+'a','gÍ'+root,'gß'+root]),
                   'positive base · negative base · definite stem · indefinite stem',
                   f'{domain.capitalize()}. Read the forms in order. The first two are the chart’s positive and negative bases. The next two are its definite and indefinite beginnings. Each prefixed specimen ends where the chart supplies an ellipsis.')
            direct('correlative-forms',' · '.join([root+'Ñe',root+'uz',root+'lÝ']),
                   'demonstrative pattern · extended negative in -uz · extended negative in -lī',
                   f'{domain.capitalize()}. The first specimen sets the base beside che, the demonstrative element; the chart allows intervening and following material. The other two are the printed beginnings of extended negatives. Their choice in ordinary conversation is undetermined here.')
        for key,label in [('who','person'),('where','place'),('how','manner')]:
            authored('correlative-comparison',key,'Later lexicon. '+key.capitalize()+'? A complete interrogative for '+label+'.',initial=False)
    def features():
        seen = set()
        for line in (WORK/'form-reference.txt').read_text(encoding='utf8').splitlines():
            f,a,e = line.split(' | ')
            if f in seen or not re.search(r':'+f+r'(?=[:\s.,?]|$)',a):
                raise ValueError('Invalid feature specimen '+f)
            seen.add(f)
            authored('morphology',a,e)
        if seen != lang.prefix.keys() | lang.suffix.keys():
            raise ValueError('Feature inventory differs from the language package')
    def pronouns():
        for k,p,label in [('i','my','personal singular I'),('ipl','mypl','internally plural I'),
                  ('wesg','ourone','one acting we'),('wepl','ourpl','individuated plural we'),
                  ('thou','thy','familiar singular you'),('you','your','formal or plural you'),
                  ('he','his','he'),('she','her','she'),('they','their','animate they'),('it','its','inanimate it')]:
            forms=[lang.word(x) for x in (k,k+':a',k+':d',p+'/boat')]
            series('pronoun',[v[0] for v in forms],[v[1] for v in forms],
                   label.capitalize()+'. Free subject, direct object, recipient, then the same person as possessor of a boat.')
    def boundaries():
        for invalid,valid,code,explanation in [
            ('you:g:d','each:d of you','CONFLICTING_CASE','A set and its selected member need separate heads.'),
            ('eye:du:pl','eye:du','CONFLICTING_NUMBER','A pair has one number choice.'),
            ('be:pa:pr','be:pa','CONFLICTING_TENSE_ASPECT','Choose one finite anchor for this event.'),
            ('sleep:pr:cv','sleep:cv','FINITE_NONFINITE_CONFLICT','An attendant action gets its time from the main event.'),
            ('be:pr:app:rep','she say:pr that boat return:perf:app.','UNLICENSED_EVIDENTIAL_STACK','Use a reporting clause to enclose a claim about appearances.'),
            ('be:rep','be:pr:rep','FINITE_ANCHOR_REQUIRED','Reportative needs a finite host.'),
            ('open:pr:psv','open:psv:pr','VOICE_AFTER_CLAUSE_ENDING','Form the passive before choosing tense.'),
            ('go:inf:perf','go:perf:inf','PERFECT_INFINITIVE_ORDER','Anteriority is inside the infinitive.'),
            ('go:pr:must:may','go:pr:may','UNLICENSED_MODAL_STACK','Choose possibility when that is the intended force.'),
            ('go:excl:pr','go:pr:excl','EXCLAMATIVE_NOT_FINAL','Heightened delivery takes the completed assertion.'),
            ('boat:dep','he:a:dep he','DEPENDENT_FORM_REQUIRES_PRONOUN','The dependent allomorph requires a personal pronoun.'),
            ('boat:add:a','boat:a:add','INFLECTION_AFTER_PHRASE_CLITIC','Place the additive outside case.'),
            ('love:subend','love:pr:subend love:pr','DEPENDENT_CLAUSE_NEEDS_FINITE_PREDICATE','The first finite predicate must close a dependent clause.')]:
            try:
                lang.compile(invalid)
            except ValueError as exc:
                if str(exc)!=code: raise
            else:
                raise ValueError('Expected rejection for '+invalid)
            # Spell out the rejected analysis, without posing it as a native word.
            labels=[(lang.suffix | lang.prefix)[f][1] for f in invalid.split(':')[1:]]
            authored('boundary',valid,'Rejected analysis, '+invalid.split(':')[0]+' + '+' + '.join(labels)+'. '+explanation)
    def numbers():
        for n,kind,d in [(n,'cardinal',1) for n in [*range(13),24,100,144,1728]]+[
                (3,'ordinal',1),(3,'times',1),(3,'fold',1),(1,'fraction',3),(1,'fraction',7)]:
            w = quantity(n,kind,d)
            digits = quantity(n,kind,d,notation='digits')
            sense = {'ordinal':'third in order','times':'three occurrences','fold':'threefold measure',
                     'fraction':f'{n} out of {d} equal parts','cardinal':str(n)}[kind]
            series('unta',[w['form'],digits['form']],[sense,sense],
                   f'{sense.capitalize()}. '+('Exact part-to-whole construction.' if d==7 else
                   f'The base-twelve numeral is {w["base12"]}.')+(' Its decimal value is '+str(n)+'.' if n>=12 else ''))
    extensions = dict(census=census,letters=letters,charts=charts,correlatives=correlatives,features=features,
                      pronouns=pronouns,boundaries=boundaries,numbers=numbers)
    def controls():
        files = [LANG_DATA/('later-dramatic-'+version)/'flow-cases.json' for version in ('0.12','0.13')]
        cases = [{u['id']:u for u in json.loads(path.read_bytes())} for path in files]
        ids = sorted(cases[0].keys() & cases[1].keys())
        values = [len(ids),*[sum(cases[0][i][field]==cases[1][i][field] for i in ids)
                             for field in ('expectedText','expectedGloss')]]
        series('historical-control',[quantity(v,notation='digits')['form'] for v in values],
               ['shared cases','same native','same gloss'],
               f'Dramatic 0.12 and 0.13. {values[0]} shared cases, {values[1]} with identical native wording and {values[2]} with identical construction gloss.')
    extensions['controls'] = controls
    lines = (WORK/'grammar.txt').read_text(encoding='utf8').splitlines()
    at = next(i for i,line in enumerate(lines) if line.startswith('# Reference A.'))
    lines[at:at] = [line for title in SUPPLEMENTS for line in (WORK/(title+'.txt')).read_text(encoding='utf8').splitlines()]
    lines = list(chapter_studies(lines))
    literary_pages=collate_literary_witnesses(lines)
    for line in lines:
        if not line.strip(): continue
        if line == '@ study':
            study = True
            continue
        if line.startswith('@ '):
            extensions[line[2:]]()
            continue
        if line.startswith('# '):
            study = False
            name,analysis = line[2:].split(' | ')
            chapter += 1
            section = f'ch{chapter:02d}'
            ordinal = 0
            res = lang.compile(analysis)
            direct('section',quantity(chapter,notation='digits')['form']+'. '+res['text'],
                   f'{chapter}. '+res['gloss'],f'{chapter}. '+name,section)
            continue
        tag,*fields = line.split(' | ')
        if tag in {'P','E'}:
            authored('exposition' if tag=='P' else 'example',*fields)
        elif tag=='T':
            book, citation_form, *queries = fields
            heads, features = head_counts(book)
            title = lang.compile(citation_form)['text']
            counts, labels, native = [], [], []
            for query in queries:
                selector, specimen = query.split('=', 1)
                if selector.startswith('$'):
                    roots = selector[1:].split(',')
                    if any(key not in lang.lexicon for key in roots):
                        raise ValueError('Unknown head in count: '+selector)
                    forms = {lang.word(key)[0] for key in roots}
                    if len(forms) != 1:
                        raise ValueError('Grouped heads have different native forms')
                    count = sum(heads[key] for key in roots)
                else:
                    if selector not in (lang.prefix | lang.suffix):
                        raise ValueError('Unknown feature in count: '+selector)
                    count = features[selector]
                sample = lang.compile(specimen,initial=False)
                counts.append(count)
                labels.append(sample['gloss'])
                native.append(sample['text']+' · '+quantity(count,notation='digits')['form'])
            total = sum(heads.values())
            direct('corpus-observation', title+' · '+quantity(total,notation='digits')['form']+'. '+' · '.join(native),
                   f'{BOOKS[book]} · {total:,} lexical heads. '+', '.join(f'{k} · {n:,}' for k,n in zip(labels,counts)),
                   f'{BOOKS[book]} authoring ledger, {total:,} lexical heads. '+
                   ', '.join(f'{label} ({n:,})' for label,n in zip(labels,counts))+'. The forms illustrate the categories counted.')
        elif tag=='G':
            key,=fields
            entry=lang.lexicon[key]
            roots=entry['derivationKeys']
            if entry['form']!=''.join(lang.lexicon[k]['form'] for k in roots):
                raise ValueError('Technical term has a different derivation: '+key)
            direct('technical-term',entry['form'],' + '.join(lang.glosses.get(k,k.replace('_','-')) for k in roots),
                   f'{entry["roman"]} ({entry["label"]}). {entry["meaning"]} Proposed technical term in this edition.')
        elif tag=='Q':
            op,a,b,ans,comment=fields
            x,y,z=map(Fraction,(a,b,ans))
            if op=='sum':
                value=x+y
                template='{0} and {1} together {2} be:pr.'
                sign='+'
            elif op=='difference':
                value=x-y
                template='{0}:abl {1}:a take:imp. {2} remain:pr.'
                sign='−'
            elif op=='share':
                value=x/y
                template='{0} into {1} equal:m part:pl divide:imp. each {2} be:pr.'
                sign='÷'
            else:
                raise ValueError('Unknown arithmetic operation '+op)
            if z!=value:
                raise ValueError('Incorrect worked calculation: '+line)
            # Compile the words and quantities together to preserve the numeric glyph slots.
            keys=('calcleft','calcright','calcresult')
            for slot,v in zip(keys,(x,y,z),strict=True):
                quant=quantity(v.numerator,'cardinal' if v.denominator==1 else 'fraction',
                               v.denominator,notation='digits')
                lang.lexicon[slot]=dict(form=quant['form'],pos='numeral')
                lang.glosses[slot]=str(v)
            authored('calculation',template.format(*keys),f'{a} {sign} {b} = {ans} (decimal values). {comment}',initial=False)
            for slot in keys:
                del lang.lexicon[slot],lang.glosses[slot]
        elif tag=='V':
            score,translation = [field.split(' // ') for field in fields]
            if len(score)<2 or len(score)!=len(translation):
                raise ValueError('Unaligned stanza in '+name)
            initial=True
            stanza=[]
            for number,(verse,english) in enumerate(zip(score,translation,strict=True),1):
                authored('verse-line',verse,english,initial=initial)
                rows[-1]['verseLine']=number
                rows[-1]['verseLength']=len(score)
                stanza.append(rows[-1]['text'])
                initial=verse.endswith(('.','?','!'))
            if english=='Shore fills eye.' and [len(t.split()) for t in stanza]!=[3]*4:
                raise ValueError('Twelve-word stanza lost its count')
            if english=='Lamp.' and [len(t.split()) for t in stanza]!=[4,3,2,1]:
                raise ValueError('Retreating stanza lost its count')
            if english=='Leave her lamp here.':
                if ''.join(t[0] for t in stanza)!=''.join(lang.maxima(c) for c in lang.word('ultimate_grief')[0]):
                    raise ValueError('Acrostic lost one of its four native initials')
            if english=='Hear the rain.' and ''.join(t[0] for t in stanza)!=''.join(lang.maxima(c) for c in lang.word('word')[0]):
                raise ValueError('The specialist acrostic must spell the native word for word')
        elif tag=='H':
            early,one,late,two,note=fields
            records=[edition_lexicon(v)[k] for v,k in ((early,one),(late,two))]
            native=[r['form'] for r in records]
            series('historical-pair',native,[f'{early} {one}',f'{late} {two}'],
                   f'{early} {lang.reading(native[0])} → {late} {lang.reading(native[1])}. '+note)
        elif tag=='C':
            book,key,note=fields
            examples=lexical_citations(book)[key]
            record=json.loads(SOURCES[book].with_name('dictionary-additions.json').read_bytes())['entries'][key]
            if not examples or record['form']!=lang.lexicon[key]['form']:
                raise ValueError('Contact citation mismatch: '+key)
            form=lang.word(key)[0]
            elements=record.get('derivationKeys',[])
            display=' + '.join(lang.glosses.get(k,k.replace('_','-')) for k in elements)
            spread=book_spread_index(book)[examples[0]]
            ref=f'{BOOKS[book]}, pp. {spread["leftPage"]}–{spread["rightPage"]}'
            rid=direct('contact-entry',form,record['meaning']+(' · '+display if display else ''),
                       f'{lang.reading(form)}. {note} {len(examples)} cited passage'+('s' if len(examples)!=1 else '')+
                       f'. First occurrence in {ref}.')
            witnesses.append(dict(row=rid,source=book,key=key,reference=ref,units=examples))
        elif tag=='W':
            book,key = fields
            u = units(book)[key]
            ref=u.get('reference') or key
            citation=SOURCE_NAMES[book]+', '+ref
            if book in BOOKS:
                path=SOURCES[book]
                spread=book_spread_index(book)[key]
                pos=spread['unitIds'].index(key)
                source_file=next(path.parent.parent.glob('*.vay'))
                columns=published_spread(source_file,spread['leftPage'])
                if [col[pos] for col in columns]!=[u[f] for f in FIELDS]:
                    raise ValueError('Witness has changed in the published book: '+key)
                citation+=f', pp. {spread["leftPage"]}–{spread["rightPage"]}'
            elif (book,key) in literary_pages:
                left=literary_pages[book,key]
                citation+=f', pp. {left}–{left+1}'
            native = u['text'] if 'text' in u else u['expectedText']
            gloss = u['gloss'] if 'gloss' in u else u['expectedGloss']
            rid=direct('witness',native,gloss,u['source']+' ('+citation+')')
            witnesses.append(dict(row=rid,source=book,key=key,reference=citation))
        elif tag=='I':
            label,=fields
            e=idiom_records[label]
            source=idiom_source[label]
            head=lang.compile(source['head'],initial=False)
            ref=f'Idiom Inventory, pp. {e["leftPage"]}–{e["leftPage"]+1}'
            definition=e['definition']
            assert head['text']==e['native']
            native=head['text']+': '+definition['native']
            gloss=head['gloss']+': '+definition['gloss']
            english=label+' — '+definition['english']
            source_file=next(IDIOMS.parent.glob('*.vay'))
            columns=published_spread(source_file,e['leftPage'])
            position=columns[0].index(native)
            if [col[position] for col in columns]!=[native,native,gloss,english]:
                raise ValueError('Idiom differs from its published spread: '+label)
            rid=direct('idiom-witness',native,gloss,english+' ('+ref+')')
            witnesses.append(dict(row=rid,source='idioms',key=e['id'],reference=ref))
            for src,ex in zip(source['examples'],e['examples'],strict=True):
                res=lang.compile(src['analysis'])
                assert res['text']==ex['native'] and src['english']==ex['english']
                direct('idiom-example',res['text'],res['gloss'],ex['english'])
        else: raise ValueError(line)
    study = False
    section = 'subject-index'
    name = 'Subject index'
    ordinal = 0
    authored('section','list of thing:pl in chart_grammar',name,section)
    index_lines = [(line, filename=='chapter-study-index.txt') for filename in
                   ('subject-index.txt','literary-index.txt','specialist-index.txt','chapter-study-index.txt')
                   for line in (WORK/filename).read_text(encoding='utf8').splitlines() if line.strip()]
    for line, in_study in sorted(index_lines,key=lambda item:item[0].casefold()):
        label,analysis,anchor = line.split(' | ')
        matches = [r for r in rows if bool(r.get('chapterStudy')) == in_study and r['section']!=section and r['source'].startswith(anchor)]
        if len(matches)!=1: raise ValueError(f'Index anchor {anchor!r} has {len(matches)} targets')
        authored('index-term',analysis,label)
        rows[-1]['pointsTo']=matches[0]['id']
    assert len({r['id'] for r in rows})==len(rows)
    return rows,witnesses,corpus


def publish():
    rows,witnesses,corpus=compile_book()
    print('Compiled',len(rows),'rows',flush=True)
    if '--check' in sys.argv: return
    STAGE.mkdir(parents=True,exist_ok=True)
    stage=STAGE/'publication.vay'
    target=FOLDER/(TITLE+'.vay')
    receipt=WORK/'publication.json'
    if target.exists() and (not receipt.exists() or sha(target)!=json.loads(receipt.read_bytes())['sha256']):
        raise ValueError('Existing book has independent edits.')
    sources=[*SOURCES.values(),LETTER_FILE,IDIOMS/'entries.json',IDIOMS/'idioms.txt',ROOT/'Inputs/Language Terms.jpg',
             WORK/'grammar.txt',WORK/'form-reference.txt',WORK/'subject-index.txt',WORK/'dictionary-additions.json',
             ROOT/'tools/comprehensive_grammar.py',ROOT/'tools/unta_language.py']
    sources += [p for p in (ROOT/'Inputs').glob('*') if p.is_file() and
                (p.name=='Inventory of Clitics.jpg' or p.name.startswith(('Origins_2_','Origins_3_','Origins_5_','Origins_6_','Origins_7_','Origins_8_')))]
    for sub in ['consolidated-0.10','later-dramatic-0.11','later-dramatic-0.12','later-dramatic-0.13']:
        sources.append(ROOT/'data/language'/sub/'grammar.md')
        sources.append(LANG_DATA/sub/'lexicon.json')
    sources += [WORK/(title+'.txt') for title in (*SUPPLEMENTS,'literary-index','specialist-index','chapter-study-index')]
    sources += sorted(WORK.glob('depth-*.txt'))
    sources.append(WORK/'specialist-sources.json')
    sources += [SOURCES[b].with_name('dictionary-additions.json') for b in ('dampier','boyle')]
    sources += [LANG_DATA/('later-dramatic-'+v)/'flow-cases.json' for v in ('0.12','0.13')]
    hashes={str(p.relative_to(ROOT)):sha(p) for p in sources}
    digest=hashlib.sha256(json.dumps(rows,ensure_ascii=True,sort_keys=True).encode()).hexdigest()
    layout=GrammarLayout(title=TITLE,document_id='document.comprehensive-grammar',id_prefix='grammar',column_names=COLUMNS,cache_root=STAGE)
    try:
        from tools.vayrshemon_thesaurus import locations
        rows,targets=subject_guide(rows,layout)
        pages_by_row={}
        for section,items in groupby(rows[2:],key=lambda r:r['section']):
            if section not in targets or section=='subject-index': continue
            local=locations(list(items),layout)
            pages_by_row.update({key:targets[section]+page-1 for key,page in local.items()})
        for item in rows:
            if 'pointsTo' in item:
                p=pages_by_row[item['pointsTo']]
                item['indexedPage']=p
                item['text']+=' · '+quantity(p,notation='digits')['form']
                for field in ('gloss','source'): item[field]+=' · '+str(p)
        print('Chapter guide measured',flush=True)
        report,spreads=layout.build(rows,stage,digest)
    finally: layout.session.finish()
    by_id={r['id']:r for r in rows}
    loc={k:s['leftPage'] for s in spreads for k in s['ids']}
    assert all(loc[k]==v for k,v in targets.items())
    assert all(loc[r['pointsTo']]==r['indexedPage'] for r in rows if 'pointsTo' in r)
    for n,r in enumerate(rows):
        if r.get('verseLine')==1 and loc[r['id']]!=loc[rows[n+r['verseLength']-1]['id']]:
            raise ValueError('Stanza split across spreads: '+r['id'])
    proofs = {1,2,3,4,len(spreads)*2}
    for left in targets.values():
        proofs.update([left,left+1])
    for s in spreads:
        if any(by_id[k]['kind'] in {'letter','aspect-chart','morphology','unta','boundary','pronoun','idiom-witness','census'} for k in s['ids']):
            proofs.update([s['leftPage'],s['rightPage']])
    session=FileSession(ROOT,source_fonts=False,recovery=False)
    session.remember=lambda *a:None
    session.log.emit=lambda *a,**kw:None
    try:
        session.open(stage,advance_revision=False)
        state=session.state
        assert state['title']==TITLE and session.saved_page_mode=='two' and len(state['pages'])==2*len(spreads)
        for spread in spreads:
            pair=state['pages'][spread['leftPage']-1:spread['rightPage']]
            frames=[f for p in pair for f in sorted(p['frames'],key=lambda f:int(f['x']))]
            assert [f['name'] for f in frames]==list(COLUMNS)
            for field,frame in zip(FIELDS,frames,strict=True):
                if texts(frame)!=[by_id[k][field] for k in spread['ids']]: raise ValueError('Reopen mismatch at '+str(spread['leftPage']))
            for frame,digest in zip(frames[:2],[reading.SCRIPT_SHA,reading.ROMAN_SHA],strict=True):
                doc=frame['content']['document']
                styles={s['styleId']:s.get('fontId') for s in doc['styles']}
                for block in doc['stories'][0]['blocks']:
                    for run in block['runs']:
                        text=run.get('sourceText',run.get('text',''))
                        if any(c.isalpha() for c in text) and styles[run['styleId']]!='font:'+digest+':0':
                            raise ValueError('Fallback font used for a native letter: '+repr(text))
        for n in sorted(proofs):
            picture,_=pages.render(session,page_id=state['pages'][n-1]['pageId'],mode='mono',dpi=80,reading=True)
            if not picture.save(str(STAGE/f'proof-{n:03d}.png')): raise OSError('Page proof failed')
    finally: session.finish()
    report.update(stanzas=sum(r.get('verseLine')==1 for r in rows),
                  chapters=[dict(chapter=i,heading=by_id[k]['reference'],leftPage=v) for i,(k,v) in enumerate(targets.items(),1) if k!='subject-index'],
                  indexStart=targets['subject-index'],checkedIndexEntries=sum('pointsTo' in r for r in rows),
                  rowKinds=dict(Counter(r['kind'] for r in rows)),columns=list(COLUMNS),witnesses=witnesses,
                  census=corpus,sourceHashes=hashes,nativeReopenVerified=True,checkedGuideTargets=len(targets),
                  renderedProofPages=sorted(proofs))
    for w in witnesses:w['page']=loc[w['row']]
    report['chapterStudies'] = []
    for heading in report['chapters']:
        section = f'ch{heading["chapter"]:02d}'
        study_rows = [r for r in rows if r['section'] == section and r.get('chapterStudy')]
        report['chapterStudies'].append(dict(chapter=heading['chapter'],
            firstRow=study_rows[0]['id'], lastRow=study_rows[-1]['id'],
            leftPage=loc[study_rows[0]['id']], lastRightPage=loc[study_rows[-1]['id']]+1,
            nativeWords=sum(len(r['text'].split()) for r in study_rows),
            kinds=dict(Counter(r['kind'] for r in study_rows))))
    report['specialistReferences']=json.loads((WORK/'specialist-sources.json').read_bytes())
    for citation in report['specialistReferences']:
        anchor=citation.pop('anchor')
        example,=(r for r in rows if r['kind']=='exposition' and r['source'].startswith(anchor))
        citation['pages']=[loc[example['id']],loc[example['id']]+1]
    stage.replace(target)
    write_atomic(WORK/'page-index.json',spreads)
    write_atomic(receipt,report)
    print('Published',report['pages'],'pages.',flush=True)


if __name__=='__main__': publish()
