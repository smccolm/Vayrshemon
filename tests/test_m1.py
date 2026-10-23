"""Native input, preservation, transport and rendering regression gates."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
import uuid

if os.name != 'nt':
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import Qt, QPoint, QCoreApplication, QMimeData
from PySide6.QtGui import QInputMethodEvent, QTextCursor, QFont
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from tools.m0.synthetic import make_font, document, unicode_run
from tools.m0.common import write_json, load_json
from vayrshemon.session import Session, utf16_length, scalar_offset, micro_points
from vayrshemon.api import API, LocalServer
from vayrshemon.desktop import Editor, accessibility
from vayrshemon import layout

ROOT = Path(__file__).resolve().parents[1]
APP = QApplication.instance() or QApplication([])


class LabTests(unittest.TestCase):
    def setUp(self):
        self.session = Session(ROOT, source_fonts=False)
        self.api = API(self.session)
        self.work = ROOT / '.local/test-m1' / uuid.uuid4().hex
        self.work.mkdir(parents=True)

    def tearDown(self):
        if self.session.editor:
            self.session.editor.hide()
            self.session.editor.deleteLater()
        self.session.deleteLater()
        APP.processEvents()

    def simple(self, text):
        value = document('document.test', [unicode_run(text)])
        value['layoutProfile'] = 'layout.qt-6.8.3-m1'
        self.session.load_model(value)

    def mutate(self, method, **params):
        result = self.api.call(method, params, expected_revision=self.session.revision, idempotency_key=uuid.uuid4().hex)
        self.assertTrue(result['ok'], result)
        return result

    def test_native_edit_graphemes_undo_and_unicode_preservation(self):
        self.simple('A\u0301 😀\u00a0Z')
        before = self.session.text()
        self.assertEqual(before, 'A\u0301 😀\u00a0Z')
        self.assertRaisesRegex(ValueError, 'GRAPHEME', self.session.edit, 1, 1, 'x')
        self.assertRaisesRegex(ValueError, 'SURROGATE', self.session.edit, 4, 4, 'x')
        self.mutate('document.edit', start=5, end=5, text=' / revised')
        self.mutate('history.undo')
        self.assertEqual(before, self.session.text())
        self.mutate('history.redo')
        self.assertIn('revised', self.session.text())

    def test_revision_checks_and_idempotency(self):
        self.simple('Hello')
        args = dict(start=5, end=5, text='!')
        first = self.api.call('document.edit', args, expected_revision=0, idempotency_key='retry')
        self.assertTrue(first['ok'])
        self.assertEqual(self.api.call('document.edit', args, expected_revision=0, idempotency_key='retry'), first)
        self.assertEqual(self.session.text(), 'Hello!')
        conflict = self.api.call('document.edit', args, expected_revision=0, idempotency_key='another')
        self.assertFalse(conflict['ok'])
        self.assertIn('STALE_REVISION', conflict['error']['code'])
        misuse = self.api.call('document.edit', dict(args, text='?'), expected_revision=0, idempotency_key='retry')
        self.assertFalse(misuse['ok'])

    def test_save_reopen_semantics_and_external_change(self):
        self.simple('A\u0301 Á\u00a0😀\nSecond line')
        path = self.work/'roundtrip.vaylab.json'
        before = self.session.snapshot()
        self.session.save(path)
        self.session.edit(0, 0, 'changed')
        self.session.open(path)
        self.assertEqual(before, self.session.snapshot())
        self.assertEqual('A\u0301 Á\u00a0😀\nSecond line', self.session.text())
        path.write_text('{}', encoding='utf-8')
        self.assertRaisesRegex(ValueError, 'CHANGED_ON_DISK', self.session.save, path)

    def test_live_reopen_rejects_stale_commands_and_correlates_components(self):
        self.simple('before')
        path=self.work/'live-reopen.vaylab.json'
        self.mutate('document.save',path=str(path))
        self.mutate('document.edit',start=6,end=6,text=' edit')
        stale_revision=self.session.revision
        opened=self.mutate('document.open',path=str(path),discardUnsaved=True)
        self.assertGreater(opened['revision'],stale_revision)
        self.assertEqual(self.session.text(),'before')
        rejected=self.api.call('document.edit',dict(start=0,end=0,text='stale'),expected_revision=stale_revision,
                               idempotency_key='pre-open-command',origin='mcp',document_id='document.test')
        self.assertEqual(rejected['error']['code'],'STALE_REVISION')
        related=[e for e in self.session.log.tail(100) if e['traceId']==opened['traceId']]
        self.assertEqual([e['code'] for e in related],['COMMAND_STARTED','DOCUMENT_OPENED','COMMAND_COMPLETED'])

    def test_arbitrary_page_dimensions_and_bounded_tiles(self):
        self.simple('A')
        self.session.set_page(123.456, 234.567, 'mm')
        self.assertEqual(self.session.model['pages'][0]['widthMicroPoints'], micro_points(123.456, 'mm'))
        self.session.set_page(1_000_000, 1_000_000)
        self.assertRaisesRegex(ValueError, 'RASTER_LIMIT', layout.render, self.session)
        image, report = layout.render(self.session, region=[0,0,256,256])
        self.assertEqual((image.width(), image.height()), (256,256))
        self.assertEqual(report['bufferBytes'], 256*256*4)
        self.assertRaises(ValueError, self.session.set_page, float('nan'), 100)
        self.assertRaises(ValueError, self.session.set_page, 1, 1)

    def test_same_family_fonts_stay_separate_and_source_is_unchanged(self):
        first, second = self.work/'first.ttf', self.work/'second.ttf'
        make_font(first, 600)
        make_font(second, 800)
        before = first.read_bytes()
        a, b = self.session.fonts.register(first), self.session.fonts.register(second)
        self.assertEqual(a.original_family, b.original_family)
        self.assertNotEqual(a.family, b.family)
        self.assertEqual(before, first.read_bytes())
        self.simple('AAA')
        self.session.format_range(0,3,font_id=a.font_id,size=40)
        one = layout.inspect(self.session)
        self.session.format_range(0,3,font_id=b.font_id,size=40)
        two = layout.inspect(self.session)
        self.assertEqual({g['fontId'] for g in one['glyphs']}, {a.font_id})
        self.assertEqual({g['fontId'] for g in two['glyphs']}, {b.font_id})
        self.assertGreater(two['lines'][0]['width'], one['lines'][0]['width'])
        first.write_bytes(b'changed')
        self.assertRaisesRegex(ValueError, 'MISSING_OR_CHANGED', self.session.fonts.resolve, a.font_id)

    def test_layer_registration_reuses_master_positions(self):
        from fontTools.ttLib import TTFont
        files=[]
        for i in range(3):
            path=self.work/f'layer{i}.ttf'
            make_font(path)
            font=TTFont(path, recalcTimestamp=False)
            font['name'].setName(f'Layer {i}', 1, 3, 1, 0x409)
            # Different outlines and side bearings are intentional; advances agree.
            font['glyf']['A'].coordinates.translate((i*10, 0))
            advance, bearing=font['hmtx'].metrics['A']
            font['hmtx'].metrics['A']=(advance,bearing+i*10)
            font.save(path)
            files.append(self.session.fonts.register(path))
        self.session.fonts.set_recipe(files[2], files)
        self.simple('A A A')
        self.session.format_range(0,5,font_id=files[2].font_id, language='language.vayrshemon', size=48)
        before = layout.inspect(self.session)['geometryHash']
        mono,_=layout.render(self.session, mode='mono', region=[0,0,300,150])
        color,_=layout.render(self.session, mode='color', region=[0,0,300,150])
        self.assertNotEqual(bytes(mono.bits()),bytes(color.bits()))
        self.assertEqual(before,layout.inspect(self.session)['geometryHash'])
        for layer in self.session.fonts.recipe['layers']:
            layer['enabled']=False
        blank,_=layout.render(self.session, mode='color', region=[0,0,300,150])
        self.assertNotEqual(bytes(blank.bits()),bytes(color.bits()))

    def test_native_editor_headless_geometry_and_accessibility(self):
        self.simple('office A\u0301 😀\nHello العربية')
        before=layout.inspect(self.session)
        editor=Editor(self.session)
        editor.resize(600,400)
        editor.show()
        APP.processEvents()
        after=layout.inspect(self.session)
        self.assertEqual(before['geometryHash'],after['geometryHash'])
        access=accessibility(editor)
        self.assertTrue(access['editableText'])
        self.assertTrue(access['textInterface'])
        self.assertEqual(access['text'],self.session.text())
        editor.setTextCursor(self.session.range_cursor(0,6))
        self.assertEqual(accessibility(editor)['selections'], [(0,6)])
        cursor=editor.textCursor()
        cursor.setPosition(0)
        editor.setTextCursor(cursor)
        QTest.keyClick(editor,Qt.Key.Key_Right)
        QTest.keyClick(editor,Qt.Key.Key_Down)
        self.assertGreater(editor.textCursor().position(),0)
        rect=editor.cursorRect()
        QTest.mouseClick(editor.viewport(),Qt.MouseButton.LeftButton,pos=rect.center())
        self.assertGreaterEqual(editor.textCursor().position(),0)

    def test_ime_preedit_commit_clipboard_and_native_undo(self):
        clipboard_copy = QMimeData()
        original = QApplication.clipboard().mimeData()
        if original:
            for format_name in original.formats():
                clipboard_copy.setData(format_name, original.data(format_name))
        self.addCleanup(lambda: QApplication.clipboard().setMimeData(clipboard_copy))
        self.simple('')
        editor=Editor(self.session)
        editor.show()
        editor.setFocus()
        APP.processEvents()
        QCoreApplication.sendEvent(editor,QInputMethodEvent('かな', []))
        self.assertTrue(self.session.composing)
        self.assertEqual(self.session.revision,0)
        self.assertEqual(self.session.text(),'')
        blocked=self.api.call('document.edit',dict(start=0,end=0,text='X'),expected_revision=0,idempotency_key='blocked-ime')
        self.assertFalse(blocked['ok'])
        self.assertEqual(blocked['error']['code'],'COMPOSITION_ACTIVE')
        event=QInputMethodEvent()
        event.setCommitString('仮名')
        QCoreApplication.sendEvent(editor,event)
        self.assertFalse(self.session.composing)
        self.assertEqual(self.session.text(),'仮名')
        editor.selectAll()
        editor.copy()
        self.assertEqual(QApplication.clipboard().text(),'仮名')
        cursor=editor.textCursor()
        cursor.clearSelection()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        editor.setTextCursor(cursor)
        editor.paste()
        self.assertEqual(self.session.text(),'仮名仮名')
        editor.undo()
        self.assertEqual(self.session.text(),'仮名')

    def test_render_dpi_does_not_reflow(self):
        self.simple('DPI test\nA\u0301 😀')
        before=layout.inspect(self.session)['geometryHash']
        one,a=layout.render(self.session,dpi=96,region=[0,0,200,100])
        two,b=layout.render(self.session,dpi=192,region=[0,0,200,100])
        self.assertEqual((one.width()*2,one.height()*2),(two.width(),two.height()))
        self.assertEqual(before,layout.inspect(self.session)['geometryHash'])

    def test_protected_paths_and_invalid_model_leave_document_unchanged(self):
        self.simple('Keep this')
        before=self.session.snapshot()
        bad=deepcopy(before)
        bad['pages'][0]['widthMicroPoints']='1'
        self.assertRaises(ValueError,self.session.load_model,bad)
        self.assertEqual(self.session.snapshot(),before)
        self.assertRaises(ValueError,self.session.save,ROOT/'Inputs/do-not-write.vaylab.json')
        self.assertRaises(ValueError,self.session.edit,0,0,'\ud800')
        self.assertRaises(ValueError,self.session.edit,0,0,'\r\n')

    def test_local_transport_and_live_edit(self):
        from PySide6.QtCore import QProcess
        self.simple('Hello')
        server=LocalServer(self.api,publish=False)
        try:
            process=QProcess()
            process.setWorkingDirectory(str(ROOT))
            process.start(sys.executable,['-m','vayrshemon','call','document.edit','--params',json.dumps(dict(start=5,end=5,text=' from MCP bridge')),
                                          '--expected-revision','0','--idempotency-key','live-test','--document-id','document.test','--descriptor',str(server.descriptor)])
            deadline=__import__('time').monotonic()+15
            while process.state()!=QProcess.ProcessState.NotRunning and __import__('time').monotonic()<deadline:
                APP.processEvents()
                QTest.qWait(10)
            if process.state()!=QProcess.ProcessState.NotRunning:
                process.kill()
                self.fail('Local transport timed out')
            output=json.loads(bytes(process.readAllStandardOutput()))
            self.assertTrue(output['ok'],output)
            self.assertEqual(self.session.text(),'Hello from MCP bridge')
        finally:
            server.close()

    def test_stdio_mcp_handshake_and_revision_checked_edit(self):
        self.simple('seed')
        doc_path=self.work/'mcp.vaylab.json'
        self.session.save(doc_path)
        requests=[dict(jsonrpc='2.0',id=1,method='initialize',params={'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'test','version':'1'}}),
                  dict(jsonrpc='2.0',method='notifications/initialized'),
                  dict(jsonrpc='2.0',id=2,method='tools/list'),
                  dict(jsonrpc='2.0',id=3,method='tools/call',params={'name':'document_edit','arguments':{'start':0,'end':0,'text':'MCP: ','expectedRevision':0,'idempotencyKey':'mcp-1','documentId':'document.test'}}),
                  dict(jsonrpc='2.0',id=4,method='tools/call',params={'name':'document_read','arguments':{}})]
        result=subprocess.run([sys.executable,str(ROOT/'tools/run_lab.py'),'mcp','--headless','--no-source-fonts','--document',str(doc_path)],
                              cwd=self.work,input=''.join(json.dumps(r)+'\n' for r in requests),text=True,encoding='utf-8',capture_output=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stderr)
        responses=[json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual([r['id'] for r in responses],[1,2,3,4])
        self.assertGreaterEqual(len(responses[1]['result']['tools']),15)
        self.assertFalse(responses[2]['result']['isError'])
        document=json.loads(responses[3]['result']['content'][0]['text'])
        self.assertTrue(document['result']['text'].startswith('MCP: '))

    def test_feature_undo_save_reopen_keeps_actual_features(self):
        self.simple('office AV')
        self.mutate('features.configure',kern=False,liga=False)
        self.assertFalse(layout.inspect(self.session)['glyphs'][0]['features']['kern'])
        self.mutate('history.undo')
        before=layout.inspect(self.session)
        self.assertTrue(before['glyphs'][0]['features']['kern'])
        path=self.work/'features.vaylab.json'
        self.session.save(path)
        self.session.open(path)
        self.assertEqual(before['geometryHash'],layout.inspect(self.session)['geometryHash'])

    def test_invalid_lab_settings_do_not_mutate_live_session(self):
        self.simple('keep me')
        path=self.work/'invalid.vaylab.json'
        self.session.save(path)
        payload=load_json(path)
        payload['lab']['view']['zoom']=-5
        write_json(path,payload)
        before=self.session.snapshot()
        self.assertRaises(Exception,self.session.open,path)
        self.assertEqual(before,self.session.snapshot())

    def test_mutation_cannot_target_another_document_at_same_revision(self):
        result=self.api.call('document.edit',dict(start=0,end=0,text='wrong'),expected_revision=0,
                             idempotency_key='wrong-document',origin='mcp',document_id='document.some-other-file')
        self.assertFalse(result['ok'])
        self.assertEqual(result['error']['code'],'DOCUMENT_ID_MISMATCH')

    def test_fallback_cluster_ranges_do_not_swallow_neighboring_fonts(self):
        self.simple('A 😀 Z')
        info=layout.inspect(self.session)
        for glyph in info['glyphs']:
            if glyph['source']==' ':
                self.assertEqual(glyph['sourceUtf16'][1]-glyph['sourceUtf16'][0],1)
        self.assertEqual(sorted({tuple(g['sourceUtf16']) for g in info['glyphs']}),[(0,1),(1,2),(2,4),(4,5),(5,6)])

    def test_png_dimensions_and_physical_resolution(self):
        import struct
        self.simple('A')
        path=self.work/'physical.png'
        layout.render(self.session,path,dpi=144)
        data=path.read_bytes()
        self.assertEqual(struct.unpack('>II',data[16:24]),(1224,1584))
        offset=8
        found=False
        while offset<len(data):
            length=struct.unpack('>I',data[offset:offset+4])[0]
            if data[offset+4:offset+8]==b'pHYs':
                x,y,unit=struct.unpack('>IIB',data[offset+8:offset+8+length])
                self.assertEqual((x,y,unit),(5669,5669,1))
                found=True
            offset+=12+length
        self.assertTrue(found)

    def test_same_font_multiple_colors_and_paragraph_leading_roundtrip(self):
        self.simple('AAAA\nAAAA')
        cursor=QTextCursor(self.session.doc)
        bf=cursor.blockFormat()
        from PySide6.QtGui import QTextBlockFormat
        bf.setLineHeight(180,QTextBlockFormat.LineHeightTypes.ProportionalHeight.value)
        cursor.setBlockFormat(bf)
        self.session.format_range(0,9,size=40,color='#FF0000FF')
        self.session.format_range(5,9,size=40,color='#0000FFFF')
        image,_=layout.render(self.session,region=[0,0,300,250],mode='mono')
        colors={image.pixelColor(x,y).name() for x in range(image.width()) for y in range(image.height())}
        self.assertIn('#ff0000',colors)
        self.assertIn('#0000ff',colors)
        before=layout.inspect(self.session)['geometryHash']
        path=self.work/'leading.vaylab.json'
        self.session.save(path)
        self.session.open(path)
        self.assertEqual(before,layout.inspect(self.session)['geometryHash'])

    def test_controls_reflect_api_changes_without_extra_mutations(self):
        from vayrshemon.desktop import LabWindow
        window=LabWindow(self.session,self.api)
        self.addCleanup(window.deleteLater)
        self.mutate('page.configure',width=400.125,height=500.25)
        self.mutate('view.configure',zoom=1.25,baselines=True)
        self.mutate('features.configure',kern=False)
        revision=self.session.revision
        window.refresh()
        self.assertEqual(self.session.revision,revision)
        self.assertEqual(window.width_input.value(),400.125)
        self.assertEqual(window.height_input.value(),500.25)
        self.assertTrue(window.overlay_checks['baselines'].isChecked())
        self.assertFalse(window.feature_checks['kern'].isChecked())
        self.assertEqual(window.zoom_control.value(),125)
        window.width_input.setValue(123)
        window.refresh()
        self.assertEqual(window.width_input.value(),123)

    def test_native_line_break_cannot_exceed_document_limit(self):
        self.simple('A'*100_000)
        editor=Editor(self.session)
        cursor=editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        editor.setTextCursor(cursor)
        QTest.keyClick(editor,Qt.Key.Key_Return)
        self.assertEqual(len(self.session.text()),100_000)
        editor.setTextCursor(self.session.range_cursor(99_999,100_000))
        QTest.keyClicks(editor,'Z')
        self.assertTrue(self.session.text().endswith('Z'))
        self.assertEqual(len(self.session.text()),100_000)


if __name__=='__main__':
    unittest.main()
