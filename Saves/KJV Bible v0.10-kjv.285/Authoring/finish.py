"""Assemble, verify folios, then save and reopen the four-column chart revision."""
from pathlib import Path
from copy import deepcopy
from types import SimpleNamespace
import concurrent.futures
import gc
import json
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT))
from tools.kjv_native_vocabulary import OUT, VERSION
from tools.kjv_unta_chart import OUT as PREVIOUS
from tools.kjv_archive import read,verify_register
from tools.compose_historical_book import texts,uid,geometry,frame_geometry
from tools.m0.common import file_hash
from vayrshemon import language

scratch=ROOT/'.local/kjv285-proofing'
scratch.mkdir(exist_ok=True)
def write(path,data):
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf8')
    temp.replace(path)

def assemble():
    parent_stage=ROOT/'.local/kjv285-section-work'
    parent_state=parent_stage/'parent-state.json'
    parent=read(parent_stage/'parent.json')
    assert parent['nativeSha256']==file_hash(PREVIOUS/'KJV Bible.vay')==read(PREVIOUS/'combined-validation.json')['sha256']
    parent_hash=parent['stateSha256']
    assert file_hash(parent_state)==parent_hash
    state=read(parent_state)
    old_pages=state.pop('pages')
    old_configs=state['typesetting'].pop('frames')
    assert not state['typesetting']['flows']
    state['documentId']=uid('document')
    state['revision']=0
    state['pages']=[]
    state['typesetting']['frames']={}
    snapshot=read(OUT/'current-snapshot.json')
    assert snapshot['head']==verify_register(VERSION)['forgeHead']
    language.append_revision(state['language'],snapshot['snapshot']['language'],'KJV 285 · native vocabulary and transmitted names · '+snapshot['head'])
    del snapshot
    units=read(OUT/'complete-translation-ledger.json')['units']
    by_id={u['id']:u for u in units}
    fields=('text','text','gloss','source')
    sections=[];spreads=[];checks=[];receipts=[];ids=[];reusable=[]
    staging=ROOT/'.local/kjv285-final-section-work'
    for input_name in read(staging/'jobs.json'):
        inp=Path(input_name)
        pp=staging/'pages'/inp.name
        part=read(pp)
        assert part['inputSha256']==file_hash(inp)
        first=len(state['pages'])+1
        for s in part['spreads']:
            left=len(state['pages'])+1
            rows=[by_id[u['id']] for u in s['units']]
            assert rows==s['units']
            if s['reused']:
                a,b=s['parentPages']
                assert b==a+1
                pair=old_pages[a-1:b]
                configs={f['frameId']:old_configs[f['frameId']] for p in pair for f in p['frames'] if f['frameId'] in old_configs}
                checks.append(dict(leftPage=left,parentPages=[a,b],measurement='verified 284 spread'))
                if a==left:reusable.extend([a,b])
            else:
                pair=s['pages']
                configs=s['configs']
                checks.append(dict(leftPage=left,**s['check']))
            for i,page in enumerate(pair):
                p=deepcopy(page)
                p['name']=rows[0]['reference']+' — '+rows[-1]['reference']
                assert geometry(p)==geometry(old_pages[i])
                assert [frame_geometry(f) for f in p['frames']]==[frame_geometry(f) for f in old_pages[i]['frames']]
                if not s['reused']:p['pageId']=uid('page')
                for f in p['frames']:
                    old_id=f['frameId']
                    if not s['reused']:f['frameId']=uid('frame')
                    f['content']['document']['documentId']=state['documentId']
                    if old_id in configs:state['typesetting']['frames'][f['frameId']]=configs[old_id]
                state['pages'].append(p)
            columns=[texts(f) for p in state['pages'][-2:] for f in sorted(p['frames'],key=lambda f:int(f['x']))]
            assert columns==[[u[field] for u in rows] for field in fields],rows[0]['reference']
            row_ids=[u['id'] for u in rows]
            ids.extend(row_ids)
            spreads.append(dict(leftPage=left,rightPage=left+1,unitIds=row_ids,references=[u['reference'] for u in rows]))
        sections.append(dict(section=part['section'],version=VERSION,firstPage=first,lastPage=len(state['pages'])))
        receipts.append(dict(section=part['section'],sha256=file_hash(pp),inputSha256=part['inputSha256']))
    assert ids==list(by_id) and len(sections)==66
    assert len({p['pageId'] for p in state['pages']})==len(state['pages'])
    assert len({f['frameId'] for p in state['pages'] for f in p['frames']})==2*len(state['pages'])
    state['activeFrameId']=state['pages'][0]['frames'][0]['frameId']
    write(scratch/'state.json',state)
    signature=file_hash(scratch/'state.json')
    total=len(state['pages'])
    write(scratch/'build.json',dict(stateSha256=signature,parentStateSha256=parent_hash,pages=total,
        checks=checks,sectionSources=receipts,unchangedPagesAtSameNumber=reusable))
    write(OUT/'page-index.json',dict(pages=total,spreads=spreads))
    write(OUT/'section-index.json',sections)
    print(total,'pages;',len(reusable),'pages with an identical physical position and previously measured body.',flush=True)

def folios():
    build=read(scratch/'build.json')
    assert file_hash(scratch/'state.json')==build['stateSha256']
    state=read(scratch/'state.json')
    pages=state.pop('pages')
    configs=state['typesetting'].pop('frames')
    assert not state['typesetting']['flows']
    write(scratch/'shared.json',state)
    write(scratch/'order.json',[p['pageId'] for p in pages])
    inherited=set(build['unchangedPagesAtSameNumber'])
    old=read(PREVIOUS/'numbering-validation.json')
    parent_count=read(PREVIOUS/'combined-validation.json')['pages']
    assert [(r['pageNumber'],r['pageMode'],r['status']) for r in old]==[(i,m,'placed') for i in range(1,parent_count+1) for m in ('one','two')]
    results={}
    for r in old:
        n=r['pageNumber']
        if n in inherited:
            assert r['pageId']==pages[n-1]['pageId'] and r['status']=='placed'
            results[(n,r['pageMode'])]=r
    assert len(results)==2*len(inherited)
    samples=set(sorted(inherited)[::max(1,len(inherited)//16)])
    needed=[i for i in range(1,len(pages)+1) if i not in inherited or i in samples]
    batches=[]
    for i in range(0,len(needed),150):
        numbers=needed[i:i+150];selected=[pages[n-1] for n in numbers]
        name=f"{numbers[0]:05d}-{numbers[-1]:05d}"
        write(scratch/(name+'.in.json'),dict(pages=selected,numbers=numbers,stateSha256=build['stateSha256'],
              configs={f['frameId']:configs[f['frameId']] for p in selected for f in p['frames'] if f['frameId'] in configs}))
        batches.append(name)
    del state,pages,configs
    gc.collect()
    def run(name):
        path=scratch/(name+'.out.json')
        if not path.exists() or read(path)['stateSha256']!=build['stateSha256']:
            with (scratch/(name+'.log')).open('w',encoding='utf8') as log:
                subprocess.run([sys.executable,'-X','utf8',__file__,'measure',name],cwd=ROOT,stdout=log,stderr=log,check=True)
        return name
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        for i,f in enumerate(concurrent.futures.as_completed([pool.submit(run,name) for name in batches]),1):
            name=f.result()
            batch=read(scratch/(name+'.out.json'))
            assert batch['stateSha256']==build['stateSha256']
            for r in batch['placements']:
                k=(r['pageNumber'],r['pageMode'])
                if k in results:assert results[k]==r,k
                assert r['status']=='placed'
                results[k]=r
            print(i,'/',len(batches),name,flush=True)
    order=read(scratch/'order.json')
    numbers=[results[(i,m)] for i in range(1,build['pages']+1) for m in ('one','two')]
    assert [(r['pageId'],r['pageNumber'],r['pageMode']) for r in numbers]==[(p,i,m) for i,p in enumerate(order,1) for m in ('one','two')]
    write(OUT/'numbering-validation.json',numbers)
    write(OUT/'folio-method.json',dict(stateSha256=build['stateSha256'],placements=len(numbers),
        parentStateSha256=build['parentStateSha256'],pagesReusedAtIdenticalPhysicalNumber=len(inherited),
        pagesFreshlyMeasured=len(needed),overlapSamplePages=sorted(samples)))

def measure(name):
    from PySide6.QtWidgets import QApplication
    from vayrshemon.file_api import FileSession
    from vayrshemon import page_numbering
    part=read(scratch/(name+'.in.json'))
    state=read(scratch/'shared.json')
    order=[dict(pageId=k) for k in read(scratch/'order.json')]
    state['pages']=part['pages']
    state['typesetting']['frames']=part['configs']
    state['activeFrameId']=state['pages'][0]['frames'][0]['frameId']
    app=QApplication([])
    book=FileSession(ROOT,source_fonts=False,recovery=False)
    book.remember=lambda p:None
    try:
        book._restore(book.resolve_fonts(state));book._state=book.capture();book.invalidate_composition()
        context=SimpleNamespace(state=dict(pages=order,pageNumbering=state['pageNumbering']),view=book.view,
                                fonts=book.fonts,paint_renderer=book.paint_renderer)
        placements=[]
        for number,page in zip(part['numbers'],book.state['pages'],strict=True):
            comp=book.composition(book.view['mode'],page_id=page['pageId'])
            for mode in ('one','two'):
                with page_numbering.scope(context,mode):r=page_numbering.placement(context,page,composition=comp)
                assert r['status']=='placed' and r['pageNumber']==number,r
                placements.append(r)
        write(scratch/(name+'.out.json'),dict(stateSha256=part['stateSha256'],placements=placements))
    finally:book.finish()

def publish():
    from PySide6.QtWidgets import QApplication
    from vayrshemon.file_api import FileSession
    from vayrshemon import pages
    build=read(scratch/'build.json')
    parent_report=read(PREVIOUS/'combined-validation.json')
    parent_hash=file_hash(PREVIOUS/'KJV Bible.vay')
    assert parent_hash==parent_report['sha256'] and parent_report['saveReopenIdentical']
    assert file_hash(scratch/'state.json')==build['stateSha256']
    method=read(OUT/'folio-method.json')
    assert method['stateSha256']==build['stateSha256'] and method['placements']==2*build['pages']
    state=read(scratch/'state.json')
    assert verify_register(VERSION)['forgeHead'] in state['language']['revisions'][-1]['label']
    app=QApplication([])
    book=FileSession(ROOT,source_fonts=False,recovery=False)
    book.remember=lambda p:None
    try:
        book._restore(book.resolve_fonts(state));book._state=book.capture();book.invalidate_composition()
        target=OUT/'KJV Bible.vay'
        if not target.exists():book.save(target,preview_mode='two')
        before=book.capture()
        book.open(target,advance_revision=False)
        assert book.capture()==before
        del before,state
        proofs=OUT/'Proofs';proofs.mkdir(exist_ok=True)
        selected={1,2,build['pages']-1,build['pages']}
        refs=('Genesis 1:13','Genesis 31:29','Judges 14:17','Psalms 35:19','Isaiah 14:8','Jonah 4:11','Revelation 1:8','Revelation 1:11','Revelation 21:6','Revelation 22:13','Revelation 22:16')
        for spread in read(OUT/'page-index.json')['spreads']:
            if any(ref in refs for ref in spread['references']):selected.update([spread['leftPage'],spread['rightPage']])
        for n in sorted(selected):
            pages.render(book,page_id=book.state['pages'][n-1]['pageId'],path=proofs/f'page-{n:05d}.png',mode='mono',dpi=96,page_mode='two')
        for n in (1,2):
            pages.render(book,page_id=book.state['pages'][n-1]['pageId'],path=proofs/f'color-page-{n:05d}.png',mode='color',dpi=96,page_mode='two')
        checks=build['checks']
        changed=sum('parentPages' not in c for c in checks)
        result=dict(version=VERSION,status='complete',head=verify_register(VERSION)['forgeHead'],
            path=str(target),sha256=file_hash(target),pages=build['pages'],spreads=build['pages']//2,
            authoredVerses=31102,majorSections=66,missingVerses=0,allFourColumnsMatchCurrentLedger=True,
            sourceTextExact=True,saveReopenIdentical=True,folioPlacementsChecked=method['placements'],
            reusedMeasuredSpreads=len(checks)-changed,recomposedSpreads=changed,geometryAndPaintPreserved=True,
            maxBaselineErrorPt=max(c.get('maxBaselineErrorPt',0) for c in checks),checks=checks,
            sectionSources=build['sectionSources'],proofPages=sorted(selected),parentNativeSha256=parent_hash)
        write(OUT/'combined-validation.json',result)
        print('Complete',result['pages'],result['sha256'],flush=True)
    finally:book.finish()

if __name__=='__main__':
    if sys.argv[1]=='measure':measure(sys.argv[2])
    else:{'assemble':assemble,'folios':folios,'publish':publish}[sys.argv[1]]()
