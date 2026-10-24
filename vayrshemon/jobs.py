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
        path=params.pop('path');replace_sha256=params.pop('replace_sha256',None)
        page_ids=params.pop('page_ids',None);hashes=params.pop('replace_sha256s',None)
        outputs=None
        if page_ids is not None:
            from .proof_names import spread_png_paths
            if params['format']!='png' or 'page_id' in params or replace_sha256 is not None:raise ValueError('PNG_SPREAD_PARAMS')
            if not isinstance(page_ids,list) or not 1<=len(page_ids)<=2 or len(set(page_ids))!=len(page_ids):raise ValueError('PNG_SPREAD_PAGE_COUNT')
            if not set(page_ids)<={p['pageId'] for p in self.book.state['pages']}:raise ValueError('PAGE_NOT_FOUND')
            if hashes is None:hashes=[None]*len(page_ids)
            if len(hashes)!=len(page_ids):raise ValueError('PNG_SPREAD_REPLACEMENT_COUNT')
            outputs=[dict(path=p,pageId=pid,replaceSha256=h) for p,pid,h in zip(spread_png_paths(path,len(page_ids)),page_ids,hashes)]
        elif hashes is not None:raise ValueError('PNG_SPREAD_PARAMS')
        destinations=outputs or [dict(path=path,replaceSha256=replace_sha256)]
        for item in destinations:
            if item['replaceSha256'] is None:destination=target(self.book,item['path'])
            else:
                destination=self.book.output_path(item['path'])
                if not destination.is_file() or sha(destination.read_bytes())!=item['replaceSha256']:raise ValueError('EXPORT_TARGET_CHANGED')
            item['path']=str(destination)
        destination=destinations[0]['path']
        state=self.book.capture();self.book.validate(state)
        jid='job.'+uuid.uuid4().hex;folder=self.book.root/'.local/jobs'/jid;folder.mkdir(parents=True)
        snapshot=dict(format='vayrshemon.document',formatVersion=self.book.file_version,state=state,history=[],engine=self.book.fingerprint())
        write_json(folder/'snapshot.vay.json',snapshot)
        request=dict(root=str(self.book.root),params=dict(params,path=str(folder/('proof.'+params['format']))))
        if outputs:request=dict(root=str(self.book.root),outputs=[dict(params,page_id=o['pageId'],path=str(folder/f'proof-{i}.png')) for i,o in enumerate(outputs)])
        write_json(folder/'request.json',request)
        log_path=folder/'worker.log'
        env=dict(os.environ,PYTHONUTF8='1',PYTHONUNBUFFERED='1')
        if os.name!='nt': env.setdefault('QT_QPA_PLATFORM','offscreen')
        with log_path.open('wb') as log:
            process=subprocess.Popen([sys.executable,'-u','-m','vayrshemon.jobs',str(folder)],cwd=Path(__file__).resolve().parents[1],
                stdout=log,stderr=subprocess.STDOUT,env=env,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        self.jobs[jid]=dict(jobId=jid,status='running',revision=state['revision'],documentId=state['documentId'],
            path=str(destination),replaceSha256=replace_sha256,folder=str(folder),logPath=str(log_path),started=time.time(),_process=process)
        if outputs:self.jobs[jid]['outputs']=outputs
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
                result=load_json(folder/'result.json')
                outputs=job.get('outputs',[job]);results=result['outputs'] if 'outputs' in job else [result]
                if len(outputs)!=len(results):raise ValueError('WORKER_OUTPUT_COUNT_MISMATCH')
                prepared=[]
                # Verify both proofs and both chosen destinations before publishing
                # either side. A changed right file must not replace the left one.
                for item,render in zip(outputs,results):
                    proof=Path(render['path'])
                    if proof.parent!=folder:raise ValueError('WORKER_OUTPUT_PATH_MISMATCH')
                    payload=proof.read_bytes()
                    if sha(payload)!=render['sha256']:raise ValueError('WORKER_OUTPUT_HASH_MISMATCH')
                    destination=Path(item['path']);previous=item.get('replaceSha256')
                    if (previous is None and destination.exists()) or (previous is not None and (not destination.is_file() or sha(destination.read_bytes())!=previous)):
                        raise ValueError('EXPORT_TARGET_CHANGED: existing images were preserved')
                    prepared.append((item,render,payload))
                published=[]
                for item,render,payload in prepared:
                    if item.get('replaceSha256') is None:exclusive_write(item['path'],payload)
                    else:
                        destination=Path(item['path'])
                        if sha(destination.read_bytes())!=item['replaceSha256']:raise ValueError('EXPORT_TARGET_CHANGED')
                        from .publication import atomic
                        atomic(destination,payload)
                    published.append(dict(render,path=item['path']));job['publishedPaths']=[p['path'] for p in published]
                job.update(status='completed',result=dict(outputs=published) if 'outputs' in job else published[0])
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


def progress(folder,phase):
    # Windows may briefly deny atomic replacement while the UI reads progress.
    # A progress label must never turn an otherwise successful proof into failure.
    for attempt in range(4):
        try:write_json(folder/'progress.json',dict(phase=phase));return
        except PermissionError:
            if attempt<3:time.sleep(.02*(attempt+1))
            else:print('PROGRESS_UPDATE_BUSY: '+phase,file=sys.stderr,flush=True)


def worker(folder):
    folder=Path(folder).resolve();request=load_json(folder/'request.json')
    progress(folder,'opening snapshot')
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import qInstallMessageHandler
    from .reliability_session import ReliabilitySession
    from . import publication
    app=QApplication.instance() or QApplication([])
    session=ReliabilitySession(request['root'],source_fonts=False,recovery=False)
    qInstallMessageHandler(lambda kind,context,message:print(str(kind)+': '+message,file=sys.stderr,flush=True))
    try:
        session.open(folder/'snapshot.vay.json')
        results=[];outputs=request.get('outputs',[request.get('params')])
        for i,params in enumerate(outputs):
            progress(folder,f'rendering page {i+1} of {len(outputs)}')
            result=publication.export(session,**params)
            path=Path(result['path']);result['sha256']=sha(path.read_bytes());results.append(result)
        result=dict(outputs=results) if 'outputs' in request else results[0]
        write_json(folder/'result.json',result);progress(folder,'ready to publish')
    finally: session.finish()


if __name__=='__main__':
    try: worker(sys.argv[1])
    except Exception: traceback.print_exc();raise SystemExit(1)
