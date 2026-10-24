"""M14 native file dialogs; the reading layout and glyph renderer are unchanged."""
from pathlib import Path
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFileDialog,QMessageBox
from .gloss_window import GlossWindow


def saves_directory(book):
    path=book.root/'Saves'
    path.mkdir(parents=True,exist_ok=True)
    return path


def suggested_path(book):
    value=Path(book.saved_path).name if book.saved_path else 'Untitled.vay'
    for suffix in ('.vaylab.json','.vay.json'):
        if value.lower().endswith(suffix):
            value=value[:-len(suffix)]+'.vay'
            break
    return str(saves_directory(book)/value)


class FileWindow(GlossWindow):
    def __init__(self,book,api):
        self.workspace_layout=None
        super().__init__(book,api)
        self.setWindowIcon(QIcon(str(book.root/'data/icons/memon-color.ico')))
        self.restore_saved_arrangement()
        from .workspace_layout import WorkspaceLayout
        self.workspace_layout=WorkspaceLayout(self)

    def configure_workspace(self,**params):
        result=super().configure_workspace(**params)
        if self.workspace_layout is not None:
            if params.get('diagnostics'):self.refresh()
            self.workspace_layout.sync(persist=any(params.get(k) is not None for k in self.workspace_layout.FIELDS))
        return result

    def restore_saved_arrangement(self):
        if self.book.saved_preview:self.invoke('view.pages',mode=self.book.saved_page_mode)

    def refresh(self):
        super().refresh()
        path=self.book.saved_path
        self.setWindowFilePath(str(path) if path else '')
        self.setWindowTitle((Path(path).name if path else 'Untitled')+(' *' if self.book.dirty else '')+' — Vayrshemon')

    def open_file(self):
        path,_=QFileDialog.getOpenFileName(self,'Open document',str(saves_directory(self.book)),'Vayrshemon (*.vay *.vay.json *.vaylab.json)')
        if path:self.open_path(path)

    def save_as(self):
        path,_=QFileDialog.getSaveFileName(self,'Save document as',suggested_path(self.book),'Vayrshemon document (*.vay)')
        if path:
            if not path.lower().endswith(('.vay','.vay.json')):path+='.vay'
            self.invoke('document.save-as',path=path)

    def about(self):
        from .paint import ENGINE_VERSION
        QMessageBox.about(self,'About Vayrshemon',f'Vayrshemon\nM14 · {self.book.application_version}\nPaint engine {ENGINE_VERSION}\n.vay documents · Memon icons · saved page thumbnails')
