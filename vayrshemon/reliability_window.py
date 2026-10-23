"""M6 navigation, visible background proof jobs, portable backup controls."""
import json
from PySide6.QtCore import QTimer,Qt
from PySide6.QtGui import QAction,QKeySequence
from PySide6.QtWidgets import QHBoxLayout,QLabel,QFileDialog,QPlainTextEdit,QButtonGroup
from .language_window import LanguageWindow
from .proof_names import suggested_proof_path


class ReliabilityWindow(LanguageWindow):
    def __init__(self,book,api):
        super().__init__(book,api)
        for label in self.findChildren(QLabel):
            if label.text()=='LANGUAGE WORKBENCH  /  M5': label.setText('LANGUAGE WORKBENCH  /  M6')
        row=QHBoxLayout();group=QButtonGroup(self);group.setExclusive(True);self.tool_buttons={}
        for tool,label,shortcut in [('select','Select','Ctrl+Alt+V'),('hand','Hand','Ctrl+Alt+H')]:
            button=self.button(label,lambda t=tool:self.invoke('view.tool',tool=t));button.setCheckable(True)
            button.setAccessibleName(label+' tool');button.setToolTip(label+' tool · '+shortcut)
            group.addButton(button);row.addWidget(button);self.tool_buttons[tool]=button
            action=QAction(label+' tool',self);action.setShortcut(QKeySequence(shortcut));action.triggered.connect(lambda checked=False,t=tool:self.invoke('view.tool',tool=t));self.addAction(action)
        row.addWidget(self.button('Center page',lambda:self.invoke('view.center')))
        row.addWidget(self.button('Fit page',lambda:self.invoke('ui.workspace',fit_page=True)))
        row.addStretch();self.preview.parentWidget().layout().insertLayout(1,row)
        self.sync_navigation()
        form=self.add_scroll_tab('Reliability')
        self.note(form,'Every save creates a verified local backup containing the document and its exact fonts. Local backups survive source edits, but share this disk. Export a bundle to your chosen backup drive for disk-loss protection. No copies are uploaded.')
        form.addRow(self.button('Back up saved document…',self.backup_dialog))
        form.addRow(self.button('Recover backup to new folder…',self.restore_dialog))
        form.addRow(self.button('Inspect performance / cache limits',lambda:self.show_result('performance.inspect')))
        self.job_output=QPlainTextEdit();self.job_output.setReadOnly(True);self.job_output.setAccessibleName('Proof jobs and backup status');self.job_output.setMinimumHeight(180);form.addRow(self.job_output)
        form.addRow(self.button('Cancel current proof',self.cancel_job))
        self.note(form,'Select: click a frame to edit. Hand: drag the page. Ctrl+Alt+H / Ctrl+Alt+V work anywhere. With preview focus: H / V, hold Space to pan, arrows to move, Home to center. Typing in text fields keeps these characters.')
        self.job_timer=QTimer(self);self.job_timer.setInterval(500);self.job_timer.timeout.connect(self.poll_jobs);self.job_timer.start()
        self._job_signature=None;self.refresh()

    def sync_navigation(self):
        if not hasattr(self,'tool_buttons'): return
        for name,button in self.tool_buttons.items(): button.setChecked(self.preview.tool==name)
        self.preview_hint.setText('PAGE PREVIEW · Drag to move the view' if self.preview.tool=='hand' else 'PAGE PREVIEW · Click a frame to edit')

    def configure_workspace(self,**params):
        result=super().configure_workspace(**params)
        if params.get('fit_page'): self.preview.center_page()
        return result

    def refresh(self):
        super().refresh();self.setWindowTitle(self.windowTitle().replace('M5','M6'))
        if self.book.backup_error: self.statusBar().showMessage('Saved, but BACKUP FAILED: '+self.book.backup_error)

    def export_png(self): self.export_proof('png')
    def export_svg(self): self.export_proof('svg')

    def export_proof(self,kind):
        path,_=QFileDialog.getSaveFileName(self,'Export '+kind.upper()+' proof',suggested_proof_path(self.book,kind),kind.upper()+' (*.'+kind+')')
        if path:
            params=dict(path=path,format=kind,mode=self.book.view['mode'],dpi=int(self.proof_dpi.value()),raster_policy='raster')
            if kind!='pdf': params['page_id']=self.book.current_page()['pageId']
            result=self.invoke('jobs.export',**params)
            if result:
                self.statusBar().showMessage('Proof rendering in background. Reliability panel shows progress and Cancel.');self.poll_jobs()

    def poll_jobs(self):
        value=self.book.jobs.status();signature=json.dumps(dict(lastBackup=self.book.last_backup,backupError=self.book.backup_error,**value),sort_keys=True)
        if signature!=self._job_signature:
            old=self._job_signature;self._job_signature=signature
            backup=self.book.last_backup
            lines=['Backup failed: '+self.book.backup_error if self.book.backup_error else
                'Backup verified · revision '+str(backup['revision'])+'\n'+backup['path'] if backup else 'Save this document to create its local backup.']
            for job in value['jobs']:
                lines.append('Proof '+job['status']+' · revision '+str(job['revision'])+(' (earlier revision)' if job['stale'] else '')+
                    '\n'+job['progress']['phase']+'\n'+job.get('error',job['path'])+'\nLog: '+job['logPath'])
            if not value['jobs']: lines.append('No background proofs in this session.')
            self.job_output.setPlainText('\n\n'.join(lines))
            if old and value['jobs']:
                job=value['jobs'][-1]
                if job['status']!='running': self.statusBar().showMessage('Proof '+job['status']+': '+job.get('error',job['path'])+(' · from an earlier revision' if job['stale'] else ''),20000)

    def cancel_job(self):
        for job in self.book.jobs.status()['jobs']:
            if job['status']=='running': self.invoke('jobs.cancel',job_id=job['jobId'])
        self.poll_jobs()

    def backup_dialog(self):
        directory=QFileDialog.getExistingDirectory(self,'Choose backup folder',str(self.book.root/'.local/backups'))
        if directory: self.show_result('backup.create',directory=directory)

    def restore_dialog(self):
        path,_=QFileDialog.getOpenFileName(self,'Choose backup bundle',str(self.book.root/'.local/backups'),'Vayrshemon backup (*.vaybackup)')
        if not path: return
        destination,_=QFileDialog.getSaveFileName(self,'Choose a NEW recovery folder',str(self.book.root/'.local/recovered-document'),'Folder (*)')
        if destination: self.show_result('backup.restore',path=path,destination=destination)
