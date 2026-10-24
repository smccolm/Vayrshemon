"""Real SVG menu exports: shared snapshots, both treatments and safe destinations."""
import base64
from pathlib import Path
import shutil
import time
import unittest
from unittest.mock import patch
import uuid
import xml.etree.ElementTree as ET
from PySide6.QtCore import QCoreApplication,QEvent
from PySide6.QtGui import QImage
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication,QMessageBox
from tools.m0.common import load_json
from tools.m0.synthetic import make_font
from vayrshemon.file_api import FileSession,FileAPI
from vayrshemon.file_window import FileWindow
from vayrshemon.proof_names import spread_proof_paths
from vayrshemon import publication

ROOT=Path(__file__).resolve().parents[1]
APP=QApplication.instance() or QApplication([])
STAMP=r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}_\d{3}'


class SpreadSVGTests(unittest.TestCase):
    def setUp(self):
        self.root=ROOT/'.local/test-svg-spread'/uuid.uuid4().hex
        shutil.copytree(ROOT/'schemas',self.root/'schemas');shutil.copytree(ROOT/'data',self.root/'data')
        self.book=FileSession(self.root,source_fonts=False,recovery=False);self.api=FileAPI(self.book)
        font=self.root/'synthetic.ttf';make_font(font)
        self.fid=self.call('fonts.load',path=str(font))['fontId'];self.ids=[]
        for i in range(2):
            self.call('page.add' if i else 'page.configure',width=200+i*20,height=240+i*20)
            self.ids.append(self.book.current_page()['pageId'])
            self.call('document.edit',start=0,end=0,text='A'*(i+1))
            self.call('document.format',start=0,end=i+1,font_id=self.fid,size=24)
        self.call('view.configure',mode='mono',monochromePaper='white')
        self.w=FileWindow(self.book,self.api);self.w.proof_dpi.setValue(72);self.w.page_controls.set_mode('two')

    def tearDown(self):
        self.w.job_timer.stop();self.w.forge_panel.timer.stop();self.w.timer.stop();self.w.hide()
        self.book.window=None;self.book._editor=None;self.w.deleteLater();self.book.finish()
        QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);APP.processEvents()

    def call(self,method,**params):
        r=self.api.call(method,params,expected_revision=self.book.revision,idempotency_key=uuid.uuid4().hex)
        self.assertTrue(r['ok'],r);return r['result']

    def export(self,path=None,side='_Left'):
        def choose(*args,**kwargs):
            name=Path(args[2]).name
            self.assertRegex(name,'^'+STAMP+side+r'\.svg$')
            self.chosen=path or self.root/name
            return str(self.chosen),'SVG (*.svg)'
        with patch('PySide6.QtWidgets.QFileDialog.getSaveFileName',side_effect=choose):
            self.w.svg_export_action.trigger()
        return self.chosen

    def wait(self):
        deadline=time.monotonic()+45
        while time.monotonic()<deadline:
            jobs=self.book.jobs.status()['jobs'];self.assertTrue(jobs,self.w.last_error)
            if jobs[-1]['status']!='running':return jobs[-1]
            QTest.qWait(30)
        self.fail('SVG worker timed out')

    def test_pair_from_file_menu_keeps_order_timestamp_and_snapshot(self):
        self.assertIn(self.w.export_menu.menuAction(),self.w.file_menu.actions())
        expected=[]
        for i,pid in enumerate(self.ids):
            path=self.root/f'expected-{i}.svg'
            publication.export(self.book,path,format='svg',mode='mono',dpi=72,raster_policy='raster',page_id=pid)
            expected.append(path.read_bytes())
        before=self.book.capture();path=self.export();self.assertEqual(self.book.capture(),before)
        job=self.book.jobs.status()['jobs'][-1]
        self.assertEqual(load_json(Path(job['folder'])/'snapshot.vay.json')['state'],before)
        self.call('document.edit',start=0,end=0,text='A')
        self.w.page_controls.set_mode('one')
        job=self.wait();self.assertEqual(job['status'],'completed',job);self.assertTrue(job['stale'])
        outputs=job['result']['outputs']
        self.assertEqual([o['path'] for o in outputs],spread_proof_paths(path,2,'svg'))
        self.assertEqual([o['pageId'] for o in job['outputs']],self.ids)
        self.assertEqual([Path(o['path']).read_bytes() for o in outputs],expected)
        for i,o in enumerate(outputs):
            svg=ET.parse(o['path']).getroot();self.assertEqual(svg.attrib['width'],f'{200+i*20}.0pt')
            self.assertFalse(any(e.tag.endswith('image') for e in svg.iter()))

    def test_color_pair_retains_exact_raster_effects_and_original_view(self):
        self.call('paint.bind',fontId=self.fid,enabled=True,kind='derived')
        self.call('publication.configure',background='#FF000000')
        self.call('view.configure',mode='color')
        expected=[publication.raster(self.book,p,'color',72) for p in self.book.state['pages']]
        before=self.book.capture();self.export();self.assertEqual(self.book.capture(),before)
        self.call('view.configure',mode='mono',monochromePaper='white')
        job=self.wait();self.assertEqual(job['status'],'completed',job)
        for o,reference in zip(job['result']['outputs'],expected):
            svg=ET.parse(o['path']).getroot()
            embedded=next(e for e in svg.iter() if e.tag.endswith('image'))
            actual=QImage.fromData(base64.b64decode(embedded.attrib['href'].split(',',1)[1]),'PNG')
            self.assertEqual(actual.convertToFormat(QImage.Format.Format_RGBA8888),reference.convertToFormat(QImage.Format.Format_RGBA8888))

    def test_single_and_unpaired_last_page_and_custom_stems(self):
        self.w.page_controls.set_mode('one');before=self.book.capture();path=self.export(side='')
        job=self.wait();self.assertEqual(job['status'],'completed',job);self.assertNotIn('outputs',job)
        self.assertEqual(ET.parse(path).getroot().attrib['width'],'220.0pt')
        self.assertEqual(self.book.capture(),before)
        self.call('page.add',width=180,height=240);self.w.page_controls.set_mode('two')
        before=self.book.capture();path=self.export(self.root/'custom_Right.SVG')
        job=self.wait();self.assertEqual(job['status'],'completed',job)
        self.assertEqual([Path(o['path']).name for o in job['result']['outputs']],['custom_Left.svg'])
        self.assertFalse((self.root/'custom_Right.svg').exists());self.assertEqual(self.book.capture(),before)
        for name in ('custom','custom.svg','custom_Left.svg','custom_Right.SVG'):
            self.assertEqual([Path(p).name for p in spread_proof_paths(name,2,'svg')],['custom_Left.svg','custom_Right.svg'])

    def test_temporary_progress_lock_keeps_status_available_and_both_exports_finish(self):
        self.export();job=self.book.jobs.status()['jobs'][-1]
        cached=dict(phase='rendering page 1 of 2')
        def read(path):return cached if Path(path).name=='progress.json' else load_json(path)
        with patch('vayrshemon.jobs.load_json',side_effect=read):
            self.assertEqual(self.book.jobs.status(job['jobId'])['progress'],cached)
        def locked(path):
            if Path(path).name=='progress.json':raise PermissionError('Simulated Windows sharing lock')
            return load_json(path)
        with patch('vayrshemon.jobs.load_json',side_effect=locked):
            status=self.book.jobs.status(job['jobId'])
            self.assertEqual(status['progress'],cached);self.assertEqual(status['status'],'running')
        job=self.wait();self.assertEqual(job['status'],'completed',job)
        self.assertEqual(len(job['result']['outputs']),2)

    def test_cancel_and_overwrite_guards_cover_both_files(self):
        with patch('PySide6.QtWidgets.QFileDialog.getSaveFileName',return_value=('','')):
            self.w.svg_export_action.trigger()
        self.assertFalse(self.book.jobs.status()['jobs'])
        path=self.export();job=self.book.jobs.status()['jobs'][-1];self.call('jobs.cancel',job_id=job['jobId'])
        self.assertEqual(self.book.jobs.status(job['jobId'])['status'],'cancelled')
        self.assertTrue(all(not Path(p).exists() for p in spread_proof_paths(path,2,'svg')))
        base=self.root/'replace.svg';left,right=map(Path,spread_proof_paths(base,2,'svg'))
        left.write_bytes(b'old left');right.write_bytes(b'old right')
        before=len(self.book.jobs.status()['jobs'])
        with patch('PySide6.QtWidgets.QMessageBox.question',return_value=QMessageBox.StandardButton.No):self.export(base)
        self.assertEqual(len(self.book.jobs.status()['jobs']),before)
        with patch('PySide6.QtWidgets.QMessageBox.question',return_value=QMessageBox.StandardButton.Yes):self.export(base)
        right.write_bytes(b'newer right');job=self.wait()
        self.assertEqual(job['status'],'failed');self.assertIn('TARGET_CHANGED',job['error'])
        self.assertEqual(left.read_bytes(),b'old left');self.assertEqual(right.read_bytes(),b'newer right')
        with patch('PySide6.QtWidgets.QMessageBox.question',return_value=QMessageBox.StandardButton.Yes):self.export(base)
        job=self.wait();self.assertEqual(job['status'],'completed',job)
        for p in (left,right):self.assertTrue(ET.parse(p).getroot().tag.endswith('svg'))


if __name__=='__main__':unittest.main()
