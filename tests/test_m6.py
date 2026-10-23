"""M6 navigation, partial shaping, portable recovery and worker failure boundaries."""
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import unittest
from unittest.mock import patch
import uuid
import zipfile
if os.name!='nt': os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtCore import QCoreApplication,QEvent,QPointF,Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication,QFileDialog
from tools.m0.synthetic import make_font
from tools.recovery import create_backup,verify_backup,restore_backup
from vayrshemon.reliability_session import ReliabilitySession
from vayrshemon.reliability_api import ReliabilityAPI,METHODS
from vayrshemon.reliability_window import ReliabilityWindow
from vayrshemon.language_session import LanguageSession
from vayrshemon import pages

ROOT=Path(__file__).resolve().parents[1]
APP=QApplication.instance() or QApplication([])


class ReliabilityTests(unittest.TestCase):
    def setUp(self):
        self.work=ROOT/'.local/test-m6'/uuid.uuid4().hex;self.work.mkdir(parents=True)
        shutil.copytree(ROOT/'schemas',self.work/'schemas')
        (self.work/'data').mkdir();shutil.copy2(ROOT/'data/fonts.json',self.work/'data/fonts.json')
        self.s=ReliabilitySession(self.work,source_fonts=False,recovery=False);self.api=ReliabilityAPI(self.s);self.window=None

    def tearDown(self):
        if self.window:
            self.window.hide();self.window.job_timer.stop();self.window.deleteLater();self.s.window=None
        self.s.finish()
        for frame in self.s.frames.values(): frame.deleteLater()
        self.s.deleteLater();QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);APP.processEvents()

    def call(self,method,**params):
        r=self.api.call(method,params,expected_revision=self.s.revision,document_id=self.s.state['documentId'],idempotency_key=uuid.uuid4().hex,origin='mcp')
        self.assertTrue(r['ok'],r);return r['result']

    def window_open(self):
        self.window=ReliabilityWindow(self.s,self.api);self.window.show();APP.processEvents();return self.window

    def save(self): return self.call('document.save-as',path=str(self.work/'source.vay.json'))

    def test_hand_drag_selection_return_and_keyboard_scope(self):
        self.call('document.edit',start=0,end=0,text='Structural navigation specimen')
        w=self.window_open();canvas=w.preview;self.call('ui.workspace',source=False,diagnostics=False,fit_page=True)
        self.save();before=self.s.capture();undo=len(self.s._undo)
        w.poll_jobs();self.assertIn('Backup verified',w.job_output.toPlainText())
        self.call('view.tool',tool='hand');origin=canvas.navigation_state()['pageOrigin'];vp=canvas.viewport()
        QTest.mousePress(vp,Qt.MouseButton.LeftButton,pos=vp.rect().center())
        p=QPointF(vp.rect().center())+QPointF(80,60)
        QCoreApplication.sendEvent(vp,QMouseEvent(QEvent.Type.MouseMove,p,p,Qt.MouseButton.NoButton,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier))
        QTest.mouseRelease(vp,Qt.MouseButton.LeftButton,pos=p.toPoint())
        self.assertEqual(canvas.navigation_state()['pageOrigin'],[origin[0]+80,origin[1]+60])
        self.assertEqual(before,self.s.capture());self.assertEqual(undo,len(self.s._undo));self.assertFalse(self.s.dirty)
        self.assertEqual(canvas.viewport().cursor().shape(),Qt.CursorShape.OpenHandCursor)
        self.call('view.tool',tool='select');self.call('view.center')
        area=pages.rect(self.s.locate()[1]);origin=canvas.navigation_state()['pageOrigin'];z=self.s.view['zoom']
        click=QPointF(origin[0]+(area.x()+20)*z,origin[1]+(area.y()+20)*z)
        QTest.mouseClick(vp,Qt.MouseButton.LeftButton,pos=click.toPoint());APP.processEvents()
        self.assertFalse(w.editor.parentWidget().isHidden());self.assertTrue(w.editor.hasFocus())
        self.assertIn('Click a frame to edit',w.preview_hint.text())
        QTest.keyClicks(w.editor,'hv ');self.assertEqual(canvas.tool,'select');self.assertIn('hv ',self.s.text())
        canvas.setFocus();QTest.keyClick(canvas,Qt.Key.Key_H);self.assertEqual(canvas.tool,'hand')
        QTest.keyClick(canvas,Qt.Key.Key_V);self.assertEqual(canvas.tool,'select')
        QTest.keyPress(canvas,Qt.Key.Key_Space);self.assertTrue(canvas.space_pan)
        QTest.keyRelease(canvas,Qt.Key.Key_Space);self.assertFalse(canvas.space_pan)
        for name in ('select','hand'): self.assertTrue(w.tool_buttons[name].accessibleName())

    def test_incremental_shaping_and_page_scope(self):
        self.call('document.edit',start=0,end=0,text='First independent frame')
        first=self.s.state['activeFrameId'];pid=self.s.current_page()['pageId']
        self.call('frame.add',x=40,y=160,width=200,height=200,name='Second');second=self.s.state['activeFrameId']
        self.call('document.edit',start=0,end=0,text='Second independent frame')
        before=pages.inspect(self.s);info=self.s.story_cache.info();self.assertEqual(info['misses'],2)
        self.call('document.edit',start=0,end=0,text='Edited ')
        after=pages.inspect(self.s);next_info=self.s.story_cache.info()
        self.assertEqual(next_info['misses']-info['misses'],1);self.assertEqual(next_info['hits']-info['hits'],1)
        a=[g for g in before['glyphs'] if g['sourceFrameId']==first];b=[g for g in after['glyphs'] if g['sourceFrameId']==first]
        self.assertEqual(a,b)
        self.call('page.add');self.call('document.edit',start=0,end=0,text='Separate page')
        pages.inspect(self.s);self.assertEqual(len(self.s.composition().stories),1)
        self.assertNotEqual(self.s.current_page()['pageId'],pid)
        self.s.story_cache.max_entries=1;self.s.invalidate_composition();pages.inspect(self.s,page_id=pid)
        self.assertLessEqual(self.s.story_cache.info()['entries'],1)
        # A request for a continuation page must include its source and the
        # neighbouring independent frame, matching the full M5 composition.
        target=self.s.state['activeFrameId'];target_page=self.s.current_page()['pageId']
        self.call('document.edit',start=0,end=len(self.s.text()),text='')
        self.call('frame.configure',frame_id=first,height=12)
        self.call('flow.set',source_frame_id=first,targets=[target])
        from vayrshemon.studio_typesetting import StudioComposition
        scoped=self.s.composition(page_id=target_page)
        self.assertEqual(set(scoped.frames),{first,second,target})
        self.assertEqual(scoped.report(target_page,100)['geometryHash'],StudioComposition(self.s,'color').report(target_page,100)['geometryHash'])

    def test_font_backup_offline_recovery_and_m5_compatibility(self):
        font=self.work/'font.ttf';make_font(font)
        fid=self.call('fonts.load',path=str(font))['fontId']
        self.call('document.edit',start=0,end=0,text='A😀 B')
        self.call('document.format',start=0,end=1,font_id=fid)
        saved=self.save();self.assertIsNone(saved['backupError']);bundle=Path(saved['backup']['path'])
        manifest,files=verify_backup(bundle);self.assertEqual(len(manifest['fonts']),1)
        font.rename(self.work/'unavailable.ttf')
        result=subprocess.run([sys.executable,'-S',str(ROOT/'tools/recovery.py'),'restore',str(bundle),'--out',str(self.work/'restored')],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr);restored=json.loads(result.stdout)
        other=LanguageSession(self.work,source_fonts=False,recovery=False)
        try:
            other.open(restored['path']);self.assertEqual(other.text(),self.s.text());self.assertEqual(other.state['language'],self.s.state['language'])
            self.assertEqual(other.state['paint'],self.s.state['paint']);self.assertIsNone(other.migrated_from)
        finally: other.finish();other.deleteLater()
        self.assertEqual((self.work/'restored/original.vay.json').read_bytes(),files['document.vay.json'])
        with self.assertRaisesRegex(ValueError,'NEW_DIRECTORY'): restore_backup(bundle,self.work/'restored')

    def test_tampered_backup_never_creates_destination(self):
        saved=self.save();bundle=Path(saved['backup']['path']);bad=self.work/'bad.vaybackup'
        with zipfile.ZipFile(bundle) as src,zipfile.ZipFile(bad,'w') as dst:
            for item in src.infolist(): dst.writestr(item.filename,b'{}' if item.filename=='document.vay.json' else src.read(item.filename))
        with self.assertRaisesRegex(ValueError,'HASH_MISMATCH'): restore_backup(bad,self.work/'bad-recovery')
        self.assertFalse((self.work/'bad-recovery').exists())

    def test_backup_failure_visible_without_lying_about_saved_file(self):
        with patch('tools.recovery.create_backup',side_effect=OSError('simulated offline destination')):
            result=self.save()
        self.assertTrue(Path(result['path']).exists());self.assertIn('offline',result['backupError']);self.assertFalse(self.s.dirty)
        self.assertIn('offline',self.call('session.status')['backupError'])

    def test_backup_rejects_external_change_and_ambiguous_json(self):
        from tools.recovery import read_document
        self.save();path=self.s.saved_path;payload=json.loads(path.read_text());payload['state']['title']='External edit';path.write_text(json.dumps(payload))
        with self.assertRaisesRegex(ValueError,'DOCUMENT_CHANGED_ON_DISK'): create_backup(path,self.work/'other-backup',expected_sha256=self.s.saved_hash)
        path.write_text('{"format":"vayrshemon.document","format":"different"}')
        with self.assertRaisesRegex(ValueError,'DUPLICATE_JSON_KEY'): read_document(path)

    def wait_job(self,jid):
        deadline=time.monotonic()+40
        while time.monotonic()<deadline:
            result=self.call('jobs.status',job_id=jid)
            if result['status']!='running': return result
            APP.processEvents();time.sleep(.05)
        self.fail('worker timeout')

    def export_job(self,path):
        return self.call('jobs.export',path=str(path),format='png',mode='mono',dpi=72,raster_policy='raster')

    def test_background_snapshot_staleness_and_cancel(self):
        self.call('document.edit',start=0,end=0,text='Snapshot specimen')
        out=self.work/'proof.png';job=self.export_job(out)
        self.call('document.edit',start=0,end=0,text='Later edit ')
        done=self.wait_job(job['jobId']);self.assertEqual(done['status'],'completed',done);self.assertTrue(done['stale']);self.assertTrue(out.exists())
        cancelled=self.work/'cancelled.png';job=self.export_job(cancelled)
        self.assertEqual(self.call('jobs.cancel',job_id=job['jobId'])['status'],'cancelled');self.assertFalse(cancelled.exists())

    def test_background_destination_race_and_failure_are_observable(self):
        out=self.work/'race.png';job=self.export_job(out);out.write_bytes(b'User file')
        done=self.wait_job(job['jobId']);self.assertEqual(done['status'],'failed',done);self.assertEqual(out.read_bytes(),b'User file');self.assertIn('error',done)
        self.call('page.configure',width=100000,height=100000)
        job=self.export_job(self.work/'huge.png');done=self.wait_job(job['jobId'])
        self.assertEqual(done['status'],'failed');self.assertTrue(Path(done['logPath']).read_text().strip());self.assertFalse((self.work/'huge.png').exists())

    def test_timestamp_dialogs_use_background_api_and_guards(self):
        self.window_open()
        for kind in ('png','svg'):
            with patch.object(QFileDialog,'getSaveFileName',return_value=('','')) as dialog:
                getattr(self.window,'export_'+kind)()
                self.assertRegex(Path(dialog.call_args.args[2]).name,r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}_\d{3}\.'+kind+'$')
        failed=self.api.call('view.tool',dict(tool='hand'),expected_revision=self.s.revision-1,idempotency_key=uuid.uuid4().hex,origin='mcp',document_id=self.s.state['documentId'])
        self.assertFalse(failed['ok']);self.assertEqual(self.window.preview.tool,'select')
        from vayrshemon.mcp import tools
        self.assertEqual(len(tools(METHODS)),len(METHODS));self.assertIn('jobs.export',METHODS)

    def test_release_integrity_activation_and_rollback(self):
        from tools.release import activate,rollback,verify,check_installed
        from tools.recovery import encoded,sha
        install=self.work/'install'
        for key in ('old','new'):
            folder=install/'releases'/key;(folder/'.local').mkdir(parents=True)
            payload=(key+' public source').encode();(folder/'source.py').write_bytes(payload)
            (folder/'release.json').write_bytes(encoded(dict(files={'source.py':dict(sha256=sha(payload),bytes=len(payload))})))
            (folder/'.local/install-verified.json').write_bytes(b'{}')
        activate(install,'old');activate(install,'new')
        self.assertEqual(rollback(install)['active'],'old');self.assertEqual(rollback(install)['active'],'new')
        (install/'releases/old/source.py').write_text('tampered')
        with self.assertRaisesRegex(ValueError,'MODIFIED'): rollback(install)
        self.assertEqual(json.loads((install/'active.json').read_text())['active'],'new')
        bad=self.work/'unsafe.zip'
        with zipfile.ZipFile(bad,'w') as z:z.writestr('../escape.py',b'')
        with self.assertRaisesRegex(ValueError,'UNSAFE_RELEASE_PATH'): verify(bad)


if __name__=='__main__': unittest.main()
