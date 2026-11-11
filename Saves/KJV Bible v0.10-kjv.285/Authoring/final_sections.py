"""Reuse measured draft spreads only when every printed paragraph still matches."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
import sys
import sections
from sections import edition, file_hash, layout, read, ROOT

draft=sections.stage
final=ROOT/'.local/kjv285-final-section-work'
patches=final/'amendments'
fields=('text','text','gloss','source')

def printed(pair):
    return [layout.texts(f) for p in pair for f in sorted(p['frames'],key=lambda f:int(f['x']))]

def columns(rows):
    return [[u[k] for u in rows] for k in fields]

def inputs():
    units={u['id']:u for u in read(edition.OUT/'complete-translation-ledger.json')['units']}
    jobs=[]
    for name in read(draft/'jobs.json'):
        src=Path(name);job=read(src)
        for s in job['spreads']:
            s['units']=[units[u['id']] for u in s['units']]
            s['unchanged']=printed(s['pages'])==columns(s['units'])
        dst=final/'inputs'/src.name
        layout.write(dst,job);jobs.append(str(dst))
    layout.write(final/'jobs.json',jobs)

def measure(path):
    job=read(path)
    completed=final/'pages'/path.name
    if completed.exists():
        assert read(completed)['inputSha256']==file_hash(path)
        return
    baseline=draft/'pages'/path.name
    log=final/'logs'/(path.stem+'.log')
    log.parent.mkdir(parents=True,exist_ok=True)
    with log.open('w',encoding='utf8') as stream:
        def worker(mode,p):
            subprocess.run([sys.executable,'-B','-X','utf8',__file__,mode,str(p)],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,check=True)
        if not baseline.exists():
            worker('whole',path)
            return
        old=read(baseline)
        assert old['inputSha256']==file_hash(draft/'inputs'/path.name)
        assert [u['id'] for s in old['spreads'] for u in s['units']]==[u['id'] for s in job['spreads'] for u in s['units']]
        lookup={u['id']:u for s in job['spreads'] for u in s['units']}
        edited=[];patch_ids=set()
        for i,s in enumerate(old['spreads']):
            base=s['units']
            assert printed(s['pages'])==columns(base)
            latest=[lookup[u['id']] for u in base]
            s['units']=latest
            if columns(base)!=columns(latest):
                patch_ids.add(i)
                edited.append(dict(pages=s['pages'],configs=s['configs'],units=latest,unchanged=False))
        if edited:
            patch=patches/'inputs'/path.name
            layout.write(patch,dict(job,spreads=edited))
            worker('patch',patch)
            revised=read(patches/'pages'/path.name)
            assert revised['inputSha256']==file_hash(patch)
            it=iter(revised['spreads'])
        result=[]
        for i,s in enumerate(old['spreads']):
            if i not in patch_ids:
                result.append(s)
                continue
            want=[u['id'] for u in s['units']];got=[]
            while len(got)<len(want):
                fresh=next(it)
                assert not fresh['reused'] and printed(fresh['pages'])==columns(fresh['units'])
                got.extend(u['id'] for u in fresh['units']);result.append(fresh)
            assert got==want
        if edited:assert next(it,None) is None
        layout.write(completed,dict(number=job['number'],section=job['section'],inputSha256=file_hash(path),
            draftMeasurementSha256=file_hash(baseline),editedDraftSpreads=len(edited),spreads=result))
    print(path.stem,len(edited),'changed measured spreads',flush=True)

if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='prepare':inputs()
    elif mode in ('whole','patch'):
        layout.HERE=final if mode=='whole' else patches
        layout.worker(sys.argv[2])
    elif mode=='run':
        jobs=[Path(p) for p in read(final/'jobs.json')]
        jobs.sort(key=lambda p: not (draft/'pages'/p.name).exists())
        with ThreadPoolExecutor(max_workers=10) as pool:
            list(pool.map(measure,jobs))
