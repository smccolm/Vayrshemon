"""Compile the authored four-column working text of The Prince."""
import argparse
from bisect import bisect_right
from hashlib import sha256
from itertools import chain
import json
from pathlib import Path
import re
from shutil import copy2
from tempfile import TemporaryDirectory

from tools.editorial_language import EditorialLanguage, ROOT
from tools.shakespeare_endin import check_clean
from tools.shakespeare_lexicon import lexical_entries
from tools.unta_language import quantity, semantic_key
from vayrshemon.archive_language import base


BOOK = ROOT / 'Saves/The Prince - Four-Column Progressive Edition'
WORK = BOOK / 'Working'
SOURCE = ROOT / 'Inputs/Sources/The Prince.txt'
PARENT = ROOT / 'Saves/Archive/Shakespeare Project 0.13'
HEAD = '824145664cfc5080a3ccdcfd85cd0fdc82ea2eee70f5dab9722418b9b688afa4'
SOURCE_DIGEST = 'd0e37c0096d18ab466d242bc79de7b039966a8a00407d7e12328c7cfd422ba7d'

# These names identify the people and places in Marriott's text. The author
# and the dedicatee have separate keys from Shakespeare's dramatic names.
NAMES = {
    'nikolo_makyaveli': ('nikolo Makyaveli', 'Niccolò Machiavelli', 'Author of The Prince.'),
    'du_ke_mariyot': ('dabelyu Ke Mariyot', 'W. K. Marriott', 'English translator. The initials are rendered by sound.'),
    'lorentso_medichi': ('lorentso', 'Lorenzo', 'Medici dedicatee of the book.'),
    'piero_medichi': ('piyero', 'Piero', 'Father named in the dedicatory address.'),
    'medichi_house': ('mediÑi', 'Medici', 'Family named in the dedicatory address.'),
    'frantsesko_sfortsa': ('frantsesko Sfortsa', 'Francesco Sforza', 'Milanese ruler in chapter I.'),
    'yulyo_pontiff': ('yulyo', 'Julius', 'Pope named in chapter II, distinct from the Roman dictator.'),
    'valentino_borgia': ('valentino', 'Valentino', 'Ducal title used for Cesare Borgia in the appended narrative.'),
    'vitellotso_vitelli': ('vitelotso Viteli', 'Vitellozzo Vitelli', 'Person named in the first appended title.'),
    'oliveroto_fermo': ('oliveroto da Fermo', 'Oliverotto da Fermo', 'Person named in the first appended title.'),
    'pagolo_orsini': ('pagolo', 'Pagolo', 'Lord named in the first appended title.'),
    'gravina_orsini': ('di Gravina Orsini', 'di Gravina Orsini', 'Ducal designation in the first appended title.'),
    'kastruchyo_kastrakani': ('kastruÑo Kastrakani', 'Castruccio Castracani', 'Subject of the appended Life.'),
    'lukka_city': ('luka', 'Lucca', 'City of Castruccio in the appended Life.'),
}
SENSES = {
    'chapter_book': (['book', 'part'], 'chapter', 'noun', 'A numbered division of a written book.'),
    'republic_civic': (['people', 'rule'], 'republic', 'noun', 'A polity governed collectively, distinguished from rule by a prince.'),
    'trusted_secretary': (['secret', 'counsellor'], 'secretary', 'noun', 'A prince’s confidential minister in chapter XXII.'),
    'balanced_clause': (['balance', 'speech'], 'balanced-period', 'noun', 'A polished, balanced rhetorical sentence.'),
}


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def compile_opening(through=None):
    raw = SOURCE.read_bytes()
    assert sha256(raw).hexdigest() == SOURCE_DIGEST
    lines = raw.decode('utf-8-sig').splitlines()
    source = ' '.join(line.strip() for line in lines if line.strip())
    paragraph_starts = set()
    line_offsets = []
    line_numbers = []
    offset = 0
    for i, line in enumerate(lines):
        if line.strip():
            line_offsets.append(offset)
            line_numbers.append(i + 1)
            if i == 0 or not lines[i-1].strip() or line.startswith('CHAPTER '):
                paragraph_starts.add(offset)
            offset += len(line.strip()) + 1
    language = EditorialLanguage(PARENT / 'Language')
    extra_path = WORK / 'vocabulary.json'
    extra = json.loads(extra_path.read_text(encoding='utf-8')) if extra_path.exists() else {}
    additions, glosses = lexical_entries(language, NAMES | extra.get('names', {}),
                                          SENSES | extra.get('senses', {}),
                                          places={'lukka_city', *extra.get('places', [])})
    for key, entry in additions.items():
        assert key not in language.lexicon and set(entry['form']) <= language.letters | {' '}
    language.lexicon.update(additions)
    language.glosses.update(glosses)
    units = []
    cursor = 0
    section = None
    passage_number = part = 0
    sections = sorted((WORK / 'sections').glob('*.txt'))
    manuscripts = [WORK / 'opening.txt', *(p for p in sections if through is None or int(p.stem) <= through)]
    for row in chain.from_iterable(p.read_text(encoding='utf-8').splitlines() for p in manuscripts):
        if not row.strip():
            continue
        if row.startswith('['):
            section = row[1:-1]
            continue
        end_text, analysis = row.split(' | ')
        if end_text.startswith('+ '):
            # A smaller aligned clause within the same source passage.
            assert units and units[-1]['chapter'] == section
            end_text = end_text[2:]
            part += 1
        else:
            passage_number += 1
            part = 1
        stop = source.index(end_text, cursor) + len(end_text)
        passage = source[cursor:stop]
        assert not any(cursor < start < stop for start in paragraph_starts), (end_text, passage)
        assert stop == len(source) or source[stop] == ' ', end_text
        values = []
        def figure(match):
            value = int(match[1])
            values.append(value)
            key = semantic_key(value, notation='digits')
            q = quantity(value, notation='digits')
            if key not in language.lexicon:
                additions[key] = dict(form=q['form'], roman=language.reading(q['spokenForm']),
                                      pos='numeral', meaning='Exact numeral ' + str(value),
                                      origin='Unta positional figures from chart 2.')
                language.lexicon[key] = additions[key]
                language.glosses[key] = str(value)
            assert language.lexicon[key]['form'] == q['form']
            return key
        analysis = re.sub(r'#(\d+)', figure, analysis)
        def spoken(match):
            n = int(match[1])
            den = int(match[2] or 1)
            kind = 'fraction' if match[2] else {'o':'ordinal', 'x':'times', 'f':'fold', '':'cardinal'}[match[3]]
            key = semantic_key(n,kind,den)
            q = quantity(n,kind,den)
            if key not in language.lexicon:
                additions[key] = dict(form=q['form'],roman=language.reading(q['spokenForm']),
                                      pos='numeral',meaning=f"Exact {kind} quantity {q['value']}.",
                                      origin='Reviewed Unta spoken construction from chart 2.',
                                      numericKind=kind,numericValue=q['value'],numericNotation='words')
                language.lexicon[key] = additions[key]
                language.glosses[key] = q['value'] + ('(ord.)' if kind=='ordinal' else '')
            assert language.lexicon[key]['form'] == q['form']
            return key
        analysis = re.sub(r'@(\d+)(?:/(\d+))?([oxf]?)', spoken, analysis)
        roman_heading = re.match(r'CHAPTER ([IVXL]+)\.', passage)
        expected = []
        if roman_heading:
            roman = roman_heading[1]
            digits = [{'I':1,'V':5,'X':10,'L':50}[c] for c in roman]
            expected.append(sum(-v if v < following else v for v, following in zip(digits,digits[1:]+[0])))
        expected.extend(int(n) for n in re.findall(r'\d+',passage))
        assert values == expected, (passage, values, expected)
        # Prefer the corrected native reading whenever the checkpoint supplies one.
        analysis = re.sub(r'[a-z_]+', lambda m: 'drama_native_' + m[0]
                          if 'drama_native_' + m[0] in language.lexicon else m[0], analysis)
        suffix = '' if part == 1 else f'.{part}'
        uid = f'prince-{passage_number:04d}{suffix}'
        reference_title = {
            'Description of the Methods Adopted by the Duke Valentino': 'Duke Valentino',
            'The Life of Castruccio Castracani of Lucca': 'Life of Castruccio',
        }.get(section, section)
        omitted = analysis == '[…]'
        units.append(dict(id=uid, reference=f'{reference_title} · {passage_number}{suffix}', chapter=section,
                          source='[…]' if omitted else passage,
                          sourceOffsets=[cursor,stop], analysis=analysis,
                          lineStart=line_numbers[bisect_right(line_offsets,cursor)-1],
                          lineEnd=line_numbers[bisect_right(line_offsets,stop-1)-1],
                          continuesParagraph=bool(units and cursor not in paragraph_starts
                                                  and units[-1]['chapter']==section
                                                  and section != 'Title and contents')))
        if omitted:
            units[-1]['editorialTreatment'] = 'Omission'
        cursor = stop + 1
    assert ' '.join(source[a:b] for a,b in (u['sourceOffsets'] for u in units)) == source[:cursor-1]
    assert all(u['source'] == source[slice(*u['sourceOffsets'])] for u in units if 'editorialTreatment' not in u)
    next_text = source[cursor:]
    next_heading = re.match(r'CHAPTER ([IVXL]+)\.', next_text)
    compiled = language.compile_units(units)
    for u in compiled:
        if u.get('editorialTreatment') == 'Omission':
            u['text'] = u['gloss'] = '[…]'
        check_clean(u, language)
    ledger = dict(book='The Prince', editionLabel=('Four-column progressive working edition' if next_text
                                                  else 'Four-column progressive edition'),
                  sourceLabel='W. K. Marriott · English source', languageVersion='0.14',
                  sourcePath=SOURCE.relative_to(ROOT).as_posix(), sourceSha256=SOURCE_DIGEST,
                  parentLanguageHead=HEAD, status='incomplete' if next_text else 'translated', units=compiled,
                  sourceOffsetBasis='Unicode code points in source order, with stripped nonblank lines joined by one space; end exclusive.',
                  nextPassage='Chapter '+next_heading[1] if next_heading else next_text[:100],
                  sourceWords=len(source.split()),
                  coveredSourceWords=sum(len(source[slice(*u['sourceOffsets'])].split()) for u in compiled),
                  translatedSourceWords=sum(len(u['source'].split()) for u in compiled if 'editorialTreatment' not in u))
    if not next_text:
        chapters = re.findall(r'^CHAPTER ([IVXL]+)\.', '\n'.join(lines), re.M)[-26:]
        expected_sections = ['Title and contents', 'Dedication',
                             *('Chapter ' + c for c in chapters),
                             'Description of the Methods Adopted by the Duke Valentino',
                             'The Life of Castruccio Castracani of Lucca']
        assert len(set(chapters)) == 26
        assert list(dict.fromkeys(u['chapter'] for u in compiled)) == expected_sections
        assert compiled[-1]['sourceOffsets'][1] == len(source)
        assert ledger['coveredSourceWords'] == ledger['sourceWords']
        ledger['omittedUnits'] = [u['id'] for u in compiled if 'editorialTreatment' in u]
        if ledger['omittedUnits']:
            ledger['status'] = 'translated with omissions'
        ledger['editorialNotes'] = 'Working/editorial-notes.txt'
    return ledger, additions


def prepare(stage, through=None):
    stage.mkdir(parents=True, exist_ok=True)
    ledger, additions = compile_opening(through)
    parent = json.loads((PARENT / 'current-snapshot.json').read_text(encoding='utf-8'))
    assert parent['head'] == HEAD
    language = parent['snapshot']['language']
    sid = 'prince.marriott.source'
    language['sources'].append(dict(base(sid, 'The Prince · W. K. Marriott', None, '', status='draft'),
                                    kind='other', path=ledger['sourcePath'], sha256=SOURCE_DIGEST))
    for key, entry in additions.items():
        eid = 'prince.lex.' + key
        language['lexicon'].append(dict(base(eid,key,sid,entry['origin'],status='draft'),
            headword=entry['form'],orthographyId='thimfora-79',pronunciation=entry['roman'],ipa='',
            partOfSpeech=entry['pos'],senses=[dict(id=eid+'.sense',definition=entry['meaning'],status='draft',
            citations=[dict(sourceId=sid,locator=key)])],variants=[],etymology=entry['origin'],
            exampleIds=[],audioLinks=[]))
    draft_hash = sha256(json.dumps(language, ensure_ascii=False, sort_keys=True,
                                   separators=(',',':')).encode()).hexdigest()
    write(stage/'snapshot.json', dict(head='working-language-'+draft_hash, snapshot=dict(language=language)))
    write(stage/'ledger.json', ledger)
    write(stage/'dictionary-additions.json', dict(parent=HEAD, entries=additions))
    return ledger


def publish_verified(stage):
    """Install a verified extension of the currently issued working manuscript."""
    from tools.compose_historical_book import texts
    from vayrshemon.native_storage import unpack
    name = 'The Prince - Four-Column Progressive Edition.vay'
    load = lambda p: json.loads(p.read_text(encoding='utf-8'))
    digest = lambda p: sha256(p.read_bytes()).hexdigest()
    ledger = load(stage/'ledger.json')
    previous = load(WORK/'ledger.json')
    assert SOURCE_DIGEST == ledger['sourceSha256'] == previous['sourceSha256'] == digest(SOURCE)
    assert HEAD == ledger['parentLanguageHead'] == previous['parentLanguageHead']
    if previous['nextPassage']:
        assert len(ledger['units']) > len(previous['units'])
        for prior, current in zip(previous['units'], ledger['units']):
            assert all(prior[k] == current[k] for k in ('id','sourceOffsets','source','text','gloss'))
    else:
        assert not ledger['nextPassage'] and ledger == compile_opening()[0]
    report = load(stage/'layout-validation.json')
    assert report['allFourColumnsMatchLedger'] and report['saveReopenIdentical']
    assert report['templateUnchanged'] and report['geometryAndPaintPreserved']
    assert not report['missingGlyphs'] and not report['verticalOverset']
    assert report['units'] == len(ledger['units'])
    placements = load(stage/'numbering-validation.json')
    expected_folios = {(page, mode) for page in range(1, report['pages'] + 1)
                       for mode in ('one', 'two')}
    assert len(placements) == len(expected_folios)
    assert {(p['pageNumber'], p['pageMode']) for p in placements if p['status'] == 'placed'} == expected_folios
    assert digest(stage/name) == report['sha256']
    assert digest(BOOK/name) == load(WORK/'layout-validation.json')['sha256']
    state = unpack(load(stage/name))['state']
    assert len(state['pages']) == report['pages']
    index = load(stage/'page-index.json')
    assert [i for spread in index['spreads'] for i in spread['unitIds']] == [u['id'] for u in ledger['units']]
    positions = {u['id']: i for i, u in enumerate(ledger['units'])}
    assert len(positions) == len(ledger['units'])
    for spread in index['spreads']:
        frames = [f for p in state['pages'][spread['leftPage']-1:spread['rightPage']]
                  for f in sorted(p['frames'],key=lambda f:int(f['x']))]
        assert len(frames)==4
        start = positions[spread['unitIds'][0]]
        group = ledger['units'][start:start+len(spread['unitIds'])]
        for f,k in zip(frames, ('text','text','gloss','source')):
            assert texts(f)==[u[k] for u in group]
    files = [(stage/f, WORK/f) for f in ('ledger.json','dictionary-additions.json','layout-validation.json','page-index.json')]
    if (stage/'editorial-notes.txt').exists():
        files.append((stage/'editorial-notes.txt', WORK/'editorial-notes.txt'))
    files.append((stage/name, BOOK/name))
    with TemporaryDirectory(prefix='prince-publication-', dir=stage) as staging:
        temp = Path(staging)
        original = {}
        for source, target in files:
            original[target] = digest(target)
            copy2(target, temp/('old-'+target.name))
            copy2(source, temp/target.name)
            assert digest(temp/target.name)==digest(source)
        changed = []
        try:
            for source, target in files:
                assert original[target]==digest(target), target
                (temp/target.name).replace(target)
                changed.append(target)
            assert all(digest(s)==digest(t) for s,t in files)
        except BaseException:
            for target in reversed(changed):
                (temp/('old-'+target.name)).replace(target)
            raise
    print(f"Installed {report['pages']} verified pages.")
    if ledger['nextPassage']:
        print('Next passage:', ledger['nextPassage'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', required=True, type=Path)
    parser.add_argument('--through', type=int, help='Last numbered manuscript section to include.')
    parser.add_argument('--compose', action='store_true')
    parser.add_argument('--reuse', type=Path, help='Previously verified manuscript with its layout receipts.')
    parser.add_argument('--publish', action='store_true', help='Install the previously composed stage in Saves.')
    args = parser.parse_args()
    if args.publish:
        publish_verified(args.stage)
        raise SystemExit(0)
    ledger = prepare(args.stage, args.through)
    if args.compose:
        from tools.compose_historical_book import compose
        compose(args.stage/'ledger.json', args.stage/'snapshot.json',
                args.stage/'The Prince - Four-Column Progressive Edition.vay', reuse=args.reuse)
    print(ledger['translatedSourceWords'], 'source words translated in', len(ledger['units']), 'aligned units.')
