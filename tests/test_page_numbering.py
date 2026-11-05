"""Unta folios: exact values, protected layout, document history and exports."""
from copy import deepcopy
from io import BytesIO
from pathlib import Path
import shutil,time,unittest,uuid
import numpy as np
from PIL import Image
from pypdf import PdfReader
from PySide6.QtCore import QRectF,QCoreApplication,QEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from tools.m0.common import load_json
from tools.m0.synthetic import make_font
from vayrshemon.file_api import FileSession,FileAPI
from vayrshemon.file_window import FileWindow
from vayrshemon.numbering_window import NumberingDialog
from vayrshemon import page_numbering as numbers,pages,publication,saved_preview

ROOT=Path(__file__).resolve().parents[1]
APP=QApplication.instance() or QApplication([])


def pixels(image):
    return np.array(Image.open(BytesIO(publication.png_bytes(image))).convert('RGBA'))


class NumberingTests(unittest.TestCase):
    def setUp(self):
        self.root=ROOT/'.local/test-numbering'/uuid.uuid4().hex
        shutil.copytree(ROOT/'data',self.root/'data');shutil.copytree(ROOT/'schemas',self.root/'schemas')
        self.book=FileSession(self.root,source_fonts=False,recovery=False);self.api=FileAPI(self.book)
        font=self.root/'synthetic.ttf';make_font(font);fid=self.call('fonts.load',path=str(font))['fontId']
        for i in range(3):
            self.call('page.add' if i else 'page.configure',width=300,height=400)
            self.call('page.configure',margins={k:60 for k in ('left','right','top','bottom')})
            self.call('frame.configure',x=60,y=60,width=180,height=280)
            self.call('document.edit',start=0,end=0,text='A A\nAA')
            self.call('document.format',start=0,end=6,font_id=fid,size=24)
        self.call('publication.configure',background='#FF000000')
        self.w=None

    def tearDown(self):
        if self.w:
            self.w.job_timer.stop();self.w.forge_panel.timer.stop();self.w.timer.stop();self.w.hide()
            self.book.window=None;self.book._editor=None;self.w.deleteLater()
        self.book.finish();QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);APP.processEvents()

    def call(self,method,**params):
        result=self.api.call(method,params,expected_revision=self.book.revision,idempotency_key=uuid.uuid4().hex)
        self.assertTrue(result['ok'],result);return result['result']

    def test_base12_transitions_and_legacy_slots(self):
        expected={0:'0',1:'1',9:'9',10:'À',11:'Á',12:'10',13:'11',143:'ÁÁ',144:'100',674:'482',1728:'1000',2048:'1228'}
        for decimal,text in expected.items():self.assertEqual(numbers.digits(decimal),text)
        for bad in (-1,1.5,True):
            with self.assertRaises(ValueError):numbers.digits(bad)

    def test_defaults_undo_redo_save_reopen_and_no_body_changes(self):
        before=self.book.capture();config=self.call('page.numbering.read')
        self.assertTrue(config['enabled']);self.assertEqual(config['minimumPages'],2)
        self.assertEqual((config['sizePt'],config['edgeInsetPt']),(50,28))
        self.call('page.numbering.configure',enabled=True,left=dict(vertical='top'),right=dict(visible=False))
        after=self.book.capture();self.assertEqual(after['pages'],before['pages']);self.assertEqual(after['paint'],before['paint'])
        self.assertEqual(after['typesetting'],before['typesetting'])
        self.call('history.undo');self.assertEqual(self.book.state['pageNumbering'],before['pageNumbering'])
        self.call('history.redo');self.assertEqual(numbers.settings(self.book),after['pageNumbering'])
        history=len(self.book._undo);self.call('page.numbering.configure',enabled=True);self.assertEqual(len(self.book._undo),history)
        path=self.root/'numbered.vay';self.book.save(path,preview_mode='two')
        settings=numbers.settings(self.book);self.book.open(path,advance_revision=False)
        self.assertEqual(numbers.settings(self.book),settings);self.assertEqual(self.book.saved_page_mode,'two')
        self.assertEqual(self.book.capture()['pages'],before['pages'])
        self.assertTrue(set(numbers.FONT_IDS)<={s['fontId'] for s in self.book.capture()['fontSources']})

    def test_automatic_numbering_tracks_document_count_and_preserves_opt_out(self):
        self.book.new(width=300,height=400)
        self.assertFalse(self.book.dirty)
        self.call('page.configure',margins={k:60 for k in ('left','right','top','bottom')})
        self.call('frame.configure',x=60,y=60,width=180,height=280)
        first=self.book.current_page()['pageId']
        for mode in ('one','two'):
            self.assertEqual(self.call('page.numbering.inspect',all_pages=True,page_mode=mode)['pages'][0]['status'],'hidden')
        before=self.book.capture()
        second=self.call('page.add',width=300,height=400)['pageId']
        self.assertEqual(self.call('page.numbering.inspect',page_id=first)['pages'][0]['status'],'placed')
        self.call('history.undo')
        self.assertEqual(self.book.capture()['pages'],before['pages'])
        self.assertEqual(self.call('page.numbering.inspect')['pages'][0]['status'],'hidden')
        self.call('history.redo')
        self.call('page.configure',margins={k:60 for k in ('left','right','top','bottom')})
        self.call('frame.configure',x=60,y=60,width=180,height=280)
        for mode in ('one','two'):
            report=self.call('page.numbering.inspect',all_pages=True,page_mode=mode)
            self.assertEqual([p['status'] for p in report['pages']],['placed','placed'])
            for p in report['pages']:
                self.assertEqual(p['sizePt'],50)
                self.assertFalse(p['adjusted'])
                self.assertAlmostEqual(QRectF(*p['bounds']).bottom(),(400-28)*numbers.SCALE)
        self.call('page.delete',page_id=second)
        self.assertEqual(self.call('page.numbering.inspect')['pages'][0]['status'],'hidden')
        self.call('history.undo')
        self.assertTrue(numbers.enabled_for(self.book.state))
        self.call('page.numbering.configure',enabled=False,sizePt=44,edgeInsetPt=19)
        self.call('page.add',width=300,height=400)
        self.assertFalse(numbers.enabled_for(self.book.state))
        path=self.root/'opted-out.vay';self.book.save(path);config=numbers.settings(self.book)
        self.book.open(path,advance_revision=False)
        self.assertEqual(numbers.settings(self.book),config)
        self.assertEqual((config['sizePt'],config['edgeInsetPt']),(44,19))

    def test_positions_visibility_modes_and_incomplete_final_pair(self):
        self.call('page.numbering.configure',enabled=True)
        for vertical in ('top','bottom'):
            for horizontal in ('left','right'):
                self.call('page.numbering.configure',single=dict(vertical=vertical,horizontal=horizontal))
                report=self.call('page.numbering.inspect',all_pages=True,page_mode='one')
                for page,item in zip(self.book.state['pages'],report['pages']):
                    self.assertEqual(item['status'],'placed');rect=QRectF(*item['bounds'])
                    self.assertTrue(pages.page_rect(page).contains(rect))
                    self.assertLess(rect.bottom(),80) if vertical=='top' else self.assertGreater(rect.top(),450)
                    self.assertLess(rect.left(),100) if horizontal=='left' else self.assertGreater(rect.left(),250)
                    self.assertTrue(all(not rect.intersects(pages.rect(f).adjusted(-numbers.CLEARANCE,-numbers.CLEARANCE,numbers.CLEARANCE,numbers.CLEARANCE)) for f in page['frames']))
        self.call('page.numbering.configure',right=dict(visible=False))
        report=self.call('page.numbering.inspect',all_pages=True,page_mode='two')
        self.assertEqual([p['role'] for p in report['pages']],['left','right','left'])
        self.assertEqual([p['status'] for p in report['pages']],['placed','hidden','placed'])
        self.assertEqual([p['pageNumber'] for p in report['pages']],[1,2,3])

    def test_margin_move_or_block_instead_of_overlap_and_export_failure(self):
        self.call('page.numbering.configure',enabled=True)
        page=self.book.current_page();base=numbers.placement(self.book,page,'mono');self.assertEqual(base['status'],'placed')
        # A real text region occupies the preferred bottom corner. Find another
        # vertical position in that same margin, without moving either frame.
        box=QRectF(*base['bounds'])
        self.call('frame.add',x=box.x()/numbers.SCALE,y=box.y()/numbers.SCALE,width=box.width()/numbers.SCALE,height=2)
        page=self.book.current_page()
        shifted=numbers.placement(self.book,page,'mono');self.assertEqual(shifted['status'],'placed');self.assertTrue(shifted['adjusted'])
        self.call('frame.configure',x=0,y=340,width=300,height=60)
        page=self.book.current_page()
        blocked=numbers.placement(self.book,page,'mono');self.assertEqual(blocked['status'],'blocked')
        before=self.book.capture();image=publication.raster(self.book,page,'mono',96)
        self.assertIsNotNone(image);self.assertEqual(self.book.capture(),before)
        check=publication.preflight(self.book,mode='mono',dpi=96)
        self.assertFalse(check['ok']);self.assertIn('PAGE_NUMBER_NO_SPACE',[i['code'] for i in check['issues']])
        target=self.root/'blocked.pdf'
        with self.assertRaisesRegex(ValueError,'PAGE_NUMBER_NO_SPACE'):publication.export(self.book,target,mode='mono',dpi=96,pdf_view='one')
        self.assertFalse(target.exists());self.assertFalse(list(self.root.glob('.vayrshemon-pdf-*')))
        # Switching the position is one undoable correction, with body intact.
        self.call('page.numbering.configure',single=dict(vertical='top'))
        self.assertEqual(numbers.placement(self.book,page,'mono')['status'],'placed')
        self.assertEqual(self.book.capture()['pages'],before['pages'])

    def test_overset_effects_and_edits_invalidate_safety(self):
        self.call('page.numbering.configure',enabled=True)
        page=self.book.current_page();comp=self.book.composition('color',page_id=page['pageId'])
        item=numbers.placement(self.book,page,'color',comp);self.assertEqual(item['status'],'placed')
        # Overset is outside the frame: reserve its actual effect box as well.
        comp._page_numbering={}
        glyph=dict(comp.final[0]);glyph['effectBounds']=[0,450,400,84];glyph['_clip']=None;comp.final.append(glyph)
        self.assertEqual(numbers.placement(self.book,page,'color',comp)['status'],'blocked')
        self.call('document.edit',start=0,end=0,text='A')
        self.assertEqual(numbers.placement(self.book,page,'color')['status'],'placed')

    def test_color_mono_exports_saved_preview_and_body_pixels(self):
        page=self.book.state['pages'][0]
        self.call('page.numbering.configure',enabled=True)
        for mode,paper in (('color','black'),('mono','black'),('mono','white')):
            self.call('view.configure',mode=mode,monochromePaper=paper)
            for view in ('one','two'):
                with self.subTest(mode=mode,paper=paper,view=view):
                    expected=publication.raster(self.book,page,mode,96,page_mode=view);with_number=pixels(expected)
                    self.call('page.numbering.configure',enabled=False)
                    without_number=pixels(publication.raster(self.book,page,mode,96,page_mode=view))
                    self.call('page.numbering.configure',enabled=True)
                    np.testing.assert_array_equal(with_number[80:453,80:320],without_number[80:453,80:320])
                    self.assertTrue(np.any(with_number!=without_number))
                    if mode=='mono':np.testing.assert_array_equal(with_number[:,:,0],with_number[:,:,2])
                    stem=self.root/f'{mode}-{paper}-{view}'
                    png=publication.export(self.book,str(stem)+'.png',format='png',mode=mode,dpi=96,raster_policy='raster',page_id=page['pageId'],page_mode=view)
                    self.assertEqual(Path(png['path']).read_bytes(),publication.png_bytes(expected))
                    svg=publication.export(self.book,str(stem)+'.svg',format='svg',mode=mode,dpi=96,raster_policy='raster',page_id=page['pageId'],page_mode=view)
                    from PySide6.QtSvg import QSvgRenderer
                    from PySide6.QtGui import QImage,QPainter
                    rendered=QImage(expected.size(),QImage.Format.Format_ARGB32_Premultiplied);rendered.fill(0)
                    painter=QPainter(rendered);QSvgRenderer(svg['path']).render(painter);painter.end()
                    # Independent SVG engine must show ink at the numeral's actual location.
                    with numbers.scope(self.book,view):box=QRectF(*numbers.placement(self.book,page,mode)['bounds']).toAlignedRect()
                    region=pixels(rendered)[box.top():box.bottom(),box.left():box.right()]
                    self.assertGreater(np.ptp(region[:,:,:3].astype(int)),10)
                    pdf=publication.export(self.book,str(stem)+'.pdf',mode=mode,dpi=96,raster_policy='raster',pdf_view=view)
                    reader=PdfReader(pdf['path']);self.assertEqual(reader.page_labels,['1','2','3'])
                    self.assertEqual(reader.page_layout,'/SinglePage' if view=='one' else '/TwoPageLeft')
                    if mode=='color':self.assertEqual(reader.pages[0].images[0].image.convert('RGB').tobytes(),Image.open(BytesIO(publication.png_bytes(expected))).convert('RGB').tobytes())
        state=self.book.capture();self.book.save(self.root/'preview.vay',preview_mode='two')
        saved=load_json(self.root/'preview.vay')['shellPreview'];self.assertEqual(saved['pageMode'],'two')
        self.assertEqual(saved_preview.create(self.book,state,'two')['pngSha256'],saved['pngSha256'])

    def test_menu_dialog_apply_and_frozen_worker_mode(self):
        self.w=FileWindow(self.book,self.api);self.w.page_controls.set_mode('two',persist=False)
        dialog=NumberingDialog(self.w);dialog.enabled.setChecked(True)
        self.assertTrue(dialog.multiple_only.isChecked())
        self.assertEqual(dialog.font_size.value(),50);self.assertEqual(dialog.inset.value(),28)
        dialog.rows['left'][1].setCurrentIndex(0);dialog.rows['right'][0].setChecked(False)
        self.assertTrue(dialog.apply_settings());dialog.deleteLater()
        self.assertEqual(numbers.settings(self.book)['left']['vertical'],'top')
        self.assertFalse(numbers.settings(self.book)['right']['visible'])
        self.call('view.configure',mode='mono',monochromePaper='white')
        target=self.root/'worker.pdf'
        job=self.call('jobs.export',path=str(target),format='pdf',mode='mono',dpi=96,raster_policy='raster',pdf_view='two')
        self.w.page_controls.set_mode('one',persist=False);self.call('page.numbering.configure',enabled=False)
        end=time.monotonic()+40
        while time.monotonic()<end:
            job=self.book.jobs.status(job['jobId'])
            if job['status']!='running':break
            QTest.qWait(40)
        self.assertEqual(job['status'],'completed',job)
        reports=job['result']['preflight']['pages']
        self.assertEqual([p['pageNumbering']['status'] for p in reports],['placed','hidden','placed'])
        self.assertEqual([p['pageNumbering']['role'] for p in reports],['left','right','left'])
        self.assertTrue(job['stale'])


if __name__=='__main__':unittest.main()
