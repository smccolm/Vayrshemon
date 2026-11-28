"""Build and verify the thousand-page anthology from its saved publication inputs."""
import argparse
import hashlib
import json
from html import escape
from pathlib import Path
from urllib.parse import quote

from tools import poetic_anthology as book
from tools import poetic_anthology_print as letter
from tools import shakespeare_collected as sc
from tools.compose_historical_book import texts

PROGRESSIVE = book.BOOK
PRINT = letter.DEST
WORK = PROGRESSIVE / 'Working'
NATIVE = PROGRESSIVE / (book.TITLE + ' - Four-Column Progressive Edition.vay')


def content_hash(units):
    """Independent of pagination and TOC positions, sensitive to every passage."""
    digest = hashlib.sha256()
    for unit in sorted(units, key=lambda r: r['id']):
        if unit['id'].startswith('contents.'):
            continue
        fields = [unit[name] for name in ('id', 'text', 'gloss', 'source')]
        digest.update(json.dumps(fields, ensure_ascii=False, separators=(',', ':')).encode('utf8'))
        digest.update(b'\n')
    return digest.hexdigest()


def progressive(seed=None, workers=3, catalogue_path=None):
    book.BOOK, book.WORK, book.TARGET = PROGRESSIVE, WORK, NATIVE
    selection = sc.read(WORK / 'selection-validation.json')
    works = sc.read(WORK / 'works.json')
    assert sc.digest(WORK / 'works.json') == selection['catalogueSha256']
    if seed is not None:
        seed = Path(seed)
        prior = sc.read(seed.parent / 'Working' / 'source-validation.json')
        assert sc.digest(seed) == prior['sha256']
        folios = {w['id']: prior['entryOpenings'].get(w['id'], 1) for w in works}
    else:
        folios = {}
    fonts = [book.SOURCE_FONTS / name for name in (
        'NotoSerifJP-Ogura.ttf', 'NotoSerifSC-Shijing.ttf', 'NotoSerifSC-NorthernBallads.ttf')]
    book.build(True, initial_folios=folios, edition_lexicon=True, additional_source_fonts=fonts,
               measured_edition=seed, folio_workers=workers, catalogue_path=catalogue_path)
    verify_progressive()


def verify_progressive():
    selection = sc.read(WORK / 'selection-validation.json')
    source = sc.read(WORK / 'source-validation.json')
    material = sc.read(WORK / 'ledger.json')['units']
    assert content_hash(material) == selection['bodySha256']
    assert sc.digest(NATIVE) == source['sha256']
    assert source['reconstructedAllSourceLines'] and source['contentsPagesVerified']
    state = sc.unpack(sc.read(NATIVE))['state']
    rows = {u['id']: u for u in material}
    spreads = sc.read(WORK / 'page-index.json')['spreads']
    ordered = []
    for spread in spreads:
        pages = state['pages'][spread['leftPage'] - 1:spread['rightPage']]
        frames = [f for pg in pages for f in sorted(pg['frames'], key=lambda f: int(f['x']))]
        assert len(frames) == 4
        ids = spread['unitIds']
        for frame, field in zip(frames, ('text', 'text', 'gloss', 'source'), strict=True):
            assert texts(frame) == [rows[k][field] for k in ids], (spread['leftPage'], field)
        ordered.extend(ids)
    assert ordered == list(rows)
    receipt = dict(works=source['works'], sourceLines=source['sourceLines'], alignedUnits=len(rows),
                   pages=len(state['pages']), nativeSha256=source['sha256'], bodySha256=selection['bodySha256'],
                   preservedWorks=selection['preservedWorks'], nativeFourColumnsVerified=True,
                   sourceLinesReconstructed=True, nativeReopenIdentical=True)
    sc.write(WORK / 'publication-check.json', receipt)
    print('Verified all four saved columns.', receipt, flush=True)


def print_edition():
    letter.BOOK, letter.WORK, letter.TARGET, letter.DEST = PROGRESSIVE, WORK, NATIVE, PRINT
    letter.build(document_id='document.poetic-anthology.thousand-page.letter', target_pages=1000)
    manifest = sc.read(PRINT / letter.MANIFEST)
    assert manifest['duplexSheets'] == 500
    catalogue(manifest)


def print_proofs():
    from tools import poetic_anthology_print_proof as proof
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    letter.DEST = PRINT
    letter.STAGE = book.ROOT / '.local' / 'anthology-thousand-print-proof'
    manifest = sc.read(PRINT / letter.MANIFEST)
    with letter.PdfReader(PRINT / letter.PDF) as pdf:
        preferences = pdf.trailer['/Root']['/ViewerPreferences']
        assert preferences['/Duplex'] == '/DuplexFlipLongEdge'
        assert preferences['/PrintScaling'] == '/None'
        assert len(pdf.pages) == 1000
        assert all(tuple(pg.mediabox) == (0, 0, 612, 792) for pg in pdf.pages)
    samples = ('wisdomsayings','northmulan','northpipa','marinerballad','masambaelegy',
               'andalusromance18','wolnekartografia','portraitgrunge','bookcaseballad','harlemdancer')
    proof.prove([k for k in samples if k in manifest['sections']])
    receipt = PRINT / 'Working' / 'print-proof.json'
    results = sc.read(receipt)
    results.update(letterMediaBoxesVerified=1000, duplexFlip='long edge', printScaling='none')
    sc.write(receipt, results)


def catalogue(manifest):
    works = sc.read(WORK / 'works.json')
    entries = manifest['sections']
    assert list(entries) == [w['id'] for w in works]
    rows = ['<!doctype html><html lang="en"><meta charset="utf-8"><title>Contents and sources · '
            + escape(book.TITLE) + '</title><style>body{color:#29251e;background:#fcfaf4;max-width:75rem;'
            'margin:2.8rem auto;padding:0 1.5rem;font:17px Georgia,serif}h1{font-size:2.4rem;font-weight:normal}'
            'table{width:100%;border-collapse:collapse}td,th{padding:.5rem .6rem;text-align:left;vertical-align:top;'
            'border-bottom:1px solid #d6cdbc}a{color:#623e25}small{color:#514c43}p{line-height:1.45}'
            'details{margin:.25rem 0}summary{cursor:pointer;font-size:.85rem}</style><h1>' + escape(book.TITLE)
            + '</h1><p>' + f'{len(works):,} poems and songs · {manifest["physicalPages"]:,} pages · {manifest["duplexSheets"]:,} duplex Letter sheets. '
            'Each title opens its page in the print edition. Folio 1 begins with the first work.</p>'
            '<table><thead><tr><th>Poem or song</th><th>Date</th><th>Tradition</th><th>Folio</th>'
            '<th>Witnesses</th></tr></thead><tbody>']
    for w in works:
        entry = entries[w['id']]
        links = ' · '.join('<a href="' + escape(url, quote=True) + '">' + str(i) + '</a>'
                           for i, url in enumerate(w['sources'], 1))
        title = escape(w['title'])
        original = w.get('originalTitle')
        if original and original.casefold() != w['title'].casefold():
            title += '<br><small>' + escape(original) + '</small>'
        note = w.get('note', '')
        if note:
            links += '<details><summary>Edition note</summary><p>' + escape(note) + '</p></details>'
        rows.append('<tr><td><a href="' + quote(letter.PDF) + '#page=' + str(entry['physicalPage']) + '">'
                    + title + '</a></td><td>' + escape(w['date']) + '</td><td>' + escape(w['genre'])
                    + '</td><td>' + str(entry['folio']) + '</td><td>' + links + '</td></tr>')
    rows.append('</tbody></table><p><a href="Song%20license.txt">Credits and adaptation licenses</a></p></html>')
    (PRINT / 'Contents and sources.html').write_text('\n'.join(rows), encoding='utf8')


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('edition', choices=('progressive', 'print', 'verify-progressive', 'print-proofs'))
    cli.add_argument('--seed', type=Path, help='A verified earlier progressive manuscript to reuse for layout.')
    cli.add_argument('--folio-workers', type=int, default=3)
    options = cli.parse_args()
    if options.edition == 'progressive':
        progressive(options.seed, options.folio_workers)
    elif options.edition == 'print':
        print_edition()
    elif options.edition == 'verify-progressive':
        verify_progressive()
    else:
        print_proofs()
