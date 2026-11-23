"""Select short, complete, keyed example sentences from aligned manuscript units."""
import re
from collections import defaultdict
from functools import lru_cache

from tools.dictionary_corpus import ORTH, ROOT, WORK, normalize, read
from tools.dictionary_lexicon import load_gzip, save_gzip
from tools.dictionary_scope import word_senses

CACHE=ROOT/'.local/dictionary-layout/sentence-witnesses.json.gz'
END=re.compile(r'(?<=[.!?])\s+')
FINITE=re.compile(r':(?:pr|pa|fu|perf|pp|fp|prog|pprog|gn|imp|opt|juss)(?=[:.,;?!\s]|$)')
TOKENS=re.compile(r'[A-Za-z_][A-Za-z_0-9]*(?:[+/:][A-Za-z_][A-Za-z_0-9]*)*')
SPEAKER=re.compile(r'^[A-Z][A-Z ’\-.,]{1,65}(?:\s{2,}|\n)')
BAD=re.compile(r'\[|\]|\.{3}|…|\{\{|\}\}|https?://|Project Gutenberg|[¦|]',re.I)
# The dictionary illustrates ordinary usage. Technical recipes, instructions
# for fighting, and descriptions of sexual violence are poor example sentences.
REMOTE=re.compile(r'\b(?:gunpowder|saltpetre|poison|arsenic|pestilence|bomb|musket|ambush|rape|ravish|venereal|aqua fortis|fulminat\w*|incendiary)\b',re.I)
START_FRAGMENT=re.compile(r'^(?:which|whose|whom|because|although|whereas|inasmuch|to wit|viz|namely|i\.?\s*e\b)\b',re.I)

def head_present(native,head):
    phrase=normalize(head)
    text=normalize(native)
    return re.search(r"(?<![^\s.,:;!?()’\-])"+re.escape(phrase),text) is not None


@lru_cache(maxsize=100000)
def lexical_keys(token):
    # A derivation containing the root is not automatically an example of the independent word.
    return tuple(part.partition(':')[0] for part in token.split('/') if '+' not in part)


def chunks(value):
    return [s.strip() for s in END.split(value.strip()) if s.strip()]


def gloss_chunks(value):
    result=[]; section=[]
    for token in value.split(' · '):
        section.append(token)
        if token.endswith(('.','?','!')):
            result.append(' · '.join(section)); section=[]
    if section:result.append(' · '.join(section))
    return result


STOP=set('a an the i me my thee thine thy thou ye you he she him his her it we their them they and or of for to with at by up on in into out all no be are is was were am as that this there which who shall will do did hath have had not then but so from unto also'.split())
@lru_cache(maxsize=40000)
def stem(word):
    word=word.lower()
    if word in STOP:return ''
    word=re.sub(r'(?:eth|est|ing|ed|es|s)$','',word) if len(word)>4 else word
    return word.rstrip('e') if len(word)>3 else word

def anchors(value,gloss=False):
    if gloss:value=re.sub(r'\([^)]*\)|\{[^}]*\}','',value)
    return {s for w in re.findall('[a-zA-Z]+',value) if (s:=stem(w))}

def aligned_clauses(n,a,g,e):
    # Seek an independent clause using both the keyed native predicate and
    # the words of the actual English witness, even if the translator chose
    # different punctuation in the surrounding paragraph.
    split=re.compile(r'(?<=[,;:.!?])\s+')
    ns,ana=split.split(n),split.split(a)
    gs=re.split(r'(?<=[,;:.!?])\s+·\s+',g)
    if not len(ns)==len(ana)==len(gs):return
    english=split.split(e)
    if len(ns)==1 and len(english)==1:return
    eng=[(q,anchors(q)) for q in english if 3<=len(q.split())<=36]
    for nt,at,gt in zip(ns,ana,gs):
        if not FINITE.search(at) or not 2<=len(nt.split())<=22:continue
        ga=anchors(gt,True)
        if len(ga)<2:continue
        matches=[]
        for et,ea in eng:
            common=len(ga&ea)
            if common>=2 and common>=.67*len(ga) and common>=.67*len(ea):
                matches.append((common,et))
        if len(matches)!=1:continue
        et=matches[0][1].strip()
        if re.match(r'^(?:if|after|before|where|that|unless|when|as|having|while|whose|because|since|whereupon|inasmuch)\b',et,re.I):continue
        yield (ORTH['maximaPairs'].get(nt[0],nt[0])+nt[1:].rstrip(',;:')+('.' if nt[-1] not in '.!?' else ''),
               at,gt.rstrip(',;:'),et[0].upper()+et[1:].rstrip(',;:')+('.' if et[-1] not in '.!?' else ''))


def candidates(unit):
    source=unit.get('source','')
    native=unit.get('text','').strip()
    analysis=unit.get('analysis','').strip()
    gloss=unit.get('gloss','').strip()
    if not all((native,analysis,gloss,source)):return
    if re.match(r'^[^.:;!?]{1,75}:\s',native):
        speaker=SPEAKER.match(source)
        if speaker and ': ' in analysis and ': · ' in gloss:
            native=native.split(': ',1)[1];analysis=analysis.split(': ',1)[1]
            gloss=gloss.split(': · ',1)[1];source=source[speaker.end():]
    # Directions and speaking cues surround many complete lines of dialogue.
    source=re.sub(r'\[[^\[\]]*\]',' ',source).strip()
    native=re.sub(r'\[[^\[\]]*\]',' ',native).strip()
    analysis=re.sub(r'\[[^\[\]]*\]',' ',analysis).strip()
    gloss=re.sub(r'\[.*?\]',' ',gloss).strip(' ·')
    source=' '.join(source.split())
    texts,analyses,glosses,english=chunks(native),chunks(analysis),gloss_chunks(gloss),chunks(source)
    if len(english)==len(texts)==len(analyses)==len(glosses):
        options=zip(texts,analyses,glosses,english)
    elif len(english)==1 and len(texts)<=3 and len(texts)==len(analyses):
        options=[(native,analysis,gloss,source)]
    else:options=[]
    options=list(options)
    options.extend(aligned_clauses(native,analysis,gloss,source))
    # Early prose editions use a semicolon or a colon between independent
    # sentences. Only take an internal clause with its own finite predicate.
    sub=lambda t:[s.strip(' ·') for s in re.split(r'[,;:.!?](?:\s+·\s+|\s+|$)',t) if s.strip(' ·')]
    # Gloss punctuation follows morphological closing parentheses. Splitting
    # ordinary periods inside grammatical labels would lose the alignment.
    gt=[s.strip(' ·') for s in re.split(r'(?<![a-z])[,;:.!?](?:\s+·\s+|$)|[,;:](?:\s+·\s+|$)',gloss) if s.strip(' ·')]
    nt,at,et=sub(native),sub(analysis),sub(source)
    if len(nt)==len(at)==len(et)==len(gt):
        for n,a,g,e in zip(nt,at,gt,et):
            if len(e.split())<4 or re.match(r'^(and|or|but|then|if|when|that|as|whose|before|after|while)\b',e,re.I):continue
            options.append((ORTH['maximaPairs'].get(n[0],n[0])+n[1:]+'.',a+'.',g+'.',e[:1].upper()+e[1:]+'.'))
    for text,syntax,constr,en in options:
        if not 2<=len(text.split())<=36 or not 2<=len(en.split())<=54:continue
        if not FINITE.search(syntax) or BAD.search(text+' '+en) or REMOTE.search(en):continue
        if START_FRAGMENT.search(en) or ':' in en:continue
        if en[-1] in ',;:' and len(en.split())>=4:en=en[:-1]+'.'
        if text[-1] in ',;:':text=text[:-1]+'.'
        if en[-1] not in '.!?' or text[-1] not in '.!?':continue
        if en.isupper() or (len(en)>2 and en[:1].islower()):continue
        if text.count('(')!=text.count(')') or en.count('(')!=en.count(')'):continue
        keys={k for t in TOKENS.findall(syntax) for k in lexical_keys(t)}
        yield text,constr,en,keys


def lexical_facts(unit,senses):
    """Read explicit relations, including genealogies whose listing has no finite verb."""
    analysis=unit.get('analysis','')
    raw=re.findall(r'[a-zA-Z_][a-zA-Z_0-9]*(?::[a-z]+)*|[.,;:!?]',analysis)
    tokens=[t.partition(':')[0] for t in raw]
    def named(k):return k in senses
    def add(a,rel,b):
        if a!=b and named(a) and named(b):return (a,rel,b)
    for i in range(len(tokens)-2):
        a,b,c=tokens[i:i+3]
        if b in ('beget','begat') and (f:=add(a,'father',c)):yield f
        if b=='of' and ':pl' not in raw[i] and a in ('son','daughter','wife','father','mother','brother','sister','king','queen','priest','duke','earl'):
            before=next((t for t in reversed(tokens[max(0,i-3):i]) if t not in (',','the')),None)
            if f:=add(before,a,c):yield f
        # The sons of X: A, B, and C. Limit this expansion to literal name
        # lists so that the next family or the next clause cannot be included.
        if a in ('son','daughter','child') and ':pl' in raw[i] and b=='of' and named(c):
            j=i+3
            while j<len(tokens) and tokens[j] in (',',':','be','and'):j+=1
            while j<len(tokens) and named(tokens[j]):
                if f:=add(tokens[j],a,c):yield f
                j+=1
                while j<len(tokens) and tokens[j] in ('and',','):j+=1


def build():
    corpus=load_gzip(WORK/'attestations.json.gz')
    bykey=defaultdict(list)
    for identity,s in word_senses(corpus).items():bykey[s['key']].append((identity,s['form']))
    best={};scores={}
    names={s['key'] for s in corpus['senses'].values() if s['pos']=='proper'}
    facts=defaultdict(list)
    def consider(u,book,ref,priority):
        for left,rel,right in lexical_facts(u,names):
            fact=[left,rel,right,book,str(ref)]
            for key in (left,right):
                if len(facts[key])<12 and fact not in facts[key]:facts[key].append(fact)
        for n,g,e,keys in candidates(u):
            score=(priority,abs(len(n.split())-8)+len(e.split())/12, len(n))
            for key in keys & bykey.keys():
                for ident,form in bykey[key]:
                    if score<scores.get(ident,(9,999,999)) and head_present(n,form):
                        best[ident]=dict(native=n,gloss=g,english=e,book=book,ref=str(ref),method='attested')
                        scores[ident]=score
    for q in corpus['contexts'].values():consider(q,q['book'],q['reference'],1)
    for row in corpus['catalog']:
        if not row.get('current'):continue
        path=ROOT/row['path']
        if not path.is_file():continue
        skip=set()
        over=path.with_name('preserved-edit-overrides.json')
        if over.is_file():
            for group in read(over)['spreads'].values():skip.update(group['originalLedgerUnitIds'])
        for unit in read(path)['units']:
            if unit.get('id') not in skip:
                consider(unit,row['book'],unit.get('reference') or unit['id'],0)
    save_gzip(CACHE,best)
    save_gzip(CACHE.with_name('dictionary-relations.json.gz'),dict(facts))
    print('Paired example witnesses:',len(best),flush=True)

if __name__=='__main__':build()
