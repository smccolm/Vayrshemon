"""M3 derived geometry, Unicode, persistence and desktop regression gates."""
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
import uuid
import xml.etree.ElementTree as ET
from unittest.mock import patch
if os.name!='nt': os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtCore import QCoreApplication,QEvent,Qt
from PySide6.QtGui import QImage,QTextCursor
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from tools.m0.common import load_json
from tools.m0.synthetic import make_font
from vayrshemon.typesetting_session import TypesettingSession
from vayrshemon.typesetting_api import TypesettingAPI,METHODS
from vayrshemon.typesetting_contracts import profile
from vayrshemon.typesetting import break_opportunities,boundaries
from vayrshemon.session import utf16_length,SCALE
from vayrshemon import pages

ROOT=Path(__file__).resolve().parents[1]
APP=QApplication.instance() or QApplication([])


class TypesettingTests(unittest.TestCase):
    def setUp(self):
        self.work=ROOT/'.local/test-m3'/uuid.uuid4().hex; self.work.mkdir(parents=True)
        for name in ('data/fonts.json','data/orthography/thimfora-79.json'):
            target=self.work/name; target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(ROOT/name,target)
        shutil.copytree(ROOT/'schemas',self.work/'schemas')
        self.book=TypesettingSession(self.work,source_fonts=False,recovery=True); self.api=TypesettingAPI(self.book); self.window=None

    def tearDown(self):
        self.book.finish()
        if self.window: self.window.timer.stop(); self.window.hide(); self.window.deleteLater()
        for frame in self.book.frames.values(): frame.deleteLater()
        self.book.deleteLater(); QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)
        if APP.platformName()=='offscreen': APP.clipboard().clear()
        APP.processEvents()

    def call(self,method,**params):
        result=self.api.call(method,params,expected_revision=self.book.revision,idempotency_key=uuid.uuid4().hex,document_id=self.book.state['documentId'],origin='mcp')
        self.assertTrue(result['ok'],result); return result['result']

    def reject(self,method,code,**params):
        before=self.book.capture(); rev=self.book.revision
        result=self.api.call(method,params,expected_revision=rev,idempotency_key=uuid.uuid4().hex,origin='mcp',document_id=self.book.state['documentId'])
        self.assertFalse(result['ok'],result); self.assertIn(code,result['error']['message']); self.assertEqual(before,self.book.capture()); self.assertEqual(rev,self.book.revision)

    def write(self,text): self.call('document.edit',start=0,end=utf16_length(self.book.text()),text=text)
    def enable(self): self.call('typesetting.configure',enabled=True)
    def report(self): return self.call('layout.inspect')
    def content(self): return [deepcopy(f['content']) for p in self.book.capture()['pages'] for f in p['frames']]

    def dense(self):
        self.write('AAAA\nAAAA'); self.call('document.format',start=0,end=9,size=40)
        self.call('paragraph.format',start=0,end=9,lineHeight=dict(mode='exact',value=10)); self.enable()

    def test_repair_clearance_source_unchanged_deterministic_undo(self):
        self.dense(); self.call('document.format',start=0,end=9,tracking=3); before=self.report(); content=self.content()
        self.assertGreater(before['collisionReport']['beforeCount'],0)
        self.call('collision.configure',mode='repair',clearance=2,maximumExpansion=100)
        after=self.report(); self.assertEqual(after['collisionReport']['afterCount'],0); self.assertTrue(after['collisionReport']['complete'])
        self.assertTrue(after['baselineDifferences']); self.assertEqual(content,self.content())
        self.book.invalidate_composition(); self.assertEqual(after['geometryHash'],self.report()['geometryHash'])
        self.call('history.undo'); self.assertEqual(before['geometryHash'],self.report()['geometryHash'])
        self.call('history.redo'); self.assertEqual(after['geometryHash'],self.report()['geometryHash'])

    def test_fixed_frame_and_expansion_fail_with_stable_reasons(self):
        self.dense(); self.call('frame.configure',height=40)
        self.call('collision.configure',mode='repair',maximumExpansion=100)
        report=self.report()['collisionReport']; self.assertGreater(report['afterCount'],0); self.assertIn('FIXED_FRAME_CONSTRAINT',report['unresolvedReasons'])
        self.call('collision.configure',fixedFrame=False,maximumExpansion=0)
        self.assertIn('EXPANSION_LIMIT',self.report()['collisionReport']['unresolvedReasons'])
        self.call('collision.configure',fixedFrame=False,maximumExpansion=100)
        self.assertEqual(self.report()['collisionReport']['afterCount'],0)
        self.assertTrue(self.report()['frames'][0]['overflow']); self.assertEqual(self.book.text(),'AAAA\nAAAA')

    def test_leading_distribution_grid_and_paragraph_spacing(self):
        self.write('A\nA'); self.call('document.format',start=0,end=3,size=16)
        self.call('paragraph.format',start=0,end=3,lineHeight=dict(mode='exact',value=40),before=3,after=7); self.enable()
        after=self.report()['lines']; self.call('typesetting.configure',leadingDistribution='before'); before=self.report()['lines']
        self.call('typesetting.configure',leadingDistribution='split'); split=self.report()['lines']
        self.assertGreater(before[0]['baseline'],after[0]['baseline'])
        self.assertAlmostEqual(split[0]['baseline'],(before[0]['baseline']+after[0]['baseline'])/2,places=4)
        self.assertAlmostEqual((after[1]['baseline']-after[0]['baseline'])/SCALE,50,places=4)
        self.call('typesetting.configure',grid=dict(enabled=True,step=13.125,offset=2.5))
        for line in self.report()['lines']:
            v=(line['baseline']/SCALE-2.5)/13.125; self.assertAlmostEqual(v,round(v),places=5)

    def flow(self,text='A\nB\nC\nD',height=35):
        self.write(text); self.call('document.format',start=0,end=utf16_length(text),size=12)
        self.call('paragraph.format',start=0,end=utf16_length(text),lineHeight=dict(mode='exact',value=18))
        self.call('frame.configure',width=180,height=height); source=self.book.state['activeFrameId']; page=self.book.current_page()['pageId']
        self.call('page.add'); self.call('frame.configure',width=180,height=150); target=self.book.state['activeFrameId']
        self.call('frame.select',frame_id=source); self.call('flow.set',source_frame_id=source,targets=[target]); return source,target,page

    def test_flow_has_one_source_and_maps_continuation_click(self):
        source,target,page=self.flow(); text=self.book.text()
        report=pages.inspect(self.book,page_id=self.book.locate(target)[0]['pageId'])
        self.assertTrue(report['glyphs']); self.assertTrue(all(g['sourceFrameId']==source for g in report['glyphs']))
        self.assertEqual(self.book.frames[target].text(),''); self.assertEqual(self.book.frames[source].text(),text)
        line=report['lines'][0]; hit=pages.hit_test(self.book,page_id=report['pageId'],x=line['x']+1,y=line['baseline'])
        self.assertEqual(hit['frameId'],source); self.assertEqual(hit['targetFrameId'],target); self.assertGreaterEqual(hit['offset'],line['sourceUtf16'][0])
        self.call('frame.select',frame_id=target); self.reject('document.edit','FLOW_TARGET_READ_ONLY',start=0,end=0,text='unsafe')
        self.reject('frame.configure','M3_FLOW_REQUIRES_EQUAL_WIDTHS',width=181)
        self.reject('flow.set','FLOW_CYCLE_OR_SHARED_FRAME',source_frame_id=target,targets=[source])
        self.call('page.delete',page_id=self.book.current_page()['pageId']); self.assertEqual(self.book.state['typesetting']['flows'],[])
        self.call('history.undo'); self.assertEqual(self.book.state['typesetting']['flows'][0]['targets'],[target])

    def test_nonempty_flow_rejected_and_paragraph_keeps(self):
        source,target,_=self.flow('Heading\nFollowing',height=22)
        self.call('paragraph.rules',start=0,end=7,keepWithNext=True)
        comp=self.book.composition(); self.assertTrue(all(l['frameId']==target for l in comp.lines))
        self.call('flow.set',source_frame_id=source,targets=[])
        self.call('frame.select',frame_id=target); self.write('Owned content')
        self.reject('flow.set','FLOW_TARGET_HAS_TEXT',source_frame_id=source,targets=[target])

    def test_widow_orphan_distribution_and_overflow(self):
        source,target,_=self.flow('A\u2028B\u2028C\u2028D',height=55)
        self.call('paragraph.rules',start=0,end=7,widows=2,orphans=2)
        lines=self.book.composition().lines
        self.assertEqual([l['frameId'] for l in lines],[source,source,target,target])
        self.call('frame.configure',frame_id=target,height=12)
        self.assertTrue(pages.inspect(self.book,page_id=self.book.locate(target)[0]['pageId'])['frames'][0]['overflow'])
        self.assertEqual(self.book.text(),'A\u2028B\u2028C\u2028D')

    def test_unicode_breaks_never_split_graphemes_or_nonbreaking_controls(self):
        for value in ['A\u0301B','👩\u200d💻Z','A\u00a0B','A\u202fB','A\u2060B']:
            p=profile(); p['wrap']='grapheme'
            allowed,_=break_opportunities(value,{'language.en':p},lambda _: 'language.en')
            self.assertTrue(set(allowed)<=set(boundaries(value)))
            if '\u00a0' in value or '\u202f' in value or '\u2060' in value: self.assertEqual(allowed,[0,utf16_length(value)])
        self.write('A\u0301 emoji 😀 漢字 one\u00a0two x\u00ady\u200bz\u2028end'); self.call('frame.configure',width=75)
        self.enable(); report=self.report(); valid=set(boundaries(self.book.text()))
        self.assertTrue(self.call('breaks.inspect')['blocks'])
        self.assertTrue(all(l['sourceUtf16'][1] in valid for l in report['lines']))
        self.assertEqual(report['lines'][-1]['sourceUtf16'][1],utf16_length(self.book.text()))
        self.assertTrue(any(l['breakInfo']['reason']=='explicit-line-separator' for l in report['lines']))

    def test_tailoring_versions_manual_controls_and_rejected_split(self):
        self.write('ab/cd'); self.enable(); p=profile(); p.update(revision=2,breakAfter='/')
        self.call('breaks.profile',**p); self.reject('breaks.profile','PROFILE_REVISION_MUST_INCREASE',**p)
        self.assertTrue(any(o['offset']==3 and o['profileRevision']==2 for o in self.call('breaks.inspect')['blocks'][0]['opportunities']))
        self.call('breaks.insert',offset=2,kind='soft-hyphen'); self.assertEqual(self.book.text(),'ab\u00ad/cd')
        self.write('A\u0301B'); self.reject('breaks.insert','GRAPHEME',offset=1,kind='zero-width-space')

    def test_optical_pair_separate_from_kerning_and_probe_isolated(self):
        self.write('AV AV'); self.call('document.format',start=0,end=5,size=36); self.enable()
        before=self.content(); state=self.book.capture(); probe=self.call('pairs.inspect',text='AV',size=36,delta=2)
        self.assertEqual(state,self.book.capture()); self.assertGreater(probe['opticalDelta'],0)
        width=self.report()['lines'][0]['width']
        self.call('optical.set',rules=[dict(left='A',right='V',fontId=None,delta=2,independentLegacy=False)])
        report=self.report(); self.assertGreater(report['lines'][0]['width'],width); self.assertTrue(all(e['applied'] for e in report['opticalAdjustments']))
        self.assertEqual(before,self.content()); self.assertTrue(self.book.features['kern'])
        self.write('A\u0301V'); self.call('optical.set',rules=[dict(left='A\u0301',right='V',fontId=None,delta=2,independentLegacy=False)])
        self.assertFalse(self.report()['opticalAdjustments'][0]['applied'])

    def test_legacy_optical_requires_explicit_independence_and_no_auto_horizontal(self):
        font_path=self.work/'fixture.ttf'; make_font(font_path); fid=self.call('fonts.load',path=str(font_path))['fontId']
        self.write('AA'); self.call('document.format',start=0,end=2,font_id=fid,language='language.vayrshemon',size=40,tracking=-12); self.enable()
        rule=dict(left='A',right='A',fontId=fid,delta=2,independentLegacy=False)
        self.call('optical.set',rules=[rule]); self.assertFalse(self.report()['opticalAdjustments'][0]['applied'])
        rule['independentLegacy']=True; self.call('optical.set',rules=[rule]); self.assertTrue(self.report()['opticalAdjustments'][0]['applied'])
        self.write('AA'); self.call('document.format',start=0,end=2,font_id=None,language='language.en',size=40,tracking=-15)
        self.call('collision.configure',mode='repair'); self.assertIn('HORIZONTAL_REQUIRES_EXPLICIT_OPTICAL_RULE',self.report()['collisionReport']['unresolvedReasons'])

    def test_reserved_bounds_and_allow_policy(self):
        self.dense(); self.call('collision.configure',bounds='effect',strokeWidth=2,effectPadding=3,mode='allow')
        report=self.report(); g=report['glyphs'][0]
        self.assertAlmostEqual(g['effectBounds'][2]-g['inkBounds'][2],8*SCALE,places=4)
        self.assertTrue(all(c['severity']=='info' for c in report['collisionReport']['collisions']))
        self.assertFalse(report['collisionReport']['boundsMeaning']['reservedEffectsArePainted'])

    def test_m3_save_reopen_geometry_and_cli(self):
        self.flow(); self.call('typesetting.configure',grid=dict(enabled=True,step=20,offset=1.5))
        state=self.book.capture(); hashes=[pages.inspect(self.book,page_id=p['pageId'])['geometryHash'] for p in state['pages']]
        path=self.work/'m3.vay.json'; self.call('document.save',path=str(path)); self.assertEqual(load_json(path)['formatVersion'],'0.3.0')
        self.write('Changed'); self.call('document.open',path=str(path),discardUnsaved=True)
        current=self.book.capture(); current['revision']=state['revision']; self.assertEqual(current,state)
        self.assertEqual(hashes,[pages.inspect(self.book,page_id=p['pageId'])['geometryHash'] for p in state['pages']])
        child=subprocess.run([sys.executable,'-m','vayrshemon','--root',str(self.work),'inspect','--no-source-fonts','--document',str(path)],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',timeout=30)
        self.assertEqual(child.returncode,0,child.stderr); self.assertEqual(json.loads(child.stdout)['geometryHash'],hashes[0])

    def test_m2_migration_preserves_original_and_requires_new_save_path(self):
        from vayrshemon.authoring import AuthoringSession
        old=AuthoringSession(self.work,source_fonts=False,recovery=False); old.active.edit(0,0,'Original M2')
        path=self.work/'m2.vay.json'; old.save(path); original=path.read_bytes(); old.deleteLater()
        self.call('document.open',path=str(path)); self.assertEqual(self.book.text(),'Original M2')
        self.reject('document.save','MIGRATION_REQUIRES_NEW_PATH',path=str(path)); self.assertEqual(path.read_bytes(),original)
        self.call('document.save',path=str(self.work/'upgraded.vay.json'))

    def test_png_and_outline_svg_use_derived_layout(self):
        self.dense(); self.call('collision.configure',mode='repair',maximumExpansion=100)
        before=self.report()['geometryHash']; png=self.work/'proof.png'; svg=self.work/'proof.svg'
        result=self.call('render.png',path=str(png)); self.call('render.svg',path=str(svg))
        self.assertFalse(QImage(str(png)).isNull()); self.assertTrue(ET.parse(svg).findall('.//{http://www.w3.org/2000/svg}path'))
        self.assertEqual(before,self.report()['geometryHash']); self.assertEqual(result['width'],816)

    def test_desktop_commands_source_ids_and_continuation_readonly(self):
        from vayrshemon.workbench_window import WorkbenchWindow
        self.write('First\nSecond'); self.call('paragraph.rules',start=6,end=12,keepWithNext=True)
        rule=deepcopy(self.book.state['typesetting']['frames'][self.book.state['activeFrameId']]['paragraphs'][0])
        self.window=WorkbenchWindow(self.book,self.api); self.window.show(); APP.processEvents()
        c=self.window.editor.textCursor(); c.setPosition(0); self.window.editor.setTextCursor(c)
        QTest.keyClick(self.window.editor,Qt.Key.Key_Return); APP.processEvents()
        blocks=self.book.capture()['pages'][0]['frames'][0]['content']['document']['stories'][0]['blocks']
        self.assertEqual(len({b['blockId'] for b in blocks}),3); self.assertEqual(blocks[-1]['blockId'],rule['blockId'])
        self.call('history.undo'); self.assertEqual(self.book.text(),'First\nSecond')
        self.call('typesetting.configure',enabled=True); self.window.refresh(); self.assertTrue(self.window.typeset_enabled.isChecked())
        source,target,_=self.flow(); self.call('frame.select',frame_id=target); self.assertTrue(self.window.editor.isReadOnly())
        self.window.refresh(); self.assertIn('M3 / 0.4.0',self.window.windowTitle()); self.assertIsNone(self.window.last_error)

    def test_generated_contracts_match_runtime(self):
        from tools.generate_m3_contracts import generate
        generate(self.work)
        for name in ('schemas/typesetting-command.schema.json','schemas/typesetting-document.schema.json','data/typesetting-mcp-tools.json','data/typesetting-capabilities.json'):
            self.assertEqual(load_json(self.work/name),load_json(ROOT/name))
        self.assertEqual(len(METHODS),57)

    def test_empty_paragraphs_bidi_ligatures_and_marks_preserve_native_shaping(self):
        from vayrshemon import layout
        self.enable(); self.assertEqual(self.report()['glyphs'],[])
        self.write('fi A\u0301 العربية\n\nend')
        native=layout.inspect(self.book.active); derived=self.report()
        self.assertEqual(sorted((g['glyphId'],tuple(g['sourceUtf16'])) for g in native['glyphs']),sorted((g['glyphId'],tuple(g['sourceUtf16'])) for g in derived['glyphs']))
        self.assertEqual(len(derived['lines']),3)
        self.call('collision.configure',mode='repair',clearance=10,maximumExpansion=20)
        report=self.report(); self.assertTrue(any(g['protected'] for g in report['glyphs']))
        self.assertTrue(all(not c['protected'] or c['reason']=='PROTECTED_JOIN_OR_MARK' for c in report['collisionReport']['collisions']))

    def test_analysis_budget_is_explicit_and_blocks_automatic_repair(self):
        self.dense(); self.call('collision.configure',mode='repair')
        with patch('vayrshemon.typesetting.MAX_COMPARISONS',0):
            self.book.invalidate_composition(); report=self.report()
        self.assertFalse(report['collisionReport']['complete']); self.assertIn('ANALYSIS_LIMIT',report['collisionReport']['unresolvedReasons'])
        self.assertEqual(report['baselineDifferences'],[])

    def test_imported_format_boundary_inside_grapheme_is_retained(self):
        self.write('A\u0301'); native=self.book.active; model=native.snapshot()
        first=model['stories'][0]['blocks'][0]['runs'][0]; first['text']='A'
        second=deepcopy(first); second.update(runId='run.mark',text='\u0301',styleId='style.mark')
        style=deepcopy(model['styles'][0]); style.update(styleId='style.mark',color='#FF0000FF')
        model['styles'].append(style); model['stories'][0]['blocks'][0]['runs'].append(second)
        with self.book.command('Import colored combining mark'): native.load_model(model)
        before=self.content(); self.enable(); report=self.report()
        colors={color for g in self.book.composition().final for _,_,color in g['_paints']}
        self.assertIn('#ffff0000',colors); self.assertEqual(before,self.content())
        self.assertTrue(all(g['sourceUtf16']==[0,2] for g in report['glyphs']))

    def test_unbreakable_overflow_and_explicit_emergency_wrap(self):
        self.write('abcdefghijklmnopqrstuv'); self.call('frame.configure',width=30); self.enable()
        self.assertEqual(len(self.report()['lines']),1); self.assertTrue(self.report()['frames'][0]['overflow'])
        p=profile(); p.update(revision=2,emergency=True); self.call('breaks.profile',**p)
        self.assertGreater(len(self.report()['lines']),1); self.assertEqual(self.book.text(),'abcdefghijklmnopqrstuv')
        for text in ('A\u00a0B','A\u202fB','A\u2060B','A\u0301😀'):
            self.write(text); self.call('frame.configure',width=1)
            lines=self.report()['lines']; valid=set(boundaries(text))
            self.assertTrue(all(l['sourceUtf16'][1] in valid for l in lines))
            if text!='A\u0301😀': self.assertEqual(len(lines),1)

    def test_typesetting_recovery_after_forced_exit(self):
        script="""import os,sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from tools.m0.common import write_json
from vayrshemon.typesetting_session import TypesettingSession
from vayrshemon.typesetting_api import TypesettingAPI
from vayrshemon import pages
app=QApplication([]); s=TypesettingSession(Path(sys.argv[1]),source_fonts=False); a=TypesettingAPI(s)
for method,params in [('document.edit',dict(start=0,end=0,text='Recovered Á 😀')),('typesetting.configure',dict(enabled=True,grid=dict(enabled=True,step=17,offset=2)))]:
    r=a.call(method,params,expected_revision=s.revision,origin='desktop'); assert r['ok'],r
write_json(sys.argv[2],dict(path=str(s.recovery_path),hash=pages.inspect(s)['geometryHash'],report=pages.inspect(s)))
os._exit(73)
"""
        locator=self.work/'crashed.json'; child=subprocess.run([sys.executable,'-c',script,str(self.work),str(locator)],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',timeout=30)
        self.assertEqual(child.returncode,73,child.stderr); expected=load_json(locator)
        self.call('recovery.restore',path=expected['path'],discardUnsaved=True)
        from tools.m0.common import write_json
        write_json(self.work/'recovered-report.json',self.report())
        self.assertEqual(self.book.text(),'Recovered Á 😀'); self.assertEqual(self.report()['geometryHash'],expected['hash'])


if __name__=='__main__': unittest.main()
