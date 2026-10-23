"""A full-sized Forge workspace, beside the untouched page workbench."""
from copy import deepcopy
import json
from pathlib import Path
from PySide6.QtCore import Qt,QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QTabWidget,QLabel,QPushButton,
    QComboBox,QLineEdit,QPlainTextEdit,QTextBrowser,QSplitter,QListWidget,QTableWidget,
    QTableWidgetItem,QFormLayout,QFileDialog,QInputDialog,QMessageBox,QHeaderView)
from .reliability_window import ReliabilityWindow


class ForgePanel(QWidget):
    def __init__(self,window):
        super().__init__();self.window=window;self.api=window.api;self.book=window.book
        self.value=None;self.version=None;self.loading=False;self.pending=None;self.selection=None
        self.timer=QTimer(self);self.timer.setSingleShot(True);self.timer.setInterval(700);self.timer.timeout.connect(self.save_pending)
        outer=QVBoxLayout(self);outer.setContentsMargins(20,12,20,12)
        header=QHBoxLayout();title=QLabel('LANGUAGE FORGE  /  M7');title.setStyleSheet('font-size:20px;font-weight:600;color:#256089');header.addWidget(title);header.addStretch()
        for label,fn in [('New project',self.new_project),('Open project',self.open_project),('Reload draft',self.reload),('Export history',self.export_project)]: header.addWidget(self.button(label,fn))
        outer.addLayout(header);self.status=QLabel('Open or create a language project. Workbench documents keep their own history.');self.status.setWordWrap(True);outer.addWidget(self.status)
        bar=QHBoxLayout();bar.addWidget(QLabel('Branch'));self.branches=QComboBox();self.branches.setMinimumWidth(170);self.branches.activated.connect(self.checkout);bar.addWidget(self.branches)
        bar.addWidget(self.button('Branch from version…',self.branch));bar.addWidget(QLabel('Version'));self.versions=QComboBox();self.versions.setMinimumWidth(340);self.versions.activated.connect(self.select_version);bar.addWidget(self.versions,1)
        bar.addWidget(self.button('Commit version…',self.commit));outer.addLayout(bar)
        self.tabs=QTabWidget();outer.addWidget(self.tabs,1)
        self.history=QTextBrowser();self.tabs.addTab(self.history,'Versions')
        dictionary=QWidget();dl=QVBoxLayout(dictionary);self.search=QLineEdit();self.search.setPlaceholderText('Search headword, English meaning, pronunciation or stable ID');self.search.textChanged.connect(self.fill_dictionary);dl.addWidget(self.search)
        split=QSplitter();dl.addWidget(split,1);self.table=QTableWidget(0,4);self.table.setHorizontalHeaderLabels(['Headword / slots','Meaning','Evidence','Stable ID']);self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows);self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers);self.table.horizontalHeader().setSectionResizeMode(1,QHeaderView.ResizeMode.Stretch);self.table.itemSelectionChanged.connect(self.select_entry);split.addWidget(self.table)
        detail=QWidget();form=QFormLayout(detail);self.fields={}
        self.entry_script=QLabel();self.entry_script.setMinimumHeight(58);self.entry_script.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse);form.addRow('Script preview',self.entry_script)
        for key,label in [('headword','Headword'),('pronunciation','Transliteration'),('partOfSpeech','Part of speech'),('definition','First sense')]:
            edit=QLineEdit();self.fields[key]=edit;form.addRow(label,edit);edit.textEdited.connect(lambda _,k=key:self.queue('lexicon'))
        self.entry_notes=QPlainTextEdit();self.entry_notes.setReadOnly(True);form.addRow('Provenance',self.entry_notes);split.addWidget(detail);split.setSizes([760,400]);self.tabs.addTab(dictionary,'Dictionary')
        wiki=QSplitter();self.wiki_list=QListWidget();self.wiki_list.currentRowChanged.connect(self.select_wiki);wiki.addWidget(self.wiki_list)
        editpanel=QWidget();el=QVBoxLayout(editpanel);self.wiki_title=QLineEdit();self.wiki_title.setPlaceholderText('Wiki page title');el.addWidget(self.wiki_title)
        panes=QSplitter();self.wiki_editor=QPlainTextEdit();self.wiki_editor.setAccessibleName('Versioned grammar wiki editor');self.wiki_editor.setPlaceholderText('Select a wiki page. Markdown is stored with this language version.');panes.addWidget(self.wiki_editor);self.wiki_preview=QTextBrowser();self.wiki_preview.setOpenExternalLinks(False);panes.addWidget(self.wiki_preview);el.addWidget(panes,1)
        el.addWidget(self.button('New wiki page…',self.new_wiki));wiki.addWidget(editpanel);wiki.setSizes([230,1000]);self.tabs.addTab(wiki,'Wiki')
        self.wiki_title.textEdited.connect(lambda _:self.queue('wiki'));self.wiki_editor.textChanged.connect(self.wiki_changed)
        tests=QWidget();tl=QVBoxLayout(tests);self.test_list=QListWidget();tl.addWidget(self.test_list);tr=QHBoxLayout();tr.addWidget(self.button('Run frozen version in Workbench',self.run_test));tr.addWidget(self.button('Open selected run',self.open_run));tr.addStretch();tl.addLayout(tr)
        self.run_list=QListWidget();tl.addWidget(self.run_list);self.run_detail=QPlainTextEdit();self.run_detail.setReadOnly(True);tl.addWidget(self.run_detail);self.run_list.currentRowChanged.connect(self.show_run);self.tabs.addTab(tests,'Tests')
        self.research=QPlainTextEdit();self.research.setReadOnly(True);self.tabs.addTab(self.research,'Research')
        self.message=QLabel('Draft edits save after a short pause. Commit to name a reproducible language version.');self.message.setWordWrap(True);outer.addWidget(self.message)
        self.refresh()

    def button(self,label,fn):
        b=QPushButton(label);b.clicked.connect(fn);return b

    def call(self,method,**params):
        if 'expected_generation' in params: params['project_id']=self.value['projectId']
        value=self.api.call(method,params,expected_revision=self.book.revision,origin='desktop')
        if not value['ok']:
            self.message.setText('ERROR · '+value['error']['message']);self.message.setStyleSheet('color:#ffb3a8');return None
        self.message.setStyleSheet('');return value['result']

    def guard(self): return self.value['generation'] if self.value else -1

    def refresh(self):
        if self.pending: return  # Never overwrite unflushed editor contents.
        if hasattr(self,'laboratory') and self.laboratory.dirty: return
        self.loading=True
        try:
            if not self.book.forge: return
            self.value=self.book.forge.read(self.version);v=self.value;hist=self.book.forge.history()
            self.status.setText(v['title']+'  ·  '+v['branch']+'  ·  '+('Historical version (read only)' if self.version else 'Draft has changes' if v['dirty'] else 'Committed')+'  ·  '+(self.version or v['head'])[:12]+'\n'+v['path'])
            self.branches.clear()
            for b in v['branches']: self.branches.addItem(b['name'])
            self.branches.setCurrentText(v['branch']);self.versions.clear();self.versions.addItem('Working draft (autosaved)',None)
            for c in hist: self.versions.addItem(c['label']+' · '+c['id'][:10],c['id'])
            self.versions.setCurrentIndex(max(0,self.versions.findData(self.version)))
            self.history.setPlainText('\n\n'.join(c['label']+'\n'+c['id']+'\nParents: '+', '.join(c.get('parents',[c['parent']] if c['parent'] else []))+'\n'+c['createdAt'] for c in hist))
            self.fill_dictionary();self.wiki_list.clear()
            for row in v['snapshot']['wiki']: self.wiki_list.addItem(row['title'])
            self.test_list.clear()
            for row in v['snapshot']['tests']: self.test_list.addItem(row['title'])
            if self.test_list.count(): self.test_list.setCurrentRow(0)
            self.runs=self.book.forge.runs();self.run_list.clear()
            for run in self.runs: self.run_list.addItem(run['status']+' · '+run['testId']+' · '+run['version'][:10])
            if self.runs: self.run_list.setCurrentRow(0)
            self.research.setPlainText(json.dumps(dict(decisions=v['snapshot']['decisions'],research=v['snapshot']['research']),ensure_ascii=False,indent=2))
            for edit in [self.wiki_title,self.wiki_editor,*self.fields.values()]: edit.setReadOnly(bool(self.version))
            self.selection=None;self.wiki_editor.clear();self.wiki_title.clear();self.wiki_preview.clear()
        finally:
            self.loading=False
            if hasattr(self,'laboratory'): self.laboratory.refresh()
            if hasattr(self,'integration'): self.integration.refresh()

    def flush(self):
        self.timer.stop()
        if self.pending and not self.save_pending(): return False
        return self.laboratory.save() if hasattr(self,'laboratory') else True

    def reload(self):
        lab=getattr(self,'laboratory',None)
        if (self.pending or (lab and lab.dirty)) and QMessageBox.question(self,'Reload saved draft','Discard this editor\'s unsaved text and reload the project? Copy your text first if you want to keep it.')!=QMessageBox.StandardButton.Yes: return
        self.timer.stop();self.pending=None
        if lab: lab.dirty=False
        self.refresh();self.message.setText('Reloaded the durable project draft.')

    def queue(self,kind):
        if self.loading or self.version or not self.selection or self.selection[0]!=kind: return
        self.pending=(kind,deepcopy(self.selection[1]));self.timer.start();self.message.setText('Saving draft…')

    def wiki_changed(self):
        self.wiki_preview.setMarkdown(self.wiki_editor.toPlainText());self.queue('wiki')

    def save_pending(self):
        if not self.pending: return True
        kind,record=self.pending
        if kind=='wiki': record.update(title=self.wiki_title.text(),body=self.wiki_editor.toPlainText())
        else:
            for k,edit in self.fields.items():
                if k=='definition': record['senses'][0]['definition']=edit.text();record['senses'][0]['status']='draft'
                else: record[k]=edit.text()
            record['status']='draft'
            notice='Forge editorial draft; previous version preserves the attested record.'
            if notice not in record['notes']: record['notes']+='\n'+notice
        value=self.call('forge.record.put',collection=kind,record=record,expected_generation=self.guard())
        if value is None: return False
        self.pending=None;self.selection=(kind,record);self.value['generation']=value['generation'];self.value['dirty']=True
        rows=self.value['snapshot'][kind] if kind=='wiki' else self.value['snapshot']['language'][kind]
        for i,r in enumerate(rows):
            if r['id']==record['id']: rows[i]=record;break
        if kind=='lexicon': self.fill_dictionary()
        else:
            for i,r in enumerate(rows):
                if r['id']==record['id']: self.wiki_list.item(i).setText(record['title']);break
        self.message.setText('Draft saved · generation '+str(value['generation'])+' · commit to create a named version.')
        self.status.setText(self.value['title']+' · '+self.value['branch']+' · Draft has changes · '+self.value['head'][:12]+'\n'+self.value['path'])
        return True

    def fill_dictionary(self):
        if not self.value: return
        query=self.search.text().casefold();rows=self.value['snapshot']['language']['lexicon']
        self.visible_entries=[r for r in rows if query in ' '.join([r['headword'],r['label'],r['id'],r['pronunciation'],*[s['definition'] for s in r['senses']]]).casefold()]
        self.table.blockSignals(True);self.table.setRowCount(len(self.visible_entries))
        for i,r in enumerate(self.visible_entries):
            for j,t in enumerate([r['headword'],r['senses'][0]['definition'] if r['senses'] else r['label'],r['status'],r['id']]): self.table.setItem(i,j,QTableWidgetItem(t))
            face=next((f for f in self.book.fonts.faces.values() if f.sha256=='a9bb4075285df9acf2bf75c08446d44cfd83b29f6940937671cc07bd68f9f6cc'),None)
            if r['orthographyId']=='thimfora-79' and face:
                font=QFont(face.family);font.setPointSizeF(25);self.table.item(i,0).setFont(font);self.table.setRowHeight(i,42)
        self.table.blockSignals(False)
        self.table.setColumnWidth(0,180);self.table.setColumnWidth(2,95);self.table.setColumnWidth(3,150)

    def select_entry(self):
        if self.loading or not self.flush(): return
        i=self.table.currentRow()
        if i<0 or i>=len(self.visible_entries): return
        r=self.visible_entries[i];self.selection=('lexicon',r);self.loading=True
        for k,e in self.fields.items(): e.setText(r['senses'][0]['definition'] if k=='definition' else r[k])
        self.entry_notes.setPlainText(json.dumps(dict(id=r['id'],status=r['status'],citations=r['citations'],variants=r['variants'],notes=r['notes']),ensure_ascii=False,indent=2));self.loading=False
        face=next((f for f in self.book.fonts.faces.values() if f.sha256=='a9bb4075285df9acf2bf75c08446d44cfd83b29f6940937671cc07bd68f9f6cc'),None)
        if r['orthographyId']=='thimfora-79' and face:
            self.entry_script.setStyleSheet('font-family: "'+face.family+'"; font-size:34pt;');self.entry_script.setText(r['headword'])
        else:
            self.entry_script.setStyleSheet('');self.entry_script.setText('Historical encoding — source slots retained above')

    def select_wiki(self,i):
        if self.loading or not self.flush() or i<0: return
        r=self.value['snapshot']['wiki'][i];self.selection=('wiki',r);self.loading=True
        self.wiki_title.setText(r['title']);self.wiki_editor.setPlainText(r['body']);self.wiki_preview.setMarkdown(r['body']);self.loading=False

    def select_version(self,i):
        if self.loading or not self.flush(): return
        self.version=self.versions.itemData(i);self.refresh()

    def checkout(self):
        if self.loading or not self.flush(): return
        name=self.branches.currentText();self.version=None
        self.call('forge.checkout',name=name,expected_generation=self.guard())

    def new_project(self):
        if not self.flush(): return
        path,_=QFileDialog.getSaveFileName(self,'New language project',str(self.book.root/'.local/forge/Language.vayforge'),'Forge (*.vayforge)')
        if path:
            self.version=None;self.call('forge.create',path=path,title=Path(path).stem,archive=(self.book.root/'Inputs/Versions Best/Translation Chart.docx').exists())

    def open_project(self):
        if not self.flush(): return
        path,_=QFileDialog.getOpenFileName(self,'Open language project',str(self.book.root/'.local'),'Forge (*.vayforge)')
        if path: self.version=None;self.call('forge.open',path=path)

    def export_project(self):
        if not self.value or not self.flush(): return
        path,_=QFileDialog.getSaveFileName(self,'Export complete Forge history',str(self.book.root/'.local/forge-history.json'),'JSON (*.json)')
        if path: self.call('forge.export',path=path)

    def commit(self):
        if not self.value or not self.flush(): return
        if self.version:
            self.message.setText('Historical versions are read only. Branch from this version to edit, or select Working draft to commit.');return
        label,ok=QInputDialog.getText(self,'Commit language version','Version label')
        if ok and label: self.version=None;self.call('forge.commit',label=label,expected_generation=self.guard())

    def branch(self):
        if not self.value or not self.flush(): return
        name,ok=QInputDialog.getText(self,'Branch from frozen version','Branch name (letters, digits, dot, underscore or dash)')
        if ok and name:
            version=self.version or self.value['head'];self.version=None;self.call('forge.branch',name=name,version=version,expected_generation=self.guard())

    def new_wiki(self):
        if not self.value or self.version or not self.flush(): return
        name,ok=QInputDialog.getText(self,'New wiki page','Stable page ID')
        if ok and name: self.call('forge.record.put',collection='wiki',record=dict(id=name,title=name,body='',ruleIds=[]),expected_generation=self.guard())

    def run_test(self):
        if not self.value or not self.flush(): return
        i=self.test_list.currentRow()
        if i<0: return
        if not self.version and self.value['dirty']:
            self.message.setText('Commit the draft first, or select a frozen version to run.');return
        import uuid
        result=self.call('forge.test.run',version=self.version or self.value['head'],test_id=self.value['snapshot']['tests'][i]['id'],directory=str(self.book.root/'.local/forge-runs'/uuid.uuid4().hex))
        if result and result.get('document'): self.call('forge.run.open',run_id=result['runId'])

    def show_run(self,i):
        if hasattr(self,'runs') and 0<=i<len(self.runs): self.run_detail.setPlainText(json.dumps(self.runs[i],indent=2))

    def open_run(self):
        i=self.run_list.currentRow()
        if i>=0: self.call('forge.run.open',run_id=self.runs[i]['runId'])


class ForgeWindow(ReliabilityWindow):
    def __init__(self,book,api):
        super().__init__(book,api)
        workbench=self.takeCentralWidget();outer=QWidget();layout=QVBoxLayout(outer);layout.setContentsMargins(0,0,0,0)
        self.workspace_tabs=QTabWidget();self.workspace_tabs.addTab(workbench,'Language Workbench');self.forge_panel=ForgePanel(self);self.workspace_tabs.addTab(self.forge_panel,'Language Forge');layout.addWidget(self.workspace_tabs);self.setCentralWidget(outer)
        self.workspace_tabs.currentChanged.connect(lambda index:self.forge_panel.refresh() if index==1 else None)
        self.setWindowTitle(self.windowTitle().replace('M6.1','M7'))
        for label in self.findChildren(QLabel):
            if label.text()=='LANGUAGE WORKBENCH  /  M6.1': label.setText('LANGUAGE WORKBENCH  /  M7')

    def refresh(self):
        super().refresh();self.setWindowTitle(self.windowTitle().replace('M6.1','M7'))

    def show_forge(self,tab='forge',section=None,version=None,record_id=None,query=None):
        panel=self.forge_panel
        if not panel.flush(): raise ValueError('FORGE_DRAFT_SAVE_FAILED')
        if version is not None:
            self.book.forge.read(version);panel.version=version;panel.refresh()
        self.workspace_tabs.setCurrentIndex(1 if tab=='forge' else 0)
        if section is not None: panel.tabs.setCurrentIndex(next(i for i in range(panel.tabs.count()) if panel.tabs.tabText(i)==section))
        if query is not None: panel.search.setText(query)
        if record_id is not None:
            if not panel.value: raise ValueError('FORGE_PROJECT_REQUIRED')
            if section=='Wiki':
                rows=panel.value['snapshot']['wiki'];widget=panel.wiki_list
            elif section=='Tests':
                rows=panel.value['snapshot']['tests'];widget=panel.test_list
            elif section=='Dictionary':
                rows=panel.visible_entries;widget=panel.table
            else: raise ValueError('FORGE_RECORD_SECTION_REQUIRED')
            i=next((i for i,r in enumerate(rows) if r['id']==record_id),None)
            if i is None: raise ValueError('FORGE_VISIBLE_RECORD_NOT_FOUND')
            if section=='Dictionary': widget.selectRow(i)
            else: widget.setCurrentRow(i)
        return dict(tab=tab,section=panel.tabs.tabText(panel.tabs.currentIndex()),version=panel.version)

    def closeEvent(self,event):
        if not self.forge_panel.flush(): event.ignore();return
        super().closeEvent(event)
