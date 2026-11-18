"""Second, independent clause comparison using a local frozen textual entailment classifier."""
import gzip,json,re,sys,time
from pathlib import Path
from collections import Counter
import torch
from transformers import AutoModelForSequenceClassification,AutoTokenizer
root=Path(__file__).resolve().parents[1]
stage=root/'.local/corpus-clause-review'
def main():
    modelpath=stage/'nli'; tokenizer=AutoTokenizer.from_pretrained(modelpath,local_files_only=True)
    device='cuda' if torch.cuda.is_available() else 'cpu'
    model=AutoModelForSequenceClassification.from_pretrained(modelpath,local_files_only=True,torch_dtype=torch.float16 if device=='cuda' else torch.float32).to(device).eval()
    mode=sys.argv[1] if len(sys.argv)>1 else 'reading'
    assert mode in ('reading','gloss','context-reading','context-gloss')
    inputs=stage/(mode+'-input.jsonl.gz'); out=stage/(mode+'-scores.jsonl.gz')
    count=0;t=time.monotonic()
    def flush(batch,f):
        nonlocal count
        if not batch:return
        ordered=sorted(enumerate(batch),key=lambda pair:sum(len(x) for x in pair[1][1:]))
        output=[None]*len(batch)
        for start in range(0,len(ordered),64):
            sub=ordered[start:start+64]
            tok=tokenizer([v[1] for _,v in sub],[v[2] for _,v in sub],padding=True,truncation='only_first',max_length=384,return_tensors='pt').to(device)
            with torch.inference_mode():vals=model(**tok).logits.float().softmax(-1).cpu().tolist()
            for (idx,(key,_,_)),sc in zip(sub,vals):output[idx]=[key,*[round(a,4) for a in sc]]
        for v in output:f.write(json.dumps(v,separators=(',',':'))+'\n')
        count+=len(batch)
        if count%20480==0:print(count,'clauses',round(time.monotonic()-t),'s',flush=True)
    with gzip.open(inputs,'rt',encoding='utf8') as fin,gzip.open(out.with_suffix('.tmp'),'wt',encoding='utf8',compresslevel=3) as f:
        batch=[]
        for line in fin:
            batch.append(json.loads(line))
            if len(batch)==2048:flush(batch,f);batch=[]
        flush(batch,f)
    out.with_suffix('.tmp').replace(out)
    print('Completed semantic comparisons',count,flush=True)
if __name__=='__main__':main()

