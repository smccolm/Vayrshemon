"""Compose the issued Paradise Lost text in the collected Shakespeare print layout."""
import argparse
import base64
from bisect import bisect_right
from copy import deepcopy
from io import BytesIO
from itertools import groupby
from pathlib import Path
import re
import shutil
from tempfile import TemporaryDirectory

from PIL import Image
from PySide6.QtCore import QRectF
from PySide6.QtWidgets import QApplication

from tools import shakespeare_collected as sc
from tools.compose_historical_book import column_text, texts
from tools.locke_print import LockeVolume
from tools.paradise_lost_working import BOOK, ROOT, SOURCE, WORK
from tools.shakespeare_collected_pdf import render_duplex

TITLE = 'Paradise Lost'
SOURCE_BOOK = BOOK / (BOOK.name + '.vay')
DEST = ROOT / 'Saves/Paradise Lost - Letter Print Edition'
STAGE = ROOT / '.local/paradise-lost-print'
NATIVE = TITLE + '.vay'
PDF = TITLE + ' - Duplex Print.pdf'
TITLE_ART = ROOT / 'Inputs/Print artwork/Paradise Lost Title Page - Approved.png'
TITLE_UNITS = {'pl.00001.001', 'pl.00003.001'}


def place_title_art(state):
    """Embed the author's completed composition without altering its pixels."""
    page = state['pages'][0]
    edition = state['printEdition']
    title = edition['pages'][page['pageId']]
    assert title['kind'] == 'title'
    rows = [r for r in edition['verses'] if any(f['pageId'] == page['pageId'] for f in r['fragments'])]
    assert {r['id'] for r in rows} in (set(), TITLE_UNITS)
    edition['verses'] = [r for r in edition['verses'] if r not in rows]
    blank = state['pages'][1]
    assert not sc.pe.text_of(blank)
    page['frames'][0]['content'] = deepcopy(blank['frames'][0]['content'])
    page['frames'][0]['content']['document']['title'] = page['name']
    title.update(lines=[], sourceSha256=sc.pe.hash_text(''))
    raw = TITLE_ART.read_bytes()
    key = sc.digest(TITLE_ART)
    with Image.open(BytesIO(raw)) as image:
        width, height = image.size
        x0, y0, x1, y1 = image.convert('L').point(lambda v: 255 if v < 96 else 0).getbbox()
    available = 792 - sc.TOP - sc.BOTTOM
    scale = min(sc.MEASURE / (x1 - x0), available / (y1 - y0))
    rect = [306 - scale * (x0 + x1) / 2,
            sc.TOP + (available - scale * (y0 + y1)) / 2, width * scale, height * scale]
    old = {item['asset'] for item in title['images']}
    title['images'] = [dict(asset=key, rect=rect)]
    edition['assets'][key] = dict(png=base64.b64encode(raw).decode('ascii'), width=width, height=height)
    used = {item['asset'] for spec in edition['pages'].values() for item in spec['images']}
    for unused in old - used:
        del edition['assets'][unused]


def title_art_metadata(state):
    plate, = state['printEdition']['pages'][state['pages'][0]['pageId']]['images']
    asset = state['printEdition']['assets'][plate['asset']]
    return dict(file=TITLE_ART.relative_to(ROOT).as_posix(), sha256=plate['asset'],
                rectPt=plate['rect'], pixels=[asset['width'], asset['height']])


def checked_source(ledger):
    receipt = sc.read(WORK / 'completion-report.json')
    assert sc.digest(SOURCE_BOOK) == receipt['nativeSha256']
    assert ledger['status'] == 'complete' and ledger['nextSourceLine'] is None
    assert sc.digest(SOURCE) == ledger['sourceSha256'] == receipt['sourceSha256']
    assert ledger['translatedSourceWords'] == ledger['sourceWords'] == 82597
    state = sc.unpack(sc.read(SOURCE_BOOK))['state']
    rows = iter(ledger['units'])
    for left, right in zip(state['pages'][::2], state['pages'][1::2], strict=True):
        columns = [texts(frame) for page in (left, right)
                   for frame in sorted(page['frames'], key=lambda f: int(f['x']))]
        assert len(columns) == 4
        for passage in zip(*columns, strict=True):
            row = next(rows)
            assert passage == tuple(column_text(row, f) for f in ('text', 'text', 'gloss', 'source')), row['id']
    assert next(rows, None) is None
    return state['language'], receipt['nativeSha256']


class MiltonVolume(LockeVolume):
    def __init__(self, ledger, language, checksum):
        assert sc.digest(sc.DEST) == sc.read(sc.DEST.parent / 'edition-manifest.json')['nativeSha256']
        self.state = sc.unpack(sc.read(sc.DEST))['state']
        old = self.state['printEdition']
        record = next(r for r in old['verses'] if r['id'] == 'nav/contents')
        pages = {p['pageId']: sc.pe.text_of(p) for p in self.state['pages']}
        self.contents_title = ''.join(pages[f['pageId']][f['start']:f['end']] for f in record['fragments'])
        self.prototype = self.state['pages'][0]
        self.proof = sc.Typesetter(next(f for f in self.state['fontSources'] if f['fontId'] == sc.pe.DRAMA_PUNCT))
        self.edition = dict(version=1, layoutVersion=sc.pe.COLLECTED, typography=dict(sc.pe.COMPACT_TYPE),
                            languageVersion=ledger['languageVersion'], sourceSha256=checksum,
                            ledgerSha256=sc.digest(WORK / 'ledger.json'), assets={}, pages={}, verses=[], sections=[])
        self.state.update(title=TITLE, documentId='document.milton.paradise-lost.letter', language=language,
                          pages=[], printEdition=self.edition, revision=0)
        self.records = {}
        self.page = self.work = None
        self.start_body = 5
        self.groups = {key: list(rows) for key, rows in groupby(ledger['units'], lambda r: r['chapter'])}
        self.chapters = [key for key in self.groups if key != 'Title']
        assert len(self.chapters) == 12
        self.folios = {}
        self.rebalanced_endings = []
        self.bookmarks = {key: key for key in self.chapters}
        self.headings = {key: next(r for r in self.groups[key] if r['kind'] == 'heading') for key in self.chapters}

    def contents(self):
        self.label('nav/contents', self.contents_title, 50, 100)
        for i, chapter in enumerate(self.chapters):
            x, y = (i // 6) * 251, 161 + (i % 6) * 36
            self.label('nav/toc/' + chapter, self.headings[chapter]['text'], 30, y,
                       at=x, width=195, align='left')
            self.label('nav/folio/' + chapter, sc.digits(self.folios[chapter]), 24, y,
                       at=x + 204, width=31, align='right')
        # Identical thin divider to the collected Shakespeare contents page.
        page = dict(frames=[dict(x=sc.mp(self.left), width=sc.mp(sc.MEASURE))])
        self.page['paths'] = [sc.contents_divider(page, self.page)]

    def paragraph(self, items, centered=False, keep_next=False):
        """Use the collected layout, keeping a very short final word with its neighbour."""
        starts, ends, pieces = [], [], []
        length = 0
        for key, row in items:
            if pieces:
                gap = ' ' if row['continuation'] else '   '
                pieces.append(gap)
                length += len(gap)
            starts.append(length)
            pieces.append(row['text'])
            length += len(row['text'])
            ends.append(length)
        paragraph = ''.join(pieces)
        layout = self.proof.layout(paragraph, sc.BODY, sc.MEASURE - 2)
        spans = [(layout.lineAt(i).textStart(), layout.lineAt(i).textStart() + layout.lineAt(i).textLength())
                 for i in range(layout.lineCount())]
        if not centered and len(spans) > 1:
            a, b = spans[-2]
            last = paragraph[spans[-1][0]:spans[-1][1]].strip()
            words = list(re.finditer(r'\S+', paragraph[a:b]))
            if len(last.split()) == 1 and len(last) < 12 and len(words) > 1:
                cut = a + words[-1].start()
                ending = paragraph[cut:spans[-1][1]].strip()
                if self.proof.ink(ending, sc.BODY).width() <= sc.MEASURE - 2:
                    self.rebalanced_endings.append(dict(unit=items[-1][0],oldLastLine=last,newLastLine=ending))
                    spans[-2], spans[-1] = (a, cut), (cut, spans[-1][1])
        assert ''.join(paragraph[a:b] for a, b in spans) == paragraph
        for i, (a, b) in enumerate(spans):
            segment = paragraph[a:b]
            visible = segment.strip()
            bounds = self.proof.ink(visible, sc.BODY)
            baseline = max(self.y, self.last_bottom + .25 - bounds.top())
            reserve = sc.LEADING if keep_next and i == len(spans) - 1 else 0
            if baseline + bounds.bottom() + reserve > 792 - sc.BOTTOM:
                self.new_page('body', self.work['title'])
                baseline = max(self.y, sc.TOP - bounds.top())
            if self.source and i == 0:
                self.source += '\n'
            start = len(self.source)
            self.source += segment
            row_index = bisect_right(ends, a)
            while row_index < len(items) and starts[row_index] < b:
                key, row = items[row_index]
                first, last = max(a, starts[row_index]), min(b, ends[row_index])
                if first < last:
                    self.fragment(key, row['text'], start + first - a, start + last - a)
                row_index += 1
            trim = len(segment) - len(segment.lstrip())
            x = self.left + ((sc.MEASURE - bounds.width()) / 2 - bounds.left() if centered else max(0., -bounds.left()))
            gap = 0.
            if i + 1 < len(spans) and not centered:
                gaps = len(visible.split()) - 1
                if gaps:
                    x = self.left - bounds.left()
                    extra = sc.MEASURE - bounds.width()
                    gap = extra / gaps
                    bounds = bounds.adjusted(0, 0, extra, 0)
            self.place(start + trim, start + trim + len(visible), x, baseline, sc.BODY, bounds, gap)
            self.y = baseline + sc.LEADING

    def chapter(self, key):
        self.opening(key)
        group, kind = [], None
        self.y = 95

        def flush():
            if group:
                self.body(group)
                group.clear()

        for row in self.groups[key]:
            current = row['kind']
            if current in ('booktitle', 'heading', 'argument_heading'):
                flush()
                size = {'booktitle': 32, 'heading': 44, 'argument_heading': 28}[current]
                bottom = self.block(row['id'], row['text'], size, self.y)
                self.y = bottom + (25 if current == 'argument_heading' else 29)
            elif current == 'colophon':
                flush()
                self.paragraph([(row['id'], dict(text=row['text'], continuation=False))], centered=True)
            else:
                assert current in ('argument', 'verse')
                if kind != current:
                    flush()
                group.append(row)
            kind = current
        flush()
        print(f'{key}: through native page {len(self.state["pages"]) + 1}', flush=True)

    def compose(self):
        title, author = self.groups['Title']
        self.new_page('title', 'Title page')
        bottom = self.block(title['id'], title['text'], 50, 300, width=440, at=23)
        self.block(author['id'], author['text'], 32, bottom + 55)
        self.new_page('blank', 'Blank')
        self.new_page('frontispiece', 'Frontispiece')
        quote = next(r for r in reversed(self.groups['Book XII']) if r['kind'] == 'verse')
        self.frontispiece_source = quote['id']
        bottom = self.block('nav/frontispiece/quotation', quote['text'], 32, 280, width=400, at=43)
        self.block('nav/frontispiece/reference', self.headings['Book XII']['text'], 26, bottom + 40)
        self.new_page('contents', 'Contents')
        for chapter in self.chapters:
            self.chapter(chapter)
        self.finish_page()
        body = self.state['pages'][4:]
        self.state['pages'] = self.state['pages'][:3]
        self.new_page('contents', 'Contents')
        self.contents()
        self.finish_page()
        self.state['pages'].extend(body)
        self.state['activeFrameId'] = self.state['pages'][0]['frames'][0]['frameId']
        self.edition['verses'].sort(key=lambda r: (r['fragments'][0]['pageId'], r['fragments'][0]['start']))
        place_title_art(self.state)
        return self.state


def verify(state, ledger, folios):
    sc.pe.validate(state)
    edition = state['printEdition']
    pages = {p['pageId']: sc.pe.text_of(p) for p in state['pages']}
    records = {r['id']: ''.join(pages[f['pageId']][f['start']:f['end']] for f in r['fragments'])
               for r in edition['verses']}
    title = edition['pages'][state['pages'][0]['pageId']]
    illustrated = bool(title['images'])
    expected = [(u['id'], u['text']) for u in ledger['units']
                if not (illustrated and u['id'] in TITLE_UNITS)]
    assert [(k, v) for k, v in records.items() if not k.startswith('nav/')] == expected
    assert len(expected) == 1993 - (2 if illustrated else 0)
    if illustrated:
        plate, = title['images']
        assert plate['asset'] == sc.digest(TITLE_ART)
        assert base64.b64decode(edition['assets'][plate['asset']]['png']) == TITLE_ART.read_bytes()
        assert not title['lines'] and not sc.pe.text_of(state['pages'][0])
    assert records['nav/frontispiece/quotation'] == next(u['text'] for u in ledger['units'] if u['id'] == 'pl.11034.001')
    assert all(records['nav/folio/' + key] == sc.digits(f) for key, f in folios.items())
    links = sc.pe.contents_links(state)
    assert sum(map(len, links.values())) == len(folios) == 12
    all_links = [link for p in state['pages'] for link in links.get(p['pageId'], [])]
    assert [link['page'] for link in all_links] == [f + 4 for f in folios.values()]
    assert len(edition['sections']) == 12
    for rows in links.values():
        boxes = [QRectF(*r['bounds']) for r in rows]
        assert all(not box.intersects(other) for i, box in enumerate(boxes) for other in boxes[i + 1:])
    for n, page in enumerate(state['pages'], 1):
        spec = edition['pages'][page['pageId']]
        boxes = [QRectF(*line['bounds']) for line in spec['lines']]
        assert all(not box.intersects(other) for i, box in enumerate(boxes) for other in boxes[i + 1:]), page['name']
        assert int(page['margins']['left']) == int(sc.mp(63 if n == 1 else 54 if n % 2 else 72))
        for path in spec['paths']:
            assert path['role'] == 'contents-column-divider'
            assert not any(sc.pe.decode_path(path).intersects(box) for box in boxes)
    return sc.pe.hash_text('\n'.join(text for _, text in expected))


def build():
    STAGE.mkdir(parents=True, exist_ok=True)
    ledger = sc.read(WORK / 'ledger.json')
    language, checksum = checked_source(ledger)
    volume = MiltonVolume(ledger, language, checksum)
    state = volume.compose()
    text_hash = verify(state, ledger, volume.folios)
    book = sc.FileSession(ROOT, recovery=False)
    book.remember = lambda path: None
    book.log.emit = lambda *a, **kw: None
    try:
        for f in state['fontSources']:
            book.fonts.register(book.fonts.document_path(f['path'], f['sha256']), f['sha256'])
        book._restore(state, take_ownership=True)
        book._state = book.capture()
        with TemporaryDirectory(dir=STAGE) as scratch:
            staged = Path(scratch) / NATIVE
            book.save(staged, preview_mode='two')
            before = book.capture()
            book.open(staged, advance_revision=False)
            state = book.capture()
            assert state == before and book.saved_page_mode == 'two'
            staged.replace(STAGE / NATIVE)
    finally:
        book.finish()
    assert verify(state, ledger, volume.folios) == text_hash
    physical = render_duplex(state, STAGE / PDF, TITLE, use_printed_folios=True)
    sc.write(STAGE / 'edition-manifest.json', dict(
        title=TITLE, author='John Milton', nativeSha256=sc.digest(STAGE / NATIVE),
        pdfSha256=sc.digest(STAGE / PDF), layoutReferenceSha256=sc.digest(sc.DEST),
        sourceProgressiveSha256=checksum, ledgerSha256=volume.edition['ledgerSha256'],
        englishSourceSha256=ledger['sourceSha256'], sourceWords=ledger['sourceWords'],
        exactNativeUnits=1991, titleUnitsInArtwork=2, sourceUnits=1993,
        titleArtwork=title_art_metadata(state), sharedNativeTextSha256=text_hash, omittedUnits=0,
        nativePages=len(state['pages']), pdfPages=physical, duplexSheets=(physical + 1) // 2,
        leadingBindingBlanks=1, marginsPt=dict(inside=72, outside=54, top=48, bottom=71),
        typeSizePt=sc.BODY, leadingPt=sc.LEADING, chapterAndFrontMatterFolios=volume.folios,
        contentsNativePages=[4], linkedContentsEntries=12, saveReopenIdentical=True,
        allNativeUnitsMatchProgressive=True, frontispieceQuotationUnit=volume.frontispiece_source,
        bodyAlignment='Justified full lines; natural paragraph endings',
        shortFinalLinesRebalanced=volume.rebalanced_endings,
        folios='Outside in native spreads and physical duplex order',
        sourceNotes='All supplied titles, Arguments, verse passages and colophons retained in order.'))
    (STAGE / 'Printing notes.txt').write_text(
        f'Paradise Lost - Letter Print Edition\n\n'
        f'{len(state["pages"])} native pages; {physical} PDF pages; {(physical + 1) // 2} duplex sheets.\n'
        'Print the PDF on US Letter paper at Actual Size / 100%, double-sided, flip on the long edge.\n'
        'Keep the first binding blank: it makes the PDF spreads match the native facing-page view.\n'
        'Inside margin: 1 inch; outside margin: 0.75 inch. Page numbers are on the outside.\n'
        'The contents page and PDF bookmarks link to all twelve books; their numbers are the printed Unta folios.\n'
        'The approved illustrated title page is embedded intact. The textual frontispiece repeats the final verse passage verbatim.\n'
        'The title and author units appear in the approved artwork; all 1,991 remaining source units match the four-column Vayrshemon exactly and in order.\n'
        'The progressive manuscript is unchanged. Verification is recorded in the accompanying JSON receipts.\n',
        encoding='utf8')
    assert sc.digest(SOURCE_BOOK) == checksum
    print(f'Verified {len(state["pages"])} native pages and {physical} PDF pages.', flush=True)


def install():
    manifest = sc.read(STAGE / 'edition-manifest.json')
    proof = sc.read(STAGE / 'proof-validation.json')
    assert proof['nativeSha256'] == manifest['nativeSha256'] and proof['pdfSha256'] == manifest['pdfSha256']
    assert proof['visuallyReviewedPages'] == proof['renderedPages']
    for filename, key in ((NATIVE, 'nativeSha256'), (PDF, 'pdfSha256')):
        assert sc.digest(STAGE / filename) == manifest[key]
    assert manifest['sourceProgressiveSha256'] == sc.digest(SOURCE_BOOK)
    if DEST.exists():
        raise FileExistsError(DEST)
    with TemporaryDirectory(dir=DEST.parent) as scratch:
        folder = Path(scratch) / DEST.name
        folder.mkdir()
        for name in (NATIVE, PDF, 'edition-manifest.json', 'proof-validation.json', 'Printing notes.txt'):
            shutil.copy2(STAGE / name, folder / name)
        folder.rename(DEST)
    print(DEST)


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('operation', choices=['build', 'install'])
    args = cli.parse_args()
    if args.operation == 'build':
        app = QApplication([])
        build()
    else:
        install()
