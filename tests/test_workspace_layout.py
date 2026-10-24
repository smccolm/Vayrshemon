"""Real window restart and menu/API coverage for reading layout preferences."""
import json
import shutil
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch
from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication
from tools.m0.common import write_json
from vayrshemon.file_api import FileAPI, FileSession
from vayrshemon.file_window import FileWindow

ROOT = Path(__file__).resolve().parents[1]
APP = QApplication.instance() or QApplication([])


class WorkspaceLayoutTests(unittest.TestCase):
    def setUp(self):
        self.root = ROOT / '.local/test-workspace-layout' / uuid.uuid4().hex
        shutil.copytree(ROOT / 'schemas', self.root / 'schemas')
        (self.root / 'data').mkdir()
        shutil.copy2(ROOT / 'data/fonts.json', self.root / 'data/fonts.json')
        self.path = self.root / '.local/workspace/layout.json'
        self.window = self.book = None

    def open_window(self):
        self.book = FileSession(self.root, source_fonts=False, recovery=False)
        self.api = FileAPI(self.book)
        self.before = self.book.capture()
        self.window = FileWindow(self.book, self.api)
        self.window.show()
        APP.processEvents()
        return self.window

    def close_window(self):
        if self.window:
            self.window.job_timer.stop()
            self.window.forge_panel.timer.stop()
            self.window.close()
            self.window.deleteLater()
            self.book.window = None
            self.window = None
        if self.book:
            self.book.finish()
            for frame in self.book.frames.values(): frame.deleteLater()
            self.book.deleteLater()
            self.book = None
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        APP.processEvents()

    def tearDown(self):
        self.close_window()

    def call(self, **params):
        result = self.api.call('ui.workspace', params, expected_revision=self.book.revision, idempotency_key=uuid.uuid4().hex)
        self.assertTrue(result['ok'], result)
        return result['result']

    def assert_unmodified(self):
        self.assertEqual(self.book.capture(), self.before)
        self.assertEqual(self.book.revision, 0)
        self.assertEqual(len(self.book._undo), 0)
        self.assertFalse(self.book.dirty)

    def test_clean_default_and_menu_choice_survives_new_session(self):
        window = self.open_window()
        self.assertTrue(window.inspection.isHidden())
        self.assertTrue(window.editor.parentWidget().isHidden())
        self.assertFalse(window.preview.guides)
        self.assert_unmodified()
        self.assertFalse(self.path.exists())
        window.workspace_layout.actions['diagnostics'].trigger()
        self.assertFalse(window.inspection.isHidden())
        self.assertTrue(json.loads(self.path.read_text())['diagnostics'])
        self.assert_unmodified()
        self.close_window()
        window = self.open_window()
        self.assertFalse(window.inspection.isHidden())
        self.assertTrue(window.workspace_layout.actions['diagnostics'].isChecked())
        self.assertTrue(window.editor.parentWidget().isHidden())
        self.assert_unmodified()

    def test_api_and_editor_close_remember_clean_layout(self):
        window = self.open_window()
        self.call(source=True, diagnostics=True, guides=True)
        self.assertTrue(all(a.isChecked() for a in window.workspace_layout.actions.values()))
        window.close_source_button.click()
        self.assertFalse(window.workspace_layout.actions['source'].isChecked())
        self.call(diagnostics=False, guides=False)
        self.assert_unmodified()
        self.close_window()
        window = self.open_window()
        self.assertFalse(any(window.workspace_state()[k] for k in ('source', 'diagnostics', 'guides')))
        self.assert_unmodified()

    def test_invalid_preferences_fall_back_without_overwriting(self):
        write_json(self.path, dict(version='1.0.0', source=False, diagnostics='false', guides=False))
        original = self.path.read_bytes()
        window = self.open_window()
        self.assertIn('INVALID_WORKSPACE_LAYOUT', window.workspace_layout.error)
        self.assertTrue(window.inspection.isHidden())
        self.assertEqual(self.path.read_bytes(), original)
        self.assert_unmodified()

    def test_write_failure_keeps_visibility_change_and_reports_error(self):
        window = self.open_window()
        with patch('vayrshemon.workspace_layout.write_json', side_effect=OSError('read-only preferences')):
            self.call(diagnostics=True)
        self.assertFalse(window.inspection.isHidden())
        self.assertIn('read-only preferences', window.workspace_layout.error)
        self.assertIn('could not be saved', window.statusBar().currentMessage())
        self.assert_unmodified()
        self.call(diagnostics=False)
        self.assertIsNone(window.workspace_layout.error)
