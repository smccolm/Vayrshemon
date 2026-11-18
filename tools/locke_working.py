"""Build Locke's progressive edition from the supplied text and authored clause analyses."""
import argparse
from collections import Counter
from hashlib import sha256
import json
import os
from pathlib import Path
import re
from shutil import copy2
from tempfile import TemporaryDirectory

from tools.editorial_language import EditorialLanguage, ROOT
from tools.prince_working import HEAD, NAMES, PARENT, SENSES, WORK as PRINCE
from tools.shakespeare_endin import check_clean
from tools.shakespeare_lexicon import lexical_entries
from tools.unta_language import quantity, semantic_key
from vayrshemon.archive_language import base

TITLE = 'Two Treatises of Government'
BOOK = ROOT / 'Saves' / (TITLE + ' - Four-Column Progressive Edition')
WORK = BOOK / 'Working'
SOURCE = ROOT / 'Inputs/Sources/John Locke - Two Treatises of Government.txt'
SOURCE_HASH = 'f4d420fdb452129f94a34b2a8a5723a1e1a5b3496e269881563d46723c956c6a'


def read(path):
    return json.loads(path.read_bytes())


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf8')


def install(stage):
    """Replace the working volume only after its save/reopen checks pass."""
    name = BOOK.name+'.vay'
    ledger = read(stage/'ledger.json')
    layout = read(stage/'layout-validation.json')
    index = read(stage/'page-index.json')
    assert ledger['sourceSha256']==SOURCE_HASH==sha256(SOURCE.read_bytes()).hexdigest()
    assert layout['allFourColumnsMatchLedger'] and layout['saveReopenIdentical']
    assert layout['geometryAndPaintPreserved'] and not layout['missingGlyphs'] and not layout['verticalOverset']
    assert layout['sha256']==sha256((stage/name).read_bytes()).hexdigest()
    assert [uid for s in index['spreads'] for uid in s['unitIds']]==[u['id'] for u in ledger['units']]
    if (BOOK/name).exists():
        if sha256((BOOK/name).read_bytes()).hexdigest()!=read(WORK/'layout-validation.json')['sha256']:
            raise ValueError('The on-disk manuscript has been edited since compilation.')
        if read(WORK/'ledger.json')['translatedSourceWords']>ledger['translatedSourceWords']:
            raise ValueError('Refusing to shorten the manuscript.')
    targets=[(stage/f,WORK/f) for f in ('ledger.json','layout-validation.json','page-index.json')]
    if (stage/'dictionary-additions.json').is_file():
        targets.append((stage/'dictionary-additions.json', WORK/'dictionary-additions.json'))
    targets.append((stage/name,BOOK/name))
    with TemporaryDirectory(dir=BOOK) as folder:
        temp=Path(folder)
        for src,dst in targets:
            copy2(src,temp/dst.name)
            if dst.exists():
                copy2(dst,temp/('old-'+dst.name))
        installed=[]
        try:
            for _,dst in targets:
                (temp/dst.name).replace(dst)
                installed.append(dst)
        except OSError:
            for dst in reversed(installed):
                previous=temp/('old-'+dst.name)
                if previous.exists():
                    previous.replace(dst)
                else:
                    dst.unlink()
            raise
    print('Installed',layout['pages'],'pages and',layout['units'],'aligned passages.')


def chapter_titles():
    return (WORK / 'chapter-titles.txt').read_text(encoding='utf8').splitlines()


def roman(text):
    values = [{'I':1, 'V':5, 'X':10}[letter] for letter in text]
    return sum(-a if a < b else a for a,b in zip(values, values[1:]+[0]))


def build(stage, compose_pages=False, reuse=None):
    raw = SOURCE.read_bytes()
    assert sha256(raw).hexdigest() == SOURCE_HASH
    source = raw.decode('utf8')
    lines = source.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1]+len(line))
    language = EditorialLanguage(PARENT / 'Language')
    prior = read(PRINCE / 'vocabulary.json')
    inherited, labels = lexical_entries(language, NAMES | prior['names'], SENSES | prior['senses'], prior['places'])
    published = read(PRINCE / 'dictionary-additions.json')
    assert published['parent'] == HEAD
    assert all(entry['form'] == published['entries'][key]['form'] for key,entry in inherited.items())
    language.lexicon.update(inherited)
    language.glosses.update(labels)
    vocab = read(WORK / 'vocabulary.json')
    # Some inherited biblical entries have a native reading but no English
    # construction label. Keep their provenance keys out of the reading column.
    for key, entry in language.lexicon.items():
        if key.startswith('kjv_') and key not in language.glosses:
            word = key.removeprefix('kjv_')
            if '_' not in word:
                language.glosses[key] = word.capitalize() if entry['pos'] == 'proper' else word
    language.glosses.update(vocab['constructionLabels'])
    additions, glosses = lexical_entries(language, vocab['names'], vocab['senses'], vocab.get('places', []))
    index_path = ROOT / 'Saves/KJV Bible v0.10-kjv.285/section-index.json'
    if sha256(index_path.read_bytes()).hexdigest() != '4ee26d924f3946ab0c3be90192e51c02a3bd19b691423b302cf3df3d4f8922a5':
        raise ValueError('Unexpected Bible title index')
    titles_by_book = {item['section']: item for item in read(index_path)}
    for key, book_name in vocab.get('biblicalTitles', {}).items():
        title = titles_by_book[book_name]
        additions[key] = dict(form=title['titleSlots'], roman=title['titleRoman'], pos='proper',
                              meaning=f"The book of {book_name}, as cited by Locke.", semanticId='lex.' + key,
                              origin='Book title from the sealed 0.10-kjv.285 Bible.',
                              usageScope='later-standard', status='authored', historicalForms=[])
        glosses[key] = book_name
    if set(additions) & language.lexicon.keys():
        raise ValueError('A Locke dictionary entry shadows an earlier entry')
    language.lexicon.update(additions)
    language.glosses.update(glosses)

    def number(match):
        mark, digits, denominator, ordinal = match.groups()
        value = int(digits)
        notation = 'digits' if mark == '#' else 'words'
        kind = 'fraction' if denominator else 'ordinal' if ordinal else 'cardinal'
        divisor = int(denominator or 1)
        q = quantity(value, kind, divisor, notation=notation)
        key = semantic_key(value, kind, divisor, notation=notation)
        label = digits + ('/' + denominator if denominator else '') + ('(ord.)' if ordinal else '')
        if key not in language.lexicon:
            entry = dict(form=q['form'], roman=language.reading(q['spokenForm']), pos='numeral',
                         meaning='Unta ' + label,
                         origin='Chart 2 Unta number system.')
            additions[key] = language.lexicon[key] = entry
            language.glosses[key] = label
        assert language.lexicon[key]['form'] == q['form']
        return key

    authored = {}
    for path in sorted((WORK / 'Analyses').glob('*.txt')):
        for record in path.read_text(encoding='utf8').splitlines():
            if not record.strip():
                continue
            line, anchor, analysis = record.split(' | ')
            authored.setdefault(int(line), []).append((anchor, analysis))
    titles = chapter_titles()
    assert len(titles)==30
    units = []
    book = 1
    section = 'Title'
    for i, line in enumerate(lines, 1):
        text = line.rstrip('\r\n')
        if not text.strip():
            continue
        if i == 7: section = 'Preface'
        if i == 20: section = 'Contents · Book I'
        if i == 66: section = 'Contents · Book II'
        if i == 146: section = 'First Treatise'
        if i == 564:
            book, section = 2, 'Second Treatise'
        if text.startswith('CHAP. '):
            section = ('First' if book==1 else 'Second') + ' Treatise · Chapter ' + text.split()[1].rstrip('.')
        records = authored.get(i)
        if records is None:
            heading = re.fullmatch(r'(?:CHAP\.|Chap\.) ([IVX]+)\.(.*)', text)
            page = re.fullmatch(r'p\. (\d+)\.', text)
            if heading:
                if text.startswith('CHAP.') and not any(j>i for j in authored):
                    break
                n = roman(heading[1])
                second = section.endswith('Book II') or book == 2
                label = titles[(11 if second else 0)+n-1] if heading[2].strip() else ''
                records = [('$', ('chapter_book #'+str(n)+'. '+label).strip())]
            elif page:
                records = [('$', 'book_leaf #'+page[1]+'.')]
            else:
                break
        cursor = 0
        for j,(anchor, analysis) in enumerate(records,1):
            if anchor != '$' and anchor not in text[cursor:]:
                raise ValueError((i,anchor,'source anchor not found'))
            end = len(text) if anchor == '$' else text.index(anchor,cursor)+len(anchor)
            if end < len(text) and not text[end].isspace():
                raise ValueError((i,anchor,'ends inside a word'))
            assert cursor < end
            clause = text[cursor:end]
            analysis = re.sub(r'([#@])(\d+)(?:/(\d+))?(o?)',number,analysis)
            analysis = re.sub(r'[a-z_]+',lambda m:'drama_native_'+m[0] if 'drama_native_'+m[0] in language.lexicon else m[0],analysis)
            units.append(dict(id=f'locke-{i:04d}.{j}',chapter=section,reference=f'{section} · {i}.{j}',
                              source=clause, sourceOffsets=[offsets[i-1]+cursor,offsets[i-1]+end],
                              analysis=analysis,continuesParagraph=j>1))
            cursor=end
            while cursor<len(text) and text[cursor].isspace():
                cursor+=1
        if cursor!=len(text):
            raise ValueError((i,'untranslated tail',text[cursor:]))
    unknown={}
    for unit in units:
        for key in re.findall(r'[a-z_]+',re.sub(r':[a-z]+','',unit['analysis'])):
            if key not in language.lexicon and key not in language.possessors:
                unknown.setdefault(key,unit['id'])
    if unknown:
        raise ValueError('Missing keys: '+str(unknown))
    errors = []
    for unit in units:
        try:
            language.compile(unit['analysis'])
        except ValueError as err:
            errors.append(f"{unit['id']} {unit['analysis']}: {err}")
    if errors:
        raise ValueError('\n'.join(errors))
    compiled = language.compile_units(units)
    end = 0
    for unit in compiled:
        check_clean(unit,language)
        numeric_source = unit['source']
        if unit['id'].startswith('locke-0348.') and 'Gen. 111. 16.' in numeric_source:
            # The parallel witness reads the Roman chapter numeral iii (Book I, §73).
            numeric_source = numeric_source.replace('Gen. 111. 16.', 'Gen. 3. 16.')
        source_figures = Counter(re.findall(r'\d+', numeric_source))
        if unit['id'].startswith('locke-0676.') and '1/•000' in numeric_source:
            source_figures = Counter(re.findall(r'\d+', numeric_source.replace('1/•000', '1/1000')))
        translated_figures = Counter(re.findall(r'\d+', unit['gloss']))
        if missing := source_figures - translated_figures:
            raise ValueError(f"{unit['id']}: missing source numerals {dict(missing)}")
        a,b=unit['sourceOffsets']
        assert not source[end:a].strip() and source[a:b]==unit['source']
        end=b
    assert not (set(authored)-{int(u['id'][6:10]) for u in compiled}), 'Manuscript has a non-contiguous authored section'
    complete = not source[end:].strip()
    ledger = dict(book=TITLE,editionLabel='Four-column progressive edition' if complete else 'Four-column progressive working edition',
                  status='translated' if complete else 'incomplete',languageVersion='0.14',sourceLabel='John Locke · English source',
                  sourceSha256=SOURCE_HASH,sourcePath=SOURCE.relative_to(ROOT).as_posix(),parentLanguageHead=HEAD,
                  sourceOffsetBasis='Unicode code points in the exact UTF-8 file, end exclusive.',
                  sourceWords=len(source.split()),translatedSourceWords=len(source[:end].split()),
                  nextPassage=source[end:].lstrip()[:160],units=compiled)
    stage.mkdir(parents=True,exist_ok=True)
    write(stage/'ledger.json',ledger)
    named_entries = vocab['names'].keys() | vocab['senses'].keys() | vocab['biblicalTitles'].keys()
    used_entries = {key for unit in compiled for key in unit['keys']}
    write(stage/'dictionary-additions.json', dict(
        parent=HEAD, sourceSha256=SOURCE_HASH,
        entries={key: additions[key] for key in sorted(named_entries & used_entries)}))
    print(ledger['status'],ledger['translatedSourceWords'],'/',ledger['sourceWords'],len(units),'units',flush=True)
    if compose_pages:
        from tools.compose_historical_book import compose
        parent=read(PARENT/'current-snapshot.json')
        assert parent['head']==HEAD
        lang=parent['snapshot']['language']
        sid='locke.1690.source'
        lang['sources'].append(dict(base(sid,TITLE,None,'',status='draft'),kind='other',path=ledger['sourcePath'],sha256=SOURCE_HASH))
        used={k for u in compiled for k in u['keys']}
        for key in sorted(used & (inherited.keys()|additions.keys())):
            entry=language.lexicon[key]
            eid='locke.lex.'+key
            lang['lexicon'].append(dict(base(eid,key,sid,entry['origin'],status='draft'),
                headword=entry['form'],orthographyId='thimfora-79',pronunciation=entry['roman'],ipa='',
                partOfSpeech=entry['pos'],senses=[dict(id=eid+'.sense',definition=entry['meaning'],status='draft',citations=[dict(sourceId=sid,locator=key)])],
                variants=[],etymology=entry['origin'],exampleIds=[],audioLinks=[]))
        label=sha256(json.dumps(lang,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
        write(stage/'snapshot.json',dict(head='working-language-'+label,snapshot=dict(language=lang)))
        extra=Path(os.environ['WINDIR'])/'Fonts/malgun.ttf' if any('〈' in u['source'] or '〉' in u['source'] for u in compiled) else None
        compose(stage/'ledger.json',stage/'snapshot.json',stage/(BOOK.name+'.vay'),reuse=reuse,source_fallback=extra)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',required=True,type=Path)
    parser.add_argument('--compose',action='store_true')
    parser.add_argument('--reuse',type=Path,help='Reuse verified spreads with identical text, fonts, and layout.')
    parser.add_argument('--install',action='store_true')
    args=parser.parse_args()
    if args.install:
        install(args.stage)
    else:
        build(args.stage,args.compose,args.reuse)
