"""Compose an authored historical ledger in the approved four-column template.

Never translates, shrinks type, modifies its template, or overwrites a book.
"""
from copy import deepcopy
from pathlib import Path
from hashlib import sha256
import argparse
import json
import uuid

from tools.kjv_archive import ROOT, digest, read, write_new


def uid(prefix):
    return prefix + '.' + uuid.uuid4().hex


def texts(frame):
    return [''.join(r.get('sourceText', r.get('text', '')) for r in b['runs'])
            for b in frame['content']['document']['stories'][0]['blocks']]


def column_text(unit, field):
    """Tree connectors are presentation; keep the source and translation unaltered."""
    return unit.get('hierarchyPrefix', '') + unit[field]


def mixed_persian_reading(text):
    return '\u2028' in text and any('\u0600' <= c <= '\u06ff' for c in text) and any(c.isascii() and c.isalpha() for c in text)


def body(frame, paragraphs, font, literal, index, extra_font=None, prefixes=None, other_fonts=(), tracking=None,
         mixed_source_ltr=False):
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
    tree_style = dict(fallback, styleId='style.archive-tree', fontSizeMicroPoints='12000000')
    if prefixes and any(prefixes):
        doc['styles'] = [s for s in doc['styles'] if s['styleId'] != tree_style['styleId']] + [tree_style]
        content['styleFeatures'][tree_style['styleId']] = dict(kern=True, liga=True)
    if not any(f['fontId'] == literal.font_id for f in doc['fonts']):
        doc['fonts'].append(dict(fontId=literal.font_id, sha256=literal.sha256, faceIndex=0))
    source_styles = []
    for number, face in enumerate(([extra_font] if extra_font else []) + list(other_fonts)):
        style_id = 'style.source-signs' if number == 0 else f'style.source-signs-{number + 1}'
        extra_style = dict(fallback, styleId=style_id, fontId=face.font_id)
        doc['styles'] = [s for s in doc['styles'] if s['styleId'] != extra_style['styleId']] + [extra_style]
        content['styleFeatures'][extra_style['styleId']] = dict(kern=True,liga=True)
        if not any(f['fontId'] == face.font_id for f in doc['fonts']):
            doc['fonts'].append(dict(fontId=face.font_id, sha256=face.sha256, faceIndex=0))
        source_styles.append((face.cmap, style_id))
    blocks, characters, offset = [], [], 0
    for paragraph_index, text in enumerate(paragraphs):
        prefix_length = len(prefixes[paragraph_index]) if prefixes else 0
        runs, chunks = [], []
        for char_index, char in enumerate(text):
            punctuation = (char_index < prefix_length or (not char.isspace() and
                           (ord(char) not in font.cmap or
                            (index >= 2 and (char in '·()+-[]{}/’“”‘' or ord(char) > 127)))))
            style = fallback['styleId'] if punctuation else main['styleId']
            if char_index < prefix_length:
                style = tree_style['styleId']
            if punctuation and ord(char) not in literal.cmap:
                style = next((sid for cmap, sid in source_styles if ord(char) in cmap), None)
                if style is None:
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
                                   attributes=dict(tracking=tracking[paragraph_index] if tracking else 0,
                                                   wordSpacing=0., baseline=0.)))
            offset = end
        direction='ltr' if mixed_source_ltr and mixed_persian_reading(text) else 'auto'
        blocks.append(dict(blockId=uid('block'), type='paragraph', direction=direction, runs=runs))
        offset += 1
    doc['stories'][0]['blocks'] = blocks
    content['characters'] = characters
    content['paragraphs'] = [dict(alignment='left', before=1., after=24., tabs=[]) for _ in paragraphs]


def geometry(page):
    return {k: v for k, v in page.items() if k not in ('pageId', 'name', 'frames')}


def frame_geometry(frame):
    return {k: frame[k] for k in ('x', 'y', 'width', 'height')}


def reusable_spreads(path, template_hash, engine, prototype, additional_font_ids=()):
    """Only reuse byte-verified, measured spreads from the same rendering setup."""
    path = Path(path)
    evidence=path.parent if (path.parent/'layout-validation.json').is_file() else path.parent/'Working'
    proof = read(evidence / 'layout-validation.json')
    if proof['sha256'] != digest(path) or proof['templateSha256'] != template_hash:
        raise ValueError('REUSE_PROOF_HASH_MISMATCH')
    payload = read(path)
    # The language revision is provenance, not a rendering input: all four
    # compiled strings are compared before reusing a measured spread. Every
    # font/Qt/paint/typesetting fingerprint field still has to match exactly.
    # An explicitly added source-sign font cannot affect an already verified
    # spread: its runs name the old fonts and its glyph coverage was checked.
    # Existing font identities remain checked even if listed as additional.
    old_font_ids = {f.get('fontId') for f in payload['engine']['fonts']}
    additions = set(additional_font_ids) - old_font_ids
    def rendering_engine(value):
        result = {k: v for k, v in value.items() if k != 'languageRevision'}
        result['fonts'] = [f for f in value['fonts'] if f.get('fontId') not in additions]
        return result
    if rendering_engine(payload['engine']) != rendering_engine(engine):
        raise ValueError('REUSE_ENGINE_MISMATCH')
    old = payload['state']
    for field in ('recipe', 'paint', 'styles', 'features', 'fontSources'):
        current = prototype[field]
        if field == 'fontSources':
            current = [f for f in current if f.get('fontId') not in additions]
            # A moved font can reuse its measurements if its new file has the
            # recorded bytes and every other part of its declaration matches.
            for index, (before, after) in enumerate(zip(old[field], current)):
                if before == after or not before.get('path') or not after.get('path'):
                    continue
                location = Path(after['path'])
                if (dict(before, path=after['path']) == after and location.is_file()
                        and digest(location) == before.get('sha256')):
                    current[index] = before
        if old[field] != current:
            raise ValueError('REUSE_FORMAT_MISMATCH: ' + field)
    if old['typesetting']['profiles'] != prototype['typesetting']['profiles']:
        raise ValueError('REUSE_TYPESETTING_MISMATCH')
    checks = {c['leftPage']: c for c in proof['checks']}
    result = {}
    for spread in read(evidence / 'page-index.json')['spreads']:
        pair = old['pages'][spread['leftPage'] - 1:spread['rightPage']]
        columns = [texts(f) for p in pair for f in sorted(p['frames'], key=lambda f:int(f['x']))]
        if len(pair) != 2 or len(columns) != 4 or any(len(c) != len(spread['unitIds']) for c in columns):
            raise ValueError('REUSE_INDEX_MISMATCH')
        measured_frames = {f['frameId']: old['typesetting']['frames'][f['frameId']]
                           for page in pair for f in page['frames'] if f['frameId'] in old['typesetting']['frames']}
        state = dict(pages=pair, typesetting=dict(frames=measured_frames))
        check = {k:v for k,v in checks[spread['leftPage']].items() if k != 'leftPage'}
        result[spread['unitIds'][0]] = (spread['unitIds'], columns, state, check)
    return result


def check_folios(session, start, stop, mode):
    from vayrshemon import page_numbering
    result = []
    for i in range(start, stop):
        page = session.state['pages'][i]
        for page_mode in ('one', 'two'):
            with page_numbering.scope(session, page_mode):
                placement = page_numbering.placement(session, page, mode=mode)
                if placement['status'] != 'placed':
                    raise ValueError('NUMBERING_NOT_PLACED: ' + str(placement))
                result.append(placement)
    return result


def check_saved_folios(path, start, stop, mode):
    from PySide6.QtWidgets import QApplication
    from vayrshemon.file_api import FileSession
    app = QApplication.instance() or QApplication([])
    session = FileSession(ROOT, source_fonts=False, recovery=False)
    session.remember = lambda _: None
    session.log.emit = lambda *args, **kwargs: None
    try:
        session.open(path, advance_revision=False)
        return check_folios(session, start, stop, mode)
    finally:
        session.finish()


def compose(ledger_path, snapshot_path, target, template=None, reuse=None, preflight=False, source_fallback=None,
            additional_reuse=(), remeasure_incompatible=False, folio_workers=1, other_source_fonts=(), pass_cache=None):
    from PySide6.QtWidgets import QApplication
    from vayrshemon.file_api import FileSession
    from vayrshemon import language, pages, reading, paragraph_alignment, page_numbering
    from vayrshemon.numbering_contracts import new_document_defaults

    target = Path(target)
    if target.exists() or (target.parent / 'FROZEN.json').exists():
        raise ValueError('REFUSING_TO_OVERWRITE_EDITION')
    default_template = ROOT / 'Saves/Black on white.vay'
    if not default_template.is_file():
        default_template = ROOT / 'Saves/Archive/Black on white.vay'
    template = Path(template or default_template)
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
        if ledger.get('wrapLongWords'):
            from vayrshemon.typesetting_contracts import profile
            profiles = {p['languageId']: p for p in prototype['typesetting']['profiles']}
            for language_id in ('language.vayrshemon', 'language.en'):
                policy = profiles.setdefault(language_id, profile(language_id))
                policy.update(emergency=True, revision=policy['revision'] + 1)
            prototype['typesetting']['profiles'] = list(profiles.values())
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
        roman = reading.font(session, 'transliteration')
        # The approved template can reference a different Times New Roman
        # build than the one currently installed in Windows/Fonts.
        literal = next((session.fonts.faces[f['fontId']] for f in prototype['fontSources']
                        if Path(f['path']).name.lower() == 'times.ttf'
                        and session.fonts.faces[f['fontId']].original_family == 'Times New Roman'), None)
        if literal is None:
            literal = reading.font(session, 'literal')
            declaration = dict(fontId=literal.font_id, sha256=literal.sha256, path=str(literal.path))
            prototype['fontSources'].append(declaration)
            book['fontSources'].append(deepcopy(declaration))
        fonts = [script, roman, roman, roman]
        extra_font = session.fonts.register(source_fallback) if source_fallback else None
        other_fonts = [session.fonts.register(path) for path in other_source_fonts]
        source_fonts = ([extra_font] if extra_font else []) + other_fonts
        for face in source_fonts:
            if face.font_id not in {f['fontId'] for f in prototype['fontSources']}:
                declaration = dict(fontId=face.font_id, sha256=face.sha256, path=str(face.path))
                prototype['fontSources'].append(declaration)
                book['fontSources'].append(deepcopy(declaration))
        fields = ['text', 'text', 'gloss', 'source']
        reusable = {}
        for measured in (*([reuse] if reuse else []), *additional_reuse):
            try:
                spreads = reusable_spreads(measured, template_hash, session.fingerprint(), prototype,
                                           additional_font_ids=[face.font_id for face in source_fonts])
            except ValueError as exc:
                if not remeasure_incompatible or str(exc) != 'REUSE_ENGINE_MISMATCH':
                    raise
                print(f'Remeasuring pages from {measured} with the current rendering engine.', flush=True)
                continue
            reusable.update(spreads)
        reused = 0
        # A multi-pass book can share body measurements while its contents folios settle.
        # Keep this cache private to a build, and bind it to the rendering environment.
        if pass_cache is not None:
            signature=(template_hash, {k:v for k,v in session.fingerprint().items() if k!='languageRevision'},
                       ledger.get('sourceLabel'), prototype['typesetting']['profiles'], [f.font_id for f in source_fonts])
            if 'signature' in pass_cache and pass_cache['signature']!=signature:
                raise ValueError('PAGINATION_CACHE_FINGERPRINT_CHANGED')
            pass_cache['signature']=signature
            if reusable:
                pass_cache.setdefault('spreads',{}).update(reusable)
            reusable.update(pass_cache.setdefault('spreads',{}))
            if cache_root := pass_cache.get('directory'):
                stamp=sha256(json.dumps(signature,sort_keys=True).encode()).hexdigest()
                cache_root=Path(cache_root)/stamp
                cache_root.mkdir(parents=True,exist_ok=True)
                if not pass_cache.get('diskLoaded'):
                    for path in cache_root.glob('*.json'):
                        entry=read(path)
                        pass_cache['spreads'][entry[0][0]]=entry
                    reusable.update(pass_cache['spreads'])
                    pass_cache['diskLoaded']=True

        def candidate(group, spacing=None):
            spacing = {} if spacing is None else spacing
            tracking_steps = (0., -.10, .15, -.25, .35, -.45, .55, -.65)
            state = deepcopy(prototype)
            frames = [f for p in state['pages'] for f in sorted(p['frames'], key=lambda f: int(f['x']))]
            for index, (frame, font, field) in enumerate(zip(frames, fonts, fields)):
                body(frame, [column_text(u, field) for u in group], font, literal, index,
                     extra_font if index==3 else None, prefixes=[u.get('hierarchyPrefix','') for u in group],
                     other_fonts=other_fonts if index==3 else (),
                     tracking=[tracking_steps[spacing.get((index,i),0)] for i in range(len(group))] if spacing else None,
                     mixed_source_ltr=index==3 and ledger.get('pairedPersianReading',False))
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
                            if ledger.get('wrapLongWords') and excess > 1.0 and by + bh <= y + height + .05:
                                column = len(rows)
                                blocks = frames[column]['content']['document']['stories'][0]['blocks']
                                paragraph = next(i for i,b in enumerate(blocks) if b['blockId']==line['blockId'])
                                key = column, paragraph
                                step = spacing.get(key,0) + 1
                                if step < len(tracking_steps):
                                    # Punctuation in a fallback face can have a different bearing at
                                    # a Qt line break. Remeasure only this paragraph's letterspacing.
                                    spacing[key] = step
                                    return candidate(group,spacing)
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
            used_cache = False
            # Branch typography is authored by this compositor; measure tables
            # again even when their four text strings have not changed.
            previous = reusable.get(units[position]['id']) if not units[position].get('tableId') else None
            if previous:
                ids, columns, cached, check = previous
                group = units[position:position + len(ids)]
                compatible_direction = True
                if ledger.get('pairedPersianReading') and any(mixed_persian_reading(t) for t in columns[3]):
                    source_frame=max(cached['pages'][1]['frames'],key=lambda f:int(f['x']))
                    blocks=source_frame['content']['document']['stories'][0]['blocks']
                    compatible_direction=all(b['direction']=='ltr' for b,t in zip(blocks,columns[3]) if mixed_persian_reading(t))
                opening_ok = not group[0].get('keepWithOpening') or any('lines' in u for u in group)
                if opening_ok and compatible_direction and ids == [u['id'] for u in group] and columns == [[column_text(u, f) for u in group] for f in fields]:
                    best = len(ids), cached, check
                    used_cache = True
                    reused += 1
            for count in ([] if best else range(1, min(12, len(units) - position) + 1)):
                if units[position + count - 1]['chapter'] != units[position]['chapter']:
                    break
                if units[position + count - 1].get('tableId') != units[position].get('tableId'):
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
            if pass_cache is not None and not used_cache and not group[0].get('tableId'):
                saved=dict(pages=state['pages'],typesetting=dict(frames=state['typesetting']['frames']))
                pass_cache['spreads'][group[0]['id']]=([u['id'] for u in group],
                    [[column_text(u,f) for u in group] for f in fields],saved,result)
                if cache_root:
                    path=cache_root/(sha256(group[0]['id'].encode()).hexdigest()+'.json')
                    temp=path.with_suffix('.'+uuid.uuid4().hex+'.tmp')
                    temp.write_text(json.dumps(pass_cache['spreads'][group[0]['id']],ensure_ascii=False),encoding='utf8')
                    temp.replace(path)
            left = len(book['pages']) + 1
            page_label = f'{group[0]["reference"]} — {group[-1]["reference"]}'
            if len(page_label)>100:
                line_ranges=[u['lines'] for u in group if 'lines' in u]
                locator=(f' · {line_ranges[0][0]}–{line_ranges[-1][-1]}' if line_ranges else f' · p. {left}')
                chapter=str(group[0]['chapter'])
                if len(chapter)+len(locator)>100:
                    chapter=chapter[:99-len(locator)].rstrip()+'…'
                page_label=chapter+locator
            for side, page in enumerate(state['pages']):
                copy = deepcopy(page)
                copy['pageId'] = uid('page')
                copy['name'] = page_label
                if side == 1 and ledger.get('sourceLabel'):
                    max(copy['frames'], key=lambda f:int(f['x']))['name'] = ledger['sourceLabel']
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
        reusable.clear()
        session._restore(book)
        session._state = session.capture()
        session.invalidate_composition()
        page_numbering.ensure_fonts(session)
        session._undo = []
        session._redo = []
        paint_mode = session.view['mode']
        page_count = len(book['pages'])
        if folio_workers <= 1:
            numbering = check_folios(session, 0, page_count, paint_mode)
        target.parent.mkdir(parents=True, exist_ok=True)
        session.save(target, preview_mode='two')
        before = session.capture()
        session.open(target, advance_revision=False)
        assert session.capture() == before
        del before
        if folio_workers > 1:
            # Each process reopens the actual saved book, so parity, folio numbers,
            # all frames and their collision geometry have their final values.
            from concurrent.futures import ProcessPoolExecutor, as_completed
            size = (page_count + folio_workers - 1) // folio_workers
            with ProcessPoolExecutor(max_workers=folio_workers) as pool:
                futures = {pool.submit(check_saved_folios, target, start, min(start+size, page_count), paint_mode):start
                           for start in range(0, page_count, size)}
                chunks = {}
                for future in as_completed(futures):
                    start = futures[future]
                    chunks[start] = future.result()
                    print(f'Verified saved folios on pages {start+1}–{min(start+size, page_count)}.', flush=True)
            numbering = [placement for start in sorted(chunks) for placement in chunks[start]]
            assert len(numbering) == page_count * 2
        actual = [[], [], [], []]
        for i in range(0, len(book['pages']), 2):
            frames = [f for p in session.state['pages'][i:i+2] for f in sorted(p['frames'], key=lambda f: int(f['x']))]
            for j, frame in enumerate(frames):
                actual[j].extend(texts(frame))
        for j, field in enumerate(fields):
            assert actual[j] == [column_text(u, field) for u in units], 'ROUNDTRIP_COLUMN_MISMATCH: ' + field
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
