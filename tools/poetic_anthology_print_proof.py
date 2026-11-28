"""Check the print master's rendered pages and exercise its native contents links."""
import subprocess
from unittest.mock import patch

from PIL import Image, ImageDraw, ImageOps
from PySide6.QtCore import QRectF, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from Reader import storage
from Reader.app import Window
from Reader.render import Engine, read_image
from tools import poetic_anthology_print as book


def reader_links(engine, works):
    with patch("Reader.control.Server"):
        window = Window()
    window.meta = engine.index.meta
    assert window.meta["coverFirst"]
    window.schedule = lambda: None
    window.fit_mode = None
    window.zoom = .65
    window.resize(1450,900)
    window.show()
    QApplication.processEvents()
    count = 0
    for mode in ("one","two"):
        window.mode = mode
        for number,page in enumerate(window.meta["headers"],1):
            for row in window.meta["contentsLinks"].get(page["pageId"],[]):
                window.navigate(page=number)
                frame = dict(window.canvas.geometry_pages())[number]
                point = (frame.topLeft()+QRectF(*row["bounds"]).center()*(96/72))*window.zoom
                point += window.canvas.page_origin()
                assert window.canvas.link_at(point)==row["page"]
                QTest.mouseClick(window.canvas.viewport(),Qt.MouseButton.LeftButton,pos=point.toPoint())
                assert window.page==row["page"]
                count += 1
    window.meta = None
    window.close()
    assert count==2*works
    return count


def ink(im):
    return ImageOps.invert(im.convert("L")).point(lambda n: 255 if n>75 else 0).getbbox()


def prove(additional_samples=()):
    native,pdf = book.DEST/book.NATIVE, book.DEST/book.PDF
    manifest = book.sc.read(book.DEST/book.MANIFEST)
    assert book.sc.digest(native)==manifest["nativeSha256"] and book.sc.digest(pdf)==manifest["pdfSha256"]
    stage = book.STAGE / "raster"
    stage.mkdir(exist_ok=True,parents=True)
    out = book.DEST / "Working"
    out.mkdir(exist_ok=True)
    total = manifest["physicalPages"]
    front = manifest.get("titlePages",0)+manifest["contentsPages"]
    # A single Poppler run covers every printed page, including the last.
    subprocess.run(["pdftoppm","-r","96","-gray","-png",str(pdf),str(stage/"page")],check=True)
    paths = {int(p.stem.split("-")[-1]):p for p in stage.glob("page-*.png")}
    selected = sorted({1,2,front,front+1,front+2,total//3,total//2,total-1,total,
                       *(manifest["sections"][k]["physicalPage"] for k in
                         ("psalm","hearts","resist","riotcity",*additional_samples) if k in manifest["sections"])})
    thumbnails = []
    engine = Engine(storage.build(native)["cache"])
    try:
        clicks = reader_links(engine,manifest["works"])
        for n in range(1,total+1):
            with Image.open(paths[n]) as im:
                assert im.size==(816,1056)
                region = ink(im)
                assert region and min(region[:2])>=48 and region[2]<781 and region[3]<1020,(n,region)
                if n not in selected:
                    continue
                qimage = read_image(engine.render(n,"white","two",1)["path"])
                qimage.save(str(stage/"native.png"))
                with Image.open(stage/"native.png") as native_im:
                    assert native_im.size==im.size
                    native_region=ink(native_im)
                    assert max(abs(a-b) for a,b in zip(region,native_region))<=2,(n,region,native_region)
                thumb = im.convert("RGB")
                thumb.thumbnail((278,360),Image.Resampling.LANCZOS)
                thumbnails.append((n,thumb))
                if n==front+1:
                    im.save(out/"Reading page.png")
    finally:
        engine.index.close()
    sheet = Image.new("RGB",(4*292,((len(thumbnails)+3)//4)*388),"#dededb")
    draw = ImageDraw.Draw(sheet)
    for i,(n,im) in enumerate(thumbnails):
        x,y=i%4*292+7,i//4*388+6
        sheet.paste(im,(x,y))
        draw.text((x,y+362),f"Page {n}",fill="black")
    sheet.save(stage/"overview.png")
    book.sc.write(out/"print-proof.json",dict(nativeSha256=manifest["nativeSha256"],pdfSha256=manifest["pdfSha256"],
                  physicalPagesRasterChecked=total,readerContentsClicks=clicks,matchingReaderAndPopplerPages=selected))
    print(f"{clicks} Reader clicks, {total} rasterized pages, {len(selected)} matching Reader and PDF proofs.",flush=True)


if __name__=="__main__":
    app = QApplication.instance() or QApplication([])
    prove()
