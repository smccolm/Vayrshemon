"""Measure long four-column volumes in independent runs before binding their native pages."""
import argparse
from concurrent.futures import ProcessPoolExecutor,as_completed
from itertools import groupby
import json
from pathlib import Path

from PySide6.QtCore import QCoreApplication,QEvent
from tools.conventional_reference import edition
from tools.dictionary_layout import DictionaryLayout
from tools.dictionary_lexicon import load_gzip
from tools.reciprocal_verify import stamp


def runs(rows,size):
    start=0
    for _,section in groupby(rows,key=lambda r:r['section']):
        end=start+sum(1 for _ in section)
        while start+size+100<end:
            limit=start+size
            # Prefer a new headword. In a long family break before a member and its example.
            stop=next((i for i in range(limit,limit+80) if rows[i]['id'].startswith('h')),None)
            if stop is None:
                stop=next(i for i in range(limit,limit+80) if not rows[i]['id'].endswith('x'))
            yield start,stop
            start=stop
        yield start,end
        start=end


def measure(job):
    kind,n,start,stop,digest=job
    b=edition(kind)
    ledger=load_gzip(b.stage/'volumes'/f'{n:02}.json.gz')
    stage=b.stage/f'progressive-{n:02}'
    parts=stage/('plan-'+digest);parts.mkdir(exist_ok=True,parents=True)
    path=parts/f'{start}-{stop}.json'
    if path.exists():return json.loads(path.read_text('utf8'))
    layout=DictionaryLayout(title=b.title+' · '+ledger['meta']['name'],document_id=f'document.{b.key}.{n}',id_prefix=b.key+str(n),
        column_names=('Vayrshemon','Transliteration 7','Construction gloss',b.fourth),cache_root=stage)
    original=layout.session.fonts.resolve;seen={}
    def cached_font(identity):
        face=layout.session.fonts.faces.get(identity)
        if face is None:return original(identity)
        st=face.path.stat();key=(face.path,st.st_size,st.st_mtime_ns,st.st_ctime_ns)
        if seen.get(identity)!=key:face=original(identity);seen[identity]=key
        return face
    layout.session.fonts.resolve=cached_font
    output={};pos=start;last=7;rows=ledger['rows']
    try:
        while pos<stop:
            QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)
            group=rows[pos:min(pos+layout.spread_window,stop)];length=min(last+2,len(group))
            while True:
                count,_,_=layout.measured(group[:length])
                if count<length or length==len(group):break
                length=min(len(group),length+4)
            output[group[0]['id']]=[length,count]
            pos+=count;last=count
        assert pos==stop
        for identity in seen:original(identity)
    finally:layout.session.finish()
    temp=path.with_suffix('.writing');temp.write_text(json.dumps(output),encoding='utf8');temp.replace(path)
    return output


def main(kind,numbers,workers):
    b=edition(kind);all_jobs=[];rows_by_volume={};keys={};plans={}
    for n in numbers:
        rows=load_gzip(b.stage/'volumes'/f'{n:02}.json.gz')['rows']
        digest=stamp(rows);keys[n]=digest;rows_by_volume[n]=rows;plans[n]={}
        all_jobs.extend((kind,n,start,end,digest) for start,end in runs(rows,600))
    with ProcessPoolExecutor(max_workers=workers,max_tasks_per_child=1) as pool:
        pending={pool.submit(measure,j):j for j in all_jobs}
        for f in as_completed(pending):
            _,n,start,stop,_=pending[f];plans[n].update(f.result())
            print('Checked spread measurements',kind,n,start,stop,flush=True)
    for n,plan in plans.items():
        rows=rows_by_volume[n];pos=0;count=0
        while pos<len(rows):
            length,fit=plan[rows[pos]['id']]
            assert 0<fit<=length<=16
            pos+=fit;count+=1
        assert pos==len(rows) and count==len(plan)
        path=b.stage/f'progressive-{n:02}'/('measured-'+keys[n]+'.json')
        tmp=path.with_suffix('.writing');tmp.write_text(json.dumps(plan),encoding='utf8');tmp.replace(path)
        print(kind,n,len(plan),'spreads ready',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('kind',choices=['dictionary','thesaurus'])
    p.add_argument('volumes',type=int,nargs='+')
    p.add_argument('--workers',type=int,default=4)
    a=p.parse_args();main(a.kind,a.volumes,a.workers)
