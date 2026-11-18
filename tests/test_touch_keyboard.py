import json
import hashlib
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from PySide6.QtCore import QCoreApplication, QEvent, QPoint, QRect, Qt
from PySide6.QtGui import QFontDatabase, QGuiApplication, QTextCursor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from vayrshemon import reading
from vayrshemon.file_api import FileAPI, FileSession
from vayrshemon.file_window import FileWindow
from vayrshemon.fonts import FontRegistry
from vayrshemon.keyboard_layout import DIGITS, ENGLISH_ROWS, english_character, native_keys
from vayrshemon.touch_keyboard import on_screen
from vayrshemon.typesetting import Composition


ROOT = Path(__file__).resolve().parents[1]
APP = QApplication.instance() or QApplication([])
# The offscreen plugin on Windows does not enumerate installed desktop fonts.
if APP.platformName() == 'offscreen' and 'Segoe UI' not in QFontDatabase.families():
    ui_font = Path(os.environ.get('WINDIR', 'C:/Windows'))/'Fonts/segoeui.ttf'
    if ui_font.is_file():
        QFontDatabase.addApplicationFont(str(ui_font))


class KeyMappingTests(unittest.TestCase):
    def test_serviced_punctuation_font_requires_exact_publication_hash(self):
        registry = object.__new__(FontRegistry)
        registry.bundled = {}
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, WINDIR=directory):
            windows = Path(directory)
            current = windows/'Fonts/times.ttf'
            earlier = windows/'WinSxS/amd64_microsoft-windows-f..etype-timesnewroman_123/times.ttf'
            for file, data in [(current, b'current'), (earlier, b'published')]:
                file.parent.mkdir(parents=True)
                file.write_bytes(data)
            for data, expected in [(b'current', current), (b'published', earlier), (b'other', current)]:
                self.assertEqual(registry.document_path(current, hashlib.sha256(data).hexdigest()), expected)
            foreign = windows/'user/times.ttf'
            self.assertEqual(registry.document_path(foreign, hashlib.sha256(b'published').hexdigest()), foreign)

    def test_all_letters_digits_and_english_modifier_combinations(self):
        chart = json.loads((ROOT/'data/orthography/chart-transcription.json').read_text(encoding='utf-8'))
        keys = native_keys(ROOT)
        self.assertEqual(len(keys), 70)
        by_name = {key.name: key for key in keys}
        for _, upper, lower, name, *_ in chart['letters']:
            self.assertEqual((by_name[name].lower, by_name[name].upper), (chr(lower), chr(upper)))
        for i, (value, scalar, _) in zip(DIGITS, chart['numerals']):
            self.assertEqual((keys[i].lower, keys[i].upper), (chr(scalar), '{}%|_~=+-*/\\'[value]))
        self.assertEqual([keys[i].lower for i in (55, 60, 64, 68)], ['?', ':', '’', '"'])
        for row, shifted in ENGLISH_ROWS:
            for a, b in zip(row, shifted):
                self.assertEqual([english_character(a, b, caps, shift) for caps, shift in
                                  ((False, False), (False, True), (True, False), (True, True))],
                                 [a, b, a.upper(), a if a.isalpha() else b])

    def test_screen_placement_negative_stacked_disconnected_and_smaller(self):
        main = QRect(0, 0, 1920, 1040)
        left = QRect(-2400, -200, 2400, 1400)
        above = QRect(240, -1080, 1920, 1040)
        screens = [main, left, above]
        for screen in screens:
            rect = QRect(screen.x()+50, screen.y()+60, 800, 370)
            self.assertEqual(rect, on_screen(rect, screens, main))
        self.assertEqual(on_screen(QRect(-3000, 100, 800, 400), screens, main).left(), left.left())
        self.assertEqual(on_screen(QRect(-2300, 80, 800, 400), [main], main).left(), main.left())
        self.assertEqual(on_screen(QRect(10, 10, 2400, 1400), [main], main), main)


class KeyboardWindowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT/'schemas', self.root/'schemas')
        for part in ('runtime-fonts', 'orthography', 'keyboard'):
            shutil.copytree(ROOT/'data'/part, self.root/'data'/part)
        shutil.copy2(ROOT/'data/fonts.json', self.root/'data/fonts.json')
        self.book = FileSession(self.root, source_fonts=False, recovery=False)
        self.api = FileAPI(self.book)
        self.ids = []
        for i, name in enumerate(('Vayrshemon', 'Transliteration 7', 'Construction gloss', 'Marriott · English source')):
            if i == 2:
                self.call('page.add')
            if i % 2:
                self.call('frame.add', x=300, y=20, width=250, height=700)
            self.call('frame.configure', name=name, width=250)
            self.call('document.edit', start=0, end=0, text='abc')
            self.call('document.format', start=0, end=3, size=18, color='#123456FF',
                      font_id='font:'+ (reading.SCRIPT_SHA if i == 0 else reading.ROMAN_SHA)+':0',
                      language='language.vayrshemon' if i < 2 else 'language.en')
            self.ids.append(self.book.state['activeFrameId'])
        self.window = FileWindow(self.book, self.api)
        self.addCleanup(self.dispose)
        self.window.show()
        self.window.activateWindow()
        APP.processEvents()
        self.controls = self.window.typing_controls
        self.select(3, 1)
        QTest.mouseClick(self.controls.launch, Qt.MouseButton.LeftButton)
        APP.processEvents()
        self.kb = self.controls.keyboard
        self.editor = self.window.editor
        self.assertTrue(self.kb.isVisible())

    def dispose(self):
        self.window.timer.stop()
        self.window.job_timer.stop()
        self.window.forge_panel.timer.stop()
        self.window.hide()
        self.book.window = self.book._editor = None
        self.window.deleteLater()
        self.book.finish()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def call(self, method, **params):
        response = self.api.call(method, params, expected_revision=self.book.revision, origin='desktop')
        self.assertTrue(response['ok'], response)
        return response['result']

    def select(self, column, start, end=None):
        self.call('selection.set', frame_id=self.ids[column], start=start, end=start if end is None else end)

    def tap(self, widget):
        QTest.mouseClick(widget, Qt.MouseButton.LeftButton)
        APP.processEvents()

    def test_source_ink_remains_readable_through_typing_and_undo(self):
        from collections import Counter
        from PySide6.QtGui import QImage

        self.window.configure_workspace(source=True)
        self.call('document.format', start=0, end=3, color='#E4E9F0FF')
        self.select(3, 1)
        stored = self.book.capture()['pages']
        self.editor.setFocus()
        for after_input in (False, True):
            if after_input:
                QTest.keyClicks(self.editor, 'a')
            image = self.editor.viewport().grab().toImage().convertToFormat(QImage.Format.Format_RGB32)
            pixels = Counter(memoryview(image.constBits()).cast('I'))
            self.assertGreater(pixels[0xff17212b], 2)
            self.assertGreater(pixels[0xffffffff], 100)
            self.assertEqual(self.editor.textCursor().charFormat().foreground().color().name(), '#e4e9f0')
        self.call('history.undo')
        self.assertEqual(self.book.capture()['pages'], stored)

    def test_durable_keys_alternate_with_full_edits_and_recover_from_write_failure(self):
        from vayrshemon.typing_storage import read_checkpoint
        self.select(3, 0)
        book = self.book
        book.recovery_enabled = True
        book.checkpoint()

        def check():
            current = book.capture()
            self.assertEqual(book._state, current)
            self.assertEqual(read_checkpoint(book.recovery_path, book.max_file_bytes)['state'], current)
            self.assertEqual(book.history[-1]['sha256'], book.content_digest(current))
            self.assertEqual(book.revision, book.durable_revision)

        QTest.keyClicks(self.editor, 'a')
        check()
        last = book.durable_revision
        with patch('vayrshemon.typing_storage.write_atomic', side_effect=OSError('disk full')):
            self.kb.write('b')
        self.assertEqual(book.durable_revision, last)
        self.assertIn('disk full', book.recovery_error)
        self.assertEqual(read_checkpoint(book.recovery_path, book.max_file_bytes)['state']['revision'], last)
        self.kb.write('c')
        check()
        self.call('document.title', title='Typing checkpoint test')
        QTest.keyClick(self.editor, Qt.Key.Key_Backspace)
        check()
        for change in ('history.undo', 'history.undo', 'history.undo', 'history.redo', 'history.redo', 'history.redo'):
            self.call(change)
            check()
        self.assertEqual(book.text(), 'ababc')

    def test_navigation_during_typing_is_clean_and_paste_is_one_undo(self):
        self.select(3, 1)
        rev = self.book.revision
        QTest.keyClick(self.editor, Qt.Key.Key_Right)
        self.assertEqual(self.book.revision, rev)
        APP.clipboard().setText('two words')
        QTest.keyClick(self.editor, Qt.Key.Key_V, Qt.KeyboardModifier.ControlModifier)
        self.assertEqual(self.book.text(), 'abtwo wordsc')
        self.assertEqual(self.book.revision, rev+1)
        self.call('history.undo')
        self.assertEqual(self.book.text(), 'abc')

    def test_all_art_regions_route_at_two_sizes_in_both_cases_and_scripts(self):
        board = self.kb.native
        for col in (0, 1):
            self.select(col, 1)
            for width in (750, 1040):
                self.kb.resize(width, 400)
                APP.processEvents()
                for upper in (False, True):
                    self.kb.caps = upper
                    self.controls.sync()
                    with patch.object(self.kb, 'write') as write, patch.object(self.kb, 'command') as command:
                        for i, key in enumerate(board.keys):
                            with self.subTest(col=col, width=width, upper=upper, index=i):
                                child = board.buttons[i]
                                center = child.geometry().center()
                                self.assertIs(board.childAt(center), child)
                                self.assertTrue(child.mask().contains(child.rect().center()))
                                self.tap(child)
                                if key.command:
                                    command.assert_called_with(key.name)
                                else:
                                    write.assert_called_with(key.upper if upper else key.lower)
                                command.reset_mock()
                                write.reset_mock()
                    self.assertIsNone(board.childAt(QPoint(0, 0)))

    def test_live_columns_case_clitics_english_and_history(self):
        for col, role in enumerate(('script', 'roman', 'gloss', 'english')):
            self.select(col, 1, 2)
            self.assertEqual(self.controls.role(), role)
            if col < 2:
                self.tap(self.kb.native.buttons[2])
                self.tap(self.kb.shift_button)
                self.tap(self.kb.native.buttons[2])
                self.tap(self.kb.native.buttons[64])
                self.tap(self.kb.native.buttons[67])
                self.tap(self.kb.native.buttons[65])
                self.tap(self.kb.native.buttons[2])
                self.tap(self.kb.native.buttons[65])
                self.assertEqual(self.book.text(), 'aÃÂ’ÁÂc')
                self.assertEqual(self.editor.textCursor().position(), 6)
                runs = self.book.active.package()['document']['stories'][0]['blocks'][0]['runs']
                self.assertTrue(all(r['type'] == 'legacy' for r in runs))
                self.assertTrue(all(r['sourceFontSha256'] == (reading.SCRIPT_SHA, reading.ROMAN_SHA)[col] for r in runs))
            else:
                a = next(k for lo, _, k in self.kb.latin if lo == 'a')
                self.tap(self.kb.shift_button)
                self.tap(a)
                if col == 2:
                    self.assertTrue(self.kb.dot.isVisible())
                    self.tap(self.kb.dot)
                else:
                    self.assertFalse(self.kb.dot.isVisible())
                self.tap(a)
                self.assertEqual(self.book.text(), 'aA·ac' if col == 2 else 'aAac')
                runs = self.book.active.package()['document']['stories'][0]['blocks'][0]['runs']
                self.assertTrue(all(r['type'] == 'unicode' for r in runs))
        self.assertEqual([self.book.frames[f].text() for f in self.ids], ['aÃÂ’ÁÂc']*2+['aA·ac', 'aAac'])
        self.call('history.undo')
        self.assertEqual(self.book.text(), 'aAc')
        self.call('history.redo')
        self.assertEqual(self.book.text(), 'aAac')
        path = self.root/'roundtrip.vay'
        self.book.save(path)
        self.book.open(path)
        self.assertEqual([self.book.frames[f].text() for f in self.ids], ['aÃÂ’ÁÂc']*2+['aA·ac', 'aAac'])

    def test_every_printable_key_roundtrips_through_each_column(self):
        expected = []
        for col in range(4):
            self.select(col, 0, 3)
            chars = []
            for upper in (False, True):
                if upper:
                    self.kb.command('Caps')
                if col < 2:
                    for k, widget in zip(self.kb.native.keys, self.kb.native.buttons):
                        if not k.command:
                            self.tap(widget)
                            chars.append(k.upper if upper else k.lower)
                else:
                    for lo, hi, widget in self.kb.latin:
                        if upper and not lo.isalpha():
                            self.kb.command('Shift')
                        self.tap(widget)
                        chars.append(hi if upper else lo)
            self.kb.command('Caps')
            expected.append(''.join(chars))
            self.assertEqual(self.book.text(), expected[-1])
            self.assertEqual(self.editor.textCursor().position(), len(expected[-1]))
        path = self.root/'all-keys.vay'
        self.book.save(path)
        self.book.open(path)
        self.assertEqual([self.book.frames[f].text() for f in self.ids], expected)

    def test_selection_mixed_alignment_caret_and_physical_typing(self):
        self.select(3, 0, 3)
        self.call('document.edit', start=0, end=3, text='first\nsecond\nthird')
        self.call('paragraph.format', start=0, end=0, before=3, after=7, tabs=[24.0])
        cursor = self.editor.textCursor()
        cursor.setPosition(13)
        cursor.setPosition(1, QTextCursor.MoveMode.KeepAnchor)
        self.editor.setTextCursor(cursor)
        self.tap(self.kb.align['center'])
        self.assertEqual((self.editor.textCursor().anchor(), self.editor.textCursor().position()), (13, 1))
        paras = self.book.active.package()['paragraphs']
        self.assertEqual([p['alignment'] for p in paras], ['center','center','left'])
        self.assertEqual((paras[0]['before'], paras[0]['tabs']), (3, [24]))
        self.assertAlmostEqual(paras[0]['after'], 7)
        for source, dest in ((self.controls, self.kb), (self.kb, self.controls)):
            for name in ('right', 'left', 'justify', 'center'):
                self.tap(source.align[name])
                self.assertTrue(dest.align[name].isChecked())
                self.assertEqual((self.editor.textCursor().anchor(), self.editor.textCursor().position()), (13, 1))
        self.select(3, 1, 14)
        self.assertFalse(any(b.isChecked() for b in self.kb.align.values()))
        self.select(3, 3)
        cursor = self.editor.textCursor().position()
        self.kb.move(self.kb.pos() + QPoint(12, 8))
        self.assertEqual(self.editor.textCursor().position(), cursor)
        self.assertIs(QApplication.focusWidget(), self.editor)
        QTest.keyClicks(self.editor, 'Z')
        self.assertTrue(self.book.text().startswith('firZst'))

    def test_forward_backward_delete_return_navigation_and_reopen(self):
        self.select(3, 1)
        for action, expected in [('Right','abc'), ('Backspace','ac'), ('Enter','a\nc'), ('Delete','a\n')]:
            self.kb.command(action)
            self.assertEqual(self.book.text(), expected)
        self.kb.command('Up')
        self.kb.command('Down')
        self.kb.write('x')
        self.assertEqual(self.book.text(), 'a\nx')
        self.kb.command('Shift')
        self.kb.close()
        self.assertFalse(self.controls.launch.isChecked())
        self.tap(self.controls.launch)
        self.assertIs(self.controls.keyboard, self.kb)
        self.assertFalse(self.kb.shift)
        self.assertEqual(self.editor.textCursor().position(), 3)
        self.assertTrue(self.kb.settings.value('frame', type=QRect).isValid())

    def test_connected_monitor_move_focus_typing_and_saved_position(self):
        self.select(0, 1)
        key = self.kb.native.buttons[2]
        for index, screen in enumerate(QGuiApplication.screens()):
            self.kb.move(screen.availableGeometry().topLeft() + QPoint(18, 36))
            APP.processEvents()
            self.assertEqual(self.kb.screen().name(), screen.name())
            self.tap(key)
            self.assertEqual(self.editor.textCursor().position(), 2 + index)
            self.assertIs(QApplication.focusWidget(), self.editor)
        saved = on_screen(self.kb.frameGeometry(), [s.availableGeometry() for s in QGuiApplication.screens()],
                          self.window.screen().availableGeometry())
        self.kb.close()
        self.tap(self.controls.launch)
        APP.processEvents()
        self.assertEqual(self.kb.screen().name(), screen.name())
        self.assertLessEqual((self.kb.frameGeometry().topLeft() - saved.topLeft()).manhattanLength(), 2)

    def test_touch_tap_on_art_and_english_key(self):
        device = QTest.createTouchDevice()
        def touch(widget):
            point = widget.rect().center()
            QTest.touchEvent(widget, device).press(0, point, widget).commit()
            QTest.touchEvent(widget, device).release(0, point, widget).commit()
            APP.processEvents()
        self.select(0, 1)
        touch(self.kb.native.buttons[2])
        self.assertEqual(self.book.text(), 'aÃbc')
        self.select(3, 2)
        touch(next(k for lo, _, k in self.kb.latin if lo == 'q'))
        self.assertEqual(self.book.text(), 'abqc')

    def test_empty_paragraph_and_missing_font_punctuation(self):
        self.select(0, 0, 3)
        self.kb.command('Delete')
        self.assertEqual(self.book.text(), '')
        self.kb.command('Shift')
        self.tap(self.kb.native.buttons[0])
        self.tap(self.kb.native.buttons[2])
        self.assertEqual(self.book.text(), '{Ã')
        runs = self.book.active.package()['document']['stories'][0]['blocks'][0]['runs']
        self.assertEqual([r['type'] for r in runs], ['unicode', 'legacy'])
        self.assertEqual(runs[1]['sourceFontSha256'], reading.SCRIPT_SHA)
        self.kb.command('Enter')
        self.tap(self.kb.native.buttons[1])
        self.assertEqual(self.book.text(), '{Ã\nj')
        self.select(2, 3)
        self.tap(self.kb.dot)
        self.kb.write('q')
        doc = self.book.active.package()['document']
        runs = doc['stories'][0]['blocks'][0]['runs']
        style = next(s for s in doc['styles'] if s['styleId'] == runs[-1]['styleId'])
        self.assertEqual(style['fontId'], 'font:' + reading.ROMAN_SHA + ':0')

    def test_readonly_composing_forge_and_document_limit(self):
        rev = self.book.revision
        for guarded in ('readonly', 'composition', 'forge'):
            self.editor.setReadOnly(guarded == 'readonly')
            self.editor.session.composing = guarded == 'composition'
            self.window.workspace_tabs.setCurrentIndex(int(guarded == 'forge'))
            self.controls.sync()
            self.assertFalse(self.kb.boards.isEnabled())
            self.kb.write('z')
            self.kb.command('Delete')
            self.controls.apply('right')
            self.assertEqual(self.book.revision, rev)
        self.window.workspace_tabs.setCurrentIndex(0)
        with patch.object(self.book, 'max_document_scalars', 12):
            self.kb.write('z')
            self.assertEqual(self.book.text(), 'abc')
            self.select(3, 0, 1)
            self.kb.write('z')
            self.assertEqual(self.book.text(), 'zbc')

    def test_justified_layout_stops_at_last_line(self):
        text = 'one two three four five six seven eight nine ten eleven twelve end'
        self.call('document.edit', start=0, end=3, text=text)
        self.call('typesetting.configure', enabled=True)
        self.controls.apply('justify')
        comp = Composition(self.book, page_id=self.book.current_page()['pageId'])
        lines = comp.stories[self.ids[3]]['lines']
        self.assertGreater(len(lines), 1)
        for item in lines[:-1]:
            line = item['_line']
            end = line.textStart() + line.textLength()
            while text[end-1].isspace():
                end -= 1
            self.assertAlmostEqual(line.cursorToX(end)[0], line.width(), delta=2)
        last = lines[-1]['_line']
        self.assertLess(last.cursorToX(len(text))[0], last.width()-5)
