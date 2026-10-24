"""Remember reading/diagnostic panes independently of saved documents."""
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu
from tools.m0.common import load_json, write_json


class WorkspaceLayout:
    FIELDS = ('source', 'diagnostics', 'guides')

    def __init__(self, window):
        self.window = window
        self.path = window.book.root / '.local/workspace/layout.json'
        self.error = None
        self.actions = {}
        menu = next(m for m in window.findChildren(QMenu) if m.title() == 'View')
        menu.addSeparator()
        for key, label in zip(self.FIELDS, ('Source editor', 'Diagnostics panels', 'Page guides')):
            action = QAction(label, window)
            action.setCheckable(True)
            action.triggered.connect(lambda checked, field=key: window.invoke('ui.workspace', **{field: checked}))
            menu.addAction(action)
            self.actions[key] = action
        value = dict.fromkeys(self.FIELDS, False)
        if self.path.exists():
            try:
                if self.path.stat().st_size > 8192:
                    raise ValueError('WORKSPACE_LAYOUT_TOO_LARGE')
                saved = load_json(self.path)
                if (not isinstance(saved, dict) or set(saved) != {'version', *self.FIELDS} or
                        saved['version'] != '1.0.0' or any(type(saved[k]) is not bool for k in self.FIELDS)):
                    raise ValueError('INVALID_WORKSPACE_LAYOUT')
                value = {k: saved[k] for k in self.FIELDS}
            except Exception as error:
                self.report_error('loaded', error)
        # No fitting/zoom change and no preference write during restoration.
        window.configure_workspace(**value)
        self.sync()

    def report_error(self, operation, error):
        self.error = str(error)
        self.window.book.log.exception('workspace', error)
        self.window.statusBar().showMessage('Workspace preferences could not be ' + operation + ': ' + str(error), 15000)

    def sync(self, persist=False):
        state = self.window.workspace_state()
        value = {k: state[k] for k in self.FIELDS}
        for key, action in self.actions.items():
            action.setChecked(value[key])
        if persist:
            try:
                write_json(self.path, dict(version='1.0.0', **value))
                self.error = None
            except Exception as error:
                self.report_error('saved', error)
