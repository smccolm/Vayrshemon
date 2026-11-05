"""End-to-end live Reader benchmarks against the complete four-column Bible."""
import argparse,json,time,statistics,random,ctypes
from pathlib import Path
from .control import call
from .storage import ROOT,LOCAL,dumps

def wait_action(action,timeout=60):
    end=time.perf_counter()+timeout
    while time.perf_counter()<end:
        state=call('reader.status')['result']
        if state['error']:raise RuntimeError(state['error'])
        if state['completedId']>=action:return state
        time.sleep(.015)
    raise TimeoutError('Reader action did not finish')

def memory(pid):
    from ctypes import wintypes
    class Counters(ctypes.Structure):
        _fields_=[('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD),*[(n,ctypes.c_size_t) for n in ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage','PrivateUsage')]]
    kernel=ctypes.WinDLL('kernel32',use_last_error=True);kernel.OpenProcess.restype=wintypes.HANDLE;kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
    handle=kernel.OpenProcess(0x1000|0x10,False,pid)
    if not handle:return None
    try:
        counter=Counters();counter.cb=ctypes.sizeof(counter)
        psapi=ctypes.WinDLL('psapi');psapi.GetProcessMemoryInfo.argtypes=[wintypes.HANDLE,ctypes.c_void_p,wintypes.DWORD]
        if not psapi.GetProcessMemoryInfo(handle,ctypes.byref(counter),counter.cb):return None
        return dict(pid=pid,workingSetMiB=round(counter.WorkingSetSize/1024**2,2),peakWorkingSetMiB=round(counter.PeakWorkingSetSize/1024**2,2),privateMiB=round(counter.PrivateUsage/1024**2,2))
    finally:
        kernel.CloseHandle.argtypes=[wintypes.HANDLE];kernel.CloseHandle(handle)

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',default=str(ROOT/'Saves/KJV Bible v0.10-kjv.281/KJV Bible.vay'));p.add_argument('--output',default=str(LOCAL/'benchmarks/live.json'));args=p.parse_args()
    output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True);results=[];started=time.perf_counter()
    def action(label,method,params,timeout=60):
        t=time.perf_counter();r=call(method,params);aid=r['result'].get('actionId')
        state=wait_action(aid,timeout) if aid else call('reader.status')['result']
        row=dict(label=label,ms=round((time.perf_counter()-t)*1000,2),dispatchMs=round(r['dispatchMs'],3),page=state['page'],mode=state['mode'],palette=state['palette']);results.append(row);print(json.dumps(row),flush=True);output.write_bytes(dumps(dict(source=args.source,results=results,incomplete=True)));return state
    state=call('reader.status')['result']
    if state['opening'] or state['busy']:wait_action(state['actionId'],90)
    call('reader.close')
    state=action('indexed reopen','reader.open',dict(path=args.source,restore=False),90)
    if state['pageCount']<20000:raise AssertionError('Benchmark requires the full 20k-page Bible')
    for palette in ('white','black','color'):
        action(palette+' palette','reader.palette',dict(palette=palette))
        for mode in ('one','two'):
            action(palette+' '+mode+' mode','reader.mode',dict(mode=mode))
            for page in (1,101,10001,20779):
                action(palette+' '+mode+' jump '+str(page),'reader.page',dict(page=page))
            action(palette+' '+mode+' previous','reader.page',dict(direction='previous'))
            action(palette+' '+mode+' next','reader.page',dict(direction='next'))
            action(palette+' '+mode+' warm revisit','reader.page',dict(page=10001))
        action(palette+' zoom 100%','reader.zoom',dict(zoom=1.0))
        action(palette+' zoom 150%','reader.zoom',dict(zoom=1.5))
        action(palette+' fit width','reader.fit',dict(fit='width'))
        for _ in range(10):action(palette+' pan','reader.pan',dict(dx=100,dy=120))
        action(palette+' fit height','reader.fit',dict(fit='height'))
    for query in ('In the beginning','Jerusalem','heaven and earth','Revelation'):
        t=time.perf_counter();call('reader.search',dict(query=query))
        while True:
            state=call('reader.status')['result']
            if state['searchDone']:break
            if time.perf_counter()-t>30:raise TimeoutError('Search timed out')
            time.sleep(.02)
        row=dict(label='search '+query,ms=round((time.perf_counter()-t)*1000,2),matches=len(state['searchResults']));results.append(row);print(json.dumps(row),flush=True)
    action('explicit right page','reader.page',dict(page=20000))
    assert call('reader.status')['result']['visible']==[19999,20000]
    action('right page then next','reader.page',dict(direction='next'))
    assert call('reader.status')['result']['page']==20001
    for page in (1,state['pageCount']):action('boundary '+str(page),'reader.page',dict(page=page))
    for bad in (0,state['pageCount']+1):
        try:call('reader.page',dict(page=bad));raise AssertionError('Invalid page accepted')
        except RuntimeError:pass
    # Hammer changes without waiting. Only the final target should win.
    t=time.perf_counter()
    for page in (11001,3001,19001,5001,12001):r=call('reader.page',dict(page=page))
    state=wait_action(r['result']['actionId']);assert state['page']==12001
    results.append(dict(label='five rapid distant jumps to final page',ms=round((time.perf_counter()-t)*1000,2)))
    action('restore opening','reader.page',dict(page=1));action('restore white','reader.palette',dict(palette='white'));action('restore height','reader.fit',dict(fit='height'))
    time.sleep(.2);state=call('reader.status')['result'];perf=call('reader.performance',dict(limit=3000))['result']
    report=dict(source=args.source,pageCount=state['pageCount'],seconds=round(time.perf_counter()-started,2),results=results,performance=perf,memory=[memory(pid) for pid in [state['pid'],*[w['pid'] for w in state['workers']]]],incomplete=False)
    output.write_bytes(dumps(report));print('REPORT '+str(output),flush=True)

if __name__=='__main__':main()
