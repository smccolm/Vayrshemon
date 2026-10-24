"""Explicit English, transliteration-font and literal Roman reading copies."""
import uuid
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QBoxLayout,QLabel,QComboBox,QPushButton,QPlainTextEdit,QSplitter,QMessageBox
from .spelling_window import SpellingWindow
from . import reading


class ReadingPanel(QWidget):
    def __init__(self,forge):
        super().__init__();self.forge=forge;outer=QVBoxLayout(self)
        self.notice=QLabel('Thimfora on the left; the same symbol slots and case in your Roman font on the right. English remains in the versioned test.');self.notice.setWordWrap(True);outer.addWidget(self.notice)
        row=QHBoxLayout();self.page=QComboBox();row.addWidget(self.page,1);self.mode=QComboBox()
        for mode,label in reading.MODES.items():self.mode.addItem(label,mode)
        self.mode.setCurrentIndex(1);row.addWidget(self.mode)
        for label,fn in [('Enable profile',self.enable),('Preview reading',self.preview),('Run in Workbench',self.run)]:
            b=QPushButton(label);b.clicked.connect(fn);row.addWidget(b)
        outer.addLayout(row);split=QSplitter();self.left=QPlainTextEdit();self.right=QPlainTextEdit()
        for edit in (self.left,self.right):edit.setReadOnly(True);split.addWidget(edit)
        outer.addWidget(split,1);self.refresh()

    def refresh(self):
        if not self.forge.value:return
        old=self.page.currentData();self.page.clear()
        for t in self.forge.value['snapshot']['tests']:self.page.addItem(t['title'],t['id'])
        self.page.setCurrentIndex(max(0,self.page.findData(old)))

    def enable(self):
        if self.forge.version:self.notice.setText('Select the working draft to enable the reading profile.');return
        if self.forge.value and self.forge.flush():self.forge.call('forge.reading.enable',project_id=self.forge.value['projectId'],expected_generation=self.forge.guard())

    def preview(self):
        if not self.forge.flush() or not self.page.currentData():return
        params=dict(test_id=self.page.currentData(),mode=self.mode.currentData())
        if self.forge.version:params['version']=self.forge.version
        r=self.forge.call('forge.reading.inspect',**params)
        if not r:return
        try:
            book=self.forge.book;left=book.fonts.resolve('font:'+reading.SCRIPT_SHA+':0');right=reading.font(book,self.mode.currentData())
            # The workbench's global widget stylesheet otherwise overrides setFont.
            for edit,family,size in ((self.left,left.family,28),(self.right,right.family if right else 'Times New Roman',22)):
                edit.setStyleSheet(f'QPlainTextEdit {{font-family:"{family}";font-size:{size}pt;}}')
                edit.setFont(QFont(family,size));edit.document().setDefaultFont(QFont(family,size))
            self.left.setPlainText('\n\n'.join(p['left'] for p in r['paragraphs']));self.right.setPlainText('\n\n'.join(p['right'] for p in r['paragraphs']))
            self.notice.setText(f"{sum(p['maxima'] for p in r['paragraphs'])} Maxima preserved · "+r['scope'])
        except (ValueError,OSError) as error:self.notice.setText('Font unavailable: '+str(error))

    def run(self):
        f=self.forge
        if not f.flush() or not f.value or not self.page.currentData():return
        if not f.version and f.value['dirty']:self.notice.setText('Commit the draft first to freeze its text, rules and reading profile.');return
        r=f.call('forge.test.run',version=f.version or f.value['head'],test_id=self.page.currentData(),reading_mode=self.mode.currentData(),directory=str(f.book.root/'.local/forge-runs'/uuid.uuid4().hex))
        if r and r.get('document'):f.call('forge.run.open',run_id=r['runId'])


class ReadingWindow(SpellingWindow):
    def __init__(self,book,api):
        super().__init__(book,api);self.forge_panel.reading=ReadingPanel(self.forge_panel);self.forge_panel.tabs.insertTab(5,self.forge_panel.reading,'Reading')
        row=self.preview.parentWidget().layout().itemAt(1).layout();self.reading_mode=QComboBox()
        for mode in ('transliteration','literal'):self.reading_mode.addItem(reading.MODES[mode],mode)
        button=QPushButton('Create reading copy');button.clicked.connect(self.reading_copy)
        width=next(b for b in self.findChildren(QPushButton) if b.text()=='Fit Width');index=row.indexOf(width)+1;row.insertSpacing(index,12)
        for offset,widget in enumerate((QLabel('Reading copy'),self.reading_mode,button),index+1):row.insertWidget(offset,widget)
        for label in self.forge_panel.findChildren(QLabel):
            if label.text().startswith('LANGUAGE FORGE  /'):label.setText('LANGUAGE FORGE')
        self.compact_actions(row)
        from .page_controls import PageControls
        self.page_controls=PageControls(self)
        self.menuBar().addMenu('Help').addAction('About Vayrshemon',self.about)
        self.refresh()

    def compact_actions(self,row):
        workbench=self.workspace_tabs.widget(0);top=workbench.layout().itemAt(0).layout()
        files=QWidget();file_row=QHBoxLayout(files);file_row.setContentsMargins(0,0,0,0);file_row.addStretch()
        while top.count():
            item=top.takeAt(0);widget=item.widget()
            if isinstance(widget,QPushButton):file_row.addWidget(widget)
            elif widget:widget.hide()
        preview=self.preview.parentWidget().layout();preview.removeItem(row)
        header=preview.takeAt(0).layout();header.removeWidget(self.mode);self.preview_hint.hide()
        self.mode.setFixedWidth(210);self.mode.setToolTip('Color / relief, white on black, or black on white. Proofs use this choice.')
        row.insertWidget(row.count()-1,self.mode)
        navigation=QWidget();navigation.setLayout(row);row.setContentsMargins(0,0,0,0)
        top.addWidget(navigation,1);top.addWidget(files)
        self.action_bar=top;self.action_groups=(navigation,files)
        for tool,button in self.tool_buttons.items():
            button.setToolTip('Click a frame to edit · Ctrl+Alt+V' if tool=='select' else 'Drag to move the view · Ctrl+Alt+H')
        self.resize_actions()

    def resize_actions(self):
        if not hasattr(self,'action_bar'):return
        needed=sum(w.minimumSizeHint().width() for w in self.action_groups)+40
        self.action_bar.setDirection(QBoxLayout.Direction.LeftToRight if self.workspace_tabs.width()>=needed else QBoxLayout.Direction.TopToBottom)

    def resizeEvent(self,event):
        super().resizeEvent(event);self.resize_actions()

    def about(self):
        from .paint import ENGINE_VERSION
        QMessageBox.about(self,'About Vayrshemon',f'Vayrshemon\nM12 · {self.book.application_version}\nPaint engine {ENGINE_VERSION}\nLanguage Workbench and Language Forge')

    def reading_copy(self):
        r=self.invoke('page.reading.copy',mode=self.reading_mode.currentData(),directory=str(self.book.root/'.local/reading-copies'/uuid.uuid4().hex))
        if r and r.get('document'):self.open_path(r['document'])

    def refresh(self):
        super().refresh();self.setWindowTitle(self.book.state['title']+(' *' if self.book.dirty else '')+' — Vayrshemon')

    def show_forge(self,reading_test=None,reading_mode=None,reading_preview=False,**params):
        result=super().show_forge(**params);p=self.forge_panel.reading
        if reading_test:
            i=p.page.findData(reading_test)
            if i<0:raise ValueError('READING_PAGE_MISSING')
            p.page.setCurrentIndex(i)
        if reading_mode:p.mode.setCurrentIndex(p.mode.findData(reading_mode))
        if reading_preview:p.preview()
        return result
