"""M2 authoring, persistence, interruption and independent export acceptance tests."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch
import uuid
import xml.etree.ElementTree as ET

if os.name!='nt': os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtCore import Qt,QCoreApplication,QEvent,QMimeData
from PySide6.QtGui import QTextCursor,QInputMethodEvent,QImage,QPainter,QColor
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from tools.m0.common import load_json,write_json
from tools.m0.synthetic import make_font
from vayrshemon.authoring import AuthoringSession,digest,MIME
from vayrshemon.editor_api import EditorAPI
from vayrshemon.editor_window import EditorWindow
from vayrshemon.session import Session,utf16_length
from vayrshemon import pages

ROOT=Path(__file__).resolve().parents[1]
APP=QApplication.instance() or QApplication([])


class AuthoringTests(unittest.TestCase):
    def setUp(self):
        self.work=ROOT/'.local/test-m2'/uuid.uuid4().hex
        self.work.mkdir(parents=True)
        for name in ('data/fonts.json','data/orthography/thimfora-79.json'):
            target=self.work/name; target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(ROOT/name,target)
        shutil.copytree(ROOT/'schemas',self.work/'schemas')
        self.book=AuthoringSession(self.work,source_fonts=False,recovery=True)
        self.api=EditorAPI(self.book)
        self.window=None

    def tearDown(self):
        self.book.finish()
        if self.window:
            self.window.timer.stop(); self.window.hide(); self.window.deleteLater()
        for frame in self.book.frames.values(): frame.deleteLater()
        self.book.deleteLater()
        QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)
        if APP.platformName()=='offscreen': APP.clipboard().clear()
        APP.processEvents()

    def call(self,method,**params):
        result=self.api.call(method,params,expected_revision=self.book.revision,idempotency_key=uuid.uuid4().hex,
                             document_id=self.book.state['documentId'],origin='mcp')
        self.assertTrue(result['ok'],result)
        return result['result']

    def show(self):
        self.window=EditorWindow(self.book,self.api); self.window.show(); APP.processEvents(); return self.window

    def write(self,text): self.call('document.edit',start=0,end=utf16_length(self.book.text()),text=text)

    def font(self,name='source.ttf'):
        path=self.work/name; make_font(path); return self.call('fonts.load',path=str(path))['fontId'],path

    def test_pages_frames_complete_history_and_stale_frame_guard(self):
        self.write('First page')
        first=self.book.state['activeFrameId']
        self.call('page.add',width=420.123,height=600.456)
        second=self.book.state['activeFrameId']
        self.write('Second page')
        self.call('frame.add',x=40,y=60,width=150,height=80,name='Caption')
        self.write('Caption')
        deleted=self.book.state['activeFrameId']
        self.call('frame.delete',frame_id=deleted)
        self.call('history.undo')
        self.assertEqual(self.book.frames[deleted].text(),'Caption')
        old=self.book.revision
        self.call('frame.select',frame_id=first)
        stale=self.api.call('document.edit',dict(start=0,end=0,text='wrong'),expected_revision=old,idempotency_key='stale',origin='mcp',document_id=self.book.state['documentId'])
        self.assertEqual(stale['error']['code'],'STALE_REVISION')
        self.assertEqual(self.book.text(),'First page')
        self.assertEqual(self.book.frames[second].text(),'Second page')

    def test_fractional_pages_asymmetric_margins_and_frame_rollback(self):
        self.call('page.configure',width=180.123,height=241.456,unit='mm',margins=dict(top=8,right=12,bottom=16,left=20))
        page=self.book.current_page(); frame=page['frames'][0]
        self.assertNotEqual(page['margins']['left'],page['margins']['right'])
        self.assertEqual(int(frame['width']),int(page['width'])-int(page['margins']['left'])-int(page['margins']['right']))
        before=self.book.capture(); rev=self.book.revision
        bad=self.api.call('frame.configure',dict(x=999999),expected_revision=rev,idempotency_key='bad-frame')
        self.assertFalse(bad['ok']); self.assertEqual(self.book.capture(),before); self.assertEqual(self.book.revision,rev)
        self.call('history.undo')
        self.assertEqual(self.book.current_page()['width'],'612000000')

    def test_native_file_roundtrip_spacing_tabs_baseline_and_history(self):
        self.write('A\u0301\u00a0Á 😀\nSecond\tcolumn')
        end=utf16_length(self.book.text())
        self.call('document.format',start=0,end=end,size=27,tracking=1.25,wordSpacing=2,baseline=12)
        self.call('paragraph.format',start=0,end=end,alignment='center',before=6,after=8,tabs=[42,100],lineHeight=dict(mode='at-least',value=38))
        self.call('page.add',width=480,height=300); self.write('Different page')
        state=self.book.capture(); hashes=[pages.inspect(self.book,page_id=p['pageId'])['geometryHash'] for p in state['pages']]
        path=self.work/'roundtrip.vay.json'; self.call('document.save',path=str(path))
        self.write('unsaved edit'); self.call('document.open',path=str(path),discardUnsaved=True)
        restored=self.book.capture(); restored['revision']=state['revision']
        self.assertEqual(restored,state)
        self.assertEqual([pages.inspect(self.book,page_id=p['pageId'])['geometryHash'] for p in restored['pages']],hashes)
        self.assertFalse(self.book.dirty)
        self.assertTrue(self.book.history)

    def test_save_as_external_change_backup_and_recent_paths(self):
        self.write('v1'); one=self.work/'one.vay.json'; two=self.work/'two.vay.json'
        self.call('document.save',path=str(one)); original=one.read_bytes()
        self.write('v2'); self.call('document.save-as',path=str(two)); self.assertEqual(one.read_bytes(),original)
        self.write('v3'); self.call('document.save',path=str(two))
        backups=list((self.work/'.local/history'/self.book.state['documentId']).glob('*.vay.json')); self.assertEqual(len(backups),1)
        two.write_text('{}',encoding='utf-8')
        error=self.api.call('document.save',dict(path=str(two)),expected_revision=self.book.revision,idempotency_key='outside-edit')
        self.assertEqual(error['error']['code'],'DOCUMENT_CHANGED_ON_DISK')
        self.assertEqual(self.book.recent()[0]['path'],str(two))

    def test_m1_migration_preserves_source_and_page_geometry(self):
        lab=Session(self.work,source_fonts=False)
        model=lab.snapshot(); model['stories'][0]['blocks']=model['stories'][0]['blocks'][:1]; model['stories'][0]['blocks'][0]['runs'][0]['text']='M1 content'
        lab.load_model(model)
        original=self.work/'legacy.vaylab.json'; lab.save(original); original_bytes=original.read_bytes()
        from vayrshemon import layout
        prior=layout.inspect(lab)['glyphs']
        self.call('document.open',path=str(original),discardUnsaved=True)
        self.assertEqual(self.book.text(),'M1 content')
        current=pages.inspect(self.book)['glyphs']
        self.assertEqual([g['origin'] for g in prior],[g['origin'] for g in current])
        blocked=self.api.call('document.save',dict(path=str(original)),expected_revision=self.book.revision,idempotency_key='migration-overwrite')
        self.assertFalse(blocked['ok'])
        target=self.work/'migrated.vay.json'; self.call('document.save-as',path=str(target))
        self.assertEqual(original.read_bytes(),original_bytes)
        self.assertEqual(load_json(target)['formatVersion'],'0.2.0')
        lab.deleteLater()

    def test_font_relocation_requires_exact_bytes(self):
        fid,path=self.font(); self.write('AAA'); self.call('document.format',start=0,end=3,font_id=fid,language='language.vayrshemon',size=32)
        file=self.work/'fonts.vay.json'; self.call('document.save',path=str(file))
        moved=self.work/'relocated.ttf'; path.rename(moved)
        report=self.call('document.preflight',path=str(file)); self.assertEqual(report['missingFonts'][0]['fontId'],fid)
        before=self.book.capture()
        bad=self.api.call('document.open',dict(path=str(file),discardUnsaved=True),expected_revision=self.book.revision,idempotency_key='missing')
        self.assertFalse(bad['ok']); self.assertEqual(self.book.capture(),before)
        self.call('document.open',path=str(file),fontPaths={fid:str(moved)},discardUnsaved=True)
        self.assertEqual(self.book.fonts.resolve(fid).path,moved)
        self.call('document.save',path=str(file))

    def test_semantic_clipboard_keeps_legacy_unicode_and_spacing(self):
        fid,path=self.font(); self.write('A EN A')
        self.call('document.format',start=0,end=1,font_id=fid,language='language.vayrshemon',size=36,tracking=2)
        fragment=self.call('clipboard.read',start=0,end=6)
        self.call('page.add'); self.call('clipboard.paste',start=0,end=0,fragment=fragment)
        self.assertEqual(self.book.text(),'A EN A')
        runs=self.book.active.snapshot()['stories'][0]['blocks'][0]['runs']
        self.assertEqual(runs[0]['type'],'legacy'); self.assertEqual(runs[0]['sourceFontSha256'],fid.split(':')[1])
        self.assertEqual(runs[1]['type'],'unicode')
        self.assertEqual(self.book.active.package()['characters'][0]['attributes']['tracking'],2)
        self.call('history.undo'); self.assertEqual(self.book.text(),'')

    def test_find_replace_across_frames_is_one_transaction(self):
        self.write('A\u0301 cat catfish Cat')
        self.call('page.add'); self.write('cat CAT')
        hits=self.call('document.find',text='cat',whole_word=True)
        self.assertEqual(hits['count'],4)
        before=[f.text() for f in self.book.frames.values()]
        result=self.call('document.replace',text='cat',replacement='dog',whole_word=True)
        self.assertEqual(result['replacements'],4)
        self.call('history.undo'); self.assertEqual([f.text() for f in self.book.frames.values()],before)
        self.assertEqual(self.call('document.find',text='A\u0301')['count'],1)

    def test_partial_format_preserves_languages_fonts_and_exact_spacing(self):
        fid,path=self.font(); self.write('A English')
        self.call('document.format',start=0,end=1,font_id=fid,language='language.vayrshemon',size=36,tracking=2)
        self.call('document.format',start=0,end=9,color='#123456FF')
        runs=self.book.active.snapshot()['stories'][0]['blocks'][0]['runs']
        self.assertEqual([r['type'] for r in runs],['legacy','unicode'])
        styles={s['styleId']:s for s in self.book.model['styles']}
        self.assertEqual(styles[runs[0]['styleId']]['fontId'],fid)
        self.assertEqual(styles[runs[0]['styleId']]['fontSizeMicroPoints'],'36000000')
        self.assertEqual(self.book.active.package()['characters'][0]['attributes']['tracking'],2)
        self.call('history.undo'); self.assertEqual(self.book.active.package()['characters'][0]['attributes']['tracking'],2)

    def test_empty_frame_insertion_style_roundtrips(self):
        self.call('document.format',start=0,end=0,size=31,tracking=2,baseline=9)
        path=self.work/'empty.vay.json'; self.call('document.save',path=str(path))
        self.call('document.edit',start=0,end=0,text='After empty')
        run=self.book.active.snapshot()['stories'][0]['blocks'][0]['runs'][0]
        self.assertEqual(next(s for s in self.book.model['styles'] if s['styleId']==run['styleId'])['fontSizeMicroPoints'],'31000000')
        before=pages.inspect(self.book)['geometryHash']
        self.call('document.open',path=str(path),discardUnsaved=True)
        self.call('document.edit',start=0,end=0,text='After empty')
        self.assertEqual(pages.inspect(self.book)['geometryHash'],before)
        self.assertEqual(self.book.active.package()['characters'][0]['attributes']['tracking'],2)

    def test_next_input_format_in_nonempty_frame_through_api(self):
        fid,path=self.font(); self.write('English ')
        self.call('document.format',start=8,end=8,font_id=fid,language='language.vayrshemon',size=36,tracking=2)
        self.call('document.edit',start=8,end=8,text='A')
        runs=self.book.active.snapshot()['stories'][0]['blocks'][0]['runs']
        self.assertEqual(runs[-1]['type'],'legacy'); self.assertEqual(runs[-1]['sourceFontSha256'],fid.split(':')[1])
        self.assertEqual(self.book.active.package()['characters'][-1]['attributes']['tracking'],2)

    def test_font_catalog_undo_and_invalid_cross_frame_selection_are_atomic(self):
        fid,path=self.font(); self.assertEqual(len(self.book.capture()['fontSources']),1)
        self.call('history.undo'); self.assertEqual(self.book.capture()['fontSources'],[])
        self.call('history.redo'); self.assertEqual(self.book.capture()['fontSources'][0]['fontId'],fid)
        first=self.book.state['activeFrameId']; self.call('page.add'); before=self.book.capture()
        result=self.api.call('selection.set',dict(frame_id=first,start=900,end=900),expected_revision=self.book.revision,idempotency_key='bad-selection')
        self.assertFalse(result['ok']); self.assertEqual(self.book.capture(),before)

    def test_native_semantic_clipboard_and_external_newlines(self):
        fid,path=self.font(); self.write('A English')
        self.call('document.format',start=0,end=1,font_id=fid,language='language.vayrshemon',size=32)
        window=self.show(); editor=window.editor
        editor.selectAll(); editor.copy(); self.assertTrue(APP.clipboard().mimeData().hasFormat(MIME))
        self.call('page.add'); editor.paste()
        self.assertEqual(self.book.text(),'A English')
        self.assertEqual(self.book.active.snapshot()['stories'][0]['blocks'][0]['runs'][0]['type'],'legacy')
        self.call('history.undo'); APP.clipboard().setText('one\r\ntwo\rthree'); editor.paste()
        self.assertEqual(self.book.text(),'one\ntwo\nthree')

    def test_overflow_clipping_png_and_outline_svg_physical_dimensions(self):
        self.call('page.configure',width=200.125,height=150.375)
        self.call('frame.configure',x=20,y=20,width=120,height=30,overflow='clip')
        self.write('A\nA\nA\nA')
        self.call('document.format',start=0,end=7,size=22)
        report=self.call('layout.inspect'); self.assertTrue(report['frames'][0]['overflow'])
        png=self.work/'proof.png'; self.call('render.png',path=str(png),dpi=144)
        import struct
        self.assertEqual(struct.unpack('>II',png.read_bytes()[16:24]),(401,301))
        svg=self.work/'proof.svg'; self.call('render.svg',path=str(svg))
        root=ET.parse(svg).getroot(); self.assertEqual(root.attrib['width'],'200.125pt'); self.assertEqual(root.attrib['height'],'150.375pt')
        tags={e.tag.split('}')[-1] for e in root.iter()}; self.assertIn('path',tags); self.assertNotIn('text',tags); self.assertNotIn('image',tags)
        independent=QImage(401,301,QImage.Format.Format_ARGB32); independent.fill(QColor('magenta'))
        painter=QPainter(independent); QSvgRenderer(str(svg)).render(painter); painter.end()
        # Frame ends at 50pt = 100px at 144dpi. Lower overflow must be absent
        # even in a separately loaded SVG renderer.
        self.assertTrue(all(independent.pixelColor(x,y)==QColor('white') for y in range(103,300) for x in range(400)))
        self.assertEqual(self.book.text(),'A\nA\nA\nA')

    def test_recovery_after_forced_process_exit_keeps_unsaved_text(self):
        script="""import os,sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from vayrshemon.authoring import AuthoringSession
from vayrshemon.editor_api import EditorAPI
app=QApplication([])
s=AuthoringSession(Path(sys.argv[1]),source_fonts=False)
a=EditorAPI(s)
r=a.call('document.edit',dict(start=0,end=0,text='Recovered Á 😀'),expected_revision=0,idempotency_key='crash')
assert r['ok'],r
Path(sys.argv[2]).write_text(str(s.recovery_path),encoding='utf-8')
os._exit(73)
"""
        locator=self.work/'crash-location.txt'
        result=subprocess.run([sys.executable,'-c',script,str(self.work),str(locator)],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',timeout=30)
        self.assertEqual(result.returncode,73,result.stderr)
        path=locator.read_text(encoding='utf-8')
        self.assertIn(path,[c['path'] for c in self.book.recovery_list()])
        self.call('recovery.restore',path=path,discardUnsaved=True)
        self.assertEqual(self.book.text(),'Recovered Á 😀'); self.assertTrue(self.book.dirty)
        self.assertEqual(self.book.durable_revision,self.book.revision)
        self.assertNotIn(path,[c['path'] for c in self.book.recovery_list()])

    def test_failed_checkpoint_reports_last_durable_revision(self):
        self.write('durable'); old=self.book.durable_revision
        previous=self.book.recovery_path.read_bytes()
        with patch('vayrshemon.authoring.write_json',side_effect=OSError('disk full')):
            self.write('accepted but not durable')
        self.assertEqual(self.book.durable_revision,old); self.assertIn('disk full',self.book.recovery_error)
        self.assertEqual(self.book.recovery_path.read_bytes(),previous)
        self.write('durable again'); self.assertIsNone(self.book.recovery_error); self.assertEqual(self.book.durable_revision,self.book.revision)

    def test_unknown_format_or_corrupt_checkpoint_does_not_replace_document(self):
        self.write('keep this'); before=self.book.capture()
        wrong=self.work/'future.vay.json'; write_json(wrong,dict(format='vayrshemon.document',formatVersion='99.0.0'))
        result=self.api.call('document.open',dict(path=str(wrong),discardUnsaved=True),expected_revision=self.book.revision,idempotency_key='future')
        self.assertFalse(result['ok']); self.assertEqual(self.book.capture(),before)
        path=self.book.recovery_path.parent/'editor.corrupt.json'; write_json(path,dict(recoveryVersion='0.1.0',state=before,sha256='wrong'))
        self.assertTrue(any(c.get('error') for c in self.book.recovery_list()))
        result=self.api.call('recovery.restore',dict(path=str(path),discardUnsaved=True),expected_revision=self.book.revision,idempotency_key='corrupt')
        self.assertFalse(result['ok']); self.assertEqual(self.book.capture(),before)
        self.assertEqual(result['error']['code'],'RECOVERY_HASH_MISMATCH')

    def test_empty_legacy_insertion_format_survives_reopen(self):
        fid,path=self.font()
        self.call('document.format',start=0,end=0,font_id=fid,language='language.vayrshemon',size=36)
        document=self.work/'empty-legacy.vay.json'; self.call('document.save',path=str(document))
        self.call('document.open',path=str(document),discardUnsaved=True)
        self.call('document.edit',start=0,end=0,text='A')
        run=self.book.active.snapshot()['stories'][0]['blocks'][0]['runs'][0]
        self.assertEqual(run['type'],'legacy'); self.assertEqual(run['sourceFontSha256'],fid.split(':')[1])

    def test_native_window_input_ime_ui_headless_and_document_undo(self):
        window=self.show(); editor=window.editor; editor.setFocus()
        QTest.keyClicks(editor,'Hello')
        self.assertEqual(self.book.text(),'Hello'); self.assertEqual(self.book.durable_revision,self.book.revision)
        before=self.book.revision
        QCoreApplication.sendEvent(editor,QInputMethodEvent('かな',[]))
        self.assertEqual(self.book.revision,before)
        event=QInputMethodEvent(); event.setCommitString('仮名'); QCoreApplication.sendEvent(editor,event)
        self.assertEqual(self.book.text(),'Hello仮名')
        self.call('history.undo'); self.assertEqual(self.book.text(),'Hello')
        self.call('page.configure',width=420,height=600)
        geometry=pages.inspect(self.book)['geometryHash']; window.refresh(); APP.processEvents()
        self.assertEqual(pages.inspect(self.book)['geometryHash'],geometry)
        self.assertEqual(window.page_width.value(),420)
        self.assertTrue(window.access.toPlainText())

    def test_named_styles_and_features_keep_spacing_after_reopen(self):
        self.write('office AV')
        self.call('styles.define',name='Body',format=dict(size=24,tracking=1.5,baseline=8,color='#164E78FF'))
        self.call('styles.apply',start=0,end=9,name='Body')
        self.call('features.configure',kern=False,liga=False)
        self.assertEqual(self.book.active.package()['characters'][0]['attributes']['tracking'],1.5)
        path=self.work/'styles.vay.json'; self.call('document.save',path=str(path)); before=pages.inspect(self.book)['geometryHash']
        self.call('document.open',path=str(path),discardUnsaved=True)
        self.assertEqual(pages.inspect(self.book)['geometryHash'],before)
        self.assertEqual(self.book.state['styles'][0]['name'],'Body')
        self.call('page.add'); self.write('office AV')
        run=self.book.active.snapshot()['stories'][0]['blocks'][0]['runs'][0]
        self.assertEqual(self.book.active.style_features[run['styleId']],dict(kern=False,liga=False))

    def test_public_cli_and_stdio_mcp_authoring_contract(self):
        self.write('M2'); path=self.work/'mcp.vay.json'; self.call('document.save',path=str(path))
        requests=[dict(jsonrpc='2.0',id=1,method='initialize',params={'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'test','version':'1'}}),
                  dict(jsonrpc='2.0',method='notifications/initialized'),dict(jsonrpc='2.0',id=2,method='tools/list'),
                  dict(jsonrpc='2.0',id=3,method='tools/call',params={'name':'page_add','arguments':dict(width=400,height=500,expectedRevision=self.book.revision,idempotencyKey='m2-mcp',documentId=self.book.state['documentId'])})]
        process=subprocess.run([sys.executable,str(ROOT/'tools/run_lab.py'),'--root',str(self.work),'mcp','--headless','--editor','--no-source-fonts','--document',str(path)],
                               cwd=self.work,input=''.join(json.dumps(r)+'\n' for r in requests),capture_output=True,text=True,encoding='utf-8',timeout=30)
        self.assertEqual(process.returncode,0,process.stderr)
        output=[json.loads(line) for line in process.stdout.splitlines()]
        self.assertIn('recovery_restore',[t['name'] for t in output[1]['result']['tools']])
        self.assertFalse(output[2]['result']['isError'],output[2])

    def test_published_contracts_match_runtime(self):
        from tools.generate_m2_contracts import generate
        generate(self.work)
        for name in ('schemas/editor-command.schema.json','schemas/editor-document.schema.json','data/editor-mcp-tools.json','data/editor-capabilities.json'):
            self.assertEqual(load_json(ROOT/name),load_json(self.work/name),name)


if __name__=='__main__': unittest.main()
