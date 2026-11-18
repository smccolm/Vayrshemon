from tools.corpus_clause_revision import *
from tools.corpus_clause_audit import parsed
import gzip
def readable(g):
    def features(m):
        labels={'neg.':'not','pass.':'passive','fut.':'future','necess.':'must','cond.':'would','possib.':'may','imp.':'command','dat.':'indirect object','acc.':'object'}
        return ' '+' '.join(labels[k] for k in m[1].split(',') if k in labels)+' '
    return ' '.join(re.sub(r'\(([^()]*)\)',features,g).replace(' · ',' ').replace('{',' (').replace('}',')').split())
if __name__=='__main__':
    with gzip.open(S/'reading-input.jsonl.gz','wt',encoding='utf8',compresslevel=2) as one,gzip.open(S/'gloss-input.jsonl.gz','wt',encoding='utf8',compresslevel=2) as two:
        for slug,path in textpaths():
            for u,(key,clauses) in zip(read(edited(path))['units'],parsed(slug),strict=True):
                assert key==u['id'];g=readable(u['gloss'])
                back=u.get('backTranslation',u.get('backReading',''))
                for i,c in enumerate(clauses):
                    en=' '.join(t[0] for t in c);id=slug+'/'+key+'/'+str(i)
                    for f,stem in [(one,(back+' '+g).strip()),(two,g)]:
                        f.write(json.dumps([id,stem,en],ensure_ascii=False,separators=(',',':'))+'\n')

