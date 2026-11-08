"""Build the author's Unta erratum from the sealed 282 verse analyses."""
from collections import Counter
from copy import deepcopy
from fractions import Fraction
import html
from math import prod
from pathlib import Path
import json
import re
import shutil
import sqlite3

from tools.kjv_archive import digest, read, verify_register
from tools.kjv_historical_flow import compiler
from tools.unta_language import quantity, semantic_key

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / 'Saves/KJV Bible v0.10-kjv.282'
VERSION = '0.10-kjv.283'
OUT = ROOT / f'Saves/KJV Bible v{VERSION}'
COMPACT = ROOT / f'Saves/KJV Bible - Compact Letter Edition v{VERSION}'
PARENT = ROOT / 'data/language/archaic-kjv-282'
PACKAGE = ROOT / 'data/language/archaic-kjv-283'
LEDGER_HASH = '41b50cf2314fd17e1528a9ee719db4361b1733b337d6a439f2b1179ffd90f9f2'
PROGRESSIVE_HASH = '9f37f4432a90065996380110a62e736e4dc7e554de275eb664d903d3f1b2e2a3'
COMPACT_HASH = '42aca1b6dbb594b2b8f49817e793278186e3f9fe06de7f601fd3649ee649c6a2'
WORDS = 'zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen'.split()
VALUES = dict(zip(WORDS, range(20)))
VALUES.update(zip('twenty thirty forty fifty sixty seventy eighty ninety'.split(), range(20, 100, 10)))
VALUES.update(hundred=100, thousand=1000, million=1000000)
KEYS = {**VALUES, 'one_num': 1, 'kjv_three': 3, 'kjv_score': 20}
del KEYS['one']  # Generic person in this register.
ORDINAL = dict(first=1, second=2, kjv_second=2, third=3, fourth=4)
DENOM = {'half': 2, 'one_num+half': 2, 'kjv_third_share': 3, 'kjv_fourth_share': 4,
         'kjv_fifth_share': 5, 'kjv_sixth_share': 6, 'kjv_tenth_share': 10}
EN_ORD = dict(zip('first second third fourth fifth sixth seventh eighth ninth tenth eleventh twelfth thirteenth fourteenth fifteenth sixteenth seventeenth eighteenth nineteenth twentieth thirtieth fortieth fiftieth sixtieth seventieth eightieth ninetieth hundredth thousandth'.split(),
                  [*range(1, 21), *range(30, 100, 10), 100, 1000]))
ENGLISH = {**VALUES, **EN_ORD, 'score': 20, 'twain': 2, 'dozen': 12}
ENGLISH.update({word+'score': value*20 for word,value in VALUES.items() if 1 <= value <= 11})
SOURCE_TOKEN = re.compile(r'\b('+'|'.join(sorted(ENGLISH, key=len, reverse=True))+r')(?:fold)?\b', re.I)
TOKEN = re.compile(r'[A-Za-z_][A-Za-z_+/:\-]*|\d+|[^\w\s]')
ONCE_NONCOUNT = {'Deuteronomy 7:22','Jeremiah 13:27','Luke 13:25','Hebrews 6:4',
                 'Hebrews 10:2','1 Peter 3:20','Jude 1:5'}
SOURCE_REVIEW = {
    **{ref: ('they:du','two they:du') for ref in ('2 Kings 2:6','2 Kings 2:7','2 Kings 2:8','2 Kings 4:33')},
    **{ref: ('tithe:a','kjv_tenth_share:a') for ref in ('1 Samuel 8:15','1 Samuel 8:17')},
    'Nehemiah 9:3': ('one_num fourth part','fourth part'),
    'Daniel 3:19': ('one_num seven time:pl','seven kjv_fold'),
}


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf8')


def source_amounts(source):
    """Whole amounts as written in the verse, including KJV inverted tens."""
    groups, group, end = [], [], None
    for m in SOURCE_TOKEN.finditer(source):
        gap = source[end:m.start()].lower() if end is not None else ''
        if group and gap.strip() not in ('', '-', 'and'):
            groups.append(group)
            group = []
        group.append(m.group(1).lower())
        end = m.end()
    if group:
        groups.append(group)
    result = set()
    for words in groups:
        # "two and two" is distributive, and "one and one" can be a pair.
        if len(words) == 2 and words[0] == words[1] and ENGLISH[words[0]] < 12:
            continue
        partial = total = 0
        for word in words:
            v = ENGLISH[word]
            if v == 100:
                partial = (partial or 1)*100
            elif v >= 1000:
                total += (partial or 1)*v
                partial = 0
            else:
                partial += v
        result.add(total + partial)
    return result


def numeric_token(token):
    stem, *features = token.split(':')
    parts = stem.split('+')
    if all(p in KEYS for p in parts):
        return prod(KEYS[p] for p in parts), features
    if stem in ORDINAL:
        return ORDINAL[stem], ['ord', *features]
    return None


def label(value, kind):
    value = Fraction(value)
    if kind == 'fraction':
        return str(value)+' share'
    n = value.numerator
    if kind == 'ordinal':
        return next((w for w,v in EN_ORD.items() if v == n), f'ordinal {n}')
    name = WORDS[n] if 0 <= n < len(WORDS) else f'{n:,}'
    return name + {'cardinal':'','times':' times','fold':'fold'}[kind]


class Correction:
    def __init__(self):
        self.forms = {}

    def entry(self, value, kind, features, notation='words'):
        value = Fraction(value)
        key = semantic_key(value.numerator, kind, value.denominator, notation=notation)
        if key not in self.forms:
            self.forms[key] = quantity(value.numerator, kind, value.denominator, notation=notation)
        return ':'.join([key, *features])

    def revise(self, unit):
        analysis = unit['analysis']
        source = unit['source']
        ref = unit['reference']
        if ref in SOURCE_REVIEW:
            before,after=SOURCE_REVIEW[ref]
            assert analysis.count(before)==1,ref
            analysis=analysis.replace(before,after)
        amounts = source_amounts(source)
        # These two source expressions use an explicit multiplication of like factors.
        analysis = analysis.replace('ten+thousand+ten+thousand', 'ten+thousand kjv_fold ten+thousand')
        analysis = analysis.replace('six kjv_score thousand', 'six+kjv_score+thousand')
        if ref == 'Ecclesiastes 6:6':
            analysis = analysis.replace('two+thousand year:pl','thousand year:pl twice')
        if ref == '1 Chronicles 21:5':
            amounts.add(1100000)  # A thousand thousand and an hundred thousand.
        # Working on compiler tokens preserves all punctuation and prose spacing.
        matches = list(TOKEN.finditer(analysis))
        edits = []
        i = 0
        while i < len(matches):
            start = i
            token = matches[i].group()
            owners = token.split('/')[:-1]
            leaf = token.split('/')[-1]
            stem, *features = leaf.split(':')
            endcolon = bool(features and features[-1] == '')
            if endcolon: features.pop()
            i += 1
            value = None
            kind = 'cardinal'
            numeric = numeric_token(leaf.rstrip(':'))
            if numeric:
                value, features = numeric
                # Coalesce only a single source-attested amount. Preserve enumerations,
                # distributives, distinct units and morphology on the original phrase.
                total, best = value, None
                j = i
                while j+1 < len(matches) and matches[j].group() == 'and':
                    following = numeric_token(matches[j+1].group().rstrip(':'))
                    if not following or 'ord' in features: break
                    total += following[0]
                    if total in amounts and following[0] != value and max(total-following[0], following[0]) >= 10:
                        best = (j+2, total, following[1])
                    if following[1]: break
                    j += 2
                if best:
                    i, value, trailing = best
                    features = list(dict.fromkeys([*features, *trailing]))
                if 'ord' in features:
                    kind = 'ordinal'
                    features.remove('ord')
                if i < len(matches):
                    next_stem, *next_features = matches[i].group().split(':')
                    if next_stem == 'part' and kind=='ordinal' and value>1 and re.search(r'\b(?:part|deal|portion|fraction)s?\b',source,re.I):
                        value, kind = Fraction(1,value), 'fraction'
                        features += next_features
                        i += 1
                    elif next_stem == 'kjv_fold' or (next_stem == 'time' and re.search(r'\b\w+fold\b',source,re.I)):
                        kind = 'fold'
                        features += [f for f in next_features if f not in ('pl','')]
                        i += 1
                    elif next_stem == 'time' and kind=='cardinal' and re.search(r'\b(?:once|twice|thrice|times)\b',source,re.I):
                        kind = 'times'
                        features += [f for f in next_features if f not in ('pl','')]
                        i += 1
            elif stem in DENOM:
                value,kind = Fraction(1,DENOM[stem]),'fraction'
            elif stem in ('once','twice','thrice') and not (stem=='once' and (ref in ONCE_NONCOUNT or (start and matches[start-1].group()=='at'))):
                value,kind = {'once':1,'twice':2,'thrice':3}[stem],'times'
            elif stem=='double' and re.search(r'\bdouble(?:d)?\b',source,re.I):
                value,kind = 2,'fold'
            if value is not None:
                endcolon = matches[i-1].group().endswith(':')
                features = [f for f in features if f]
                replacement = '/'.join([*owners,self.entry(value,kind,features)])+(':' if endcolon else '')
                edits.append((matches[start].start(),matches[i-1].end(),replacement))
        for a,b,new in reversed(edits):
            analysis = analysis[:a]+new+analysis[b:]
        return analysis


NOTE = """The author requested a correction of Unta throughout the two historical Bibles.
The same verse ledger supplies the study text and compact print text. Match the source's
notation. Spelled quantities take spoken Unta and printed figures take Unta digits.
The 31,102 KJV verse bodies in this particular source have no printed digits. Chapter,
verse and folio labels are separate numerical furniture and retain their Unta glyphs.

Genesis 1:13 uses venik’t for “third.” In Revelation 13:18 the quantity is one spoken
666. In Jonah 4:11 the threshold is strictly more than 120,000 people. Genesis 7:9
retains the pairing “two and two.” Matthew 18:22 retains both factors of seventy
times seven. Fractions are exact. A tenth or hundredth part retains its denominator
without rounding. Compound and personal titles keep their established identities.

This author-directed erratum branches from 282. The historical clause order,
pronoun distinctions, narrative register and Yeshūa naming decisions are inherited.
The quantities table identifies each value, spelling and base-twelve representation.
The correction ledger records the before and after analysis of each revised verse.
"""


def prepare():
    verify_register('0.10-kjv.282')
    assert digest(OLD/'KJV Bible.vay') == PROGRESSIVE_HASH
    old_compact = ROOT/'Saves/KJV Bible - Compact Letter Edition v0.10-kjv.282'
    assert digest(next(old_compact.glob('*.vay'))) == COMPACT_HASH
    for base in (OLD,old_compact):
        assert digest(base/'complete-translation-ledger.json') == LEDGER_HASH
    if (OUT/'FROZEN.json').exists() or any(OUT.glob('*.vay')) or (PACKAGE/'manifest.json').exists():
        raise FileExistsError('Refusing to rewrite a published or composed edition')
    PACKAGE.mkdir(exist_ok=True)
    OUT.mkdir(exist_ok=True)
    COMPACT.mkdir(exist_ok=True)
    for name in ('compiler.py','orthography.json','grammar.md','flow-cases.json','names.md','display-labels.json','name-forms.json'):
        shutil.copyfile(PARENT/name,PACKAGE/name)
    (PACKAGE/'unta.md').write_text(NOTE,encoding='utf8')
    language = compiler(PARENT)
    lex = read(PARENT/'lexicon.json')
    lex['version'] = VERSION
    morph = read(PARENT/'morphology.json')
    original = read(OLD/'complete-translation-ledger.json')
    correction = Correction()
    analyses = [correction.revise(u) for u in original['units']]
    quantities = correction.forms
    entries = lex['entries']
    place = entries['kjv_three_taverns_acts']
    place.update(form=quantity(3)['form']+' '+entries['drink']['form']+entries['house']['form'],
                 origin='Transparent KJV place name Three Taverns, with spoken Unta three and the native drink-house compound.',register=VERSION)
    place['roman']=language.reading(place['form'])
    for key in KEYS.keys() | ORDINAL.keys() | DENOM.keys() | {'twenty_four','twice','thrice'}:
        if key not in entries: continue
        if key in DENOM: q = quantity(1,'fraction',DENOM[key])
        elif key in ORDINAL: q = quantity(ORDINAL[key],'ordinal')
        elif key in ('twice','thrice'): q = quantity(2 if key=='twice' else 3,'times')
        else: q = quantity(KEYS.get(key,24))
        entry = entries[key]
        if entry['form'] != q['form']:
            entry.setdefault('historicalForms',[]).append(dict(version='0.10-kjv.282',form=entry['form'],roman=entry['roman']))
            entry.update(form=q['form'],roman=language.reading(q['form']),origin=q['evidence'],register=VERSION)
            if key in ('kjv_three','kjv_second','kjv_score'):
                entry['meaning'] = label(Fraction(q['value']),q['kind'])+' in this historical register'
    for key,q in quantities.items():
        name = label(Fraction(q['value']),q['kind'])
        entries[key] = dict(form=q['form'],roman=language.reading(q['form']),pos='numeral',meaning=name,
            origin=q['evidence'],semanticId='lex.'+key,status='authored',derivationKeys=[],register=VERSION)
        morph['glosses'][key] = name
    write(PACKAGE/'quantities.json',quantities)
    write(PACKAGE/'lexicon.json',lex)
    write(PACKAGE/'morphology.json',morph)
    revised_language = compiler(PACKAGE)
    changes,units = [],[]
    for old,a in zip(original['units'],analyses,strict=True):
        donor = language.compile(old['analysis'])
        assert donor['text']==old['text'] and donor['gloss']==old['gloss'], old['reference']
        new = dict(old, analysis=a, **revised_language.compile(a))
        notes = {
            'Genesis 1:8':'The ordinal of two uses the chart word with the historical ordinal ending.',
            'Genesis 1:13':'The written word third takes the Unta ordinal venik’t.',
            'Jonah 1:17':'Fish is retained. Both counts use the chart name for three. The purpose clause names the fish as swallower.'}
        if old['reference'] in notes: new['note']=notes[old['reference']]
        if new != old:
            changes.append(dict(id=old['id'],reference=old['reference'],beforeAnalysis=old['analysis'],afterAnalysis=a,
                                nativeChanged=new['text']!=old['text'],glossChanged=new['gloss']!=old['gloss']))
        units.append(new)
    assert len(units)==31102 and len({u['id'].split('.')[0] for u in units})==66
    assert all(not re.search(r'\d',u['source']) for u in units)
    assert 'venik’t' in units[12]['text'] and units[12]['reference']=='Genesis 1:13'
    assert not any('tren’t' in u['text'].split() for u in units)
    summary = dict(version=VERSION,parent='0.10-kjv.282',verses=len(units),sections=66,
        revisedAnalyses=sum(c['beforeAnalysis']!=c['afterAnalysis'] for c in changes),revisedVerses=len(changes),
        nativeChanged=sum(c['nativeChanged'] for c in changes),glossChanged=sum(c['glossChanged'] for c in changes),
        distinctQuantityReadings=len(quantities),sourceDigitVerses=0,parentLedgerSha256=LEDGER_HASH,
        parentNativeSha256=PROGRESSIVE_HASH,parentCompactSha256=COMPACT_HASH,sourcePreserved=True)
    write(OUT/'complete-translation-ledger.json',dict(original,version=VERSION,correctionOf='0.10-kjv.282',units=units))
    write(OUT/'correction-ledger.json',changes)
    write(PACKAGE/'coverage-summary.json',summary)
    write(OUT/'language-delta.json',summary)
    print(summary,flush=True)


def publish():
    from vayrshemon.forge import ForgeProject
    parent_head = verify_register('0.10-kjv.282')['forgeHead']
    path = OUT/'KJV 283.vayforge'
    if (PACKAGE/'manifest.json').exists(): raise FileExistsError('Already published')
    if not path.exists():
        with sqlite3.connect((OLD/'KJV 282.vayforge').as_uri()+'?mode=ro',uri=True) as src, sqlite3.connect(path) as dest:
            src.backup(dest)
    project = ForgeProject(path)
    snapshot = read(OLD/'current-snapshot.json')
    assert snapshot['head']==parent_head==project.status()['head']
    snap = snapshot['snapshot']
    lex = read(PACKAGE/'lexicon.json')['entries']
    glossary = read(PACKAGE/'morphology.json')['glosses']
    quantities = read(PACKAGE/'quantities.json')
    entries = snap['language']['lexicon']
    template = next(entry for entry in entries if entry['label']=='kjv_three')
    for entry in entries:
        word = lex.get(entry['label'])
        if word and word.get('register')==VERSION:
            entry.update(headword=word['form'],pronunciation=word['roman'],etymology=word['origin'])
            entry['senses'][0]['definition']=word['meaning']
    for key,q in quantities.items():
        word=lex[key]
        entry=deepcopy(template)
        entry.update(id='kjv.lex.'+key,label=key,headword=q['form'],pronunciation=word['roman'],
                     etymology=q['evidence'],notes='Unta quantity '+q['value']+' / '+q['kind'],citations=[])
        entry['senses']=[dict(id='kjv.sense.'+key,definition=word['meaning'],status='draft',citations=[])]
        entries.append(entry)
    units=read(OUT/'complete-translation-ledger.json')['units']
    snap['wiki'].insert(0,dict(id='kjv283-unta',title='Unta quantities in the Bible',body=NOTE,ruleIds=[]))
    snap['decisions'].append(dict(id='kjv283-unta',status='draft',choice=NOTE,evidence='Author correction, Unta chart 2, sealed source verse analyses.'))
    snap['tests']=[t for t in snap['tests'] if not t['id'].startswith('kjv')]
    for u in units:
        snap['tests'].append(dict(id='kjv283.verse.'+u['id'],title='KJV 283 · '+u['reference'],
            ruleIds=[],paragraphs=[dict(text=u['text'],translation=u['source'],analysis=u['gloss']+'\nAnalysis: '+u['analysis']+'\n'+u['note'])]))
    delta=read(OUT/'language-delta.json')
    snap['research']['kjv283Unta']=delta
    st=project.replace_draft(snap,project.status()['generation'])
    st=project.commit('KJV 283 · Unta number words in both historical editions',st['generation'])
    write(OUT/'current-snapshot.json',dict(head=st['head'],snapshot=snap))
    for directory in (OUT,COMPACT):
        write(directory/'forge-reference.json',dict(project=str(path),branch='main',head=st['head'],parentHead=parent_head))
    manifest=dict(version=VERSION,policy='never-modernize',basePackage=PARENT.relative_to(ROOT).as_posix(),
        baseManifestSha256=digest(PARENT/'manifest.json'),baseForgeHead=parent_head,forgeHead=st['head'],
        compilerPath=(PACKAGE/'compiler.py').relative_to(ROOT).as_posix(),compilerSha256=digest(PACKAGE/'compiler.py'),
        files={p.name:digest(p) for p in PACKAGE.iterdir() if p.is_file() and p.name!='manifest.json'})
    write(PACKAGE/'manifest.json',manifest)
    registry=read(ROOT/'data/language/historical.json')
    assert not any(r['version']==VERSION for r in registry['registers'])
    registry['registers'].append(dict(version=VERSION,package=PACKAGE.relative_to(ROOT).as_posix(),
        manifestSha256=digest(PACKAGE/'manifest.json'),forgeHead=st['head'],policy='never-modernize',guide='docs/KJV_ARCHIVE.md'))
    write(ROOT/'data/language/historical.json',registry)
    verify_register(VERSION)
    style='<meta charset="utf-8"><style>body{max-width:1100px;margin:3em auto;font:18px/1.6 Georgia}td,th{padding:8px;text-align:left;border-bottom:1px solid #ddd}pre{white-space:pre-wrap}</style>'
    rows=''.join('<tr>'+''.join('<td>'+html.escape(str(v))+'</td>' for v in
                    (k,entry['roman'],glossary.get(k,''),entry['meaning']))+'</tr>' for k,entry in sorted(lex.items()))
    (OUT/'Dictionary.html').write_text(style+'<h1>KJV 283 · Historical dictionary</h1><table><tr><th>Key</th><th>Roman form</th><th>Gloss</th><th>Meaning</th></tr>'+rows+'</table>',encoding='utf8')
    wiki=NOTE+'\n\n'+(PARENT/'names.md').read_text(encoding='utf8')+'\n\n'+(PARENT/'grammar.md').read_text(encoding='utf8')
    (OUT/'Wiki.md').write_text(wiki,encoding='utf8')
    (OUT/'Wiki.html').write_text(style+'<h1>KJV 283 · Historical grammar and Unta</h1><pre>'+html.escape(wiki)+'</pre>',encoding='utf8')
    print('Registered',VERSION,st['head'],flush=True)


if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['prepare','publish'])
    args = parser.parse_args()
    (prepare if args.action=='prepare' else publish)()
