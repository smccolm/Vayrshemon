"""Tighten the bilingual example and the English lookup cue for conventional allusions."""
from collections import defaultdict
import json
import re
from tools.semantic_expansion import WORK,adapted,prepare_lang,readrules
from tools.dictionary_lexicon import load_gzip,save_gzip

def apply(data,entries,lang):
    diction=readrules('Allusive diction.txt')
    rules={}
    for file in ('Allusive transfers.txt','Register transfers.txt'):
        for kind,lab,*_ in readrules(file):
            op=kind.split()[1].split('/')[0]
            matches=[r for r in diction if lab.startswith(r[0])]
            if op in ('measure','hand'):matches=[r for r in diction if r[0]=={'measure':'measure','hand':'by'}[op]]
            rules[op]=(lab,max(matches,key=lambda r:len(r[0])))
    fields={r[0]:r for r in readrules('Fields of ordinary use.txt')}
    scopes={r[0]:r for r in readrules('Conditions of use.txt')}
    activities=('sharing a catch|mending nets|placing a mooring|taking soundings|changing the night watch|landing a boat|running a ferry|teaching a route|marking a boundary|repairing a roof|reckoning a debt|giving a pledge|distributing bread|keeping seed|tending a sickbed|choosing a guardian|handing over a key|sealing a letter|taking testimony|rehearsing a song|naming a child|recording descent|counting sleepers|setting prices|storing water|drawing charts|passing messages|calling a council|keeping a promise|making a mould|fitting hinges|dyeing cloth|tending the hearth|settling quarrels|dividing a household|carrying a burden|collecting tolls|tending a shared lamp|sharing inherited tools|telling a voyage|opening roads|returning a loan|weighing shares|caring for graves|timing a departure|choosing witnesses|recovering strays|learning a dance|drying grain|marking seasons|setting traps|keeping a child’s confidence|building bridges|measuring a fever|laying down office|preserving recipes').split('|')
    assert len(activities)==len(fields)
    tags=dict(zip(fields,activities))
    trans={'include':'count','number':'count','tally':'count','board':'plank_board','source':'origin',
           'buyer':'buy:ag','expected':'usual','loaded':'heavy','grain':'rye_grain','dawn':'kjv_dawn',
           'loaf':'kjv_loaf','pot':'vessel','bridge':'river_bridge','cart':'cart_vehicle','reef':'dam_reef',
           'handle':'kjv_handle','undo':'reverse','fault':'error','usual':'common','household':'house'}
    def compile_words(s):
        s=re.sub(r'\b[a-z_]+\b',lambda m:trans.get(m[0],m[0]) if m[0] not in lang.lexicon else m[0],s)
        return lang.compile(adapted(s,lang))
    fixed={text:compile_words(text) for text in [r[4] for r in fields.values()]+[r[4] for r in scopes.values()]}
    for n in data['nodes']:
        if n.get('method')!='allusive transfer':continue
        field=n['ordinaryField'];scope=n['usageCondition'];lab,choice=rules[n['formation']]
        if n['label']!=lab.replace('{t}',field)+' · '+scope:continue
        prefix,gloss,en,analysis=choice
        r=n['reads'][0];s=fields[field];t=scopes[scope]
        n['label']=gloss+' · '+tags[field]+' · '+scope
        lang.lexicon['allusiveterm']={'form':n['form'],'pos':n['pos']};lang.glosses['allusiveterm']=gloss
        ne=compile_words(analysis.replace('@','allusiveterm'))
        assert 'allusiveterm' in ne['keys']
        for key,prop in [('example','text'),('exampleGloss','gloss')]:
            r[key]=' '.join(part[prop].rstrip('. ')+'.' for part in (fixed[s[4]],fixed[t[4]],ne))
        r['exampleEnglish']=' '.join((s[5],t[3],en))
        entries[r['id']]['label']=n['label']
    data['counts']['distinctProductiveAllusions']=len({n['label'] for n in data['nodes'] if n.get('method')=='allusive transfer'})
    return data

def main():
    data=load_gzip(WORK/'reciprocal-lexicon.json.gz');ad=json.loads((WORK/'dictionary-additions.json').read_text('utf8'))
    apply(data,ad['entries'],prepare_lang())
    save_gzip(WORK/'reciprocal-lexicon.json.gz',data)
    (WORK/'dictionary-additions.json').write_text(json.dumps(ad,ensure_ascii=False,separators=(',',':')),encoding='utf8')
    (WORK/'coverage.json').write_text(json.dumps(data['counts'],indent=2),encoding='utf8')
if __name__=='__main__':main()
