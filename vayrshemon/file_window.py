"""M14 native file dialogs; the reading layout and glyph renderer are unchanged."""
from pathlib import Path
from PySide6.QtCore import QEvent,QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFileDialog,QMessageBox,QPushButton
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
    # Approved sidebar defaults; saved sidebar preferences take precedence.
    DEFAULT_SIDEBAR=dict(expanded=False,pinned=False,width=390,panel='Paint')
    SHOW_SVG_PROOF_BUTTON=False

    def build_export_menu(self,menu):
        self.export_menu=menu.addMenu('Export')
        self.png_export_action=self.export_menu.addAction('PNG…',lambda:self.guard(self.export_png))
        self.svg_export_action=self.export_menu.addAction('SVG…',lambda:self.guard(self.export_svg))
        self.svg_export_action.setToolTip('Export the visible page or both facing pages as SVG proofs. Color relief uses embedded images.')

    def export_proof(self,kind):
        if kind!='svg':return super().export_proof(kind)
        from .page_proof_export import export_pages
        return export_pages(self,kind)

    def __init__(self,book,api):
        self.workspace_layout=None
        super().__init__(book,api)
        for button in self.findChildren(QPushButton):
            if button.text() in ('Export PNG · current page','Export SVG · current page'):
                button.setText(button.text().replace('current page','current view'))
        language=self.language_menu
        language.addSeparator()
        self.update_transliteration_action=language.addAction('Update transliteration',self.update_transliteration)
        self.update_transliteration_action.setToolTip('Update the Roman column from Vayrshemon in this page or spread. Undo restores the previous text.')
        self.setWindowIcon(QIcon(str(book.root/'data/icons/memon-color.ico')))
        self.restore_saved_arrangement()
        from .workspace_layout import WorkspaceLayout
        self.workspace_layout=WorkspaceLayout(self)
        self._startup_fit=QTimer(self)
        self._startup_fit.setSingleShot(True)
        self._startup_fit.setInterval(100)
        self._startup_fit.timeout.connect(self.fit_initial_page)
        self._startup_fit_pending=not book.saved_path and book.revision==0 and not book.dirty
        self.preview.viewport().installEventFilter(self)

    def showEvent(self,event):
        super().showEvent(event)
        if self._startup_fit_pending:
            self._startup_fit.start()

    def update_transliteration(self):
        plan=self.invoke('page.transliteration.inspect')
        if not plan:return
        if not plan['changed']:
            self.statusBar().showMessage('Transliteration is already up to date.',8000)
            return
        choice=QMessageBox.question(self,'Update transliteration',
            'Replace the transliteration column with the current Vayrshemon text in Transliteration 7?\n\n'
            'This replaces any edits made directly in that column. Its formatting and Maxima are preserved; '
            'the gloss and English text stay unchanged.\n\nYou can undo the update in one step.',
            QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.Cancel,QMessageBox.StandardButton.Cancel)
        if choice!=QMessageBox.StandardButton.Yes:return
        result=self.invoke('page.transliteration.update',expected_plan=plan['planId'])
        if result:
            status=result.get('alignment',{})
            self.statusBar().showMessage('Transliteration updated. '+(status.get('message','') if status.get('status')=='paused' else 'Undo restores the previous text.'),12000)

    def eventFilter(self,target,event):
        if target is self.preview.viewport() and event.type()==QEvent.Type.Resize and self._startup_fit_pending:
            # Maximizing and the compact action bar can resize the viewport in
            # separate events. Fit once after that initial resize burst settles.
            self._startup_fit.start()
        return super().eventFilter(target,event)

    def fit_initial_page(self):
        self._startup_fit_pending=False
        self.centralWidget().layout().activate()
        if self.book.initialize_startup_zoom(self.fitted_zoom(fit_height=True)):
            self.preview.center_page()

    def configure_workspace(self,**params):
        result=super().configure_workspace(**params)
        if self.workspace_layout is not None:
            if params.get('diagnostics'):self.refresh()
            self.workspace_layout.sync(persist=any(params.get(k) is not None for k in self.workspace_layout.FIELDS))
        return result

    def restore_saved_arrangement(self):
        if self.book.saved_preview:
            self.page_controls.set_mode(self.book.saved_page_mode,persist=False)
        elif not self.book.saved_path:
            # A new blank document always starts with its one-page control
            # selected, regardless of the previous document's workspace mode.
            self.page_controls.set_mode('one',persist=False)

    def refresh(self):
        super().refresh()
        path=self.book.saved_path
        self.setWindowFilePath(str(path) if path else '')
        title=Path(path).name if path else 'Untitled'
        for suffix in ('.vaylab.json','.vay.json','.vay'):
            if path and title.lower().endswith(suffix):
                title=title[:-len(suffix)]
                break
        self.setWindowTitle(title)

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
