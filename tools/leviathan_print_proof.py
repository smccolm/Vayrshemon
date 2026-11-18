"""Exercise the real contents links and compare Reader/Poppler print proofs."""
import subprocess
from unittest.mock import patch

from PIL import Image, ImageDraw, ImageOps
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from Reader import storage
from Reader.render import Engine, read_image
from Reader.app import Window
from tools import leviathan_print as lp
from vayrshemon.editor_window import PageCanvas


def prove():
    folder = lp.STAGE
    native, pdf = folder / lp.NATIVE, folder / lp.PDF
    receipt = lp.sc.read(folder / 'edition-manifest.json')
    assert lp.sc.digest(native) == receipt['nativeSha256']
    assert lp.sc.digest(pdf) == receipt['pdfSha256']
    state = lp.sc.unpack(lp.sc.read(native))['state']
    lp.verify(state, lp.sc.read(lp.WORK / 'ledger.json'), receipt['chapterAndFrontMatterFolios'])
    cache = storage.build(native)['cache']
    engine = Engine(cache)
    with patch('Reader.control.Server'):
        window = Window()
    window.meta = engine.index.meta
    window.schedule = lambda: None
    window.fit_mode = None
    window.zoom = .67
    window.resize(1450, 840)
    window.show()
    QApplication.processEvents()
    numbers = {p['pageId']: i for i, p in enumerate(window.meta['headers'], 1)}
    links = {numbers[k]: v for k, v in window.meta['contentsLinks'].items()}
    assert sum(map(len, links.values())) == 51
    reader_clicks = 0
    for mode in ('one', 'two'):
        window.mode = mode
        for toc, rows in sorted(links.items()):
            for row in rows:
                window.navigate(page=toc)
                area = dict(window.canvas.geometry_pages())[toc]
                pt = (area.topLeft() + QRectF(*row['bounds']).center() * (96 / 72)) * window.zoom
                pt += window.canvas.page_origin()
                assert window.canvas.link_at(pt) == row['page']
                QTest.mouseClick(window.canvas.viewport(), Qt.MouseButton.LeftButton, pos=pt.toPoint())
                assert window.page == row['page'], (mode, toc, row)
                reader_clicks += 1
    window.meta = None
    window.close()
    print(f'Reader: {reader_clicks} contents clicks passed in both page modes.', flush=True)

    book = lp.sc.FileSession(lp.ROOT, recovery=False)
    book.log.emit = lambda *a, **kw: None
    book.remember = lambda *a: None
    book.open(native, advance_revision=False)
    workbench_clicks = 0
    for mode in ('one', 'two'):
        for toc, rows in sorted(links.items()):
            book.select_frame(book.state['pages'][toc - 1]['frames'][0]['frameId'])
            actions = []
            canvas = PageCanvas(book, lambda command, **args: actions.append((command, args)))
            canvas.page_mode = mode
            book.view['zoom'] = .65
            canvas.resize(1450, 840)
            canvas.update_page()
            pid = book.state['pages'][toc - 1]['pageId']
            area = next(rect for page, rect in canvas.display_pages() if page['pageId'] == pid)
            for row in rows:
                pt = (area.topLeft() + QRectF(*row['bounds']).center() * (96 / 72)) * canvas.zoom
                pt += QPointF(canvas.RULER - canvas.horizontalScrollBar().value(),
                              canvas.RULER - canvas.verticalScrollBar().value())
                QTest.mouseClick(canvas.viewport(), Qt.MouseButton.LeftButton, pos=pt.toPoint())
            assert actions == [('view.page', dict(page=r['page'])) for r in rows], (mode, toc, actions)
            workbench_clicks += len(actions)
            canvas.close()
    book.finish()
    print(f'Workbench: {workbench_clicks} contents clicks passed in both page modes.', flush=True)

    folios = receipt['chapterAndFrontMatterFolios']
    selected = sorted(set([1, 3, 4, 5, 7, 8, folios['Chapter 1'] + 6,
                           folios['Chapter 9'] + 6, *receipt['tableNativePages'],
                           folios['Chapter 10'] + 6, folios['Chapter 17'] + 6,
                           folios['Chapter 32'] + 6, folios['Chapter 42'] + 6,
                           folios['Chapter 44'] + 6, folios['Review and conclusion'] + 6,
                           receipt['nativePages']]))
    previews = []
    for n in selected:
        image = read_image(engine.render(n, 'white', 'two', 1)['path'])
        image.save(str(folder / f'native-{n}.png'))
        prefix = folder / f'pdf-{n}'
        subprocess.run(['pdftoppm', '-f', str(n + 1), '-l', str(n + 1), '-r', '96', '-singlefile',
                        '-png', str(pdf), str(prefix)], check=True)
        with Image.open(prefix.with_suffix('.png')) as printed, Image.open(folder / f'native-{n}.png') as saved:
            assert printed.size == saved.size, (n, printed.size, saved.size)
            boxes = [ImageOps.invert(im.convert('L')).point(lambda v: 255 if v > 80 else 0).getbbox()
                     for im in (printed, saved)]
            assert max(abs(a - b) for a, b in zip(*boxes)) <= 2, (n, boxes)
            previews.append(printed.convert('RGB').resize((306, 396), Image.Resampling.LANCZOS))
    for start in range(0, len(selected), 8):
        sheet = Image.new('RGB', (4 * 322, 2 * 424), '#dddddd')
        draw = ImageDraw.Draw(sheet)
        for i, (n, im) in enumerate(zip(selected[start:start + 8], previews[start:start + 8])):
            x, y = i % 4 * 322 + 8, i // 4 * 424 + 6
            sheet.paste(im, (x, y))
            draw.text((x, y + 399), f'Native {n} / PDF {n + 1}', fill='black')
        sheet.save(folder / f'proof-{start // 8 + 1}.png')
    engine.index.close()
    lp.sc.write(folder / 'proof-validation.json', dict(
        nativeSha256=receipt['nativeSha256'], pdfSha256=receipt['pdfSha256'],
        readerClicks=reader_clicks, workbenchClicks=workbench_clicks,
        renderedPages=selected, matchingReaderAndPDFInkBounds=True,
        visuallyReviewedPages=[]))
    print(f'Poppler and native Reader ink bounds matched on {len(selected)} proof pages.', flush=True)


if __name__ == '__main__':
    app = QApplication([])
    prove()
