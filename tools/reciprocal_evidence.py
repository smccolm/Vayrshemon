"""Find an attested field of transfer in the evidence for the actual named referent."""
from collections import defaultdict
import re

from tools.semantic_neighbours import content_keys

STOP=set('about after before which while speak see look call each must term know role other from source book witness local early great latter cannot here named text variant spelling english name context remain reading identity given woe general whose modern nearby below above this that both came went were unto account recorded related stated person people place says father son year days after city neither same form locality relations relationships local biblical mentioned verse mean chapter note wording names narrative use explicitly records bible reference what correct distinct follows closing witness section further copied referred supplied title additional alternative later without translated written index listed references parallel tradition determiner historical scope unknown current exact literal editorial explicit figurative narrative structure book portion item proper semantic personage external identified identification'.split())
STOP.update('on in at as by to and with into am is was have had being many more late of us do yes may can could thou shall then there than when who his her they him its my or an over upon every last first also north south east west book alone hear say ask come see alone go out how away set get all not put one the than following form singular plural named route accordingly within its their our yours personal speaking supplied what addition possessive locality specific spelling source name homonym no interpretation putative language'.split())
NOMINAL={'artifact','plant','animal','location','water','material','time','food','person','thought','group','shape','relation','exchange','body','feeling','speech','quantity','event','affiliation'}
DOMAIN={'kin':('family_group','kin','inheritance','birth','memory','line'), 'place':('boundary','way','shore','land','harbour'),
    'journey':('journey','hobbes_navigation','voyage','passage','return','shelter'), 'care':('care','help','duty','safety','trust'),
    'office':('judgment','duty','rule','office','trust'), 'speech':('testimony','news','warning','memory','story'),
    'gift':('gift','provision','care','relief','work'), 'loss':('memory','loss','family_group','home','inheritance'),
    'conflict':('disagreement','land','oath','judgment','duty'), 'conceal':('identity','testimony','likeness','judgment'),
    'craft':('work','measure','shape','skill','material'),'promise':('promise','debt','exchange','pledge'),
    'list':('record_register','roll','assembly','family_group'), 'kinsign':('identity','name','family_group','likeness'),
    'parallel':('testimony','record_register','story','memory'),'recordlast':('record_register','practice','inheritance','memory'),
    'roster':('record_register','family_group','company','journey')}
FALLBACK=dict(kin='kin',place='boundary',office='office',journey='journey',speech='testimony',gift='gift',loss='memory',conflict='disagreement',conceal='identity',craft='work',care='care',promise='promise',list='count',kinsign='mark',recordlast='inherit',parallel='testimony',roster='register')
def word_lookup(anchors):
    result=defaultdict(list)
    for h,rs,r,f in anchors:
        for q in rs:
            if not q['sid'].startswith('n') or q['pos'] not in ('noun','noun/verb','root','lexical') or not q['label'].islower():continue
            label=q['label'].lower()
            if label not in STOP and re.fullmatch(r'[a-z]+(?:[- ][a-z]+){0,2}',label):result[label].append((h,q))
    return result

def source_target(h,r,th,i,att,word_index,key_index,by_head,wn,resolve,classification,fields):
    primary=re.split(r'Identity follows|Local context|Supplied local|No modern',r['meaning'])[0]
    source=r['row']['article']['exampleEnglish']; ranked={}
    def rank(nh,q,score):
        if h==nh or q['label'].lower() in STOP or len(q['label'])>32 or not q['sid'].startswith('n'):return
        if q['pos'] not in ('noun','noun/verb','lexical','root') or not q['label'].islower() or nh==h or len(q['label'])<3:return
        cat=classification(q,wn)
        if cat not in NOMINAL or cat not in fields[th].split():return
        if q['pos'] in ('root','lexical') and (wn.index.get((q['label'].lower(),'verb')) or wn.index.get((q['label'].lower(),'adj'))):return
        score+=2*(cat in fields[th].split())
        if nh not in ranked or score>ranked[nh][0]:ranked[nh]=(score,q)
    for witness,score in ((primary,30),(source,18)):
        terms=re.findall('[a-z]+',witness.lower())
        for at,t in enumerate(terms):
            for w in (t,t.removesuffix('s'),t.removesuffix('es'),t[:-3]+'y' if t.endswith('ies') else ''):
                for nh,q in word_index.get(w,()):rank(nh,q,score+min(5,len(t)*.4)-min(at,100)*.03)
    for cite in r['record'].get('citations',[]):
        for k in content_keys(att['contexts'].get(cite,{}).get('analysis','')):
            if k in ('one_num','two','be','say','see'):continue
            for nh in key_index.get(k,()):
                q=by_head[nh];rank(nh,q,12)
    candidates=sorted((nh for nh in ranked if ranked[nh][0]>=29),key=lambda nh:-ranked[nh][0])
    if candidates:
        nh=candidates[min(i,len(candidates)-1)]
        return nh,ranked[nh][1],'source language'
    choices=DOMAIN[th]
    nh=next(resolve(t) for t in (*choices[i:],*choices[:i],FALLBACK[th],'name','word') if resolve(t))
    return nh,by_head[nh],'function of the record'
