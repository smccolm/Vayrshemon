"""Version-pinned construction glosses from exhaustively annotated clauses.

English labels are editorial data, never inferred translations or a prose parser.
Original scalar/case sequences and explicit dictionary/grammar references survive.
"""
from .forge import digest
from .session import utf16_length

KEY='constructionGloss'
ENGINE='1.0.0'
TAGS={'sg.':'singular','du.':'dual','pl.':'plural','prs.':'present','pst.':'past','fut.':'future',
      'pst.d.':'distant past','pst.i.':'immediate past','fut.d.':'distant future','fut.i.':'immediate future',
      'simp.':'simple aspect','prog.':'progressive aspect','perf.':'perfect aspect','nom.':'nominative',
      'acc.':'accusative','cnt.':'count-noun modifier','n.':'verb-to-noun conversion','th.':'thing class'}
FEATURES={'number':{'singular':'sg.','dual':'du.','plural':'pl.'},'case':{'nominative':'nom.','accusative':'acc.'},
          'tense':{'present':'prs.','past':'pst.','future':'fut.','distantPast':'pst.d.','immediatePast':'pst.i.','distantFuture':'fut.d.','immediateFuture':'fut.i.'},
          'aspect':{'simple':'simp.','progressive':'prog.','perfect':'perf.'},'class':{'count':'cnt.'}}


def require(ok,code):
    if not ok:raise ValueError('GLOSS_'+code)


def profile(snapshot):
    p=snapshot['research'].get(KEY)
    require(isinstance(p,dict),'PROFILE_REQUIRED')
    require(set(p)=={'formatVersion','showSimpleAspect','entries','prefixes'} and p['formatVersion']==ENGINE,'PROFILE_VERSION')
    require(type(p['showSimpleAspect']) is bool,'ASPECT_OPTION')
    lex={e['id']:e for e in snapshot['language']['lexicon']}
    require(isinstance(p['entries'],dict) and len(p['entries'])<=2000 and isinstance(p['prefixes'],dict) and len(p['prefixes'])<=64,'PROFILE_LIMIT')
    for eid,row in p['entries'].items():
        require(eid in lex and isinstance(row,dict) and set(row)=={'senseId','entrySha256','label','tags','note'},'ENTRY_FIELDS')
        require(row['senseId'] in {s['id'] for s in lex[eid]['senses']},'SENSE_REFERENCE')
        require(row['entrySha256']==digest(lex[eid]),'STALE_DICTIONARY_LABEL: '+eid)
        require(isinstance(row['label'],str) and 0<len(row['label'])<=80 and not any(c in row['label'] for c in '\r\n()·'),'LABEL')
        require(isinstance(row['note'],str) and len(row['note'])<=10000,'NOTE')
        require(isinstance(row['tags'],list) and len(row['tags'])<=8 and all(t in TAGS for t in row['tags']),'TAGS')
    for prefix,row in p['prefixes'].items():
        require(isinstance(prefix,str) and len(prefix)<=100 and isinstance(row,dict) and set(row)=={'tags','note'},'PREFIX_FIELDS')
        require(isinstance(row['tags'],list) and len(row['tags'])<=8 and all(t in TAGS for t in row['tags']) and isinstance(row['note'],str) and len(row['note'])<=10000,'PREFIX_TAGS')
    return p


def inspect(snapshot,test_id):
    from .forge import validate
    from .forge_lab import compile_rules,check_case
    from .variation import allowed
    from .spelling import initial_positions
    validate(snapshot);p=profile(snapshot)
    test=next((t for t in snapshot['tests'] if t['id']==test_id),None)
    require(test is not None and bool(test.get('caseIds')),'BOUND_TEST_REQUIRED')
    compiled=compile_rules(snapshot);cases={c['id']:c for c in snapshot['laboratory']['cases']};lex={e['id']:e for e in snapshot['language']['lexicon']}
    paragraphs=[];issues=[];used=set();count=0
    for index,(source,ids) in enumerate(zip(test['paragraphs'],test['caseIds'])):
        clauses=[];position=0
        for cid in ids:
            c=cases[cid];check=check_case(c,compiled)
            require(check['actual']=='accept','CASE_REJECTED: '+cid)
            require(any(x['kind']=='analysis' and x['id'] in c['ruleIds'] for x in compiled.values()),'EXHAUSTIVE_ANALYSIS_REQUIRED')
            tokens=[]
            for t in c['tokens']:
                eid=t['entryId'];require(eid in p['entries'],'LABEL_MISSING: '+eid);label=p['entries'][eid];surface=c['text'][t['start']:t['end']]
                context={**c.get('context',{}),**t.get('context',{}),'role':t['role']}
                if 'spelling' in snapshot:context['position']='sentence-initial' if t['start'] in initial_positions(c['text'],snapshot['spelling']) else 'internal'
                analyses=[]
                for rule in compiled.values():
                    if rule['kind']!='forms':continue
                    for a in rule['surfaces'].get(surface,[]):
                        if a['entryId']==eid and a['features']==t['features'] and allowed(a,context):analyses.append(dict(formRuleId=rule['id'],grammarId=rule['grammarId'],**a))
                require(bool(analyses),'ANALYSIS_MISSING')
                prefixes={a['prefix'] for a in analyses};require(len(prefixes)==1,'AMBIGUOUS_PREFIX')
                prefix=next(iter(prefixes));require(not prefix or prefix in p['prefixes'],'PREFIX_LABEL_MISSING')
                tags=list(label['tags'])+p['prefixes'].get(prefix,{}).get('tags',[])
                for field,values in FEATURES.items():
                    if field in t['features']:
                        value=t['features'][field];require(value in values,'FEATURE_UNSUPPORTED: '+field+'='+value)
                        if field=='aspect' and value=='simple' and not p['showSimpleAspect']:continue
                        tags.append(values[value])
                require(set(t['features'])<=FEATURES.keys(),'FEATURE_UNSUPPORTED')
                tags=list(dict.fromkeys(tags));used.update(tags)
                english_label=label['label']
                if not tokens:english_label=english_label[:1].upper()+english_label[1:]
                text=english_label+('('+','.join(tags)+')' if tags else '')
                start=position+t['start'];end=position+t['end']
                tokens.append(dict(surface=surface,gloss=text,entryId=eid,senseId=label['senseId'],entrySha256=digest(lex[eid]),features=t['features'],role=t['role'],
                    sourceScalar=[start,end],sourceUtf16=[utf16_length(source['text'][:start]),utf16_length(source['text'][:end])],
                    analyses=analyses,context=context,definition=next(s['definition'] for s in lex[eid]['senses'] if s['id']==label['senseId']),
                    etymology=lex[eid]['etymology'],note=label['note'],prefixNote=p['prefixes'].get(prefix,{}).get('note','')))
            require(len(tokens)>0,'EMPTY_CLAUSE');count+=len(tokens);require(count<=10000,'TOKEN_LIMIT')
            # Terminal marks belong to the source clause, not English syntax.
            ending=c['text'][c['tokens'][-1]['end']:]
            require(all(ch.isspace() or ch in '.!?;:' for ch in ending),'ENDING_UNSUPPORTED')
            if c.get('antecedent'):issues.append(dict(caseId=cid,code='IMPLICIT_SUBJECT',antecedent=c['antecedent']))
            clauses.append(dict(caseId=cid,caseSha256=digest(c),source=c['text'],tokens=tokens,text=' · '.join(t['gloss'] for t in tokens)+ending.strip(),note=c['note']))
            position+=len(c['text'])+1
        paragraphs.append(dict(index=index,source=source['text'],sourceSha256=digest(source['text']),english=source['translation'],adaptation=source['analysis'],clauses=clauses,text=' '.join(c['text'] for c in clauses)))
    return dict(engineVersion=ENGINE,profileSha256=digest(p),snapshotSha256=digest(snapshot),testId=test_id,testSha256=digest(test),
        paragraphs=paragraphs,tokenCount=count,legend={k:TAGS[k] for k in TAGS if k in used},showSimpleAspect=p['showSimpleAspect'],issues=issues,
        status='Needs review',scope='Exact annotated source order. Editorial English labels and proposed language rules require author review; no automatic translation, segmentation or grammar acceptance.')


def prepare(snapshot,test_id):
    """Editable suggestions only; no guessed pronoun features or morpheme splits."""
    test=next((t for t in snapshot['tests'] if t['id']==test_id),None);require(test is not None and test.get('caseIds'),'BOUND_TEST_REQUIRED')
    ids={i for group in test['caseIds'] for i in group};used={t['entryId'] for c in snapshot['laboratory']['cases'] if c['id'] in ids for t in c['tokens']}
    entries={}
    for e in snapshot['language']['lexicon']:
        if e['id'] not in used:continue
        sense=e['senses'][0];label=sense['definition'].splitlines()[0].split('(')[0].strip()[:80] or e['label'][:80]
        entries[e['id']]=dict(senseId=sense['id'],entrySha256=digest(e),label=label,tags=[],note='Suggested from the dictionary; edit the compact label and inherent tags before committing.')
    from .forge_lab import compile_rules
    prefixes={a['prefix']:dict(tags=[],note='Review this explicit form prefix in the pinned grammar.') for r in compile_rules(snapshot).values() if r['kind']=='forms' for aa in r['surfaces'].values() for a in aa if a['entryId'] in used and a['prefix']}
    return dict(formatVersion=ENGINE,showSimpleAspect=True,entries=entries,prefixes=prefixes)
