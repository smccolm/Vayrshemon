"""Review relational and evidential vocabulary against the source grammatical reading."""
from collections import Counter,defaultdict
import json
import re

from tools.dictionary_lexicon import load_gzip,save_gzip
from tools.semantic_neighbours import dictionary,normalize


def apply_review(data, additions, grouped, attestations, lang):
    from tools.semantic_expansion import adapted,readrules
    nodes=data['nodes']
    by_form={normalize(n['form']):n['id'] for n in nodes}
    edges=[dict(n['links']) for n in nodes]
    custom=defaultdict(list)
    standard=defaultdict(list)
    for row in readrules('Grammatical choices.txt'):custom[row[0]].append(row)
    custom['at']=custom['at'][:1]+custom['in']+custom['at'][1:]
    for row in readrules('Productive grammar.txt'):standard[row[0]].append(row)
    roles={'adposition':'spatial','preposition':'spatial','conjunction/adposition':'link','modal':'modal',
        'quantifier':'quant','connective':'link','complementizer':'link','relativizer':'link',
        'deictic':'deixis','interrogative':'ask','vocative':'answer','response':'answer'}
    cues={'spatial':['place','mark','way'],'link':['part','group','speech'],'quant':['count','measure','group'],
        'modal':['command','perhaps','promise'],'ask':['answer','recognize','witness'],
        'deixis':['point','remember','speech'],'answer':['voice','answer','listen']}
    terms={'ascend':'climb','reading':'meaning','rope':'binding_rope','buyer':'buy:ag','words':'word:pl',
        'goods':'kjv_goods','source':'origin','safe':'safety','basket':'kjv_basket','load':'kjv_load'}
    def compile_words(text):
        text=re.sub(r'\b[a-z_]+\b',lambda m: terms.get(m[0],m[0]),text)
        text=re.sub(r'\bbase\b','reviewbase',text.replace('@','reviewterm'))
        return lang.compile(adapted(text,lang))
    def link(a,b,tag):
        if a==b:return
        ts=sorted(set(edges[a].get(b,[]))|{tag})
        edges[a][b]=edges[b][a]=ts
    def discard(a,b,tags):
        remaining=sorted(set(edges[a][b])-tags)
        if remaining:edges[a][b]=edges[b][a]=remaining
        else:del edges[a][b],edges[b][a]
    changed=0
    for anchor in nodes:
        pos=anchor['pos']
        if not anchor.get('old') or pos not in roles:continue
        source={}
        for row in grouped[normalize(anchor['form'])]:
            for rid in row['article']['readingIds']:
                rec=attestations['senses'].get(rid,{})
                source.setdefault(rec.get('key',rid.split('@')[0]),row)
        key=next((k for k in source if k=='at' or k in custom),next(iter(source),''))
        family=roles[pos]
        if pos=='adposition' and key in ('of','with','about','for','without','against','except','according_to','because_of','as','by_means'):family='link'
        override=custom.get(key)
        rows=override or standard[family]
        used=anchor['children']
        if not used or any(nodes[j]['method'].startswith(('individual distinction','individual allusion')) for j in used):continue
        anchor['field']='grammar'
        inside=set(used)|{anchor['id']}
        for other in list(edges[anchor['id']]):
            if other not in inside:discard(anchor['id'],other,{'same lexical sense'})
        lang.lexicon['reviewbase']={'form':anchor['form'],'pos':pos};lang.glosses['reviewbase']=anchor['label']
        for i,j in enumerate(used):
            n=nodes[j];r=n['reads'][0];k,label,meaning,definition,example,english=rows[i%len(rows)]
            basis=source.get(k) if override else None
            if not basis:basis=source.get(key)
            lab=anchor['label']
            for other in list(edges[j]):
                if other not in inside:discard(j,other,{'associated sense','connected idea','application','same lexical sense'})
            topic=cues[family][i%3]
            if topic in lang.lexicon and normalize(lang.lexicon[topic]['form']) in by_form:
                link(j,by_form[normalize(lang.lexicon[topic]['form'])],'connected idea')
            label=label.replace('{b}',lab);meaning=meaning.replace('{b}',lab)
            lang.lexicon['reviewterm']={'form':n['form'],'pos':pos};lang.glosses['reviewterm']=label
            nd=compile_words(definition);ne=compile_words(example)
            assert 'reviewterm' in ne['keys'],(k,example,ne)
            n.update(pos=pos,method='individual grammatical choice' if override else 'grammatical specialization',field='grammar',formation='grammatical specialization')
            if basis:n['sourceSense']=basis['id'];n['sourceLabel']=basis['gloss'].partition('. ')[0].strip()
            n['label']=label
            r.update(definition=nd['text'].rstrip('.')+'.',gloss=nd['gloss'],meaning=meaning,example=ne['text'],exampleGloss=ne['gloss'],exampleEnglish=english.replace('@',n['roman']))
            if basis:r['references']=list(basis['article']['references'])
            additions[r['id']].update(pos=pos,label=label,meaning=meaning,origin=n['method']+' from '+anchor['roman'])
            changed+=1
    for n,links in zip(nodes,edges):n['links']=sorted(links.items())
    stats=data['counts']
    stats.update(grammaticalSensesReviewed=changed,edges=sum(map(len,edges))//2,directedLinks=sum(map(len,edges)),
        individual=sum(n.get('method','').startswith('individual') for n in nodes),
        partsOfSpeech=dict(Counter(n['pos'] for n in nodes if not n.get('old'))))
    return data


def main():
    from tools.semantic_expansion import WORK,prepare_lang
    g,a=dictionary();l=prepare_lang()
    data=load_gzip(WORK/'reciprocal-lexicon.json.gz')
    additions=json.loads((WORK/'dictionary-additions.json').read_text('utf8'))
    apply_review(data,additions['entries'],g,a,l)
    save_gzip(WORK/'reciprocal-lexicon.json.gz',data)
    (WORK/'dictionary-additions.json').write_text(json.dumps(additions,ensure_ascii=False,separators=(',',':')),encoding='utf8')
    (WORK/'coverage.json').write_text(json.dumps(data['counts'],indent=2),encoding='utf8')
    print(data['counts'])

if __name__=='__main__':main()
