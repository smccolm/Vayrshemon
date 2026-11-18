"""A non-activating Workbench tool window. All edits target its owner's caret."""
from PySide6.QtCore import QEvent, QRect, QSettings, Qt, QTimer
from PySide6.QtGui import QGuiApplication, QKeyEvent
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QSizePolicy,
                               QStackedWidget, QToolButton, QVBoxLayout, QWidget)
from . import reading
from .frame import ALIGNMENTS
from .keyboard_art import NativeBoard
from .keyboard_input import LABELS, column_role, selected_alignment, type_character
from .keyboard_layout import ENGLISH_ROWS, english_character


def button(label, callback, *, toggle=False):
    control = QToolButton()
    control.setText(label)
    control.setAccessibleName(label)
    control.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    control.setCheckable(toggle)
    control.clicked.connect(lambda checked=False: callback())
    return control


def alignment_buttons(layout, apply):
    controls = {}
    for name in ALIGNMENTS:
        control = button(name.title(), lambda value=name: apply(value), toggle=True)
        control.setToolTip('Align selected paragraphs ' + name if name != 'justify' else
                           'Justify wrapped lines and leave the final line at its natural width')
        layout.addWidget(control)
        controls[name] = control
    return controls


def on_screen(rect, screens, fallback):
    """Keep the whole keyboard on its saved monitor, including negative desktops."""
    def overlap(screen):
        intersection = rect.intersected(screen)
        return intersection.width() * intersection.height() if not intersection.isEmpty() else 0

    screen = max(screens, key=overlap, default=fallback)
    if not overlap(screen):
        screen = fallback
    w, h = min(rect.width(), screen.width()), min(rect.height(), screen.height())
    return QRect(min(max(rect.x(), screen.x()), screen.right()-w+1),
                 min(max(rect.y(), screen.y()), screen.bottom()-h+1), w, h)


class KeyboardWindow(QWidget):
    def __init__(self, controls):
        super().__init__(controls.window, Qt.WindowType.Tool | Qt.WindowType.WindowDoesNotAcceptFocus |
                         Qt.WindowType.WindowTitleHint | Qt.WindowType.WindowCloseButtonHint)
        self.controls = controls
        self.setWindowTitle('Vayrshemon keyboard')
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.shift = self.caps = False
        self.layer = None
        self.settings = QSettings(str(controls.window.book.root / '.local/workspace/keyboard.ini'),
                                  QSettings.Format.IniFormat)
        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        self.target = QLabel()
        top.addWidget(self.target)
        top.addStretch()
        self.align = alignment_buttons(top, controls.apply)
        layout.addLayout(top)
        self.boards = QStackedWidget()
        book = controls.window.book
        self.native = NativeBoard(book.root, book.fonts.resolve('font:' + reading.ROMAN_SHA + ':0'),
                                  self.native_key)
        self.boards.addWidget(self.native)
        english = QWidget()
        rows = QVBoxLayout(english)
        rows.setContentsMargins(0, 0, 0, 0)
        self.latin = []
        for lower, upper in ENGLISH_ROWS:
            row = QHBoxLayout()
            for a, b in zip(lower, upper, strict=True):
                k = button(a, lambda lo=a, hi=b: self.write(english_character(lo, hi, self.caps, self.shift)))
                k.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                row.addWidget(k)
                self.latin.append((a, b, k))
            rows.addLayout(row)
        row = QHBoxLayout()
        for label, fn in [('Backspace', lambda: self.command('Backspace')), ('Space', lambda: self.write(' ')),
                          ('Enter', lambda: self.command('Enter')), ('Delete', lambda: self.command('Delete'))]:
            k = button(label, fn)
            k.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            row.addWidget(k, 3 if label == 'Space' else 1)
        self.dot = button('·', lambda: self.write('·'))
        self.dot.setAccessibleName('Gloss separator')
        self.dot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        row.addWidget(self.dot)
        rows.addLayout(row)
        self.boards.addWidget(english)
        layout.addWidget(self.boards, 1)
        self.modifiers = QWidget()
        bottom = QHBoxLayout(self.modifiers)
        bottom.setContentsMargins(0, 0, 0, 0)
        self.shift_button = button('Shift', lambda: self.command('Shift'), toggle=True)
        self.caps_button = button('Caps', lambda: self.command('Caps'), toggle=True)
        bottom.addWidget(self.shift_button)
        bottom.addWidget(self.caps_button)
        bottom.addStretch()
        for name, glyph in [('Left', '←'), ('Up', '↑'), ('Down', '↓'), ('Right', '→')]:
            k = button(glyph, lambda value=name: self.command(value))
            k.setAccessibleName('Move caret ' + name.lower())
            bottom.addWidget(k)
        layout.addWidget(self.modifiers)
        app = QGuiApplication.instance()
        app.screenRemoved.connect(self.recover_position)
        app.screenAdded.connect(self.watch_screen)
        for screen in app.screens():
            self.watch_screen(screen)

    def watch_screen(self, screen):
        screen.availableGeometryChanged.connect(self.recover_position)

    def recover_position(self, *args):
        if self.isVisible():
            QTimer.singleShot(0, self.fit_screens)

    def fit_screens(self):
        available = [s.availableGeometry() for s in QGuiApplication.screens()]
        fallback = self.controls.window.screen().availableGeometry()
        frame = self.frameGeometry()
        target = on_screen(frame, available, fallback)
        if target != frame:
            self.resize(self.size() + target.size() - frame.size())
            self.move(target.topLeft())

    def open_keyboard(self):
        if self.isVisible():
            return
        area = self.controls.window.screen().availableGeometry()
        saved = self.settings.value('frame', QRect(), type=QRect)
        if not saved.isValid():
            saved = QRect(0, 0, min(area.width(), 940), min(area.height(), 425))
            saved.moveCenter(area.center())
        target = on_screen(saved, [s.availableGeometry() for s in QGuiApplication.screens()], area)
        self.resize(target.size())
        self.move(target.topLeft())
        self.show()
        # Decorations are measurable only once the native tool has been shown.
        margins = self.frameGeometry().size() - self.size()
        self.resize(target.size() - margins)
        self.move(target.topLeft())
        self.fit_screens()
        self.controls.focus_editor()

    def hideEvent(self, event):
        self.settings.setValue('frame', self.frameGeometry())
        self.settings.sync()
        self.controls.launch.setChecked(False)
        self.shift = False
        self.layer = None
        super().hideEvent(event)

    def refresh_keys(self, role):
        native = role in ('script', 'roman')
        identity = (role, self.shift, self.caps)
        if identity == self.layer:
            return
        self.layer = identity
        self.target.setText(LABELS[role])
        self.boards.setCurrentIndex(0 if native else 1)
        self.shift_button.setChecked(self.shift)
        self.caps_button.setChecked(self.caps)
        if native:
            self.native.set_layer(role == 'roman', self.caps ^ self.shift, self.caps)
        else:
            for lo, hi, k in self.latin:
                label = english_character(lo, hi, self.caps, self.shift)
                k.setText(label.replace('&', '&&'))
                k.setAccessibleName(label)
            self.dot.setVisible(role == 'gloss')

    def native_key(self, index):
        key = self.native.keys[index]
        if key.command:
            self.command(key.name)
        else:
            self.write(key.upper if self.caps ^ self.shift else key.lower)

    def write(self, text):
        if not self.controls.editable():
            return
        self.controls.focus_editor()
        window = self.controls.window
        if window.guard(lambda: type_character(window.editor, self.controls.role(), text)):
            self.shift = False
        self.controls.sync()

    def command(self, name):
        if not self.controls.editable():
            return
        if name == 'Shift':
            self.shift = not self.shift
        elif name == 'Caps':
            self.caps = not self.caps
        else:
            self.controls.focus_editor()
            key = getattr(Qt.Key, 'Key_' + ('Return' if name == 'Enter' else name))
            event = QKeyEvent(QEvent.Type.KeyPress, key, Qt.KeyboardModifier.NoModifier,
                              '\r' if name == 'Enter' else '')
            QApplication.sendEvent(self.controls.window.editor, event)
            self.shift = False
        self.controls.sync()


class TypingControls:
    def __init__(self, window):
        self.window = window
        self.keyboard = None
        row = window.action_groups[0].layout()
        group = QWidget()
        buttons = QHBoxLayout(group)
        buttons.setContentsMargins(0, 0, 0, 0)
        self.launch = button('Keyboard', self.toggle, toggle=True)
        buttons.addWidget(self.launch)
        self.align = alignment_buttons(buttons, self.apply)
        row.insertWidget(row.count()-1, group)
        window.resize_actions()
        window.editor.cursorPositionChanged.connect(self.sync)
        window.editor.selectionChanged.connect(self.sync)
        window.editor.currentCharFormatChanged.connect(self.sync)
        window.workspace_tabs.currentChanged.connect(self.sync)
        window.book.changed.connect(self.sync)
        self.sync()

    def editable(self):
        w = self.window
        return (w.workspace_tabs.currentIndex() == 0 and not w.editor.isReadOnly() and
                not w.book.state.get('printEdition') and not w.editor.session.composing)

    def role(self):
        book = self.window.book
        records = getattr(book.frames, 'records', None)
        frame = records[book.state['activeFrameId']] if records is not None else book.locate()[1]
        return column_role(frame, self.window.editor.currentCharFormat())

    def focus_editor(self):
        if self.window.editor.parentWidget().isHidden():
            self.window.configure_workspace(source=True)
        if QApplication.activeWindow() is not self.window and not QApplication.activeModalWidget():
            self.window.activateWindow()
        self.window.editor.setFocus(Qt.FocusReason.OtherFocusReason)

    def toggle(self):
        if self.keyboard and self.keyboard.isVisible():
            self.keyboard.hide()
            return
        if self.keyboard is None:
            self.keyboard = KeyboardWindow(self)
        self.focus_editor()
        self.keyboard.open_keyboard()
        self.sync()

    def apply(self, name):
        if self.editable():
            self.focus_editor()
            self.window.invoke('paragraph.format', **self.window.selected_range(), alignment=name)
        self.sync()

    def sync(self, *args):
        enabled = self.editable()
        alignment = selected_alignment(self.window.editor.textCursor())
        groups = [self.align]
        kb = self.keyboard
        if kb and kb.isVisible():
            kb.refresh_keys(self.role())
            kb.boards.setEnabled(enabled)
            kb.modifiers.setEnabled(enabled)
            groups.append(kb.align)
        self.launch.setChecked(bool(kb and kb.isVisible()))
        for group in groups:
            for name, control in group.items():
                control.setChecked(alignment == name)
                control.setEnabled(enabled)
