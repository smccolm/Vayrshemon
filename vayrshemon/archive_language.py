"""Reproducible, local-only M5 seed. Source files are verified, never rewritten.

Archive text is loaded on explicit import; it is not distributed in the repo.
Attested means present in that source, not endorsed as the latest language.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
from xml.etree import ElementTree as ET
from tools.m0.docx import extract_docx, NS
from .language import empty_data, validate_data, tokens

SOURCES = {
    'chart-original': ('Versions Best/Translation Chart.docx', '3d9bdfa6ba9ff395e8366d58cb56eca0ca943ce89f9a467f6f763431f63cf23d'),
    'chart-1': ('Versions Best/Translation Chart 1.docx', '99481c69c04a978ab6247fed44b5b474c7f8894108e6839085087317832c2d4c'),
    'terms': ('Versions Best/Language Terms.docx', 'b1604a5c55341c8c55bc041c9ad8ffea676f58626647a17259f3ca601d383e06'),
    'hadthem': ('Versions Rough/Vayrshemon Hadthem - Verb Tense.docx', 'abf56af6f003a43f8659ddc4f78e6c1385aac1670650dd1c9da0df4f528c205b'),
    'polished': ('Versions Best/Polished Examples.docx', '74cb6248e3edbdc0be1af412d5f1840ac1de1fc54451c9187c18ef4be60fefb5'),
}


def base(key, label, source, locator, status='attested', notes=''):
    return dict(id=key, label=label, status=status, citations=[dict(sourceId=source, locator=locator)] if source else [], notes=notes)


def seed(root):
    root = Path(root); data = empty_data(); extracted = {}
    for key, (path, sha) in SOURCES.items():
        file = root/'Inputs'/path
        if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest() != sha: raise ValueError('LANGUAGE_ARCHIVE_SOURCE_CHANGED: '+path)
        doc = extract_docx(file)
        if doc['sourceSha256'] != sha: raise ValueError('LANGUAGE_ARCHIVE_SOURCE_CHANGED: '+path)
        extracted[key] = doc
        data['sources'].append(dict(base(key, path, None, ''), path=path, sha256=sha, kind='docx'))
    mapping_path = root/'data/orthography/thimfora-79.json'
    mapping = json.loads(mapping_path.read_text(encoding='utf-8'))
    data['sources'].append(dict(base('mapping-79', 'Thimfora 79 chart transcription', None, '', 'uncertain'), path='data/orthography/thimfora-79.json', sha256=hashlib.sha256(mapping_path.read_bytes()).hexdigest(), kind='mapping'))
    symbols = []
    for item in mapping['inventory']:
        forms = [dict(form=e['form'], scalar=e['scalar'], transliteration=e['transliteration']) for e in mapping['entries'] if e['symbolId']==item['symbolId']]
        symbols.append(dict(id=item['symbolId'], name=item['nameTranscription'], kind=item['kind'], status='uncertain' if item.get('transliterationStatus')=='unresolved' else 'attested', forms=forms))
    data['orthographies'].append(dict(base('thimfora-79', 'Thimfora 79 · chart 2', 'mapping-79', 'inventory and entries', 'uncertain', 'Chart transcription confidence is retained in the cited mapping. No normalization or case folding.'), version=mapping['revision'], normalization='none', fontSha256s=mapping['fontSha256s'], symbols=symbols, unresolvedScalars=[e['scalar'] for e in mapping['entries'] if e['status']=='unresolved']))
    data['inputLayouts'].append(dict(base('palette-79', 'Thimfora 79 symbol palette', 'mapping-79', 'mapped scalar slots', 'attested', 'Semantic symbol/form keys, not a claim to reproduce the historical physical keyboard.'), orthographyId='thimfora-79', keys=[dict(key=s['id']+'.'+f['form'], text=chr(f['scalar'])) for s in symbols for f in s['forms']]))
    data['transliterations'].append(dict(base('chart-transliteration', 'Chart transliteration · trace preserves ambiguous forms', 'mapping-79', 'entries.transliteration', 'uncertain'), orthographyId='thimfora-79', unknownPolicy='preserve', mappings=[dict(source=chr(e['scalar']), target=e['transliteration']) for e in mapping['entries'] if e['transliteration']]))
    for key in ('chart-original', 'chart-1', 'terms'):
        doc = extracted[key]; xml = ET.fromstring(doc['sourceParts']['word/document.xml']['xml'])
        for ti, table in enumerate(xml.findall('.//w:tbl', NS)):
            for ri, row in enumerate(table.findall('w:tr', NS)):
                cells = row.findall('w:tc', NS)
                if len(cells)==1: continue  # Table title, not a lexical row.
                if len(cells) not in (3,4): raise ValueError('UNEXPECTED_LEXICAL_TABLE_COLUMNS')
                texts = ['\n'.join(''.join(n.text or '' for n in p.findall('.//w:t', NS)) for p in cell.findall('w:p', NS)) for cell in cells]
                definition = '\n'.join(texts[:-2]);headword,pronunciation=texts[-2:]
                if not definition.strip(): continue
                fonts = [sorted({v for el in cell.findall('.//w:rFonts', NS) for k,v in el.attrib.items() if k.rsplit('}',1)[-1] in ('ascii','hAnsi')}) for cell in cells]
                rid = f'{key}.t{ti}.r{ri}'; citation = dict(sourceId=key, locator=f'table {ti}, row {ri}; {len(cells)} cells: English'+(' / function' if len(cells)==4 else '')+' / script / transliteration (zero-based)')
                pos = re.search(r'\(([^)]*)\)', definition)
                data['lexicon'].append(dict(base(rid, definition.split('\n')[0], key, citation['locator'], 'attested' if headword else 'uncertain', 'Original cells and direct font-family hints retained. Exact historical face/orthography unresolved. Parallel chart versions are not merged.'),
                    headword=headword, orthographyId=None, pronunciation=pronunciation, ipa='', partOfSpeech=pos.group(1) if pos else '',
                    senses=[dict(id=rid+'.sense1', definition=definition, status='attested' if headword else 'uncertain', citations=[citation])],
                    variants=[dict(text=headword, script='archived script slots', sourceFonts=fonts[-2], note='Verbatim script cell'), dict(text=pronunciation, script='archived transliteration slots', sourceFonts=fonts[-1], note='Verbatim transliteration cell; not IPA')], etymology='', exampleIds=[], audioLinks=[]))
    def paragraph(key, index):
        return ''.join(t.get('text', '') for r in extracted[key]['paragraphs'][index]['runs'] for t in r['tokens'] if t['kind']=='t')
    for i, (si, gi, ei) in enumerate(((0,2,4), (17,19,21))):
        text = paragraph('polished', si)
        r = dict(base(f'polished.{i+1}', f'Polished example {i+1}', 'polished', f'paragraphs {si}, {gi}, {ei} (zero-based)'), text=text, translation=paragraph('polished',ei), transliteration=paragraph('polished',si+1), rawGloss=paragraph('polished',gi), orthographyId=None, sourceFonts=extracted['polished']['directFontNames'], tokens=tokens(text), offsetUnit='unicode-scalar')
        # Explicit word-level glosses from paragraph 2. No invented lexical IDs.
        if i==0:
            glosses = ['[b>n]·Many-accusative', 'I(singular)', 'be(now,simple)', 'One-accusative', 'we(singular)', 'be(now,simple)']
            if len(r['tokens']) != len(glosses): raise ValueError('POLISHED_TOKENIZATION_CHANGED')
            for t,g in zip(r['tokens'],glosses): t.update(morphemes=[t['surface']], glosses=[g], status='attested')
        data['corpus'].append(r)
    tense_ids = []
    for name, suffix, p, time, distance in [('past-general','iz',6,'past','agnostic'),('present','ow',10,'present','present'),('future-general','at',13,'future','agnostic'),('past-distant','diz',16,'past','distant'),('past-immediate','riz',19,'past','immediate'),('future-immediate','dat',23,'future','immediate'),('future-distant','rat',26,'future','distant')]:
        rid = 'hadthem.'+name; tense_ids.append(rid)
        disputed = name in ('future-immediate','future-distant')
        data['morphology'].append(dict(base(rid, name, 'hadthem', f'paragraph {p}; examples 58–63', 'disputed' if disputed else 'attested', 'Future table and paired script/transliteration example rows disagree; no winner selected.' if disputed else ''), kind='inflection', form=suffix, features=dict(tense=time, distance=distance), entryIds=[], cells=[]))
    data['grammar'].append(dict(base('hadthem.tense', 'Tense and aspect ordering', 'hadthem', 'paragraphs 1–2 and 58–63', 'disputed'), topic='tense', statement=paragraph('hadthem',1)+'\n'+paragraph('hadthem',2), morphologyIds=tense_ids, exampleIds=[], alternatives=[dict(statement='Immediate/distant future table: -dat / -rat. Script examples: -rat / -dat. Transliteration examples: -dat / -rat. Retain all readings pending adjudication.', status='disputed', citations=[dict(sourceId='hadthem',locator='paragraphs 23, 26, 58–59, 62–63')])]))
    data['grammar'].append(dict(base('polished.pronouns', 'Pronouns attested in the polished gloss', 'polished', 'paragraphs 0, 2, 17, 19', 'attested'), topic='pronouns', statement='The archived gloss explicitly identifies I(singular), we(singular), and it(inanimate, singular, subjective). The first two have token-level gloss alignment in polished.1; no full pronoun paradigm is inferred.', morphologyIds=[], exampleIds=['polished.1','polished.2'], alternatives=[]))
    data['grammar'].append(dict(base('polished.construction', 'Nominal conversions and clause construction', 'polished', 'paragraphs 2 and 19', 'uncertain'), topic='construction', statement='Retain the complete source glosses, including [b>n], [v>n], case labels, passive/perfect and modifier descriptions. Unsegmented forms remain unresolved rather than receiving guessed morpheme boundaries.', morphologyIds=[], exampleIds=['polished.1','polished.2'], alternatives=[]))
    digits = sorted([s for s in symbols if s['kind']=='digit'], key=lambda s:int(s['id'].rsplit('.',1)[1]))
    data['numberConventions'].append(dict(base('unta.chart-2', 'Unta · chart 2 digit reading', 'mapping-79', '12 numeral values and names', 'uncertain', 'Unta digits are attested. Minus, radix point and parenthesized repetends are editorial display conventions, not an asserted historical notation.'), digits=[chr(s['forms'][0]['scalar']) for s in digits], digitNames=[s['name'] for s in digits], radixPoint='.', minus='-', repeatOpen='(', repeatClose=')', readingPolicy='positional-unverified'))
    data['numberConventions'].append(dict(base('base12.ascii', 'Base 12 · ASCII 0–9 A B', None, '', 'draft', 'Editorial interchange convention. A=ten, B=eleven; parentheses denote an exact repeating fraction.'), digits=list('0123456789AB'), digitNames=[str(i) for i in range(12)], radixPoint='.', minus='-', repeatOpen='(', repeatClose=')', readingPolicy='digits-only'))
    validate_data(data)
    return data
