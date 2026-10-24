"""Readable gloss preview, editable compact labels and linked token details."""
import json
import uuid
from copy import deepcopy
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QComboBox,QPushButton,QTableWidget,QTableWidgetItem,QPlainTextEdit,QSplitter,QTabWidget,QCheckBox,QMessageBox
from .reading_window import ReadingWindow
from . import gloss


class GlossPanel(QWidget):
    def __init__(self,forge):
        super().__init__();self.forge=forge;self.profile=None;self.report=None;self.dirty=False;self.loading=False;self.value=None
        outer=QVBoxLayout(self);self.notice=QLabel('Choose a frozen language version to inspect its construction gloss. Compact labels are editorial and versioned.');self.notice.setWordWrap(True);outer.addWidget(self.notice)
        row=QHBoxLayout();self.page=QComboBox();row.addWidget(self.page,1)
        for label,fn in [('Load glossary',self.load),('Save glossary to draft',self.save),('Preview gloss',self.preview),('Create four-column copy',self.create)]:
            button=QPushButton(label);button.clicked.connect(fn);row.addWidget(button)
        outer.addLayout(row);self.tabs=QTabWidget();outer.addWidget(self.tabs,1)
        preview=QWidget();layout=QVBoxLayout(preview);split=QSplitter()
        self.prose=QPlainTextEdit();self.prose.setReadOnly(True);self.prose.setAccessibleName('Construction gloss in source order');split.addWidget(self.prose)
        self.tokens=QTableWidget(0,4);self.tokens.setHorizontalHeaderLabels(['Source word','Construction gloss','Role','Dictionary entry']);self.tokens.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers);self.tokens.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows);self.tokens.itemSelectionChanged.connect(self.details);split.addWidget(self.tokens)
        layout.addWidget(split,2);self.explanation=QPlainTextEdit();self.explanation.setReadOnly(True);layout.addWidget(self.explanation,1);self.tabs.addTab(preview,'Reading and word details')
        editor=QWidget();edit_layout=QVBoxLayout(editor);self.simple=QCheckBox('Show simple aspect (simp.) explicitly');self.simple.setChecked(True);edit_layout.addWidget(self.simple)
        self.entries=QTableWidget(0,4);self.entries.setHorizontalHeaderLabels(['Dictionary entry','Compact label','Inherent tags','Explanation']);edit_layout.addWidget(self.entries);self.tabs.addTab(editor,'Compact glossary')
        self.entries.itemChanged.connect(self.changed);self.simple.toggled.connect(self.changed)
        self.legend=QLabel(' · '.join(k+' '+v for k,v in gloss.TAGS.items()));self.legend.setWordWrap(True);outer.addWidget(self.legend);self.refresh()

    def refresh(self):
        if self.dirty or not self.forge.value:return
        self.profile=None;self.value=None;self.report=None;self.entries.setRowCount(0);self.prose.clear();self.tokens.setRowCount(0);self.explanation.clear()
        self.entries.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers if self.forge.version else QTableWidget.EditTrigger.DoubleClicked|QTableWidget.EditTrigger.EditKeyPressed)
        self.simple.setEnabled(not self.forge.version)
        old=self.page.currentData();self.page.clear()
        for t in self.forge.value['snapshot']['tests']:
            if t.get('caseIds'):self.page.addItem(t['title'],t['id'])
        self.page.setCurrentIndex(max(0,self.page.findData(old)))

    def changed(self,*_):
        if not self.loading and self.profile and not self.forge.version:
            self.dirty=True;self.notice.setText('Unsaved compact glossary. Save to the draft; invalid or stale edits are retained for correction.')

    def params(self):
        value=dict(test_id=self.page.currentData())
        if self.forge.version:value['version']=self.forge.version
        return value

    def load(self):
        f=self.forge
        if not f.flush() or not self.page.currentData():return
        params=self.params();value=f.call('forge.gloss.read',**({k:v for k,v in params.items() if k=='version'}))
        if not value:return
        p=value['profile'] or f.call('forge.gloss.prepare',**params)
        if not p:return
        self.loading=True;self.profile=deepcopy(p);self.value=deepcopy(f.value);self.simple.setChecked(p['showSimpleAspect']);self.entries.setRowCount(len(p['entries']))
        for row,(eid,item) in enumerate(p['entries'].items()):
            for col,text in enumerate((eid,item['label'],','.join(item['tags']),item['note'])):
                cell=QTableWidgetItem(text)
                if col==0:cell.setFlags(cell.flags()&~Qt.ItemFlag.ItemIsEditable)
                self.entries.setItem(row,col,cell)
        self.loading=False;self.dirty=not value['profile'] and not f.version
        self.entries.resizeColumnsToContents();self.tabs.setCurrentIndex(1);self.notice.setText('Edit labels and tags, save to a working draft, then commit in Versions. Existing versions and pages stay unchanged.')

    def save(self):
        f=self.forge
        if not self.dirty:return True
        if not self.profile or not self.value or f.version:return False
        p=deepcopy(self.profile);p['showSimpleAspect']=self.simple.isChecked()
        for row in range(self.entries.rowCount()):
            eid=self.entries.item(row,0).text();item=p['entries'][eid]
            item.update(label=self.entries.item(row,1).text().strip(),tags=[x.strip() for x in self.entries.item(row,2).text().split(',') if x.strip()],note=self.entries.item(row,3).text())
        r=f.call('forge.gloss.put',project_id=self.value['projectId'],expected_generation=self.value['generation'],profile=p)
        if r:
            self.dirty=False;f.refresh();self.notice.setText('Glossary saved to the draft. Commit it in Versions before creating a spread.');return True
        self.notice.setText('Save failed; your edits are retained. See the error below.');return False

    def preview(self):
        if not self.forge.flush() or not self.page.currentData():return
        r=self.forge.call('forge.gloss.inspect',**self.params())
        if not r:return
        self.report=r;self.rows=[dict(paragraph=p['index'],caseId=c['caseId'],adaptation=p['adaptation'],**t) for p in r['paragraphs'] for c in p['clauses'] for t in c['tokens']]
        self.prose.setPlainText('\n\n'.join(p['text'] for p in r['paragraphs']));self.tokens.setRowCount(len(self.rows))
        from . import reading
        try:source_font=QFont(reading.font(self.forge.book,'transliteration').family,18)
        except (ValueError,FileNotFoundError):source_font=None
        for row,t in enumerate(self.rows):
            for col,key in enumerate(('surface','gloss','role','entryId')):
                cell=QTableWidgetItem(t[key])
                if col==0 and source_font:cell.setFont(source_font)
                self.tokens.setItem(row,col,cell)
        self.tokens.resizeColumnsToContents();self.tabs.setCurrentIndex(0)
        self.notice.setText(str(r['tokenCount'])+' linked words · '+r['scope']+(' Simple aspect is implicit unless marked otherwise.' if not r['showSimpleAspect'] else ''))
        self.legend.setText(' · '.join(k+' '+v for k,v in r['legend'].items()))
        if self.rows:self.tokens.selectRow(0)

    def details(self):
        if not self.report or self.tokens.currentRow()<0:return
        t=self.rows[self.tokens.currentRow()]
        self.explanation.setPlainText(t['surface']+' → '+t['gloss']+'\n'+t['definition']+'\n'+t['etymology']+'\n'+t['note']+'\n'+t['prefixNote']+'\n\nEnglish adaptation: '+t['adaptation']+'\n\nPinned references:\n'+json.dumps({k:v for k,v in t.items() if k in ('entryId','senseId','sourceScalar','sourceUtf16','analyses','context')},ensure_ascii=False,indent=2))

    def create(self):
        f=self.forge
        if not f.flush() or not f.value or not self.page.currentData():return
        if not f.version and f.value['dirty']:self.notice.setText('Commit the draft in Versions first.');return
        result=f.call('page.gloss.copy',version=f.version or f.value['head'],test_id=self.page.currentData(),directory=str(f.book.root/'.local/gloss-copies'/uuid.uuid4().hex))
        if result and result.get('document'):f.call('forge.run.open',run_id=result['runId'])


class GlossWindow(ReadingWindow):
    def __init__(self,book,api):
        super().__init__(book,api);self.forge_panel.gloss=GlossPanel(self.forge_panel);self.forge_panel.tabs.insertTab(6,self.forge_panel.gloss,'Gloss')

    def about(self):
        from .paint import ENGINE_VERSION
        QMessageBox.about(self,'About Vayrshemon',f'Vayrshemon\nM13 · {self.book.application_version}\nPaint engine {ENGINE_VERSION}\nVersioned construction glosses')

    def export_proof(self,kind):
        if kind!='png':return super().export_proof(kind)
        from .png_export import export_png
        return export_png(self)

    def show_forge(self,gloss_test=None,gloss_preview=False,**params):
        result=super().show_forge(**params);panel=self.forge_panel.gloss
        if gloss_test:
            i=panel.page.findData(gloss_test)
            if i<0:raise ValueError('GLOSS_BOUND_TEST_REQUIRED')
            panel.page.setCurrentIndex(i)
        if gloss_preview:panel.preview()
        return result
