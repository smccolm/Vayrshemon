"""Close releases a document, not the application, and never bypasses saving."""
import json
import shutil
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import QCoreApplication, QEvent, Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMessageBox

from vayrshemon.file_api import FileAPI, FileSession
from vayrshemon.file_window import FileWindow

ROOT = Path(__file__).resolve().parents[1]
APP = QApplication.instance() or QApplication([])
BUTTON = QMessageBox.StandardButton


class CloseDocumentTests(unittest.TestCase):
    def setUp(self):
        self.root = ROOT / '.local/test-close-document' / uuid.uuid4().hex
        shutil.copytree(ROOT / 'schemas', self.root / 'schemas')
        (self.root / 'data').mkdir()
        shutil.copy2(ROOT / 'data/fonts.json', self.root / 'data/fonts.json')
        shutil.copytree(ROOT / 'data/runtime-fonts', self.root / 'data/runtime-fonts')
        self.book = FileSession(self.root, source_fonts=False, recovery=False)
        self.api = FileAPI(self.book)
        self.window = FileWindow(self.book, self.api)
        self.window.showMaximized()
        self.window.activateWindow()
        APP.processEvents()
        QTest.qWait(150)
        self.session_id = self.book.session_id

    def tearDown(self):
        # Do not invoke the unrelated application-exit prompt during cleanup.
        self.window.hide()
        for timer in (self.window.timer, self.window._startup_fit,
                      self.window.job_timer, self.window.forge_panel.timer):
            timer.stop()
        self.book.finish()
        self.book.window = None
        self.window.deleteLater()
        for frame in self.book.frames.values():
            frame.deleteLater()
        self.book.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        APP.processEvents()

    def call(self, method, **params):
        result = self.api.call(method, params, expected_revision=self.book.revision,
                               idempotency_key=uuid.uuid4().hex)
        self.assertTrue(result['ok'], result)
        return result['result']

    def save_example(self):
        self.call('document.edit', start=0, end=0, text='Saved text')
        path = self.root / 'Saves/example.vay'
        self.call('document.save-as', path=str(path))
        return path

    def assert_closed(self, previous_id):
        QTest.qWait(self.window.timer.interval() + 25)
        for _ in range(20):
            if not self.window._startup_fit_pending:break
            QTest.qWait(25)
        self.assertFalse(self.window._startup_fit_pending)
        self.assertTrue(self.window.isVisible())
        self.assertEqual(self.book.session_id, self.session_id)
        self.assertNotEqual(self.book.state['documentId'], previous_id)
        self.assertIsNone(self.book.saved_path)
        self.assertIsNone(self.book.saved_preview)
        self.assertFalse(self.book.dirty)
        self.assertEqual(self.book.text(), '')
        self.assertFalse(self.book._undo)
        self.assertFalse(self.book._redo)
        self.assertEqual(len(self.book.state['pages']), 1)
        self.assertEqual(self.window.windowTitle(), 'Untitled')
        self.assertEqual(self.window.windowFilePath(), '')
        self.assertEqual(self.window.preview.page_mode, 'one')
        self.assertEqual(self.window.preview.fit_mode, 'height')
        self.assertEqual(self.window.preview.zoom, self.window.fitted_zoom(fit_height=True))
        self.assertEqual(self.book.view['zoom'], self.window.preview.zoom)
        self.assertEqual(self.window.mode.currentData(), 'mono-white')
        self.assertEqual(self.window.page_navigator.number.text(), '1')
        self.assertFalse(self.window.page_navigator.next.isEnabled())

    def test_close_refits_and_recenters_a_zoomed_panned_spread(self):
        self.call('page.add', width=612, height=792)
        self.window.page_controls.set_mode('two')
        self.call('view.configure', zoom=2)
        self.window.preview.pan_by(dx=370, dy=-240)
        previous_id = self.book.state['documentId']
        revision = self.book.revision
        with patch.object(QMessageBox, 'question', return_value=BUTTON.Discard):
            self.window.close_document_action.trigger()
        self.assert_closed(previous_id)
        self.assertEqual(self.book.revision, revision + 1)
        canvas = self.window.preview
        area = canvas.display_rect()
        viewport = canvas.viewport()
        self.assertLessEqual(area.height() * canvas.zoom, viewport.height() - 55)
        self.assertEqual(canvas.verticalScrollBar().value(),
                         round((area.height() * canvas.zoom - viewport.height() + canvas.RULER) / 2))
        self.assertEqual(canvas.horizontalScrollBar().value(),
                         round((area.width() * canvas.zoom - viewport.width() + canvas.RULER) / 2))
        before = self.book.capture()
        self.window.showNormal()
        self.window.resize(1400, 760)
        QTest.qWait(self.window.timer.interval() + 25)
        self.assertEqual(canvas.zoom, self.window.fitted_zoom(fit_height=True))
        self.assertLessEqual(area.height() * canvas.zoom, viewport.height() - 55)
        self.assertEqual(self.book.capture(), before)
        self.assertFalse(self.book.dirty)

    def test_menu_closes_unchanged_blank_and_opened_files_without_prompt(self):
        action = self.window.close_document_action
        actions = self.window.file_menu.actions()
        self.assertIn(action, actions)
        self.assertEqual(action.text(), 'Close')
        self.assertEqual(action.shortcut(), QKeySequence('Ctrl+W'))
        self.assertEqual(actions.index(action) + 1, actions.index(self.window.recents.menuAction()))
        for saved in (False, True):
            with self.subTest(saved=saved):
                if saved:
                    path = self.save_example()
                    self.book.open(path)
                    original = path.read_bytes()
                    self.window.page_controls.set_mode('two')
                previous_id = self.book.state['documentId']
                with patch.object(QMessageBox, 'question') as prompt, patch.object(self.book, 'finish') as finish:
                    action.trigger()
                    prompt.assert_not_called()
                    finish.assert_not_called()
                self.assert_closed(previous_id)
                if saved:
                    self.assertEqual(path.read_bytes(), original)

    def test_cancel_then_discard_preserves_saved_file(self):
        path = self.save_example()
        original = path.read_bytes()
        self.window.configure_workspace(source=True)
        self.window.editor.setFocus()
        QTest.keyClicks(self.window.editor, 'Unsaved native typing ')
        self.assertTrue(self.book.dirty)
        before = self.book.capture()
        with patch.object(QMessageBox, 'question', return_value=BUTTON.Cancel) as prompt:
            self.window.close_document_action.trigger()
            prompt.assert_called_once()
        self.assertEqual(self.book.capture(), before)
        self.assertEqual(self.book.saved_path, path)
        self.assertTrue(self.window.isVisible())
        with patch.object(QMessageBox, 'question', return_value=BUTTON.Discard):
            self.window.close_document_action.trigger()
        self.assert_closed(before['documentId'])
        self.assertEqual(path.read_bytes(), original)

    def test_save_commits_latest_document_before_closing(self):
        path = self.save_example()
        self.call('document.edit', start=0, end=0, text='Latest edit. ')
        before = self.book.capture()
        with patch.object(QMessageBox, 'question', return_value=BUTTON.Save) as prompt:
            self.window.close_document_action.trigger()
            prompt.assert_called_once()
        self.assertEqual(json.loads(path.read_text(encoding='utf-8'))['state'], before)
        self.assert_closed(before['documentId'])

    def test_failed_save_keeps_document_open_and_unsaved(self):
        path = self.save_example()
        original = path.read_bytes()
        self.call('document.edit', start=0, end=0, text='Keep this edit. ')
        before = self.book.capture()
        with patch.object(QMessageBox, 'question', return_value=BUTTON.Save), \
                patch('vayrshemon.saved_preview.create', side_effect=OSError('Cannot write preview')):
            self.window.close_document_action.trigger()
        self.assertEqual(self.book.capture(), before)
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual(self.book.saved_path, path)
        self.assertTrue(self.book.dirty)
        self.assertTrue(self.window.isVisible())
        self.assertIn('Cannot write preview', self.window.last_error)

    def test_unsaved_document_cancelled_save_as_then_successful_save_as(self):
        self.call('document.edit', start=0, end=0, text='New unsaved writing')
        before = self.book.capture()
        with patch.object(QMessageBox, 'question', return_value=BUTTON.Save), \
                patch('vayrshemon.file_window.QFileDialog.getSaveFileName', return_value=('', '')):
            self.window.close_document_action.trigger()
        self.assertEqual(self.book.capture(), before)
        self.assertTrue(self.book.dirty)
        self.assertTrue(self.window.isVisible())
        path = self.root / 'Saves/new writing.vay'
        with patch.object(QMessageBox, 'question', return_value=BUTTON.Save), \
                patch('vayrshemon.file_window.QFileDialog.getSaveFileName', return_value=(str(path), '')) as dialog:
            self.window.close_document_action.trigger()
        self.assertEqual(Path(dialog.call_args.args[2]).parent, self.root / 'Saves')
        self.assertEqual(json.loads(path.read_text(encoding='utf-8'))['state'], before)
        self.assert_closed(before['documentId'])

    def test_ctrl_w_from_editor_after_undo_to_saved_state_does_not_prompt(self):
        self.save_example()
        self.call('document.edit', start=0, end=0, text='An edit to undo. ')
        self.call('history.undo')
        self.assertFalse(self.book.dirty)
        previous_id = self.book.state['documentId']
        self.window.configure_workspace(source=True)
        self.window.editor.setFocus()
        APP.processEvents()
        with patch.object(QMessageBox, 'question') as prompt, patch.object(self.book, 'finish') as finish:
            QTest.keyClick(self.window.editor, Qt.Key.Key_W, Qt.KeyboardModifier.ControlModifier)
            prompt.assert_not_called()
            finish.assert_not_called()
        self.assert_closed(previous_id)

    def test_api_requires_explicit_discard_for_dirty_document(self):
        self.call('document.edit', start=0, end=0, text='Keep unless explicitly discarded')
        before = self.book.capture()
        result = self.api.call('document.close', {}, expected_revision=self.book.revision,
                               idempotency_key=uuid.uuid4().hex)
        self.assertFalse(result['ok'])
        self.assertEqual(result['error']['code'], 'UNSAVED_CHANGES')
        self.assertEqual(self.book.capture(), before)
        self.call('document.close', discardUnsaved=True)
        self.assert_closed(before['documentId'])
