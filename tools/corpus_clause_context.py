"""Recheck the strongest clause flags with the supplied English passage in context."""
import gzip,json,re
from difflib import SequenceMatcher
from tools.corpus_clause_report import records
from tools.corpus_clause_revision import S

def sentence(clause,passage):
    # A complete source passage supplies context when it fits. For long speeches,
    # select the complete containing sentence by ordered words, including its negatives.
    if len(passage.split())<=100:return passage
    spans=re.split(r'(?<=[?!.])\s+(?=[A-Z\[“"])',passage)
    tokens=lambda t:re.findall(r"[\w’']+",t.lower())
    terms=tokens(clause)
    def overlap(span):
        return sum(r.size for r in SequenceMatcher(None,terms,tokens(span),autojunk=False).get_matching_blocks())
    best=max(spans,key=overlap)
    if len(best.split())>135:
        words=best.split()
        windows=[' '.join(words[i:i+110]) for i in range(0,len(words),50)]
        best=max(windows,key=overlap)
    return best

def main():
    modes=('reading','gloss')
    scores=[records(S/(mode+'-scores.jsonl.gz')) for mode in modes]
    inputs=[records(S/(mode+'-input.jsonl.gz')) for mode in modes]
    handles=[gzip.open(S/('context-'+mode+'-input.jsonl.gz'),'wt',encoding='utf8') for mode in modes]
    try:
        for entry in records(S/'clause-audit.jsonl.gz'):
            for i,clause in enumerate(entry['clauses']):
                a,b=map(next,scores);v,w=map(next,inputs)
                key=f"{entry['work']}/{entry['id']}/{i}"
                assert key==a[0]==b[0]==v[0]==w[0]
                if min(a[1],b[1])<.98:continue
                hyp=sentence(clause['english'],entry['source'])
                for handle,reading in zip(handles,(v,w)):
                    handle.write(json.dumps([key,reading[1],hyp],ensure_ascii=False)+'\n')
    finally:
        for handle in handles:handle.close()
if __name__=='__main__':main()

