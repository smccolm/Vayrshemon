"""Select and index sense-specific word choices for the conventional thesaurus."""
from collections import Counter,defaultdict
import json

from tools.conventional_reference import part,print_part,write_json
from tools.dictionary_rows import filing_initial
from tools.reciprocal_publication import digit
from tools.semantic_neighbours import BOOK,Words,dictionary,normalize,readings,tokens
from tools.vayrshemon_thesaurus import read_families


def word_class(pos):
    return {'adj':'modifier','adjective':'modifier','v':'verb','noun/verb':'noun','verb/noun':'verb',
            'n, cnt':'noun','n, m':'noun'}.get(pos.strip(),pos.strip())


def groups(nodes,lang):
    result=[];signatures=set()
    by_form={normalize(n['form']):n['id'] for n in nodes}
    by_roman={n['roman']:n['id'] for n in nodes}
    senses={r['id']:(n['id'],r) for n in nodes for r in n['reads']}
    def add(title,native,category,members):
        members=list(members)
        signature=tuple(sorted((i,r['id']) for i,r in members))
        if len({i for i,_ in members})<2 or signature in signatures:return
        assert len(set(i for i,_ in members))==len(members)
        assert all(r['definition'] and r['example'] and r['exampleEnglish'] for _,r in members)
        signatures.add(signature)
        result.append(dict(title=title,native=native,kind=category,members=members))

    # The earlier thesaurus contains distinctive authored comparisons and examples.
    register=json.loads((BOOK/'Working/sense-register.json').read_text('utf8'))
    published={(s['family'],s['key']):s for s in register.values()}
    for f in read_families():
        members=[]
        for e in f['entries']:
            k=e['key'];s=published[f['title'],k];i=by_form[normalize(s['form'])]
            d=lang.compile(e['note'],initial=False)
            ex=lang.compile(e['usage'].replace('@',k))
            assert s['example']==ex['text'] and s['exampleEnglish']==e['english']
            members.append((i,dict(id='authored-'+k+'-'+f['title'],definition=d['text'],gloss=d['gloss'],
                example=s['example'],exampleGloss=ex['gloss'],exampleEnglish=s['exampleEnglish'],meaning=e['label']+'. '+e['nuance'])))
        add(f['title'],lang.compile(f['analysis'])['text'],'authored word choices',members)

    # Separate readings of polysemous words by lexical sense and grammatical function.
    source,att=dictionary();wn=Words();original={};shared=defaultdict(dict)
    pos_for=dict(n='noun',v='verb',a='modifier',r='adverb')
    for form,rows in source.items():
        for r in readings(rows,att,wn):
            sid=r['sid'];rid=r['row']['id'];pos=word_class(r['pos'])
            original[rid]=r
            if not sid or pos!=pos_for.get(sid[0]):continue
            word=r['label'].strip().casefold().replace(' ','_').replace('-','_')
            if word not in wn.synsets[sid][1]:continue
            evidence=tokens(r['meaning']) & wn.synsets[sid][3]
            glosses=wn.index.get((word,{'n':'noun','v':'verb','a':'adj','r':'adv'}[sid[0]]),[])
            if len(glosses)>1 and not (evidence-{word}):continue
            i,rd=senses[rid]
            shared[sid].setdefault(i,rd)
    for sid,forms in shared.items():
        if len(forms)>1:
            members=sorted(forms.items())
            add(original[members[0][1]['id']]['label'],nodes[members[0][0]]['form'],'shared lexical sense',members)

    # Words denoting the same native operation within the same field, qualified by
    # different conditions. A literary name by itself supplies no synonym evidence.
    allusions=defaultdict(list);specializations=defaultdict(list);parallels=defaultdict(dict)
    for n in nodes:
        if n.get('old'):continue
        rd=n['reads'][0];rid=n.get('sourceSense');method=n['method'];i=n['id']
        if method=='allusive transfer':
            key=(n['pos'],n['ordinaryField'],n['label'].partition(' · ')[0],rd['definition'].partition('. ')[0])
            allusions[key].append((i,rd))
        elif method in ('individual grammatical choice','grammatical specialization','narrower alternative'):
            parent,rr=senses[rid];r=original[rid]
            if word_class(r['pos'])==word_class(n['pos']) and n['pos'] not in ('proper','idiom'):
                specializations[rid].append((i,rd))
        if method in ('productive contrast','narrower alternative'):
            r=original[rid];sid=r['sid']
            if sid in shared and n['anchor'] in shared[sid] and shared[sid][n['anchor']]['id']==rid:
                parallels[sid,n['formation'],n['pos']][i]=rd
    for rid,others in specializations.items():
        i,r=senses[rid]
        add(original[rid]['label'],nodes[i]['form'],'more specific alternatives',[(i,r),*others])
    for (_,_,title,native),members in allusions.items():
        add(title,native,'contextual alternatives',members)
    for key,forms in parallels.items():
        if len(forms)>1:
            i=next(iter(forms))
            add(nodes[i]['label'],nodes[i]['form'],'parallel readings of synonyms',forms.items())

    # These pairs are distinguished by semantic force even where the parent English
    # label has a different grammatical role (e.g. "certain" versus "certainty").
    choices=[
        ('Ease of a task','easy:m work',['sense-fbefaafb70fc3ae721','renūl','vālem']),
        ('Certainty about an outcome','certainty',['sense-3a2fb8ee5ccee345b5','jōrek','klēmun','drigôl gren drigôllunor gläzhwen']),
        ('Grounds for reassurance','promise',['sorām','telōshel']),
        ('Trust under uncertainty','trust',['neshūl','thāmir']),
        ('Kinds of practiced skill','skill',['sense-b41efcea54d45a4a80','perōn','ēshar']),
        ('Giving someone the means to continue','gift',['sense-b91f5e6d3b69809b2b','gonzūm','govis grel mayemszarunthen']),
        ('Helping within the limits of one’s power','help:inf',['sense-f1a70d1caebee148ce','gonzār']),
        ('Giving something up while it is still yours to wield','give:inf',['sense-40b1e78736d943f5fa','sense-1d03584469131bda3b','prosen']),
        ('A pause that keeps a decision open','wait:inf',['sense-c8d92fd0d3f964e332','penūrel']),
        ('Room to reconsider','time to choose:inf',['sense-daddcee0ab823fbfac','ānggif i felen']),
        ('A warning that precedes public evidence','warning',['sense-a30e7558c13699cb01','enifetyeks pôn kumul']),
        ('Putting a claim to the test','judge:inf',['sense-a0b63d47b768466ff6','shalōvek','natēl']),
        ('An opinion that becomes a judgment of oneself','judgment',['sense-0b5e529d79c038ea62','nerbwāvumen chetib zôlin mourowya']),
        ('Grounds for believing a claim','evidence',['sense-0ac71e0e5a2a367dbf','drārun']),
        ('Credible through conduct','credible:m',['sense-57376ee61ecadcff14','shalōrin']),
        ('An accusation that has the wrong subject','wrong:m',['sense-b481d029746c5ce31f','adrinōl']),
        ('Sound testimony imperfectly expressed','testimony',['sense-6d2f5f0ed744954b21','dogbēn','murlamet’mū tremborel lôm’mū yemsē']),
        ('The first response given freely','free:m answer',['prosāri','trembār hüth braden']),
        ('Affection that can escape notice','love',['sense-cca16bbe1c85cb304b','kordūn']),
        ('Faithful by choice','faithful:m',['sense-db42703b5cb65f2c9d','rūtem']),
        ('Refusing to perform on demand','refuse:inf',['sense-539c74125a726337c5','kordēv']),
        ('Companionship beyond the obligation to escort','together',['rūthir','nathavim daral rãnth thātus swifun']),
        ('A shelter and what makes it one','refuge',['sense-db8bb6852b9e6976b6','sense-720523aece889d2fed','swinstel']),
        ('How care is given','care:inf',['sense-e1f3989de5fe087d40','sense-667c0700625f15b115','swinnār']),
        ('Desire for intimacy','desire',['sense-142ca4e972d53b5908','ilāven']),
        ('Kinds of permission','consent',['sense-54417249b15e9d943a','omēri','surēn']),
        ('Fixing the time for a task','time of work',['sense-4750aa866d976abb18','drākem'])]
    for title,analysis,forms in choices:
        members=[senses[r] if r in senses else (by_roman[r],nodes[by_roman[r]]['reads'][0]) for r in forms]
        add(title,lang.compile(analysis)['text'],'authored word choices',members)
    return result


def thesaurus_articles(nodes,lang,work):
    families=groups(nodes,lang)
    by_member=defaultdict(list)
    for k,f in enumerate(families,1):
        for i,r in f['members']:by_member[i].append(k)
    heads=sorted(by_member)
    locator={i:j//1600+1 for j,i in enumerate(heads)}
    lookup=lang.compile('see:imp')['text'].strip('.')
    compare=lang.compile('compare:imp')['text'].strip('.')
    narrower=lang.compile('small:m part of meaning')['text'].strip('.')
    counts=Counter(f['kind'] for f in families)
    write_json(work/'sense-groups.json',[dict(number=k,title=f['title'],kind=f['kind'],home=f['members'][0][0],
        members=[dict(word=i,sense=r['id']) for i,r in f['members']]) for k,f in enumerate(families,1)])
    write_json(work/'selection.json',dict(groups=len(families),headwords=len(heads),
        examples=sum(len(f['members']) for f in families),byEvidence=counts))
    batch=[]
    for i in heads:
        head=nodes[i]['form'];roman=nodes[i]['roman'];section='letter-'+str(ord(filing_initial(head)))
        rows=[];printed=[];refs=[]
        def row(key,kind,text,gloss,en):
            rows.append(part(key,section,roman,text,gloss,en))
            printed.append(print_part(key,head,kind,text))
        for k in by_member[i]:
            f=families[k-1];home=f['members'][0][0]
            if home!=i:
                refs.append((k,home));continue
            marker=narrower if f['kind']=='more specific alternatives' else compare
            label=f['native'].strip('. ')
            title=(head+': ' if not rows else '')+marker+' '+digit(k)+'. '+label+'.'
            row(f'h{i}g{k}','definition',title,'Compare. '+str(k)+'. '+f['title']+'.',f['title']+' ('+f['kind']+'). Group '+str(k)+'.')
            for j,r in f['members']:
                term=nodes[j];key=f'g{k}m{j}';d=term['form']+': '+r['definition'].rstrip('. ')+'.'
                en=r['meaning'].partition(' Allusion to ')[0]
                if r.get('construction'):
                    rows.append(part(key,section,roman,d+' '+r['example'],r['construction'],en+' Example: '+r['exampleEnglish']))
                    printed.extend([print_part(key,head,'definition',d),print_part(key+'x',head,'example',r['example'])])
                else:
                    row(key,'definition',d,r['gloss'],term['roman']+' · '+en)
                    row(key+'x','example',r['example'],r['exampleGloss'],r['exampleEnglish'])
        for offset in range(0,len(refs),3):
            targets=refs[offset:offset+3]
            native=', '.join(nodes[h]['form']+' ('+digit(locator[h])+', '+digit(k)+')' for k,h in targets)
            trans=', '.join(nodes[h]['roman']+' (volume '+str(locator[h])+', group '+str(k)+')' for k,h in targets)
            row(f'h{i}see{offset}','references',(head+': ' if not rows else '')+lookup+' '+native+'.','See '+trans+'.',
                roman+' · See '+trans+'.')
        assert rows
        batch.append((i,rows,printed))
        if len(batch)==1600:
            yield batch
            batch=[]
    if batch:yield batch
