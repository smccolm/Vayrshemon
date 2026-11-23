"""Compile the reciprocal vocabulary from the issued dictionary and authored sense contrasts."""
from collections import Counter, defaultdict
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
import gzip
import json
import re

from tools.semantic_neighbours import (AUTHOR, BOOK, ROOT, STAGE, Words, collate, content_keys,
                                      dictionary, normalize, readings)
from tools.dictionary_lexicon import language_set, save_gzip
from tools.reciprocal_evidence import word_lookup, source_target
from tools.dictionary_rows import FILING_SLOTS
from tools.editorial_language import TOKEN, WORD

DEST=ROOT/'Saves/Vayrshemon Dictionary and Thesaurus - Reciprocal Vocabulary'
WORK=DEST/'Working'
ALIASES=dict(agreement='dam_agreement',arise='rise',closed='shut',differ='damei_differ',dish='kjv_dish',elder='elder_age',
 feeling='bodily_feeling',members='locke_member:pl',mixture='boyle_mixt',outline='shape',pilot='sea_pilot',
 rudder='rudder_ship',shelter='protection_shelter',speaker='speak:ag',toward='towards',yesterday='yesterday_day',
 dispute='controversy_dispute',me='i',nobody='none',recall='remember',road='way',them='they',kjv_rope='binding_rope',
 contest='contest_goal',fee='price',freedom='freedom_state',goodbye='farewell',sisters='sister:pl',tool='instrument',finished='complete',
 beside='near',earlier='former',learner='pupil_student',link='chain_link',secure='sure',teacher='teach:ag',
 aftermath='after',clue='mark',deputy='instead',fracture='break',fringe='edge',glimpse='see',limit='boundary',
 meeting='meet',momentum='continue',onset='start',opening='open',quotation='quote',recognition='recognize',
 spoor='track',stock='plant_stock',substitute='instead',tide='sea',address='speak',security='pledge',truce='peace',
 remnant='remain',departure='depart',prepare='preparation')
SPECIAL={'ask:need:neg:pa':'need:neg:pa ask:inf','a little way':'little:m way','once farther reach:pa':'once far:m reach:pa',
         'which take:can:neg:pr':'which take:can:neg:pr','in order that':'so that'}
FIELDS={'noun.animal':'animal','noun.plant':'plant','noun.artifact':'artifact','noun.body':'body','noun.cognition':'thought',
 'noun.communication':'speech','noun.event':'event','noun.feeling':'feeling','noun.food':'food','noun.group':'group',
 'noun.location':'location','noun.motive':'thought','noun.object':'material','noun.person':'person','noun.phenomenon':'event',
 'noun.possession':'exchange','noun.process':'event','noun.quantity':'quantity','noun.relation':'relation','noun.shape':'shape',
 'noun.state':'event','noun.substance':'material','noun.time':'time','noun.act':'act','noun.attribute':'quality',
 'verb.body':'act','verb.change':'change','verb.cognition':'thought','verb.communication':'speech','verb.competition':'act',
 'verb.consumption':'act','verb.contact':'act','verb.creation':'act','verb.emotion':'feeling','verb.motion':'motion',
 'verb.perception':'perception','verb.possession':'exchange','verb.social':'act','verb.stative':'quality','verb.weather':'event'}
THEMES={
 'kin':r'\b(?:begat|beget|genealog|lineage|descendan|son of|sons of|daughter of|offspring|grandson|family of|ancestor)',
 'place':r'\b(?:boundary|town|village|river|island|harbou?r|encampment|geographical|coast|coastal|city|settlement|mountain|territory)',
 'office':r'\b(?:king of|queen of|governor|mayor|lieutenant|counci|priest|steward|minister|commander|envoy|consul|senator|treasurer|captain|earl|magistrate)',
 'journey':r'\b(?:sail|sailed|journey|exile|travell?|embark|pilgrim|messenger|voyage|depart|flee|flight|escape|returning)',
 'speech':r'\b(?:prophet|foretell|warning|witness|proclaim|speaker|sermon|reporter|preach|testimony|rumou?r|poet)',
 'gift':r'\b(?:give|gave|gift|bestow|provi[ds]|benefactor|bequeath|patron|bestowed|entrust|donat|hospitality)',
 'loss':r'\b(?:bereav|widow|griev|mourn|surviv|lost|orphan|exiled|perish|slain|burial|afflicted|abandon)',
 'conflict':r'\b(?:battle|quarrel|warrior|dispute|accuse|siege|rebel|rival|soldier|enemy|faction|duel)',
 'conceal':r'\b(?:secret|hidden|disguis|reveal|plotting|dissembl|betray|deceiv|confide|conceal|false identity)',
 'craft':r'\b(?:workman|smith|mason|weav|carpent|artisan|measur|painter|architect|engrave|build|wright|merchant|instrument)',
 'care':r'\b(?:guardian|nurse|tutor|protect|mother of|foster|midwife|physician|healer|companion|care of|keeper)',
 'promise':r'\b(?:promise|vow|swore|sworn|bond|surety|contract|pledge|guarant|covenant|debt)'}
SCENEKEYS=set('son daughter father mother man woman name be one_num two first second say see go come know take give make great small good other person brother sister lord king city kjv_god kjv_lord word before after from house land servant book three child day year same new old hand place time work'.split())
TARGET_FIELDS={'kin':'artifact plant animal thought speech act material food person', 'place':'location shape motion animal body material time',
 'office':'person speech group exchange act thought', 'journey':'motion location artifact food group', 'speech':'thought speech perception feeling',
 'gift':'artifact food exchange material plant', 'loss':'artifact plant speech group feeling', 'conflict':'exchange act group speech location',
 'conceal':'material quality plant animal feeling artifact', 'craft':'artifact material shape food plant', 'roster':'artifact animal plant location speech shape',
 'care':'person plant animal act thought', 'promise':'exchange act material food speech'}
TARGET_FIELDS.update(list='group quantity artifact food animal plant location speech',kinsign='animal plant artifact shape speech material',
    recordlast='act thought speech artifact food plant person location',parallel='thought perception speech act shape material')
ALIASES.update(missing='absent',omission='lack',rim='edge',strangers='stranger:pl',underneath='below',blank='empty',whom='who')
ALIASES.update(sow='plant',maker='make:ag',worker='work:ag',visitor='guest',accustomed='common',usual='common',difficult='hard',material='matter',
    smaller='small',member='locke_member',named='known',check='test',finer='small',saying='word',detail='part',vote='voice',scribe='write:ag')

def readrules(fn):
    return [[x.strip() for x in line.split('|')] for line in (AUTHOR/fn).read_text('utf8').splitlines() if line.strip() and not line.startswith('#')]

def prepare_lang():
    lang,past=language_set()
    lang.lexicon=past.lexicon|{k:v for k,v in lang.lexicon.items() if not k.startswith('reciprocal_')}
    lang.glosses=past.glosses|lang.glosses
    return lang

def adapted(analysis,lang):
    for a,b in SPECIAL.items():analysis=analysis.replace(a,b)
    def alias(m):
        k=m[0]
        return ALIASES[k] if k in ALIASES and k not in lang.lexicon else k
    return re.sub(r'\bher\b(?!/)', 'she:a', re.sub(r'\b[a-z_]+\b',alias,analysis))

def classification(r,wn):
    if r['pos']=='proper':return 'named'
    if r['pos']=='idiom':
        d=r['meaning'].partition(' — ')[-1].lower()
        if re.search(r'\b(grief|relief|shame|longing|love|affection|jealous|felt|sorrow|delight|loneliness|resentment)',d):return 'idiomfeel'
        if re.search(r'\b(skill|crew|net|work|boat|tool|navigation|craft|mend|repair)',d):return 'idiomwork'
        return 'idiom'
    p=r['pos'].lower(); lab=r['label'].lower(); k=r['key']; d=r['record'].get('meaning',r['meaning']).lower()
    if p in ('verb','verb/noun') and not r['sid'].startswith('v'):return 'act'
    if re.search(r'person identified with|resident of|member of the people|inhabitant of|person from|resident or native',d):return 'affiliation'
    if p in ('modifier','adjective','adverb') and (re.search(r'relative to|relating to|pertaining to|bestowed by choice|of or belonging',d) or (r['sid'] and wn.synsets[r['sid']][0]=='adj.pert')):return 'affiliation'
    if p in ('pronoun','preposition','conjunction','particle','clitic','determiner','interjection','article','grammar') or k.startswith(('grammar_','chart_pronoun','chart_particle','thimfora_')):return 'grammar'
    if p in ('number','numeral','ordinal') or 'place-value' in d:return 'quantity'
    if r['sid']:
        domain=wn.synsets[r['sid']][0]
        if domain.startswith('adj.') or domain=='adv.all':return 'quality'
        if (wn.parents(r['sid'])&{'body_of_water','current','tide'}) and domain in ('noun.object','noun.phenomenon','noun.location'):return 'water'
        return FIELDS.get(domain,'thought')
    for f,pat in [('animal','bird|fish|animal|whale|snake|beast|turtle|insect'),('plant','tree|shrub|plant|herb|fruit tree|flower'),('food','food|meal|bread|edible|beverage'),('artifact','tool|implement|vessel|fabric|garment|instrument|furniture|weapon'),('material','substance|metal|powder|mineral|matter'),('person','worker|someone who|artisan|person who|officer'),('location','place where|harbou?r|boundary|region|island'),('time','period of time|interval|season'),('speech','utterance|speaking|declaration|testimony|saying'),('feeling','emotion|grief|feeling|desire'),('group','group of|company of'),('body','part of the body|bodily organ'),('shape','shape|geometric'),('relation','relationship|kinship'),('quantity','amount|unit of|quantity'),('thought','concept|idea|knowledge|opinion')]:
        if re.search(r'\b(?:'+pat+r')\b',d[:180]):return f
    return 'act' if p in ('verb','verb/noun') or re.search(r'^(?:to |act of |action of )',d) else 'quality' if p in ('adverb','modifier','adjective') else 'thought'

def short(s,n=135):
    if len(s)<=n:return s
    return s[:n].rsplit(' ',1)[0]+'…'

def syllable_roots(head,lang):
    raw=normalize(head).translate(FILING_SLOTS)
    chunks=[''.join(c for c in part if c in lang.pairs) for part in raw.split()]
    return [s for s in chunks if s]

def coin(head,pivot,basepos,used,lang):
    h=syllable_roots(head,lang); p=syllable_roots(pivot,lang)
    if not h or not p:raise ValueError((head,pivot))
    def blend(s,n):
        if len(s)<=n:return s
        return s[:n//2]+s[-(n-n//2):]
    root=h[0] if len(h)==1 else h[0]+h[-1]
    aff=p[-1]
    for n in (8,10,13,16,21,30,50,90):
        for r,a in ((blend(root,n),blend(aff,5)),(blend(root,n),aff),(root,aff)):
            for left,right in ((r,a),(a,r)):
                for bind in ('','a','i','u'):
                    form=left+bind+right
                    if len(form)>45 or form in used:continue
                    used.add(form)
                    return form
    raise ValueError(('native compound collision',head,pivot))

def encode(rd,lang):
    inv=sorted(((lang.roman[c],c) for c in lang.pairs if c in lang.roman),key=lambda z:-len(z[0]))
    out=''
    while rd:
        a,b=next((e for e in inv if rd.startswith(e[0])),(None,None))
        if not a:raise ValueError(('Roman spelling',rd))
        out+=b;rd=rd[len(a):]
    return out

def native_key(k,lang):
    a=ALIASES.get(k,k) if k not in lang.lexicon else k
    specific={'substitute':'replace','aftermath':'after','spoor':'mark','opening':'start','quotation':'word','spirit':'breath','fringe':'edge','deputy':'office','address':'speak','remnant':'part','tide':'sea','clue':'mark','track':'mark','grace':'mercy','wear':'use'}
    if k=='substitute':a='other'
    if a not in lang.lexicon:a=specific.get(k,a)
    if a not in lang.lexicon:raise ValueError(('No morpheme',k,a))
    return a

def choose_themes(r,att):
    doc=r['record']
    def evidence(s):
        return re.split(r'identity follows|no modern|supplied local|local context|without invent|not silently|no invented|not merged|not harmonized|not the plural',s.lower())[0]
    meanings=evidence(doc.get('meaning',''))+' '+evidence(r['meaning'])
    material=meanings+' '+r['row']['article']['exampleEnglish'].lower()
    scores={t:10*len(re.findall(pat,meanings))+len(re.findall(pat,material)) for t,pat in THEMES.items()}
    concrete={'place':'gate|abbey|causeway|brook|coast|street|settlement|suburb|departure point','care':'wife|nurse|sister|shelter|fever','kin':'genealogy|beget|begotten|father|offspring|clan|tribal','journey':'navigator|captain|voyage|route','conceal':'allegory|allegorical|symbolic'}
    for th,pattern in concrete.items():scores[th]+=18*len(re.findall(r"\b("+pattern+r")\b",meanings))
    ranked=sorted((t for t in scores if scores[t]),key=lambda t:-scores[t])
    cited=r['record'].get('citations',[])
    if re.search(r'\b(alias|also called|namesake|same name|byname|surname|patronymic)\b',meanings):ranked.append('kinsign')
    if len(cited)>1:ranked.append('parallel')
    if re.search(r'\b(roll|list|census|allocation|division|register|numbered|roster|enumerat)',material):ranked.append('list')
    if re.search(r'\b(last|closing|end|outcome|final|remaining|later)\b',material):ranked.append('recordlast')
    choices=list(dict.fromkeys(ranked))[:2] or ['roster','recordlast']
    return (choices*2)[:2]

def make():
    WORK.mkdir(parents=True,exist_ok=True);STAGE.mkdir(parents=True,exist_ok=True)
    grouped,att=dictionary();l=prepare_lang();wn=Words()
    heads=sorted(grouped,key=collate)
    reserved={normalize(f) for f in att['forms']}|set(heads)|{normalize(v['form']) for v in l.lexicon.values()}
    special=defaultdict(list);rules=defaultdict(list);name_rules=defaultdict(list); edges={};nodes={};entries={};bykey=defaultdict(list); families={}; anchor_ids={};family_by_form={}
    for file in ('Choice distinctions.txt','Individual allusions.txt','Voyage and register allusions.txt'):
        for rec in readrules(file):special[rec[0]].append(rec)
    for file in ('Productive distinctions.txt','Names and idioms.txt','Allusive transfers.txt','Register transfers.txt','Near alternatives.txt'):
        for family,label,d,nd,ne,e in readrules(file):
            f,op=family.split(); typ='noun'
            if '/' in op:op,typ=op.split('/')
            (name_rules if file.startswith(('Allusive','Register')) else rules)[f].append((op,typ,label,d,nd,ne,e))
    anchors=[];key_index=defaultdict(list); pools=defaultdict(list); senseid=defaultdict(list)
    for h in heads:
        rs=readings(grouped[h],att,wn)
        for r in rs:
            key_index[r['key']].append(h)
            if r['sid']:senseid[r['sid']].append(h)
        chosen=min(rs,key=lambda r:(r['key'] not in special,r['pos']=='proper',r['pos']=='idiom' and len(rs)>1,not r['sid']))
        f=classification(chosen,wn); anchors.append((h,rs,chosen,f))
        if chosen['sid'] and f not in ('quality','named','grammar') and len(h)<19 and len(chosen['label'])<25 and not re.search(r'\d|[{}\\[\\]]',chosen['label']):
            pools[f].append((h,chosen))
    word_index=word_lookup(anchors)
    by_head={h:r for h,rs,r,f in anchors}
    def edge(a,b,tag):
        if a!=b:edges.setdefault(tuple(sorted((a,b))),set()).add(tag)
    def save_node(h,n): 
        if h in nodes:raise ValueError(('Duplicate node',h))
        nodes[h]=n
    def resolve(k):
        vals=key_index.get(k,())
        if vals:
            form=normalize(l.lexicon.get(k,{}).get('form',''))
            return form if form in vals else vals[0]
        return None
    def compile_text(ana,base,new,tag,target=None):
        l.lexicon['vendorbase']={'form':base,'pos':'proper' if tag=='named' else 'noun'}
        l.glosses['vendorbase']=by_head[normalize(base)]['label'] if normalize(base) in by_head else l.reading(base)
        if target:
            l.lexicon['vendortarget']={'form':target[0],'pos':'noun'};l.glosses['vendortarget']=target[1]
        x=re.sub(r'\bbase\b','vendorbase',ana).replace('@',new)
        x=re.sub(r'\btarget\b','vendortarget',x)
        return l.compile(adapted(x,l))
    scan=Counter();used_transfers=set(); checked_ops=set()
    for j,(h,rs,r,field) in enumerate(anchors):
        for read in rs:
            bykey[read['key']].append(h)
        base=r['row']['text'].partition('. ')[0]; a=r['row']['article']
        rr=[dict(id=s['row']['id'],definition=s['row']['article']['definition'],gloss=s['label'],construction=s['row']['gloss'],meaning=s['meaning'],
                 example=s['row']['article']['example'],exampleEnglish=s['row']['article']['exampleEnglish'],references=s['row']['article']['references']) for s in rs]
        save_node(h,dict(form=base,roman=l.reading(base),label=r['label'],pos=r['pos'],old=True,reads=rr,field=field))
        children=[]; specials=[(s,ls) for s in rs for ls in special.get(s['key'],())]
        if specials:
            # Homographs across historical versions can share an English key. Assign custom stems to its published form once.
            specials=[(s,z) for s,z in specials if resolve(s['key'])==h]
        if not specials:specials=[None,None] if field=='named' else [None,None,None]
        themes=choose_themes(r,att) if field=='named' else ('','')
        for i,sp in enumerate(specials):
            pivot=None;targ=None;src_read=r;method='productive contrast';explicit=[];op=''
            if sp:
                src_read,z=sp
                sk,extra,roman,pos,label,d,nd,ne,e=z
                form=encode(roman,l)
                if form in reserved:raise ValueError(('Assigned headword exists',sk,roman))
                reserved.add(form);explicit=[v.strip() for v in extra.split(',')];method='individual allusion' if src_read['pos']=='proper' else 'individual distinction'
            else:
                if len(rs)>1 and i==1:
                    alt=next((v for v in rs if v['row']['id']!=r['row']['id'] and (v['pos']=='proper')==(r['pos']=='proper') and v['label'].casefold()!=r['label'].casefold()),None)
                    if alt:src_read=alt
                use_field=classification(src_read,wn)
                if use_field=='named':
                    th=choose_themes(src_read,att)[i];op,pos,label,d,nd,ne,e=name_rules[th][i];method='allusive transfer'
                    # The target sense is part of the new word's denotation. Prefer a field attested alongside the name.
                    nh,q,target_origin=source_target(h,src_read,th,i,att,word_index,key_index,by_head,wn,resolve,classification,TARGET_FIELDS)
                    targ=(nh,q['label']);pivot=nh
                    applied='the '+q['label'].replace('-',' ').lower()
                    label=label.replace('{t}',q['label']);d=d.replace('{t}',applied);e=e.replace('{t}',applied)
                else:
                    op,pos,label,d,nd,ne,e=rules[use_field][i]
                    # Hyponyms and shared readings are other, independently attested entry points to this distinction.
                    if src_read['sid']:
                        ns=[v for rel,other in wn.synsets[src_read['sid']][2] if rel in ('~','@','&','$') for v in senseid.get(other,()) if v!=h]
                        if ns:
                            ns=sorted(set(ns),key=collate);pivot=ns[i%len(ns)]
                morph=native_key(op,l);prefix=src_read['row']['text'].partition('. ')[0]
                form=coin(prefix,l.lexicon[morph]['form'],pos,reserved,l);roman=l.reading(form)
                b=src_read['label'].strip().rstrip('.')
                label=label.replace('{b}',b);d=d.replace('{b}',b);e=e.replace('{b}',b)
                translations={'kin':'traced the chain back to its source','boundary':'fixed its limits','seat':'gave the ruling',
                    'departure':'stayed for the work beyond the journey','witness':'gave the account a second hearing',
                    'gift':'left the means to carry on','remember':'held a place open','limit':'narrowed the quarrel',
                    'reveal':'let the difference show itself','measure':'settled it by the fit','name':'identified it by its company',
                    'watch':'stood by without taking over','pledge':'undertook to bear the cost','omission':'noticed what the count was missing',
                    'mark':'told them apart by the small mark','carry':'carried the practice beyond the record','pair':'braided the two accounts'}
                e=e.replace('we @ the trail','we followed the trail').replace('We @ the trail','We followed the trail')
                for bad,good in [('a particular the ','a particular '),('an otherwise indistinguishable the ','an otherwise indistinguishable '),('one the ','one '),('a proposed the ','a proposed '),('the the ','the ')]:d=d.replace(bad,good);e=e.replace(bad,good)
                e=e.replace('@',translations[op] if use_field=='named' and pos=='verb' else roman)
                if i==2:method='narrower alternative'
                if use_field=='named':
                    d+=' Coined from the use of '+b+' in '+str(src_read['row']['article']['references'][0]).rstrip('.')+'.'
                # The productive morpheme describes how the form was coined. A repeated suffix alone is
                # not semantic evidence for making thousands of cross-references to a single spelling.
                explicit=[] if pivot else [k for k in src_read['record'].get('roots',()) if k not in SCENEKEYS][:2]
            uid='reciprocal_'+sha256((h+'\x00'+form).encode()).hexdigest()[:16].translate(str.maketrans('0123456789','ghijklmnop'))
            l.lexicon[uid]={'form':form,'pos':pos,'meaning':d}
            l.glosses[uid]=label
            anchor=src_read['row']['text'].partition('. ')[0]
            dd=compile_text(nd,anchor,uid,'named' if src_read['pos']=='proper' else field,targ)
            ee=compile_text(ne,anchor,uid,'named' if src_read['pos']=='proper' else field,targ)
            if uid not in ee['keys']:raise ValueError((uid,'example missing reading'))
            refs=list(src_read['row']['article']['references'])
            named_sources={'kjv_solomon':'1 Kings 3:16–28','cordelia_lear_daughter':'King Lear 1.1',
                'penelope_wife':'Odyssey 2, the web of Laertes','gonzalo_naples_councillor':'The Tempest 1.2',
                'kjv_nathan_prophet':'2 Samuel 12:1–7','kjv_ruth':'Ruth 1:14–18',
                'prospero_milan_duke':'The Tempest 5.1','cassandra_priam_daughter':'Troilus and Cressida 2.2 and 5.3',
                'dogberry_messina_constable':'Much Ado About Nothing 4.2 and 5.1',
                'dam_drake':'A New Voyage Round the World, Chapter X, 1039.8','kjv_shallecheth':'1 Chronicles 26:16',
                'adriana_ephesus_wife':'The Comedy of Errors 2.2','kjv_pedahzur':'Numbers 1:10','swinstead_abbey_place':'King John 5.6–7'}
            if sp and src_read['key'] in named_sources:refs=[named_sources[src_read['key']]]+refs
            node=dict(form=form,roman=roman,label=label,pos=pos,field=field,method=method,anchor=h,reads=[dict(id=uid,
                definition=dd['text'].rstrip('.')+'.',meaning=d,gloss=dd['gloss'],example=ee['text'],exampleGloss=ee['gloss'],exampleEnglish=e,references=refs)],
                sourceSense=src_read['row']['id'],formation=op,sourceLabel=src_read['label'])
            if method=='allusive transfer':
                node['sourceUse']=src_read['row']['article']['exampleEnglish']
                node['basis']=src_read['meaning']
                node['transferField']=target_origin
            save_node(form,node);children.append(form)
            entries[uid]=dict(form=form,pos=pos,label=label,meaning=d,origin=method+' from '+l.reading(anchor),roman=roman)
            edge(h,form,'allusion' if src_read['pos']=='proper' else 'narrower sense' if method=='narrower alternative' else 'sense')
            if pivot:edge(form,pivot,'application' if targ else 'associated sense')
            for k in explicit:
                other=resolve(k)
                if other and other!=h:edge(form,other,'connected idea')
        assert len(children)>=2,(h,children)
        for idx,c in enumerate(children):
            for other in children[:idx]:edge(c,other,'sibling distinction')
        families[h]=children
    for k in special:
        if not any(nodes[h].get('method','').startswith('individual') for h in families[resolve(k)]):raise ValueError(('missing custom',k))
    for key,phrase,label,meaning,ana,ex,sentence,related in readrules('Named idioms.txt'):
        primary=resolve(key); h=normalize(l.compile(phrase,initial=False)['text'])
        if h in reserved:raise ValueError(('Existing idiom',h))
        reserved.add(h);uid='reciprocal_idiom_'+key
        d=l.compile(adapted(ana,l));u=l.compile(adapted(ex,l))
        save_node(h,dict(form=h,roman=l.reading(h),label=label,pos='idiom',field='named',method='individual allusive idiom',
            anchor=primary,sourceLabel=by_head[primary]['label'],reads=[dict(id=uid,meaning=meaning,definition=d['text'].rstrip('.')+'.',
            gloss=d['gloss'],example=u['text'],exampleGloss=u['gloss'],exampleEnglish=sentence,references=[named_sources[key]])]))
        entries[uid]=dict(form=h,pos='idiom',label=label,meaning=meaning,roman=l.reading(h),origin='Literary allusion to '+named_sources[key])
        for member in [primary]+families[primary]:edge(h,member,'allusion')
        families[primary].append(h)
        for term in related.split(','):
            if resolve(term):edge(h,resolve(term),'figurative bridge')
    # User's hook idiom connects an observed bite, a secured catch, ease, and a guarantee by different routes.
    hook=normalize(l.compile('fish on fishing_hook',initial=False)['text'])
    if hook in reserved:raise ValueError('Hook idiom already exists')
    hookd='A task spoken of as already in hand because the first resistance has given way. The bite is certain; landing the catch still asks something of the hand. In teasing speech the phrase challenges premature confidence.'
    nd=l.compile('work which after first hard:m part easy:m seem:pr. fish yet from fishing_hook go:can:pr.')
    ee=l.compile('fish on fishing_hook he say:pa. i empty:m kjv_basket show:pa and binding_rope keep:pa.')
    save_node(hook,dict(form=hook,roman=l.reading(hook),label='A fish on the hook',pos='idiom',field='idiom',method='individual idiom',
        anchor=resolve('easy'),reads=[dict(id='reciprocal_hook_idiom',meaning=hookd,definition=nd['text'],gloss=nd['gloss'],
        example=ee['text'],exampleGloss=ee['gloss'],exampleEnglish='“A fish on the hook,” he said. I showed him the empty basket and kept hold of the line.',references=['New native figurative use in this edition.'])]))
    entries['reciprocal_hook_idiom']=dict(form=hook,roman=l.reading(hook),meaning=hookd,label='A fish on the hook',pos='idiom',origin='individual idiom')
    for sk in ('easy','certain','guarantee','fishing_hook','fish_creature'):
        b=resolve(sk)
        if b:edge(hook,b,'figurative bridge')
    for label in ('jōrek','klēmun','renūl','sorām'):edge(hook,encode(label,l),'figurative bridge')
    for a,b in [('easy','certain'),('certain','guarantee'),('desire','consent'),('consent','trust')]:
        edge(resolve(a),resolve(b),'distinguish')
    former=json.loads((BOOK/'Working/sense-register.json').read_text('utf8'))
    oldfamilies=defaultdict(set)
    for v in former.values():
        nh=normalize(v['form'])
        if nh in nodes:oldfamilies[v['family']].add(nh)
    for grp in oldfamilies.values():
        for a in grp:
            for b in grp:
                if a<b:edge(a,b,'earlier thesaurus')
    # Connect true co-lexicalizations; avoid presenting a hypernym or a literary allusion as an interchangeable synonym.
    for group in senseid.values():
        members=list(dict.fromkeys(group))
        for a,b in zip(members,members[1:]):edge(a,b,'same lexical sense')
    ordered=sorted(nodes,key=collate);ids={h:i for i,h in enumerate(ordered)}
    links=[{} for _ in ordered]
    for (a,b),types in edges.items():
        aa,bb=ids[a],ids[b];links[aa][bb]=links[bb][aa]=sorted(types)
    for h,cs in families.items():
        members=list(map(ids.get,[h]+cs))
        assert all(b in links[a] for a in members for b in members if a!=b)
    assert all(links[b][a]==v for a,ls in enumerate(links) for b,v in ls.items())
    for h in ordered:
        n=nodes[h];idx=ids[h];n['id']=idx;n['links']=sorted(links[idx].items());n['children']=[ids[c] for c in families.get(h,())]
        if 'anchor' in n:n['anchor']=ids[n['anchor']]
    totals=dict(startingHeads=len(heads),startingSenses=sum(map(len,grouped.values())),addedHeads=len(entries),heads=len(ordered),
      edges=len(edges),directedLinks=2*len(edges),individual=sum(n.get('method','').startswith('individual') for n in nodes.values()),
      allusiveTransfers=sum(n.get('method')=='allusive transfer' for n in nodes.values()),originalThesaurusFamilies=len(oldfamilies),
      partsOfSpeech=dict(Counter(n['pos'] for n in nodes.values() if not n.get('old'))),everyOriginalHasAtLeastTwo=True,
      everySiblingPairAndReverseLinkVerified=True)
    from tools.reciprocal_grammar_review import apply_review
    complete=dict(counts=totals,nodes=[nodes[h] for h in ordered])
    apply_review(complete,entries,grouped,att,l)
    from tools.reciprocal_allusions import apply as apply_allusions
    apply_allusions(complete,entries,l)
    from tools.reciprocal_diction import apply as apply_diction
    apply_diction(complete,entries,l)
    save_gzip(WORK/'reciprocal-lexicon.json.gz',complete)
    (WORK/'dictionary-additions.json').write_text(json.dumps({'entries':entries},ensure_ascii=False,separators=(',',':')),encoding='utf8')
    (WORK/'coverage.json').write_text(json.dumps(totals,indent=2),encoding='utf8');print(totals,flush=True)

if __name__=='__main__':make()
