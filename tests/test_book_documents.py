"""Book-sized native files: lazy reading, edits, persistence and real play fidelity."""
from copy import deepcopy
from pathlib import Path
import json
import shutil
import unittest
import uuid
from time import perf_counter
from unittest.mock import patch
from jsonschema import ValidationError
from PySide6.QtCore import QCoreApplication, QEvent, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from tools.m0.common import load_json, write_json
from tools.combine_volumes import verify_pages
from vayrshemon.authoring import identity
from vayrshemon.book_frames import BookFrames, loaded_values
from vayrshemon.file_api import FileSession, FileAPI
from vayrshemon.file_window import FileWindow
from vayrshemon import pages

ROOT = Path(__file__).resolve().parents[1]
PLAY = ROOT / 'Saves/Alls Well That Ends Well/Alls Well That Ends Well.vay'
APP = QApplication.instance() or QApplication([])


class BookDocumentTests(unittest.TestCase):
    def setUp(self):
        self.root = ROOT / '.local/test-books' / uuid.uuid4().hex
        shutil.copytree(ROOT / 'schemas', self.root / 'schemas')
        (self.root / 'data').mkdir()
        shutil.copy2(ROOT / 'data/fonts.json', self.root / 'data/fonts.json')
        self.book = FileSession(self.root, source_fonts=False, recovery=False)
        self.api = FileAPI(self.book)
        # This fixture isolates large-book storage without decorative fonts.
        self.call('page.numbering.configure', enabled=False)
        self.window = None

    def tearDown(self):
        if self.window:
            for timer in (self.window.timer, self.window.job_timer, self.window.forge_panel.timer, self.window.sidebar_dock.save_timer): timer.stop()
            self.window.hide(); self.book.window = None; self.window.deleteLater()
        self.book.finish()
        for runtime in loaded_values(self.book.frames): runtime.deleteLater()
        self.book.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        APP.processEvents()

    def call(self, method, **params):
        value = self.api.call(method, params, expected_revision=self.book.revision, idempotency_key=uuid.uuid4().hex)
        self.assertTrue(value['ok'], value)
        return value['result']

    def synthetic_book(self):
        # Structural test data, not proposed language text.
        self.call('document.edit', start=0, end=0, text='Book persistence test. A\u0301')
        state = self.book.capture()
        page = state['pages'][0]
        for i in range(104):
            copy = deepcopy(page); copy['pageId'] = identity('page'); copy['frames'][0]['frameId'] = identity('frame')
            state['pages'].append(copy)
        self.book._restore(state)
        self.book._state = self.book.capture()
        self.book.save(self.root / 'book.vay')
        self.assertIsInstance(self.book.frames, BookFrames)

    def test_lazy_navigation_edits_eviction_undo_save_and_recovery(self):
        self.synthetic_book()
        self.assertLessEqual(len(self.book.frames.loaded), 2)
        info = self.call('performance.inspect')
        self.assertTrue(info['lazyFrameEditors'])
        self.assertEqual(info['maxPages'], 32768)
        loaded = set(self.book.frames.loaded)
        self.assertEqual(self.call('document.find', text='A', case_sensitive=True)['count'], 0)
        self.assertEqual(self.call('document.find', text='A\u0301', case_sensitive=True)['count'], 105)
        self.assertEqual(set(self.book.frames.loaded), loaded)
        self.book.recovery_enabled = True
        self.book.checkpoint()
        original = self.book.content_digest(self.book.capture())
        checkpoint_bytes = self.book.recovery_path.read_bytes()
        with patch.object(self.book, 'capture', side_effect=AssertionError('Navigation copied complete book')):
            for page in self.book.state['pages']:
                self.call('frame.select', frame_id=page['frames'][0]['frameId'])
                self.book.active.text()
                self.book.frames.trim()
                self.assertFalse(self.book.dirty)
                self.assertLessEqual(len(self.book.frames.loaded), 16)
        self.assertEqual(self.book.recovery_path.read_bytes(), checkpoint_bytes)
        self.assertEqual(self.book.content_digest(self.book.capture()), original)
        end_id = self.book.state['activeFrameId']
        self.call('document.edit', start=0, end=0, text='Changed. ')
        self.assertTrue(self.book.dirty)
        for page in self.book.state['pages'][:20]:
            self.call('frame.select', frame_id=page['frames'][0]['frameId'])
            self.book.active.text()
            self.book.frames.trim()
        self.assertNotIn(end_id, self.book.frames.loaded)
        loaded = set(self.book.frames.loaded)
        found = self.call('document.find', text='Changed', whole_word=True)
        self.assertEqual(found['count'], 1)
        self.assertEqual(found['matches'][0]['frameId'], end_id)
        self.assertEqual(set(self.book.frames.loaded), loaded)
        self.assertTrue(self.book.frames[end_id].text().startswith('Changed. '))
        self.call('history.undo')
        self.assertFalse(self.book.dirty)
        self.call('history.redo')
        self.assertTrue(self.book.dirty)
        self.assertTrue(self.book.frames[end_id].text().startswith('Changed. '))
        recovered = FileSession(self.root, source_fonts=False, recovery=False)
        try:
            recovered.recover(self.book.recovery_path)
            self.assertEqual(recovered.frames[end_id].text(), self.book.frames[end_id].text())
            self.assertEqual(len(recovered.state['pages']), 105)
        finally:
            recovered.finish()
            for runtime in loaded_values(recovered.frames): runtime.deleteLater()
        self.book.save(self.root / 'book.vay')
        self.assertFalse(self.book.dirty)
        self.book.open(self.root / 'book.vay')
        self.assertTrue(self.book.frames[end_id].text().startswith('Changed. '))
        self.assertEqual(len(self.book.state['pages']), 105)

    def test_open_reuses_preflight_and_one_recovery_snapshot(self):
        self.synthetic_book()
        path=self.root/'book.vay'
        self.book.recovery_enabled=True
        with patch('vayrshemon.file_api.load_json',wraps=load_json) as reads, \
             patch.object(self.book,'capture',wraps=self.book.capture) as captures:
            with self.book.reuse_open_preflight():
                self.book.preflight(path)
                self.book.open(path,advance_revision=False)
            self.assertEqual(reads.call_count,1)
            self.assertEqual(captures.call_count,1)
        self.assertIsNone(self.book._prepared_open)
        self.assertFalse(self.book.dirty)
        self.assertEqual(load_json(self.book.recovery_path)['state'],self.book.capture())
        # History is independent of the mutable live state after adoption.
        self.book.state['pages'][-1]['name']='changed only in live state'
        self.assertNotEqual(self.book._state['pages'][-1]['name'],self.book.state['pages'][-1]['name'])

    def test_preflight_cache_rejects_changed_file_and_clears_on_failure(self):
        self.synthetic_book()
        path=self.root/'book.vay'
        before=self.book.capture()
        with self.assertRaises(ValidationError):
            with self.book.reuse_open_preflight():
                self.book.preflight(path)
                path.write_text('{"corrupted":true}',encoding='utf-8')
                self.book.open(path)
        self.assertIsNone(self.book._prepared_open)
        self.assertEqual(before,self.book.capture())

    def test_large_compressed_book_exceeds_previous_limits_and_roundtrips(self):
        # More than 2,048 pages, 4,096 frames and two million scalars.
        # These repetitions are storage fixtures, never translated language.
        text = 'Structural test. ' * 32
        self.call('document.edit', start=0, end=0, text=text)
        state = self.book.capture()
        template = state['pages'][0]
        state['pages'] = []
        for index in range(2052):
            page = deepcopy(template)
            page['pageId'] = identity('page')
            page['frames'].append(deepcopy(page['frames'][0]))
            for frame in page['frames']:
                frame['frameId'] = identity('frame')
            state['pages'].append(page)
        state['activeFrameId'] = state['pages'][0]['frames'][0]['frameId']
        self.book._restore(state)
        self.book._state = self.book.capture()
        self.assertGreater(self.book.text_scalar_count(), 2_000_000)
        path = self.root / 'large.vay'
        self.book.save(path)
        wire = json.loads(path.read_text())
        self.assertEqual(wire['formatVersion'], '0.7.0')
        self.assertEqual(next(iter(wire)), 'shellPreview')
        self.assertNotIn('state', wire)
        saved = self.book.capture()
        self.book.open(path, advance_revision=False)
        self.assertEqual(self.book.capture(), saved)
        self.assertLessEqual(len(self.book.frames.loaded), 4)
        final = self.book.state['pages'][-1]['frames'][-1]['frameId']
        self.call('frame.select', frame_id=final)
        self.assertEqual(self.book.active.text(), text)
        self.book.recovery_enabled = True
        self.call('document.edit', start=0, end=0, text='Edited. ')
        self.assertTrue(self.book.dirty)
        self.call('history.undo')
        self.assertEqual(self.book.active.text(), text)
        self.call('history.redo')
        self.assertTrue(self.book.active.text().startswith('Edited. '))
        checkpoint = json.loads(self.book.recovery_path.read_text())
        self.assertEqual(checkpoint['recoveryVersion'], '0.2.0')
        self.assertEqual(load_json(self.book.recovery_path)['state'], self.book.capture())
        self.book.save(path)
        self.assertFalse(self.book.dirty)
        # Exact prior wire file is retained, still directly readable.
        prior = list((self.root / '.local/history' / state['documentId']).glob('*.vay.json'))
        self.assertEqual(len(prior), 1)
        self.assertEqual(load_json(prior[0])['state'], saved)

    @unittest.skipUnless(PLAY.exists(), 'Private translated play is intentionally not in Git')
    def test_complete_play_original_pages_boundary_navigation_and_rendering(self):
        report = load_json(PLAY.with_suffix('.verification.json'))
        started = perf_counter()
        self.book.open(PLAY, advance_revision=False)
        opening = perf_counter()-started
        self.assertEqual(len(self.book.state['pages']), 674)
        self.assertEqual(verify_pages(self.book.capture(), report['sourceFiles']), 674)
        self.assertLessEqual(len(self.book.frames.loaded), 4)
        original = self.book.content_digest(self.book.capture())
        self.window = FileWindow(self.book, self.api)
        self.window.resize(1500, 960); self.window.show(); APP.processEvents()
        self.window.page_controls.set_mode('two', persist=False)
        measurements = []
        for number in (32, 33, 138, 139, 306, 307, 422, 423, 570, 571, 674):
            started = perf_counter()
            self.call('view.page', page=number); APP.processEvents()
            self.assertEqual(self.call('view.inspect')['pageNumber'], number)
            self.assertEqual(self.call('view.inspect')['visiblePageNumbers'], [((number-1)//2)*2+1, ((number-1)//2)*2+2])
            self.assertFalse(self.book.dirty)
            measurements.append(dict(page=number, seconds=perf_counter()-started))
        self.assertFalse(self.window.page_navigator.next.isEnabled())
        self.call('view.page', page=32)
        self.call('view.page', direction='next')
        self.assertEqual(self.call('view.inspect')['pageNumber'], 33)
        self.call('view.page', direction='previous')
        self.assertEqual(self.call('view.inspect')['pageNumber'], 31)
        self.window.page_controls.set_mode('one', persist=False)
        self.call('view.page', page=674)
        self.assertEqual(self.call('view.inspect')['visiblePageNumbers'], [674])
        self.assertFalse(self.window.page_navigator.next.isEnabled())
        # Exact raster comparison against the original volumes at each act and the end.
        pixel_checks = []
        for number in (1, 139, 307, 423, 571, 674):
            source = next(s for s in report['sourceFiles'] if s['firstPage'] <= number <= s['lastPage'])
            reference = FileSession(self.root, source_fonts=False, recovery=False)
            try:
                reference.open(source['path'], advance_revision=False)
                pid = self.book.state['pages'][number-1]['pageId']
                actual, _ = pages.render(self.book, page_id=pid, dpi=58, mode=self.book.view['mode'])
                expected, _ = pages.render(reference, page_id=pid, dpi=58, mode=reference.view['mode'])
                self.assertEqual(actual, expected)
                actual.save(str(self.root / f'page-{number}.png'))
                pixel_checks.append(number)
            finally:
                reference.finish()
                for runtime in loaded_values(reference.frames): runtime.deleteLater()
        self.assertEqual(self.book.content_digest(self.book.capture()), original)
        self.assertLessEqual(len(self.book.frames.loaded), 16)
        write_json(self.root / 'play-verification.json', dict(pages=674, openingSeconds=opening, turns=measurements,
                   pixelIdenticalPages=pixel_checks, exactPageComparison=True, cachedFrames=len(self.book.frames.loaded)))
