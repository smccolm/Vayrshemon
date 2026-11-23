"""Bind the issued native volumes, retaining their typeset pages and duplex positions."""
from copy import deepcopy
import gc
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from PySide6.QtWidgets import QApplication
from tools import shakespeare_collected as sc
from tools.reciprocal_publication import FOLDER,ROOT,STAGE,WORK,sha
from vayrshemon import saved_preview
from vayrshemon.file_api import FileSession
from vayrshemon.json_stream import write_atomic
from vayrshemon.native_storage import MAX_FILE_BYTES,pack

NAME='Vayrshemon Dictionary and Thesaurus - Complete Print Edition.vay'
DOCKEY='document.reciprocal.complete.letter'

def page_proof(page,layout):
    text=sc.pe.text_of(page)
    geometry=json.dumps(layout,ensure_ascii=False,sort_keys=True,separators=(',',':'))
    return sha256((text+'\0'+geometry).encode()).hexdigest()

def main():
    app=QApplication.instance() or QApplication([])
    plan=json.loads((WORK/'complete-pdf.json').read_text('utf8'));meta=json.loads((WORK/'volumes.json').read_text('utf8'))
    shell=None;state=None;edition=None;expected=[];source_count=0;sections=[]
    def append_page(page,spec,title):
        pid='page.reciprocal.complete.'+str(len(expected)+1);fid=pid.replace('page.','frame.',1)
        page.update(pageId=pid,name=title)
        frame=page['frames'][0];frame['frameId']=fid;frame['content']['document']['documentId']=DOCKEY
        state['pages'].append(page);edition['pages'][pid]=spec
        text=sc.pe.text_of(page)
        if text:edition['verses'].append(dict(id=pid,sha256=sc.pe.hash_text(text),fragments=[dict(pageId=pid,start=0,end=len(text))]))
        expected.append(page_proof(page,spec))
        return pid
    for part,v in zip(plan['volumes'],meta,strict=True):
        n=v['number'];source=FOLDER['print']/(v['name']+'.vay')
        checked=json.loads((WORK/'Publication'/f'print-{n:02d}.json').read_text('utf8'))
        assert checked['sha256']==sha(source)
        incoming=sc.unpack(sc.read(source));s=incoming['state'];se=s['printEdition']
        if shell is None:
            shell=incoming.copy();state=s.copy();edition=se.copy()
            shell['state']=state;state.update(documentId=DOCKEY,title='Vayrshemon Dictionary and Thesaurus',pages=[],printEdition=edition)
            edition.update(pages={},verses=[],sections=[],sourceSha256=plan['sha256'],ledgerSha256=sha(WORK/'reciprocal-lexicon.json.gz'))
        assert s['fontSources']==state['fontSources'] and se['typography']==edition['typography'] and not se['assets']
        blank=s['pages'][1];blank_spec=se['pages'][blank['pageId']]
        if n>1:
            # The complete PDF has one external binding blank at its beginning.
            # From volume two onward its binding blanks are actual internal native pages.
            while len(expected)+2<=part['firstPhysicalPage']:
                append_page(deepcopy(blank),deepcopy(blank_spec),'Binding blank')
        assert len(expected)+2==part['firstPhysicalPage']+1
        first_open=True
        for page in s['pages']:
            pid=page['pageId'];spec=se['pages'][pid];orig=page_proof(page,spec)
            mapped=append_page(page,spec,v['name']+' · '+page['name'])
            assert orig==expected[-1];source_count+=1
            if first_open and spec['kind']=='opening':
                edition['sections'].append(dict(number=n,pageId=mapped,name=v['name']+' · '+v['first']+' – '+v['last']))
                first_open=False
        assert len(expected)+1==part['lastPhysicalPage']
    assert len(expected)+1==plan['physicalPDFPages'] and len(edition['sections'])==len(meta)
    state['activeFrameId']=state['pages'][0]['frames'][0]['frameId']
    shell['shellPreview']=deepcopy(shell['shellPreview'])
    shell['shellPreview'].update(pageIds=[p['pageId'] for p in state['pages'][:2]],stateSha256=saved_preview.state_hash(state))
    saved_preview.validate(shell['shellPreview'],state);sc.pe.validate(state)
    dest=FOLDER['print']/NAME
    with TemporaryDirectory(dir=STAGE) as tmp:
        path=Path(tmp)/NAME
        payload=pack(shell);write_atomic(path,payload,limit=MAX_FILE_BYTES)
        del payload,shell,state,edition,s,se,incoming,page,spec;gc.collect()
        session=FileSession(ROOT,source_fonts=False,recovery=False)
        session.remember=lambda *a,**kw:None;session.log.emit=lambda *a,**kw:None
        try:
            session.open(path,advance_revision=False)
            reopened=session.state;assert len(reopened['pages'])==len(expected) and session.saved_page_mode=='two'
            for p,proof in zip(reopened['pages'],expected,strict=True):
                assert page_proof(p,reopened['printEdition']['pages'][p['pageId']])==proof
        finally:session.finish()
        path.replace(dest)
    report=dict(file=NAME,sha256=sha(dest),originalNativePages=source_count,pages=len(expected),physicalPDFPages=plan['physicalPDFPages'],
      volumeOpenings=len(meta),nativeReopened=True,everyNativePageTextAndPrintGeometryVerified=True)
    (WORK/'complete-print-native.json').write_text(json.dumps(report,indent=1),encoding='utf8');print(report,flush=True)
if __name__=='__main__':main()
