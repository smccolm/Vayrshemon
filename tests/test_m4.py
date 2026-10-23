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
from fontTools.ttLib import TTFont
from fontTools.pens.ttGlyphPen import TTGlyphPen
import pypdfium2 as pdfium
if os.name!='nt': os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtCore import QCoreApplication,QEvent,QRectF,QPointF,Qt
from PySide6.QtGui import QImage,QPainterPath,QTransform
from PySide6.QtWidgets import QApplication
from tools.m0.synthetic import make_font
from tools.parallel_translation_fixture import compose,local_material
from tools.layered_translation_fixture import compose_layered
from vayrshemon.studio_session import StudioSession
from vayrshemon.studio_api import StudioAPI
from vayrshemon.typesetting_session import TypesettingSession
from vayrshemon import pages
from vayrshemon.paint import mask,DEFAULT,LEGACY_DEFAULT,ENGINE_VERSION,vector_distance,REFERENCE_PROFILE,PROFILE_HASH

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

    def test_old_recipe_stays_legacy_and_new_lighting_roundtrips(self):
        self.bind();self.book.state['paint']['recipe']=deepcopy(LEGACY_DEFAULT)
        path=self.path('old-m4.vay.json');self.call('document.save',path=path)
        self.call('document.open',path=path,discardUnsaved=True)
        self.assertEqual(self.book.state['paint']['recipe'],LEGACY_DEFAULT)
        before=self.book.capture()['pages']
        self.call('paint.configure',lightingModel='individual-glyphs-1',interiorBevel=.061,
                  recessTop='#14185a',glowRange=.49,glowSpread=.00051,highlightOpacity=.66)
        recipe=deepcopy(self.book.state['paint']['recipe'])
        self.call('history.undo');self.assertEqual(self.book.state['paint']['recipe'],LEGACY_DEFAULT)
        self.call('history.redo');self.assertEqual(self.book.state['paint']['recipe'],recipe)
        new=self.path('new-m4.vay.json');self.call('document.save',path=new)
        self.call('document.open',path=new,discardUnsaved=True)
        self.assertEqual(self.book.state['paint']['recipe'],recipe)
        self.assertEqual(self.book.capture()['pages'],before)
        self.reject('paint.configure',glowRange=0)
        self.reject('paint.configure',lightingModel='unknown')

    def test_bevel_distance_tracks_subpixel_rotated_vector_edges(self):
        path=QPainterPath();path.addRect(QRectF(-9,-40,18,80))
        transform=QTransform().rotate(23).translate(.137,.291)
        path=transform.map(path);inverse,_=transform.inverted()
        for scale in (2.,4.):
            area=path.boundingRect().adjusted(-3,-3,3,3)
            alpha=mask(path,area,scale);actual=vector_distance(path,alpha,area,scale)
            y,x=np.nonzero(alpha>.99)
            expected=[]
            for px,py in zip(x,y):
                local=inverse.map(QPointF(area.x()+(px+.5)/scale,area.y()+(py+.5)/scale))
                expected.append(min(9-abs(local.x()),40-abs(local.y()))*scale)
            self.assertLess(np.max(abs(actual[y,x]-expected)),.02)

    def test_screen_glow_works_on_white_black_and_transparent_paper(self):
        self.bind();self.call('paint.configure',shadowOpacity=0,edgeWidth=0)
        em=100;path=self.book.fonts.raw(self.fid,em).pathForGlyph(2)
        samples=[]
        for name,bg in [('white','#FFFFFFFF'),('black','#FF000000'),('transparent','#00000000')]:
            result=self.call('glyph.proof',font_id=self.fid,glyph_id=2,em=em,dpi=192,background=bg,path=self.path('screen-'+name+'.png'))
            im=Image.open(result['path']).convert('RGBA');x,y,w,h=result['bounds']
            samples.append(np.asarray(im))
        from scipy.ndimage import distance_transform_edt
        coverage=mask(path,QRectF(x,y,w,h),im.width/w)[:im.height,:im.width]
        halo=(distance_transform_edt(coverage==0)>3)&(samples[1][:,:,1]>10)
        self.assertGreater(halo.sum(),20)
        self.assertTrue((samples[0][halo]==255).all())
        self.assertGreater(samples[2][halo,3].max(),10);self.assertLess(samples[2][halo,3].max(),200)

    def test_additive_interior_has_no_bevel_on_buried_overlap_edges(self):
        path=QPainterPath();path.setFillRule(Qt.FillRule.WindingFill)
        path.addRect(QRectF(0,0,40,80));path.addRect(QRectF(20,0,40,80))
        area=QRectF(-2,-2,64,84);scale=2.
        alpha=mask(path,area,scale);actual=vector_distance(path,alpha,area,scale)
        y,x=np.nonzero(alpha>.99)
        px=area.x()+(x+.5)/scale;py=area.y()+(y+.5)/scale
        expected=np.minimum.reduce([px,60-px,py,80-py])*scale
        self.assertLess(np.max(abs(actual[y,x]-expected)),.02)

    def test_reference_gradient_variants_require_the_verified_master(self):
        path=ROOT/'Inputs/font files/Thimfora_79.ttf'
        if not path.exists(): self.skipTest('Private reference font unavailable')
        fid=self.call('fonts.load',path=str(path))['fontId'];renderer=self.book.paint_renderer
        order=self.book.fonts.resolve(fid).glyph_order
        j=renderer.reference_gradient(dict(fontId=fid),order.index('J'))
        r=renderer.reference_gradient(dict(fontId=fid),order.index('r'))
        self.assertEqual(j['stops'][0]['color'],'#0d1167')
        self.assertEqual(r['stops'][0]['color'],'#000000')
        self.assertEqual(r['stops'][1]['midpoint'],.27)
        self.assertEqual(j['profileHash'],PROFILE_HASH)
        self.assertEqual(len(REFERENCE_PROFILE['glyphs']),106)
        self.assertIsNone(renderer.reference_gradient(dict(fontId=self.fid),2))
        self.call('paint.configure',referenceGradients=False)
        self.assertIsNone(renderer.reference_gradient(dict(fontId=fid),order.index('r')))
        self.call('history.undo')
        self.assertEqual(renderer.reference_gradient(dict(fontId=fid),order.index('r')),r)


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

    def test_derived_counter_stays_open_in_proofs_and_on_paper(self):
        # A real TTF with an outer stroke, enclosed counter and detached accent.
        path=self.work/'counter.ttf';make_font(path)
        with TTFont(path) as font:
            pen=TTGlyphPen(None)
            for points in (((40,0),(560,0),(560,700),(40,700)),
                           ((180,150),(180,550),(420,550),(420,150)),
                           ((240,750),(360,750),(360,800),(240,800))):
                pen.moveTo(points[0])
                for point in points[1:]: pen.lineTo(point)
                pen.closePath()
            font['glyf']['A']=pen.glyph();font.save(path)
        fid=self.call('fonts.load',path=str(path))['fontId']
        self.call('paint.bind',fontId=fid,kind='derived',enabled=True)
        for dpi in (96,192):
            for name,color in (('transparent','#00000000'),('white','#FFFFFFFF'),('black','#FF000000')):
                result=self.call('glyph.proof',font_id=fid,glyph_id=2,em=80,dpi=dpi,background=color,path=self.path(f'counter-{dpi}-{name}.png'))
                image=Image.open(result['path']).convert('RGBA');x,y,w,h=result['bounds']
                # The counter center is (300,350) font units; Qt flips font Y.
                pixel=image.getpixel((int((24-x)*image.width/w),int((-28-y)*image.height/h)))
                self.assertEqual(pixel[3],0 if name=='transparent' else 255)
                if name!='transparent': self.assertEqual(pixel[:3],(255,255,255) if name=='white' else (0,0,0))
                self.assertEqual(result['paintEngineVersion'],ENGINE_VERSION)
        self.assertEqual(self.book.state['paint']['recipe'],DEFAULT)

    def test_single_font_mode_preserves_historical_ink_without_claiming_layers(self):
        path=ROOT/'Inputs/font files/Test/test seven.ttf'
        if not path.exists(): self.skipTest('Private historical font unavailable')
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),'1b4ca056b0b1c80575db27185ca5fe6a952dfa50bf7da925dea513d1053218ad')
        fid=self.call('fonts.load',path=str(path))['fontId']
        self.call('paint.bind',fontId=fid,kind='derived',enabled=True)
        # Isolate solid paint from the deliberately translucent surrounding glow.
        self.call('paint.configure',edgeWidth=0,glowOpacity=0,shadowOpacity=0)
        renderer=self.book.paint_renderer;binding=renderer.binding(fid)
        for char in 'r\u00e1.ly':
            for em in (41,200):
                raw=self.book.fonts.raw(fid,em);gid=raw.glyphIndexesForString(char)[0]
                original=raw.pathForGlyph(gid);rim,silhouette,interior=renderer.paths(binding,gid,em)
                self.assertEqual(rim,original);self.assertEqual(silhouette,original);self.assertTrue(interior.isEmpty())
                tile,area=renderer.tile(binding,gid,em,4)
                expected=mask(original,area,4)
                actual=np.frombuffer(tile.constBits(),np.uint8).reshape(tile.height(),tile.bytesPerLine())[:,:tile.width()*4].reshape(tile.height(),tile.width(),4)[:,:,3]
                self.assertGreater(np.count_nonzero(expected>.99),10)
                # This catches every sealed loop, including small punctuation
                # counters, without hardcoding guessed language mappings.
                self.assertLessEqual(np.max(actual[expected==0]),1)
                self.assertLessEqual(np.abs(actual.astype(float)-expected*255).max(),1)

    def test_three_layers_share_master_origin_and_glow_is_not_solid_ink(self):
        ids=[]
        # Deliberately unequal side bearings and extents. Independent centering
        # would move the interior to the wrong side of the glyph.
        shapes=[[(40,0,160,700),(400,0,560,700)],[(0,-40,600,740)],[(200,200,300,500),(250,250,320,550)]]
        for index,rects in enumerate(shapes):
            path=self.work/f'layer-{index}.ttf';make_font(path)
            with TTFont(path) as font:
                pen=TTGlyphPen(None)
                for left,bottom,right,top in rects:
                    pen.moveTo((left,bottom));pen.lineTo((right,bottom));pen.lineTo((right,top));pen.lineTo((left,top));pen.closePath()
                font['glyf']['A']=pen.glyph();font['hmtx'].metrics['A']=(600,min(r[0] for r in rects));font.save(path)
            ids.append(self.call('fonts.load',path=str(path))['fontId'])
        self.call('paint.bind',fontId=ids[0],glowFontId=ids[1],interiorFontId=ids[2],kind='layered',enabled=True)
        self.call('document.format',start=0,end=5,font_id=ids[0])
        self.call('paint.configure',glowOpacity=0,shadowOpacity=0,edgeWidth=.001)
        report=self.call('layout.inspect')
        for glyph in report['glyphs']:
            registration=glyph['paintRegistration']
            self.assertEqual(registration['placement'],'master-origin')
            self.assertEqual([l['fontId'] for l in registration['layers']],[ids[0],ids[2],ids[1]])
            self.assertEqual([l['sideBearing'] for l in registration['layers']],[40,200,0])
            self.assertTrue(all(l['origin']==glyph['origin'] for l in registration['layers']))
        boxes=[]
        for layer in ('composite','outline','interior','glow-mask'):
            result=self.call('glyph.proof',font_id=ids[0],glyph_id=2,em=100,dpi=192,background='#00000000',path=self.path(layer+'.png'),layer=layer)
            boxes.append(result['bounds']);im=Image.open(result['path']).convert('RGBA')
            x,y,w,h=result['bounds']
            def alpha(fx,fy): return im.getpixel((int((fx/10-x)*im.width/w),int((-fy/10-y)*im.height/h)))[3]
            if layer=='composite':
                self.assertEqual(alpha(350,350),0)  # 80 cannot become a solid matte.
                self.assertEqual(alpha(100,350),255)
                self.assertEqual(alpha(270,350),255)
            if layer=='interior':
                self.assertEqual(alpha(270,350),255)  # overlapping subpaths ADD.
                self.assertEqual(alpha(100,350),0)
        self.assertTrue(all(box==boxes[0] for box in boxes))

    def test_layer_binding_rejects_different_character_mapping(self):
        path=self.work/'wrong-cmap.ttf';make_font(path)
        with TTFont(path) as font:
            for table in font['cmap'].tables:
                if table.isUnicode(): table.cmap[65]='space'
            font.save(path)
        other=self.call('fonts.load',path=str(path))['fontId']
        result=self.reject('paint.bind',fontId=self.fid,glowFontId=other,interiorFontId=self.fid,kind='layered',enabled=True)
        self.assertIn('PAINT_LAYER_CMAP_MISMATCH',str(result))

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

    def test_color_review_uses_three_real_fonts_on_standard_page(self):
        if not (ROOT/'Inputs/Versions Best/Translation 1.psd').exists(): self.skipTest('Private corpus unavailable')
        self.call('document.new',discardUnsaved=True)
        pairs,_=local_material(ROOT,self.call)
        historical='\n'.join(''.join(r['text'] for r in p['original']) for p in pairs)
        ids,text,provenance=compose_layered(ROOT,self.call)
        self.assertEqual(text['original'],historical.replace('\u00be','\u2019'))
        self.assertEqual(len(provenance['changes']),historical.count('\u00be'))
        self.assertEqual(text['translation'],'\n'.join(p['translation'] for p in pairs))
        self.assertEqual(len(self.book.current_page()['frames']),2)
        self.assertEqual(self.book.state['paint']['bindings'][0]['kind'],'layered')
        report=self.call('layout.inspect')
        for glyph in report['glyphs']:
            self.assertFalse(glyph['missingGlyph'])
            if glyph['frameId']==ids['original']:
                self.assertEqual(glyph['paintBinding'],'layered')
                self.assertEqual(len(glyph['paintRegistration']['layers']),3)
                self.assertTrue(all(l['origin']==glyph['origin'] for l in glyph['paintRegistration']['layers']))
        self.call('publication.export',path=self.path('layered-standard.png'),format='png',mode='color',dpi=144,raster_policy='raster')

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
