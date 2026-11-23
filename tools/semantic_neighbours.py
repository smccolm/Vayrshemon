"""Find sense-specific neighbours in the dictionary, using lexical evidence and WordNet 3.0."""
from collections import Counter, defaultdict
from functools import lru_cache
import re

from tools.dictionary_corpus import ROOT, WORK, normalize
from tools.dictionary_lexicon import load_gzip
from tools.dictionary_rows import collate
from tools.editorial_language import TOKEN, WORD

STAGE=ROOT/'.local/semantic-expansion'
BOOK=ROOT/'Saves/Vayrshemon Thesaurus - Four-Column Progressive Edition'
AUTHOR=BOOK/'Working/Lexical expansion'
LEXNAMES='adj.all adj.pert adv.all noun.Tops noun.act noun.animal noun.artifact noun.attribute noun.body noun.cognition noun.communication noun.event noun.feeling noun.food noun.group noun.location noun.motive noun.object noun.person noun.phenomenon noun.plant noun.possession noun.process noun.quantity noun.relation noun.shape noun.state noun.substance noun.time verb.body verb.change verb.cognition verb.communication verb.competition verb.consumption verb.contact verb.creation verb.emotion verb.motion verb.perception verb.possession verb.social verb.stative verb.weather adj.ppl'.split()
DROP=set('this that people person thing native word form example used noun verb adjective lexical drama semantic where which whose whose what having have been being with from into himself itself mother father source narrative passage king james bible chapter proper earlier witness distinct gloss name supplied text reading rather than without'.split())

def tokens(s):
    return {t for t in re.findall(r'[a-z]{3,}',s.lower()) if t not in DROP}

class Words:
    def __init__(self):
        self.synsets={};self.index=defaultdict(list)
        for tag in ('noun','verb','adj','adv'):
            with (STAGE/f'data.{tag}').open(encoding='ascii') as f:
                for line in f:
                    if not line[0].isdigit():continue
                    rec,gloss=line.rstrip().split(' | ',1);x=rec.split()
                    off,lf,_,n=x[:4];n=int(n,16)
                    terms=[x[i].lower().partition('(')[0] for i in range(4,4+n*2,2)]
                    i=4+n*2;nptr=int(x[i]);i+=1
                    related=[(x[h],x[h+2].replace('s','a')+x[h+1]) for h in range(i,i+4*nptr,4)]
                    self.synsets[tag[0]+off]=(LEXNAMES[int(lf)],terms,related,tokens(gloss.partition('; "')[0]))
            with (STAGE/f'index.{tag}').open(encoding='ascii') as f:
                for line in f:
                    if line.startswith(' '):continue
                    cols=line.split();self.index[cols[0],tag]=[tag[0]+off for off in cols[-int(cols[2]):]]

    @lru_cache(maxsize=None)
    def parents(self,sid):
        if not sid:return frozenset()
        todo=[sid];seen=set();words=set()
        while todo:
            item=todo.pop()
            if item in seen:continue
            seen.add(item)
            _,terms,rels,_=self.synsets[item]
            words.add(terms[0]);todo.extend(other for k,other in rels if k in ('@','@i'))
        return frozenset(words)

    def choose(self,label,key,pos,meaning):
        pos=str(pos).strip().lower()
        kinds=['verb'] if pos in ('verb','v','verb/noun') else ['adj','adv'] if pos in ('modifier','adjective','adj','adverb') else ['noun'] if pos.startswith(('noun','n,')) else ['noun','verb','adj','adv']
        names=[label.lower(),re.sub(r'^(kjv|milton|dam(?:at|bk|pac)?|boyle|drama_native|hobbes|locke)_','',key).lower()]
        context=tokens(meaning+' '+label)
        options={}
        for name in names:
            name=re.sub(r'[\[\{(].*$','',name).strip().replace('-','_').replace(' ','_')
            for kind in kinds:
                for i,sid in enumerate(self.index.get((name,kind),[])):
                    ln,terms,_,v=self.synsets[sid]
                    rank=6*len(context&v)+2*(name==names[0].replace(' ','_'))-min(i,16)*0.55
                    options[sid]=max(options.get(sid,-100),rank)
        return max(options,key=options.get) if options else ''

def dictionary():
    ledger=load_gzip(WORK/'dictionary-rows.json.gz')
    att=load_gzip(WORK/'attestations.json.gz')
    rows=defaultdict(list)
    for r in ledger['rows']:
        if 'article' in r:rows[normalize(r['text'].partition('. ')[0])].append(r)
    return rows,att

def content_keys(analysis):
    return [k for token in TOKEN.findall(analysis) if WORD.fullmatch(token) for part in token.split('/') for k in part.partition(':')[0].split('+')]

def readings(rows,att,wordnet):
    out=[]
    for r in rows:
        a=r['article']; ids=a['readingIds']
        recs=[att['senses'][i] for i in ids if i in att['senses']]
        s=max(recs,key=lambda v:v['contemporary']+v['historical'],default={})
        label=r['gloss'].partition('. ')[0].split('{')[0].strip()
        key=s.get('key',ids[0].partition('@')[0] if ids else r['id'])
        meaning=r['source'].partition(' Example: ')[0];meaning=re.sub(r'^\d+\. ','',meaning)
        pos=s.get('pos',r.get('partOfSpeech',''))
        sid=wordnet.choose(label,key,pos,meaning) if pos not in ('proper','idiom') else ''
        out.append(dict(row=r,key=key,label=label,pos=pos,meaning=meaning,record=s,sid=sid))
    return out

def filing_heads(groups):
    return sorted(groups,key=collate)
