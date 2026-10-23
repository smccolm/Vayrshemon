"""Reproducible local M1 proof; original assets and images stay under .local."""
from copy import deepcopy
import ctypes
from datetime import datetime, timezone
import math
import os
import platform
import statistics
import time
import uuid

from PySide6.QtCore import Qt, QCoreApplication
from PySide6.QtGui import QInputMethodEvent, QTextCursor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from tools.m0.synthetic import document, unicode_run
from tools.m0.common import write_json
from .api import API
from .desktop import LabWindow, accessibility
from . import layout


def memory_bytes():
    if os.name == 'nt':
        class Counters(ctypes.Structure):
            _fields_ = [('cb',ctypes.c_ulong),('pageFaults',ctypes.c_ulong)] + [(name,ctypes.c_size_t) for name in
                ('peakWorkingSet','workingSet','quotaPeakPaged','quotaPaged','quotaPeakNonpaged','quotaNonpaged','pagefile','peakPagefile')]
        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        kernel = ctypes.WinDLL('kernel32')
        kernel.GetCurrentProcess.restype = ctypes.c_void_p
        psapi = ctypes.WinDLL('psapi')
        psapi.GetProcessMemoryInfo.argtypes = [ctypes.c_void_p,ctypes.POINTER(Counters),ctypes.c_ulong]
        if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(),ctypes.byref(counters),counters.cb):
            raise OSError('MEMORY_MEASUREMENT_FAILED')
        return counters.workingSet
    import resource
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if platform.system()=='Darwin' else 1024)


def distribution(values):
    ordered=sorted(values)
    return dict(samples=len(values),medianMs=statistics.median(values),p95Ms=ordered[max(0,math.ceil(len(values)*.95)-1)],maxMs=max(values))


def benchmark(session):
    app=QApplication.instance()
    proof=session.root/'.local/m1-proof'/uuid.uuid4().hex
    proof.mkdir(parents=True)
    original=session.snapshot()
    before=layout.inspect(session)
    initial_memory=memory_bytes()
    api=API(session)
    window=LabWindow(session,api)
    window.show()
    app.processEvents()
    after=layout.inspect(session)
    parity=before['geometryHash']==after['geometryHash']
    if not parity:
        raise AssertionError('UI_HEADLESS_GEOMETRY_MISMATCH')
    window.grab().save(str(proof/'window.png'))
    mono,mono_report=layout.render(session,proof/'mono.png',mode='mono')
    color,color_report=layout.render(session,proof/'color.png',mode='color')
    layout.render(session,proof/'overlays.png',mode='color',overlays={'baselines':True,'origins':True,'bounds':True})
    native_access=accessibility(window.editor)
    cursor=window.editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    window.editor.setTextCursor(cursor)
    window.editor.setFocus()
    session.timings=[]
    for _ in range(40):
        QTest.keyClick(window.editor,Qt.Key.Key_X)
        app.processEvents()
        QTest.qWait(5)
    input_times=list(session.timings)
    if not input_times:
        raise AssertionError('NO_NATIVE_PAINT_MEASUREMENTS')
    started=time.perf_counter()
    window.refresh()
    inspector_ms=(time.perf_counter()-started)*1000
    session.load_model(original)
    app.processEvents()
    # Exercise the actual input-method event path, without claiming an installed
    # OS IME candidate-window/keyboard test that this experiment did not perform.
    cursor=window.editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    window.editor.setTextCursor(cursor)
    QCoreApplication.sendEvent(window.editor,QInputMethodEvent('かな',[]))
    preedit_hidden_from_saved_text='かな' not in session.text()
    event=QInputMethodEvent()
    event.setCommitString('仮名')
    QCoreApplication.sendEvent(window.editor,event)
    ime_committed=session.text().endswith('仮名')
    session.load_model(original)
    model=session.snapshot()
    session.save(proof/'roundtrip.vaylab.json')
    session.open(proof/'roundtrip.vaylab.json')
    roundtrip=model==session.snapshot()
    app.processEvents()
    geometry_before_dpi=layout.inspect(session)['geometryHash']
    _,dpi96=layout.render(session,region=[0,0,256,256],dpi=96)
    _,dpi192=layout.render(session,region=[0,0,256,256],dpi=192)
    dpi_stable=geometry_before_dpi==layout.inspect(session)['geometryHash']
    paint_times=[]
    for _ in range(30):
        _,report=layout.render(session,region=[0,0,512,256])
        paint_times.append(report['elapsedMs'])
    large_text=('AV office A\u0301 / typography. '*5000)[:100000]
    large=document('document.benchmark.large',[unicode_run(large_text)])
    started=time.perf_counter()
    session.load_model(large)
    session.doc.size()
    large_layout_ms=(time.perf_counter()-started)*1000
    _,large_tile=layout.render(session,region=[0,0,512,256])
    large_memory=memory_bytes()
    # M1 does not have a multi-page flow editor. Measure 100 independent page
    # layouts and label the distinction so this does not pretend to test M2.
    started=time.perf_counter()
    for index in range(100):
        page=document(f'document.benchmark.page{index}',[unicode_run(large_text[index*1000:(index+1)*1000])])
        session.load_model(page)
        session.doc.size()
    hundred_pages_ms=(time.perf_counter()-started)*1000
    session.set_page(1000000,1000000)
    _,huge_tile=layout.render(session,region=[0,0,512,256])
    session.load_model(original)
    app.processEvents()
    result=dict(schemaVersion='0.1.0',milestone='M1',timestampUtc=datetime.now(timezone.utc).isoformat(),
                machine=dict(os=platform.platform(),cpu=platform.processor(),logicalProcessors=os.cpu_count()),
                engine=session.fingerprint(),proofDirectory=str(proof),
                gates=dict(uiHeadlessGeometryEqual=parity,geometryHash=before['geometryHash'],
                           actualSourceFonts=bool(session.fonts.recipe),nativeAccessibleText=native_access['text']==session.text(),
                           accessibilityRole=native_access['role'],nativeTextInterface=native_access['textInterface'],
                           imePreeditNotCommitted=preedit_hidden_from_saved_text,imeCommitPassed=ime_committed,
                           saveReopenSemanticEquality=roundtrip,dpiChangeDoesNotReflow=dpi_stable),
                latency=dict(keyToNativePaint=distribution(input_times),tileRender=distribution(paint_times),
                             fullInspectorRefreshMs=inspector_ms,transport='shared in-process glyphs; no per-frame IPC copies'),
                raster=dict(mono=mono_report,color=color_report,dpi96=dpi96,dpi192=dpi192,
                            hugePageTile=huge_tile,maxPixels=layout.MAX_PIXELS),
                scale=dict(textScalars=len(large_text),largeLayoutMs=large_layout_ms,largeTextTile=large_tile,
                           independentPages=100,independentPageLayoutTotalMs=hundred_pages_ms,
                           caveat='100 separate 1000-scalar page layouts, not a paginated multi-page editor'),
                memory=dict(initialWorkingSetBytes=initial_memory,largeTextWorkingSetBytes=large_memory,
                            measurement='Windows working set; Linux/macOS peak RSS'),
                limitations=['Native IME preedit/commit events tested; OS candidate-window interaction requires an installed IME/manual pass.',
                             'Qt accessibility provider inspected; external Windows UIA computer-use approval timed out in this run.',
                             'DPI tested through raster scale and shared geometry; moving between physical monitors is a separate manual pass.',
                             'Flat color layers only; source Photoshop bevel/glow is M4.'])
    write_json(proof/'measurements.json',result)
    window.hide()
    session.log.emit('benchmark','M1_PROOF_COMPLETED',proofDirectory=str(proof),gates=result['gates'])
    return result
