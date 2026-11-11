"""Measure changed four-column spreads against the sealed 284 native book."""
from pathlib import Path
from functools import partial
import concurrent.futures
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT))
from tools import kjv_native_vocabulary as edition
from tools.m0.common import file_hash
from tools.kjv_archive import read
from vayrshemon.native_storage import unpack

old=edition.prior.OUT
stage=ROOT/'.local/kjv285-section-work'
sys.path.insert(0,str(ROOT/'Saves/KJV Bible v0.10-kjv.283/Authoring'))
import build_pages as layout
from tools.layout_clitics import apply as clitic_break
layout.HERE=stage;layout.OLD=old;layout.WORK=edition.OUT;layout.REGISTER=edition.VERSION
layout.clitic_break=partial(clitic_break,lexical_boundaries=True)

def prepare():
    assert not (edition.OUT/'FROZEN.json').exists()
    path=old/'KJV Bible.vay'
    report=read(old/'combined-validation.json')
    parent_hash=file_hash(path)
    assert report['sha256']==parent_hash and report['saveReopenIdentical']
    payload=unpack(read(path))
    state=payload['state'];engine=payload['engine']
    layout.write(stage/'parent-state.json',state)
    layout.write(stage/'parent.json',dict(nativeSha256=parent_hash,stateSha256=file_hash(stage/'parent-state.json'),pages=len(state['pages'])))
    old_units={u['id']:u for u in read(old/'complete-translation-ledger.json')['units']}
    units={u['id']:u for u in read(edition.OUT/'complete-translation-ledger.json')['units']}
    assert list(units)==list(old_units)
    index=read(old/'page-index.json')['spreads']
    sections=read(old/'section-index.json')
    jobs=[];changed=0;cursor=0
    for number,section in enumerate(sections,1):
        spreads=[]
        for s in index[(section['firstPage']-1)//2:section['lastPage']//2]:
            a,b=s['leftPage'],s['rightPage'];assert (a,b)==(cursor+1,cursor+2)
            pair=state['pages'][a-1:b]
            rows=[units[i] for i in s['unitIds']]
            columns=[layout.texts(f) for p in pair for f in sorted(p['frames'],key=lambda f:int(f['x']))]
            fields=['text','text','gloss','source']
            assert columns==[[old_units[i][k] for i in s['unitIds']] for k in fields]
            same=columns==[[u[k] for u in rows] for k in fields]
            changed+=not same
            cfg=state['typesetting']['frames']
            configs={f['frameId']:cfg[f['frameId']] for p in pair for f in p['frames'] if f['frameId'] in cfg}
            spreads.append(dict(pages=pair,configs=configs,units=rows,index=dict(leftPage=a,rightPage=b),unchanged=same,reuseSource=parent_hash))
            cursor+=2
        f=stage/'inputs'/f'{number:02d}.json'
        layout.write(f,dict(section=section['section'],number=number,engine=engine,parentSha256=parent_hash,spreads=spreads))
        jobs.append(str(f))
    assert cursor==len(state['pages']) and len(jobs)==66
    layout.write(stage/'jobs.json',jobs)
    print('Parent pages',cursor,'spreads requiring measurement',changed,flush=True)

def run_one(p):
    (stage/'logs').mkdir(exist_ok=True)
    with (stage/'logs'/(Path(p).stem+'.log')).open('w',encoding='utf8') as log:
        result=subprocess.run([sys.executable,'-B','-X','utf8',__file__,'worker',p],cwd=ROOT,stdout=log,stderr=log)
    print(Path(p).stem,result.returncode,flush=True)
    return result.returncode

if __name__=='__main__':
    if sys.argv[1]=='worker':layout.worker(sys.argv[2])
    elif sys.argv[1]=='prepare':prepare()
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
            codes=list(pool.map(run_one,read(stage/'jobs.json')))
        if any(codes):raise SystemExit('A section failed. See its measurement log.')
