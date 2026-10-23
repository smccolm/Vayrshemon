"""Readable variation evidence beside versioned definitions; no prose rewriting."""
from copy import deepcopy
import json
import uuid
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QComboBox,QPushButton,QPlainTextEdit,QTabWidget,QTableWidget,QTableWidgetItem,QHeaderView,QLineEdit,QFormLayout)
from .integration_window import IntegrationWindow
from .variation import empty


class VariationPanel(QWidget):
    def __init__(self,forge):
        super().__init__();self.forge=forge;self.dirty=False;self.loading=False;self.value=None
        layout=QVBoxLayout(self)
        self.notice=QLabel('Variation is a choice in context. Counts describe this sample; they do not measure whether a language is natural.');self.notice.setWordWrap(True);layout.addWidget(self.notice)
        bar=QHBoxLayout();self.page=QComboBox();bar.addWidget(QLabel('Page'));bar.addWidget(self.page,1)
        for title,fn in [('Inspect page',self.audit),('Freeze audit',self.run)]:
            b=QPushButton(title);b.clicked.connect(fn);bar.addWidget(b)
        layout.addLayout(bar)
        compare=QHBoxLayout();self.before=QComboBox();self.after=QComboBox()
        for title,combo in [('Before',self.before),('After',self.after)]:compare.addWidget(QLabel(title));compare.addWidget(combo,1)
        self.compare_button=QPushButton('Compare repetition');self.compare_button.clicked.connect(self.compare);compare.addWidget(self.compare_button);layout.addLayout(compare)
        self.views=QTabWidget();layout.addWidget(self.views,1)
        results=QWidget();rl=QVBoxLayout(results);self.summary=QLabel('Inspect a page or compare two frozen versions.');self.summary.setWordWrap(True);rl.addWidget(self.summary)
        self.table=QTableWidget(0,5);self.table.setHorizontalHeaderLabels(['Watched prefix','Before','After / count','Clause openings','Consecutive tokens']);self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers);self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents);self.table.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeMode.Stretch);rl.addWidget(self.table)
        evidence=QTabWidget();self.details=QPlainTextEdit();self.details.setReadOnly(True);evidence.addTab(self.details,'Reading notes');self.diagnostics=QPlainTextEdit();self.diagnostics.setReadOnly(True);evidence.addTab(self.diagnostics,'Full diagnostics');rl.addWidget(evidence,1);self.views.addTab(results,'Repetition')
        definitions=QWidget();dl=QVBoxLayout(definitions);dl.addWidget(QLabel('Optional forms: exact paradigm prefixes, explicit context conditions, preserved full forms. Save draft, then commit to freeze.'))
        self.config=QPlainTextEdit();self.config.textChanged.connect(self.changed);dl.addWidget(self.config,1);self.save_button=QPushButton('Save variation draft');self.save_button.clicked.connect(self.save);dl.addWidget(self.save_button);self.views.addTab(definitions,'Definitions')
        forms=QWidget();fl=QFormLayout(forms);self.entry=QLineEdit();self.features=QLineEdit('{}');self.context=QLineEdit('{}')
        for title,e in [('Dictionary entry ID',self.entry),('Features (JSON)',self.features),('Context (JSON)',self.context)]:fl.addRow(title,e)
        inspect=QPushButton('Inspect available forms');inspect.clicked.connect(self.forms);fl.addRow(inspect);self.form_result=QPlainTextEdit();self.form_result.setReadOnly(True);fl.addRow(self.form_result);self.views.addTab(forms,'Forms in context')
        self.refresh()

    def changed(self):
        if not self.loading:self.dirty=True;self.notice.setText('Unsaved variation definitions. Invalid or stale edits remain here until resolved.')

    def refresh(self):
        if self.dirty or not self.forge.value:return
        self.loading=True
        try:
            self.value=deepcopy(self.forge.value);snap=self.value['snapshot']
            self.config.setPlainText(json.dumps(snap.get('variation',empty()),ensure_ascii=False,indent=2));self.config.setReadOnly(bool(self.forge.version));self.save_button.setEnabled(not self.forge.version)
            old=self.page.currentData();self.page.clear()
            for t in snap['tests']:self.page.addItem(t['title'],t['id'])
            self.page.setCurrentIndex(max(0,self.page.findData(old)))
            for combo in (self.before,self.after):
                old=combo.currentData();combo.clear()
                for row in reversed(self.forge.book.forge.history()):combo.addItem(row['label']+' · '+row['id'][:8],row['id'])
                combo.setCurrentIndex(max(0,combo.findData(old)))
        finally:self.loading=False

    def save(self):
        if not self.dirty:return True
        if not self.value or self.forge.version:return False
        try:
            result=self.forge.api.call('forge.variation.replace',dict(project_id=self.value['projectId'],expected_generation=self.value['generation'],variation=json.loads(self.config.toPlainText())),expected_revision=self.forge.book.revision,origin='desktop')
            if not result['ok']:raise ValueError(result['error']['message'])
            self.dirty=False;self.forge.refresh();self.notice.setText('Draft saved. Commit a version to freeze these proposals.');return True
        except (ValueError,TypeError,KeyError) as error:self.notice.setText('Save failed; edits retained: '+str(error));return False

    def audit(self):
        if not self.save() or not self.page.currentData():return
        params=dict(test_id=self.page.currentData())
        if self.forge.version:params['version']=self.forge.version
        r=self.forge.call('forge.variation.audit',**params)
        if r:self.show_report(r)

    def run(self):
        if not self.save() or not self.value or not self.page.currentData():return
        if not self.forge.version and self.value['dirty']:self.notice.setText('Commit the draft or select a frozen version first.');return
        r=self.forge.call('forge.variation.run',version=self.forge.version or self.value['head'],test_id=self.page.currentData(),directory=str(self.forge.book.root/'.local/forge-runs'/uuid.uuid4().hex))
        if r:self.show_report(r)

    def compare(self):
        if not self.save() or not self.page.currentData() or not self.before.currentData() or not self.after.currentData():return
        r=self.forge.call('forge.variation.compare',before=self.before.currentData(),after=self.after.currentData(),test_id=self.page.currentData())
        if r:self.show_report(r)

    def forms(self):
        if not self.save():return
        try:
            params=dict(entry_id=self.entry.text(),features=json.loads(self.features.text()),context=json.loads(self.context.text()))
            if self.forge.version:params['version']=self.forge.version
            r=self.forge.call('forge.variation.forms',**params)
            if r:self.form_result.setPlainText(json.dumps(r,ensure_ascii=False,indent=2))
        except ValueError as error:self.notice.setText(str(error))

    def show_report(self,report):
        self.report=report;after=report.get('after',report);before=report.get('before');self.table.setRowCount(len(after['watched']))
        for i,row in enumerate(after['watched']):
            values=[row['label'],str(before['watched'][i]['count']) if before else '—',f"{row['count']} / {after['tokenCount']} ({row['tokenShare']:.0%})",f"{row['clauseOpenings']} / {row['clauseCount']}",str(row['longestConsecutiveTokens'])]
            for j,value in enumerate(values):self.table.setItem(i,j,QTableWidgetItem(value))
        inspection='Review flagged repetition' if after['warnings'] else 'No watch threshold triggered'
        self.summary.setText(f"{after['tokenCount']} tokens · {after['clauseCount']} annotated clauses · {inspection}. "+report['scope'])
        notes=[w['message'] for w in after['warnings']]
        if before:
            for a,b in zip(before['watched'],after['watched']):notes.append(f"{b['label']}: {a['count']} → {b['count']} tokens; {a['clauseOpenings']} → {b['clauseOpenings']} clause openings. The texts differ; the watch definitions are identical.")
        notes.append('Review the remaining occurrences in their discourse context. Context labels below are author interpretations, not inferred facts.')
        for row in after['watched']:
            notes.append('\n'+row['label'])
            for item in row['locations']:
                context=', '.join(f'{k}: {v}' for k,v in item['context'].items()) or 'unannotated'
                notes.append(f"Paragraph {item['paragraph']+1} · {item.get('caseId','unbound')} · {item['entryId'] or item['surface']}\n  {context}")
            if row['locationsTruncated']:notes.append('Locations truncated after 256; full counts retained.')
        self.details.setPlainText('\n\n'.join(notes));self.diagnostics.setPlainText(json.dumps(report,ensure_ascii=False,indent=2));self.views.setCurrentIndex(0)
        self.notice.setText('Comparison uses the same watch definitions on each version’s own text.' if before else 'Audit retained with exact input hashes.' if report.get('runId') else 'Preview of the selected version or draft.')


class VariationWindow(IntegrationWindow):
    def __init__(self,book,api):
        super().__init__(book,api);self.forge_panel.variation=VariationPanel(self.forge_panel);self.forge_panel.tabs.insertTab(4,self.forge_panel.variation,'Variation')
        for label in self.findChildren(QLabel):
            if '/  M9' in label.text():label.setText(label.text().replace('/  M9','/  M10'))
        self.setWindowTitle(self.windowTitle().replace('M9','M10'))

    def refresh(self):
        super().refresh();self.setWindowTitle(self.windowTitle().replace('M9','M10'))

    def show_forge(self,variation_before=None,variation_after=None,variation_test=None,variation_run=None,**params):
        if bool(variation_before)!=bool(variation_after):raise ValueError('VARIATION_COMPARISON_VERSIONS_REQUIRED')
        if variation_before and not variation_test:raise ValueError('VARIATION_TEST_REQUIRED')
        result=super().show_forge(**params);panel=self.forge_panel.variation
        if variation_test:
            index=panel.page.findData(variation_test)
            if index<0:raise ValueError('VARIATION_PAGE_MISSING')
            panel.page.setCurrentIndex(index)
        if variation_before:
            for combo,value in [(panel.before,variation_before),(panel.after,variation_after)]:combo.setCurrentIndex(combo.findData(value))
            panel.show_report(self.api.dispatch('forge.variation.compare',dict(before=variation_before,after=variation_after,test_id=variation_test)))
        if variation_run:
            report=next((r for r in self.book.forge.runs() if r['runId']==variation_run and r.get('kind')=='variation-audit'),None)
            if not report:raise ValueError('VARIATION_RUN_MISSING')
            panel.show_report(report)
        return result
