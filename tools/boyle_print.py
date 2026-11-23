"""Compose Boyle's issued Vayrshemon in the Paradise Lost Letter print layout."""
import argparse
import base64
from itertools import groupby
from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory

from PySide6.QtCore import QRectF
from PySide6.QtWidgets import QApplication

from tools import shakespeare_collected as sc
from tools.boyle_working import BOOK, ROOT, SOURCE, TITLE, WORK
from tools.compose_historical_book import texts
from tools.paradise_lost_print import MiltonVolume, place_title_art, title_art_metadata
from tools.shakespeare_collected_pdf import render_duplex

REFERENCE = ROOT / 'Saves/Paradise Lost - Letter Print Edition/Paradise Lost.vay'
SOURCE_BOOK = BOOK / (BOOK.name + '.vay')
DEST = ROOT / 'Saves' / (TITLE + ' - Letter Print Edition')
STAGE = ROOT / '.local/boyle-letter-print'
NATIVE = TITLE + '.vay'
PDF = TITLE + ' - Duplex Print.pdf'
TITLE_ART = ROOT / 'Inputs/Print artwork/The Sceptical Chymist - Title Page - Approved II.png'
QUOTE = [f'boyle.590.{i:03d}' for i in range(1, 5)]
PROPOSITIONS = {78, 85, 96, 103}
# These clauses start standalone paragraphs in the print frontispiece.
FRONTISPIECE_INITIALS = {'boyle.001.002': ('l', 'L'), 'boyle.001.003': ('g', 'G')}


def print_text(row):
    text = row['text']
    if row['id'] in FRONTISPIECE_INITIALS:
        minima, maxima = FRONTISPIECE_INITIALS[row['id']]
        assert text.startswith((minima, maxima))
        return maxima + text[1:]
    return text


def checked_source(ledger):
    report = sc.read(WORK / 'layout-validation.json')
    assert ledger['status'] == 'complete' and ledger['nextSourceLine'] is None
    assert ledger['sourceWords'] == ledger['translatedSourceWords']
    assert sc.digest(SOURCE) == ledger['sourceSha256']
    checksum = sc.digest(SOURCE_BOOK)
    assert checksum == report['sha256']
    state = sc.unpack(sc.read(SOURCE_BOOK))['state']
    rows = iter(ledger['units'])
    for left, right in zip(state['pages'][::2], state['pages'][1::2], strict=True):
        columns = [texts(f) for p in (left, right) for f in sorted(p['frames'], key=lambda f: int(f['x']))]
        for passage in zip(*columns, strict=True):
            unit = next(rows)
            assert passage == tuple(unit[k] for k in ('text', 'text', 'gloss', 'source')), unit['id']
    assert next(rows, None) is None
    return state['language'], checksum


class BoyleVolume(MiltonVolume):
    def __init__(self, ledger, language, checksum):
        self.state = sc.unpack(sc.read(REFERENCE))['state']
        original = self.state['printEdition']
        assert original['typography'] == sc.pe.COMPACT_TYPE and original['layoutVersion'] == sc.pe.COLLECTED
        header = next(r for r in original['verses'] if r['id'] == 'nav/contents')
        toc = self.state['pages'][3]
        self.contents_title = ''.join(sc.pe.text_of(toc)[f['start']:f['end']] for f in header['fragments'])
        assert all(f['pageId'] == toc['pageId'] for f in header['fragments'])
        self.prototype = self.state['pages'][0]
        self.proof = sc.Typesetter(next(f for f in self.state['fontSources'] if f['fontId'] == sc.pe.DRAMA_PUNCT))
        self.edition = dict(version=1, layoutVersion=original['layoutVersion'], typography=dict(original['typography']),
                            languageVersion=ledger['languageVersion'], sourceSha256=checksum,
                            ledgerSha256=sc.digest(WORK / 'ledger.json'), assets={}, pages={}, verses=[], sections=[])
        self.state.update(title=TITLE, documentId='document.boyle.sceptical-chymist.letter', revision=0,
                          language=language, pages=[], printEdition=self.edition)
        self.records = {}
        self.page = self.work = None
        self.start_body = 5
        self.rebalanced_endings = []
        self.folios = {}
        self.units = {r['id']: r for r in ledger['units']}
        self.groups = {key: list(rs) for key, rs in groupby(ledger['units'], key=lambda r: r['chapter'])}
        self.chapters = [key for key in self.groups if key != 'Title']
        self.bookmarks = {k: k for k in self.chapters}
        self.bookmarks.update({'First dialogue': 'Part of the First Dialogue',
                               'Second title': 'Second title, epigraph and imprint',
                               'Part VI': 'Part VI · A Paradoxical Appendix'})
        self.labels = {}
        for key in self.chapters:
            text = self.groups[key][0]['text']
            if key.startswith('Part '):
                self.labels[key] = text.rstrip('.').rsplit('. ', 1)[1]
            elif key == 'Preface':
                self.labels[key] = text.rstrip('.').rsplit(' ', 1)[1]
            elif key == 'First dialogue':
                self.labels[key] = self.groups[key][1]['text'].rstrip('.')
            elif key == 'Second title':
                self.labels[key] = text.split(',', 1)[0]
            elif key == 'Publisher’s notice':
                # The opening phrase in the issued text names the publisher.
                self.labels[key] = ' '.join(text.split()[:2])
            else:
                assert key == 'Conclusion'
                self.labels[key] = text.rstrip('.')

    def contents(self):
        self.label('nav/contents', self.contents_title, 50, 100)
        half = (len(self.chapters) + 1) // 2
        for col, entries in enumerate((self.chapters[:half], self.chapters[half:])):
            x, y = 251 * col, 161
            for key in entries:
                bottom = self.block('nav/toc/' + key, self.labels[key], 30, y,
                                    width=195, at=x, center=False, leading=18)
                self.label('nav/folio/' + key, sc.digits(self.folios[key]), 24, y,
                           at=x + 204, width=31, align='right')
                y = max(y + 36, bottom + 23)
        frame = dict(x=sc.mp(self.left), width=sc.mp(sc.MEASURE))
        self.page['paths'] = [sc.contents_divider(dict(frames=[frame]), self.page)]

    def centered(self, row, size, y, inset=0):
        return self.block(row['id'], print_text(row), size, y, at=inset, width=sc.MEASURE - 2 * inset)

    def title_page(self):
        self.new_page('title', 'Title page')

    def frontispiece(self):
        self.new_page('frontispiece', 'Frontispiece')
        sub, continuation, introduction, byline = self.groups['Title'][1:]
        bottom = self.centered(sub, 28, 92, 35)
        bottom = self.centered(continuation, 28, bottom + 18, 35)
        bottom = self.centered(introduction, 25, bottom + 25, 35)
        bottom = self.centered(byline, 28, bottom + 29, 18)
        quote = ' '.join(self.units[k]['text'] for k in QUOTE)
        bottom = self.block('nav/frontispiece/quotation', quote, 32, bottom + 76, width=400, at=43)
        self.block('nav/frontispiece/reference', self.labels['Conclusion'], 26, bottom + 40)

    def second_title(self, rows):
        y = 120
        for r in rows:
            first = r['id'].endswith('.001')
            size = 36 if r['sourceLine'] == 64 and first else 28
            gap = 27 if first else 20
            if r['sourceLine'] == 68 or (r['sourceLine'] == 66 and first):
                y += 23
            y = self.centered(r, size, y, 28) + gap

    def chapter(self, key):
        self.opening(key)
        rows = iter(self.groups[key])
        if key == 'Second title':
            self.second_title(rows)
            return
        if key == 'Publisher’s notice':
            self.block('nav/publisher-heading', self.labels[key], 42, 95)
            self.y = self.last_bottom + 32
        else:
            header = next(rows)
            size = 33 if key == 'First dialogue' else 42
            self.y = self.centered(header, size, 95) + 30
            if key == 'First dialogue':
                self.y = self.centered(next(rows), 32, self.y) + 33

        for line, group in groupby(rows, key=lambda r: r['sourceLine']):
            paragraph = [(r['id'], dict(text=r['text'], continuation=r['continuesParagraph'])) for r in group]
            heading = line in PROPOSITIONS
            self.paragraph(paragraph, centered=heading or line in (592, 604), keep_next=heading)

    def compose(self):
        self.title_page()
        self.new_page('blank', 'Blank')
        self.frontispiece()
        self.new_page('contents', 'Contents')
        for key in self.chapters:
            self.chapter(key)
        self.finish_page()
        body = self.state['pages'][4:]
        self.state['pages'] = self.state['pages'][:3]
        self.new_page('contents', 'Contents')
        self.contents()
        self.finish_page()
        self.state['pages'].extend(body)
        self.state['activeFrameId'] = self.state['pages'][0]['frames'][0]['frameId']
        self.edition['verses'].sort(key=lambda r: (r['fragments'][0]['pageId'], r['fragments'][0]['start']))
        place_title_art(self.state, artwork=TITLE_ART, title_units={self.groups['Title'][0]['id']})
        return self.state


def verify(state, ledger, folios):
    sc.pe.validate(state)
    edition = state['printEdition']
    pages = state['pages']
    source = {p['pageId']: sc.pe.text_of(p) for p in pages}
    records = {r['id']: ''.join(source[f['pageId']][f['start']:f['end']] for f in r['fragments'])
               for r in edition['verses']}
    expected = [(r['id'], print_text(r)) for r in ledger['units']]
    _, full_title = expected.pop(0)
    assert full_title.endswith(':') and ledger['units'][0]['chapter'] == 'Title'
    assert [(k, v) for k, v in records.items() if not k.startswith('nav/')] == expected
    assert records['nav/frontispiece/quotation'] == ' '.join(records[k] for k in QUOTE)
    assert [edition['pages'][p['pageId']]['kind'] for p in pages[:4]] == ['title','blank','frontispiece','contents']
    front = [print_text(r) for r in ledger['units'] if r['chapter'] == 'Title'][1:]
    title_page = edition['pages'][pages[0]['pageId']]
    assert not source[pages[0]['pageId']] and not title_page['lines']
    plate, = title_page['images']
    assert plate['asset'] == sc.digest(TITLE_ART)
    assert base64.b64decode(edition['assets'][plate['asset']]['png']) == TITLE_ART.read_bytes()
    assert source[pages[2]['pageId']] == '\n'.join([
        *front, records['nav/frontispiece/quotation'], records['nav/frontispiece/reference']])
    assert not source[pages[1]['pageId']]
    assert all(records['nav/folio/' + k] == sc.digits(v) for k, v in folios.items())
    links, = sc.pe.contents_links(state).values()
    assert [l['page'] for l in links] == [f + 4 for f in folios.values()]
    assert [s['pageId'] for s in edition['sections']] == [pages[l['page'] - 1]['pageId'] for l in links]
    assert all(edition['pages'][s['pageId']]['kind'] == 'opening' for s in edition['sections'])
    rects = [QRectF(*l['bounds']) for l in links]
    assert all(not b.intersects(c) for i,b in enumerate(rects) for c in rects[i+1:])
    for n, p in enumerate(pages, 1):
        spec = edition['pages'][p['pageId']]
        assert spec['folio'] == (n - 4 if n > 4 else None)
        assert int(p['margins']['left']) == int(sc.mp(63 if n == 1 else 54 if n % 2 else 72))
        boxes = [QRectF(*l['bounds']) for l in spec['lines']]
        assert all(not b.intersects(c) for i,b in enumerate(boxes) for c in boxes[i+1:]), n
        for path in spec['paths']:
            assert path['role'] == 'contents-column-divider' and n == 4
            assert all(not sc.pe.decode_path(path).intersects(b) for b in boxes)
    return sc.pe.hash_text('\n'.join(t for _, t in expected))


def build():
    STAGE.mkdir(parents=True, exist_ok=True)
    ledger = sc.read(WORK / 'ledger.json')
    language, checksum = checked_source(ledger)
    reference_hash = sc.digest(REFERENCE)
    volume = BoyleVolume(ledger, language, checksum)
    state = volume.compose()
    text_hash = verify(state, ledger, volume.folios)
    session = sc.FileSession(ROOT, recovery=False)
    session.remember = lambda _: None
    session.log.emit = lambda *args, **kwargs: None
    try:
        for f in state['fontSources']:
            session.fonts.register(session.fonts.document_path(f['path'], f['sha256']), f['sha256'])
        session._restore(state, take_ownership=True)
        session._state = session.capture()
        with TemporaryDirectory(dir=STAGE) as scratch:
            staged_native = Path(scratch) / NATIVE
            session.save(staged_native, preview_mode='two')
            before = session.capture()
            session.open(staged_native, advance_revision=False)
            state = session.capture()
            assert state == before and session.saved_page_mode == 'two'
            staged_native.replace(STAGE / NATIVE)
    finally:
        session.finish()
    assert verify(state, ledger, volume.folios) == text_hash
    physical = render_duplex(state, STAGE / PDF, TITLE, use_printed_folios=True)
    assert sc.digest(REFERENCE) == reference_hash and sc.digest(SOURCE_BOOK) == checksum
    sc.write(STAGE / 'edition-manifest.json', dict(
        title=TITLE, author='Robert Boyle', nativeSha256=sc.digest(STAGE / NATIVE), pdfSha256=sc.digest(STAGE / PDF),
        sourceProgressiveSha256=checksum, layoutReference=REFERENCE.relative_to(ROOT).as_posix(),
        layoutReferenceSha256=reference_hash, ledgerSha256=volume.edition['ledgerSha256'],
        englishSourceSha256=ledger['sourceSha256'], sourceWords=ledger['sourceWords'],
        sourceUnits=len(ledger['units']), exactNativeUnits=sum(print_text(r) == r['text'] for r in ledger['units'][1:]),
        titleUnitsInArtwork=1,
        omittedUnits=0, printedNativeTextSha256=text_hash, titleArtwork=title_art_metadata(state, artwork=TITLE_ART),
        sourceNativeTextSha256=sc.pe.hash_text('\n'.join(r['text'] for r in ledger['units'])),
        titlePunctuationEdit=dict(unit=volume.groups['Title'][0]['id'], removedSuffix=':'),
        nativePages=len(state['pages']), pdfPages=physical, duplexSheets=(physical+1)//2, leadingBindingBlanks=1,
        contentsNativePages=[4], linkedContentsEntries=len(volume.chapters), chapterAndFrontMatterFolios=volume.folios,
        marginsPt=dict(inside=72, outside=54, top=48, bottom=71), typeSizePt=sc.BODY, leadingPt=sc.LEADING,
        frontispieceQuotationUnits=QUOTE, titlePage='Illustrated main title',
        frontispieceInitialMaxima={k: dict(source=a, printed=b) for k, (a, b) in FRONTISPIECE_INITIALS.items()},
        frontispieceOpeningUnits=[row['id'] for row in volume.groups['Title'][1:]],
        saveReopenIdentical=True, allOtherNativeUnitsMatchProgressive=True))
    print(f'Verified {len(state["pages"])} native pages and {physical} PDF pages.', flush=True)


def install():
    manifest = sc.read(STAGE / 'edition-manifest.json')
    proof = sc.read(STAGE / 'proof-validation.json')
    for f, key in ((NATIVE, 'nativeSha256'), (PDF, 'pdfSha256')):
        assert sc.digest(STAGE / f) == manifest[key] == proof[key]
    assert sc.digest(SOURCE_BOOK) == manifest['sourceProgressiveSha256']
    if DEST.exists():
        raise FileExistsError(DEST)
    with TemporaryDirectory(dir=DEST.parent) as scratch:
        folder = Path(scratch) / DEST.name
        folder.mkdir()
        for f in (NATIVE, PDF, 'edition-manifest.json', 'proof-validation.json'):
            shutil.copy2(STAGE / f, folder / f)
        (folder / 'Printing notes.txt').write_text(
            f"{TITLE} — Letter Print Edition\n\n"
            f"{manifest['nativePages']} native pages. {manifest['pdfPages']} PDF pages on "
            f"{manifest['duplexSheets']} duplex sheets.\n"
            "Print at Actual Size on US Letter paper, double-sided, flipping on the long edge. "
            "Keep the leading binding blank to match the facing spreads in the Reader. "
            "The contents numbers are the printed Unta folios.\n", encoding='utf8')
        folder.rename(DEST)


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('operation', choices=['build', 'proof', 'install'])
    args = cli.parse_args()
    if args.operation == 'build':
        app = QApplication([])
        build()
    elif args.operation == 'proof':
        from tools.paradise_lost_print_proof import prove
        app = QApplication([])
        prove(sys.modules[__name__])
    else:
        install()
