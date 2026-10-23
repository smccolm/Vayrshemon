"""M8 test authoring, readable outcomes, coverage and pinned version comparison."""
from copy import deepcopy
import json
import uuid
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QFormLayout,QSplitter,QListWidget,QLineEdit,QPlainTextEdit,QComboBox,QLabel,QPushButton,QTabWidget,QTableWidget,QTableWidgetItem,QHeaderView)
from .forge_window import ForgeWindow


class LaboratoryPanel(QWidget):
    def __init__(self,forge):
        super().__init__();self.forge=forge;self.loading=False;self.dirty=False;self.value=None;self.rows=[]
        outer=QVBoxLayout(self);bar=QHBoxLayout();self.collection=QComboBox();self.collection.addItems(['Test cases','Rules','Bilingual pages']);bar.addWidget(self.collection)
        for text,fn in [('New',self.new),('Save draft',self.save),('Preview draft',self.preview),('Run frozen suite',self.run_suite)]:
            b=QPushButton(text);b.clicked.connect(fn);bar.addWidget(b)
        bar.addStretch();outer.addLayout(bar)
        self.notice=QLabel('Tests assert spelling, inflection and annotated clause structure. Meaning and literary interpretation remain editorial.');self.notice.setWordWrap(True);outer.addWidget(self.notice)
        split=QSplitter();outer.addWidget(split,1);self.records=QListWidget();split.addWidget(self.records)
        pane=QWidget();form=QFormLayout(pane);self.fields={}
        for key,label,multiline in [('id','Stable ID',False),('title','Title',False),('text','Input text / Vayrshemon paragraphs',True),('translation','English paragraphs',True),('note','Analysis / editorial note',True),('ruleIds','Rule IDs (comma separated)',False),('grammarId','Grammar record ID',False),('tokens','Token annotations (JSON; scalar offsets)',True),('config','Rule configuration (JSON)',True),('caseIds','Bound clause IDs per paragraph (JSON)',True)]:
            edit=QPlainTextEdit() if multiline else QLineEdit();self.fields[key]=edit;form.addRow(label,edit)
            if multiline: edit.setMaximumHeight(100);edit.textChanged.connect(self.changed)
            else: edit.textEdited.connect(self.changed)
        self.kind=QComboBox();self.expected=QComboBox();self.expected.addItems(['accept','reject','review','unsupported']);form.insertRow(2,'Kind',self.kind);form.insertRow(3,'Expected outcome',self.expected)
        self.kind.currentTextChanged.connect(self.changed);self.expected.currentTextChanged.connect(self.changed)
        split.addWidget(pane);split.setSizes([250,850]);self.form=form
        self.views=QTabWidget();outer.addWidget(self.views,1)
        self.results=QTableWidget(0,4);self.results.setHorizontalHeaderLabels(['Test','Expected','Actual','Result']);self.results.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers);self.results.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeMode.Stretch);self.views.addTab(self.results,'Results')
        self.coverage=QPlainTextEdit();self.coverage.setReadOnly(True);self.views.addTab(self.coverage,'Coverage')
        self.detail=QPlainTextEdit();self.detail.setReadOnly(True);self.views.addTab(self.detail,'Diagnostics')
        compare=QWidget();cl=QVBoxLayout(compare);cb=QHBoxLayout();self.before=QComboBox();self.after=QComboBox();cb.addWidget(QLabel('Before'));cb.addWidget(self.before,1);cb.addWidget(QLabel('After'));cb.addWidget(self.after,1);button=QPushButton('Compare same cases');button.clicked.connect(self.compare);cb.addWidget(button);cl.addLayout(cb);self.comparison=QPlainTextEdit();self.comparison.setReadOnly(True);cl.addWidget(self.comparison);self.views.addTab(compare,'Version comparison')
        self.collection.currentIndexChanged.connect(self.change_collection);self.records.currentRowChanged.connect(self.select)
        self.results.currentCellChanged.connect(self.result_detail)
        self.refresh()

    def changed(self,*_):
        if not self.loading: self.dirty=True;self.notice.setText('Unsaved test edits. Save draft, then commit a language version to run reproducibly.')

    def text(self,key):
        e=self.fields[key];return e.toPlainText() if isinstance(e,QPlainTextEdit) else e.text()

    def set_text(self,key,text):
        e=self.fields[key];e.setPlainText(text) if isinstance(e,QPlainTextEdit) else e.setText(text)

    def change_collection(self):
        # Keep edits in their original collection until saved; do not re-interpret
        # the visible form after a combo change.
        requested=self.collection.currentIndex()
        if self.dirty:
            self.collection.blockSignals(True);self.collection.setCurrentIndex(self.edit_collection);self.collection.blockSignals(False)
            if not self.save(): return
            self.collection.blockSignals(True);self.collection.setCurrentIndex(requested);self.collection.blockSignals(False)
        self.refresh()

    def refresh(self):
        if self.dirty or not self.forge.value: return
        self.loading=True
        try:
            self.value=deepcopy(self.forge.value);snap=self.value['snapshot'];i=self.collection.currentIndex();self.edit_collection=i
            self.rows=snap.get('laboratory',{}).get('cases' if i==0 else 'rules',[]) if i<2 else snap['tests']
            old=self.text('id');self.records.clear()
            for r in self.rows: self.records.addItem(r['title'])
            for key,e in self.fields.items():
                visible=key in ({'id','title','text','note','ruleIds','tokens'} if i==0 else {'id','title','grammarId','config'} if i==1 else {'id','title','text','translation','note','ruleIds','caseIds'})
                e.setVisible(visible);self.form.labelForField(e).setVisible(visible);e.setReadOnly(bool(self.forge.version))
            self.kind.blockSignals(True);self.kind.clear();self.kind.addItems(['word','clause','review'] if i==0 else ['inventory','forms','analysis','order','review']);self.kind.blockSignals(False)
            self.kind.setVisible(i<2);self.form.labelForField(self.kind).setVisible(i<2);self.kind.setEnabled(not self.forge.version)
            self.expected.setVisible(i==0);self.form.labelForField(self.expected).setVisible(i==0);self.expected.setEnabled(not self.forge.version)
            history=self.forge.book.forge.history()
            for combo in (self.before,self.after):
                selected=combo.currentData();combo.clear()
                for r in reversed(history): combo.addItem(r['label']+' · '+r['id'][:8],r['id'])
                combo.setCurrentIndex(max(0,combo.findData(selected)))
            if self.after.count() and not self.after.currentData()==self.value['head']: self.after.setCurrentIndex(self.after.findData(self.value['head']))
            index=next((n for n,r in enumerate(self.rows) if r['id']==old),0)
            self.records.setCurrentRow(index if self.rows else -1)
        finally: self.loading=False
        if self.rows: self.select(self.records.currentRow())
        else:
            self.loading=True
            for e in self.fields.values(): e.clear()
            self.loading=False

    def select(self,index):
        if self.loading or index<0 or index>=len(self.rows): return
        selected_id=self.rows[index]['id']
        if self.dirty and not self.save(): return
        self.loading=True
        try:
            r=next(r for r in self.rows if r['id']==selected_id)
            for key in self.fields: self.set_text(key,'')
            for key in ('id','title','text','note','grammarId'):
                if key in r: self.set_text(key,r[key])
            self.fields['id'].setReadOnly(True)
            self.set_text('ruleIds',', '.join(r.get('ruleIds',[])))
            self.set_text('tokens',json.dumps(r.get('tokens',[]),ensure_ascii=False,indent=2));self.set_text('config',json.dumps(r.get('config',{}),ensure_ascii=False,indent=2))
            self.set_text('caseIds',json.dumps(r['caseIds'],indent=2) if 'caseIds' in r else '')
            if 'kind' in r: self.kind.setCurrentText(r['kind'])
            if 'expected' in r: self.expected.setCurrentText(r['expected'])
            if 'paragraphs' in r:
                for field,key in [('text','text'),('translation','translation'),('note','analysis')]: self.set_text(field,'\n\n'.join(p[key] for p in r['paragraphs']))
            self.dirty=False
        finally: self.loading=False

    def new(self):
        if not self.forge.value or self.forge.version or (self.dirty and not self.save()): return
        self.loading=True
        for e in self.fields.values(): e.clear()
        self.fields['id'].setReadOnly(False);self.set_text('id','test-'+uuid.uuid4().hex[:8]);self.set_text('title','New test' if self.edit_collection!=1 else 'New rule');self.set_text('tokens','[]');self.set_text('config','{}');self.loading=False;self.dirty=True

    def save(self):
        if not self.dirty: return True
        if not self.value or self.forge.version: return False
        try:
            record=dict(id=self.text('id').strip(),title=self.text('title'))
            rules=[r.strip() for r in self.text('ruleIds').split(',') if r.strip()]
            if self.edit_collection==0: record.update(kind=self.kind.currentText(),text=self.text('text'),note=self.text('note'),ruleIds=rules,expected=self.expected.currentText(),tokens=json.loads(self.text('tokens') or '[]'))
            elif self.edit_collection==1: record.update(kind=self.kind.currentText(),grammarId=self.text('grammarId').strip(),config=json.loads(self.text('config') or '{}'))
            else:
                a=self.text('text').split('\n\n');b=self.text('translation').split('\n\n');notes=self.text('note').split('\n\n')
                if len(a)!=len(b) or len(notes) not in (1,len(a)): raise ValueError('Use equal numbers of Vayrshemon and English paragraphs, separated by a blank line. Supply one analysis or one per pair.')
                record.update(ruleIds=rules,paragraphs=[dict(text=x,translation=y,analysis=notes[0] if len(notes)==1 else notes[n]) for n,(x,y) in enumerate(zip(a,b))])
                if self.text('caseIds').strip(): record['caseIds']=json.loads(self.text('caseIds'))
            # Use the generation captured when editing started, not a fresh read.
            params=dict(collection=['cases','rules','tests'][self.edit_collection],record=record,expected_generation=self.value['generation'],project_id=self.value['projectId'])
            method='forge.record.put' if self.edit_collection==2 else 'forge.lab.put'
            result=self.forge.api.call(method,params,expected_revision=self.forge.book.revision,origin='desktop')
            if not result['ok']: raise ValueError(result['error']['message'])
            self.dirty=False;self.forge.refresh();self.notice.setText('Draft saved. Commit a version to freeze these tests and rules.');return True
        except (ValueError,KeyError,TypeError) as error:
            self.notice.setText('Save failed; your text is retained: '+str(error));return False

    def preview(self):
        if not self.save(): return
        params=dict(version=self.forge.version) if self.forge.version else {}
        result=self.forge.call('forge.lab.evaluate',**params)
        if result: self.show_report(result)

    def run_suite(self):
        if not self.save() or not self.forge.value: return
        if not self.forge.version and self.forge.value['dirty']: self.notice.setText('Commit the draft or select a frozen version first.');return
        result=self.forge.call('forge.lab.run',version=self.forge.version or self.forge.value['head'],directory=str(self.forge.book.root/'.local/forge-runs'/uuid.uuid4().hex))
        if result: self.show_report(result)

    def show_report(self,report):
        self.report=report;self.results.setRowCount(len(report['results']))
        for i,r in enumerate(report['results']):
            for j,key in enumerate(('title','expected','actual','status')): self.results.setItem(i,j,QTableWidgetItem(r[key]))
            self.results.item(i,3).setForeground(QColor({'Pass':'#17633a','Fail':'#a52525','Needs review':'#85520c','Unsupported':'#5f6582'}[r['status']]))
        self.coverage.setPlainText('\n'.join(f"{r['ruleId']}: {r['positive']} positive, {r['negative']} negative passed; {'BOTH DIRECTIONS' if r['bidirectional'] else 'partial' if r['covered'] else 'NOT COVERED'}" for r in report['coverage'])+'\n\nGrammar without executable rules:\n'+'\n'.join(report['unimplementedGrammar']))
        self.detail.setPlainText(json.dumps(report,ensure_ascii=False,indent=2));self.views.setCurrentIndex(0)
        self.notice.setText(f"{report['status']} · {report['caseCount']} cases · "+', '.join(f'{n} {k}' for k,n in report['counts'].items())+' · '+('Draft preview' if report.get('draft') else 'Frozen version'))

    def result_detail(self,row,*_):
        if hasattr(self,'report') and 0<=row<len(self.report['results']): self.detail.setPlainText(json.dumps(self.report['results'][row],ensure_ascii=False,indent=2))

    def compare(self):
        if not self.save() or not self.before.currentData() or not self.after.currentData(): return
        report=self.forge.call('forge.lab.compare',before=self.before.currentData(),after=self.after.currentData())
        if report: self.show_comparison(report)

    def show_comparison(self,report):
        self.comparison.setPlainText('Same frozen cases: '+report['caseVersion']+'\n\n'+'\n'.join(f"{r['caseId']}: {r['before']} → {r['after']} · {'REGRESSION' if r['regression'] else 'IMPROVED' if r['improvement'] else 'changed' if r['changed'] else 'unchanged'}" for r in report['cases']));self.views.setCurrentWidget(self.comparison.parentWidget())


class LaboratoryWindow(ForgeWindow):
    def __init__(self,book,api):
        super().__init__(book,api);self.forge_panel.laboratory=LaboratoryPanel(self.forge_panel);self.forge_panel.tabs.insertTab(3,self.forge_panel.laboratory,'Laboratory')
        for label in self.findChildren(QLabel):
            if '/  M7' in label.text(): label.setText(label.text().replace('/  M7','/  M8'))
        self.setWindowTitle(self.windowTitle().replace('M7','M8'))

    def refresh(self):
        super().refresh();self.setWindowTitle(self.windowTitle().replace('M7','M8'))

    def show_forge(self,tab='forge',section=None,version=None,record_id=None,query=None,draft=False,run_id=None,compare_before=None,compare_after=None,lab_view=None):
        if bool(compare_before)!=bool(compare_after): raise ValueError('FORGE_COMPARISON_VERSIONS_REQUIRED')
        if draft and version: raise ValueError('FORGE_CHOOSE_DRAFT_OR_VERSION')
        if draft:
            if not self.forge_panel.flush(): raise ValueError('FORGE_DRAFT_SAVE_FAILED')
            self.forge_panel.version=None;self.forge_panel.refresh()
        lab_id=record_id if section=='Laboratory' else None
        result=super().show_forge(tab,section,version,None if lab_id else record_id,query)
        if lab_id:
            lab=self.forge_panel.laboratory
            for n,rows in enumerate([self.book.forge.read(lab.forge.version)['snapshot'].get('laboratory',{}).get(k,[]) for k in ('cases','rules')]):
                index=next((i for i,r in enumerate(rows) if r['id']==lab_id),None)
                if index is not None: lab.collection.setCurrentIndex(n);lab.refresh();lab.records.setCurrentRow(index);break
            else: raise ValueError('FORGE_VISIBLE_RECORD_NOT_FOUND')
        if run_id:
            report=next((r for r in self.book.forge.runs() if r['runId']==run_id and r.get('kind')=='language-suite'),None)
            if not report: raise ValueError('LAB_SUITE_RUN_NOT_FOUND')
            self.forge_panel.laboratory.show_report(report)
        if compare_before:
            from .forge_lab import compare
            self.forge_panel.laboratory.show_comparison(compare(self.book.forge,compare_before,compare_after))
        lab=self.forge_panel.laboratory
        if lab_id and hasattr(lab,'report'):
            row=next((i for i,r in enumerate(lab.report['results']) if r['caseId']==lab_id),None)
            if row is not None: lab.results.setCurrentCell(row,0);lab.results.scrollToItem(lab.results.item(row,0))
        if lab_view is not None: lab.views.setCurrentIndex(next(i for i in range(lab.views.count()) if lab.views.tabText(i)==lab_view))
        return result
