"""M6.1 workspace-only controls; never change a document or its zoom."""
from PySide6.QtCore import QEvent, QTimer, Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QMenu, QToolButton, QVBoxLayout, QWidget
from tools.m0.common import load_json, write_json


class SidebarDock(QWidget):
    RAIL = 40
    MIN_WIDTH = 320
    MAX_WIDTH = 560

    def __init__(self, window):
        super().__init__()
        self.owner = window
        self.tabs = window.sidebar
        self.splitter = self.tabs.parentWidget()
        self.path = window.book.root / '.local/workspace/sidebar.json'
        self.preference_error = None
        self.expanded = True
        self.pinned = True
        self.expanded_width = 390
        self._placing = True
        self._ready = False
        self.setObjectName('workspaceSidebar')
        self.setAccessibleName('Collapsible workbench controls')

        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.setInterval(150)
        self.save_timer.timeout.connect(self.persist)
        self.collapse_timer = QTimer(self)
        self.collapse_timer.setSingleShot(True)
        self.collapse_timer.timeout.connect(self.collapse_temporary)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        rail = QWidget()
        rail.setFixedWidth(self.RAIL)
        rail_layout = QVBoxLayout(rail)
        rail_layout.setContentsMargins(2, 0, 4, 0)
        self.toggle_button = QToolButton()
        self.toggle_button.setFixedSize(32, 30)
        self.toggle_button.clicked.connect(self.toggle)
        rail_layout.addWidget(self.toggle_button)
        rail_layout.addStretch()
        layout.addWidget(rail)
        self.body = QWidget()
        body_layout = QVBoxLayout(self.body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(5)
        header = QHBoxLayout()
        header.addWidget(QLabel('CONTROLS'))
        header.addStretch()
        self.pin_button = QToolButton()
        self.pin_button.setCheckable(True)
        self.pin_button.setAccessibleName('Pin controls panel open')
        self.pin_button.setToolTip('Keep controls open · Ctrl+Alt+P')
        self.pin_button.clicked.connect(lambda checked: window.invoke('ui.sidebar', pinned=checked))
        header.addWidget(self.pin_button)
        body_layout.addLayout(header)
        layout.addWidget(self.body, 1)
        # Replace before reparenting the existing tabs, retaining all controls.
        self.splitter.replaceWidget(0, self)
        self.splitter.setCollapsible(0, False)
        self.tabs.setMinimumWidth(280)
        self.tabs.setMaximumWidth(self.MAX_WIDTH - self.RAIL)
        body_layout.addWidget(self.tabs)

        self.load_preferences()
        self.apply_geometry()
        self._ready = True
        self._placing = False
        self.tabs.currentChanged.connect(lambda _: self.persist())
        for target in (window.preview.viewport(), window.editor.viewport()):
            target.installEventFilter(self)
        self.view_menu = next(menu for menu in window.findChildren(QMenu) if menu.title() == 'View')
        for text, shortcut, callback in (
            ('Expand or collapse controls', 'Ctrl+Alt+B', self.toggle),
            ('Pin or unpin controls', 'Ctrl+Alt+P', self.toggle_pin),
        ):
            action = QAction(text, window)
            action.setShortcut(QKeySequence(shortcut))
            action.triggered.connect(callback)
            window.addAction(action)
            # Existing View menu remains the single menu for workspace controls.
            self.view_menu.addAction(action)
        self.splitter.splitterMoved.connect(self.remember_width)

    def inspect(self):
        return dict(expanded=self.expanded, pinned=self.pinned, width=self.expanded_width,
                    actualWidth=self.width(), panel=self.tabs.tabText(self.tabs.currentIndex()),
                    state='pinned' if self.pinned else 'temporary' if self.expanded else 'collapsed',
                    preferencePath=str(self.path), preferenceError=self.preference_error,
                    toggleShortcut='Ctrl+Alt+B', pinShortcut='Ctrl+Alt+P')

    def load_preferences(self):
        if not self.path.exists():
            return
        try:
            if self.path.stat().st_size > 8192:
                raise ValueError('SIDEBAR_PREFERENCES_TOO_LARGE')
            value = load_json(self.path)
            if not isinstance(value, dict) or set(value) != {'version', 'expanded', 'pinned', 'width', 'panel'}:
                raise ValueError('INVALID_SIDEBAR_PREFERENCES')
            if (value['version'] != '1.0.0' or type(value['expanded']) is not bool or
                type(value['pinned']) is not bool or type(value['width']) is not int or
                not self.MIN_WIDTH <= value['width'] <= self.MAX_WIDTH or
                (value['pinned'] and not value['expanded'])):
                raise ValueError('INVALID_SIDEBAR_PREFERENCES')
            names = [self.tabs.tabText(i) for i in range(self.tabs.count())]
            if value['panel'] not in names:
                raise ValueError('UNKNOWN_SAVED_SIDEBAR_PANEL')
            self.expanded, self.pinned, self.expanded_width = value['expanded'], value['pinned'], value['width']
            self.tabs.setCurrentIndex(names.index(value['panel']))
        except Exception as error:
            self.preference_error = str(error)
            self.owner.book.log.exception('workspace', error)
            self.owner.statusBar().showMessage('Controls preferences could not be loaded: ' + str(error), 15000)

    def persist(self):
        if not self._ready:
            return
        self.save_timer.stop()
        try:
            write_json(self.path, dict(version='1.0.0', expanded=self.expanded, pinned=self.pinned,
                       width=self.expanded_width, panel=self.tabs.tabText(self.tabs.currentIndex())))
            self.preference_error = None
        except Exception as error:
            self.preference_error = str(error)
            self.owner.book.log.exception('workspace', error)
            self.owner.statusBar().showMessage('Controls preferences could not be saved: ' + str(error), 15000)

    def apply_geometry(self):
        self._placing = True
        sizes = self.splitter.sizes()
        old_width = sizes[0]
        self.body.setVisible(self.expanded)
        self.setMinimumWidth(self.MIN_WIDTH if self.expanded else self.RAIL)
        self.setMaximumWidth(self.MAX_WIDTH if self.expanded else self.RAIL)
        target = self.expanded_width if self.expanded else self.RAIL
        # Give released space to the preview; keep the source editor's width.
        sizes[0] = target
        sizes[-1] = max(1, sizes[-1] + old_width - target)
        self.splitter.setSizes(sizes)
        self.toggle_button.setText('‹' if self.expanded else '›')
        label = 'Collapse controls' if self.expanded else 'Expand controls'
        self.toggle_button.setAccessibleName(label)
        self.toggle_button.setToolTip(label + ' · Ctrl+Alt+B')
        self.pin_button.setChecked(self.pinned)
        self.pin_button.setText('Pinned' if self.pinned else 'Pin')
        self.pin_button.setAccessibleDescription('Pinned open' if self.pinned else 'Closes when you click the page or source editor')
        self._placing = False

    def configure(self, expanded=None, pinned=None, width=None):
        if expanded is False and pinned is True:
            raise ValueError('SIDEBAR_STATE_CONFLICT: a pinned panel must be expanded')
        if width is not None and (type(width) is not int or not self.MIN_WIDTH <= width <= self.MAX_WIDTH):
            raise ValueError('SIDEBAR_WIDTH_RANGE: expected 320 through 560 logical pixels')
        if width is not None:
            self.expanded_width = width
        if pinned is not None:
            self.pinned = pinned
            if pinned:
                self.expanded = True
        if expanded is not None:
            self.expanded = expanded
            if not expanded:
                self.pinned = False
        focus = QApplication.focusWidget()
        if not self.expanded and focus and self.body.isAncestorOf(focus):
            self.owner.preview.setFocus()
        self.apply_geometry()
        self.persist()
        return self.inspect()

    def toggle(self):
        self.owner.invoke('ui.sidebar', expanded=not self.expanded)

    def toggle_pin(self):
        self.owner.invoke('ui.sidebar', pinned=not self.pinned)

    def remember_width(self, *_):
        if self._ready and self.expanded and not self._placing:
            self.expanded_width = min(self.MAX_WIDTH, max(self.MIN_WIDTH, self.width()))
            self.save_timer.start()

    def eventFilter(self, target, event):
        # Only explicit clicks into the page/source dismiss a temporary panel.
        # Focus changes, popup choices, typing, menus and IME do not dismiss it.
        if (event.type() == QEvent.Type.MouseButtonPress and self.expanded and not self.pinned
                and QApplication.activePopupWidget() is None and QApplication.activeModalWidget() is None):
            self.collapse_timer.start(0)
        return super().eventFilter(target, event)

    def collapse_temporary(self):
        if self.expanded and not self.pinned:
            self.owner.invoke('ui.sidebar', expanded=False)
