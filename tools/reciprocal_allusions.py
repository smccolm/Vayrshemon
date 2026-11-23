"""Lexicalize source allusions into ordinary situations and connect their comparable readings."""
from collections import Counter,defaultdict
from hashlib import sha256
import json
import re
from itertools import combinations

from tools.semantic_neighbours import normalize
from tools.dictionary_lexicon import load_gzip,save_gzip

def apply(data,entries,lang):
    from tools.semantic_expansion import adapted,readrules
    nodes=data['nodes']
    byform={normalize(n['form']):n['id'] for n in nodes}
    edges=[dict(n['links']) for n in nodes]
    spots=readrules('Fields of ordinary use.txt')
    conditions=readrules('Conditions of use.txt')
    variants=defaultdict(list)
    for file in ('Allusive transfers.txt','Register transfers.txt'):
        for head,*row in readrules(file):
            op=head.split()[1].split('/')[0]
            variants[op].append(row)
    for op,*row in readrules('Alternative allusive readings.txt'):variants[op].append(row)
    enverb=dict(kin='traced it back',boundary='fixed the limits',seat='gave a ruling',departure='stayed on',
        witness='brought it to a second hearing',gift='left her the means to carry on',remember='held a place open',
        limit='narrowed the quarrel',reveal='let the difference show',measure='tested it by the fit',
        name='identified it by its company',watch='stood by without taking over',pledge='undertook the cost',
        omission='noticed what was missing',mark='told them apart',carry='carried the teaching on',pair='put the two accounts together')
    links=defaultdict(list);bytopic=defaultdict(list);comparisons=defaultdict(list); counts=Counter();usage=Counter()
    concepts={}
    def target(k):
        if k in concepts:return concepts[k]
        extra={'road':'way','buyer':'buy','dispute':'controversy_dispute','agreement':'dam_agreement','reserve':'keep','objection':'oppose',
          'generation':'child','gesture':'point','kin':'family_group','borrow':'lend','far':'distance','pupil_student':'learn',
          'hunt':'hunting','watch':'guard','keeper':'keep','letter':'write','map':'way','animal':'beast'}
        t=lang.lexicon.get(k) or lang.lexicon.get(extra.get(k,'')) or {}
        concepts[k]=byform.get(normalize(t.get('form','')))
        return concepts[k]
    def couple(a,b,tag):
        if a is None or b is None or a==b:return
        ts=sorted(set(edges[a].get(b,()))|{tag});edges[a][b]=edges[b][a]=ts
    trans={'buyer':'buy:ag','tally':'count','local':'here','heretofore':'before','reading':'meaning','safe':'safety',
       'expected':'usual','handover':'give:ev','loaded':'heavy','exactly':'truly','fault':'error','unknown':'hidden','correct':'mend',
       'learner':'pupil_student','undo':'reverse','household':'house','usual':'common','mould':'shape','road':'way','dying':'dyeing'}
    trans.update(hunting='hunt:ev',dawn='kjv_dawn',grain='rye_grain',reef='dam_reef',board='plank_board',assent='consent',
                 bridge='river_bridge',pot='vessel',loaf='kjv_loaf',cart='cart_vehicle',handle='kjv_handle')
    def compilation(s):
        s=re.sub(r'\b[a-z_]+\b',lambda m: trans.get(m[0],m[0]) if m[0] not in lang.lexicon else m[0],s)
        return lang.compile(adapted(s,lang))
    native={x:compilation(x) for row in spots for x in (row[1],row[4])}
    native.update({x:compilation(x) for row in conditions for x in (row[2],row[4])})
    keywords=[set(row[3].lower().split()) for row in spots]
    def wordset(s):return {w.removesuffix('s') for w in re.findall('[a-z]+',s.lower())}
    def salt(s):return int.from_bytes(sha256(s.encode()).digest()[:4],'big')
    changed=0
    for n in nodes:
        if n.get('method')!='allusive transfer':continue
        r=n['reads'][0];j=n['id'];op=n['formation']
        ref=n['sourceLabel']; choices=variants[op]
        v=(salt(n['form']+op)%len(choices));rule=choices[v]
        head=n['form']; label,d,nd,ne,ex=rule
        primary=wordset(n['basis']);secondary=wordset(n['sourceUse'])
        ranking=[4*len(s&primary)+len(s&secondary) for s in keywords]
        start=salt(ref+head)%len(spots);off=salt(head+ref)%len(conditions)
        theme,vary=min(((a,b) for a in range(len(spots)) for b in range(len(conditions))),
           key=lambda ab:(usage[(op,v,*ab)], -ranking[ab[0]], counts[(op,v,ab[0])], (ab[0]-start)%len(spots), (ab[1]-off)%len(conditions)))
        usage[(op,v,theme,vary)]+=1;counts[(op,v,theme)]+=1
        phrase,ana,key,cues,scene,engscene=spots[theme]
        qualification,meaningq,criterion,engdetail,detail,cue=conditions[vary]
        label=label.replace('{t}',phrase)+' · '+qualification
        d=d.replace('an otherwise indistinguishable {t}','an otherwise indistinguishable element in the '+phrase).replace('an uncertain instance of {t}','an uncertain point in the '+phrase)
        d=d.replace('a particular {t}','a particular practice in the '+phrase).replace('a proposed {t}','the proposed arrangement for the '+phrase)
        d=d.replace('one {t} from another','two instances within the '+phrase).replace('missing {t}','gap in the '+phrase)
        d=d.replace('{t}','the '+phrase)
        d=d.rstrip('.')+'. '+meaningq
        basis=str(r['references'][0]).rstrip('.')
        d+=' Allusion to '+ref+' in '+basis+'.'
        lang.lexicon['allusiveterm']={'form':head,'pos':n['pos']};lang.glosses['allusiveterm']=label.partition(' · ')[0]
        dd=compilation(nd.replace('target','('+ana+')').replace('(','').replace(')',''))
        ee=compilation(ne.replace('target',ana).replace('@','allusiveterm'))
        assert 'allusiveterm' in ee['keys']
        english=ex.replace('{t}', 'the '+phrase).replace('we @ the trail','we traced the line').replace('We @ the trail','We traced the line')
        english=english.replace('@',enverb.get(op,n['roman']) if n['pos']=='verb' else n['roman'])
        for src,dst in (('the the ','the '),('the place of the the ','the place of the ')):english=english.replace(src,dst);d=d.replace(src,dst)
        def joined(parts):return ' '.join(p.rstrip('. ')+'.' for p in parts)
        r.update(meaning=d,definition=joined([dd['text'],native[criterion]['text']]),gloss=joined([dd['gloss'],native[criterion]['gloss']]),
          example=joined([native[scene]['text'],native[detail]['text'],ee['text']]),
          exampleGloss=joined([native[scene]['gloss'],native[detail]['gloss'],ee['gloss']]),exampleEnglish=' '.join((engscene,engdetail,english)))
        n.update(label=label,ordinaryField=phrase,usageCondition=qualification)
        entries[r['id']].update(label=label,meaning=d)
        oldanchor=n['anchor']
        for other in list(edges[j]):
            if 'application' in edges[j][other]:
                ts=sorted(set(edges[j][other])-{'application'})
                if ts:edges[j][other]=edges[other][j]=ts
                else:del edges[j][other],edges[other][j]
        couple(j,target(key),'application')
        links[(op,v,theme)].append(j)
        comparisons[(op,v,vary)].append(j)
        bytopic[(theme,vary)].append(j)
        changed+=1
    def weave(groups):
        # Two adjacent native forms provide a tractable way to browse a large semantic family.
        # Every edge is reciprocal, and the original source/sibling families retain their full cliques.
        for group in groups.values():
            ids=sorted(group)
            if len(ids)==1:continue
            for a,b in zip(ids,ids[1:]+ids[:1]):couple(a,b,'associated sense')
    weave(links);weave(comparisons)
    for grp in bytopic.values():
        byop={}
        for j in grp:byop.setdefault(nodes[j]['formation'],j)
        ids=list(byop.values())
        for a,b in zip(ids,ids[1:]):couple(a,b,'application')
    # Link ordinary new words across dictionary roots only where they share a lexical
    # operation and their parents already have a dictionary or thesaurus relationship.
    old=[n for n in nodes if n.get('old')]
    index={n['id']:{nodes[c].get('formation'):c for c in n['children'] if nodes[c].get('method') in ('productive contrast','narrower alternative')} for n in old}
    for a in old:
        i=a['id']
        for k,tags in list(edges[i].items()):
            if k<=i or k not in index or not(set(tags)&{'earlier thesaurus','same lexical sense'}):continue
            for op in index[i].keys() & index[k].keys():couple(index[i][op],index[k][op],'associated sense')
    # The near alternative's English definition identifies its actual head even when the common
    # productive rule, e.g. 'a plant of this kind', occurs in several dictionary entries.
    for n in nodes:
        if n.get('method')!='narrower alternative':continue
        r=n['reads'][0];core=r['meaning'].split(' — ',1)[-1];r['meaning']=n['sourceLabel']+' — '+core
        entries[r['id']]['meaning']=r['meaning']
    # Connect isolated source families by the documented lexical morpheme in their new word.
    def components():
        seen=set();out=[]
        for i in range(len(nodes)):
            if i in seen:continue
            group=[];stack=[i];seen.add(i)
            while stack:
                a=stack.pop();group.append(a)
                for b in edges[a]:
                    if b not in seen:seen.add(b);stack.append(b)
            out.append(group)
        return sorted(out,key=len,reverse=True)
    initial=components()
    from tools.semantic_expansion import native_key
    for group in initial[1:]:
        inside=set(group)
        for j in group:
            op=nodes[j].get('formation','')
            if not op or nodes[j].get('old'):continue
            try:pivot=target(native_key(op,lang))
            except ValueError:continue
            if pivot is None or pivot in inside:continue
            couple(j,pivot,'connected idea');break
    for n,ls in zip(nodes,edges):n['links']=sorted(ls.items())
    cs=components()
    data['counts'].update(edges=sum(map(len,edges))//2,directedLinks=sum(map(len,edges)),allusiveUseConditions=len(conditions),allusiveOrdinaryFields=len(spots),distinctProductiveAllusions=len({n['label'] for n in nodes if n.get('method')=='allusive transfer'}),connectedComponents=len(cs),largestComponent=len(cs[0]))
    return data

def main():
    from tools.semantic_expansion import WORK,prepare_lang
    lang=prepare_lang();data=load_gzip(WORK/'reciprocal-lexicon.json.gz');ad=json.loads((WORK/'dictionary-additions.json').read_text('utf8'))
    apply(data,ad['entries'],lang);save_gzip(WORK/'reciprocal-lexicon.json.gz',data)
    (WORK/'dictionary-additions.json').write_text(json.dumps(ad,ensure_ascii=False,separators=(',',':')),encoding='utf8')
    (WORK/'coverage.json').write_text(json.dumps(data['counts'],indent=2),encoding='utf8');print(data['counts'])
if __name__=='__main__':main()
