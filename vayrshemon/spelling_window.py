"""M11 explicit Maxima review and conditional order inspection."""
from copy import deepcopy
import json
import uuid
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QComboBox,QPushButton,QTabWidget,QPlainTextEdit,QTableWidget,QTableWidgetItem,QHeaderView,QFormLayout,QLineEdit
from .variation_window import VariationWindow
from . import spelling


class SpellingPanel(QWidget):
    def __init__(self,forge):
        super().__init__();self.forge=forge;self.dirty=False;self.loading=False;self.value=None;self.plan=None
        layout=QVBoxLayout(self);self.notice=QLabel('Maxima are mapped letterforms, not scaled Minima. Preview an explicit spelling revision before applying it.');self.notice.setWordWrap(True);layout.addWidget(self.notice)
        bar=QHBoxLayout();self.page=QComboBox();bar.addWidget(QLabel('Page'));bar.addWidget(self.page,1)
        for label,fn,key in [('Preview Maxima',self.preview,'preview_button'),('Apply reviewed preview',self.apply,'apply_button'),('Inspect initials',self.audit,'audit_button'),('Freeze audit',self.run,'run_button')]:
            b=QPushButton(label);b.clicked.connect(fn);bar.addWidget(b);setattr(self,key,b)
        layout.addLayout(bar);self.views=QTabWidget();layout.addWidget(self.views,1)
        self.table=self.make_table(['Paragraph','Scalar offset','Letter','Before · Minima','After · Maxima']);self.views.addTab(self.table,'Proposed edits')
        self.pair_table=self.make_table(['Letter identity','Name','Minima','Maxima']);self.views.addTab(self.pair_table,'Letter pairs')
        self.evidence=QPlainTextEdit();self.evidence.setReadOnly(True);self.views.addTab(self.evidence,'Audit evidence')
        definitions=QWidget();dl=QVBoxLayout(definitions);dl.addWidget(QLabel('Changing the policy saves a draft only. Text changes require a separate preview and apply.'))
        self.config=QPlainTextEdit();self.config.textChanged.connect(self.changed);dl.addWidget(self.config);save=QPushButton('Save spelling policy');save.clicked.connect(self.save);dl.addWidget(save);self.views.addTab(definitions,'Policy')
        self.refresh()

    def make_table(self,labels):
        t=QTableWidget(0,len(labels));t.setHorizontalHeaderLabels(labels);t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers);t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch);return t

    def fill(self,table,rows,script_columns):
        face=next((f for f in self.forge.book.fonts.faces.values() if f.sha256=='a9bb4075285df9acf2bf75c08446d44cfd83b29f6940937671cc07bd68f9f6cc'),None)
        table.setRowCount(len(rows))
        for i,row in enumerate(rows):
            for j,value in enumerate(row):
                cell=QTableWidgetItem(str(value));table.setItem(i,j,cell)
                if j in script_columns:
                    cell.setToolTip(' '.join(f'U+{ord(c):04X}' for c in str(value)))
                    if face:font=QFont(face.family);font.setPointSizeF(38);cell.setFont(font)
            table.setRowHeight(i,82)

    def changed(self):
        if not self.loading:self.dirty=True;self.plan=None;self.apply_button.setEnabled(False);self.notice.setText('Unsaved policy; save and preview again before changing text.')

    def refresh(self):
        if self.dirty or not self.forge.value:return
        self.loading=True
        try:
            self.value=deepcopy(self.forge.value);s=self.value['snapshot'];self.config.setPlainText(json.dumps(s.get('spelling',{}),ensure_ascii=False,indent=2));self.config.setReadOnly(bool(self.forge.version))
            old=self.page.currentData();self.page.clear()
            for t in s['tests']:self.page.addItem(t['title'],t['id'])
            self.page.setCurrentIndex(max(0,self.page.findData(old)))
            rows=[[r['symbolId'],r['name'],lo,r['maxima']] for lo,r in spelling.pairs(s).items()] if 'spelling' in s else []
            self.fill(self.pair_table,rows,{2,3});self.plan=None;self.apply_button.setEnabled(False)
        finally:self.loading=False

    def save(self):
        if not self.dirty:return True
        if not self.value or self.forge.version:return False
        try:
            r=self.forge.api.call('forge.spelling.replace',dict(project_id=self.value['projectId'],expected_generation=self.value['generation'],policy=json.loads(self.config.toPlainText())),expected_revision=self.forge.book.revision,origin='desktop')
            if not r['ok']:raise ValueError(r['error']['message'])
            self.dirty=False;self.forge.refresh();self.notice.setText('Policy saved. Preview before applying any spelling changes.');return True
        except (ValueError,TypeError,KeyError) as error:self.notice.setText('Save failed; text retained: '+str(error));return False

    def params(self):return dict(test_id=self.page.currentData(),**(dict(version=self.forge.version) if self.forge.version else {}))

    def preview(self):
        if not self.save() or not self.page.currentData():return
        r=self.forge.call('forge.spelling.preview',**self.params())
        if r:
            self.plan=r;rows=[[p['paragraph']+1,c['offset'],c['name'],c['before'],c['after']] for p in r['audit']['paragraphs'] for c in p['changes']];self.fill(self.table,rows,{3,4});self.views.setCurrentIndex(0)
            self.apply_button.setEnabled(not self.forge.version and bool(rows) and not r['audit']['unmappedCount']);self.notice.setText(f"{len(rows)} Maxima edits proposed. Earlier cases will be retained; English and the Workbench stay unchanged until you run the new version.")

    def apply(self):
        if not self.plan or self.forge.version:return
        r=self.forge.call('forge.spelling.apply',test_id=self.plan['testId'],plan_id=self.plan['planId'],project_id=self.plan['projectId'],expected_generation=self.plan['generation'])
        if r:self.show_report(r['audit']);self.notice.setText('Reviewed spelling applied to the draft. Commit a language version, then Run in Workbench.')

    def audit(self):
        if not self.save() or not self.page.currentData():return
        r=self.forge.call('forge.spelling.audit',**self.params())
        if r:self.show_report(r)

    def run(self):
        if not self.save() or not self.value or not self.page.currentData():return
        if not self.forge.version and self.value['dirty']:self.notice.setText('Commit the draft or select a frozen version first.');return
        r=self.forge.call('forge.spelling.run',version=self.forge.version or self.value['head'],test_id=self.page.currentData(),directory=str(self.forge.book.root/'.local/forge-runs'/uuid.uuid4().hex))
        if r:self.show_report(r)

    def show_report(self,r):
        self.report=r;self.notice.setText(f"{r['maximaInitialCount']} / {r['initialCount']} mapped sentence initials use Maxima · {r['missingCount']} missing · {r['unmappedCount']} unresolved. "+r['scope']);self.evidence.setPlainText(json.dumps(r,ensure_ascii=False,indent=2));self.views.setCurrentWidget(self.evidence)


class SpellingWindow(VariationWindow):
    def __init__(self,book,api):
        super().__init__(book,api);self.forge_panel.spelling=SpellingPanel(self.forge_panel);self.forge_panel.tabs.insertTab(4,self.forge_panel.spelling,'Orthography')
        order=QWidget();form=QFormLayout(order);self.order_rule=QLineEdit('clause');self.order_context=QLineEdit('{"register":"literary","topic":"subject","focus":"neutral"}');form.addRow('Order rule ID',self.order_rule);form.addRow('Context (JSON)',self.order_context);b=QPushButton('Inspect optional orders');b.clicked.connect(self.inspect_orders);form.addRow(b);self.order_result=QPlainTextEdit();self.order_result.setReadOnly(True);form.addRow(self.order_result);self.forge_panel.variation.views.addTab(order,'Orders in context')
        for label in self.findChildren(QLabel):
            if '/  M10' in label.text():label.setText(label.text().replace('/  M10','/  M11'))
        self.setWindowTitle(self.windowTitle().replace('M10','M11'))

    def inspect_orders(self):
        if not self.forge_panel.flush():return
        try:
            params=dict(rule_id=self.order_rule.text(),context=json.loads(self.order_context.text()))
            if self.forge_panel.version:params['version']=self.forge_panel.version
            r=self.forge_panel.call('forge.variation.orders',**params)
            if r:self.order_result.setPlainText(r['scope']+'\n\n'+'\n\n'.join(('AVAILABLE' if row['allowed'] else 'BLOCKED')+' · '+' → '.join(row['pattern'])+'\n'+row.get('note',row.get('source','')) for row in r['patterns']))
        except ValueError as error:self.order_result.setPlainText(str(error))

    def refresh(self):
        super().refresh();self.setWindowTitle(self.windowTitle().replace('M10','M11'))

    def show_forge(self,spelling_test=None,spelling_preview=False,spelling_run=None,**params):
        r=super().show_forge(**params);panel=self.forge_panel.spelling
        if spelling_test:
            i=panel.page.findData(spelling_test)
            if i<0:raise ValueError('SPELLING_PAGE_MISSING')
            panel.page.setCurrentIndex(i)
        if spelling_preview:panel.preview()
        if spelling_run:
            report=next((r for r in self.book.forge.runs() if r['runId']==spelling_run and r.get('kind')=='spelling-audit'),None)
            if not report:raise ValueError('SPELLING_RUN_MISSING')
            panel.show_report(report)
        return r
