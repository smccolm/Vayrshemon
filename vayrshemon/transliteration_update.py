"""Refresh an existing Roman column without converting or recasing source slots."""
from copy import deepcopy
from difflib import SequenceMatcher
from PySide6.QtCore import QTextBoundaryFinder
from PySide6.QtGui import QTextBlockFormat, QTextCursor
from . import reading
from .authoring import digest, identity
from .session import BLOCK


def uses_font(frame, sha):
    model = frame['content']['document']
    styles = {s['styleId']: s for s in model['styles']}
    fonts = {f['fontId']: f['sha256'] for f in model['fonts']}
    runs = [r for b in model['stories'][0]['blocks'] for r in b['runs']]
    return bool(runs) and all(
        r['type'] == 'legacy' and r.get('sourceFontSha256') == sha
        and fonts.get(styles[r['styleId']]['fontId']) == sha for r in runs)


def pair(book, state):
    pages = state['pages']
    index = next(i for i, p in enumerate(pages) if any(
        f['frameId'] == state['activeFrameId'] for f in p['frames']))
    # Viewing modes never change the document or determine the source. When
    # editing the gloss/English page, use its preceding script/Roman page.
    indices = [index // 2 * 2, index] if index % 2 else [index]
    for i in dict.fromkeys(indices):
        page = pages[i]
        if len(page['frames']) != 2:
            continue
        left, right = sorted(page['frames'], key=lambda f: int(f['x']))
        if uses_font(left, reading.SCRIPT_SHA) and uses_font(right, reading.ROMAN_SHA):
            ids = {left['frameId'], right['frameId']}
            if any(ids & {flow['source'], *flow['targets']} for flow in state['typesetting']['flows']):
                raise ValueError('TRANSLITERATION_LINKED_COLUMNS: The script and Roman columns must be independent text frames.')
            return page, left, right
    raise ValueError('TRANSLITERATION_PAIR_REQUIRED: Select a page or spread with Thimfora beside an existing Transliteration 7 column. English columns are not replaced.')


def inspect(book):
    state = book.capture()
    page, left, right = pair(book, state)
    source = reading.text_blocks(left)
    target = reading.text_blocks(right)
    return dict(pageId=page['pageId'], sourceFrameId=left['frameId'], targetFrameId=right['frameId'],
                changed=source != target, sourceParagraphs=len(source), targetParagraphs=len(target),
                planId=digest([state['documentId'], left, right]),
                scope='Replace the Roman column text with the exact source slots and Maxima/Minima. Retain destination styling; English and gloss text stay unchanged.')


def graphemes(text):
    finder = QTextBoundaryFinder(QTextBoundaryFinder.BoundaryType.Grapheme, text)
    offsets = [0]
    while (position := finder.toNextBoundary()) != -1:
        offsets.append(position)
    encoded = text.encode('utf-16-le')
    return [encoded[a * 2:b * 2].decode('utf-16-le') for a, b in zip(offsets, offsets[1:])], offsets


def update(book, expected_plan=None):
    plan = inspect(book)
    if expected_plan is not None and expected_plan != plan['planId']:
        raise ValueError('TRANSLITERATION_CHANGED: The source or Roman column changed while the update was being reviewed. Choose Update transliteration again.')
    if not plan['changed']:
        return dict(plan, revision=book.revision)
    if book.composing:
        raise ValueError('COMPOSITION_ACTIVE: Finish the current text input before updating transliteration.')
    source = book.frames[plan['sourceFrameId']]
    target = book.frames[plan['targetFrameId']]
    text = source.text()
    old, offsets = graphemes(target.text())
    new, _ = graphemes(text)
    # Preserve small inline differences on normal pages, while avoiding
    # quadratic matching of very long, repetitive overset text.
    edits = SequenceMatcher(None, old, new, autojunk=max(len(old), len(new)) > 5000).get_opcodes()
    formats = []
    block = target.doc.begin()
    while block.isValid():
        formats.append(QTextBlockFormat(block.blockFormat()))
        block = block.next()
    selection = book.selection()
    with book.command('Update transliteration'):
        target.insertion_format = None
        # Apply differences from the end so unchanged text retains its inline
        # styling. Qt grapheme boundaries protect combining marks and surrogates.
        for tag, a, b, c, d in reversed(edits):
            if tag != 'equal':
                target.edit(offsets[a], offsets[b], ''.join(new[c:d]))
        # Retain the destination paragraph design by ordinal position; newly
        # added paragraphs inherit its final paragraph, never the script size.
        block = target.doc.begin()
        i = 0
        while block.isValid():
            fmt = QTextBlockFormat(formats[min(i, len(formats) - 1)])
            if i >= len(formats):
                fmt.setProperty(BLOCK, identity('block'))
            QTextCursor(block).setBlockFormat(fmt)
            block = block.next()
            i += 1
        if target.text() != text:
            raise ValueError('TRANSLITERATION_TEXT_MISMATCH')
        # The existing automatic aligner handles complete four-column spreads
        # in this same commit. A standalone reading page also aligns its pair.
        from .paragraph_alignment import align, spread_frames
        from .automatic_alignment import message
        try:
            spread_frames(book, plan['pageId'])
        except ValueError:
            ids = [plan['sourceFrameId'], plan['targetFrameId']]
            try:
                result = align(book, ids, automatic=True)
                book.automatic_alignment = dict(enabled=True, status='aligned', message=message([]), results=[result])
            except Exception as error:
                issues = [dict(frameIds=ids, reason=str(error))]
                book.automatic_alignment = dict(enabled=True, status='paused', message=message(issues), issues=issues)
                book.log.exception('transliteration-alignment', error)
        book.restore_selection(selection)
    result = dict(plan, revision=book.revision, alignment=deepcopy(book.automatic_alignment))
    book.log.emit('reading', 'TRANSLITERATION_UPDATED', **result)
    return result
