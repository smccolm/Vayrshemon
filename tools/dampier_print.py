"""Set the issued Dampier manuscript as a Letter reading edition."""
import argparse
from base64 import b64decode
from itertools import groupby
from pathlib import Path
from shutil import copy2
import sys
from tempfile import TemporaryDirectory

from PySide6.QtCore import QRectF
from PySide6.QtWidgets import QApplication

from tools import shakespeare_collected as sc
from tools.boyle_print import BoyleVolume, REFERENCE
from tools.compose_historical_book import texts
from tools.dampier_working import BOOK, ROOT, SOURCE, TITLE, WORK
from tools.paradise_lost_print import place_title_art, title_art_metadata
from tools.shakespeare_collected_pdf import render_duplex


SOURCE_BOOK = BOOK / (BOOK.name + '.vay')
DEST = ROOT / 'Saves' / (TITLE + ' - Letter Print Edition')
STAGE = ROOT / '.local/dampier-letter-print'
NATIVE = TITLE + '.vay'
PDF = TITLE + ' - Duplex Print.pdf'
TITLE_ART = ROOT / 'Inputs/Print artwork' / (TITLE + ' - Title Page - Approved.png')


def checked_source(ledger):
    checksum = sc.digest(SOURCE_BOOK)
    status = sc.read(WORK / 'translation-status.json')
    assert checksum == status['publicationSha256'] == sc.read(WORK / 'layout-validation.json')['sha256']
    assert sc.digest(SOURCE) == ledger['sourceSha256']
    state = sc.unpack(sc.read(SOURCE_BOOK))['state']
    rows = iter(ledger['units'])
    for left, right in zip(state['pages'][::2], state['pages'][1::2], strict=True):
        columns = [texts(frame) for page in (left, right)
                   for frame in sorted(page['frames'], key=lambda frame: int(frame['x']))]
        for passage in zip(*columns, strict=True):
            row = next(rows)
            assert passage == tuple(row[k] for k in ('text', 'text', 'gloss', 'source')), row['id']
    assert next(rows, None) is None
    assert status['alignedPassages'] == len(ledger['units'])
    return state['language'], checksum


class DampierVolume(BoyleVolume):
    def __init__(self, ledger, language, checksum):
        self.state = sc.unpack(sc.read(REFERENCE))['state']
        original = self.state['printEdition']
        assert original['layoutVersion'] == sc.pe.COLLECTED and original['typography'] == sc.pe.COMPACT_TYPE
        self.prototype = self.state['pages'][0]
        self.proof = sc.Typesetter(next(f for f in self.state['fontSources'] if f['fontId'] == sc.pe.DRAMA_PUNCT))
        self.edition = dict(version=1, layoutVersion=sc.pe.COLLECTED, typography=dict(original['typography']),
                            languageVersion=ledger['languageVersion'], sourceSha256=checksum,
                            ledgerSha256=sc.digest(WORK / 'ledger.json'), pages={}, verses=[], sections=[], assets={})
        self.state.update(title=TITLE, documentId='document.dampier.new-voyage.letter', revision=0,
                          language=language, pages=[], printEdition=self.edition)
        self.records = {}
        self.page = self.work = None
        self.start_body = 5
        self.rebalanced_endings = []
        self.folios = {}
        self.groups = {k: list(g) for k, g in groupby(ledger['units'], key=lambda r: r['chapter'])}
        # The supplied map is a caption. Set it with the preceding original contents.
        self.groups['Contents'].extend(self.groups.pop('World map'))
        # The sectional title introduces the narrative that starts with Chapter I.
        travels = self.groups['Introduction'][-1]
        assert travels['sourceLine'] == 119
        self.groups['Chapter I'].insert(0, self.groups['Introduction'].pop())
        self.chapters = [k for k in self.groups if k != 'Title']
        self.bookmarks = {'Contents': "Dampier’s original chapter summaries"}
        self.labels = {k: rows[0]['text'].rstrip('.') for k, rows in self.groups.items()}
        self.labels['Dedication'] = self.labels['Dedication'].split(',', 1)[0]
        self.labels['Introduction'] = self.groups['Introduction'][1]['text'].rstrip('.')
        self.labels['Chapter I'] = self.groups['Chapter I'][1]['text'].rstrip('.')
        self.contents_title = self.labels['Contents']

    def set_paragraph(self, rows, centered=False, keep_next=False):
        items = [(r['id'], dict(text=r['text'], continuation=r['continuesParagraph'])) for r in rows]
        self.paragraph(items, centered=centered, keep_next=keep_next)

    def title_page(self):
        title = self.groups['Title'][0]
        assert title['source'].rstrip('.').casefold() == TITLE.casefold()
        self.new_page('title', 'Title page')
        self.block(title['id'], title['text'].removesuffix('.'), 54, 355)

    def frontispiece(self):
        self.new_page('frontispiece', 'Original title particulars and imprint')
        self.y = 202
        for line, rows in groupby(self.groups['Title'][1:], key=lambda r: r['sourceLine']):
            self.y += 20 if line in (9, 13) else 4
            self.set_paragraph(rows, centered=True)

    def chapter(self, key):
        self.opening(key)
        groups = groupby(self.groups[key], key=lambda r: r['sourceLine'])
        self.y = 91
        for line, group in groups:
            rows = list(group)
            chapter_title = rows[0]['source'].startswith(('CHAP.', 'CHAP '))
            if line in (25, 43, 89, 91, 119, 2177) or chapter_title:
                row, = rows
                size = 34 if line in (89, 119) else 44
                self.y = self.block(row['id'], row['text'], size, self.y) + 31
            else:
                caption = line in (87, 117, 253)
                deck = line in (15, 93) or (key.startswith('Chapter ') and
                    line == (self.groups[key][1 if key == 'Chapter I' else 0]['sourceLine'] + 2))
                if caption:
                    self.y += 9
                self.set_paragraph(rows, centered=caption or deck, keep_next=deck)
                self.y += 14 if deck else 3

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
    pages, edition = state['pages'], state['printEdition']
    source = {p['pageId']: sc.pe.text_of(p) for p in pages}
    expected = [(r['id'], r['text']) for r in ledger['units'][1:]]
    actual = [(r['id'], ''.join(source[f['pageId']][f['start']:f['end']] for f in r['fragments']))
              for r in edition['verses'] if not r['id'].startswith('nav/')]
    assert actual == expected
    assert not source[pages[0]['pageId']] and not source[pages[1]['pageId']]
    plate, = edition['pages'][pages[0]['pageId']]['images']
    assert plate['asset'] == sc.digest(TITLE_ART)
    assert b64decode(edition['assets'][plate['asset']]['png'], validate=True) == TITLE_ART.read_bytes()
    assert [edition['pages'][p['pageId']]['kind'] for p in pages[:4]] == ['title','blank','frontispiece','contents']
    links, = sc.pe.contents_links(state).values()
    assert [l['page'] for l in links] == [4 + f for f in folios.values()]
    assert [s['pageId'] for s in edition['sections']] == [pages[l['page'] - 1]['pageId'] for l in links]
    for n, p in enumerate(pages, 1):
        spec = edition['pages'][p['pageId']]
        assert spec['folio'] == (n - 4 if n > 4 else None)
        assert int(p['margins']['left']) == int(sc.mp(63 if n == 1 else 54 if n % 2 else 72))
        boxes = [QRectF(*l['bounds']) for l in spec['lines']]
        assert all(not b.intersects(c) for i, b in enumerate(boxes) for c in boxes[i + 1:]), n
        assert all(not sc.pe.decode_path(rule).intersects(b) for rule in spec['paths'] for b in boxes)
    return sc.pe.hash_text('\n'.join(t for _, t in actual))


def build(*, update_title=False):
    STAGE.mkdir(parents=True, exist_ok=True)
    ledger = sc.read(WORK / 'ledger.json')
    if not update_title and (ledger['status'] != 'complete' or ledger.get('nextSourceLine') is not None or
                             ledger.get('sourceWordsAccountedFor') != ledger['sourceWords']):
        raise ValueError('The complete Dampier print edition needs a source-accounted progressive manuscript.')
    language, checksum = checked_source(ledger)
    volume = DampierVolume(ledger, language, checksum)
    if update_title:
        prior = sc.read(DEST / 'edition-manifest.json')
        assert sc.digest(DEST / NATIVE) == prior['nativeSha256']
        assert prior['sourceProgressiveSha256'] == checksum
        state = sc.unpack(sc.read(DEST / NATIVE))['state']
        volume.folios = prior['chapterAndFrontMatterFolios']
        place_title_art(state, artwork=TITLE_ART, title_units={ledger['units'][0]['id']})
    else:
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
            path = Path(scratch) / NATIVE
            session.save(path, preview_mode='two')
            before = session.capture()
            session.open(path, advance_revision=False)
            state = session.capture()
            assert state == before and session.saved_page_mode == 'two'
            path.replace(STAGE / NATIVE)
    finally:
        session.finish()
    assert verify(state, ledger, volume.folios) == text_hash
    physical = render_duplex(state, STAGE / PDF, TITLE, use_printed_folios=True)
    assert sc.digest(SOURCE_BOOK) == checksum
    pending = {r['id']: [int(f['pageId'].split('.')[-1]) - 4 for f in r['fragments']]
               for r in state['printEdition']['verses'] if r['id'] in ledger['pendingUnits']}
    summary_ids = {r['id'] for r in ledger['units'] if r.get('sourceTreatment')}
    source_notes = sc.read(WORK / 'source-treatments.json') if summary_ids else {}
    summary_spans = sum(len(source_notes[u].get('spans', [None])) for u in summary_ids)
    summary_folios = {r['id']: sorted({int(f['pageId'].split('.')[-1]) - 4 for f in r['fragments']})
                      for r in state['printEdition']['verses'] if r['id'] in summary_ids}
    assert summary_ids == summary_folios.keys()
    sc.write(STAGE / 'edition-manifest.json', dict(
        title=TITLE, author='William Dampier', translationStatus=ledger['status'], lastSection=volume.chapters[-1],
        nativeSha256=sc.digest(STAGE / NATIVE), pdfSha256=sc.digest(STAGE / PDF), sourceProgressiveSha256=checksum,
        ledgerSha256=volume.edition['ledgerSha256'], englishSourceSha256=ledger['sourceSha256'],
        sourceUnits=len(ledger['units']), suppliedWords=ledger['sourceWords'], translatedWords=ledger['translatedSourceWords'],
        accountedSourceWords=ledger.get('sourceWordsAccountedFor',ledger['translatedSourceWords']),
        sourceWordsInSummaryPassages=ledger.get('sourceWordsInSummaryPassages',0),
        editorialSummarySpans=summary_spans,
        editorialSummaryUnits=[r['id'] for r in ledger['units'] if r.get('sourceTreatment')],
        editorialSummaryPrintedFolios=summary_folios,
        pendingUnitPrintedFolios=pending, titleArtwork=title_art_metadata(state, artwork=TITLE_ART),
        titleUnitsInArtwork=1, otherNativeUnitsExact=len(ledger['units'])-1,
        layoutReference=REFERENCE.relative_to(ROOT).as_posix(), layoutReferenceSha256=sc.digest(REFERENCE),
        printedNativeTextSha256=text_hash, nativePages=len(state['pages']), pdfPages=physical, duplexSheets=(physical+1)//2,
        linkedContentsEntries=len(volume.chapters), chapterAndFrontMatterFolios=volume.folios,
        leadingBindingBlanks=1, saveReopenIdentical=True))
    print(f'{len(state["pages"])} native pages, {physical} PDF pages, {len(volume.folios)} linked sections.', flush=True)


def install():
    receipt = sc.read(STAGE / 'edition-manifest.json')
    proof = sc.read(STAGE / 'proof-validation.json')
    assert sc.digest(SOURCE_BOOK) == receipt['sourceProgressiveSha256']
    for name, key in ((NATIVE, 'nativeSha256'), (PDF, 'pdfSha256')):
        assert sc.digest(STAGE / name) == receipt[key] == proof[key]
    current = {}
    if DEST.exists():
        current = {name: sc.digest(DEST / name) for name in (NATIVE, PDF, 'edition-manifest.json',
                                                             'proof-validation.json','Printing notes.txt')}
        previous = sc.read(DEST / 'edition-manifest.json')
        if current[NATIVE] != previous['nativeSha256'] or current[PDF] != previous['pdfSha256']:
            raise ValueError('The existing print publication differs from its recorded hashes.')
    with TemporaryDirectory(dir=DEST.parent) as scratch:
        folder = Path(scratch) / DEST.name
        folder.mkdir()
        for name in (NATIVE, PDF, 'edition-manifest.json', 'proof-validation.json'):
            copy2(STAGE / name, folder / name)
        notes = [TITLE, 'William Dampier', '',
                 f"This impression follows the progressive edition through {receipt['lastSection']}.",
                 f"{receipt['accountedSourceWords']:,} of {receipt['suppliedWords']:,} source words are accounted for."]
        if receipt['editorialSummaryUnits']:
            notes.append(f"{receipt['translatedWords']:,} words are translated directly. "
                         f"Square brackets mark abbreviated wording for "
                         f"{receipt['sourceWordsInSummaryPassages']:,} original words across "
                         f"{len(receipt['editorialSummaryUnits'])} passages. "
                         "The print folios are listed in edition-manifest.json. The progressive edition’s "
                         "Working/source-treatments.json identifies the exact spans within each source passage.")
        for unit, numbers in receipt['pendingUnitPrintedFolios'].items():
            notes.append(f"Printed folio {numbers[0]} retains the progressive manuscript’s dash at {unit}.")
        notes.extend(['', 'Print at Actual Size on US Letter paper, double-sided, flipping on the long edge.',
                      f"Keep the leading binding blank. {receipt['pdfPages']} PDF pages on {receipt['duplexSheets']} sheets."])
        (folder / 'Printing notes.txt').write_text('\n'.join(notes) + '\n', encoding='utf-8')
        if not current:
            folder.rename(DEST)
            return
        replaced = []
        try:
            for name, checksum in current.items():
                if sc.digest(DEST / name) != checksum:
                    raise ValueError('Print file changed during installation: ' + name)
                copy2(DEST / name, Path(scratch) / name)
                (folder / name).replace(DEST / name)
                replaced.append(name)
        except BaseException:
            for name in reversed(replaced):
                (Path(scratch) / name).replace(DEST / name)
            raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['build', 'update-title', 'proof', 'install'])
    operation = parser.parse_args().operation
    if operation == 'install':
        install()
    else:
        app = QApplication([])
        if operation == 'proof':
            from tools.paradise_lost_print_proof import prove
            prove(sys.modules[__name__])
        else:
            build(update_title=operation == 'update-title')
