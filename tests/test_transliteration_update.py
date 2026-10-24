"""In-place Roman refresh, protected typography, one-step history and UI modes."""
from copy import deepcopy
from pathlib import Path
import shutil
import unittest
import uuid
from unittest.mock import patch
from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication, QLabel, QMessageBox, QPushButton
from tools.m0.synthetic import make_font
from vayrshemon.file_api import FileAPI, FileSession
from vayrshemon.file_window import FileWindow
from vayrshemon.paragraph_alignment import without_before
from vayrshemon.session import utf16_length
from vayrshemon import reading, pages

ROOT = Path(__file__).resolve().parents[1]
APP = QApplication.instance() or QApplication([])


class TransliterationUpdateTests(unittest.TestCase):
    def setUp(self):
        self.root = ROOT / '.local/test-transliteration-update' / uuid.uuid4().hex
        shutil.copytree(ROOT / 'schemas', self.root / 'schemas')
        shutil.copytree(ROOT / 'data', self.root / 'data')
        self.book = FileSession(self.root, source_fonts=False, recovery=False)
        self.api = FileAPI(self.book)
        self.window = None
        self.font_patches = []
        for name, advance in (('script', 550), ('roman', 610)):
            make_font(self.root / (name + '.ttf'), advance=advance)
        self.script = self.book.fonts.register(self.root / 'script.ttf')
        self.roman = self.book.fonts.register(self.root / 'roman.ttf')
        for field, value in (('SCRIPT_SHA', self.script.sha256), ('ROMAN_SHA', self.roman.sha256)):
            patcher = patch.object(reading, field, value)
            patcher.start()
            self.font_patches.append(patcher)
            self.addCleanup(patcher.stop)
        self.ids = []
        self.call('page.configure', width=600, height=1000)
        for i, text in enumerate(('A A A\nAA A', 'AA A\nA A', 'Synthetic gloss.\nSecond gloss.', 'Synthetic English.\nSecond English.')):
            if i == 2:
                self.call('page.add', width=600, height=1000)
            elif i in (1, 3):
                self.call('frame.add', x=310, y=40, width=240, height=900)
            self.call('frame.configure', x=40 if i % 2 == 0 else 310, y=40, width=240, height=900)
            self.ids.append(self.book.state['activeFrameId'])
            self.call('document.edit', start=0, end=0, text=text)
            self.call('document.format', start=0, end=utf16_length(text),
                      font_id=self.script.font_id if i == 0 else self.roman.font_id,
                      language='language.vayrshemon', size=50 if i == 0 else 22, color='#135799FF')
            self.call('paragraph.format', start=0, end=utf16_length(text), before=1, after=24,
                      lineHeight=dict(mode='exact', value=38))
            self.call('typesetting.configure', enabled=True, grid=dict(enabled=False, step=12, offset=0))
        self.call('view.configure', mode='mono', monochromePaper='white')
        self.call('page.paragraphs.align')

    def tearDown(self):
        if self.window:
            self.window.job_timer.stop()
            self.window.forge_panel.timer.stop()
            self.window.timer.stop()
            self.window.hide()
            self.book.window = None
            self.book._editor = None
            self.window.deleteLater()
        self.book.finish()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def call(self, method, **params):
        result = self.api.call(method, params, expected_revision=self.book.revision, idempotency_key=uuid.uuid4().hex)
        self.assertTrue(result['ok'], result)
        return result['result']

    def assert_protected(self, before, after):
        for a, b in zip(before['pages'], after['pages']):
            self.assertEqual({k: v for k, v in a.items() if k != 'frames'}, {k: v for k, v in b.items() if k != 'frames'})
            for old, new in zip(a['frames'], b['frames']):
                if old['frameId'] != self.ids[1]:
                    self.assertEqual(without_before(old), without_before(new))
                else:
                    for field in ('x', 'y', 'width', 'height'):
                        self.assertEqual(old[field], new[field])
                    self.assertEqual(old['content']['document']['styles'], new['content']['document']['styles'])
                    for p, q in zip(old['content']['paragraphs'], new['content']['paragraphs']):
                        self.assertEqual({k: v for k, v in p.items() if k != 'before'}, {k: v for k, v in q.items() if k != 'before'})
        for key in ('paint', 'recipe', 'view', 'activeFrameId', 'typesetting', 'fontSources'):
            self.assertEqual(before[key], after[key])

    def test_spread_update_one_undo_redo_noop_and_saved_roundtrip(self):
        before = self.book.capture()
        undo = len(self.book._undo)
        plan = self.call('page.transliteration.inspect')
        self.assertEqual((plan['sourceFrameId'], plan['targetFrameId']), tuple(self.ids[:2]))
        result = self.call('page.transliteration.update', expected_plan=plan['planId'])
        self.assertTrue(result['changed'])
        self.assertEqual(self.book.frames[self.ids[0]].text(), self.book.frames[self.ids[1]].text())
        self.assertEqual(self.book.revision, before['revision'] + 1)
        self.assertEqual(len(self.book._undo), undo + 1)
        after = self.book.capture()
        self.assert_protected(before, after)
        self.assertEqual(self.book.automatic_alignment['status'], 'aligned')
        self.assertFalse(self.call('page.transliteration.update')['changed'])
        self.assertEqual(self.book.capture(), after)
        self.call('history.undo')
        restored = self.book.capture(); restored['revision'] = before['revision']
        self.assertEqual(restored, before)
        self.call('history.redo')
        self.assertEqual(self.book.capture()['pages'], after['pages'])
        path = self.root / 'updated.vay'
        self.call('document.save-as', path=str(path))
        self.book.open(path, advance_revision=False)
        self.assertEqual(self.book.capture()['pages'], after['pages'])

    def test_language_action_both_view_modes_cancel_and_obsolete_ribbon_removed(self):
        self.window = FileWindow(self.book, self.api)
        self.window.showMaximized(); APP.processEvents()
        self.assertNotIn('Create reading copy', [b.text() for b in self.window.findChildren(QPushButton)])
        self.assertNotIn('Reading copy', [l.text() for l in self.window.findChildren(QLabel)])
        self.assertFalse(hasattr(self.window, 'reading_mode'))
        language = self.window.language_menu
        action = next(a for a in language.actions() if a.text() == 'Update transliteration')
        for mode in ('one', 'two'):
            self.call('view.pages', mode=mode)
            before = self.book.capture()
            with patch('vayrshemon.file_window.QMessageBox.question', return_value=QMessageBox.StandardButton.Cancel):
                action.trigger()
            self.assertEqual(self.book.capture(), before)
            with patch('vayrshemon.file_window.QMessageBox.question', return_value=QMessageBox.StandardButton.Yes) as question:
                action.trigger()
            self.assertIn('edits made directly', question.call_args.args[2])
            self.assertEqual(self.book.frames[self.ids[0]].text(), self.book.frames[self.ids[1]].text())
            self.assertEqual(self.window.preview.page_mode, mode)
            self.assertEqual(self.book.state['activeFrameId'], self.ids[3])
            self.call('history.undo')
            self.assertEqual(self.book.capture()['pages'], before['pages'])

    def test_graphemes_case_paragraphs_and_stale_review(self):
        self.call('frame.select', frame_id=self.ids[0])
        source = 'AÑÉ×ßÛÕ a\u0301 😀\nSecond\nThird'
        self.call('document.edit', start=0, end=utf16_length(self.book.text()), text=source)
        plan = self.call('page.transliteration.inspect')
        self.call('document.edit', start=0, end=0, text='A')
        before = self.book.capture()
        failed = self.api.call('page.transliteration.update', dict(expected_plan=plan['planId']), expected_revision=self.book.revision, idempotency_key=uuid.uuid4().hex)
        self.assertFalse(failed['ok']); self.assertIn('TRANSLITERATION_CHANGED', str(failed))
        self.assertEqual(self.book.capture(), before)
        self.call('page.transliteration.update')
        target = self.book.frames[self.ids[1]]
        self.assertEqual(target.text(), 'A' + source)
        self.assertEqual(target.doc.blockCount(), 3)
        self.assertEqual(self.book.automatic_alignment['status'], 'paused')
        model = target.package()['document']
        used = {r['styleId'] for b in model['stories'][0]['blocks'] for r in b['runs']}
        for style in (s for s in model['styles'] if s['styleId'] in used):
            self.assertEqual(style['fontSizeMicroPoints'], '22000000')
            self.assertEqual(style['lineHeight'], dict(mode='exact', microPoints='38000000'))
        self.assertTrue(all(p['after'] == 24 for p in target.package()['paragraphs']))

    def test_standalone_pair_and_protection_against_english(self):
        self.call('page.delete', page_id=self.book.state['pages'][1]['pageId'])
        self.call('page.transliteration.update')
        self.assertEqual(self.book.frames[self.ids[0]].text(), self.book.frames[self.ids[1]].text())
        self.assertEqual(self.book.automatic_alignment['status'], 'aligned')
        self.call('frame.select', frame_id=self.ids[1])
        self.call('document.format', start=0, end=utf16_length(self.book.text()), language='language.en')
        before = self.book.capture()
        result = self.api.call('page.transliteration.update', {}, expected_revision=self.book.revision, idempotency_key=uuid.uuid4().hex)
        self.assertFalse(result['ok']); self.assertIn('TRANSLITERATION_PAIR_REQUIRED', str(result))
        self.assertEqual(self.book.capture(), before)

    def test_existing_inline_formatting_survives_text_refresh(self):
        self.call('frame.select', frame_id=self.ids[1])
        self.call('document.format', start=0, end=1, color='#AA3311FF', tracking=1.5)
        before = self.book.frames[self.ids[1]].package()
        self.call('page.transliteration.update')
        after = self.book.frames[self.ids[1]].package()
        self.assertEqual(after['document']['stories'][0]['blocks'][0]['runs'][0]['styleId'],
                         before['document']['stories'][0]['blocks'][0]['runs'][0]['styleId'])
        self.assertEqual(after['characters'][0]['attributes'], before['characters'][0]['attributes'])

    @unittest.skipUnless((ROOT / '.local/baselines/visual.left-page.2026-10-24/approved.vay.json').exists(), 'Private approved page absent')
    def test_real_fonts_maxima_and_approved_rendering_survive_update_and_undo(self):
        from tools.approved_baseline import rgba_hash
        for patcher in self.font_patches:
            patcher.stop()
        source = ROOT / '.local/baselines/visual.left-page.2026-10-24/approved.vay.json'
        self.book.open(source, advance_revision=False)
        left, right = reading.pairs(self.book.capture())
        self.ids = [left['frameId'], right['frameId']]
        original = self.book.capture()
        image, _ = pages.render(self.book, dpi=72)
        original_pixels = rgba_hash(image)
        self.assertFalse(self.call('page.transliteration.update')['changed'])
        self.assertEqual(self.book.capture(), original)
        self.call('frame.select', frame_id=self.ids[0])
        # Reuse an attested source word, including its original Maxima slots.
        word = self.book.text().split()[0]
        self.call('document.edit', start=0, end=0, text=word + ' ')
        before_update = self.book.capture()
        self.call('page.transliteration.update')
        self.assertEqual(self.book.frames[self.ids[0]].text(), self.book.frames[self.ids[1]].text())
        self.assert_protected(before_update, self.book.capture())
        self.call('history.undo')
        self.assertEqual(self.book.capture()['pages'], before_update['pages'])
        self.call('history.undo')
        self.assertEqual(self.book.capture()['pages'], original['pages'])
        restored, _ = pages.render(self.book, dpi=72)
        self.assertEqual(rgba_hash(restored), original_pixels)
