"""Black/white reading and proof output without changing the color document."""
from pathlib import Path
import shutil,unittest,uuid
import numpy as np
import pypdfium2 as pdfium
from PySide6.QtCore import QCoreApplication,QEvent,Qt
from PySide6.QtGui import QImage,QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication
from tools.m0.synthetic import make_font
from vayrshemon.studio_session import StudioSession
from vayrshemon.studio_api import StudioAPI
from vayrshemon.typesetting_session import TypesettingSession
from vayrshemon.typesetting_api import TypesettingAPI
from vayrshemon import pages,layout

ROOT=Path(__file__).resolve().parents[1]
APP=QApplication.instance() or QApplication([])


def pixels(image):
    image=image.convertToFormat(QImage.Format.Format_RGBA8888)
    return np.frombuffer(image.constBits(),np.uint8).reshape(image.height(),image.width(),4).copy()


class MonochromeTests(unittest.TestCase):
    def setUp(self):
        self.work=ROOT/'.local/test-monochrome'/uuid.uuid4().hex;self.work.mkdir(parents=True)
        shutil.copytree(ROOT/'schemas',self.work/'schemas')
        for name in ('data/fonts.json','data/orthography/thimfora-79.json'):
            path=self.work/name;path.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,path)
        self.book=StudioSession(self.work,source_fonts=False,recovery=False);self.api=StudioAPI(self.book)
        font=self.work/'synthetic.ttf';make_font(font);fid=self.call('fonts.load',path=str(font))['fontId']
        for index in range(4):
            if index==0:self.call('page.configure',width=200,height=240)
            elif index==2:self.call('page.add',width=200,height=240)
            else:self.call('frame.add',x=110,y=20,width=80,height=200)
            self.call('frame.configure',x=10 if index%2==0 else 110,y=20,width=80,height=200)
            self.call('document.edit',start=0,end=0,text='AA\nA')
            self.call('document.format',start=0,end=4,font_id=fid,size=24,color=('#123456FF','#FFFFFFFF','#EE1155FF','#1133FF80')[index])
        self.call('paint.bind',fontId=fid,kind='derived',enabled=True)

    def tearDown(self):
        self.book.finish()
        for frame in self.book.frames.values():frame.deleteLater()
        self.book.deleteLater();QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)

    def call(self,method,**params):
        result=self.api.call(method,params,expected_revision=self.book.revision,idempotency_key=uuid.uuid4().hex)
        self.assertTrue(result['ok'],result);return result['result']

    def assert_neutral(self,image,paper):
        data=pixels(image)
        self.assertTrue((data[:,:,0]==data[:,:,1]).all(),'red/green tint')
        self.assertTrue((data[:,:,1]==data[:,:,2]).all(),'green/blue tint')
        self.assertEqual(tuple(data[2,2]),(paper,paper,paper,255))
        # Every independent column must contain visible opposite ink.
        for start,end in ((10,90),(110,190)):
            crop=data[30:200,int(start*image.width()/200):int(end*image.width()/200),0]
            self.assertGreater(np.count_nonzero(crop!=paper),20)

    def test_colored_and_transparent_paper_get_contrasting_opaque_ink(self):
        for background,paper in (('#FF000000',0),('#FFFFFFFF',255),('#FF123456',0),('#FFFFFFAA',255),('#00000000',255)):
            with self.subTest(background=background):
                self.call('publication.configure',background=background);before=self.book.capture()
                for page in self.book.state['pages']:
                    image,_=pages.render(self.book,page_id=page['pageId'],mode='mono',dpi=96)
                    self.assert_neutral(image,paper)
                self.assertEqual(self.book.capture(),before)

    def test_png_svg_pdf_share_monochrome_across_both_pages(self):
        # Explicit paper overrides the opposite source background in every format.
        for background,paper in (('#FFFFFFAA',0),('#FF123456',255)):
            self.call('publication.configure',background=background)
            self.call('view.configure',mode='mono',monochromePaper='black' if paper==0 else 'white')
            for index,page in enumerate(self.book.state['pages']):
                preview,_=pages.render(self.book,page_id=page['pageId'],mode='mono',dpi=96)
                for kind in ('png','svg'):
                    path=self.work/f'{paper}-{index}.{kind}'
                    self.call('publication.export',path=str(path),format=kind,mode='mono',dpi=96,raster_policy='reject',page_id=page['pageId'])
                    if kind=='png':
                        image=QImage(str(path));self.assertTrue(np.array_equal(pixels(preview),pixels(image)))
                    else:
                        self.assertNotIn('<image',path.read_text());image=QImage(preview.size(),QImage.Format.Format_ARGB32_Premultiplied);image.fill(Qt.GlobalColor.transparent)
                        painter=QPainter(image)
                        try:QSvgRenderer(str(path)).render(painter)
                        finally:painter.end()
                    self.assert_neutral(image,paper)
            path=self.work/f'{paper}.pdf'
            self.call('publication.export',path=str(path),format='pdf',mode='mono',dpi=96,raster_policy='reject')
            pdf=pdfium.PdfDocument(str(path))
            try:
                self.assertEqual(len(pdf),2)
                for page in pdf:
                    bitmap=page.render(scale=96/72)
                    try:
                        data=np.array(bitmap.to_pil().convert('RGBA'));image=QImage(data.data,data.shape[1],data.shape[0],data.strides[0],QImage.Format.Format_RGBA8888).copy()
                        self.assert_neutral(image,paper)
                    finally:bitmap.close();page.close()
            finally:pdf.close()

    def test_return_to_color_preserves_pixels_geometry_and_document(self):
        self.call('publication.configure',background='#FF000000');before=self.book.capture()
        colored=[pixels(pages.render(self.book,page_id=p['pageId'],mode='color')[0]) for p in self.book.state['pages']]
        for page in self.book.state['pages']:
            color=self.book.composition('color',page_id=page['pageId']);mono=self.book.composition('mono',page_id=page['pageId'])
            self.assertEqual([g['origin'] for g in color.final],[g['origin'] for g in mono.final])
            pages.render(self.book,page_id=page['pageId'],mode='mono')
        for page,expected in zip(self.book.state['pages'],colored):
            self.assertTrue(np.array_equal(expected,pixels(pages.render(self.book,page_id=page['pageId'],mode='color')[0])))
        self.assertEqual(self.book.capture(),before)

    def test_paper_choice_roundtrips_with_undo_without_changing_formatting(self):
        self.call('publication.configure',background='#FF000000');before=self.book.capture()
        self.call('view.configure',mode='mono',monochromePaper='white')
        white=self.book.capture();self.assertEqual(white['pages'],before['pages']);self.assertEqual(white['paint'],before['paint'])
        self.call('view.configure',monochromePaper='black');self.call('history.undo')
        self.assertEqual(self.book.view['monochromePaper'],'white')
        self.call('history.redo');self.assertEqual(self.book.view['monochromePaper'],'black')
        self.call('view.configure',monochromePaper='white')
        path=self.work/'white-paper.vay.json';self.call('document.save',path=str(path));self.call('document.open',path=str(path))
        self.assertEqual(self.book.view['monochromePaper'],'white');self.assertEqual(self.book.capture()['pages'],before['pages'])
        for page in self.book.state['pages']:self.assert_neutral(pages.render(self.book,page_id=page['pageId'],mode='mono')[0],255)
        state=self.book.capture();result=self.api.call('view.configure',dict(monochromePaper='pink'),expected_revision=self.book.revision,idempotency_key=uuid.uuid4().hex)
        self.assertFalse(result['ok']);self.assertEqual(self.book.capture(),state)

    def test_legacy_native_and_outline_paths_also_use_black_ink(self):
        book=TypesettingSession(self.work,source_fonts=False,recovery=False);api=TypesettingAPI(book)
        try:
            for method,params in [('document.edit',dict(start=0,end=0,text='Visible ink')),('document.format',dict(start=0,end=11,color='#0000FFFF',size=30))]:
                result=api.call(method,params,expected_revision=book.revision,idempotency_key=uuid.uuid4().hex);self.assertTrue(result['ok'],result)
            for image in (layout.render(book.active,mode='mono')[0],pages.render(book,mode='mono')[0]):
                data=pixels(image);self.assertTrue((data[:,:,0]==data[:,:,2]).all());self.assertLess(data[:,:,:3].min(),20)
            path=self.work/'legacy.svg';pages.export_svg(book,path,mode='mono')
            image=QImage(816,1056,QImage.Format.Format_ARGB32_Premultiplied);image.fill(Qt.GlobalColor.transparent);painter=QPainter(image)
            try:QSvgRenderer(str(path)).render(painter)
            finally:painter.end()
            data=pixels(image);self.assertTrue((data[:,:,0]==data[:,:,2]).all());self.assertLess(data[:,:,:3].min(),20)
            result=api.call('view.configure',dict(monochromePaper='black'),expected_revision=book.revision,idempotency_key=uuid.uuid4().hex);self.assertTrue(result['ok'],result)
            for image in (layout.render(book.active,mode='mono')[0],pages.render(book,mode='mono')[0]):
                data=pixels(image);self.assertEqual(tuple(data[2,2]),(0,0,0,255));self.assertGreater(data[:,:,0].max(),200)
        finally:book.finish()


if __name__=='__main__':unittest.main()
