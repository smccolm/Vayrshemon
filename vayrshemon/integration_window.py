"""M9 conflict review, evidence-pinned releases and centered single-page views."""
import json
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QFormLayout,QLabel,QComboBox,
    QLineEdit,QPlainTextEdit,QTableWidget,QTableWidgetItem,QHeaderView,QFileDialog,QMessageBox,QPushButton,QApplication)
from .laboratory_window import LaboratoryWindow


class IntegrationPanel:
    def __init__(self, forge):
        self.forge = forge; self.plan = None
        self.merges = QWidget(); layout = QVBoxLayout(self.merges)
        note = QLabel('Merge a committed source branch into the active branch. Commit the target draft first. Source drafts stay saved and are not merged.'); note.setWordWrap(True); layout.addWidget(note)
        row = QHBoxLayout(); self.source = QComboBox(); row.addWidget(QLabel('Source branch')); row.addWidget(self.source,1)
        row.addWidget(forge.button('Preview merge',self.preview)); layout.addLayout(row)
        self.summary = QPlainTextEdit(); self.summary.setReadOnly(True); self.summary.setMaximumHeight(160); layout.addWidget(self.summary)
        self.conflicts = QTableWidget(0,5); self.conflicts.setHorizontalHeaderLabels(['Field / stable ID','Base','Active branch','Source branch','Resolution'])
        self.conflicts.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch); self.conflicts.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers); layout.addWidget(self.conflicts,1)
        row = QHBoxLayout(); self.label = QLineEdit(); self.label.setPlaceholderText('Name the merged language version'); row.addWidget(self.label,1)
        self.apply_button = forge.button('Commit resolved merge',self.apply); row.addWidget(self.apply_button); layout.addLayout(row)
        self.releases = QWidget(); layout = QVBoxLayout(self.releases)
        note = QLabel('A release permanently pins its language version, dictionary, wiki and test evidence. Experimental releases retain meaning/coverage gaps; stable releases require all gates to pass.'); note.setWordWrap(True); layout.addWidget(note)
        form = QFormLayout(); layout.addLayout(form)
        self.name = QLineEdit(); self.name.setPlaceholderText('e.g. 0.3.0-experimental.1'); form.addRow('Release name',self.name)
        self.channel = QComboBox(); self.channel.addItems(['experimental','stable']); form.addRow('Channel',self.channel)
        self.version = QComboBox(); form.addRow('Frozen language version',self.version)
        self.suite = QComboBox(); self.page = QComboBox(); form.addRow('Frozen suite run',self.suite); form.addRow('Workbench proof run',self.page)
        self.version.currentIndexChanged.connect(self.fill_runs)
        self.reviewer = QLineEdit(); self.reviewer.setPlaceholderText('Required for stable acceptance'); form.addRow('Accepting reviewer',self.reviewer)
        self.notes = QPlainTextEdit(); self.notes.setMaximumHeight(90); self.notes.setPlaceholderText('What changed, known gaps, and intended use'); form.addRow('Release notes',self.notes)
        layout.addWidget(forge.button('Create immutable release',self.create_release))
        row = QHBoxLayout(); self.release_list = QComboBox(); row.addWidget(self.release_list,1); row.addWidget(forge.button('Export selected release…',self.export)); layout.addLayout(row)
        self.release_detail = QPlainTextEdit(); self.release_detail.setReadOnly(True); layout.addWidget(self.release_detail,1)
        self.release_list.currentIndexChanged.connect(self.show_release)
        forge.tabs.addTab(self.merges,'Merges'); forge.tabs.addTab(self.releases,'Releases'); self.refresh()

    def refresh(self):
        p = self.forge.book.forge
        if not p: return
        status = p.status(); previous = self.source.currentText(); self.source.clear()
        self.source.addItems([b['name'] for b in status['branches'] if b['name'] != status['branch']]); self.source.setCurrentText(previous)
        previous = self.version.currentData(); self.version.blockSignals(True); self.version.clear()
        for c in p.history(): self.version.addItem(c['label']+' · '+c['id'][:10],c['id'])
        index = self.version.findData(previous or status['head']); self.version.setCurrentIndex(max(0,index)); self.version.blockSignals(False); self.fill_runs()
        from .forge_release import list_releases
        self.release_values = list_releases(p); previous = self.release_list.currentText(); self.release_list.clear()
        self.release_list.addItems([r['name'] for r in self.release_values]); self.release_list.setCurrentText(previous); self.show_release()
        self.apply_button.setEnabled(self.plan is not None and self.plan['generation'] == status['generation'])

    def fill_runs(self):
        p = self.forge.book.forge
        if not p: return
        for combo, suite in ((self.suite,True),(self.page,False)):
            previous = combo.currentData(); combo.clear()
            for r in p.runs():
                if r['version'] == self.version.currentData() and bool(r.get('kind') == 'language-suite') == suite and (suite or r.get('document')):
                    combo.addItem(r['status']+' · '+r['testId']+' · '+r['runId'][:10],r['runId'])
            if combo.findData(previous) >= 0: combo.setCurrentIndex(combo.findData(previous))

    def preview(self):
        if not self.forge.flush() or not self.source.currentText(): return
        plan = self.forge.call('forge.merge.preview',source=self.source.currentText())
        if plan: self.show_plan(plan)

    def show_plan(self,plan):
        self.plan = plan; self.source.setCurrentText(plan['source'])
        self.summary.setPlainText(f"{plan['source']} → {plan['target']}\nBase: {plan['base']}\nActive: {plan['ours']}\nSource: {plan['theirs']}\n{len(plan['conflicts'])} conflict(s). Every choice is recorded in the merge commit." + ('\nValidation: '+plan['validationError'] if plan.get('validationError') else ''))
        self.conflicts.setRowCount(len(plan['conflicts']))
        for i,c in enumerate(plan['conflicts']):
            for j,k in enumerate(('path','base','ours','theirs')):
                text = c[k] if k == 'path' else json.dumps(c[k]['value'],ensure_ascii=False,indent=2) if c[k]['present'] else '(deleted / absent)'
                item = QTableWidgetItem(text); item.setToolTip(text); self.conflicts.setItem(i,j,item)
            choice = QComboBox(); choice.addItems(['Choose…','Active branch','Source branch','Base','Delete']); self.conflicts.setCellWidget(i,4,choice)
        self.conflicts.resizeRowsToContents(); self.apply_button.setEnabled(True)

    def apply(self):
        if not self.plan or not self.forge.flush(): return
        choices = {}; names = [None,'ours','theirs','base','delete']
        for i,c in enumerate(self.plan['conflicts']):
            choice = names[self.conflicts.cellWidget(i,4).currentIndex()]
            if not choice: self.forge.message.setText('Choose a resolution for every conflict.'); return
            choices[c['path']] = dict(choice=choice)
        result = self.forge.call('forge.merge.apply',source=self.plan['source'],plan_id=self.plan['planId'],label=self.label.text(),resolutions=choices,expected_generation=self.plan['generation'])
        if result:
            self.summary.appendPlainText('\nMERGED · '+result['mergeVersion']); self.plan = None; self.apply_button.setEnabled(False)
            self.forge.version=None; self.forge.refresh(); self.version.setCurrentIndex(self.version.findData(result['mergeVersion']))

    def create_release(self):
        if not self.forge.flush(): return
        if not self.suite.currentData() or not self.page.currentData(): self.forge.message.setText('Run the selected frozen version in Laboratory and Workbench first.'); return
        result = self.forge.call('forge.release.create',name=self.name.text(),version=self.version.currentData(),channel=self.channel.currentText(),notes=self.notes.toPlainText(),reviewer=self.reviewer.text(),suite_run_id=self.suite.currentData(),workbench_run_id=self.page.currentData(),expected_generation=self.forge.guard())
        if result: self.release_list.setCurrentText(result['name']); self.show_release()

    def show_release(self):
        index = self.release_list.currentIndex()
        if index < 0: self.release_detail.clear(); return
        r = self.release_values[index]
        self.release_detail.setPlainText(f"{r['name']} · {r['channel']} · {r['acceptance']['status']}\nLanguage: {r['version']}\nRelease: {r['releaseId']}\n\n{r['notes']}\n\nSuite: {r['suite']['counts']}\n"+'\n'.join(c['name']+': '+c['status'] for c in r['workbench']['checks'])+'\n\nProof: '+r['workbench']['proof'])

    def export(self):
        name = self.release_list.currentText()
        if not name: return
        path,_ = QFileDialog.getSaveFileName(self.releases,'Export language release',str(self.forge.book.root/'.local'/(name+'.vayrelease.json')),'Language release (*.vayrelease.json)')
        if path: self.forge.call('forge.release.export',name=name,path=path)


class IntegrationWindow(LaboratoryWindow):
    def __init__(self,book,api):
        super().__init__(book,api)
        self.forge_panel.integration = IntegrationPanel(self.forge_panel)
        fit=next(b for b in self.findChildren(QPushButton) if b.text()=='Fit page')
        fit.setText('Fit Height');fit.setAccessibleName('Fit Height');fit.clicked.disconnect()
        fit.clicked.connect(lambda:self.invoke('ui.workspace',fit_height=True))
        fit.setToolTip('Fit the page height to the preview. Document size and type stay unchanged.')
        row=self.preview.parentWidget().layout().itemAt(1).layout()
        width=self.button('Fit Width',lambda:self.invoke('ui.workspace',fit_width=True));width.setAccessibleName('Fit Width')
        width.setToolTip('Fit the visible page width and align its top below the ruler; scroll or use Hand to move vertically.')
        row.insertWidget(row.indexOf(fit)+1,width)
        self.preview.auto_center_single = True; self.preview._center_signature = None; self.preview.update_page()
        for label in self.findChildren(QLabel):
            if '/  M8' in label.text(): label.setText(label.text().replace('/  M8','/  M9'))
        self.setWindowTitle(self.windowTitle().replace('M8','M9'))

    def refresh(self):
        super().refresh(); self.setWindowTitle(self.windowTitle().replace('M8','M9'))

    def fitted_zoom(self,*,fit_height):
        area=self.preview.display_rect();viewport=self.preview.viewport()
        ratio=(viewport.height()-56)/area.height() if fit_height else (viewport.width()-56)/area.width()
        return int(max(.1,min(3,ratio))*100)/100

    def configure_workspace(self,fit_height=False,fit_width=False,**params):
        if sum(bool(v) for v in (fit_height,fit_width,params.get('fit_page',False)))>1:
            raise ValueError('CHOOSE_ONE_FIT_MODE')
        result=super().configure_workspace(**params)
        if fit_height or fit_width:
            self.centralWidget().layout().activate();QApplication.processEvents()
            self.invoke('view.configure',zoom=self.fitted_zoom(fit_height=fit_height));self.preview.center_page()
            if fit_width:self.preview.verticalScrollBar().setValue(0)
        return result

    def show_forge(self,merge_source=None,release_name=None,**params):
        result=super().show_forge(**params)
        panel=self.forge_panel.integration
        if merge_source:
            plan=self.api.dispatch('forge.merge.preview',dict(source=merge_source)); panel.show_plan(plan)
        if release_name:
            if panel.release_list.findText(release_name)<0: raise ValueError('RELEASE_NOT_FOUND')
            panel.release_list.setCurrentText(release_name);panel.show_release()
        return result

    def export_proof(self,kind):
        from .proof_names import suggested_proof_path
        from .proof_options import supported_dpi
        from .pages import page_rect
        page=self.book.current_page(); requested=int(self.proof_dpi.value())
        try: dpi=supported_dpi(page_rect(page),requested)
        except ValueError as error:
            self.statusBar().showMessage(str(error),30000);return
        side=None
        if kind=='svg' and self.preview.page_mode=='two':
            side=next(('Left','Right')[i] for i,(shown,_) in enumerate(self.preview.display_pages()) if shown['pageId']==page['pageId'])
        suggestion=suggested_proof_path(self.book,kind,page_side=side)
        path,_=QFileDialog.getSaveFileName(self,'Export '+kind.upper()+' proof · '+str(dpi)+' DPI',suggestion,kind.upper()+' (*.'+kind+')',options=QFileDialog.Option.DontConfirmOverwrite)
        if not path: return
        # QFileDialog's typed filename may omit the suffix.
        if not path.lower().endswith('.'+kind): path+='.'+kind
        from pathlib import Path
        from tools.m0.common import file_hash
        replace={}
        if Path(path).exists():
            if not Path(path).is_file(): self.statusBar().showMessage('Export path must be a file.');return
            previous=file_hash(Path(path))
            if QMessageBox.question(self,'Replace proof?',path+' already exists. Replace it when the new proof finishes?',QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)!=QMessageBox.StandardButton.Yes: return
            replace['replace_sha256']=previous
        result=self.invoke('jobs.export',path=path,format=kind,mode=self.book.view['mode'],dpi=dpi,raster_policy='raster',page_id=page['pageId'],**replace)
        if result:
            self.poll_jobs()
            message=f'Exporting {kind.upper()} at {dpi} DPI'
            if dpi!=requested: message+=f' (requested {requested}; adjusted to fit the image-size limit)'
            self.statusBar().showMessage(message+' · '+path,30000)
            self.book.log.emit('publication','DESKTOP_PROOF_REQUESTED',requestedDpi=requested,actualDpi=dpi,path=path)
