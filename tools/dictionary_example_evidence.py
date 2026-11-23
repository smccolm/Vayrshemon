"""Choose complete, aligned usage evidence for a particular lexical identity."""
import re
from collections import defaultdict
from functools import lru_cache
from tools.dictionary_corpus import ROOT, WORK, ORTH, normalize, read
from tools.dictionary_lexicon import load_gzip, save_gzip
from tools.dictionary_sentence_witnesses import BAD, REMOTE, FINITE, anchors, lexical_keys, head_present, TOKENS

BANK=ROOT/'.local/dictionary-layout/context-examples.json.gz'
INVENTORY=ROOT/'.local/dictionary-layout/example-contexts.json.gz'
BREAK=re.compile(r'(?<=[.!?])\s+(?=[^ ])')
FRAGMENT=re.compile(r'^(?:which|whose|although|inasmuch as|namely|viz\.|because|as for|to wit)\b',re.I)
DIRECTION=re.compile(r'\[([^\[\]]*)\]')
CUE=re.compile(r"^([A-Z][A-Z ’'.,–-]+?)\s{2,}")
IMPERATIVE=re.compile(r':(?:imp|juss)\b')
def normspace(s):return ' '.join(s.split())
def maxima(s):
    return ORTH['maximaPairs'].get(s[:1],s[:1])+s[1:]
@lru_cache(maxsize=100000)
def words(a):
    return frozenset(k for t in TOKENS.findall(a) for k in lexical_keys(t))
def parallel_units(u):
    n,a,g,e=[u.get(k,'').strip() for k in ('text','analysis','gloss','source')]
    if not all((n,a,g,e)):return
    e=e.replace('ſ','s')
    m=CUE.match(e)
    speaker=None
    if ': ' in n and ': ' in a and ': · ' in g and m:
        na,n=n.split(': ',1);ka,a=a.split(': ',1);ga,g=g.split(': · ',1)
        speaker=(na,ka,ga,m[1].strip().title());e=e[m.end():]
    if any('[' in x or ']' in x for x in (e,n,g,a)):
        n,a,g,e=(DIRECTION.sub(' ',x).strip(' ·') for x in (n,a,g,e))
    n,a,g,e=map(normspace,(n,a,g,e))
    ns,aa,ee=map(BREAK.split,(n,a,e))
    # Periods inside (prs.,sg.) don't end a construction-gloss sentence.
    gs=re.split(r'(?<=[.!?])\s+·\s+',g)
    choices=[]
    if len(ns)==len(aa)==len(ee)==len(gs):
        choices.extend(zip(ns,aa,gs,ee))
    if len(choices)!=1 and len(e.split())<=56 and len(n.split())<=37:
        choices.append((n,a,g,e))
    for nt,at,gt,et in choices:
        if not nt or not et or len(nt.split())>42 or len(et.split())>65:continue
        if BAD.search(nt+' '+et) or REMOTE.search(et) or not FINITE.search(at):continue
        if FRAGMENT.match(et) or re.match(r'^\S{1,36}: ',nt):continue
        if nt[-1] not in '.!?;:,' or et[-1] not in '.!?;:,':continue
        if et[-1] in ',:;' and len(et.split())<5:continue
        nt=maxima(nt.rstrip(',;:')+('.' if nt[-1] in ',;:' else ''))
        et=et[:1].upper()+et[1:].rstrip(',;:')+('.' if et[-1] in ',;:' else '')
        gt=gt.rstrip(',;:')+('.' if gt[-1:] in (',',';',':') else '')
        yield nt,gt,et,words(at),None
        if speaker and 3<=len(nt.split())<=24:
            yield nt,gt,et,{speaker[1]},speaker

def build():
    c=load_gzip(WORK/'attestations.json.gz')
    from tools.dictionary_scope import word_senses
    senses=word_senses(c)
    keys=defaultdict(list)
    for ident,s in senses.items():
        ctx=c['contexts'][s['citations'][0]]
        label=anchors(s['label'].split('{')[0].replace('-',' '))
        meaning=anchors(s['meaning'].split(';')[0]) - label
        keys[s['key']].append((ident,s['form'],ctx['book'],str(ctx['reference']),label,meaning,s['pos']=='proper'))
    ranked=defaultdict(list);locations={};inventory=defaultdict(list)
    def collect(u,book,ref,primary):
        source=normspace(u.get('source',''))
        if not source or REMOTE.search(source) or BAD.search(source):return
        ref=str(ref)
        if (book,ref) not in locations:
            locations[book,ref]=len(locations)
            ix=locations[book,ref]
            context=dict(book=book,reference=ref,**{f:u.get(f,'') for f in ('chapter','text','gloss','analysis','source')})
            contexts.append(context)
            for k in words(u.get('analysis','')):
                for ident,form,eb,er,*_ in keys.get(k,()):
                    indices=inventory[ident]
                    if (len(indices)<18 or (book,ref)==(eb,er)) and head_present(context['text'],form):
                        indices.append(ix)
        for n,g,e,used,speaker in parallel_units(u):
            en=anchors(e)
            if not en:continue
            for k in used:
                for ident,form,eb,er,labels,markers,proper in keys.get(k,()):
                    if not head_present(speaker[0] if speaker else n,form):continue
                    if proper and not speaker and labels and not labels&en and not any(z in en for z in anchors(k.replace('_',' '))):continue
                    if not speaker and (len(n.split())<3 or len(e.split())<4):continue
                    score=(1.6*(eb==book)+1.8*(eb==book and er==ref)+.35*primary+
                           min(4,len(markers&en))*1.6+2*bool(labels&en)+min(11,len(en))*.16-
                           max(0,len(n.split())-20)*.065+(.4 if speaker else 0))
                    options=ranked[ident]
                    if len(options)>=9 and score<=options[-1][0]:continue
                    if any(cand[1]==n and cand[4]==speaker for _,cand in options):continue
                    cand=(book,n,g,e,speaker,ref)
                    options.append((score,cand));options.sort(key=lambda pair:-pair[0]);del options[9:]
    contexts=[]
    for q in c['contexts'].values():collect(q,q['book'],q['reference'],False)
    for row in c['catalog']:
        if not row.get('current'):continue
        path=ROOT/row['path']
        if not path.is_file():continue
        skip=set();over=path.with_name('preserved-edit-overrides.json')
        if over.is_file():
            for grp in read(over)['spreads'].values():skip.update(grp['originalLedgerUnitIds'])
        for u in read(path)['units']:
            if u.get('id') not in skip:collect(u,row['book'],u.get('reference') or u['id'],True)
    save_gzip(BANK,dict(ranked))
    save_gzip(INVENTORY,dict(contexts=contexts,occurrences=dict(inventory)))
    print('Collected',len(contexts),'passages and ranked examples for',len(ranked),'identities.')
if __name__=='__main__':build()
