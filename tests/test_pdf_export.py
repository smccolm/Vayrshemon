"""Whole-document PDF, initial view, paint fidelity and safe background publication."""
from pathlib import Path
from contextlib import closing
from io import BytesIO
import shutil,time,unittest,uuid
from unittest.mock import patch
import numpy as np
import pypdfium2 as pdfium
from pypdf import PdfReader
from PySide6.QtCore import QCoreApplication,QEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication,QMessageBox
from tools.m0.common import load_json
from tools.m0.synthetic import make_font
from vayrshemon.file_api import FileSession,FileAPI
from vayrshemon.file_window import FileWindow
from vayrshemon import publication

ROOT=Path(__file__).resolve().parents[1]
APP=QApplication.instance() or QApplication([])


class PDFExportTests(unittest.TestCase):
    def setUp(self):
        self.root=ROOT/'.local/test-pdf-export'/uuid.uuid4().hex
        shutil.copytree(ROOT/'schemas',self.root/'schemas');shutil.copytree(ROOT/'data',self.root/'data')
        self.book=FileSession(self.root,source_fonts=False,recovery=False);self.api=FileAPI(self.book)
        # Preserve the original tiny-margin, unnumbered export fixture.
        # Numbering/export integration is exercised in test_page_numbering.
        self.call('page.numbering.configure',enabled=False)
        font=self.root/'synthetic.ttf';make_font(font)
        self.fid=self.call('fonts.load',path=str(font))['fontId']
        self.sizes=[(200.25,240.375),(220.498700,1120.057141),(240.25,280.375)]
        for i,(width,height) in enumerate(self.sizes):
            self.call('page.add' if i else 'page.configure',width=width,height=height)
            self.call('document.edit',start=0,end=0,text='A'*(i+1))
            self.call('document.format',start=0,end=i+1,font_id=self.fid,size=24)
        self.call('paint.bind',fontId=self.fid,enabled=True,kind='derived')
        self.call('publication.configure',background='#FF000000')
        self.w=FileWindow(self.book,self.api);self.w.proof_dpi.setValue(96)

    def tearDown(self):
        self.w.job_timer.stop();self.w.forge_panel.timer.stop();self.w.timer.stop();self.w.hide()
        self.book.window=None;self.book._editor=None;self.w.deleteLater();self.book.finish()
        QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);APP.processEvents()

    def call(self,method,**params):
        result=self.api.call(method,params,expected_revision=self.book.revision,idempotency_key=uuid.uuid4().hex)
        self.assertTrue(result['ok'],result);return result['result']

    def export(self,path=None):
        chosen=[]
        def choose(*args,**kwargs):
            suggestion=Path(args[2]);self.assertEqual(suggestion.parent,self.root/'Exports')
            self.assertRegex(suggestion.name,r'^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}_\d{3}\.pdf$')
            self.assertTrue(suggestion.parent.is_dir());chosen.append(path or suggestion)
            return str(chosen[-1]),'PDF (*.pdf)'
        with patch('PySide6.QtWidgets.QFileDialog.getSaveFileName',side_effect=choose):self.w.pdf_export_action.trigger()
        self.assertEqual(len(chosen),1);return Path(chosen[0])

    def wait(self):
        deadline=time.monotonic()+45
        while time.monotonic()<deadline:
            jobs=self.book.jobs.status()['jobs'];self.assertTrue(jobs,self.w.last_error)
            if jobs[-1]['status']!='running':return jobs[-1]
            QTest.qWait(40)
        self.fail('PDF worker timed out')

    def test_menu_all_pages_six_modes_labels_sizes_and_paint(self):
        self.assertIn(self.w.pdf_export_action,self.w.export_menu.actions())
        for view in ('one','two'):
            for mode,paper in (('mono','white'),('mono','black'),('color','black')):
                with self.subTest(view=view,mode=mode,paper=paper):
                    self.call('view.configure',mode=mode,monochromePaper=paper);self.w.page_controls.set_mode(view)
                    before=self.book.capture();path=self.export();job=self.wait()
                    self.assertEqual(job['status'],'completed',job);self.assertEqual(self.book.capture(),before)
                    reader=PdfReader(path);self.assertEqual(len(reader.pages),3)
                    self.assertEqual(reader.page_labels,['1','2','3'])
                    self.assertEqual(reader.page_layout,'/SinglePage' if view=='one' else '/TwoPageLeft')
                    self.assertEqual(reader.get_destination_page_number(reader.open_destination),0)
                    self.assertEqual(reader.viewer_preferences.direction,'/L2R')
                    self.assertEqual(job['result']['preflight']['pdfView'],view)
                    with closing(pdfium.PdfDocument(str(path))) as pdf:
                        for i,page in enumerate(reader.pages):
                            self.assertEqual((float(page.mediabox.width),float(page.mediabox.height)),self.sizes[i])
                            self.assertEqual(page.cropbox,page.mediabox)
                            with closing(pdf[i]) as rendered:
                                with closing(rendered.render(scale=1)) as bitmap:
                                    rgb=np.array(bitmap.to_pil().convert('RGB'))
                            if mode=='mono':
                                self.assertTrue((rgb[:,:,0]==rgb[:,:,1]).all());self.assertTrue((rgb[:,:,1]==rgb[:,:,2]).all())
                                self.assertEqual(tuple(rgb[2,2]),(255,255,255) if paper=='white' else (0,0,0))
                                self.assertGreater(int(rgb.max())-int(rgb.min()),200)
                            else:
                                self.assertTrue(np.any(rgb[:,:,0]!=rgb[:,:,2]))
                                # Lossless PDF image preserves exactly the approved renderer's pixels.
                                expected=publication.raster(self.book,self.book.state['pages'][i],mode,96)
                                from PIL import Image
                                reference=Image.open(BytesIO(publication.png_bytes(expected))).convert('RGB')
                                self.assertEqual(page.images[0].image.convert('RGB').tobytes(),reference.tobytes())

    def test_snapshot_keeps_view_and_all_pages_when_live_document_changes(self):
        self.call('view.configure',mode='mono',monochromePaper='white');self.w.page_controls.set_mode('two')
        before=self.book.capture();path=self.export();job=self.book.jobs.status()['jobs'][-1]
        self.assertEqual(load_json(Path(job['folder'])/'snapshot.vay.json')['state'],before)
        self.w.page_controls.set_mode('one');self.call('document.edit',start=0,end=0,text='A')
        job=self.wait();self.assertEqual(job['status'],'completed',job);self.assertTrue(job['stale'])
        reader=PdfReader(path);self.assertEqual(reader.page_layout,'/TwoPageLeft');self.assertEqual(len(reader.pages),3)

    def test_cancel_and_overwrite_conflict_preserve_destination(self):
        with patch('PySide6.QtWidgets.QFileDialog.getSaveFileName',return_value=('','')):self.w.pdf_export_action.trigger()
        self.assertFalse(self.book.jobs.status()['jobs'])
        path=self.export();job=self.book.jobs.status()['jobs'][-1];self.call('jobs.cancel',job_id=job['jobId'])
        self.assertFalse(path.exists())
        path=self.root/'existing.pdf';path.write_bytes(b'original')
        count=len(self.book.jobs.jobs)
        with patch('PySide6.QtWidgets.QMessageBox.question',return_value=QMessageBox.StandardButton.No):self.export(path)
        self.assertEqual(len(self.book.jobs.jobs),count)
        with patch('PySide6.QtWidgets.QMessageBox.question',return_value=QMessageBox.StandardButton.Yes):self.export(path)
        path.write_bytes(b'newer external file');job=self.wait()
        self.assertEqual(job['status'],'failed');self.assertIn('TARGET_CHANGED',job['error'])
        self.assertEqual(path.read_bytes(),b'newer external file')
        with patch('PySide6.QtWidgets.QMessageBox.question',return_value=QMessageBox.StandardButton.Yes):self.export(path)
        self.assertEqual(self.wait()['status'],'completed');self.assertEqual(len(PdfReader(path).pages),3)

    def test_progress_tracks_physical_pages_and_keeps_reading_ui_informed(self):
        before=self.book.capture();phases=[]
        path=self.root/'progress.pdf'
        from vayrshemon.studio_typesetting import StudioComposition
        from vayrshemon.jobs import pdf_progress
        original=StudioComposition.__init__;built=[]
        def construct(comp,*args,**kwargs):
            built.append(1);original(comp,*args,**kwargs)
        self.book.invalidate_composition()
        with patch.object(StudioComposition,'__init__',new=construct):
            publication.export(self.book,path,format='pdf',mode='mono',dpi=72,raster_policy='raster',pdf_view='two',progress_callback=phases.append)
        self.assertEqual(len(built),3,'Each physical page must be composed only once for monochrome PDF')
        self.assertEqual([p for p in phases if p.startswith('checking page ')],[f'checking page {i} of 3' for i in range(1,4)])
        self.assertEqual([p for p in phases if p.startswith('writing PDF page ')],[f'writing PDF page {i} of 3' for i in range(1,4)])
        self.assertIn('finishing PDF numbering and reading view',phases)
        self.assertEqual(phases[-1],'verifying output')
        percentages=[pdf_progress(phase,3,True)['percent'] for phase in phases]
        self.assertEqual(percentages,sorted(percentages));self.assertLess(max(percentages),100)
        self.assertEqual(len(PdfReader(path).pages),3);self.assertEqual(self.book.capture(),before)

        # Exercise worker-to-window progress with controls collapsed: page
        # counts must remain visible in the reading UI.
        self.w.sidebar_dock.configure(expanded=False)
        self.w.prepare_export_progress();self.w.poll_jobs()
        self.assertFalse(self.w.export_progress_bar.isHidden())
        self.assertEqual(self.w.export_progress_bar.maximum(),0)
        self.assertFalse(self.w.export_cancel.isEnabled())
        self.w._preparing_export=False
        self.export();deadline=time.monotonic()+45;saw_bar=False
        while time.monotonic()<deadline:
            self.w.poll_jobs();job=self.book.jobs.status()['jobs'][-1]
            if job['status']!='running':break
            self.assertFalse(self.w.export_progress.isHidden())
            self.assertFalse(self.w.export_progress_bar.isHidden())
            self.assertFalse(self.w.export_cancel.isHidden())
            self.assertIn('elapsed',self.w.export_progress.text())
            if self.w.export_progress_bar.maximum()==100:
                saw_bar=True;self.assertLess(self.w.export_progress_bar.value(),100)
            QTest.qWait(10)
        self.assertEqual(job['status'],'completed',job)
        self.assertTrue(saw_bar);self.assertEqual(job['progress']['percent'],100)
        self.w.poll_jobs();self.assertTrue(self.w.export_progress.isHidden())
        self.assertTrue(self.w.export_progress_bar.isHidden());self.assertTrue(self.w.export_cancel.isHidden())
        self.assertIn('completed',self.w.statusBar().currentMessage())

    def test_late_preflight_failure_does_not_publish_partially_written_pdf(self):
        from vayrshemon.studio_typesetting import StudioComposition
        original=StudioComposition.report;phases=[];last=self.book.state['pages'][-1]['pageId']
        def report(comp,page_id,*args,**kwargs):
            result=original(comp,page_id,*args,**kwargs)
            if page_id==last:result['glyphs'][0]['missingGlyph']=True
            return result
        for mode in ('mono','color'):
            phases.clear();target=self.root/f'late-failure-{mode}.pdf'
            with patch.object(StudioComposition,'report',new=report):
                with self.assertRaisesRegex(ValueError,'PUBLICATION_PREFLIGHT_FAILED'):
                    publication.export(self.book,target,format='pdf',mode=mode,dpi=72,raster_policy='raster',
                                       pdf_view='two',progress_callback=phases.append)
            self.assertIn('writing PDF page 2 of 3',phases)
            self.assertFalse(target.exists());self.assertFalse(list(self.root.glob('.vayrshemon-pdf-*')))

    def test_visible_cancel_button_keeps_existing_document_and_files(self):
        before=self.book.capture();path=self.export();self.w.poll_jobs()
        self.assertFalse(self.w.export_cancel.isHidden());self.w.export_cancel.click()
        job=self.book.jobs.status()['jobs'][-1]
        self.assertEqual(job['status'],'cancelled');self.assertFalse(path.exists())
        self.assertTrue(self.w.export_progress_bar.isHidden());self.assertEqual(self.book.capture(),before)

    def test_color_single_pass_keeps_mixed_page_raster_policy_and_pixels(self):
        from vayrshemon.studio_typesetting import StudioComposition
        from PIL import Image
        other=self.root/'undecorated.ttf';make_font(other,advance=700)
        plain=self.call('fonts.load',path=str(other))['fontId']
        original=StudioComposition.__init__
        for first_decorated in (True,False):
            for index,page in enumerate(self.book.state['pages']):
                self.call('frame.select',frame_id=page['frames'][0]['frameId'])
                decorated=index==(0 if first_decorated else 1)
                self.call('document.format',start=0,end=index+1,font_id=self.fid if decorated else plain)
            before=self.book.capture();built=[];phases=[]
            def construct(comp,*args,**kwargs):
                built.append(1);original(comp,*args,**kwargs)
            self.book.invalidate_composition();target=self.root/f'mixed-{first_decorated}.pdf'
            with patch.object(StudioComposition,'__init__',new=construct):
                result=publication.export(self.book,target,format='pdf',mode='color',dpi=96,
                    raster_policy='raster',pdf_view='two',progress_callback=phases.append)
            self.assertTrue(result['preflight']['rasterFallback'])
            if first_decorated:
                self.assertEqual(len(built),3)
                self.assertIn('checking and writing PDF pages',phases)
            else:self.assertNotIn('checking and writing PDF pages',phases)
            reader=PdfReader(target)
            for index,page in enumerate(self.book.state['pages']):
                expected=publication.raster(self.book,page,'color',96)
                reference=Image.open(BytesIO(publication.png_bytes(expected))).convert('RGB')
                self.assertEqual(reader.pages[index].images[0].image.convert('RGB').tobytes(),reference.tobytes())
            self.assertEqual(self.book.capture(),before)

    def test_metadata_preserves_compressed_artwork_and_exact_rendering(self):
        from pypdf import Transformation
        from pypdf.generic import EncodedStreamObject
        from vayrshemon.pdf_view import with_view
        raw=self.root/'raw.pdf'
        publication.write_pdf_pages(self.book,raw,self.book.state['pages'],'mono',96,False,expand_bounds=True)
        # The large-book failure was caused by decoding/parsing every glyph's
        # drawing operations during a simple page-origin adjustment.
        with patch.object(EncodedStreamObject,'get_data',side_effect=AssertionError('Artwork must stay compressed')):
            fast=with_view(raw,'two',self.sizes)
        def legacy(writer,page,offset):page.add_transformation(Transformation().translate(0,offset))
        with patch('vayrshemon.pdf_view._translate_contents',side_effect=legacy):
            reference=with_view(raw,'two',self.sizes)
        original=PdfReader(raw);updated=PdfReader(BytesIO(fast))
        for old,new in zip(original.pages,updated.pages):
            self.assertEqual(old['/Contents']._data,new['/Contents'][1].get_object()._data)
        with closing(pdfium.PdfDocument(fast)) as actual,closing(pdfium.PdfDocument(reference)) as expected:
            for i in range(3):
                with closing(actual[i]) as a,closing(expected[i]) as b:
                    with closing(a.render(scale=2)) as ap,closing(b.render(scale=2)) as bp:
                        self.assertEqual(ap.to_pil().tobytes(),bp.to_pil().tobytes())

    def test_metadata_failure_publishes_nothing_and_non_pdf_option_is_rejected(self):
        path=self.root/'failed.pdf';before=self.book.capture()
        with patch('vayrshemon.pdf_view.with_view',side_effect=ValueError('injected metadata failure')):
            with self.assertRaisesRegex(ValueError,'injected metadata failure'):
                publication.export(self.book,path,format='pdf',mode='mono',dpi=72,raster_policy='raster',pdf_view='two')
        self.assertFalse(path.exists());self.assertFalse(list(self.root.glob('.vayrshemon-pdf-*')))
        self.assertEqual(self.book.capture(),before)
        result=self.api.call('jobs.export',dict(path=str(self.root/'invalid.png'),format='png',mode='mono',dpi=72,raster_policy='raster',pdf_view='two'),
            expected_revision=self.book.revision,idempotency_key=uuid.uuid4().hex)
        self.assertFalse(result['ok']);self.assertFalse(self.book.jobs.jobs)
