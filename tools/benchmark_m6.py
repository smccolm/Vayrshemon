"""Reproducible synthetic 100-page/100k-scalar and large-page latency evidence."""
import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import platform
import statistics
import time
import uuid
if os.name!='nt': os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication
from vayrshemon.authoring import blank_content,identity
from vayrshemon.reliability_session import ReliabilitySession
from vayrshemon.reliability_api import ReliabilityAPI
from vayrshemon.reliability_window import ReliabilityWindow
from vayrshemon import pages
from tools.m0.common import write_json


def timed(callback):
    start=time.perf_counter();value=callback();return value,(time.perf_counter()-start)*1000


def memory():
    if os.name!='nt': return None
    import ctypes
    from ctypes import wintypes
    class Counters(ctypes.Structure):
        _fields_=[('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD)]+[(name,ctypes.c_size_t) for name in ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage')]
    data=Counters();data.cb=ctypes.sizeof(data)
    kernel=ctypes.WinDLL('kernel32');kernel.GetCurrentProcess.restype=wintypes.HANDLE
    psapi=ctypes.WinDLL('psapi');psapi.GetProcessMemoryInfo.argtypes=[wintypes.HANDLE,ctypes.POINTER(Counters),wintypes.DWORD]
    if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(),ctypes.byref(data),data.cb): return None
    return dict(workingSetBytes=data.WorkingSetSize,peakWorkingSetBytes=data.PeakWorkingSetSize,privateCommitBytes=data.PagefileUsage)


def run(root,out,decorative=None):
    app=QApplication.instance() or QApplication([]);s=ReliabilitySession(root,source_fonts=False,recovery=False);api=ReliabilityAPI(s)
    def call(method,**params):
        result=api.call(method,params,expected_revision=s.revision,idempotency_key=uuid.uuid4().hex,origin='desktop')
        if not result['ok']: raise ValueError(result)
        return result['result']
    try:
        state=deepcopy(s.state);state['pages']=[]
        text=('Synthetic benchmark paragraph. '*40)[:1000]
        for _ in range(100):
            page=s.make_page(state['documentId'],612,792);f=page['frames'][0]
            f['content']=blank_content(state['documentId'],f['width'],f['height'],text);state['pages'].append(page)
        state['activeFrameId']=state['pages'][0]['frames'][0]['frameId']
        _,load_ms=timed(lambda:s._restore(state));s._state=s.capture()
        _,cold_ms=timed(lambda:pages.inspect(s,max_glyphs=1200));_,warm_ms=timed(lambda:pages.inspect(s,max_glyphs=1200))
        window=ReliabilityWindow(s,api);window.show();call('ui.workspace',source=False,diagnostics=False,guides=False,fit_page=True);app.processEvents()
        edit=[];pan=[];shapes=s.story_cache.info()
        for i in range(10):
            def edit_paint():
                call('document.edit',start=0,end=1,text='A' if i%2==0 else 'B');window.preview.viewport().repaint();app.processEvents()
            _,duration=timed(edit_paint);edit.append(duration)
        call('view.tool',tool='hand')
        for i in range(30):
            def pan_paint(): window.preview.pan_by(8 if i%2 else -8,4);window.preview.viewport().repaint();app.processEvents()
            _,duration=timed(pan_paint);pan.append(duration)
        info=s.story_cache.info();window.hide();window.job_timer.stop();window.deleteLater();s.window=None
        result=dict(version='1.0.0',machine=dict(os=platform.platform(),processor=platform.processor(),cpuCount=os.cpu_count(),python=platform.python_version()),
            scenario=dict(pages=100,scalars=100000,frames=100,font='system Segoe UI on Windows; platform default elsewhere',effects='none',recovery='disabled for timing; full snapshot/validation/undo enabled'),
            loadMs=load_ms,coldPageInspectMs=cold_ms,warmPageInspectMs=warm_ms,
            editToPagePaintMs=dict(samples=edit,p95=sorted(edit)[-1],definition='API edit plus synchronous page paint and event pump, not physical input latency; 10-sample nearest rank'),
            panPaintMs=dict(samples=pan,p95=sorted(pan)[28]),memory=memory(),cache=info,
            incremental=dict(rebuiltStories=info['misses']-shapes['misses'],expectedLocalEdits=10,wholeDocumentShaping=False),
            budgets=dict(edit50msMet=max(edit)<50,pan16_7msMet=sorted(pan)[28]<16.7))
        if decorative:
            call('document.open',path=str(decorative),discardUnsaved=True)
        call('page.configure',width=10000,height=12000)
        _,large=timed(lambda:pages.render(s,None,mode='color',dpi=96,region=[0,0,1200,1200]))
        result['largePage']=dict(points=[10000,12000],regionPixels=[1200,1200],renderMs=large,actualLayeredFonts=bool(decorative),memory=memory(),fullRaster='Rejected above 32,767 pixels per axis or 16 million pixels; use bounded regions')
        write_json(out,result);return result
    finally: s.finish()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--decorative',type=Path);a=p.parse_args()
    value=run(Path(__file__).resolve().parents[1],a.out,a.decorative);print(json.dumps(value,indent=2))
