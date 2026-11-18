"""Measure independent individual books concurrently; copy their exact corrected frames into the collection."""
from concurrent.futures import ThreadPoolExecutor
import subprocess
from tools.corpus_clause_spreads import *
def item(slug):
    w=next(w for w in sources() if w['slug']==slug);path=saved_source(w['output'])
    ledger_sha=sha(edited(ledger(w)))
    data=unpack(read(edited(path)));state=data['state'];units=iter(read(edited(ledger(w)))['units']);changes=read(S/'changes.json')[slug]
    app=QApplication.instance() or QApplication([]);session=FileSession(ROOT,source_fonts=False,recovery=False)
    session.remember=lambda p:None;session.log.emit=lambda *a,**k:None
    session.open(SV/'Archive'/'Black on white.vay',advance_revision=False)
    base={k:v for k,v in state.items() if k not in ('pages','language')};base['language']=session.capture()['language']
    pids=[];total=0
    try:
        for i in range(0,len(state['pages']),2):
            pair=state['pages'][i:i+2];fs=[f for pg in pair for f in sorted(pg['frames'],key=lambda f:int(f['x']))]
            cols=[texts(f) for f in fs];us=[next(units) for _ in cols[0]]
            if not any(u['id'] in changes for u in us):continue
            pids.extend(p['pageId'] for p in pair)
            if cols!=[[u[k] for u in us] for k in ('text','text','gloss','source')]:
                try:fx=checked_spread(session,base,pair,us)
                except Exception as exc:raise ValueError((slug,i+1,[u['id'] for u in us],str(exc))) from exc
                for fid,cfg in fx['typesetting']['frames'].items():state['typesetting']['frames'][fid]=cfg
                total+=1
        assert next(units,None) is None
        if total:
            if set(data['shellPreview']['pageIds'])&set(pids):
                # Only the current spread is required to render the thumbnail.
                assert data['shellPreview']['pageIds']==[pg['pageId'] for pg in state['pages'][:2]]
                subset=dict(base,pages=state['pages'][:2],activeFrameId=state['activeFrameId'])
                ids={f['frameId'] for pg in subset['pages'] for f in pg['frames']}
                subset['typesetting']=dict(base['typesetting'],frames={k:v for k,v in base['typesetting']['frames'].items() if k in ids})
                session._restore(subset);img=saved_preview.create(session,session.capture(),'two')
                data['shellPreview']['image']=img['image'] if 'image' in img else data['shellPreview'].get('image')
                if 'image' not in img:data['shellPreview'].pop('image',None)
                for k in img:
                    if k not in ('revision','stateSha256'):data['shellPreview'][k]=img[k]
            save_native(data,path)
        assert ledger_sha==sha(edited(ledger(w)))
        write(S/'recomposed'/f'{slug}.json',dict(ledger=ledger_sha,pages=pids,hash=sha(edited(path))))
        print(slug,total,flush=True)
    finally:session.finish()
def rebuild():
    changes=read(S/'changes.json');works=[w for w in sources() if w['slug'] in changes]
    def measure(w):
        slug=w['slug'];report=S/'recomposed'/f'{slug}.json'
        if report.exists() and read(report)['ledger']==sha(edited(ledger(w))):return
        logs=S/'measure-logs';logs.mkdir(exist_ok=True)
        with (logs/(slug+'.txt')).open('w',encoding='utf8') as f:
            job=subprocess.run([sys.executable,'-B','-u','-m','tools.corpus_clause_parallel',slug],stdout=f,stderr=subprocess.STDOUT)
        print(slug,job.returncode,flush=True);return job.returncode
    with ThreadPoolExecutor(max_workers=8) as pool:fail=list(pool.map(measure,works))
    if any(fail):raise ValueError('One or more individual works require reflow; see measure-logs.')
    path=next(HP.glob('*.vay'));data=unpack(read(path));state=data['state']
    indexed={p['pageId']:(i,p) for i,p in enumerate(state['pages'],1)};report={}
    for w in works:
        single=saved_source(w['output']);work=unpack(read(edited(single)))['state']
        pids=set(read(S/'recomposed'/(w['slug']+'.json'))['pages'])
        for pg in work['pages']:
            if pg['pageId'] not in pids:continue
            i,dest=indexed[pg['pageId']];report[pg['pageId']]=(w['slug'],i)
            for fr,df in zip(pg['frames'],dest['frames'],strict=True):
                fid=fr['frameId'];assert fid==df['frameId']
                df['content']=deepcopy(fr['content']);df['content']['document']['documentId']=state['documentId']
                if fid in work['typesetting']['frames']:state['typesetting']['frames'][fid]=work['typesetting']['frames'][fid]
    save_native(data,path);write(S/'shakespeare-spreads.json',report)
    print('Collected corrected pages',len(report),flush=True)
if __name__=='__main__':
    if len(sys.argv)>1:item(sys.argv[1])
    else:rebuild()

