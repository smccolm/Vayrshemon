"""M4 persistence, real paint extents, deliberate fallback and independent proofs."""
from copy import deepcopy
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time
import unittest
import uuid
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image,ImageFont,ImageDraw
import pypdfium2 as pdfium
if os.name!='nt': os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtCore import QCoreApplication,QEvent
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication
from tools.m0.synthetic import make_font
from tools.parallel_translation_fixture import compose,local_material
from vayrshemon.studio_session import StudioSession
from vayrshemon.studio_api import StudioAPI
from vayrshemon.typesetting_session import TypesettingSession
from vayrshemon import pages

ROOT=Path(__file__).resolve().parents[1]
APP=QApplication.instance() or QApplication([])


class StudioTests(unittest.TestCase):
    def setUp(self):
        self.work=ROOT/'.local/test-m4'/uuid.uuid4().hex;self.work.mkdir(parents=True)
        shutil.copytree(ROOT/'schemas',self.work/'schemas')
        for name in ('data/fonts.json','data/orthography/thimfora-79.json'):
            path=self.work/name;path.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,path)
        self.book=StudioSession(self.work,source_fonts=False,recovery=False);self.api=StudioAPI(self.book)
        font_path=self.work/'synthetic.ttf';make_font(font_path)
        self.fid=self.call('fonts.load',path=str(font_path))['fontId']
        self.call('document.edit',start=0,end=0,text='AAA\nA')
        self.call('document.format',start=0,end=5,font_id=self.fid,size=40)

    def tearDown(self):
        self.book.finish()
        for frame in self.book.frames.values(): frame.deleteLater()
        self.book.deleteLater();QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);APP.processEvents()

    def call(self,method,**params):
        value=self.api.call(method,params,expected_revision=self.book.revision,document_id=self.book.state['documentId'],idempotency_key=uuid.uuid4().hex,origin='mcp')
        self.assertTrue(value['ok'],value);return value['result']

    def bind(self): self.call('paint.bind',fontId=self.fid,enabled=True,kind='derived')
    def path(self,name): return str(self.work/name)

    def reject(self,method,**params):
        before=self.book.capture()
        result=self.api.call(method,params,expected_revision=self.book.revision,document_id=self.book.state['documentId'],idempotency_key=uuid.uuid4().hex,origin='mcp')
        self.assertFalse(result['ok']);self.assertEqual(before,self.book.capture());return result

    def test_recipe_persistence_undo_migration_and_source_preservation(self):
        source=self.book.capture()['pages'][0]['frames'][0]['content'];self.bind()
        self.call('paint.configure',glowRadius=.024,rim='#128acb')
        self.assertEqual(self.book.state['paint']['recipe']['revision'],2)
        self.call('history.undo');self.assertEqual(self.book.state['paint']['recipe']['revision'],1)
        self.call('history.redo');self.assertEqual(self.book.capture()['pages'][0]['frames'][0]['content'],source)
        before=self.book.capture();path=self.path('native.vay.json');self.call('document.save',path=path)
        self.call('document.open',path=path,discardUnsaved=True)
        after=self.book.capture();before.pop('revision');after.pop('revision');self.assertEqual(before,after)
        payload=json.loads(Path(path).read_text());payload['formatVersion']='0.3.0';payload['state'].pop('paint')
        old=self.work/'old.vay.json';old.write_text(json.dumps(payload))
        self.call('document.open',path=str(old),discardUnsaved=True)
        self.assertEqual(self.book.state['paint']['bindings'],[]);self.assertIsNone(self.book.saved_path)
        self.assertEqual(self.book.capture()['pages'][0]['frames'][0]['content'],source)

    def test_effect_bounds_background_dpi_and_limits(self):
        self.bind();report=self.call('layout.inspect');glyph=report['glyphs'][0]
        self.assertGreater(glyph['effectBounds'][2],glyph['inkBounds'][2])
        self.call('publication.configure',background='#00000000')
        for dpi in (96,192):
            image,info=pages.render(self.book,dpi=dpi)
            self.assertEqual(image.pixelColor(0,0).alpha(),0)
            self.assertEqual(info['width'],round(612*dpi/72))
        path=self.path('glyph.png');self.call('glyph.proof',font_id=self.fid,glyph_id=2,em=80,dpi=96,background='#00000000',path=path)
        alpha=np.asarray(Image.open(path).convert('RGBA'))[:,:,3]
        self.assertTrue(((alpha>0)&(alpha<200)).any())
        self.assertLess(alpha[[0,-1],:].max(),3);self.assertLess(alpha[:,[0,-1]].max(),3)
        self.reject('paint.configure',glowRadius=1)
        self.reject('paint.bind',fontId=self.fid,kind='layered',enabled=True)

    def test_collision_uses_real_paint_before_solver(self):
        self.bind();self.call('typesetting.configure',enabled=True)
        self.call('paragraph.format',start=0,end=5,lineHeight=dict(mode='exact',value=35))
        self.call('collision.configure',bounds='effect',mode='warn')
        small=self.call('collision.inspect')
        self.call('paint.configure',glowRadius=.08)
        large=self.call('collision.inspect');self.assertGreaterEqual(large['afterCount'],small['afterCount'])
        self.assertTrue(any(c['direction']=='vertical' for c in large['collisions']))
        self.call('collision.configure',mode='repair',maximumExpansion=100,fixedFrame=False)
        fixed=self.call('collision.inspect');self.assertTrue(fixed['solver'])
        self.assertEqual(self.book.text(),'AAA\nA')

    def test_preflight_reports_changed_font_without_rendering_it(self):
        self.bind();path=self.work/'synthetic.ttf';path.write_bytes(path.read_bytes()+b'changed')
        report=self.call('publication.preflight',format='pdf',mode='color',dpi=300,raster_policy='raster')
        self.assertFalse(report['ok']);self.assertIn('MISSING_OR_CHANGED_FONT',[i['code'] for i in report['issues']])
        self.assertIsNone(report['pages'][0]['geometryHash'])

    def test_export_rejection_atomicity_svg_pdf_and_physical_size(self):
        self.bind()
        self.reject('publication.export',path=self.path('refused.pdf'),format='pdf',mode='color',dpi=144,raster_policy='reject')
        self.assertFalse((self.work/'refused.pdf').exists())
        page=self.book.current_page()['pageId']
        for kind in ('png','svg','pdf'):
            result=self.call('publication.export',path=self.path('proof.'+kind),format=kind,mode='color',dpi=144,raster_policy='raster')
            self.assertFalse(result['preflight']['searchable'])
        svg=ET.parse(self.work/'proof.svg').getroot();self.assertEqual(svg.attrib['width'],'612.0pt')
        self.assertEqual(len(svg.findall('{http://www.w3.org/2000/svg}image')),1)
        with closing(pdfium.PdfDocument(self.path('proof.pdf'))) as pdf:
            self.assertEqual(len(pdf),1);self.assertEqual(pdf[0].get_size(),(612,792))
            self.assertEqual(pdf[0].get_textpage().get_text_range(),'')
            actual=np.asarray(pdf[0].render(scale=2).to_pil().convert('RGB')).astype(float)
        expected=np.asarray(Image.open(self.work/'proof.png').convert('RGB')).astype(float)
        self.assertEqual(actual.shape,expected.shape);self.assertLess(np.abs(actual-expected).mean(),1.0)
        second=self.call('page.add',width=420,height=900)
        self.call('publication.export',path=self.path('multi.pdf'),format='pdf',mode='color',dpi=96,raster_policy='raster')
        with closing(pdfium.PdfDocument(self.path('multi.pdf'))) as pdf:
            self.assertEqual(len(pdf),2);self.assertEqual(pdf[1].get_size(),(420,900))
        self.reject('publication.export',path=self.path('multi.png'),format='png',mode='color',dpi=96,raster_policy='raster')
        self.call('publication.export',path=self.path('one.png'),format='png',mode='color',dpi=96,raster_policy='raster',page_id=page)

    def load_layers(self):
        files=['Thimfora_79.ttf','Thimfora_80_Infill.ttf','Thimfora_81_Fragments.ttf']
        if not (ROOT/'Inputs/font files'/files[0]).exists(): self.skipTest('Private layer fonts unavailable')
        ids=[self.call('fonts.load',path=str(ROOT/'Inputs/font files'/name))['fontId'] for name in files]
        self.call('paint.bind',fontId=ids[0],glowFontId=ids[1],interiorFontId=ids[2],kind='layered',enabled=True)
        return ids[0]

    def test_reproducible_color_font_and_independent_freetype(self):
        fid=self.fid
        self.call('paint.bind',fontId=fid,glowFontId=fid,interiorFontId=fid,kind='layered',enabled=True)
        self.check_color_font(fid,'AA')

    def test_archived_color_font_and_independent_freetype(self):
        self.check_color_font(self.load_layers(),'Jj0.')

    def check_color_font(self,fid,text):
        for name in ('a.ttf','b.ttf'): self.call('font.build',font_id=fid,path=self.path(name),treatment='flat-colr-v0')
        self.assertEqual((self.work/'a.ttf').read_bytes(),(self.work/'b.ttf').read_bytes())
        # Pillow uses FreeType, independently of Qt and the source renderer.
        font=ImageFont.truetype(self.path('a.ttf'),300)
        im=Image.new('RGBA',(600,400),'white');d=ImageDraw.Draw(im);d.text((20,20),text,font=font,embedded_color=True)
        im.save(self.path('independent-colr.png'));a=np.asarray(im).astype(int)
        self.assertGreater(np.count_nonzero(a[:,:,2]>a[:,:,0]+40),100)
        manifest=json.loads((self.work/'a.ttf.build.json').read_text())
        self.assertIn('bevel lighting',manifest['unsupportedEffects']);self.assertTrue(manifest['validation']['baseMetrics'])

    def test_standard_real_page_keeps_attested_source(self):
        if not (ROOT/'Inputs/Versions Best/Polished Examples.docx').exists(): self.skipTest('Private corpus unavailable')
        self.call('document.new',discardUnsaved=True)
        pairs,fonts=local_material(ROOT,self.call);ids,text=compose(ROOT,self.call,pairs,fonts)
        before={fid:n.text() for fid,n in self.book.frames.items()}
        self.call('paint.bind',fontId=fonts['test seven'],kind='derived',enabled=True)
        self.call('collision.configure',frame_id=ids['original'],bounds='effect',mode='warn')
        self.assertEqual(before,{fid:n.text() for fid,n in self.book.frames.items()})
        self.assertEqual(len(self.book.current_page()['frames']),2)
        self.assertEqual(self.book.state['typesetting']['flows'],[])
        check=self.call('publication.preflight',format='pdf',mode='color',dpi=144,raster_policy='raster')
        self.assertTrue(check['ok']);self.assertFalse(any(i['code']=='MISSING_GLYPHS' for i in check['issues']))
        self.call('publication.export',path=self.path('standard.png'),format='png',mode='color',dpi=144,raster_policy='raster')
        self.call('document.save',path=self.path('standard.vay.json'))
        self.assertEqual(before[ids['original']][186],'\u00be')

    def test_studio_window_constructs_and_uses_api(self):
        from vayrshemon.studio_window import StudioWindow
        window=StudioWindow(self.book,self.api)
        try:
            self.assertIn('M4',window.windowTitle());self.assertIn('glowRadius',window.paint_controls)
            self.bind();window.refresh();APP.processEvents()
            result=self.call('ui.workspace',source=False,diagnostics=False,guides=False,panel='Paint')
            self.assertEqual(result,dict(source=False,diagnostics=False,guides=False,panel='Paint'))
        finally: window.timer.stop();window.hide();window.deleteLater()

    def test_m4_local_cli_transport(self):
        from PySide6.QtCore import QProcess
        from PySide6.QtTest import QTest
        from vayrshemon.api import LocalServer
        server=LocalServer(self.api,publish=False)
        try:
            process=QProcess();process.setWorkingDirectory(str(ROOT))
            process.start(sys.executable,['-m','vayrshemon','call','paint.read','--descriptor',str(server.descriptor)])
            deadline=time.monotonic()+15
            while process.state()!=QProcess.ProcessState.NotRunning and time.monotonic()<deadline:
                APP.processEvents();QTest.qWait(10)
            if process.state()!=QProcess.ProcessState.NotRunning: process.kill();self.fail('M4 transport timed out')
            output=json.loads(bytes(process.readAllStandardOutput()))
            self.assertTrue(output['ok'],output);self.assertEqual(output['apiVersion'],'0.5.0')
            self.assertEqual(output['result'],self.book.state['paint'])
        finally: server.close()


if __name__=='__main__': unittest.main()
