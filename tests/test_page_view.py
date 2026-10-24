"""Facing views preserve physical pages and route interaction to either page."""
from copy import deepcopy
import shutil
import unittest
import uuid
from pathlib import Path
from PySide6.QtCore import Qt,QCoreApplication,QEvent,QPoint
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from tools.m0.common import load_json
from vayrshemon.reading_api import ReadingSession,ReadingAPI
from vayrshemon.reading_window import ReadingWindow
from vayrshemon import pages

ROOT=Path(__file__).resolve().parents[1]
APP=QApplication.instance() or QApplication([])


class PageViewTests(unittest.TestCase):
    def setUp(self):
        self.root=ROOT/'.local/test-page-view'/uuid.uuid4().hex
        shutil.copytree(ROOT/'schemas',self.root/'schemas');shutil.copytree(ROOT/'data',self.root/'data')
        self.s=ReadingSession(self.root,source_fonts=False,recovery=False);self.api=ReadingAPI(self.s)
        self.left=self.s.current_page()['pageId'];self.left_frame=self.s.state['activeFrameId']
        self.call('page.add',width=480,height=900);self.right=self.s.current_page()['pageId'];self.right_frame=self.s.state['activeFrameId']
        self.call('frame.select',frame_id=self.left_frame)
        self.w=ReadingWindow(self.s,self.api);self.w.resize(1400,900);self.w.show();self.w.sidebar_dock.configure(expanded=False)
        self.w.configure_workspace(source=False,diagnostics=False,guides=False);APP.processEvents()

    def call(self,method,**params):
        r=self.api.call(method,params,expected_revision=self.s.revision,idempotency_key=uuid.uuid4().hex)
        self.assertTrue(r['ok'],r);return r['result']

    def tearDown(self):
        self.w.job_timer.stop();self.w.forge_panel.timer.stop();self.w.hide();self.s.window=None;self.w.deleteLater();self.s.finish()
        QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);APP.processEvents()

    def test_icon_buttons_toggle_without_document_changes_and_fit_the_spread(self):
        original=self.s.capture();history=deepcopy(self.s.history);revision=self.s.revision
        for mode in ('two','one','two'):
            b=self.w.page_controls.buttons[mode]
            self.assertEqual(b.text(),'');self.assertFalse(b.icon().isNull());self.assertTrue(b.accessibleName())
            QTest.mouseClick(b,Qt.MouseButton.LeftButton);APP.processEvents()
            self.assertTrue(b.isChecked());self.assertEqual(self.w.preview.page_mode,mode)
            self.assertEqual(self.s.capture(),original);self.assertEqual(self.s.history,history);self.assertEqual(self.s.revision,revision)
        self.assertLessEqual(self.w.zoom.width(),220)
        self.assertEqual(load_json(self.w.page_controls.path)['mode'],'two')
        self.w.configure_workspace(fit_width=True);area=self.w.preview.display_rect()
        self.assertLessEqual(area.width()*self.s.view['zoom'],self.w.preview.viewport().width()-55)
        self.w.preview.update_page();nav=self.w.preview.navigation_state()
        self.assertEqual(nav['pageOrigin'][1],self.w.preview.RULER)
        self.assertAlmostEqual(nav['pageOrigin'][0]+area.width()*nav['zoom']/2,(nav['viewport'][0]+self.w.preview.RULER)/2,delta=1)
        self.assertEqual(self.s.capture()['pages'],original['pages'])
        self.w.configure_workspace(fit_height=True)
        self.assertLessEqual(area.height()*self.s.view['zoom'],self.w.preview.viewport().height()-55)

    def test_select_right_page_blank_frame_and_keep_pair_then_one_and_odd_page(self):
        self.call('view.pages',mode='two');self.w.configure_workspace(fit_width=True);APP.processEvents()
        p,area=self.w.preview.display_pages()[1];self.assertEqual(p['pageId'],self.right)
        f=pages.rect(p['frames'][0]);x=area.x()+f.x()+10;y=f.y()+10
        self.assertEqual(self.w.preview.hit_test(x,y)['frameId'],self.right_frame)
        self.assertIsNone(self.w.preview.hit_test(area.x()-5,y)['frameId'])
        nav=self.w.preview.navigation_state();position=QPoint(round(nav['pageOrigin'][0]+x*nav['zoom']),round(nav['pageOrigin'][1]+y*nav['zoom']))
        QTest.mouseClick(self.w.preview.viewport(),Qt.MouseButton.LeftButton,pos=position);APP.processEvents()
        self.assertEqual(self.s.state['activeFrameId'],self.right_frame)
        self.assertEqual([p['pageId'] for p,_ in self.w.preview.display_pages()],[self.left,self.right])
        self.call('view.pages',mode='one');self.assertEqual([p['pageId'] for p,_ in self.w.preview.display_pages()],[self.right])
        self.call('page.add',width=700,height=500);last=self.s.current_page()['pageId']
        self.call('view.pages',mode='two');self.assertEqual([p['pageId'] for p,_ in self.w.preview.display_pages()],[last])
        self.assertEqual(self.w.preview.display_pages()[0][1].x(),0)

    def test_pan_stays_put_and_page_exports_and_saved_content_are_independent_of_mode(self):
        first,_=pages.render(self.s,page_id=self.left,mode='mono',dpi=72)
        original=deepcopy(self.s.capture()['pages']);self.call('view.pages',mode='two')
        self.w.preview.pan_by(41,23);nav=self.w.preview.navigation_state();self.w.preview.update_page()
        self.assertEqual(self.w.preview.navigation_state(),nav)
        second,_=pages.render(self.s,page_id=self.left,mode='mono',dpi=72);self.assertEqual(first,second)
        path=self.root/'spread.vay.json';self.call('document.save-as',path=str(path));self.s.open(path)
        self.assertEqual(self.s.capture()['pages'],original)
        result=self.api.call('view.pages',dict(mode='invalid'),expected_revision=self.s.revision,idempotency_key=uuid.uuid4().hex)
        self.assertFalse(result['ok']);self.assertEqual(self.w.preview.page_mode,'two')

    @unittest.skipUnless((ROOT/'.local/baselines/visual.left-page.2026-10-24/approved.vay.json').exists(),'Private approved left page absent')
    def test_approved_left_page_remains_pixel_and_geometry_identical(self):
        from tools.approved_baseline import verify
        result=verify(ROOT,self.root/'approved-left','data/formatting/approved-left-page-20261024.json')
        self.assertTrue(result['rgbaIdentical']);self.assertTrue(result['geometryIdentical'])


if __name__=='__main__':unittest.main()
