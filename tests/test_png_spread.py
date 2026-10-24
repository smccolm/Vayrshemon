"""The PNG button exports the visible arrangement with one snapshot/timestamp."""
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
import shutil,time,unittest,uuid
import numpy as np
from PySide6.QtWidgets import QApplication,QPushButton,QMessageBox
from PySide6.QtCore import Qt,QCoreApplication,QEvent
from PySide6.QtGui import QImage
from PySide6.QtTest import QTest
from tools.m0.common import load_json
from vayrshemon.gloss_api import GlossSession,GlossAPI
from vayrshemon.gloss_window import GlossWindow
from vayrshemon.proof_names import spread_png_paths

ROOT=Path(__file__).resolve().parents[1];APP=QApplication.instance() or QApplication([])
STAMP=r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}_\d{3}'


class SpreadPNGTests(unittest.TestCase):
    def setUp(self):
        self.work=ROOT/'.local/test-png-spread'/uuid.uuid4().hex;self.work.mkdir(parents=True)
        shutil.copytree(ROOT/'schemas',self.work/'schemas');shutil.copytree(ROOT/'data',self.work/'data')
        self.s=GlossSession(self.work,source_fonts=False,recovery=False);self.api=GlossAPI(self.s)
        self.left=self.s.current_page()['pageId'];self.call('document.edit',start=0,end=0,text='LEFT')
        self.call('page.add',width=480,height=900);self.right=self.s.current_page()['pageId'];self.call('document.edit',start=0,end=0,text='RIGHT')
        self.w=GlossWindow(self.s,self.api);self.w.proof_dpi.setValue(72);self.w.page_controls.set_mode('two')

    def call(self,m,**p):
        r=self.api.call(m,p,expected_revision=self.s.revision,idempotency_key=uuid.uuid4().hex);self.assertTrue(r['ok'],r);return r['result']

    def tearDown(self):
        self.w.job_timer.stop();self.w.forge_panel.timer.stop();self.w.hide();self.s.window=None;self.w.deleteLater();self.s.finish();QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)

    def click(self,pattern):
        choices=[]
        def choose(*args,**kwargs):
            suggestion=Path(args[2]);self.assertRegex(suggestion.name,'^'+pattern+'$')
            self.assertEqual(suggestion.parent,self.work/'Exports');self.assertTrue(suggestion.parent.is_dir())
            choices.append(suggestion);return str(choices[-1]),'PNG (*.png)'
        with patch('vayrshemon.png_export.QFileDialog.getSaveFileName',side_effect=choose):
            QTest.mouseClick(next(b for b in self.w.findChildren(QPushButton) if b.text()=='PNG'),Qt.MouseButton.LeftButton)
        self.assertEqual(len(choices),1);return choices[0]

    def wait(self):
        deadline=time.monotonic()+45
        while time.monotonic()<deadline:
            jobs=self.s.jobs.status()['jobs'];self.assertTrue(jobs)
            if jobs[-1]['status']!='running':return jobs[-1]
            QTest.qWait(50)
        self.fail('PNG worker timed out')

    def test_pair_uses_visible_order_shared_timestamp_and_immutable_snapshot(self):
        before=self.s.capture();left_path=self.click(STAMP+'_Left.png');self.assertEqual(self.s.capture(),before)
        job=self.s.jobs.status()['jobs'][-1];frozen=load_json(Path(job['folder'])/'snapshot.vay.json')['state']
        self.assertEqual(frozen,before)
        self.call('document.edit',start=0,end=0,text='LATER EDIT ')
        job=self.wait();self.assertEqual(job['status'],'completed',job);self.assertTrue(job['stale'])
        outputs=job['result']['outputs'];self.assertEqual([o['path'] for o in outputs],spread_png_paths(left_path))
        self.assertEqual([o['pageId'] for o in job['outputs']],[self.left,self.right])
        images=[QImage(o['path']) for o in outputs];self.assertTrue(all(not i.isNull() for i in images));self.assertNotEqual(images[0].width(),images[1].width())
        self.assertEqual((images[1].width(),images[1].height()),(480,900))
        self.assertEqual(load_json(Path(job['folder'])/'snapshot.vay.json')['state'],before)

    def test_single_page_exports_selected_right_page_without_side_or_title(self):
        self.w.page_controls.set_mode('one');before=self.s.capture();path=self.click(STAMP+'.png');job=self.wait()
        self.assertEqual(job['status'],'completed',job);self.assertNotIn('outputs',job)
        self.assertEqual((QImage(str(path)).width(),QImage(str(path)).height()),(480,900));self.assertEqual(self.s.capture(),before)
        self.assertEqual(len(list((self.work/'Exports').glob('*.png'))),1)

    def test_monochrome_pair_worker_uses_contrasting_neutral_ink(self):
        self.call('document.format',start=0,end=5,color='#0000FFFF')
        self.call('publication.configure',background='#FF123456')
        self.call('view.configure',mode='mono');before=self.s.capture()
        self.click(STAMP+'_Left.png');job=self.wait();self.assertEqual(job['status'],'completed',job)
        for output in job['result']['outputs']:
            image=QImage(output['path']).convertToFormat(QImage.Format.Format_RGBA8888)
            data=np.frombuffer(image.constBits(),np.uint8).reshape(image.height(),image.width(),4)
            self.assertTrue((data[:,:,0]==data[:,:,1]).all());self.assertTrue((data[:,:,1]==data[:,:,2]).all())
            self.assertEqual(tuple(data[2,2]),(0,0,0,255));self.assertGreater(data[:,:,0].max(),200)
        self.assertEqual(self.s.capture(),before)

    def test_paper_dropdown_and_single_png_use_saved_white_preference(self):
        self.call('publication.configure',background='#FF000000');before=self.s.capture()
        self.w.mode.setCurrentIndex(self.w.mode.findData('mono-white'))
        self.assertEqual(self.s.view['mode'],'mono');self.assertEqual(self.s.view['monochromePaper'],'white')
        self.assertEqual(self.s.capture()['pages'],before['pages']);self.assertEqual(self.s.state['paint'],before['paint'])
        self.w.page_controls.set_mode('one');path=self.click(STAMP+'.png')
        # Switching the live view must not change the worker's captured choice.
        self.w.mode.setCurrentIndex(self.w.mode.findData('mono'));self.assertEqual(self.s.view['monochromePaper'],'black')
        job=self.wait();self.assertEqual(job['status'],'completed',job)
        image=QImage(str(path)).convertToFormat(QImage.Format.Format_RGBA8888)
        data=np.frombuffer(image.constBits(),np.uint8).reshape(image.height(),image.width(),4)
        self.assertEqual(tuple(data[2,2]),(255,255,255,255));self.assertLess(data[:,:,0].min(),20)
        self.assertTrue((data[:,:,0]==data[:,:,1]).all());self.assertTrue((data[:,:,1]==data[:,:,2]).all())
        self.w.mode.setCurrentIndex(self.w.mode.findData('color'));self.assertEqual(self.s.view['mode'],'color')
        self.assertEqual(self.s.capture()['pages'],before['pages']);self.assertEqual(self.s.state['paint'],before['paint'])

    def test_pair_overwrite_decline_or_changed_right_preserves_both_destinations(self):
        base=self.work/'pair.png';left,right=map(Path,spread_png_paths(base));left.write_bytes(b'old left');right.write_bytes(b'old right')
        with patch('vayrshemon.png_export.QFileDialog.getSaveFileName',return_value=(str(base),'PNG')),patch('vayrshemon.png_export.QMessageBox.question',return_value=QMessageBox.StandardButton.No):self.w.export_png()
        self.assertFalse(self.s.jobs.status()['jobs'])
        with patch('vayrshemon.png_export.QFileDialog.getSaveFileName',return_value=(str(base),'PNG')),patch('vayrshemon.png_export.QMessageBox.question',return_value=QMessageBox.StandardButton.Yes):self.w.export_png()
        right.write_bytes(b'changed during rendering');job=self.wait();self.assertEqual(job['status'],'failed');self.assertIn('TARGET_CHANGED',job['error'])
        self.assertEqual(left.read_bytes(),b'old left');self.assertEqual(right.read_bytes(),b'changed during rendering')

    def test_cancel_prevents_both_outputs_and_empty_picker_starts_nothing(self):
        with patch('vayrshemon.png_export.QFileDialog.getSaveFileName',return_value=('','PNG')):self.w.export_png()
        self.assertFalse(self.s.jobs.status()['jobs'])
        path=self.click(STAMP+'_Left.png');job=self.s.jobs.status()['jobs'][-1];self.call('jobs.cancel',job_id=job['jobId'])
        self.assertEqual(self.s.jobs.status(job['jobId'])['status'],'cancelled');self.assertTrue(all(not Path(p).exists() for p in spread_png_paths(path)))

    def test_unpaired_final_page_exports_only_left_and_preserves_user_stems(self):
        self.call('page.add',width=400,height=600);path=self.click(STAMP+'_Left.png');job=self.wait()
        self.assertEqual(job['status'],'completed',job);self.assertEqual(len(job['result']['outputs']),1)
        self.assertTrue(path.exists());self.assertFalse(Path(spread_png_paths(path)[1]).exists())
        for name in ('custom','custom.png','custom_Left.png','custom_Right.PNG'):
            self.assertEqual([Path(p).name for p in spread_png_paths(name)],['custom_Left.png','custom_Right.png'])


if __name__=='__main__':unittest.main()
