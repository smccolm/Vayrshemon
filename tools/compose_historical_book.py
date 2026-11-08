"""Compose an authored historical ledger in the approved four-column template.

Never translates, shrinks type, modifies its template, or overwrites a book.
"""
from copy import deepcopy
from pathlib import Path
import argparse
import json
import uuid

from tools.kjv_archive import ROOT, digest, read, write_new


def uid(prefix):
    return prefix + '.' + uuid.uuid4().hex


def texts(frame):
    return [''.join(r.get('sourceText', r.get('text', '')) for r in b['runs'])
            for b in frame['content']['document']['stories'][0]['blocks']]


def body(frame, paragraphs, font, literal, index):
    """Preserve approved body styles and explicit punctuation-font treatment."""
    from vayrshemon.session import utf16_length
    content = frame['content']
    doc = content['document']
    old = doc['stories'][0]['blocks'][0]['runs'][0]
    size = '50000000' if index == 0 else '22000000'
    main = deepcopy(next(s for s in doc['styles']
                         if s.get('fontId') == font.font_id
                         and s['fontSizeMicroPoints'] == size
                         and s['lineHeight'] == dict(mode='exact', microPoints='38000000')))
    fallback = deepcopy(main)
    fallback.update(styleId='style.archive-punctuation', fontId=literal.font_id)
    if index == 0:
        fallback['fontSizeMicroPoints'] = '22000000'
    # A previously composed edition already has this fallback style.
    # Replace its definition when rebuilding a frame instead of duplicating IDs.
    doc['styles'] = [s for s in doc['styles'] if s['styleId'] != fallback['styleId']] + [fallback]
    content['styleFeatures'][fallback['styleId']] = dict(kern=True, liga=True)
    if not any(f['fontId'] == literal.font_id for f in doc['fonts']):
        doc['fonts'].append(dict(fontId=literal.font_id, sha256=literal.sha256, faceIndex=0))
    blocks, characters, offset = [], [], 0
    for text in paragraphs:
        runs, chunks = [], []
        for char in text:
            punctuation = (not char.isspace() and
                           (ord(char) not in font.cmap or
                            (index >= 2 and (char in '·()+-[]{}/’“”‘' or ord(char) > 127))))
            style = fallback['styleId'] if punctuation else main['styleId']
            if punctuation and ord(char) not in literal.cmap:
                raise ValueError('UNSUPPORTED_PUNCTUATION: ' + repr(char))
            if chunks and chunks[-1][0] == style:
                chunks[-1][1] += char
            else:
                chunks.append([style, char])
        for style, chunk in chunks:
            if index < 2 and style == main['styleId']:
                run = dict(runId=uid('run'), languageId='language.vayrshemon', styleId=style,
                           type='legacy', normalization='none', sourceText=chunk,
                           sourceFontSha256=font.sha256,
                           mappingProfileRef=deepcopy(old.get('mappingProfileRef')) if index == 0 else None)
            else:
                run = dict(runId=uid('run'), languageId='language.en', styleId=style,
                           type='unicode', normalization='none', text=chunk)
            runs.append(run)
            end = offset + utf16_length(chunk)
            characters.append(dict(start=offset, end=end,
                                   attributes=dict(tracking=0, wordSpacing=0., baseline=0.)))
            offset = end
        blocks.append(dict(blockId=uid('block'), type='paragraph', direction='auto', runs=runs))
        offset += 1
    doc['stories'][0]['blocks'] = blocks
    content['characters'] = characters
    content['paragraphs'] = [dict(alignment='left', before=1., after=24., tabs=[]) for _ in paragraphs]


def geometry(page):
    return {k: v for k, v in page.items() if k not in ('pageId', 'name', 'frames')}


def frame_geometry(frame):
    return {k: frame[k] for k in ('x', 'y', 'width', 'height')}


def reusable_spreads(path, template_hash, engine, prototype):
    """Only reuse byte-verified, measured spreads from the same rendering setup."""
    path = Path(path)
    proof = read(path.parent / 'layout-validation.json')
    if proof['sha256'] != digest(path) or proof['templateSha256'] != template_hash:
        raise ValueError('REUSE_PROOF_HASH_MISMATCH')
    payload = read(path)
    # The language revision is provenance, not a rendering input: all four
    # compiled strings are compared before reusing a measured spread. Every
    # font/Qt/paint/typesetting fingerprint field still has to match exactly.
    def rendering_engine(value):
        return {k: v for k, v in value.items() if k != 'languageRevision'}
    if rendering_engine(payload['engine']) != rendering_engine(engine):
        raise ValueError('REUSE_ENGINE_MISMATCH')
    old = payload['state']
    for field in ('recipe', 'paint', 'styles', 'features', 'fontSources'):
        if old[field] != prototype[field]:
            raise ValueError('REUSE_FORMAT_MISMATCH: ' + field)
    if old['typesetting']['profiles'] != prototype['typesetting']['profiles']:
        raise ValueError('REUSE_TYPESETTING_MISMATCH')
    checks = {c['leftPage']: c for c in proof['checks']}
    result = {}
    for spread in read(path.parent / 'page-index.json')['spreads']:
        pair = old['pages'][spread['leftPage'] - 1:spread['rightPage']]
        columns = [texts(f) for p in pair for f in sorted(p['frames'], key=lambda f:int(f['x']))]
        if len(pair) != 2 or len(columns) != 4 or any(len(c) != len(spread['unitIds']) for c in columns):
            raise ValueError('REUSE_INDEX_MISMATCH')
        state = dict(old, pages=pair)
        check = {k:v for k,v in checks[spread['leftPage']].items() if k != 'leftPage'}
        result[spread['unitIds'][0]] = (spread['unitIds'], columns, state, check)
    return result


def compose(ledger_path, snapshot_path, target, template=None, reuse=None, preflight=False):
    from PySide6.QtWidgets import QApplication
    from vayrshemon.file_api import FileSession
    from vayrshemon import language, pages, reading, paragraph_alignment, page_numbering
    from vayrshemon.numbering_contracts import new_document_defaults

    target = Path(target)
    if target.exists() or (target.parent / 'FROZEN.json').exists():
        raise ValueError('REFUSING_TO_OVERWRITE_EDITION')
    template = Path(template or ROOT / 'Saves/Black on white.vay')
    template_hash = digest(template)
    ledger, head = read(ledger_path), read(snapshot_path)
    units = ledger['units']
    app = QApplication.instance() or QApplication([])
    session = FileSession(ROOT, source_fonts=False, recovery=False)
    session.remember = lambda path: None
    try:
        session.open(template, advance_revision=False)
        original = session.capture()
        assert len(original['pages']) == 2
        prototype = deepcopy(original)
        prototype['documentId'] = uid('document')
        prototype['language'] = language.initial()
        prototype['revision'] = 0
        book = deepcopy(prototype)
        book['pages'] = []
        book['typesetting']['frames'] = {}
        book['activeFrameId'] = ''
        edition_status = (ledger['editionLabel'] + ' ') if ledger.get('editionLabel') else (
            'working KJV ' if ledger.get('status') == 'incomplete' else 'frozen KJV ')
        book['title'] = ledger['book'] + ' · ' + edition_status + ledger['languageVersion']
        language.append_revision(book['language'], head['snapshot']['language'],
                                 edition_status.strip() + ' · ' + head['head'])
        book['pageNumbering'] = new_document_defaults()
        script = session.fonts.faces['font:' + reading.SCRIPT_SHA + ':0']
        roman, literal = reading.font(session, 'transliteration'), reading.font(session, 'literal')
        fonts = [script, roman, roman, roman]
        fields = ['text', 'text', 'gloss', 'source']
        reusable = reusable_spreads(reuse, template_hash, session.fingerprint(), prototype) if reuse else {}
        reused = 0

        def candidate(group):
            state = deepcopy(prototype)
            frames = [f for p in state['pages'] for f in sorted(p['frames'], key=lambda f: int(f['x']))]
            for index, (frame, font, field) in enumerate(zip(frames, fonts, fields)):
                body(frame, [u[field] for u in group], font, literal, index)
                frame['content']['document']['documentId'] = book['documentId']
                frame['name'] = ['Vayrshemon', 'Transliteration 7', 'Construction gloss',
                                 ledger.get('sourceLabel', 'KJV source')][index]
            state['activeFrameId'] = frames[0]['frameId']
            session._restore(state)
            session._state = session.capture()
            session.invalidate_composition()
            session._undo = []
            session._redo = []
            paragraph_alignment.align(session)
            rows, bearing = [], 0.
            for page in state['pages']:
                report = pages.inspect(session, page_id=page['pageId'], max_glyphs=100000)
                if report.get('truncated') or any(g['missingGlyph'] for g in report['glyphs']):
                    raise ValueError('MISSING_GLYPH_OR_TRUNCATED_REPORT')
                for frame in sorted(report['frames'], key=lambda f: f['rect'][0]):
                    x, y, width, height = frame['rect']
                    starts, seen = [], set()
                    for line in frame['layout']['lines']:
                        bx, by, bw, bh = line['advanceBounds']
                        excess = max(0, bx + bw - x - width)
                        bearing = max(bearing, excess)
                        if excess > 1.0 or by + bh > y + height + .05:
                            raise ValueError(f'BODY_OVERFLOW: {frame["name"]}; horizontal={excess:.3f}px; '
                                             f'vertical={max(0, by + bh - y - height):.3f}px; '
                                             f'line={line}')
                        if line['blockId'] not in seen:
                            starts.append(line['baseline'])
                            seen.add(line['blockId'])
                    rows.append(starts)
            if any(len(r) != len(group) for r in rows):
                raise ValueError('PARAGRAPH_COUNT_MISMATCH')
            error = max(max(r) - min(r) for r in zip(*rows)) / (96 / 72)
            if error > .02:
                raise ValueError('PARAGRAPH_ALIGNMENT: ' + str(error))
            return session.capture(), dict(maxBaselineErrorPt=error, maxHorizontalBearingExcessPx=bearing)

        checks, index, position = [], [], 0
        while position < len(units):
            best = None
            previous = reusable.get(units[position]['id'])
            if previous:
                ids, columns, cached, check = previous
                group = units[position:position + len(ids)]
                if ids == [u['id'] for u in group] and columns == [[u[f] for u in group] for f in fields]:
                    best = len(ids), cached, check
                    reused += 1
            for count in ([] if best else range(1, min(12, len(units) - position) + 1)):
                if units[position + count - 1]['chapter'] != units[position]['chapter']:
                    break
                try:
                    state, result = candidate(units[position:position + count])
                    best = count, state, result
                except ValueError as error:
                    if not str(error).startswith(('BODY_OVERFLOW', 'PARAGRAPH_ALIGNMENT', 'PARAGRAPH_COUNT')):
                        raise
                    if best is None:
                        raise ValueError(f'UNIT_REQUIRES_AUTHORED_SPLIT: {units[position]["reference"]}: {error}') from error
                    break
            count, state, result = best
            group = units[position:position + count]
            left = len(book['pages']) + 1
            for page in state['pages']:
                copy = deepcopy(page)
                copy['pageId'] = uid('page')
                copy['name'] = f'{group[0]["reference"]} — {group[-1]["reference"]}'
                for frame in copy['frames']:
                    old_id = frame['frameId']
                    frame['frameId'] = uid('frame')
                    frame['content']['document']['documentId'] = book['documentId']
                    if old_id in state['typesetting']['frames']:
                        book['typesetting']['frames'][frame['frameId']] = deepcopy(state['typesetting']['frames'][old_id])
                    if not book['activeFrameId']:
                        book['activeFrameId'] = frame['frameId']
                book['pages'].append(copy)
            index.append(dict(leftPage=left, rightPage=left + 1, references=[u['reference'] for u in group],
                              unitIds=[u['id'] for u in group]))
            checks.append(dict(leftPage=left, **result))
            position += count
            print(f'{ledger["book"]}: {position}/{len(units)} units; {len(book["pages"])} pages', flush=True)
            app.processEvents()

        for i, page in enumerate(book['pages']):
            assert geometry(page) == geometry(original['pages'][i % 2])
            assert [frame_geometry(f) for f in page['frames']] == [frame_geometry(f) for f in original['pages'][i % 2]['frames']]
        assert book['paint'] == original['paint'] and book['recipe'] == original['recipe']
        if preflight:
            return dict(book=ledger['book'],pages=len(book['pages']),units=len(units),
                        preflightOnly=True,checks=checks,index=index)
        session._restore(book)
        session._state = session.capture()
        session.invalidate_composition()
        page_numbering.ensure_fonts(session)
        session._undo = []
        session._redo = []
        numbering = []
        # Check both placements while this page's measured composition is hot.
        # A book-wide pass per mode evicts the bounded page cache and shapes
        # every page twice, although view mode changes only the derived folio.
        for page in session.state['pages']:
            for mode in ('one', 'two'):
                with page_numbering.scope(session, mode):
                    placement = page_numbering.placement(session, page)
                    if placement['status'] != 'placed':
                        raise ValueError('NUMBERING_NOT_PLACED: ' + str(placement))
                    numbering.append(placement)
        target.parent.mkdir(parents=True, exist_ok=True)
        session.save(target, preview_mode='two')
        before = session.capture()
        session.open(target, advance_revision=False)
        assert session.capture() == before
        actual = [[], [], [], []]
        for i in range(0, len(book['pages']), 2):
            frames = [f for p in session.state['pages'][i:i+2] for f in sorted(p['frames'], key=lambda f: int(f['x']))]
            for j, frame in enumerate(frames):
                actual[j].extend(texts(frame))
        for j, field in enumerate(fields):
            assert actual[j] == [u[field] for u in units], 'ROUNDTRIP_COLUMN_MISMATCH: ' + field
        proofs = target.parent / 'Proofs'
        proofs.mkdir(exist_ok=True)
        for number in sorted({0, 1, len(book['pages']) - 2, len(book['pages']) - 1}):
            page = session.state['pages'][number]
            pages.render(session, page_id=page['pageId'], path=proofs / f'page-{number+1:03d}.png',
                         mode='mono', dpi=96, page_mode='two')
        assert digest(template) == template_hash
        report = dict(book=ledger['book'], pages=len(book['pages']), spreads=len(index), units=len(units),
                      allFourColumnsMatchLedger=True, saveReopenIdentical=True, templateUnchanged=True,
                      geometryAndPaintPreserved=True, templateSha256=template_hash, sha256=digest(target),
                      maxBaselineErrorPt=max(c['maxBaselineErrorPt'] for c in checks),
                      maxHorizontalBearingExcessPx=max(c['maxHorizontalBearingExcessPx'] for c in checks),
                      horizontalBearingTolerancePx=1., missingGlyphs=0, verticalOverset=0,
                      numberingCheckedInBothModes=True, checks=checks,
                      reusedMeasuredSpreads=reused,
                      inkDisclaimer='Approved decorative ink overhang is not a zero ink-collision claim.')
        write_new(target.parent / 'layout-validation.json', report)
        write_new(target.parent / 'page-index.json', dict(pages=len(book['pages']), spreads=index))
        write_new(target.parent / 'numbering-validation.json', numbering)
        return report
    finally:
        session.finish()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ledger', type=Path, required=True)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--reuse', type=Path, help='Previously measured native book with adjacent validation and page-index files.')
    parser.add_argument('--preflight', action='store_true', help='Measure the complete layout without writing a native file.')
    args = parser.parse_args()
    print(json.dumps(compose(args.ledger, args.snapshot, args.output, reuse=args.reuse,preflight=args.preflight), indent=2))
