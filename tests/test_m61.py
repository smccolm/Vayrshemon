"""M6.1 actual Qt panel interactions and document-independent preferences."""
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
if os.name != 'nt': os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import QCoreApplication, QEvent, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from vayrshemon.reliability_session import ReliabilitySession
from vayrshemon.reliability_api import ReliabilityAPI
from vayrshemon.reliability_window import ReliabilityWindow
from vayrshemon import pages

ROOT = Path(__file__).resolve().parents[1]
APP = QApplication.instance() or QApplication([])


class SidebarTests(unittest.TestCase):
    def setUp(self):
        self.work = ROOT/'.local/test-m61'/uuid.uuid4().hex
        self.work.mkdir(parents=True)
        shutil.copytree(ROOT/'schemas', self.work/'schemas')
        (self.work/'data').mkdir()
        shutil.copy2(ROOT/'data/fonts.json', self.work/'data/fonts.json')
        self.s = ReliabilitySession(self.work, source_fonts=False, recovery=False)
        self.api = ReliabilityAPI(self.s)
        self.w = None
        self.call('document.edit', start=0, end=0, text='Panel regression specimen')

    def close_window(self):
        if self.w:
            self.w.hide()
            self.w.job_timer.stop()
            self.w.deleteLater()
            self.s.window = None
            self.w = None
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            APP.processEvents()

    def tearDown(self):
        self.close_window()
        self.s.finish()
        for frame in self.s.frames.values(): frame.deleteLater()
        self.s.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        APP.processEvents()

    def call(self, method, **params):
        value = self.api.call(method, params, expected_revision=self.s.revision,
                             document_id=self.s.state['documentId'],
                             idempotency_key=uuid.uuid4().hex, origin='mcp')
        self.assertTrue(value['ok'], value)
        return value['result']

    def open_window(self):
        self.w = ReliabilityWindow(self.s, self.api)
        self.w.show()
        self.w.activateWindow()
        APP.processEvents()
        return self.w.sidebar_dock

    def click_page(self):
        self.call('view.tool', tool='hand')
        vp = self.w.preview.viewport()
        QTest.mouseClick(vp, Qt.MouseButton.LeftButton, pos=vp.rect().center())
        APP.processEvents()

    def test_real_buttons_pin_temporary_dismissal_and_reopen_preserve_document(self):
        dock = self.open_window()
        self.call('ui.workspace', source=False, diagnostics=False, fit_page=True)
        self.call('document.save-as', path=str(self.work/'original.vay.json'))
        before = self.s.capture()
        undo = len(self.s._undo)
        geometry = pages.inspect(self.s)['geometryHash']
        self.assertEqual(dock.inspect()['state'], 'pinned')
        QTest.mouseClick(dock.toggle_button, Qt.MouseButton.LeftButton)
        APP.processEvents()
        self.assertEqual(dock.inspect()['state'], 'collapsed')
        self.assertEqual(dock.width(), dock.RAIL)
        self.assertTrue(dock.toggle_button.isVisible())
        self.assertEqual(dock.toggle_button.accessibleName(), 'Expand controls')
        QTest.mouseClick(dock.toggle_button, Qt.MouseButton.LeftButton)
        APP.processEvents()
        self.assertEqual(dock.inspect()['state'], 'temporary')
        self.click_page()
        self.assertEqual(dock.inspect()['state'], 'collapsed')
        QTest.mouseClick(dock.toggle_button, Qt.MouseButton.LeftButton)
        QTest.mouseClick(dock.pin_button, Qt.MouseButton.LeftButton)
        self.click_page()
        self.assertEqual(dock.inspect()['state'], 'pinned')
        self.assertTrue(dock.pin_button.isChecked())
        self.assertEqual(before, self.s.capture())
        self.assertEqual(undo, len(self.s._undo))
        self.assertFalse(self.s.dirty)
        self.assertEqual(geometry, pages.inspect(self.s)['geometryHash'])

    def test_preferences_restart_selected_tab_width_and_workspace_reveal(self):
        dock = self.open_window()
        self.call('ui.workspace', panel='Paint')
        self.call('ui.sidebar', width=475, pinned=True)
        APP.processEvents()
        self.assertEqual(dock.width(), 475)
        self.call('ui.sidebar', expanded=False)
        before = self.s.capture()
        self.close_window()
        dock = self.open_window()
        self.assertEqual(dock.inspect()['state'], 'collapsed')
        self.assertEqual(dock.expanded_width, 475)
        self.assertEqual(self.w.sidebar.tabText(self.w.sidebar.currentIndex()), 'Paint')
        self.call('ui.workspace', panel='Reliability')
        APP.processEvents()
        self.assertEqual(dock.inspect()['state'], 'temporary')
        self.assertEqual(dock.width(), 475)
        self.call('ui.sidebar', pinned=True)
        self.close_window()
        dock = self.open_window()
        self.assertEqual(dock.inspect()['state'], 'pinned')
        self.assertEqual(dock.inspect()['panel'], 'Reliability')
        self.assertEqual(before, self.s.capture())

    def test_keyboard_and_popup_interactions(self):
        dock = self.open_window()
        QTest.keyClick(self.w, Qt.Key.Key_B, Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier)
        APP.processEvents()
        self.assertFalse(dock.expanded)
        QTest.keyClick(self.w, Qt.Key.Key_B, Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier)
        APP.processEvents()
        self.assertTrue(dock.expanded)
        self.call('ui.workspace', panel='Publish')
        self.w.paper.showPopup()
        APP.processEvents()
        QTest.keyClick(self.w.paper.view(), Qt.Key.Key_Down)
        QTest.keyClick(self.w.paper.view(), Qt.Key.Key_Return)
        APP.processEvents()
        self.assertTrue(dock.expanded)
        self.assertFalse(dock.pinned)
        self.call('ui.workspace', panel='Paint')
        field = self.w.paint_controls['rim']
        field.setFocus()
        QTest.keyClicks(field, 'abc')
        self.assertTrue(dock.expanded)
        QTest.keyClick(field, Qt.Key.Key_P, Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier)
        APP.processEvents()
        self.assertTrue(dock.pinned)

    def test_guarded_commands_conflicts_retries_and_headless_error(self):
        no_window = self.api.call('ui.sidebar.inspect')
        self.assertFalse(no_window['ok'])
        self.assertEqual(no_window['error']['code'], 'DESKTOP_REQUIRED')
        dock = self.open_window()
        before = self.s.capture()
        args = dict(expected_revision=self.s.revision, document_id=self.s.state['documentId'],
                    idempotency_key=uuid.uuid4().hex, origin='mcp')
        first = self.api.call('ui.sidebar', dict(expanded=False), **args)
        self.assertTrue(first['ok'])
        self.call('ui.sidebar', pinned=True)
        self.assertEqual(first, self.api.call('ui.sidebar', dict(expanded=False), **args))
        self.assertTrue(dock.pinned)  # Retry returns the old result, never reapplies.
        args['idempotency_key'] = uuid.uuid4().hex
        invalid = self.api.call('ui.sidebar', dict(expanded=False, pinned=True, width=510), **args)
        self.assertFalse(invalid['ok'])
        self.assertNotEqual(dock.expanded_width, 510)
        args['expected_revision'] -= 1
        stale = self.api.call('ui.sidebar', dict(expanded=False), **args)
        self.assertFalse(stale['ok'])
        self.assertTrue(dock.pinned)
        self.assertEqual(before, self.s.capture())

    def test_current_version_remote_client_reaches_desktop_panel(self):
        from vayrshemon.api import LocalServer
        dock = self.open_window()
        before = self.s.capture()
        server = LocalServer(self.api, publish=False)
        script = """import json,sys,uuid
from pathlib import Path
from vayrshemon.api import remote_call
root,descriptor=Path(sys.argv[1]),Path(sys.argv[2])
status=remote_call(root,'session.status',descriptor=descriptor)['result']
result=remote_call(root,'ui.sidebar',dict(expanded=False),descriptor=descriptor,
 expected_revision=status['revision'],document_id=status['documentId'],idempotency_key=uuid.uuid4().hex)
print(json.dumps(result))
"""
        process = subprocess.Popen([sys.executable, '-c', script, str(self.work), str(server.descriptor)],
                                   cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.monotonic()+15
            while process.poll() is None and time.monotonic()<deadline:
                APP.processEvents()
                QTest.qWait(10)
            self.assertIsNotNone(process.poll(), 'Remote client timed out')
            output, error = process.communicate(timeout=2)
            self.assertEqual(process.returncode, 0, error)
            response = json.loads(output)
            self.assertTrue(response['ok'], response)
            self.assertEqual(response['apiVersion'], self.api.version)
            self.assertEqual(response['result']['state'], 'collapsed')
            self.assertFalse(dock.expanded)
            self.assertEqual(before, self.s.capture())
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate(timeout=5)
            server.close()

    def test_corrupt_preferences_and_write_failure_are_visible(self):
        path = self.work/'.local/workspace/sidebar.json'
        path.parent.mkdir(parents=True)
        path.write_text('{broken')
        dock = self.open_window()
        self.assertTrue(dock.preference_error)
        self.assertTrue(dock.pinned)
        self.assertEqual(path.read_text(), '{broken')
        before = self.s.capture()
        with patch('vayrshemon.sidebar.write_json', side_effect=OSError('simulated read-only preferences')):
            result = self.call('ui.sidebar', expanded=False)
        self.assertIn('read-only', result['preferenceError'])
        self.assertEqual(before, self.s.capture())
        result = self.call('ui.sidebar', pinned=True)
        self.assertIsNone(result['preferenceError'])
        self.assertTrue(json.loads(path.read_text())['pinned'])

    def test_approved_local_page_matches_recorded_geometry_and_pixels(self):
        from tools.approved_baseline import MANIFEST, verify
        from tools.m0.common import load_json
        manifest = load_json(ROOT/MANIFEST)
        if not (ROOT/manifest['source']['path']).exists() or not (ROOT/manifest['proof']['path']).exists():
            self.skipTest('Private approved document/proof not available; public interaction tests still run')
        result = verify(ROOT, self.work/'approved-baseline')
        self.assertTrue(result['rgbaIdentical'])
        self.assertTrue(result['geometryIdentical'])


if __name__ == '__main__': unittest.main()
