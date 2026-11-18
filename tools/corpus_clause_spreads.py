"""Recompose only spreads containing a reviewed correction, using the issued type and fonts."""
from copy import deepcopy
import os,sys
from tools.corpus_clause_revision import *
from tools.compose_historical_book import texts,body
from vayrshemon import reading,pages,paragraph_alignment,saved_preview
from vayrshemon.file_api import FileSession
from vayrshemon.native_storage import pack,unpack
from vayrshemon.json_stream import write_atomic
from PySide6.QtWidgets import QApplication

def save_native(payload,path):
    state=payload['state']
    payload['shellPreview']['stateSha256']=saved_preview.state_hash(state)
    out=revised(path);out.parent.mkdir(parents=True,exist_ok=True)
    write_atomic(out,pack(payload))
    return out

def checked_spread(session,base,pair,units):
    state=dict(base,pages=deepcopy(pair))
    frames=[]
    for pg in state['pages']:
        pg['frames']=[f for f in pg['frames'] if f['name']!='Book title']
        frames.extend(sorted(pg['frames'],key=lambda f:int(f['x'])))
    assert len(frames)==4
    ids=[f['frameId'] for f in frames];state['activeFrameId']=ids[0]
    state['typesetting']=dict(base['typesetting'],frames={i:base['typesetting']['frames'][i] for i in ids if i in base['typesetting']['frames']})
    state['view']=dict(base['view'],activePageId=pair[0]['pageId']) if 'activePageId' in base['view'] else base['view']
    fonts=[session.fonts.faces['font:'+reading.SCRIPT_SHA+':0'],reading.font(session,'transliteration')]
    for i,(frame,field) in enumerate(zip(frames,('text','text','gloss','source'))):
        desired=[v[field] for v in units]
        if desired!=texts(frame):
            body(frame,desired,fonts[min(i,1)],reading.font(session,'literal'),i)
    for gap in (24,20,16,12,8,4,1):
        if gap!=24:
            for frame in frames:
                for paragraph in frame['content']['paragraphs']:paragraph['after']=gap
        session._restore(state)
        session._state=session.capture()
        session.invalidate_composition()
        try:
            paragraph_alignment.align(session,ids)
            break
        except ValueError as error:
            if 'PARAGRAPH_ALIGNMENT_OVERSET' not in str(error) or gap==1:raise
    final=session.capture()
    for p,issued in zip(final['pages'],pair,strict=True):
        report=pages.inspect(session,page_id=p['pageId'],max_glyphs=100000)
        assert not report.get('truncated') and not any(g['missingGlyph'] for g in report['glyphs'])
        for f in report['frames']:
            x,y,w,h=f['rect']
            for line in f['layout']['lines']:
                dx,dy,dw,dh=line['advanceBounds']
                assert dx+dw<=x+w+1.00001 and dy+dh<=y+h+.05,(issued['name'],f['name'],dx+dw-x-w,dy+dh-y-h)
        lookup={f['frameId']:f for f in p['frames']}
        issued['frames']=[lookup.get(f['frameId'],f) for f in issued['frames']]
    return final

def run(group):
    changes=read(S/'changes.json')
    worklist=sources()
    def inputs():
        if group=='bible':
            for u in read(edited(B/'complete-translation-ledger.json'))['units']:yield 'bible',u
        else:
            for w in worklist:
                for u in read(edited(ledger(w)))['units']:yield w['slug'],u
    source=next((B if group=='bible' else HP).glob('*.vay'))
    payload=unpack(read(edited(source)));state=payload['state'];rows=iter(inputs())
    app=QApplication.instance() or QApplication([]);session=FileSession(ROOT,source_fonts=False,recovery=False)
    session.remember=lambda p:None;session.log.emit=lambda *a,**k:None
    session.open(SV/'Archive'/'Black on white.vay',advance_revision=False)
    base={k:v for k,v in state.items() if k not in ('language','pages')}
    base['language']=session.capture()['language']
    changed_pages={};seen=0
    try:
        for i in range(0,len(state['pages']),2):
            pair=state['pages'][i:i+2]
            f=next(f for f in pair[0]['frames'] if f['name']=='Vayrshemon')
            us=[next(rows) for _ in texts(f)];seen+=len(us)
            if any(u['id'] in changes.get(slug,{}) for slug,u in us):
                fields=('text','text','gloss','source')
                cols=[texts(fr) for pg in pair for fr in sorted(pg['frames'],key=lambda fr:int(fr['x'])) if fr['name']!='Book title']
                if cols!=[[u[k] for _,u in us] for k in fields]:
                    try:final=checked_spread(session,base,pair,[u for _,u in us])
                    except Exception as e:raise ValueError((i+1,[(slug,u['id']) for slug,u in us],str(e))) from e
                    for pid,config in final['typesetting']['frames'].items():state['typesetting']['frames'][pid]=config
                for j,p in enumerate(pair):changed_pages[p['pageId']]=(us[0][0],i+j+1)
            for a,field in zip([f for p in pair for f in sorted(p['frames'],key=lambda f:int(f['x'])) if f['name']!='Book title'],('text','text','gloss','source'),strict=True):
                assert texts(a)==[u[field] for _,u in us],(i,field)
        assert next(rows,None) is None
        path=save_native(payload,source)
        print(group,len(changed_pages),seen,sha(path),flush=True)
        if group!='bible':
            # Propagate these exact composed pages to their individual manuscripts.
            lookup={p['pageId']:p for p in state['pages'] if p['pageId'] in changed_pages}
            for w in worklist:
                if w['slug'] not in changes:continue
                individual=saved_source(w['output']);book=unpack(read(individual))
                local=book['state']
                for pg in local['pages']:
                    if pg['pageId'] not in lookup:continue
                    for dst,src in zip(pg['frames'],lookup[pg['pageId']]['frames'],strict=True):
                        assert dst['frameId']==src['frameId']
                        dst['content']=deepcopy(src['content']);dst['content']['document']['documentId']=local['documentId']
                        fid=dst['frameId']
                        if fid in state['typesetting']['frames']:local['typesetting']['frames'][fid]=state['typesetting']['frames'][fid]
                save_native(book,individual)
        write(S/(group+'-spreads.json'),changed_pages)
    finally:session.finish()
if __name__=='__main__':run(sys.argv[1])

