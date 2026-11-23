"""Build a native progressive Dampier from consecutive, source-anchored analyses."""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import os
import re
from pathlib import Path
from shutil import copy2
from tempfile import TemporaryDirectory

from tools.boyle_working import WORK as BOYLE
from tools.compose_historical_book import compose
from tools.leviathan_working import number_gloss
from tools.paradise_lost_working import ROOT, read, write, digest, load_language
from tools.shakespeare_endin import check_clean
from tools.shakespeare_lexicon import lexical_entries
from tools.unta_language import quantity, semantic_key
from vayrshemon.archive_language import base

TITLE = 'A New Voyage Round the World'
EDITION = TITLE + ' - Four-Column Progressive Edition'
BOOK = ROOT / 'Saves' / EDITION
WORK = BOOK / 'Working'
SOURCE = ROOT / 'Inputs/Sources' / ('William Dampier - ' + TITLE + '.txt')
SOURCE_HASH = '64cf3c4181bdf8fc463b8b532166dea398d5833294c0d99451b2032a8b1cc23d'


def inventory():
    if digest(SOURCE) != SOURCE_HASH:
        raise ValueError('Dampier source changed; review the line anchors')
    starts = {1: 'Title', 15: 'Dedication', 25: 'Preface', 43: 'Contents',
              87: 'World map', 89: 'Introduction', 2177: 'Errata', 2257: 'Bookseller’s catalogue'}
    rows = []
    for n, text in enumerate(SOURCE.read_text(encoding='utf-8-sig').splitlines(), 1):
        if not text.strip():
            continue
        chapter = re.fullmatch(r'CHAP\.? ([IVX]+)\.', text.strip())
        if chapter:
            starts[n] = 'Chapter ' + chapter[1]
        if n in starts:
            section = starts[n]
        rows.append(dict(line=n, section=section, text=text))
    assert sum(s.startswith('Chapter ') for s in starts.values()) == 20
    return rows


def source_language(chapter_number=None):
    language, inherited = load_language()
    parent = read(BOYLE / 'vocabulary.json')
    entries, labels = lexical_entries(language, parent['names'], parent['senses'])
    language.lexicon.update(entries)
    language.glosses.update(labels)
    inherited.update(entries)
    additions = {}
    division_path = WORK/'compound-word-division.json'
    division = read(division_path) if division_path.exists() else {}
    for path in [WORK/'vocabulary.json', *sorted((WORK/'Vocabulary').glob('*.json'))]:
        optional = False
        if chapter_number is not None and path.parent.name == 'Vocabulary':
            match = re.match(r'(\d+)(?:-(\d+))?',path.name)
            first = int(match[1])
            last = int(match[2] or first)
            optional = first != 3 and not first <= chapter_number <= last
        vocab = read(path)
        if optional:
            # An independent chapter check can use finished entries in other
            # regional drafts while an unrelated term is still being authored.
            available = language.lexicon.keys() | vocab.get('names', {}).keys()
            vocab['senses'] = {k:v for k,v in vocab.get('senses', {}).items() if set(v[0]) <= available}
        try:
            words, labels = lexical_entries(language, vocab.get('names', {}), vocab.get('senses', {}), vocab.get('places', []))
        except KeyError as exc:
            raise ValueError(f'{path.name}: unknown derivation root {exc}') from exc
        if words.keys() & language.lexicon.keys():
            raise ValueError(f'Duplicate vocabulary in {path}: {words.keys() & language.lexicon.keys()}')
        for key in words.keys() & division.keys():
            roots = words[key]['derivationKeys']
            if roots != division[key]:
                raise ValueError('Review compound word division for ' + key)
            root_entries = language.lexicon | words
            form = ' '.join(root_entries[root]['form'] for root in roots)
            words[key].update(form=form, roman=language.reading(form),
                              orthographicNote='Open compound written as its constituent native words.')
        language.lexicon.update(words)
        language.glosses.update(labels)
        additions.update(words)
    return language, inherited, additions


def editorial_reading(original, note):
    spans = note.get('spans')
    if spans is None:
        return note['reading'], len(original.split())
    if not spans:
        raise ValueError('Empty replacement list for a marked reading')
    parts = []
    previous = count = 0
    for span in spans:
        start, end, replacement = span['start'], span['end'], span['replacement']
        if not (previous <= start < end <= len(original)
                and (start == 0 or original[start - 1].isspace())
                and (end == len(original) or original[end].isspace())
                and not original[start].isspace() and not original[end - 1].isspace()
                and replacement.startswith('[') and replacement.endswith(']')):
            raise ValueError('Invalid editorial span in ' + note['originalSha256'])
        parts.extend((original[previous:start], replacement))
        count += len(original[start:end].split())
        previous = end
    parts.append(original[previous:])
    return ''.join(parts), count


def covered_words(unit):
    return unit.get('sourceWordCount', len(unit['source'].split()))


def compile_records(rows, paths, language, additions):
    units, readings = [], []
    counts = Counter()
    cursor = offset = 0
    for path in paths:
        for record_number, line in enumerate(path.read_text(encoding='utf-8-sig').splitlines(), 1):
            if not line.strip():
                continue
            location, closing, analysis = line.split(' | ')
            r = rows[cursor]
            assert r['line'] == int(location), (location, r['line'])
            text = r['text']
            if closing == '$':
                end = len(text)
            else:
                # Editor anchors may use a single space for an original tab,
                # doubled space or layout break. Save the source slice verbatim.
                pattern = r'\s+'.join(re.escape(word) for word in closing.split())
                match = re.compile(pattern).search(text, offset)
                if match is None:
                    raise ValueError(f'{path.name}:{record_number}: closing anchor {closing!r} absent after {offset} on source line {location}')
                end = match.end()
            assert end > offset and (end == len(text) or text[end].isspace()), (path.name, record_number, line)
            counts[r['line']] += 1
            uid = f"dampier.{r['line']:04}.{counts[r['line']]:03}"

            def numeral(m):
                value = int(m[2])
                kind = 'ordinal' if m[3] else 'cardinal'
                notation = 'digits' if m[1] == '#' else 'words'
                q = quantity(value, kind, notation=notation)
                k = semantic_key(value, kind, notation=notation)
                if k not in language.lexicon:
                    additions[k] = language.lexicon[k] = dict(form=q['form'], roman=language.reading(q['spokenForm']),
                        pos='numeral', meaning=f'Unta {kind} {value}', origin='Unta chart 2')
                assert language.lexicon[k]['form'] == q['form']
                language.glosses[k] = number_gloss(value, kind == 'ordinal', notation)
                readings.append(dict(unit=uid, value=value, kind=kind, notation=notation, key=k))
                return k

            pending = analysis == '[pending]'
            analysis = '—' if pending else re.sub(r'([@#])(\d+)(o?)', numeral, analysis)
            analysis = re.sub(r'(?<!:)\b[a-z_]+\b', lambda m: 'drama_native_' + m[0]
                              if 'drama_native_' + m[0] in language.lexicon else m[0], analysis)
            try:
                language.compile(analysis)
            except ValueError as exc:
                raise ValueError(f'{path.name}:{record_number} (source {location}): {exc}') from exc
            units.append(dict(id=uid, chapter=r['section'], reference=f"{r['section']} · {location}.{counts[r['line']]}",
                              sourceLine=r['line'], sourceOffsets=[offset, end], source=text[offset:end],
                              analysis=analysis, continuesParagraph=bool(offset)))
            if pending:
                units[-1]['translationPending'] = True
            offset = end
            while offset < len(text) and text[offset].isspace():
                offset += 1
            if offset == len(text):
                cursor += 1
                offset = 0
    compiled = language.compile_units(units)
    for u in compiled:
        check_clean(u, language)
    prefix = [r['text'] for r in rows[:cursor]]
    if offset:
        prefix.append(rows[cursor]['text'][:offset])
    assert ' '.join(' '.join(prefix).split()) == ' '.join(' '.join(u['source'] for u in compiled).split())
    notes_path = WORK/'source-treatments.json'
    if notes_path.exists():
        notes = read(notes_path)
        for u in compiled:
            note = notes.get(u['id'])
            if note is None:
                continue
            original = u['source']
            if hashlib.sha256(original.encode('utf-8')).hexdigest() != note['originalSha256']:
                raise ValueError('Source treatment does not match original passage: ' + u['id'])
            u['sourceWordCount'] = len(original.split())
            u['sourceTreatment'] = 'editorial summary'
            u['source'], u['summarizedSourceWords'] = editorial_reading(original, note)
        if cursor == len(rows) and len(rows) == len(inventory()):
            if set(notes) != {u['id'] for u in compiled if 'sourceTreatment' in u}:
                raise ValueError('Some source treatment records have no corresponding passage')
    return compiled, readings, cursor, offset


def check_section(section):
    rows = [row for row in inventory() if row['section'] == section]
    if not rows:
        raise ValueError('Unknown source section: ' + section)
    paths = []
    for path in sorted((WORK/'Analyses').glob('*.txt')):
        first = next((line for line in path.read_text(encoding='utf-8-sig').splitlines() if line.strip()), '')
        if first and rows[0]['line'] <= int(first.split(' | ')[0]) <= rows[-1]['line']:
            paths.append(path)
    # Later chapters refer back to people and places already named in earlier
    # ones. Resolve them with the same vocabulary used by the whole-book build.
    chapters = list(dict.fromkeys(r['section'] for r in inventory() if r['section'].startswith('Chapter ')))
    language, _, additions = source_language(chapters.index(section) + 1 if section in chapters else 21)
    units, _, cursor, offset = compile_records(rows, paths, language, additions)
    covered = sum(u.get('sourceWordCount',len(u['source'].split())) for u in units if not u.get('translationPending'))
    total = sum(len(r['text'].split()) for r in rows)
    print(f'{section}: {covered}/{total} source words accounted for, {len(units)} aligned passages; next line '
          f'{rows[cursor]["line"] if cursor < len(rows) else None}, character {offset}')


def build(stage):
    rows = inventory()
    language, inherited, additions = source_language()
    compiled, readings, cursor, offset = compile_records(rows, sorted((WORK/'Analyses').glob('*.txt')), language, additions)
    pending = [u for u in compiled if u.get('translationPending')]
    complete = cursor == len(rows) and not pending
    ledger = dict(book=TITLE, languageVersion='0.14', editionLabel='Four-column progressive edition' +
                  ('' if complete else ' · in progress'), status='complete' if complete else 'incomplete',
                  sourceLabel='Dampier · English (bracketed editorial summaries where marked)' if any('sourceTreatment' in u for u in compiled) else 'Dampier · supplied English', sourceSha256=SOURCE_HASH,
                  sourceCharacters=len(SOURCE.read_bytes().decode('utf-8-sig')),
                  sourceWords=sum(len(r['text'].split()) for r in rows),
                  translatedSourceWords=sum(covered_words(u) - u.get('summarizedSourceWords', 0) for u in compiled if not u.get('translationPending')),
                  sourceWordsInSummaryPassages=sum(u['summarizedSourceWords'] for u in compiled if 'sourceTreatment' in u),
                  sourceWordsAccountedFor=sum(u.get('sourceWordCount',len(u['source'].split())) for u in compiled if not u.get('translationPending')),
                  pendingUnits=[u['id'] for u in pending],
                  nextSourceLine=None if cursor == len(rows) else rows[cursor]['line'], nextSourceOffset=offset, units=compiled)
    write(stage/'ledger.json', ledger)
    write(stage/'unta-readings.json', readings)
    write(stage/'dictionary-additions.json', dict(parent='Boyle and earlier issued vocabulary', entries=additions))
    write(stage/'source-inventory.json', dict(sourceSha256=SOURCE_HASH, rows=rows))
    previous = read(BOYLE/'snapshot.json')
    lang = deepcopy(previous['snapshot']['language'])
    sid = 'dampier.voyage.source'
    lang['sources'].append(dict(base(sid, TITLE, None, '', status='draft'),kind='other',
                                path=SOURCE.relative_to(ROOT).as_posix(),sha256=SOURCE_HASH))
    existing = {e['id'].removeprefix('boyle.lex.') for e in lang['lexicon'] if e['id'].startswith('boyle.lex.')}
    needed = {k for u in compiled for k in u['keys']} - existing
    for k, e in sorted((inherited | additions).items()):
        if k not in needed:
            continue
        eid = 'dampier.lex.' + k
        lang['lexicon'].append(dict(base(eid,k,sid,e['origin'],status='draft'),headword=e['form'],
            orthographyId='thimfora-79', pronunciation=e['roman'],ipa='',partOfSpeech=e['pos'],
            senses=[dict(id=eid+'.sense',definition=e['meaning'],status='draft',citations=[dict(sourceId=sid,locator=k)])],
            variants=[],etymology=e['origin'],exampleIds=[],audioLinks=[]))
    write(stage/'snapshot.json', dict(head='dampier-'+digest(stage/'ledger.json'),snapshot=dict(language=lang)))
    if complete:
        assert ledger['sourceWords'] == ledger['sourceWordsAccountedFor'] == (
            ledger['translatedSourceWords'] + ledger['sourceWordsInSummaryPassages'])
    print(f"{len(compiled)} passages; {ledger['sourceWordsAccountedFor']}/{ledger['sourceWords']} source words accounted for; next line {ledger['nextSourceLine']}",flush=True)
    return ledger


def authored_inputs():
    paths = [WORK/'vocabulary.json', WORK/'compound-word-division.json', WORK/'source-treatments.json',
             *sorted((WORK/'Analyses').glob('*.txt')), *sorted((WORK/'Vocabulary').glob('*.json'))]
    return {path: digest(path) for path in paths if path.is_file()}


def publish(stage, ledger, measured_chapters=None, inputs=None, folio_workers=1):
    name = EDITION + '.vay'
    target = BOOK/name
    reuse = None
    previous_hash = None
    if target.exists():
        old = read(WORK/'ledger.json')
        previous_hash = read(WORK/'layout-validation.json')['sha256']
        if digest(target) != previous_hash:
            raise ValueError('The native manuscript has been edited since its last build. Reconcile those edits first.')
        old_end = old['units'][-1]
        new_end = ledger['units'][-1]
        if (new_end['sourceLine'], new_end['sourceOffsets'][1]) < (old_end['sourceLine'], old_end['sourceOffsets'][1]):
            raise ValueError('The proposed edition ends before the current edition.')
        previous = stage/'previous'
        previous.mkdir()
        reuse = previous/name
        copy2(target,reuse)
        for n in ('layout-validation.json','page-index.json'):
            copy2(WORK/n,previous/n)
    signs = Path(os.environ['WINDIR']) / 'Fonts/malgun.ttf' if any(
        '〈' in u['source'] or '〉' in u['source'] for u in ledger['units']) else None
    measured = sorted((p for p in measured_chapters.glob('*/chapter.vay')
                       if p.with_name('layout-validation.json').is_file() and p.with_name('page-index.json').is_file()),
                      key=lambda p:p.stat().st_mtime) if measured_chapters else []
    report = compose(stage/'ledger.json',stage/'snapshot.json',stage/name,reuse=reuse,source_fallback=signs,
                     additional_reuse=measured, remeasure_incompatible=True, folio_workers=folio_workers)
    assert report['allFourColumnsMatchLedger'] and report['saveReopenIdentical']
    assert not report['missingGlyphs'] and not report['verticalOverset']
    page_for = {uid: [spread['leftPage'], spread['rightPage']] for spread in read(stage/'page-index.json')['spreads']
                for uid in spread['unitIds']}
    section_counts = {}
    source_rows = inventory()
    for r in source_rows:
        section_counts.setdefault(r['section'], dict(suppliedWords=0, directTranslationWords=0,
                                                     wordsInSummaryPassages=0, alignedPassages=0))
        section_counts[r['section']]['suppliedWords'] += len(r['text'].split())
    for u in ledger['units']:
        sec = section_counts[u['chapter']]
        sec['alignedPassages'] += 1
        if not u.get('translationPending'):
            summarized = u.get('summarizedSourceWords', 0)
            sec['wordsInSummaryPassages'] += summarized
            sec['directTranslationWords'] += covered_words(u) - summarized
    if ledger['status'] == 'complete':
        assert all(s['suppliedWords'] == s['directTranslationWords'] + s['wordsInSummaryPassages']
                   for s in section_counts.values())
    write(stage/'translation-status.json', dict(
        book=TITLE, status=ledger['status'], publicationSha256=report['sha256'],
        pages=report['pages'], alignedPassages=report['units'],
        suppliedCharacters=ledger['sourceCharacters'], suppliedWords=ledger['sourceWords'],
        translatedWords=ledger['translatedSourceWords'], wordsAccountedFor=ledger['sourceWordsAccountedFor'],
        sourceWordsInSummaryPassages=ledger['sourceWordsInSummaryPassages'], sections=section_counts,
        editorialSummaries=[dict(unit=u['id'],sourceLine=u['sourceLine'],sourceOffsets=u['sourceOffsets'],
                                 sourceWords=u['sourceWordCount'],summarizedSourceWords=u['summarizedSourceWords'],
                                 pages=page_for[u['id']])
                            for u in ledger['units'] if u.get('sourceTreatment')],
        lastSection=ledger['units'][-1]['chapter'], nextSourceLine=ledger['nextSourceLine'],
        nextSourceOffset=ledger['nextSourceOffset'],
        untranslatedWithinPublishedPages=[dict(unit=u['id'], sourceLine=u['sourceLine'], sourceOffsets=u['sourceOffsets'],
                                               words=len(u['source'].split()), pages=page_for[u['id']])
                                         for u in ledger['units'] if u.get('translationPending')]))
    proofs = WORK/'Proofs'
    proofs.mkdir(exist_ok=True)
    updates = [(path, WORK/path.name) for path in stage.glob('*.json')]
    updates.extend((path, proofs/path.name) for path in (stage/'Proofs').glob('*.png'))
    stale = [path for path in proofs.glob('page-*.png') if not (stage/'Proofs'/path.name).is_file()]
    backups = stage/'rollback'
    backups.mkdir()
    if (digest(target) if target.exists() else None) != previous_hash:
        raise ValueError('The native manuscript changed during composition.')
    if inputs is not None and authored_inputs() != inputs:
        if measured_chapters:
            checkpoint = measured_chapters / ('full-' + report['sha256'][:12])
            checkpoint.mkdir(exist_ok=True)
            for filename in ('layout-validation.json','page-index.json'):
                copy2(stage/filename,checkpoint/filename)
            (stage/name).replace(checkpoint/'chapter.vay')
        raise ValueError('The authored translation changed during composition. Recompile before publishing.')
    applied = []
    try:
        for source, dest in updates:
            backup = backups/dest.name if dest.exists() else None
            if backup:
                copy2(dest, backup)
            source.replace(dest)
            applied.append((dest, backup))
        for dest in stale:
            dest.replace(backups/dest.name)
            applied.append((dest, backups/dest.name))
        (stage/name).replace(target)
    except OSError:
        for dest, backup in reversed(applied):
            if backup:
                backup.replace(dest)
            else:
                dest.unlink(missing_ok=True)
        raise
    print(f"{report['pages']} native pages verified",flush=True)


if __name__ == '__main__':
    cli = argparse.ArgumentParser()
    cli.add_argument('--compose',action='store_true')
    cli.add_argument('--measured-chapters',type=Path,help='Directory of independently measured chapter editions to reuse after validating their hashes and four columns.')
    cli.add_argument('--folio-workers',type=int,choices=range(1,9),default=4,
                     help='Number of processes reopening the final native book to check folio placements.')
    cli.add_argument('--check-section',help='Check the authored prefix of one named source section independently.')
    args = cli.parse_args()
    if args.check_section:
        check_section(args.check_section)
        raise SystemExit(0)
    (ROOT/'.local').mkdir(exist_ok=True)
    with TemporaryDirectory(dir=ROOT/'.local') as tmp:
        stage = Path(tmp)
        inputs = authored_inputs()
        ledger = build(stage)
        if args.compose:
            publish(stage, ledger, args.measured_chapters, inputs=inputs, folio_workers=args.folio_workers)
