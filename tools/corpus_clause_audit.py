"""Record source-clause evidence against issued target analyses, including unresolved readings."""
import gzip,math
from collections import Counter,defaultdict
from functools import lru_cache
from itertools import chain
import numpy as np
from scipy.optimize import linear_sum_assignment
from tools.corpus_clause_revision import *
from tools.shakespeare_project import source_units
from tools.kjv_archive import parse_source
from tools.editorial_language import TOKEN,WORD
SKIP=set('i me my thou thee thy you your he his him she her it its we our us they their them there that this those these who which what some any and or but of to a an the as at on in with from for by so o oh'.split())
SEM=set('NOUN VERB ADV ADJ PROPN NUM AUX PART PRON'.split())
IRREG=dict(thou='you',thee='you',thy='your',thine='your',ye='you',hath='have',hast='have',hadst='have',spake='speak',bare='bear',begat='beget',wist='know',wot='know',art='be',wert='be',wast='be',shalt='shall',wilt='will',didst='do',dost='do',doth='do',saith='say',quoth='say',slew='slay',slain='slay',men='man',feet='foot',women='woman',children='child',brethren='brother',went='go',came='come',saw='see',given='give',gave='give',took='take',told='tell',made='make',got='get',brought='bring',bought='buy',wives='wife',unto='to',nay='no',naught='nothing',nayword='denial',morrow='morning',wherefore='why',whence='where',whither='where',anon='soon',sire='father',daughters='daughter',wed='marry',upon='on',ere='before',twain='two',aught='anything',yclept='call',wrought='work')
GROUPS=['speak say tell utter proclaim','bid command order ask invite','cry call shout crow','fade vanish disappear','worship bow reverence adore','kill slay murder put_to_death','ere before','destroy ruin perish','see look behold watch','make create fashion','issue proceed flow emanation','weep cry lament','get obtain acquire receive','father sire beget','dwell live reside','shalt shall future','would will conditional','should ought must','unto toward to','grant give bestow','bring carry bear','touch strike smite hit','hearken listen hear','depart leave go','womb belly body','take seize receive','king ruler monarch','mother dam','wife spouse bride marry','harlot prostitute whore','death die dead','know understand perceive','maid girl virgin','lie rest recline','prithee beseech pray beg','oath swear','indeed yes truly','twice two','not no never neg','heaven sky','hell underworld','garment robe raiment clothing dress','flee fly escape','swear oath vow','suffer allow endure','fight battle combat','war battle','return again back','conceive pregnant','day sun light','tomb grave','great mighty large','small little','rejoice glad joy','horse steed','ill evil bad wicked','friend companion','receive take accept','end finish cease','think deem reckon consider','bear carry endure','love affection beloved','hear listen','answer reply respond','tower fortress stronghold','child offspring son daughter','spirit ghost apparition','cock rooster fowl','shame disgrace','silver money','whensoever whenever when','letter writing mark','house dwelling home','cease stop end','name call','yea yes','nothing naught','dark darkness','honour honor','labour labor','colour color','saviour savior','succor succour','woe sorrow grief','buy purchase','stay wait remain','wed marry espouse marriage','forsake abandon leave','daybreak dawn','piss urine urinate','whilst while','get become go','must necessity','thrice three','nay no','now present','never not','good well']
EQUIV=defaultdict(set)
for group in GROUPS:
    ls=group.split()
    for word in ls:EQUIV[word].update(ls)
@lru_cache(maxsize=100000)
def variants(w):
    w=w.lower().replace('’',"'").strip(" '-");s={w,IRREG.get(w,w)}
    if len(w)>4:
        if w.endswith('eth'):s.update((w[:-3],w[:-3]+'e'))
        if w.endswith('est'):s.update((w[:-3],w[:-3]+'e'))
        if w.endswith('ies'):s.add(w[:-3]+'y')
        if w.endswith('ed'):s.update((w[:-2],w[:-1],w[:-3]+'y' if w.endswith('ied') else w[:-2]))
        if w.endswith('ing'):s.update((w[:-3],w[:-3]+'e'))
        if w.endswith('s'):s.update((w[:-1],w[:-2] if w.endswith('es') else w[:-1]))
    return s-{''}
def words(s):return set(re.findall(r"[A-Za-z0-9]+",s.lower()))
def parsed(slug):
    files=sorted((S/'parsed').glob('bible-*.jsonl.gz')) if slug=='bible' else [S/'parsed'/(slug+'.jsonl.gz')]
    for path in files:
        with gzip.open(path,'rt',encoding='utf8') as f:
            for line in f:yield json.loads(line)
def atoms(src):
    return [(surf,lem,pos,rel,k) for surf,lem,pos,rel,k in src if pos in SEM and (lem.lower() not in SKIP or k==0) and (pos!='AUX' or k==0 or lem.lower() in ('may','must','shall','will','can'))]
def compare():
    blex=compiler(ROOT/'data/language/archaic-kjv-285').lexicon
    slex=EditorialLanguage(PROJECT/'Language').lexicon
    out=S/'clause-audit.jsonl.gz';risk=[];totals={}
    with gzip.open(out,'wt',encoding='utf8',compresslevel=4) as dest:
        for slug,path in textpaths():
            lex=blex if slug=='bible' else slex
            cache={}
            def aliases(token):
                if token in cache:return cache[token]
                core=token.rstrip(':').split(':')[0];morph=token[len(core):]
                keys=re.findall(r'[a-z_0-9]+',core);strong=set();weak=set()
                for key in keys:
                    strong.update(words(key.replace('drama_native_','').replace('kjv_','').replace('_',' ')))
                    entry=lex.get(key,{})
                    definition=entry.get('meaning','')
                    if entry.get('pos')=='proper':strong.update(words(str(entry.get('roman',''))))
                    weak.update(words(definition.split(';')[0].split('.')[0]) - SKIP)
                for feat,gl in [('neg','not'),('fu','will'),('may','may'),('must','must'),('cond','would'),('can','can'),('should','should'),('excl','o'),('du','two'),('ag','person')]:
                    if feat in morph.strip(':').split(':'):strong.add(gl)
                strong=set.union(set(),*(variants(k) for k in strong))
                weak.update(set.union(set(),*(EQUIV[w] for w in strong)))
                cache[token]=(strong,weak);return strong,weak
            stats=Counter();units=read(edited(path))['units']
            if slug=='bible':
                original=[(v['id'],v['source']) for b in parse_source(ROOT/'Inputs/Sources/The King James Bible.txt')['books'] for v in b['verses']]
                assert original==[(u['id'],u['source']) for u in units]
            else:
                src=source_units((ROOT/'Inputs/Sources'/(slug+'_TXT_FolgerShakespeare.txt')).resolve())['units']
                norm=lambda s:' '.join(s.split())
                assert norm(' '.join(u['source'] for u in src))==norm(' '.join(u['source'] for u in units)),slug
            for u,(unitid,clauses) in zip(units,parsed(slug),strict=True):
                assert u['id']==unitid
                target=[t for t in TOKEN.findall(u['analysis']) if WORD.fullmatch(t) or t.isdigit() or t.startswith('{{')]
                gloss=u['gloss'].split(' · ')
                domains=[aliases(t) for t in target]
                srcidx=defaultdict(list);loidx=defaultdict(list)
                for j,(strong,weak) in enumerate(domains):
                    for w in strong:srcidx[w].append(j)
                    for w in weak:loidx[w].append(j)
                items=[(k,w) for k,c in enumerate(clauses) for w in atoms(c)]
                mat=np.zeros((len(items),len(target)),dtype=float)
                for i,(c,(surf,lem,pos,rel,rd)) in enumerate(items):
                    v=variants(surf)|variants(lem)
                    for mapping,score in ((loidx,1),(srcidx,2)):
                        for w in v:
                            for j in mapping.get(w,()):
                                mat[i,j]=max(mat[i,j],score+.09*(1-abs(i/max(len(items),1)-j/max(len(target),1))))
                matches={}
                if mat.size:
                    ii,jj=linear_sum_assignment(mat,maximize=True)
                    matches={int(i):(int(j),'literal' if mat[i,j]>=2 else 'sense') for i,j in zip(ii,jj) if mat[i,j]>0}
                evidence=[[] for c in clauses]
                for i,(c,(surf,lem,pos,rel,rd)) in enumerate(items):
                    hit=matches.get(i)
                    evidence[c].append([surf,target[hit[0]] if hit else None,hit[1] if hit else None])
                records=[]
                for k,(c,ev) in enumerate(zip(clauses,evidence)):
                    en=' '.join(x[0] for x in c);anchors=sum(bool(a[1]) for a in ev)
                    status='lexical evidence' if anchors else 'no lexical anchor' if ev else 'function words or punctuation'
                    stats[status]+=1;stats['clauses']+=1
                    if not anchors and len(ev)>=3:
                        risk.append([len(ev),slug,unitid,k,en])
                    records.append(dict(english=en,evidence=ev,status=status))
                stats['passages']+=1
                dest.write(json.dumps(dict(work=slug,id=unitid,source=u['source'],analysis=u['analysis'],clauses=records),ensure_ascii=False,separators=(',',':'))+'\n')
            totals[slug]=stats;print(slug,stats['clauses'],flush=True)
    write(S/'audit-totals.json',totals);write(S/'unsupported-clauses.json',sorted(risk,reverse=True))
if __name__=='__main__':compare()

