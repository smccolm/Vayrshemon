"""Local source-font acceptance: live MCP authoring, native UI and headless replay.

Run with python -m tools.verify_m2. Artifacts and source paths stay in .local.
Uses a separate session/descriptor and never changes the user's active window.
"""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
if os.name!='nt': os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtCore import QProcess,QEvent,QCoreApplication
from PySide6.QtWidgets import QApplication
from tools.m0.common import load_json,write_json
from vayrshemon.authoring import AuthoringSession
from vayrshemon.editor_api import EditorAPI,METHODS
from vayrshemon.editor_window import EditorWindow
from vayrshemon.api import LocalServer
from vayrshemon.session import utf16_length
from vayrshemon import pages


def main():
    root=Path(__file__).resolve().parents[1]
    work=root/'.local/m2-proof'/uuid.uuid4().hex; work.mkdir(parents=True)
    for name in ('schemas','data/orthography'): shutil.copytree(root/name,work/name)
    shutil.copy2(root/'data/fonts.json',work/'data/fonts.json')
    app=QApplication.instance() or QApplication([])
    book=AuthoringSession(work,source_fonts=False); api=EditorAPI(book)
    server=LocalServer(api,publish=False); process=QProcess(); process.setWorkingDirectory(str(work))
    process.setStandardErrorFile(str(work/'mcp-stderr.log'))
    process.start(sys.executable,[str(root/'tools/run_lab.py'),'--root',str(work),'mcp','--descriptor',str(server.descriptor)])
    if not process.waitForStarted(10000): raise RuntimeError('MCP_DID_NOT_START')
    sequence=0; pending=bytearray(); transcript=[]; timings=[]; window=None
    def rpc(method,params=None,notification=False):
        nonlocal sequence,pending
        sequence+=1; request=dict(jsonrpc='2.0',method=method,params=params or {})
        if not notification: request['id']=sequence
        process.write((json.dumps(request)+'\n').encode()); process.waitForBytesWritten(1000)
        transcript.append(dict(request=request))
        if notification: return
        deadline=time.monotonic()+30
        while time.monotonic()<deadline:
            app.processEvents(); pending.extend(bytes(process.readAllStandardOutput()))
            if b'\n' in pending:
                line,_,pending=pending.partition(b'\n'); response=json.loads(line)
                transcript[-1]['response']=response
                if 'error' in response: raise RuntimeError(str(response))
                return response['result']
            time.sleep(.002)
        raise TimeoutError('MCP_RESPONSE_TIMEOUT')
    def call(method,**params):
        if METHODS[method][1]: params.update(expectedRevision=book.revision,documentId=book.state['documentId'],idempotencyKey=uuid.uuid4().hex)
        started=time.perf_counter()
        result=rpc('tools/call',dict(name=method.replace('.','_').replace('-','_'),arguments=params))
        timings.append(dict(method=method,elapsedMs=round((time.perf_counter()-started)*1000,3)))
        if result['isError']: raise RuntimeError(str(result))
        return json.loads(result['content'][0]['text'])['result']
    try:
        rpc('initialize',dict(protocolVersion='2024-11-05',capabilities={},clientInfo=dict(name='M2 acceptance',version='0.3.0')))
        rpc('notifications/initialized',notification=True)
        discovered=rpc('tools/list')['tools']
        fonts=[call('fonts.load',path=str(root/'Inputs/font files'/name))['fontId'] for name in ('Thimfora_80_Infill.ttf','Thimfora_81_Fragments.ttf','Thimfora_79.ttf')]
        call('recipe.configure',master=fonts[2],layers=fonts)
        call('document.title',title='M2 / mixed-language typography proof')
        call('page.configure',width=480.125,height=360.375,margins=dict(top=24,right=24,bottom=24,left=24))
        mapping=load_json(root/'data/orthography/thimfora-79.json')
        letters=[e for e in mapping['entries'] if e['kind']=='letter']
        letters.sort(key=lambda e:(e['symbolId'],e['form']))
        script=' '.join(chr(e['scalar']) for e in letters[:12])
        heading='Vayrshemon / M2\n'; prefix='English + '; suffix='\nSource text and font identities stay intact.\nSpacing, pages, color and recovery.'
        text=heading+prefix+script+suffix
        call('document.edit',start=0,end=0,text=text)
        call('document.format',start=0,end=utf16_length(text),size=18)
        call('document.format',start=0,end=utf16_length(heading)-1,size=28,color='#17354CFF')
        start=utf16_length(heading+prefix)
        call('document.format',start=start,end=start+utf16_length(script),font_id=fonts[2],language='language.vayrshemon',size=42,tracking=.5)
        call('paragraph.format',start=0,end=utf16_length(text),after=8,lineHeight=dict(mode='at-least',value=46))
        call('palette.apply',colors=['#43b8a0','#164e78','#78d9f2'])
        first=book.state['activeFrameId']; first_page=book.current_page()['pageId']
        call('page.add',width=360,height=480)
        call('document.edit',start=0,end=0,text=script)
        call('document.format',start=0,end=utf16_length(script),font_id=fonts[2],language='language.vayrshemon',size=38)
        call('frame.select',frame_id=first)
        call('view.configure',mode='mono'); mono=call('render.png',path=str(work/'mono.png'),mode='mono')
        call('view.configure',mode='color'); color=call('render.png',path=str(work/'color.png'),mode='color')
        call('render.svg',path=str(work/'outlines.svg'),mode='color')
        path=work/'mixed.vay.json'; call('document.save',path=str(path))
        before=call('layout.inspect')['geometryHash']; semantic=book.capture()
        window=EditorWindow(book,api); window.show(); app.processEvents(); window.refresh(); app.processEvents()
        assert pages.inspect(book)['geometryHash']==before
        window.grab().save(str(work/'editor.png'))
        call('document.edit',start=0,end=0,text='Temporary edit: ')
        call('document.open',path=str(path),discardUnsaved=True)
        after=call('layout.inspect')['geometryHash']; restored=book.capture(); restored['revision']=semantic['revision']
        assert restored==semantic and after==before
        result=subprocess.run([sys.executable,str(root/'tools/run_lab.py'),'--root',str(work),'inspect','--no-source-fonts','--document',str(path)],capture_output=True,text=True,encoding='utf-8',timeout=30)
        (work/'headless-stderr.log').write_text(result.stderr,encoding='utf-8')
        assert result.returncode==0,result.stderr
        assert json.loads(result.stdout)['geometryHash']==before
        crash_script='''import os,sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from tools.m0.common import write_json
from vayrshemon.authoring import AuthoringSession
from vayrshemon.editor_api import EditorAPI
from vayrshemon.session import utf16_length
from vayrshemon import pages
app=QApplication([]); s=AuthoringSession(Path(sys.argv[1]),source_fonts=False)
s.open(sys.argv[2],advance_revision=False)
r=EditorAPI(s).call('document.edit',dict(start=0,end=0,text='Recovered: '),expected_revision=s.revision,idempotency_key='crash-proof')
assert r['ok'],r
write_json(sys.argv[3],dict(path=str(s.recovery_path),state=s.capture(),geometryHash=pages.inspect(s)['geometryHash']))
os._exit(73)
'''
        crash=subprocess.run([sys.executable,'-c',crash_script,str(work),str(path),str(work/'crash.json')],cwd=root,capture_output=True,text=True,encoding='utf-8',timeout=30)
        (work/'crash-stderr.log').write_text(crash.stderr,encoding='utf-8'); assert crash.returncode==73,crash.stderr
        expected=load_json(work/'crash.json'); call('recovery.restore',path=expected['path'],discardUnsaved=True)
        recovered=book.capture(); recovered['revision']=expected['state']['revision']
        assert recovered==expected['state'] and pages.inspect(book)['geometryHash']==expected['geometryHash']
        from PySide6.QtGui import QImage
        assert QImage(str(work/'mono.png'))!=QImage(str(work/'color.png'))
        report=dict(application='0.3.0',engine=book.fingerprint(),sourceFontHashes=[f.split(':')[1] for f in fonts],
            checks=dict(liveMcpAuthoring=True,semanticRoundtrip=True,geometryRoundtrip=True,uiHeadlessGeometry=True,monoColorDiffer=True,outlineSvg=True,forcedExitMixedRecovery=True),
            pages=2,toolCount=len(discovered),glyphCount=len(json.loads(result.stdout)['glyphs']),geometryHash=before,recoveredGeometryHash=expected['geometryHash'],pngDimensions=[color['width'],color['height']],timings=timings)
        write_json(work/'validation.json',report); write_json(work/'mcp-transcript.json',transcript)
        print(json.dumps(dict(ok=True,output=str(work),checks=report['checks'],tools=len(discovered))))
    finally:
        process.closeWriteChannel()
        if not process.waitForFinished(5000): process.kill(); process.waitForFinished(3000)
        server.close(); book.finish()
        if window: window.timer.stop(); window.hide(); window.deleteLater()
        for frame in book.frames.values(): frame.deleteLater()
        book.deleteLater(); QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)


if __name__=='__main__': main()
