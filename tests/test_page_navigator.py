"""Exercise real controls, view-only turns, guard clocks and the saved play."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import unittest
import uuid
from PySide6.QtCore import Qt, QCoreApplication, QEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from vayrshemon.file_api import FileSession, FileAPI
from vayrshemon.file_window import FileWindow
from vayrshemon import pages

ROOT = Path(__file__).resolve().parents[1]
PLAY = ROOT / 'Saves/Alls Well That Ends Well/Alls Well That Ends Well - Act 1 - Part 01.vay'
APP = QApplication.instance() or QApplication([])


class PageNavigatorTests(unittest.TestCase):
    def setUp(self):
        self.root = ROOT / '.local/test-page-navigator' / uuid.uuid4().hex
        shutil.copytree(ROOT / 'schemas', self.root / 'schemas')
        (self.root / 'data').mkdir()
        shutil.copy2(ROOT / 'data/fonts.json', self.root / 'data/fonts.json')
        self.book = FileSession(self.root, source_fonts=False, recovery=False)
        self.api = FileAPI(self.book)
        # Navigation fixtures deliberately use only system fonts.
        self.call('page.numbering.configure', enabled=False)
        self.window = None

    def call(self, method, **params):
        result = self.api.call(method, params, expected_revision=self.book.revision,
                               idempotency_key=uuid.uuid4().hex)
        self.assertTrue(result['ok'], result)
        return result['result']

    def open_window(self, play=False):
        if play:
            self.book.open(PLAY, advance_revision=False)
        else:
            for i in range(4):
                self.call('page.add', width=480 + i * 20, height=700 + i * 60)
            self.call('frame.select', frame_id=self.book.state['pages'][0]['frames'][0]['frameId'])
            self.book.save(self.root / 'navigation.vay', preview_mode='one')
        self.window = FileWindow(self.book, self.api)
        self.window.resize(1500, 960)
        self.window.show()
        APP.processEvents()
        self.nav = self.window.page_navigator
        return self.window

    def tearDown(self):
        if self.window:
            self.window.timer.stop()
            self.window.job_timer.stop()
            self.window.forge_panel.timer.stop()
            self.window.sidebar_dock.save_timer.stop()
            self.window.hide()
            self.book.window = None
            self.window.deleteLater()
        self.book.finish()
        for frame in self.book.frames.values(): frame.deleteLater()
        self.book.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        APP.processEvents()

    def enter(self, text):
        self.nav.number.setFocus()
        self.nav.number.selectAll()
        QTest.keyClicks(self.nav.number, str(text))
        QTest.keyClick(self.nav.number, Qt.Key.Key_Return)
        APP.processEvents()

    def assert_page(self, number, visible, previous, following):
        value = self.call('view.inspect')
        self.assertEqual(value['pageNumber'], number)
        self.assertEqual(value['visiblePageNumbers'], visible)
        self.assertEqual(self.nav.number.text(), str(number))
        self.assertEqual(self.nav.previous.isEnabled(), previous)
        self.assertEqual(self.nav.next.isEnabled(), following)

    def snapshot(self):
        return (self.book.content_digest(self.book.capture()), deepcopy(self.book._undo),
                deepcopy(self.book._redo), deepcopy(self.book.history), self.book.dirty)

    def test_control_order_single_turns_last_page_and_invalid_entry(self):
        w = self.open_window()
        row = w.zoom_row
        self.assertLess(row.indexOf(w.zoom), row.indexOf(w.page_controls.buttons['one']))
        self.assertLess(row.indexOf(w.page_controls.buttons['one']), row.indexOf(w.page_controls.buttons['two']))
        self.assertLess(row.indexOf(w.page_controls.buttons['two']), row.indexOf(self.nav.bar))
        items = [self.nav.bar.layout().itemAt(i).widget() for i in range(5)]
        self.assertEqual([items[i] for i in (0, 2, 4)], [self.nav.previous, self.nav.number, self.nav.next])
        before = self.snapshot()
        self.assertFalse(self.book.dirty)
        self.assert_page(1, [1], False, True)
        QTest.mouseClick(self.nav.next, Qt.MouseButton.LeftButton)
        self.assert_page(2, [2], True, True)
        self.enter(5)
        self.assert_page(5, [5], True, False)
        for text in ('0', '6', '-1', '1.5', 'abc', ''):
            self.enter(text)
            self.assert_page(5, [5], True, False)
            self.assertIn('1 to 5', w.statusBar().currentMessage())
        QTest.mouseClick(self.nav.previous, Qt.MouseButton.LeftButton)
        self.assert_page(4, [4], True, True)
        self.assertEqual(self.snapshot(), before)

    def test_pairs_right_target_boundary_odd_tail_and_mode_switch(self):
        self.open_window()
        before = self.snapshot()
        self.call('view.pages', mode='two')
        self.enter(2)
        self.assert_page(2, [1, 2], False, True)
        self.call('view.page', direction='previous')
        self.assert_page(2, [1, 2], False, True)
        QTest.mouseClick(self.nav.next, Qt.MouseButton.LeftButton)
        self.assert_page(3, [3, 4], True, True)
        self.enter(4)
        self.call('view.pages', mode='one')
        self.assert_page(4, [4], True, True)
        self.call('view.pages', mode='two')
        self.assert_page(4, [3, 4], True, True)
        QTest.mouseClick(self.nav.next, Qt.MouseButton.LeftButton)
        self.assert_page(5, [5], True, False)
        QTest.mouseClick(self.nav.previous, Qt.MouseButton.LeftButton)
        self.assert_page(3, [3, 4], True, True)
        self.enter(4)
        QTest.mouseClick(self.nav.previous, Qt.MouseButton.LeftButton)
        self.assert_page(1, [1, 2], False, True)
        self.assertEqual(self.snapshot(), before)

    def test_fit_and_manual_zoom_survive_differently_sized_page_turns_without_edits(self):
        w = self.open_window()
        for mode in ('one', 'two'):
            self.call('view.pages', mode=mode)
            for fit in ('height', 'width'):
                self.call('ui.workspace', **{'fit_' + fit: True})
                before = self.snapshot()
                for number in (5, 2, 3, 1):
                    self.call('view.page', page=number)
                    value = self.call('view.inspect')
                    self.assertEqual(value['fitMode'], fit)
                    self.assertEqual(value['zoom'], w.fitted_zoom(fit_height=fit == 'height'))
                    self.assertEqual(w.zoom.value(), round(value['zoom'] * 100))
                    if fit == 'width': self.assertEqual(value['pageOrigin'][1], w.preview.RULER)
                self.assertEqual(self.snapshot(), before)
        self.call('view.configure', zoom=.67)
        before = self.snapshot()
        self.call('view.page', page=5)
        self.call('view.pages', mode='one')
        self.assertIsNone(w.preview.fit_mode)
        self.assertEqual(self.call('view.inspect')['zoom'], .67)
        self.assertEqual(self.snapshot(), before)

    def test_structure_changes_selection_and_new_document_refresh_the_count(self):
        self.open_window()
        self.call('view.page', page=5)
        self.call('page.delete', page_id=self.book.current_page()['pageId'])
        self.window.refresh()
        self.assertEqual(self.nav.total.text(), 'of 4')
        self.call('history.undo')
        self.window.refresh()
        self.assert_page(5, [5], True, False)
        self.call('frame.select', frame_id=self.book.state['pages'][2]['frames'][0]['frameId'])
        self.assert_page(3, [3], True, True)
        self.enter(4)
        self.nav.number.setText('2')
        QTest.keyClick(self.nav.number, Qt.Key.Key_Escape)
        self.assert_page(4, [4], True, True)
        self.call('document.new', discardUnsaved=True)
        self.window.refresh()
        self.assert_page(1, [1], False, False)
        self.assertEqual(self.nav.total.text(), 'of 1')

    def test_navigation_invalidates_stale_edits_and_rejects_bad_api_arguments(self):
        self.open_window()
        old_revision = self.book.revision
        self.call('view.page', page=2)
        result = self.api.call('document.edit', dict(start=0, end=0, text='stale'),
                               expected_revision=old_revision, idempotency_key=uuid.uuid4().hex)
        self.assertFalse(result['ok'])
        self.assertIn('STALE_REVISION', result['error']['message'])
        for params in ({}, {'page': 0}, {'page': 6}, {'page': 1.5}, {'page': 1, 'direction': 'next'}):
            result = self.api.call('view.page', params, expected_revision=self.book.revision,
                                   idempotency_key=uuid.uuid4().hex)
            self.assertFalse(result['ok'], result)
        self.assert_page(2, [2], True, True)

    @unittest.skipUnless(PLAY.exists(), 'Private translated play absent')
    def test_real_play_every_page_and_pair_preserves_content_maxima_and_pixels(self):
        file_hash = hashlib.sha256(PLAY.read_bytes()).hexdigest()
        w = self.open_window(play=True)
        self.call('view.pages', mode='one')
        self.call('ui.workspace', fit_height=True)
        before = self.snapshot()
        original = self.book.capture()
        count = len(original['pages'])
        first = original['pages'][0]['pageId']
        image_before, _ = pages.render(self.book, page_id=first, mode='mono', dpi=72)
        seen = []
        self.call('view.page', page=1)
        for number in range(1, count + 1):
            self.assert_page(number, [number], number > 1, number < count)
            seen.append(number)
            if number < count: QTest.mouseClick(self.nav.next, Qt.MouseButton.LeftButton)
        self.call('view.pages', mode='two')
        self.enter(6)
        self.assert_page(6, [5, 6], True, True)
        QTest.mouseClick(self.nav.next, Qt.MouseButton.LeftButton)
        self.assert_page(7, [7, 8], True, True)
        self.call('view.page', page=1)
        pairs = []
        for number in range(1, count + 1, 2):
            visible = list(range(number, min(number + 1, count) + 1))
            self.assert_page(number, visible, number > 1, number + 1 < count)
            pairs.append(visible)
            if number + 1 < count: QTest.mouseClick(self.nav.next, Qt.MouseButton.LeftButton)
        self.assertEqual(self.book.capture()['pages'], original['pages'])
        self.assertEqual(self.snapshot(), before)
        image_after, _ = pages.render(self.book, page_id=first, mode='mono', dpi=72)
        self.assertEqual(image_before, image_after)
        self.assertEqual(hashlib.sha256(PLAY.read_bytes()).hexdigest(), file_hash)
        self.enter(6)
        self.call('ui.workspace', fit_width=True)
        APP.processEvents()
        w.grab().save(str(self.root / 'play-page-6.png'))
        (self.root / 'play-verification.json').write_text(json.dumps(dict(
            file=str(PLAY), fileSha256=file_hash, pages=count, singlePages=seen, pairs=pairs,
            documentContentIdentical=True, firstPagePixelsIdentical=True,
            nativeFileUnchanged=True, screenshot=str(self.root / 'play-page-6.png')), indent=2), encoding='utf-8')


if __name__ == '__main__': unittest.main()
