"""Cold-index and restart timings in an isolated disposable Reader profile."""
import json,os,subprocess,time
from pathlib import Path
from .storage import ROOT,LOCAL,dumps,file_hash
from .control import call
from .benchmark import memory

def main():
    source=ROOT/'Saves/KJV Bible v0.10-kjv.282/KJV Bible.vay';sha=file_hash(source)
    profile=LOCAL/'benchmarks'/('cold-'+time.strftime('%Y%m%d-%H%M%S'));profile.mkdir(parents=True)
    descriptor=profile/'run/active.json';env=dict(os.environ,VAY_READER_CACHE=str(profile),PYTHONUTF8='1')
    results=[]
    def request(method,params=None):return call(method,params,descriptor)
    for label in ('first use including index','restart with index and page cache'):
        started=time.perf_counter();subprocess.Popen([str(ROOT/'.venv/Scripts/pythonw.exe'),str(ROOT/'Reader/launch.py'),str(source),'--no-restore'],cwd=ROOT,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
        end=time.perf_counter()+120
        while True:
            if time.perf_counter()>end:raise TimeoutError(label)
            try:
                state=request('reader.status')['result']
                if state['error']:raise RuntimeError(state['error'])
                if state['pageCount'] and not state['opening'] and not state['busy']:break
            except (FileNotFoundError,ConnectionError):pass
            time.sleep(.025)
        elapsed=(time.perf_counter()-started)*1000
        performance=request('reader.performance',dict(limit=3000))['result']
        row=dict(label=label,readyMs=round(elapsed,2),pageCount=state['pageCount'],state=state,performance=performance,
                 memory=[memory(p) for p in [state['pid'],*[w['pid'] for w in state['workers']]]])
        results.append(row);print(label,round(elapsed,2),'ms',flush=True)
        t=time.perf_counter();request('reader.close');row['closeMs']=round((time.perf_counter()-t)*1000,2)
        request('reader.quit')
        while descriptor.exists() and time.perf_counter()<end:time.sleep(.025)
    assert file_hash(source)==sha
    report=dict(source=str(source),sha256=sha,sourceUnchanged=True,profile=str(profile),results=results)
    path=LOCAL/'benchmarks/lifecycle.json';path.write_bytes(dumps(report));print('REPORT',path)

if __name__=='__main__':main()
