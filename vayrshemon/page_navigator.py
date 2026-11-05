"""Page turns share the existing frame selection, without creating text edits."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit, QPushButton


class PageNumberEdit(QLineEdit):
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.parent().navigator.sync(force=True)
            self.clearFocus()
            event.accept()
            return
        super().keyPressEvent(event)


class PageNavigator:
    def __init__(self, window):
        self.window = window
        self.signature = None
        self.bar = QWidget()
        self.bar.navigator = self
        self.bar.setObjectName('pageNavigator')
        row = QHBoxLayout(self.bar)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)
        self.previous = QPushButton('<')
        self.number = PageNumberEdit()
        self.number.setObjectName('pageNumber')
        self.number.setAccessibleName('Page number')
        self.number.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.number.setMaxLength(10)
        self.number.returnPressed.connect(self.enter_page)
        self.number.editingFinished.connect(self.finish_entry)
        self.total = QLabel()
        self.next = QPushButton('>')
        for button, direction in ((self.previous, 'previous'), (self.next, 'next')):
            button.setFixedSize(30, 30)
            button.setObjectName(direction + 'Page')
            button.clicked.connect(lambda checked=False, d=direction: window.invoke('view.page', direction=d))
        for widget in (self.previous, QLabel('Page'), self.number, self.total, self.next):
            row.addWidget(widget)
        index = window.zoom_row.indexOf(window.page_controls.buttons['two']) + 1
        window.zoom_row.insertSpacing(index, 12)
        window.zoom_row.insertWidget(index + 1, self.bar)
        self.sync(force=True)

    def inspect(self):
        book = self.window.book
        pages = book.state['pages']
        current = book.current_page()['pageId']
        index = next(i for i, page in enumerate(pages) if page['pageId'] == current)
        step = 2 if self.window.preview.page_mode == 'two' else 1
        start = index // step * step
        return dict(pageNumber=index + 1, pageCount=len(pages),
                    visiblePageNumbers=list(range(start + 1, min(start + step, len(pages)) + 1)),
                    canPrevious=start > 0, canNext=start + step < len(pages))

    def sync(self, force=False):
        value = self.inspect()
        signature = (self.window.book.state['documentId'], self.window.book.current_page()['pageId'],
                     value['pageCount'], self.window.preview.page_mode)
        if force or signature != self.signature:
            self.number.setText(str(value['pageNumber']))
            self.number.setModified(False)
            self.signature = signature
        self.total.setText('of ' + str(value['pageCount']))
        self.number.setFixedWidth(max(38, self.number.fontMetrics().horizontalAdvance('0' * len(str(value['pageCount']))) + 20))
        self.number.setToolTip(f"Enter a page from 1 to {value['pageCount']}, then press Enter.")
        for button, enabled, direction in ((self.previous, value['canPrevious'], 'Previous'),
                                            (self.next, value['canNext'], 'Next')):
            label = direction + (' page pair' if self.window.preview.page_mode == 'two' else ' page')
            button.setEnabled(enabled)
            button.setAccessibleName(label)
            button.setToolTip(label)
        zoom = round(self.window.preview.zoom * 100)
        self.window.zoom.blockSignals(True)
        self.window.zoom.setValue(zoom)
        self.window.zoom.blockSignals(False)
        self.window.zoom_label.setText(str(zoom) + '%')

    def finish_entry(self):
        if not self.number.hasFocus():
            self.sync(force=True)

    def enter_page(self):
        text = self.number.text().strip()
        count = self.inspect()['pageCount']
        if not text.isascii() or not text.isdecimal() or not 1 <= int(text) <= count:
            self.sync(force=True)
            self.number.selectAll()
            self.window.statusBar().showMessage(f'Enter a whole page number from 1 to {count}.', 8000)
            return
        result = self.window.invoke('view.page', page=int(text))
        if result is not None:
            self.sync(force=True)
            self.number.selectAll()

    def navigate(self, page=None, direction=None):
        value = self.inspect()
        if direction is not None:
            if not value['canPrevious' if direction == 'previous' else 'canNext']:
                return self.window.preview.navigation_state()
            step = 2 if self.window.preview.page_mode == 'two' else 1
            page = value['visiblePageNumbers'][0] + (-step if direction == 'previous' else step)
        if type(page) is not int or not 1 <= page <= value['pageCount']:
            raise ValueError(f"PAGE_NUMBER_RANGE: enter 1 through {value['pageCount']}")
        if page != value['pageNumber']:
            target = self.window.book.state['pages'][page - 1]
            # Existing selection advances the API guard clock and checkpoints
            # the active frame, but changes neither content nor Undo history.
            self.window.api.dispatch('frame.select', dict(frame_id=target['frames'][0]['frameId']))
            self.window.refresh()
        self.reframe()
        self.sync(force=True)
        return self.window.preview.navigation_state()

    def reframe(self):
        canvas = self.window.preview
        canvas.center_page()
        if canvas.fit_mode == 'width':
            canvas.verticalScrollBar().setValue(0)

