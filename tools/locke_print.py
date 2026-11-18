"""Compose the Locke reading edition from the issued four-column text."""
from itertools import groupby
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory

from PySide6.QtCore import QRectF
from PySide6.QtGui import QPainterPath
from PySide6.QtWidgets import QApplication

from tools import shakespeare_collected as sc
from tools.compose_historical_book import texts
from tools.locke_working import BOOK, ROOT, SOURCE, TITLE, WORK
from tools.shakespeare_collected_pdf import render_duplex


SOURCE_BOOK = BOOK / (BOOK.name + '.vay')
DEST = ROOT / 'Saves' / (TITLE + ' - Letter Print Edition')
STAGE = ROOT / '.local/locke-print'
NATIVE = TITLE + '.vay'
PDF = TITLE + ' - Duplex Print.pdf'
BOOK_NAMES = ('First Treatise', 'Second Treatise')
CONTENTS = ('Contents · Book I', 'Contents · Book II')


def checked_source(ledger):
    receipt = sc.read(WORK / 'layout-validation.json')
    assert sc.digest(SOURCE_BOOK) == receipt['sha256']
    assert ledger['status'] == 'translated' and sc.digest(SOURCE) == ledger['sourceSha256']
    state = sc.unpack(sc.read(SOURCE_BOOK))['state']
    rows = iter(ledger['units'])
    pages = state['pages']
    for left, right in zip(pages[::2], pages[1::2], strict=True):
        columns = [texts(frame) for page in (left, right)
                   for frame in sorted(page['frames'], key=lambda f: int(f['x']))]
        assert len(columns) == 4
        for passage in zip(*columns, strict=True):
            row = next(rows)
            assert passage == (row['text'], row['text'], row['gloss'], row['source']), row['id']
    assert next(rows, None) is None
    return state['language'], receipt['sha256']


class LockeVolume(sc.Volume):
    def __init__(self, ledger, language, checksum):
        assert sc.digest(sc.DEST) == sc.read(sc.DEST.parent / 'edition-manifest.json')['nativeSha256']
        self.state = sc.unpack(sc.read(sc.DEST))['state']
        self.prototype = self.state['pages'][0]
        self.proof = sc.Typesetter(next(f for f in self.state['fontSources'] if f['fontId'] == sc.pe.DRAMA_PUNCT))
        self.edition = dict(version=1, layoutVersion=sc.pe.COLLECTED, typography=dict(sc.pe.COMPACT_TYPE),
                            languageVersion=ledger['languageVersion'], sourceSha256=checksum,
                            ledgerSha256=sc.digest(WORK / 'ledger.json'), assets={}, pages={}, verses=[], sections=[])
        self.state.update(title=TITLE, documentId='document.locke.letter', language=language, pages=[],
                          printEdition=self.edition, revision=0)
        self.records = {}
        self.page = None
        self.work = None
        self.start_body = 5
        self.groups = {key: list(rows) for key, rows in groupby(ledger['units'], lambda r: r['chapter'])}
        self.folios = {}
        self.bookmarks = {}
        self.toc = []
        for book, contents in zip(BOOK_NAMES, CONTENTS, strict=True):
            rows = self.groups[contents]
            titles = rows[1:-1] if rows[-1]['source'].startswith('The End') else rows[1:]
            chapters = [k for k in self.groups if k.startswith(book + ' · ')]
            entries = []
            for title, locator, chapter in zip(titles[::2], titles[1::2], chapters, strict=True):
                assert locator['source'].startswith('p.')
                entries.append((chapter, title, locator))
                self.bookmarks[chapter] = book + ' · ' + title['source']
            self.toc.append(entries)

    def lines(self, text, size, width):
        layout = self.proof.layout(text, size, width - 2)
        for i in range(layout.lineCount()):
            line = layout.lineAt(i)
            a = line.textStart()
            raw = text[a:a + line.textLength()]
            yield a + len(raw) - len(raw.lstrip()), raw.strip()

    def block(self, key, text, size, baseline, width=sc.MEASURE, at=0, center=True, leading=None):
        """A wrapped heading is still a single, byte-exact source passage."""
        if self.source:
            self.source += '\n'
        start = len(self.source)
        self.source += text
        self.fragment(key, text, start, len(self.source))
        for number, (offset, segment) in enumerate(self.lines(text, size, width)):
            ink = self.proof.ink(segment, size)
            assert ink.width() <= width, (key, segment)
            if number:
                baseline = max(baseline + (leading or size * .68), self.last_bottom + 1 - ink.top())
            x = self.left + at - ink.left() + ((width - ink.width()) / 2 if center else 0)
            self.place(start + offset, start + offset + len(segment), x, baseline, size, ink)
        return self.last_bottom

    def opening(self, chapter):
        name = self.bookmarks.get(chapter, chapter)
        self.work = dict(title=chapter)
        self.new_page('opening', chapter)
        self.edition['sections'].append(dict(number=len(self.folios) + 1, name=name, pageId=self.pid))
        self.folios[chapter] = self.page['folio']

    def body(self, rows):
        group = []
        for row in rows:
            if group and not row['continuesParagraph']:
                self.paragraph(group)
                group = []
            group.append((row['id'], dict(text=row['text'], continuation=row['continuesParagraph'])))
        if group:
            self.paragraph(group)

    def contents(self):
        header = self.groups[CONTENTS[0]][0]['text'].split(' i ')[0]
        self.label('nav/contents', header, 50, 93)
        for index, entries in enumerate(self.toc):
            x = index * 251
            y = 137
            if index == 0:
                self.label('nav/toc/Preface', self.groups['Preface'][0]['text'].rstrip('.'), 25, y,
                           at=x, width=202, align='left')
                self.label('nav/folio/Preface', sc.digits(self.folios['Preface']), 24, y,
                           at=x + 204, width=31, align='right')
                y += 33
            book = self.groups[BOOK_NAMES[index]][-1]['text'].rstrip('.')
            self.label(f'nav/book/{index}', book, 34, y, at=x, width=235, align='left')
            y += 28
            items = []
            for chapter, title, _ in entries:
                # The word "chapter" is shared by every entry. Retain the Unta numeral and title.
                items.append((chapter, title['text'].split(' ', 1)[1]))
            for chapter, label in items:
                bottom = self.block('nav/toc/' + chapter, label, 22, y, width=202, at=x, center=False, leading=14)
                self.label('nav/folio/' + chapter, sc.digits(self.folios[chapter]), 24, y,
                           at=x + 204, width=31, align='right')
                y = max(y + 20, bottom + 15)
        boxes = [QRectF(*line['bounds']) for line in self.page['lines'][1:]]
        rule = QPainterPath()
        top, bottom = min(b.top() for b in boxes), max(b.bottom() for b in boxes)
        rule.addRect(QRectF(self.left + sc.MEASURE / 2 - .2, top, .4, bottom - top))
        assert not any(rule.boundingRect().intersects(box) for box in boxes)
        self.page['paths'] = [sc.pe.encode_path(rule, 'contents-column-divider')]

    def compose(self):
        title, first, second = self.groups['Title']
        self.new_page('title', 'Title page')
        self.block(title['id'], title['text'], 54, 346)
        self.label('nav/author', 'Jon Lok', 32, 397)
        self.new_page('blank', 'Blank')
        self.new_page('frontispiece', 'Frontispiece')
        bottom = self.block(first['id'], first['text'], 32, 310, width=430, at=28)
        self.block(second['id'], second['text'], 32, bottom + 53, width=430, at=28)
        self.new_page('contents', 'Contents')
        self.opening('Preface')
        heading, *rest = self.groups['Preface']
        self.block(heading['id'], heading['text'], 46, 99)
        self.y = 135
        self.body(rest)
        for book, entries in zip(BOOK_NAMES, self.toc, strict=True):
            for chapter_index, (chapter, _, _) in enumerate(entries):
                self.opening(chapter)
                y = 95
                if chapter_index == 0:
                    for row in self.groups[book]:
                        y = self.block(row['id'], row['text'], 38, y) + 32
                heading, *rest = self.groups[chapter]
                bottom = self.block(heading['id'], heading['text'], 44, y)
                self.y = bottom + 31
                self.body(rest)
            print(f'{book} composed through native page {len(self.state["pages"]) + 1}', flush=True)
        self.finish_page()
        pages = self.state['pages']
        self.state['pages'] = pages[:3]
        self.new_page('contents', 'Contents')
        self.contents()
        self.finish_page()
        self.state['pages'].extend(pages[4:])
        self.state['activeFrameId'] = self.state['pages'][0]['frames'][0]['frameId']
        self.edition['verses'].sort(key=lambda r: (r['fragments'][0]['pageId'], r['fragments'][0]['start']))
        return self.state


def verify(state, units, folios):
    sc.pe.validate(state)
    edition = state['printEdition']
    pages = {p['pageId']: sc.pe.text_of(p) for p in state['pages']}
    records = {r['id']: ''.join(pages[f['pageId']][f['start']:f['end']] for f in r['fragments'])
               for r in edition['verses']}
    assert [(k, v) for k, v in records.items() if k.startswith('locke-')] == [
        (u['id'], u['text']) for u in units if u['chapter'] not in CONTENTS]
    assert all(records['nav/folio/' + k] == sc.digits(f) for k, f in folios.items())
    actual = [edition['pages'][s['pageId']]['folio'] for s in edition['sections']]
    assert actual == list(folios.values())
    assert len(folios) == 31
    links, = sc.pe.contents_links(state).values()
    assert [link['page'] for link in links] == [folio + 4 for folio in actual]
    boxes = [QRectF(*link['bounds']) for link in links]
    assert all(not box.intersects(other) for i, box in enumerate(boxes) for other in boxes[i+1:])


def build():
    STAGE.mkdir(parents=True, exist_ok=True)
    ledger = sc.read(WORK / 'ledger.json')
    language, checksum = checked_source(ledger)
    volume = LockeVolume(ledger, language, checksum)
    state = volume.compose()
    verify(state, ledger['units'], volume.folios)
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
    verify(state, ledger['units'], volume.folios)
    physical = render_duplex(state, STAGE / PDF, TITLE, use_printed_folios=True)
    sc.write(STAGE / 'edition-manifest.json', dict(title=TITLE, author='John Locke', nativeSha256=sc.digest(STAGE / NATIVE),
             pdfSha256=sc.digest(STAGE / PDF), layoutReferenceSha256=sc.digest(sc.DEST),
             sourceProgressiveSha256=checksum, ledgerSha256=volume.edition['ledgerSha256'],
             englishSourceSha256=ledger['sourceSha256'], sourceWords=ledger['sourceWords'],
             exactNativeUnits=sum(u['chapter'] not in CONTENTS for u in ledger['units']),
             originalContentsUnitsReplaced=sum(u['chapter'] in CONTENTS for u in ledger['units']),
             nativePages=len(state['pages']), pdfPages=physical,
             duplexSheets=(physical+1)//2, marginsPt=dict(inside=72, outside=54, top=48, bottom=71),
             typeSizePt=sc.BODY, leadingPt=sc.LEADING, chapterAndFrontMatterFolios=volume.folios))
    print(f'Verified {len(state["pages"])} native pages and {physical} PDF pages.', flush=True)


def install():
    manifest = sc.read(STAGE / 'edition-manifest.json')
    for filename, key in ((NATIVE, 'nativeSha256'), (PDF, 'pdfSha256')):
        assert sc.digest(STAGE / filename) == manifest[key]
    assert manifest['sourceProgressiveSha256'] == sc.digest(SOURCE_BOOK)
    if DEST.exists():
        raise FileExistsError(DEST)
    with TemporaryDirectory(dir=DEST.parent) as scratch:
        folder = Path(scratch) / DEST.name
        folder.mkdir()
        for name in (NATIVE, PDF, 'edition-manifest.json'):
            shutil.copy2(STAGE / name, folder / name)
        folder.rename(DEST)
    print(DEST)


if __name__ == '__main__':
    import argparse
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('operation', choices=['build', 'install'])
    args = cli.parse_args()
    if args.operation == 'build':
        app = QApplication([])
        build()
    else:
        install()
