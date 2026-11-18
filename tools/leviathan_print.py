"""Set the issued Leviathan text in the collected Shakespeare Letter layout."""
from itertools import groupby
from pathlib import Path
import argparse
import base64
from copy import deepcopy
from io import BytesIO
import shutil
from tempfile import TemporaryDirectory

from PIL import Image
from PySide6.QtCore import QRectF
from PySide6.QtGui import QPainterPath
from PySide6.QtWidgets import QApplication

from tools import shakespeare_collected as sc
from tools.compose_historical_book import column_text, texts
from tools.leviathan_working import BOOK, ROOT, SOURCE, WORK
from tools.locke_print import LockeVolume
from tools.shakespeare_collected_pdf import render_duplex

TITLE = 'Leviathan'
SOURCE_BOOK = BOOK / (BOOK.name + '.vay')
DEST = ROOT / 'Saves/Leviathan - Letter Print Edition'
STAGE = ROOT / '.local/leviathan-print'
NATIVE = TITLE + '.vay'
PDF = TITLE + ' - Duplex Print.pdf'
TITLE_ART = ROOT / 'Inputs/Print artwork/Leviathan Title Page - Approved - 2.png'
PARTS = {'Chapter 1': 'Part 1', 'Chapter 17': 'Part 2',
         'Chapter 32': 'Part 3', 'Chapter 44': 'Part 4'}
TABLE = 'Chapter IX table'


def place_title_art(state):
    """Replace the two typeset title labels with the author's exact approved plate."""
    page = state['pages'][0]
    edition = state['printEdition']
    title = edition['pages'][page['pageId']]
    assert title['kind'] == 'title'
    rows = [r for r in edition['verses'] if any(f['pageId'] == page['pageId'] for f in r['fragments'])]
    assert {r['id'] for r in rows} in (set(), {'title.1', 'author.1'})
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
    title = state['printEdition']['pages'][state['pages'][0]['pageId']]
    plate, = title['images']
    asset = state['printEdition']['assets'][plate['asset']]
    return dict(file=TITLE_ART.relative_to(ROOT).as_posix(), sha256=plate['asset'],
                rectPt=plate['rect'], pixels=[asset['width'], asset['height']])


def checked_source(ledger):
    receipt = sc.read(WORK / 'layout-validation.json')
    assert sc.digest(SOURCE_BOOK) == receipt['sha256']
    assert ledger['status'] == 'complete' and not ledger['omittedFigures']
    assert sc.digest(SOURCE) == ledger['sourceSha256']
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
    return state['language'], receipt['sha256']


class LeviathanVolume(LockeVolume):
    def __init__(self, ledger, language, checksum):
        assert sc.digest(sc.DEST) == sc.read(sc.DEST.parent / 'edition-manifest.json')['nativeSha256']
        self.state = sc.unpack(sc.read(sc.DEST))['state']
        self.prototype = self.state['pages'][0]
        self.proof = sc.Typesetter(next(f for f in self.state['fontSources'] if f['fontId'] == sc.pe.DRAMA_PUNCT))
        self.edition = dict(version=1, layoutVersion=sc.pe.COLLECTED, typography=dict(sc.pe.COMPACT_TYPE),
                            languageVersion=ledger['languageVersion'], sourceSha256=checksum,
                            ledgerSha256=sc.digest(WORK / 'ledger.json'), assets={}, pages={}, verses=[], sections=[])
        self.state.update(title=TITLE, documentId='document.leviathan.letter', language=language, pages=[],
                          printEdition=self.edition, revision=0)
        self.records = {}
        self.page = None
        self.work = None
        self.start_body = 7
        self.groups = {key: list(rows) for key, rows in groupby(ledger['units'], lambda r: r['chapter'])}
        self.folios, self.bookmarks = {}, {}
        self.table_rows = [u for u in ledger['units'] if u.get('tableId')]
        assert len(self.table_rows) == 60
        self.source_kinds = {r['id']: r['kind'] for r in sc.read(WORK / 'english-blocks.json')['rows']}
        self.toc_items = []
        for chapter, rows in self.groups.items():
            if chapter in ('Title', 'Contents'):
                continue
            if chapter.startswith('Part '):
                self.toc_items.append(dict(key=chapter, text=rows[0]['text'], heading=True))
                continue
            self.bookmarks[chapter] = chapter + (' · ' + rows[0]['source'] if chapter.startswith('Chapter ') else '')
            label = rows[0]['text']
            if chapter.startswith('Chapter '):
                label = label.split(' ', 1)[1]  # Chapter is implicit in the contents list.
            self.toc_items.append(dict(key=chapter, text=label, heading=False))
            if chapter == 'Chapter 9':
                self.bookmarks[TABLE] = 'Chapter IX · Table of sciences'
                self.toc_items.append(dict(key=TABLE, text=self.table_rows[0]['text'], heading=False))
        self.toc_plan = self.plan_contents()

    def plan_contents(self):
        """Fit full titles in four columns without dropping words or orphaning part labels."""
        measured = []
        for item in self.toc_items:
            size = 28 if item['heading'] else 22
            width = 235 if item['heading'] else 199
            lines = list(self.lines(item['text'], size, width))
            baseline, bottom = 0, 0
            for j, (_, text) in enumerate(lines):
                ink = self.proof.ink(text, size)
                if j:
                    baseline = max(baseline + size * .68, bottom + 1 - ink.top())
                bottom = baseline + ink.bottom()
            height = max(20, bottom + (16 if item['heading'] else 12))
            measured.append(dict(**item, height=height, size=size, width=width))
        totals = [0]
        for item in measured:
            totals.append(totals[-1] + item['height'])
        # Minimize the tallest column; part headings stay with the following entry.
        best = {(0, 0): (0, [])}
        for columns in range(1, 5):
            for end in range(columns, len(measured) + 1):
                if end < len(measured) and measured[end - 1]['heading']:
                    continue
                options = []
                for start in range(columns - 1, end):
                    prior = best.get((columns - 1, start))
                    if prior:
                        options.append((max(prior[0], totals[end] - totals[start]), prior[1] + [(start, end)]))
                if options:
                    best[columns, end] = min(options)
        maximum, groups = best[4, len(measured)]
        assert maximum <= 594, 'Contents need more than two pages'
        plan = []
        for column, (start, end) in enumerate(groups):
            y = 127
            for item in measured[start:end]:
                plan.append(dict(**item, column=column, baseline=y))
                y += item['height']
        return plan

    def contents_page(self, number):
        self.new_page('contents', f'Contents {number + 1}')
        self.label(f'nav/contents/{number}', self.groups['Contents'][0]['text'], 50, 90)
        for item in self.toc_plan:
            if item['column'] // 2 != number:
                continue
            at = item['column'] % 2 * 251
            key, y = item['key'], item['baseline']
            self.block(('nav/part/' if item['heading'] else 'nav/toc/') + key,
                       item['text'], item['size'], y, width=item['width'], at=at, center=False)
            if not item['heading']:
                self.label('nav/folio/' + key, sc.digits(self.folios[key]), 24, y,
                           at=at + 204, width=31, align='right')
        boxes = [QRectF(*line['bounds']) for line in self.page['lines'][1:]]
        rule = QPainterPath()
        top, bottom = min(b.top() for b in boxes), max(b.bottom() for b in boxes)
        rule.addRect(QRectF(self.left + sc.MEASURE / 2 - .2, top, .4, bottom - top))
        assert not any(rule.boundingRect().intersects(box) for box in boxes)
        self.page['paths'] = [sc.pe.encode_path(rule, 'contents-column-divider')]

    def prose(self, rows):
        group = []
        for row in rows:
            marginal = self.source_kinds[row['sourceBlock']] in ('marginal heading', 'heading')
            if group and (not row['continuesParagraph'] or marginal):
                self.paragraph(group)
                group = []
            item = (row['id'], dict(text=row['text'], continuation=row['continuesParagraph']))
            if marginal:
                self.paragraph([item], keep_next=True)
            else:
                group.append(item)
        if group:
            self.paragraph(group)

    def table(self):
        self.opening(TABLE)
        self.table_geometry = []
        for index, row in enumerate(self.table_rows):
            depth = row['hierarchyDepth']
            at = depth * 10 + (8 if depth else 0)
            width = sc.MEASURE - at
            segments = list(self.lines(row['text'], sc.BODY, width))

            def positions(y, last):
                result = []
                for offset, text in segments:
                    ink = self.proof.ink(text, sc.BODY)
                    y = max(y, last + .25 - ink.top())
                    result.append((offset, text, ink, y))
                    last, y = y + ink.bottom(), y + sc.LEADING
                return result

            positions_on_page = positions(self.y, self.last_bottom)
            next_row = self.table_rows[index + 1] if index + 1 < len(self.table_rows) else None
            reserve = sc.LEADING * 2 if next_row and next_row['parentNode'] == row['sourceBlock'] else 0
            if positions_on_page[-1][3] + positions_on_page[-1][2].bottom() + reserve > 792 - sc.BOTTOM:
                self.new_page('body', TABLE)
                positions_on_page = positions(self.y, self.last_bottom)
            if self.source:
                self.source += '\n'
            start = len(self.source)
            self.source += row['text']
            self.fragment(row['id'], row['text'], start, len(self.source))
            for offset, text, ink, baseline in positions_on_page:
                self.place(start + offset, start + offset + len(text), self.left + at - ink.left(),
                           baseline, sc.BODY, ink)
            first_baseline = positions_on_page[0][3]
            top = positions_on_page[0][3] + positions_on_page[0][2].top()
            bottom = self.last_bottom
            self.table_geometry.append(dict(id=row['id'], pageId=self.pid, depth=depth,
                                            parent=row['parentNode'], indentPt=at,
                                            top=top, bottom=bottom))
            # The saved hierarchy prefix specifies which ancestor branches continue.
            prefix = row['hierarchyPrefix']
            for level in range(depth):
                token = prefix[level * 2:level * 2 + 2].strip()
                x = self.left + level * 10 + 4
                path = QPainterPath()
                middle = first_baseline - 4
                if token == '│':
                    path.addRect(QRectF(x, top, .35, bottom - top + 3))
                elif token in ('├─', '└─'):
                    end = bottom + 3 if token == '├─' else middle
                    path.addRect(QRectF(x, top, .35, max(.35, end - top)))
                    path.addRect(QRectF(x, middle, max(4, at - level * 10 - 7), .35))
                if not path.isEmpty():
                    self.page['paths'].append(sc.pe.encode_path(path, 'table-hierarchy'))
            self.y = positions_on_page[-1][3] + sc.LEADING + 3
        self.work = dict(title='Chapter 9')

    def compose(self):
        title, author = self.groups['Title']
        self.new_page('title', 'Title page')
        bottom = self.block(title['id'], title['text'], 50, 290, width=440, at=23)
        self.block(author['id'], author['text'], 32, bottom + 55)
        self.new_page('blank', 'Blank')
        self.new_page('frontispiece', 'Dedication frontispiece')
        row = self.groups['Dedication'][0]
        self.block(row['id'], row['text'], 38, 335, width=430, at=28)
        for n in range(2):
            self.new_page('contents', f'Contents {n + 1}')
        self.new_page('blank', 'Blank before text')
        for chapter, rows in self.groups.items():
            if chapter in ('Title', 'Contents') or chapter.startswith('Part '):
                continue
            self.opening(chapter)
            y = 95
            if chapter in PARTS:
                part, = self.groups[PARTS[chapter]]
                y = self.block(part['id'], part['text'], 38, y) + 32
            heading, *rest = rows
            if chapter != 'Dedication':
                self.y = self.block(heading['id'], heading['text'], 44, y) + 31
            self.prose([r for r in rest if not r.get('tableId')])
            if chapter == 'Chapter 9':
                self.table()
            print(f'{chapter}: through native page {len(self.state["pages"]) + 1}', flush=True)
        self.finish_page()
        body = self.state['pages'][6:]
        self.state['pages'] = self.state['pages'][:3]
        for n in range(2):
            self.contents_page(n)
        self.new_page('blank', 'Blank before text')
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
    expected = {u['id']: u['text'] for u in ledger['units'] if u['chapter'] != 'Contents'
                and not (illustrated and u['chapter'] == 'Title')}
    actual = {k: v for k, v in records.items() if not k.startswith('nav/')}
    assert actual == expected and list(actual) == list(expected)
    assert len(expected) == 5991 - (2 if illustrated else 0)
    if illustrated:
        plate, = title['images']
        assert plate['asset'] == sc.digest(TITLE_ART)
        assert not title['lines'] and not sc.pe.text_of(state['pages'][0])
    assert all(records['nav/folio/' + k] == sc.digits(f) for k, f in folios.items())
    links = sc.pe.contents_links(state)
    assert sum(map(len, links.values())) == len(folios) == 51
    all_links = [link for p in state['pages'] for link in links.get(p['pageId'], [])]
    assert [link['page'] for link in all_links] == [f + 6 for f in folios.values()]
    for pid, page_links in links.items():
        boxes = [QRectF(*link['bounds']) for link in page_links]
        assert all(not box.intersects(other) for i, box in enumerate(boxes) for other in boxes[i + 1:])
    for page in state['pages']:
        spec = edition['pages'][page['pageId']]
        boxes = [QRectF(*line['bounds']) for line in spec['lines']]
        assert all(not box.intersects(other) for i, box in enumerate(boxes) for other in boxes[i + 1:]), page['name']
        for path in spec['paths']:
            if path['role'] == 'table-hierarchy':
                assert not any(sc.pe.decode_path(path).intersects(b) for b in boxes), page['name']
    assert sum(u.get('tableId') == 'knowledge-foldout' for u in ledger['units'] if u['id'] in records) == 60


def build():
    STAGE.mkdir(parents=True, exist_ok=True)
    ledger = sc.read(WORK / 'ledger.json')
    language, checksum = checked_source(ledger)
    volume = LeviathanVolume(ledger, language, checksum)
    state = volume.compose()
    verify(state, ledger, volume.folios)
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
    verify(state, ledger, volume.folios)
    physical = render_duplex(state, STAGE / PDF, TITLE, use_printed_folios=True)
    table_pages = list(dict.fromkeys(int(r['pageId'].split('.')[-1]) for r in volume.table_geometry))
    sc.write(STAGE / 'edition-manifest.json', dict(
        title=TITLE, author='Thomas Hobbes', nativeSha256=sc.digest(STAGE / NATIVE),
        pdfSha256=sc.digest(STAGE / PDF), layoutReferenceSha256=sc.digest(sc.DEST),
        sourceProgressiveSha256=checksum, ledgerSha256=volume.edition['ledgerSha256'],
        englishSourceSha256=ledger['sourceSha256'], sourceWords=ledger['sourceWords'],
        exactNativeUnits=5989, titleUnitsInArtwork=2, titleArtwork=title_art_metadata(state),
        originalContentsUnitsReplaced=54, restoredTableRows=60,
        tableNativePages=table_pages, tablePrintedFolios=[n - 6 for n in table_pages],
        nativePages=len(state['pages']), pdfPages=physical, duplexSheets=(physical + 1) // 2,
        marginsPt=dict(inside=72, outside=54, top=48, bottom=71), typeSizePt=sc.BODY,
        leadingPt=sc.LEADING, chapterAndFrontMatterFolios=volume.folios,
        contentsNativePages=[4, 5], linkedContentsEntries=51, saveReopenIdentical=True,
        allNativeUnitsMatchProgressive=True, bodyAlignment='Justified full lines; natural paragraph endings',
        folios='Outside in native spreads and physical duplex order',
        originalContents='Historical page references replaced by linked print-edition Unta folios.'))
    sc.write(STAGE / 'table-layout.json', volume.table_geometry)
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
        for name in (NATIVE, PDF, 'edition-manifest.json', 'proof-validation.json', 'table-layout.json'):
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
