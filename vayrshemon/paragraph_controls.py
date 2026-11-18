"""Source-pane controls for positioning a paragraph without editing its text."""
from PySide6.QtCore import QSignalBlocker, Qt
from PySide6.QtWidgets import QCheckBox, QDoubleSpinBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from .paragraph_alignment import align, spread_frames
from .session import SCALE


class ParagraphControls(QWidget):
    def __init__(self, window):
        super().__init__(window.editor.parentWidget())
        self.window = window
        self.context = self.paragraph = None
        self.frames = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        spacing = QHBoxLayout()
        layout.addLayout(spacing)
        self.number = QLabel()
        spacing.addWidget(self.number)
        self.fields = {}
        self.displayed_spacing = {}
        for name in ('before', 'after'):
            label = QLabel(name.title())
            spacing.addWidget(label)
            field = QDoubleSpinBox()
            field.setAccessibleName('Space ' + name + ' paragraph in points')
            field.setRange(0, 10000)
            field.setDecimals(2)
            field.setSuffix(' pt')
            field.setKeyboardTracking(False)
            field.setToolTip('Space ' + name + ' the paragraph at the caret')
            label.setBuddy(field)
            spacing.addWidget(field)
            self.fields[name] = field
        self.apply = QPushButton('Apply')
        self.apply.clicked.connect(lambda: window.guard(self.apply_spacing))
        spacing.addWidget(self.apply)
        spacing.addStretch()

        actions = QHBoxLayout()
        layout.addLayout(actions)
        self.match = QPushButton('Align row across columns')
        self.match.setToolTip('Align this paragraph number in all four columns at the lowest of their current starts.')
        self.match.clicked.connect(lambda: window.guard(self.align_row))
        actions.addWidget(self.match)
        self.auto = QCheckBox('Auto-align while typing')
        self.auto.setToolTip('Remember this preference for this spread in this workspace. Applying manual spacing turns it off.')
        self.auto.toggled.connect(self.set_automatic)
        actions.addWidget(self.auto)
        actions.addStretch()
        for control in (self.apply, self.match, self.auto):
            control.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        window.editor.parentWidget().layout().insertWidget(1, self)
        window.editor.cursorPositionChanged.connect(self.sync)
        self.sync()

    def sync(self):
        w = self.window
        book = w.book
        fid = book.state['activeFrameId']
        context = (id(book.state['pages']), len(book.state['pages']), fid)
        if context != self.context:
            self.context = context
            try:
                self.frames = spread_frames(book)
            except ValueError:
                self.frames = []
        block = w.editor.textCursor().block()
        if not block.isValid():
            return
        fmt = block.blockFormat()
        values = (fmt.topMargin()/SCALE, fmt.bottomMargin()/SCALE)
        paragraph = (context, block.blockNumber(), values)
        if paragraph != self.paragraph:
            self.paragraph = paragraph
            self.number.setText(f'Paragraph {block.blockNumber()+1}')
            for (name, field), value in zip(self.fields.items(), values):
                field.setValue(value)
                self.displayed_spacing[name] = field.value()
        editable = w.typing_controls.editable() and book.source_for(fid) == fid
        self.setEnabled(editable)
        self.match.setEnabled(bool(self.frames))
        self.auto.setEnabled(bool(self.frames))
        with QSignalBlocker(self.auto):
            self.auto.setChecked(bool(self.frames and book.spread_auto_alignment(self.frames[0])))

    def set_automatic(self, enabled):
        if self.frames:
            self.window.book.spread_auto_alignment(self.frames[0], enabled)

    def apply_spacing(self):
        w = self.window
        if not self.isEnabled():
            return
        block = w.editor.textCursor().block()
        values = {}
        for name, field in self.fields.items():
            field.interpretText()
            if field.value() != self.displayed_spacing[name]:
                values[name] = field.value()
        if values:
            with w.book.typing_command('Paragraph spacing'):
                w.book.active.paragraph_format(block.position(), block.position(), **values)
            self.auto.setChecked(False)
        w.typing_controls.focus_editor()
        self.sync()

    def align_row(self):
        w = self.window
        if not self.match.isEnabled():
            return
        row = w.editor.textCursor().blockNumber()
        result = align(w.book, self.frames, row=row)
        self.sync()
        w.typing_controls.focus_editor()
        w.statusBar().showMessage(f"Paragraph {row+1} aligned at {max(result['baselinesPt'][0]):.2f} pt.", 8000)
