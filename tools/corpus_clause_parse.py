"""Segment the supplied English into predicate clauses; retain token owners and offsets."""
import gzip,json,re,sys,os
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
from tools.corpus_clause_revision import ROOT,S,read,write,textpaths,edited
sys.path.insert(0,str(S/'parser'))
from ufal.udpipe import Model,Pipeline,ProcessingError
MODEL=LANG=None
def init():
    global MODEL,LANG
    LANG=Model.load(str(S/'english-ewt.udpipe'))
    if not LANG:raise ValueError('English model could not be opened')
    MODEL=Pipeline(LANG,'tokenize','','','conllu')
def parse(row):
    source=row['source'];err=ProcessingError()
    parsed=MODEL.process(source,err)
    if err.occurred():raise ValueError(err.message)
    pos=0;results=[]
    for sent in parsed.strip().split('\n\n'):
        tokens=[]
        for line in sent.splitlines():
            if line.startswith('#') or not line:continue
            parts=line.split('\t')
            if not parts[0].isdigit():continue
            i,word,lemma,upos,xpos,features,head,rel,*_=parts
            tokens.append((int(i),word,lemma,upos,int(head),rel))
        if not tokens:continue
        owners={}
        for i,word,lemma,upos,head,rel in tokens:
            if head==0 or rel.split(':')[0] in ('ccomp','xcomp','advcl','acl','csubj','parataxis') or rel=='conj' and (upos in ('VERB','AUX') or any(t[4]==i and t[5] in ('nsubj','cop') for t in tokens)):
                owners[i]=i
        for i,word,lemma,upos,head,rel in tokens:
            n=i
            while n not in owners:n=tokens[n-1][4]
            owners[i]=owners[n]
        cls={}
        for i,word,lemma,upos,head,rel in tokens:
            n=owners[i]
            if n not in cls:cls[n]=[]
            cls[n].append([word,lemma,upos,rel,i-n])
        for n,words in sorted(cls.items(),key=lambda pair:min(t[4]+pair[0] for t in pair[1])):
            results.append(words)
    return [row['id'],results]
def job(args):
    name,rows=args
    dest=S/'parsed'/(name+'.jsonl.gz')
    if dest.is_file():return name,len(rows)
    dest.parent.mkdir(parents=True,exist_ok=True);tmp=dest.with_suffix('.tmp')
    with gzip.open(tmp,'wt',encoding='utf8',compresslevel=3) as f:
        for row in rows:f.write(json.dumps(parse(row),ensure_ascii=False,separators=(',',':'))+'\n')
    tmp.replace(dest)
    return name,len(rows)
def tasks():
    for slug,path in textpaths():
        rows=[{'id':u['id'],'source':u['source']} for u in read(edited(path))['units']]
        if slug=='bible':
            from itertools import groupby
            for n,g in groupby(rows,key=lambda u:u['id'][:2]):yield 'bible-'+n,list(g)
        else:yield slug,rows
if __name__=='__main__':
    with ProcessPoolExecutor(max_workers=10,initializer=init) as pool:
        futures=[pool.submit(job,t) for t in tasks()]
        for i,f in enumerate(as_completed(futures),1):
            k,n=f.result()
            if i%10==0:print(i,len(futures),k,n,flush=True)

