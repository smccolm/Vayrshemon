"""Dictionary orthography and passage-based examples for lexical senses and namesakes."""
from collections import Counter, defaultdict
from functools import lru_cache
import re

from tools.dictionary_corpus import ORTH, WORK, WORDS, normalize
from tools.dictionary_example_evidence import BANK, INVENTORY, normspace, words
from tools.dictionary_lexicon import load_gzip
from tools.dictionary_sentence_witnesses import BAD, REMOTE, FINITE, anchors, head_present
from tools.dictionary_source_examples import said, witness_name
from tools.dictionary_articles import end

UP = ORTH['maximaPairs']
DOWN = {v:k for k,v in UP.items()}
PUNCT = ' ,:;.!?'
STRONG = re.compile(r'[:.!?]\s*$')
GENERIC = re.compile(r'^(?:The writer names |In whose account |How far is it |Who gave .+ its name|That day they spoke about |When did they |We find .+ in the family genealogy|What did .+ write about this)',re.I)
JEROHAM = {
'benjamin':('father in household of kjv_benjamin','in list of kjv_benjamin kjv_jaresiah and kjv_eliah and kjv_zichri_jeroham as son:pl of @ write:psv:perf.',
           'The Benjaminite roll lists Jaresiah, Eliah and Zichri as sons of Jeroham.','1 Chronicles 8:1'),
'adaiah':('father of kjv_adaiah_priest son of kjv_pashur','in list of priest:pl kjv_adaiah_priest son of @ and @ son of kjv_pashur be:pr.',
          'In the priestly roll Adaiah is the son of Jeroham, and Jeroham is the son of Pashur.','1 Chronicles 9:10'),
'azareel':('father of ruler of kjv_dan','kjv_azareel_jeroham son of @ kjv_tribe of kjv_dan:a rule:pa.',
           'Azareel, son of Jeroham, governed the tribe of Dan.',''),
'azariah':('father of captain kjv_azariah_jeroham_captain','kjv_azariah_jeroham_captain son of @ among captain:pl who into kjv_covenant with kjv_jehoiada_priest enter:pa be:pa.',
           'Azariah son of Jeroham was among the captains who entered into covenant with Jehoiada.',''),
'gedor':('father from kjv_gedor','from kjv_gedor two son:pl of @ to kjv_david at kjv_ziklag come:pa.',
          'Two sons of Jeroham came from Gedor to David at Ziklag.','1 Chronicles 12:1'),
'ibneiah':('father of kjv_ibneiah of kjv_benjamin','in kjv_jerusalem kjv_ibneiah son of @ among people of kjv_benjamin dwell:pa.',
          'Ibneiah son of Jeroham lived in Jerusalem among the people of Benjamin.','1 Chronicles 9:3, 7–8'),
'neh_adaiah_line':('son of kjv_pelaliah_neh_adaiah_line','in account of work of temple @ between his/son kjv_adaiah_neh_adaiah_line and his/father kjv_pelaliah_neh_adaiah_line write:psv:perf.',
          'The temple service roll places Jeroham between his son Adaiah and his father Pelaliah.','Nehemiah 11:10–12'),
}
def skeleton(en):
    # Mask personal/place names while retaining the predicate, roles and circumstances.
    t=re.sub(r'\b[A-Z][\w’\'-]*\b',lambda m: m[0].lower() if m[0] in ('The','A','An','And','But','Then','In','Of','These','From','He','She','They','We','I','With','When','On','How','His','Her','It','There','For') else ' @ ',en)
    return ' '.join(re.findall(r'[a-z0-9@]+',t.lower()))
def significant(en):
    return anchors(skeleton(en)) - {'said','name','son','father','writer','account'}
def weak(ex):
    return GENERIC.search(ex['english']) or ex['method'] in ('contextual pairing','contextual use','source relationship') or re.search(r'^.+ was the (?:son|father|daughter|mother|wife|brother) of [^,;]+[.]$',ex['english'])

class Revision:
    def __init__(self,editor):
        self.ed=editor;self.c=editor.c
        editor.revision=self
        self.bank=load_gzip(BANK);self.inventory=load_gzip(INVENTORY)
        self.verses={str(u['reference']):u for u in self.inventory['contexts'] if u['book']=='King James Bible'}
        self.names=defaultdict(set);self.common=set()
        for s in self.c['senses'].values():
            f=normalize(s['form'])
            if s['pos']=='proper':self.names[f].add(s['label'].split('{')[0].strip().casefold())
            else:self.common.add(f)
        # A lexical title can coincide with an ordinary inflection. Kings and
        # king(pl.) share a written form even though king has its own headword.
        self.witness_case={}
        for form,rows in self.c['forms'].items():
            glosses=defaultdict(set)
            for g,ids,*_ in rows:
                glosses[g.casefold().strip(PUNCT)].update(self.c['senses'][i]['pos']=='proper' for i in ids)
            roles=set().union(*glosses.values())
            if False in roles:self.common.add(form)
            if True in roles:self.names.setdefault(form,set())
            if (True in roles or form in self.names) and (False in roles or form in self.common):
                self.witness_case[form]=dict(glosses)
        self.seen=defaultdict(list);self.audit=Counter()
        self.edited={}
        self.definitions={}
        for line in (WORK/'contextual-definitions.txt').read_text(encoding='utf-8-sig').splitlines():
            if line and not line.startswith('#'):
                k,a,en=line.split(' | ')
                self.definitions[k]=(a,en)
        self.byname=defaultdict(list)
        for item in self.c['senses'].values():
            if item['pos']=='proper':
                word=item['label'].split('{')[0].strip().casefold()
                self.byname[word].append(item)
        for line in (WORK/'contextual-examples.txt').read_text(encoding='utf-8-sig').splitlines():
            if line and not line.startswith('#'):
                keys,syntax,en=line.split(' | ')
                for k in keys.split('/'):
                    if k in self.edited:raise ValueError('Duplicate illustration: '+k)
                    self.edited[k]=(syntax,en)

    def authored(self,syntax,en,s,ctx,definition=False):
        ed=self.ed
        def named(m):
            name=m[0][1:].replace('_',' ');word=name.casefold()
            choices=self.byname.get(word,[])
            if not choices:
                choices=[item for k,recs in ed.d.keyrefs.items() if word in k.split('_') for item in recs if item['pos']=='proper']
            if not choices:raise LookupError(('Missing name',name,s['key']))
            local=words(ctx['analysis'])
            best=max(choices,key=lambda a:(a['key'] in local,head_present(ctx['text'],a['form']),bool(a['contemporary']),a['key']=='kjv_'+word))
            alias='exampleproper'+re.sub('[^a-z]','',word)
            ed.lang.lexicon[alias]=dict(form=best['form'],pos='proper')
            ed.lang.glosses[alias]=name
            return alias
        analysis=re.sub(r'%[A-Za-z_]+',named,syntax)
        if definition:
            value=ed.lang.compile(analysis,initial=False)
            return value['text'],value['gloss'],en
        return ed.compile(analysis,en,'authored illustration')

    @lru_cache(maxsize=180000)
    def proper(self,form,gloss):
        readings=self.c['forms'].get(form,())
        if gloss:
            matching=[r for r in readings if r[0].casefold().rstrip(PUNCT)==gloss.casefold().rstrip(PUNCT)]
            if matching:
                types={self.c['senses'][i]['pos']=='proper' for _,ids,*_ in matching for i in ids}
                if len(types)==1:return types.pop()
        if form in self.names and gloss.casefold().split('(')[0].strip() in self.names[form]:return True
        if form in self.names and form not in self.common:return True
        if form in self.common and form not in self.names:return False
        return None

    def case(self,text,gloss,initial):
        ws=list(WORDS.finditer(text));gs=gloss.split(' · ')
        exact=len(ws)==len(gs)
        gloss_set={g.casefold().strip(PUNCT) for g in gs}
        out=[];prev=0
        for j,m in enumerate(ws):
            between=text[prev:m.start()];out.append(between)
            token=m[0];f=normalize(token)
            start=initial if j==0 else bool(STRONG.search(between))
            p=self.proper(f,gs[j] if exact else '')
            # Multiword names, compounds and explanatory glosses can make the
            # token counts differ. Resolve an ambiguous spelling from its actual
            # construction gloss before falling back to its manuscript case.
            readings=self.witness_case.get(f)
            if readings and (not exact or gs[j].casefold().strip(PUNCT) not in readings):
                roles=set().union(*(readings[g] for g in gloss_set.intersection(readings)))
                if len(roles)==1:p=roles.pop()
            char=token[0]
            new=UP.get(char,char) if start or p is True else DOWN.get(char,char) if p is False else char
            self.audit['initials corrected' if start else 'in-text initials corrected']+=new!=char
            out.append(new+token[1:]);prev=m.end()
        out.append(text[prev:]);return ''.join(out)

    def option(self,row,s,ctx,ex,score):
        n=ex['native'];e=ex['english']
        if not e or not n or not head_present(n,s['form']) or BAD.search(n+' '+e):return
        if re.search(r'^[A-Z][A-Z ,.-]{3,} [A-Z][a-z]',e):return
        if len(n.split())>62 or len(e.split())>95:return
        sk=skeleton(e);content=significant(e)
        prior=self.seen[normalize(s['form'])]
        for p,ps in prior:
            if p==sk:score-=90
            elif content and ps and len(content&ps)/len(content|ps)>.72:score-=5
        return score,ex

    def select(self,r,s,ctx,old,ident,group):
        ed=self.ed;ed.subject(s)
        if 'untaPlaces' in r:return old,None,None
        if s['key'] in self.edited:return self.authored(*self.edited[s['key']],s,ctx),None,None
        if s['key'].startswith('kjv_jeroham_') and (suffix:=s['key'][12:]) in JEROHAM:
            definition,syntax,en,ref=JEROHAM[suffix]
            p=ed.lang.compile(definition,initial=False)
            return ed.compile(syntax,en,'edited source example',ref),p['text'],p['gloss']
        options=[]
        def add(ex,v):
            cand=self.option(r,s,ctx,ex,v)
            if cand:options.append(cand)
        fixed=ident in ed.approved or s['key'] in ed.auth or 'untaPlaces' in r or not ctx
        add(old,100 if fixed else 2 if weak(old) else 11 if old['method']=='composed' else 9)
        if not fixed:
            for value,(book,n,g,e,speaker,ref) in self.bank.get(ident,()):
                if speaker:
                    ex=said(ed,s,speaker[3],n,g,e);ex.update(book=book,ref=ref)
                else:ex=dict(native=n,gloss=g,english=e,book=book,ref=ref,method='keyed passage')
                # Avoid a banked sentence that omits the very concept under discussion.
                if s['pos']!='proper':
                    value+=min(4,len(anchors(s['label'].replace('-',' ')) & anchors(e)))*1.8
                add(ex,value+4)
            if weak(old) or not options or (group and max(v for v,_ in options)<8) or (old['method']=='composed' and s['key'] not in ed.auth):
                indices=self.inventory['occurrences'].get(ident,())
                contexts=[ctx]+[self.inventory['contexts'][i] for i in indices]
                visited=set()
                for i,u in enumerate(contexts):
                    loc=u['book'],str(u['reference'])
                    if loc in visited:continue
                    visited.add(loc)
                    for ex,score in self.from_context(s,u):
                        add(ex,score+(1 if i==0 else 0))
                    if not options or max(v for v,_ in options)<14:
                        try:
                            for ex,score in self.catalogued(s,u):add(ex,score+.3*(i==0))
                        except LookupError:
                            pass  # An unmatched historical spelling cannot support this paraphrase.
                    if (weak(old) or GENERIC.search(old['english']) or group) and (not options or max(v for v,_ in options)<10):
                        for ex,score in self.documented(s,u):add(ex,score+.2*(i==0))
        if not options:return old,None,None
        best=max(options,key=lambda pair:pair[0])[1]
        return best,None,None

    def from_context(self,s,u):
        n,a,g,e=[u.get(q,'').strip() for q in ('text','analysis','gloss','source')]
        if not all((n,a,g,e)) or REMOTE.search(e):return
        book,ref=u['book'],str(u['reference'])
        e=normspace(e.replace('ſ','s'))
        def record(nt,gt,en,method):
            return dict(native=end(nt),gloss=end(gt),english=end(en),book=book,ref=ref,method=method)
        # A stage entrance is a physical action, even when printed without a finite verb.
        directions=list(re.finditer(r'\[([^]]+)\]',e))
        for m in directions:
            stage=m[1].strip();name=witness_name(s,stage)
            if s['pos']!='proper' or not re.search(r'\b'+re.escape(name)+r'\b',stage,re.I):continue
            enter=re.match(r'(?:Re-?enter|Enter)\b',stage,re.I)
            leave=re.match(r'(?:Exit|Exeunt)\b',stage,re.I)
            if not (enter or leave):continue
            verb,action=('enter','entered') if enter else ('depart','departed')
            action='returned' if stage.lower().startswith('re') and enter else action
            if action=='returned':verb='return'
            others=[]
            for k in re.findall(r'[a-zA-Z][a-zA-Z0-9_]+',a):
                candidates=self.ed.d.keyrefs.get(k)
                if not candidates or candidates[0]['pos']!='proper' or k==s['key'] or k not in self.ed.lang.lexicon:continue
                other=witness_name(candidates[0],stage)
                if other.casefold()==name.casefold() or not re.search(r'\b'+re.escape(other)+r'\b',stage,re.I):continue
                if other not in [z[1] for z in others]:others.append((k,other))
            if others:
                syntax='@ with '+' and '.join(k for k,_ in others[:3])+' '+verb+':pa.'
                en=name+' '+action+' with '+' and '.join(z for _,z in others[:3])+'.'
                ex=self.ed.compile(syntax,en,'stage action');ex.update(book=book,ref=ref)
                yield ex,8
        # Roster entries often contain a complete nominal statement with the copula
        # supplied by the preceding verse. Keep its actual count, office or locality.
        if re.match(r'^(?:[123] )?[A-Za-z ]+ \d+:\d+',ref) and s['pos']=='proper':
            for opt in self.roster(s,u,ref):yield opt
        split=r'(?<=[.;:!?])\s+'
        aa,nn,ee=[re.split(split,normspace(q)) for q in (a,n,e)]
        gg=re.split(r'(?<=[.;:!?])\s+·\s+',g)
        segs=[]
        if len(aa)==len(nn)==len(gg):
            for an,nt,gt in zip(aa,nn,gg):
                if s['key'] not in words(an) or not head_present(nt,s['form']):continue
                ga=anchors(gt,True)
                for et in ee:
                    ea=anchors(et);over=len(ga&ea)
                    if over>=2 and over/max(1,len(ga|ea))>=.38:
                        segs.append((nt,an,gt,et,2))
        segs.append((n,a,g,e,0))
        for nt,an,gt,et,extra in segs:
            en=et.strip(PUNCT);en=en[:1].upper()+en[1:]
            if (not 3<=len(nt.split())<=47 or not 4<=len(en.split())<=72 or not FINITE.search(an)
                or re.match(r'^(?:which|whose|although|who |as when|because|if |when |that |for example)',en,re.I)
                or BAD.search(nt+' '+en) or ': ' in nt or re.search(r'^[A-Z][A-Z ]{3,}\b',en)):continue
            if s['key'] not in words(an):continue
            yield record(nt.strip(PUNCT),gt.strip(PUNCT),en,'source passage'),8+extra

    def roster(self,s,u,ref):
        ed=self.ed;name=witness_name(s,u['source']);src=normspace(u['source']);k=s['key']
        match=re.match(r'(.+) (\d+):(\d+)',ref);book,ch,v=match[1],int(match[2]),int(match[3])
        def make(a,e):
            x=ed.compile(a,e,'contextual source reading');x.update(book=u['book'],ref=ref);return x
        def witness(a,e,also):
            x=self.authored(a,e,s,u);x.update(method='contextual source reading',ref=ref+'. '+also)
            return x
        if (book,ch)==('Luke',3) and v>=23:
            seq=[]
            for vn in range(max(23,v-1),min(v+2,39)):
                other=self.verses.get(f'Luke 3:{vn}',{})
                seq.extend(re.findall(r'son of (kjv_\w+)',other.get('analysis','')))
            if k in seq and 0<(j:=seq.index(k))<len(seq)-1:
                child,parent=seq[j-1],seq[j+1]
                if child in ed.lang.lexicon and parent in ed.lang.lexicon:
                    cn,pn=(witness_name(ed.d.keyrefs[t][0],self.verses.get(ref,{}).get('source','')+' '+ ' '.join(z['source'] for z in [self.verses.get(f'Luke 3:{v-1}',{}),self.verses.get(f'Luke 3:{v+1}',{})] if 'source' in z)) for t in (child,parent))
                    yield witness(f'{child} through @ to {parent} in account of kin return:pr.',f'The genealogy runs back from {cn} through {name} to {pn}.',f'Luke 3:{max(23,v-1)}–{min(38,v+1)}'),17
        if book=='1 Chronicles' and ch==8 and 14<=v<=27 and 'son' not in src[:13]:
            lo,hi,par=next(t for t in [(14,16,'Beriah'),(17,18,'Elpaal'),(19,21,'Shimhi'),(22,25,'Shashak'),(26,27,'Jeroham')] if t[0]<=v<=t[1])
            if par.lower()!=name.lower() and re.search(r'\b'+re.escape(name)+r'\b',src,re.I):
                if par=='Beriah':
                    a='@ in house of %Beriah of %Aijalon count:psv:pa.';en=f'{name} was counted in the house of Beriah of Aijalon.'
                elif par=='Elpaal':
                    a='among son:pl of %Elpaal @ in list of %Benjamin write:psv:perf.';en=f'The Benjaminite roll puts {name} among the sons of Elpaal.'
                elif par=='Shimhi':
                    a='@ to house of %Shimhi belong:pa. these house:pl in %Jerusalem dwell:pa.';en=f'{name} belonged to Shimhi’s house. These households dwelt in Jerusalem.'
                else:
                    a='of %'+par+' son:pl @ one be:pa.';en=f'{name} was one of {par}’s sons.'
                yield witness(a,en,f'1 Chronicles 8:{13 if par=="Beriah" else lo}–{28 if par=="Shimhi" else hi}'),17
        if book=='Nehemiah' and ch==12 and 2<=v<=7 and 'return_priest' in k:
            yield witness('@ with %Zerubbabel and %Jeshua from exile return:pa.',f'{name} came back from exile with Zerubbabel and Jeshua.','Nehemiah 12:1, 7'),17
        if book=='Nehemiah' and ch==12 and v==33 and 'procession' in k:
            yield witness('@ with company on wall at feast of city walk:pa.',f'{name} walked with the company on the wall at the dedication of the city wall.','Nehemiah 12:27, 31–33'),17
        if book=='Genesis' and ch==46 and 8<=v<=26:
            parent=re.search(r'(?:sons|children) (?:also )?of ([A-Z][\w-]+)',src)
            if parent and parent[1].casefold()!=name.casefold() and re.search(r'\b'+re.escape(name)+r'\b',src[parent.end():],re.I):
                if '; and the sons of' not in src.lower() and 'daughter' not in s['meaning'].split('.')[0].lower():
                    yield witness('in account of journey to %Egypt @ among child:pl of %'+parent[1]+' count:psv:perf.',f'The account of the journey to Egypt counts {name} among the children of {parent[1]}.','Genesis 46:8'),16
        if book=='Esther' and ch==9 and 7<=v<=9:
            yield witness('@ one of ten son:pl of %Haman be:pa.',f'{name} was one of Haman’s ten sons.','Esther 9:10'),16
        if book=='Genesis' and ch==10 and 26<=v<=29 and name.casefold()!='joktan':
            yield witness('after flood house of %Joktan spread:pa. @ among his/son:pl count:psv:perf.',f'Joktan’s house spread after the flood. {name} is counted among his sons.','Genesis 10:26–32'),16
        # Keep the numerical key (and thus the correct native Unta form) from the roll.
        if (book,ch) in [('Ezra',2),('Nehemiah',7)] and re.match(r'The (?:children|men|sons) of ',src,re.I):
            m=re.match(r'The (children|men|sons) of ([^,;]+),\s*(.+?)[.;:]?$',src,re.I)
            numeric=re.findall(r'\bunta_cardinal_\w+|\b(?:one|two|three|four|five|six|seven|eight|nine|ten|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand)\b',u['analysis'])
            if m and m[2].casefold()==name.casefold() and len(numeric)==1 and numeric[0] in ed.lang.lexicon:
                org='from @' if m[1].lower()=='men' else 'of house of @'
                yield make(numeric[0]+' '+org+' from exile return:pa.',f'{m[3].rstrip(".;:").capitalize()} of '+(f'the house of {name}' if m[1].lower()!='men' else name)+' returned from exile.'),14
        if book=='1 Chronicles' and ch==12 and 9<=v<=13:
            ordinal=re.search(r'\b'+re.escape(name)+r' the ([a-z-]+)',src,re.I)
            if ordinal:
                o=next((t.strip(PUNCT) for t in u['analysis'].split() if t.startswith('unta_ordinal_') and re.search(re.escape(k)+r'\s+'+re.escape(t.strip(PUNCT)),u['analysis'])),None)
                if o and o in ed.lang.lexicon:yield make('@ '+o+' among captain:pl of kjv_gad be:pa.',name+' ranked '+ordinal[1]+' among the Gadite captains.'),14
        frames=[]
        if book=='Joshua' and ch==15 and 21<=v<=62:frames.append(('@ among city:pl which kjv_judah inherit:pa be:pa.',f'{name} belonged to the towns allotted to Judah.'))
        if book=='Joshua' and ch==18 and 21<=v<=28:frames.append(('@ in land of kjv_benjamin lie:pa.',f'{name} lay in Benjamin’s allotment.'))
        if book=='Joshua' and ch==19:
            tribe=next((t for lo,hi,t in [(2,8,'simeon'),(10,16,'zebulun'),(18,22,'issachar'),(25,31,'asher'),(33,39,'naphtali'),(41,46,'dan')] if lo<=v<=hi),None)
            if tribe and 'kjv_'+tribe in ed.lang.lexicon:frames.append(('land of kjv_'+tribe+' to @ reach:pa.',f'The allotment of {tribe.title()} extended to {name}.'))
        if book=='Nehemiah' and ch==10 and 2<=v<=27:frames.append(('@ kjv_covenant:a seal:pa.',f'{name} set his seal to the covenant.'))
        if (book,ch)==('1 Chronicles',11) and 26<=v<=47 or (book,ch)==('2 Samuel',23) and 24<=v<=39:
            frames.append(('@ among warrior:pl of kjv_david serve:pa.',f'{name} served among David’s warriors.'))
        if frames and (re.fullmatch(r"[\w\s,;.'’:-]+",src) and len(src.split())<=23):
            lead,eng=frames[0]
            # Local epithets or fellow towns are meaningful only in their actual role.
            # The shared tribal/office frame alone never establishes different senses.
            named=witness_name(s,src)
            if re.search(r'\b'+re.escape(named)+r'\b',src,re.I) and s['key'] in words(u['analysis']):
                # Do not attribute the head person's office to a named father, place or tribe.
                if book in ('1 Chronicles','2 Samuel') and not re.match(r'^(?:and )?'+re.escape(named)+r'\b',src,re.I):return
                if name.lower() in ('judah','benjamin','david') or re.search('father|territory|people of',s['meaning'].split('.')[0],re.I):return
                yield make(lead,eng),10

    def fragments(self,s,u):
        """Pair short stretches around the keyed word in a longer witness."""
        n,a,g,e=[normspace(u.get(q,'').replace('ſ','s')) for q in ('text','analysis','gloss','source')]
        if not e or REMOTE.search(e) or not head_present(n,s['form']):return
        # Stage directions and dialogue need independent boundaries in all columns.
        n,a,g,e=(t.replace('[','; ').replace(']','; ') for t in (n,a,g,e))
        name=witness_name(s,e).casefold() if s['pos']=='proper' else ''
        def spans(seq):
            for i in range(len(seq)):
                for hi in range(i+1,min(i+3,len(seq))+1):
                    yield i,hi
        ns,aa=[re.split(r'(?<=[,.;:!?])\s+',t) for t in (n,a)]
        gs=re.split(r'(?<=[,.;:!?])\s+·\s+',g)
        if len(ns)!=len(aa) or len(gs)!=len(ns):
            ns,aa,gs=[re.split(r'(?<=[.;!?])\s+(?:·\s+)?',t) for t in (n,a,g)]
        ee=re.split(r'(?<=[,.;:!?])\s+',e)
        pairs=[(n,a,g,e)] if len(n.split())<=31 and len(e.split())<=50 else []
        if len(ns)==len(aa)==len(gs) and len(ns)<110 and len(ee)<130:
            ep=[]
            for i,j in spans(ee):
                t=' '.join(ee[i:j]).strip(PUNCT)
                if not 2<=len(t.split())<=42 or name and not re.search(r'\b'+re.escape(name)+r'\b',t,re.I):continue
                ep.append((t,anchors(t)))
            for i,j in spans(ns):
                at=' '.join(aa[i:j]);nt=' '.join(ns[i:j]);gt=' · '.join(gs[i:j])
                if not head_present(nt,s['form']) or s['key'] not in words(at) or not 2<=len(nt.split())<=30:continue
                ga=anchors(gt,True)
                if ga:
                    hits=[(len(ga&ea)/len(ga|ea),en) for en,ea in ep if len(ga&ea)>=2]
                    if hits and (highest:=max(hits))[0]>=.56:pairs.append((nt,at,gt,highest[1]))
        for nt,at,gt,et in pairs:
            if s['key'] not in words(at) or not head_present(nt,s['form']):continue
            if not 2<=len(nt.split())<=34 or not 2<=len(et.split())<=52:continue
            if ':' in nt.strip(PUNCT) or BAD.search(nt+et):continue
            yield nt.strip(PUNCT),at,gt.strip(PUNCT),et.strip(PUNCT)

    def documented(self,s,u):
        # When the source is an inventory, cast list or genealogy, its clause
        # can be nominal. Supply the governing context rather than inventing events.
        ref=str(u['reference'])
        m=re.match(r'^(.+?) (\d+):(\d+)$',ref)
        if m:
            book,ch,v=m[1],int(m[2]),int(m[3])
        else:book,ch,v='',0,0
        source=u['source']
        context=None
        if book=='Nehemiah' and ch==12 and v<=26:context=('list of priest:pl and people of kjv_levi','the roll of priests and Levites')
        elif book=='Nehemiah' and ch==10 and v<=27:context=('kjv_covenant which people seal:pa','the covenant the people sealed')
        elif book=='Nehemiah' and ch==11:context=('list of they who in city:pl dwell:pa','the register of the inhabitants')
        elif (book,ch) in [('Ezra',2),('Nehemiah',7),('Ezra',8)]:context=('account of journey from exile','the account of the return from exile')
        elif book=='Ezra' and ch==10 and v>=18:context=('account of marriage:pl','the inquiry into the marriages')
        elif book=='Luke' and ch==3 and v>=23:context=('account of kin of kjv_jesus','the genealogy of Jesus')
        elif book=='Numbers' and ch==33:context=('account of journey through wilderness','the itinerary through the wilderness')
        elif book=='Numbers' and ch==13 and v<=16:context=('list of they who land:a see:inf go:pa','the list of those sent to see the land')
        elif book=='1 Chronicles' and ch==6 and 31<=v<=48:context=('account of singer:pl and their/kin','the account of the singers and their families')
        elif book=='1 Chronicles' and ch==24:context=('order of service of priest:pl','the order of priestly service')
        elif book=='1 Chronicles' and ch==25:context=('order of service of musician_person:pl','the order of the musicians’ service')
        elif book=='1 Chronicles' and ch==26 and v<=19:context=('order of they who gate:pl:a guard:pa','the divisions of the gatekeepers')
        elif book=='1 Chronicles' and ch==27:context=('list of they who people:a lead:pa','the register of leaders')
        elif book=='1 Chronicles' and ch==12 and v<23:context=('account of they who to kjv_david come:pa','the account of those who came to David')
        elif book=='1 Chronicles' and ch==11 and v>=10 or book=='2 Samuel' and ch==23 and v>=8:context=('list of warrior:pl of kjv_david','the roll of David’s warriors')
        elif book=='1 Chronicles' and ch<=9 or book=='Genesis' and ch in (10,36,46):context=('account of kin','the genealogy')
        elif book=='Joshua' and 13<=ch<=21:context=('account of division of land','the account of the division of the land')
        elif u['book']=='A New Voyage Round the World':context=('account of journey by sea','the voyage account')
        elif u['book']=='The Sceptical Chymist':context=('account of matter and change','the discussion of matter and change')
        elif u['book']=='Paradise Lost':context=('song','the poem')
        elif u['book'] in ('Leviathan','Two Treatises of Government','The Prince'):context=('book','the treatise')
        else:context=('passage','the passage')
        if context and any(k not in self.ed.lang.lexicon for t in context[0].split() for k in [t.split('/')[-1].split(':')[0]]):context=('record','the record')
        for nt,at,gt,et in self.fragments(s,u):
            finite=bool(FINITE.search(at))
            if finite and not re.search(r'^(?:and |or |whose |which |where |when |saying |then |namely |if |because |that |as |who |with |of |from |to |at |by |for )',et,re.I) and re.search(r'\b(?:is|are|were|was|had|hath|has|have|may|might|can|could|will|would|shall|should|did|doth|do|does|\w{3,}(?:ed|eth))\b',et,re.I):
                yield dict(native=end(nt),gloss=end(gt),english=end(et[:1].upper()+et[1:]),book=u['book'],ref=ref,method='source clause'),8
                continue
            # Quotes mark an actual passage; its introduction is an independent sentence.
            intro=self.ed.lang.compile('in '+context[0]+' thus write:psv:perf.')
            yield dict(native=intro['text'][:-1]+': '+self.ed.lang.maxima(nt)+'.',gloss=intro['gloss'][:-1]+': · '+gt+'.',
                       english='In '+context[1]+' we read, “'+et+'.”',book=u['book'],ref=ref,method='contextual quotation'),5+.08*min(20,len(anchors(gt,True)))

    def catalogued(self,s,u):
        """Restore the governing action of a list from the surrounding record."""
        ref=str(u['reference']);src=normspace(u['source']);k=s['key']
        m=re.match(r'^(.+?) (\d+):(\d+)$',ref)
        if not m or s['pos']!='proper':return
        book,ch,v=m[1],int(m[2]),int(m[3]);name=witness_name(s,src)
        if not re.search(r'\b'+re.escape(name)+r'\b',src,re.I):return
        if re.search(r'\b(?:father|mother|ancestor) of\b',s['meaning'].split('.')[0],re.I):return
        def emit(a,en,extra):
            ex=self.authored(a,en,s,u);ex.update(method='contextual source reading',ref=ref+'. '+extra)
            return ex,14
        person_list=not re.search(r'\b(?:sons?|children|daughters?|house|men|king|inhabitants) of\s+'+re.escape(name)+r'\b',src,re.I)
        if book=='Ezra' and ch==10 and 18<=v<=44:
            qualifier=re.search(r'(?:sons|children) of ([A-Z][a-z-]+)',src)
            if qualifier and qualifier[1].casefold()==name.casefold():
                yield emit('among house of @ man:pl who foreign:m wife:pl take:pa find:psv:pa.',f'Men of the house of {name} were found among those who had taken foreign wives.','Ezra 10:18, 44')
            elif person_list and re.match(r'(?:[A-Z][a-z]+|[;, ])',src):
                yield emit('@ among man:pl who foreign:m wife:pl take:pa count:psv:pa.',f'{name} was counted among the men who had taken foreign wives.','Ezra 10:18, 44')
        elif book=='1 Chronicles' and ch==24 and 7<=v<=18:
            for ordinal,nm in re.findall(r'(?:the )?([a-z-]+) to ([A-Z][A-Za-z-]+)',src):
                if nm.casefold()!=name.casefold():continue
                # Select the ordinal governing this alignment, including historical word forms.
                ordinals=re.findall(r'(\w+(?::ord)?)\s+to\s+'+re.escape(k)+r'\b',u['analysis'])
                if ordinals and ordinals[-1].split(':')[0] in self.ed.lang.lexicon:
                    yield emit(ordinals[-1]+' place in service of priest:pl to @ fall:pa.',f'The {ordinal} turn in the priestly service fell to {name}.','1 Chronicles 24:5–7')
        elif (book,ch) in (('Ezra',2),('Nehemiah',7)):
            group=None
            if book=='Ezra':
                group= 'temple' if 43<=v<=54 else 'Solomon' if 55<=v<=58 else None
            else:group='temple' if 46<=v<=56 else 'Solomon' if 57<=v<=60 else None
            if group and re.search(r'children of '+re.escape(name)+r'\b',src,re.I):
                a='house of @ among servant:pl of '+('temple' if group=='temple' else '%Solomon')+' from exile return:pa.'
                yield emit(a,f'The house of {name} returned from exile among '+('the temple servants.' if group=='temple' else 'the descendants of Solomon’s servants.'),book+' '+str(ch)+(':'+str(43 if book=='Ezra' else 46) if group=='temple' else ':'+str(55 if book=='Ezra' else 57)))
        elif book=='Numbers' and ch==13 and 4<=v<=15:
            tribal=re.search(r'tribe of ([A-Z][a-z-]+)',src)
            who=re.search(r',\s*([A-Z][a-z-]+) the son of ([A-Z][a-z-]+)',src)
            if tribal and who:
                if name.casefold()==who[1].casefold():
                    yield emit('from kjv_tribe of %'+tribal[1]+' @ to land examine:inf send:psv:pa.',f'{name} was sent from the tribe of {tribal[1]} to explore the land.','Numbers 13:2–3')
                elif name.casefold()==who[2].casefold():
                    yield emit('%'+who[1]+' son of @ for kjv_tribe of %'+tribal[1]+' land examine:pa.',f'{who[1]}, son of {name}, explored the land for the tribe of {tribal[1]}.','Numbers 13:2–3')
        elif book=='Numbers' and ch==34 and 19<=v<=28:
            who=re.search(r'([A-Z][a-z-]+) the son of ([A-Z][a-z-]+)',src)
            if who and name.casefold()==who[2].casefold():
                yield emit('%'+who[1]+' son of @ to land divide:inf choose:psv:pa.',f'{who[1]}, son of {name}, was chosen to apportion the land.','Numbers 34:17–18')
        elif book=='Joshua' and ch==12 and 9<=v<=24 and re.search(r'king of '+re.escape(name)+r'\b',src,re.I):
            yield emit('king of @ among king:pl whom people of %Israel overcome:pa count:psv:perf.',f'The king of {name} is counted among the kings defeated by Israel.','Joshua 12:7')
        elif book=='1 Chronicles' and ch==4 and 34<=v<=37 and person_list:
            yield emit('@ one of chief:pl of house:pl of %Simeon be:pa.',f'{name} was one of the chiefs of the houses of Simeon.','1 Chronicles 4:38')
        elif book=='1 Chronicles' and ch==3 and 5<=v<=9 and person_list or (book,ch) in [('1 Chronicles',14),('2 Samuel',5)] and re.search(r'(?:child|son|born).{0,60}(?:david|jerusalem)|david.{0,42}(?:son|child)',s['meaning'].split('.')[0],re.I) and person_list:
            yield emit('when %David in %Jerusalem dwell:pa @ there bear:psv:pa.',f'{name} was born while David was living in Jerusalem.',{'1 Chronicles 3':'1 Chronicles 3:5','1 Chronicles 14':'1 Chronicles 14:4','2 Samuel 5':'2 Samuel 5:13–14'}[book+' '+str(ch)])
        # Where the record supplies a family list and no narrative action, use the
        # actual relationship and family setting, with the correct subject of "of".
        matches=list(re.finditer(r'(?:the )?(sons|children|daughters) (?:also )?of ([A-Z][A-Za-z-]+)[;:,]\s*',src,re.I))
        for j,t in enumerate(matches):
            parent=t[2];listed=src[t.end():matches[j+1].start() if j+1<len(matches) else len(src)]
            if name.casefold()==parent.casefold() or not re.search(r'\b'+re.escape(name)+r'\b',listed,re.I):continue
            if re.search(r'\b(?:father|son|wife|daughter|brother|city|prince|house) of\b',listed,re.I):continue
            if not re.fullmatch(r"[A-Za-z ,.;:’'\-]+",listed) or s['key'].startswith('kjv_tribe'):continue
            if (book,ch)==('Genesis',10):
                yield emit('@ of house of %'+parent+' be:pa when people:pl across earth spread:pa.',f'{name} belonged to the house of {parent} in the account of the dispersal of the nations.','Genesis 10:32')
            elif book=='1 Chronicles':
                yield emit('among child:pl of %'+parent+' @ by name count:psv:perf.',f'{name} is counted by name among the children of {parent}.',ref)

# These pairs denote the same object or action in the supplied readings.
# Figurative extensions and named individuals remain separately indexed.
EQUIVALENTS = (
    ('kjv_sheepcote','sheepcote_shelter'),('kjv_brick_kiln','kjv_brickkiln'),
    ('kjv_hinge','drama_native_kjv_hinge'),('kjv_merchant','merchant'),
    ('kjv_flax','native_flax_root'),('kjv_unload','unload_cargo'),
    ('baby_infant','infant','kjv_infant'),('kjv_mirror','mirror'),
)
def consolidate(rows,c):
    from tools.dictionary_definitions import part_of_speech
    synonyms={k:group for group in EQUIVALENTS for k in group};groups={};result=[]
    for row in rows:
        a=row['article'];ids=a['readingIds']
        if len(ids)!=1 or 'untaPlaces' in row or ids[0] not in c['senses']:
            result.append(row);continue
        s=c['senses'][ids[0]];term=normalize(s['form'])
        if s['pos']=='proper':
            result.append(row);continue
        k=s['key'];meaning=s['meaning'].strip().casefold()
        if k in synonyms:group=(term,synonyms[k])
        else:
            # An identical native paraphrase alone does not establish synonymous senses.
            group=(term,part_of_speech(s['pos']),s['label'].casefold(),meaning,normalize(a['definition']))
        if group not in groups:
            groups[group]=row;result.append(row);continue
        original=groups[group];b=original['article']
        b['readingIds'].extend(ids)
        old=b['references'];new=list(dict.fromkeys(old+a['references']))
        tail=' '+'. '.join(old)+'.' if old else ''
        if tail:assert original['source'].endswith(tail)
        original['source']=original['source'].removesuffix(tail)+' '+'. '.join(new)+'.'
        b['references']=new
    return result
