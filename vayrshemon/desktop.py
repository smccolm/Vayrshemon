"""Native input/accessibility adapter and the font laboratory window."""
import json
from pathlib import Path
import time

from PySide6.QtCore import Qt, QRectF, QTimer, QSize
from PySide6.QtGui import (QAccessible, QAction, QColor, QImageReader, QKeySequence,
                          QPainter, QPen, QPixmap, QTextCursor)
from PySide6.QtWidgets import (QAbstractScrollArea, QApplication, QCheckBox, QComboBox,
    QDockWidget, QDoubleSpinBox, QFileDialog, QFormLayout, QFrame, QHBoxLayout, QLabel,
    QMainWindow, QMessageBox, QPlainTextEdit, QPushButton, QScrollArea, QSlider,
    QSplitter, QTabWidget, QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget)

from . import __version__
from . import layout
from .session import SCALE, checked_text, utf16_length, scalar_offset


def accessibility(editor):
    interface = QAccessible.queryAccessibleInterface(editor)
    if interface is None:
        return dict(available=False)
    text = interface.textInterface()
    count = text.characterCount() if text else 0
    selections = []
    if text:
        # PySide 6.8 does not bind selection()'s two C++ output pointers.
        # The native provider exposes the count; the same widget supplies ranges.
        if text.selectionCount():
            cursor = editor.textCursor()
            selections.append((cursor.selectionStart(), cursor.selectionEnd()))
    return dict(available=True, role=str(interface.role()), name=interface.text(QAccessible.Text.Name),
                editableText=bool(interface.editableTextInterface()), textInterface=bool(text),
                characterCount=count, text=text.text(0, count) if text else None,
                caretUtf16=text.cursorPosition() if text else None, selections=selections,
                selectionRangeSource='QTextCursor; provider selectionCount verified',
                coordinates='UTF-16 code units', provider='Qt native accessibility adapter')


class Editor(QTextEdit):
    def __init__(self, session):
        super().__init__()
        self.session = session
        self.setObjectName('documentEditor')
        self.setAccessibleName('Document text')
        self.setAccessibleDescription('Editable English and Vayrshemon text. Use the font and language controls for the selection or next input.')
        self.setAcceptRichText(False)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setLineWrapMode(QTextEdit.LineWrapMode.FixedPixelWidth)
        self.setDocument(session.doc)
        session.editor = self
        self.setMinimumWidth(320)
        self._key_started = None
        self._format_shortcuts = {Qt.Key.Key_B, Qt.Key.Key_I, Qt.Key.Key_U}
        session.configure_layout()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'session'):
            self.session.doc.setTextWidth(int(self.session.model['pages'][0]['widthMicroPoints']) / 1_000_000 * SCALE)
            self.session.doc.documentLayout().setPaintDevice(self.session.metrics_device)

    def keyPressEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier and event.key() in self._format_shortcuts:
            return  # Unmodelled rich-text formatting is not silently introduced.
        self._key_started = time.perf_counter()
        inserts_break = event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Tab)
        if inserts_break or (event.text() and not (event.modifiers() & Qt.KeyboardModifier.ControlModifier)):
            try:
                text = '\n' if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) else event.text()
                if event.key() not in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete):
                    cursor = self.textCursor()
                    before = self.session.text()
                    start, end = scalar_offset(before,cursor.selectionStart()), scalar_offset(before,cursor.selectionEnd())
                    checked_text(before[:start] + text + before[end:])
            except ValueError as error:
                self.session.log.emit('input', 'INPUT_REJECTED', level='warning', message=str(error))
                return
        super().keyPressEvent(event)

    def insertFromMimeData(self, source):
        try:
            # Native external clipboard newlines use CRLF on Windows. Reject
            # unsupported controls explicitly rather than losing source bytes.
            text = source.text()
            cursor = self.textCursor()
            self.session.edit(cursor.selectionStart(), cursor.selectionEnd(), text)
        except Exception as error:
            self.session.log.exception('clipboard', error)
            if self.session.window:
                self.session.window.statusBar().showMessage(str(error), 10000)

    def inputMethodEvent(self, event):
        try:
            checked_text(event.preeditString())
            checked_text(event.commitString())
            checked_text(self.session.text() + event.commitString())
        except ValueError as error:
            event.ignore()
            self.session.log.emit('input', 'IME_REJECTED', level='warning', message=str(error))
            return
        self._key_started = time.perf_counter()
        before = self.session.text()
        was_loading = self.session._loading
        self.session._loading = True
        try:
            super().inputMethodEvent(event)
        finally:
            self.session._loading = was_loading
        self.session.composing = bool(event.preeditString())
        if self.session.text() != before:
            self.session._contents_changed()
        else:
            self.session.changed.emit()
        self.session.log.emit('input', 'IME_EVENT', preeditUtf16=utf16_length(event.preeditString()),
                              committedUtf16=utf16_length(event.commitString()), revision=self.session.revision)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self.viewport())
        page = self.session.model['pages'][0]
        width = int(page['widthMicroPoints']) / 1_000_000 * SCALE
        height = int(page['heightMicroPoints']) / 1_000_000 * SCALE
        painter.setPen(QPen(QColor('#96a5b3'), 1, Qt.PenStyle.DashLine))
        painter.drawRect(QRectF(-self.horizontalScrollBar().value(), -self.verticalScrollBar().value(), width, height))
        painter.end()
        if self._key_started:
            self.session.timings.append((time.perf_counter()-self._key_started)*1000)
            self.session.timings = self.session.timings[-1000:]
            self._key_started = None


class Preview(QAbstractScrollArea):
    def __init__(self, session):
        super().__init__()
        self.session = session
        self.zoom = .65
        self.setObjectName('colorPreview')
        self.setAccessibleName('Registered color page preview')
        self.setMinimumWidth(280)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.horizontalScrollBar().valueChanged.connect(self.viewport().update)
        self.verticalScrollBar().valueChanged.connect(self.viewport().update)

    def update_page(self):
        page = self.session.model['pages'][0]
        self.horizontalScrollBar().setRange(0, max(0, round(int(page['widthMicroPoints'])/1_000_000*SCALE*self.zoom)-self.viewport().width()))
        self.verticalScrollBar().setRange(0, max(0, round(int(page['heightMicroPoints'])/1_000_000*SCALE*self.zoom)-self.viewport().height()))
        self.viewport().update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_page()

    def paintEvent(self, event):
        started = time.perf_counter()
        painter = QPainter(self.viewport())
        painter.fillRect(self.viewport().rect(), QColor('#dfe6ec'))
        painter.translate(-self.horizontalScrollBar().value(), -self.verticalScrollBar().value())
        painter.scale(self.zoom, self.zoom)
        page = self.session.model['pages'][0]
        page_rect = QRectF(0, 0, int(page['widthMicroPoints'])/1_000_000*SCALE, int(page['heightMicroPoints'])/1_000_000*SCALE)
        clip = QRectF(self.horizontalScrollBar().value()/self.zoom, self.verticalScrollBar().value()/self.zoom,
                      self.viewport().width()/self.zoom, self.viewport().height()/self.zoom).intersected(page_rect)
        painter.fillRect(page_rect, QColor('white'))
        layout.paint(self.session, painter, mode=self.session.view['mode'], clip=clip, overlays=self.session.view)
        painter.end()
        self.last_paint_ms = (time.perf_counter()-started)*1000


class LabWindow(QMainWindow):
    def __init__(self, session, api):
        super().__init__()
        self.session, self.api = session, api
        self._page_signature = None
        self._font_signature = None
        session.window = self
        self.setWindowTitle(f'Vayrshemon — Font & Input Laboratory / M1 {__version__}')
        self.resize(1480, 960)
        self.setMinimumSize(1000, 700)
        self.setStyleSheet('''
            QMainWindow { background: #e8edf2; }
            QWidget { font-family: "Segoe UI"; font-size: 10pt; }
            QLabel#brand { font-size: 20pt; font-weight: 600; color: #14304a; }
            QLabel#sectionTitle { font-size: 9pt; font-weight: 600; color: #486078; padding: 7px; background: #edf2f6; }
            QPushButton { padding: 6px 11px; border: 1px solid #b5c5d1; border-radius: 4px; background: #f7fafc; }
            QPushButton:hover { background: #deedf5; }
            QComboBox, QDoubleSpinBox { min-height: 27px; }
            QTabWidget::pane { border: 1px solid #c2ced8; background: #fff; }
            QStatusBar { background: #17354c; color: #e6f2fa; }
        ''')
        central = QWidget()
        column = QVBoxLayout(central)
        column.setContentsMargins(14, 10, 14, 8)
        top = QHBoxLayout()
        brand = QLabel('Vayrshemon')
        brand.setObjectName('brand')
        top.addWidget(brand)
        top.addWidget(QLabel('FONT / INPUT LAB     M1'))
        top.addStretch()
        for name, callback in [('Open', self.open_file), ('Save', self.save_file), ('Load TTF', self.load_font),
                               ('Export PNG', self.export_png), ('Undo', lambda: self.invoke('history.undo')),
                               ('Redo', lambda: self.invoke('history.redo'))]:
            button = QPushButton(name)
            button.clicked.connect(lambda checked=False, fn=callback: self.guard(fn))
            top.addWidget(button)
        column.addLayout(top)
        controls = QHBoxLayout()
        self.width_input, self.height_input = QDoubleSpinBox(), QDoubleSpinBox()
        for control, name in ((self.width_input, 'Page width'), (self.height_input, 'Page height')):
            control.setAccessibleName(name)
            control.setRange(.001, 1_000_000)
            control.setDecimals(3)
            control.setMaximumWidth(105)
        self.width_input.setValue(612)
        self.height_input.setValue(792)
        self.unit = QComboBox()
        self.unit.addItems(['pt', 'mm', 'in'])
        self.unit.setAccessibleName('Page dimension unit')
        for widget in [QLabel('Page'), self.width_input, QLabel('×'), self.height_input, self.unit]:
            controls.addWidget(widget)
        apply_page = QPushButton('Set size')
        apply_page.clicked.connect(lambda: self.guard(lambda: self.invoke('page.configure', width=self.width_input.value(), height=self.height_input.value(), unit=self.unit.currentText())))
        controls.addWidget(apply_page)
        self.font_choice = QComboBox()
        self.font_choice.setAccessibleName('Font file')
        self.font_choice.setMinimumWidth(180)
        self.refresh_fonts()
        self.language = QComboBox()
        self.language.setAccessibleName('Text language')
        self.language.addItem('English', 'language.en')
        self.language.addItem('Vayrshemon', 'language.vayrshemon')
        self.language.addItem('Undetermined', 'language.undetermined')
        self.font_size = QDoubleSpinBox()
        self.font_size.setAccessibleName('Font size in points')
        self.font_size.setRange(1, 1000)
        self.font_size.setValue(42)
        self.font_size.setSuffix(' pt')
        for widget in [self.font_choice, self.language, self.font_size]:
            controls.addWidget(widget)
        apply_format = QPushButton('Apply to text')
        apply_format.clicked.connect(lambda: self.guard(self.apply_format))
        controls.addWidget(apply_format)
        controls.addStretch()
        column.addLayout(controls)
        panels = QSplitter(Qt.Orientation.Horizontal)
        self.editor = Editor(session)
        self.preview = Preview(session)
        self.reference = QLabel('Load an archived reference image\nto compare it beside the live text.')
        self.reference.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.reference.setWordWrap(True)
        self.reference.setMinimumSize(190, 100)
        self.reference.setAccessibleName('Reference image')
        reference_box = QWidget()
        reference_layout = QVBoxLayout(reference_box)
        reference_layout.setContentsMargins(0, 0, 0, 0)
        reference_layout.addWidget(self.reference, 1)
        reference_button = QPushButton('Choose reference image')
        reference_button.clicked.connect(lambda: self.guard(self.choose_reference))
        reference_layout.addWidget(reference_button)
        for title, content in [('EDIT / MONOCHROME · 100%', self.editor), ('COLOR / SHARED GLYPH POSITIONS', self.preview), ('REFERENCE / SOURCE ART', reference_box)]:
            panel = QWidget()
            stack = QVBoxLayout(panel)
            stack.setContentsMargins(0, 0, 0, 0)
            label = QLabel(title)
            label.setObjectName('sectionTitle')
            stack.addWidget(label)
            stack.addWidget(content, 1)
            panels.addWidget(panel)
        panels.setSizes([570, 570, 280])
        column.addWidget(panels, 1)
        options = QHBoxLayout()
        self.layer_checks = []
        for index, label in enumerate(('80 · base', '81 · interior', '79 · outline')):
            check = QCheckBox(label)
            check.setChecked(True)
            check.setEnabled(bool(session.fonts.recipe))
            check.toggled.connect(lambda enabled, i=index: self.guard(lambda: self.invoke('view.configure', layer=i, enabled=enabled)))
            options.addWidget(check)
            self.layer_checks.append(check)
        self.overlay_checks = {}
        for key in ('baselines', 'origins', 'bounds'):
            check = QCheckBox(key.title())
            self.overlay_checks[key] = check
            check.toggled.connect(lambda enabled, k=key: self.guard(lambda: self.invoke('view.configure', **{k: enabled})))
            options.addWidget(check)
        self.feature_checks = {}
        for feature in ('kern', 'liga'):
            check = QCheckBox(feature)
            self.feature_checks[feature] = check
            check.setChecked(True)
            check.toggled.connect(lambda enabled, f=feature: self.guard(lambda: self.invoke('features.configure', **{f: enabled})))
            options.addWidget(check)
        options.addStretch()
        options.addWidget(QLabel('Color zoom'))
        zoom = QSlider(Qt.Orientation.Horizontal)
        self.zoom_control = zoom
        zoom.setAccessibleName('Color preview zoom percent')
        zoom.setRange(10, 300)
        zoom.setValue(65)
        zoom.setMaximumWidth(180)
        zoom.valueChanged.connect(lambda value: self.guard(lambda: self.invoke('view.configure', zoom=value/100)))
        options.addWidget(zoom)
        column.addLayout(options)
        self.setCentralWidget(central)
        self.tabs = QTabWidget()
        self.glyph_table = QTableWidget(0, 6)
        self.glyph_table.setHorizontalHeaderLabels(['Source / cluster', 'Glyph', 'Font', 'Origin x, y', 'Advance', 'Fallback'])
        self.glyph_table.horizontalHeader().setStretchLastSection(True)
        self.tabs.addTab(self.glyph_table, 'Glyph inspector')
        self.details, self.logs, self.access = QPlainTextEdit(), QPlainTextEdit(), QPlainTextEdit()
        for widget in (self.details, self.logs, self.access):
            widget.setReadOnly(True)
        self.tabs.addTab(self.details, 'Layout / JSON')
        self.tabs.addTab(self.logs, 'Diagnostics')
        self.tabs.addTab(self.access, 'Accessibility')
        dock = QDockWidget('Inspection', self)
        dock.setWidget(self.tabs)
        dock.setMinimumHeight(180)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock)
        self.resizeDocks([dock], [220], Qt.Orientation.Vertical)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.refresh)
        session.changed.connect(self.on_change)
        self.editor.cursorPositionChanged.connect(lambda: self.timer.start())
        self.tabs.currentChanged.connect(lambda: self.timer.start())
        for shortcut, callback in [(QKeySequence.StandardKey.Save, self.save_file), (QKeySequence.StandardKey.Open, self.open_file)]:
            action = QAction(self)
            action.setShortcut(shortcut)
            action.triggered.connect(lambda checked=False, fn=callback: self.guard(fn))
            self.addAction(action)
        self.refresh()
        reference_path = session.root / 'Inputs/Origins_A Blue Jewel.jpg'
        if reference_path.exists():
            self.guard(lambda: self.set_reference(reference_path))

    def invoke(self, method, **params):
        result = self.api.call(method, params, expected_revision=self.session.revision,
                               idempotency_key=None, origin='desktop')
        if not result['ok']:
            raise ValueError(result['error']['message'])
        return result['result']

    def guard(self, callback):
        try:
            return callback()
        except Exception as error:
            self.session.log.exception('desktop', error)
            self.statusBar().showMessage(str(error), 15000)
            return None

    def refresh_fonts(self):
        selected = self.font_choice.currentData()
        self.font_choice.blockSignals(True)
        self.font_choice.clear()
        self.font_choice.addItem('System English font', None)
        for face in self.session.fonts.faces.values():
            self.font_choice.addItem(f'{face.path.stem} · {face.sha256[:6]}', face.font_id)
        index = self.font_choice.findData(selected)
        self.font_choice.setCurrentIndex(max(0,index))
        self.font_choice.blockSignals(False)
        self._font_signature = tuple(self.session.fonts.faces)

    def sync_controls(self):
        # Reflect committed changes without erasing unsubmitted page input on
        # every caret move. Blocking signals avoids turning reads into commands.
        page = self.session.model['pages'][0]
        signature = (self.session.model['documentId'],page['widthMicroPoints'],page['heightMicroPoints'])
        if signature != self._page_signature:
            self.unit.setCurrentText('pt')
            self.width_input.setValue(int(page['widthMicroPoints'])/1_000_000)
            self.height_input.setValue(int(page['heightMicroPoints'])/1_000_000)
            self._page_signature = signature
        if tuple(self.session.fonts.faces) != self._font_signature:
            self.refresh_fonts()
        values = [(check,self.session.view[key]) for key,check in self.overlay_checks.items()]
        values += [(check,self.session.features[key]) for key,check in self.feature_checks.items()]
        recipe = self.session.fonts.recipe
        for index,check in enumerate(self.layer_checks):
            check.setEnabled(bool(recipe))
            values.append((check,bool(recipe and recipe['layers'][index]['enabled'])))
        for check,value in values:
            check.blockSignals(True)
            check.setChecked(value)
            check.blockSignals(False)
        self.zoom_control.blockSignals(True)
        self.zoom_control.setValue(round(self.session.view['zoom']*100))
        self.zoom_control.blockSignals(False)

    def on_change(self):
        self.preview.update_page()
        self.timer.start()

    def refresh(self):
        try:
            self.sync_controls()
            snapshot = layout.inspect(self.session, max_glyphs=1500)
            self.glyph_table.setRowCount(len(snapshot['glyphs']))
            for row, glyph in enumerate(snapshot['glyphs']):
                values = (f"{glyph['source']!r} · {glyph['cluster']}", glyph['glyphId'], glyph['family'],
                          str(glyph['origin']), glyph['clusterAdvance'], glyph['fallbackReason'] or '')
                for col, value in enumerate(values):
                    self.glyph_table.setItem(row, col, QTableWidgetItem(str(value)))
            self.details.setPlainText(json.dumps(snapshot, ensure_ascii=False, indent=2))
            self.logs.setPlainText('\n'.join(json.dumps(e, ensure_ascii=False) for e in self.session.log.tail(80)))
            self.access.setPlainText(json.dumps(accessibility(self.editor), ensure_ascii=False, indent=2))
            warnings = ' · '.join(d['code'] for d in snapshot['diagnostics'])
            dirty = 'unsaved' if self.session.saved_revision != self.session.revision else 'saved'
            transport = 'Live API active' if getattr(self.session, 'transport_active', False) else 'In-process API'
            self.statusBar().showMessage(f'Revision {self.session.revision} / {dirty}    {len(snapshot["glyphs"])} glyphs    {warnings}    {transport} · logs: {self.session.log.path.name}')
            self.preview.zoom = self.session.view.get('zoom', .65)
            self.preview.update_page()
        except Exception as error:
            self.session.log.exception('desktop', error)
            self.statusBar().showMessage(str(error))

    def apply_format(self):
        cursor = self.editor.textCursor()
        self.invoke('document.format', start=cursor.selectionStart(), end=cursor.selectionEnd(),
                    font_id=self.font_choice.currentData(), language=self.language.currentData(), size=self.font_size.value())
        self.editor.setFocus()

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Open lab document', str(self.session.root / '.local'), 'Vayrshemon lab (*.vaylab.json)')
        if path:
            if self.session.revision != self.session.saved_revision and self.session.revision > 0:
                if QMessageBox.question(self, 'Unsaved text', 'Open this file and discard unsaved edits?') != QMessageBox.StandardButton.Yes:
                    return
            self.invoke('document.open', path=path, discardUnsaved=True)
            self.refresh_fonts()

    def save_file(self):
        path = str(self.session.saved_path) if self.session.saved_path else QFileDialog.getSaveFileName(
            self, 'Save lab document', str(self.session.root / '.local/untitled.vaylab.json'), 'Vayrshemon lab (*.vaylab.json)')[0]
        if path:
            self.invoke('document.save', path=path)
            self.refresh()

    def load_font(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Load a local TrueType font', str(self.session.root / 'Inputs'), 'TrueType (*.ttf)')
        if path:
            self.invoke('fonts.load', path=path)
            self.refresh_fonts()

    def export_png(self):
        path, _ = QFileDialog.getSaveFileName(self, 'Export color page', str(self.session.root / '.local/page.png'), 'PNG (*.png)')
        if path:
            self.invoke('render.png', path=path, mode='color', dpi=144)

    def choose_reference(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Reference image', str(self.session.root / 'Inputs'), 'Images (*.png *.jpg *.jpeg *.bmp)')
        if path:
            self.invoke('reference.load', path=path)

    def set_reference(self, path):
        reader = QImageReader(str(path))
        reader.setAutoTransform(True)
        size = reader.size()
        if not size.isValid() or size.width()*size.height() > 200_000_000:
            raise ValueError('REFERENCE_IMAGE_INVALID_OR_TOO_LARGE')
        reader.setScaledSize(size.scaled(QSize(700, 700), Qt.AspectRatioMode.KeepAspectRatio))
        image = reader.read()
        if image.isNull():
            raise ValueError('REFERENCE_IMAGE_DECODE_FAILED: ' + reader.errorString())
        self.reference.setPixmap(QPixmap.fromImage(image).scaled(270, 480, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.reference.setAccessibleDescription(str(path))
        self.reference.setToolTip(str(path))
        self.session.log.emit('desktop', 'REFERENCE_LOADED', path=str(path))

    def closeEvent(self, event):
        if self.session.revision > 0 and self.session.revision != self.session.saved_revision:
            answer = QMessageBox.question(self, 'Unsaved document', 'Close and discard unsaved edits?',
                                          QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
        event.accept()
