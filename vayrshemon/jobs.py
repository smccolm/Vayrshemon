"""One cancellable isolated proof worker per editor; no Qt objects cross threads."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
import uuid
from tools.m0.common import write_json,load_json
from tools.recovery import exclusive_write,sha


class JobManager:
    def __init__(self,book): self.book=book;self.jobs={}

    def start(self,**params):
        from .pages import target
        self.poll()
        if any(j['status']=='running' for j in self.jobs.values()): raise ValueError('JOB_BUSY: cancel or finish the current proof')
        if len(self.jobs)>=64: raise ValueError('JOB_HISTORY_LIMIT: save and reopen after 64 jobs')
        destination=target(self.book,params.pop('path'))
        state=self.book.capture();self.book.validate(state)
        jid='job.'+uuid.uuid4().hex;folder=self.book.root/'.local/jobs'/jid;folder.mkdir(parents=True)
        snapshot=dict(format='vayrshemon.document',formatVersion=self.book.file_version,state=state,history=[],engine=self.book.fingerprint())
        write_json(folder/'snapshot.vay.json',snapshot)
        request=dict(root=str(self.book.root),params=dict(params,path=str(folder/('proof.'+params['format']))))
        write_json(folder/'request.json',request)
        log_path=folder/'worker.log'
        env=dict(os.environ,PYTHONUTF8='1',PYTHONUNBUFFERED='1')
        if os.name!='nt': env.setdefault('QT_QPA_PLATFORM','offscreen')
        with log_path.open('wb') as log:
            process=subprocess.Popen([sys.executable,'-u','-m','vayrshemon.jobs',str(folder)],cwd=Path(__file__).resolve().parents[1],
                stdout=log,stderr=subprocess.STDOUT,env=env,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        self.jobs[jid]=dict(jobId=jid,status='running',revision=state['revision'],documentId=state['documentId'],
            path=str(destination),folder=str(folder),logPath=str(log_path),started=time.time(),_process=process)
        self.book.log.emit('jobs','JOB_STARTED',jobId=jid,revision=state['revision'],logPath=str(log_path))
        return self.status(jid)

    def poll(self):
        for job in self.jobs.values():
            if job['status']!='running': continue
            code=job['_process'].poll()
            if code is None: continue
            folder=Path(job['folder'])
            try:
                if code!=0: raise ValueError('PROOF_WORKER_FAILED: exit '+str(code)+'; see '+job['logPath'])
                result=load_json(folder/'result.json');proof=Path(result['path'])
                if proof.parent!=folder: raise ValueError('WORKER_OUTPUT_PATH_MISMATCH')
                payload=proof.read_bytes()
                if sha(payload)!=result['sha256']: raise ValueError('WORKER_OUTPUT_HASH_MISMATCH')
                exclusive_write(job['path'],payload)
                job.update(status='completed',result=dict(result,path=job['path']))
            except Exception as error:
                job.update(status='failed',error=str(error));self.book.log.exception('jobs',error)
            job['finished']=time.time();self.book.log.emit('jobs','JOB_FINISHED',jobId=job['jobId'],status=job['status'])

    def status(self,job_id=None):
        self.poll()
        def public(job):
            result={k:deepcopy(v) for k,v in job.items() if not k.startswith('_')}
            result['stale']=job['documentId']!=self.book.state['documentId'] or job['revision']!=self.book.revision
            progress=Path(job['folder'])/'progress.json'
            result['progress']=load_json(progress) if progress.exists() else dict(phase='starting')
            return result
        if job_id:
            if job_id not in self.jobs: raise ValueError('JOB_NOT_FOUND')
            return public(self.jobs[job_id])
        return dict(jobs=[public(j) for j in self.jobs.values()],concurrency=1,historyLimit=64)

    def cancel(self,job_id):
        if job_id not in self.jobs: raise ValueError('JOB_NOT_FOUND')
        job=self.jobs[job_id]
        # Do not poll first: cancellation wins even when the unpromoted worker
        # just completed. Its destination is never published by cancel.
        if job['status']=='running':
            process=job['_process']
            if process.poll() is None: process.kill()
            process.wait(timeout=5)
            job.update(status='cancelled',finished=time.time());self.book.log.emit('jobs','JOB_CANCELLED',jobId=job_id)
        return self.status(job_id)

    def close(self):
        for jid,job in self.jobs.items():
            if job['status']=='running': self.cancel(jid)


def worker(folder):
    folder=Path(folder).resolve();request=load_json(folder/'request.json')
    write_json(folder/'progress.json',dict(phase='opening snapshot'))
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import qInstallMessageHandler
    from .reliability_session import ReliabilitySession
    from . import publication
    app=QApplication.instance() or QApplication([])
    session=ReliabilitySession(request['root'],source_fonts=False,recovery=False)
    qInstallMessageHandler(lambda kind,context,message:print(str(kind)+': '+message,file=sys.stderr,flush=True))
    try:
        session.open(folder/'snapshot.vay.json')
        write_json(folder/'progress.json',dict(phase='preflight and rendering'))
        result=publication.export(session,**request['params'])
        path=Path(result['path']);result['sha256']=sha(path.read_bytes())
        write_json(folder/'result.json',result);write_json(folder/'progress.json',dict(phase='ready to publish'))
    finally: session.finish()


if __name__=='__main__':
    try: worker(sys.argv[1])
    except Exception: traceback.print_exc();raise SystemExit(1)
