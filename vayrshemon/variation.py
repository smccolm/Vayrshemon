"""Context-conditioned alternatives and advisory repetition inspection.

No random rewriting, universal diversity score, inferred discourse or casefolding.
Full forms remain available. Conditions constrain additional forms, not speakers.
"""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import re
import uuid
from .forge import NAME,digest,encoded
from .authoring import stamp

CONTEXT={
 'register':('citation','formal','literary','conversational'),
 'givenness':('new','established'),
 'focus':('neutral','contrast'),
 'coordination':('independent','first','continuation'),
 'role':('subject','predicate','object','modifier','verb','adverb','adjunct'),
}
EXTENDED_CONTEXT={'topic':('none','subject'),'position':('sentence-initial','internal')}


def modern(snapshot):return snapshot.get('variation',{}).get('formatVersion')=='1.1.0' or 'spelling' in snapshot


def empty(): return dict(formatVersion='1.0.0',alternations=[],watch=[])


def require(condition,code):
    if not condition: raise ValueError('VARIATION_'+code)


def valid_context(context,extended=False):
    fields={**CONTEXT,**EXTENDED_CONTEXT} if extended else CONTEXT
    require(isinstance(context,dict) and set(context)<=fields.keys(),'CONTEXT_FIELDS')
    require(all(v in fields[k] for k,v in context.items()),'CONTEXT_VALUE')


def validate_when(snapshot,when):
    fields={**CONTEXT,**EXTENDED_CONTEXT} if modern(snapshot) else CONTEXT
    require(isinstance(when,dict) and when and set(when)<=fields.keys() and 'register' in when,'CONDITIONS')
    for k,values in when.items():require(isinstance(values,list) and 0<len(values)<=len(fields[k]) and all(isinstance(v,str) for v in values) and len(values)==len(set(values)) and all(v in fields[k] for v in values),'CONDITION_VALUES')


def validate(snapshot):
    value=snapshot['variation']
    require(isinstance(value,dict) and set(value)=={'formatVersion','alternations','watch'} and value['formatVersion'] in ('1.0.0','1.1.0'),'FORMAT')
    require('laboratory' in snapshot,'LAB_REQUIRED')
    grammar={g['id'] for g in snapshot['language']['grammar']}
    forms={r['id']:r for r in snapshot['laboratory']['rules'] if r['kind']=='forms'}
    for collection,limit in [('alternations',64),('watch',32)]:
        rows=value[collection];require(isinstance(rows,list) and len(rows)<=limit,'LIMIT')
        ids=set()
        for r in rows:
            require(isinstance(r,dict) and isinstance(r.get('id'),str) and NAME.fullmatch(r['id']) and r['id'] not in ids,'IDENTITY');ids.add(r['id'])
            if collection=='watch':
                require(set(r)=={'id','label','text','minCount','minShare'},'WATCH_FIELDS')
                require(isinstance(r['label'],str) and 0<len(r['label'])<=200 and isinstance(r['text'],str) and 0<len(r['text'])<=100,'WATCH_TEXT')
                require(type(r['minCount']) is int and 2<=r['minCount']<=10000 and type(r['minShare']) in (int,float) and 0<=r['minShare']<=1,'WATCH_THRESHOLD')
                continue
            require(set(r)=={'id','title','grammarId','formRuleId','fromPrefix','toPrefix','when','note','status'},'ALTERNATION_FIELDS')
            require(all(isinstance(r[k],str) and 0<len(r[k])<=limit for k,limit in [('title',200),('note',10000)]),'DESCRIPTION')
            require(r['status'] in ('proposed','accepted') and r['grammarId'] in grammar and r['formRuleId'] in forms,'REFERENCE')
            require(all(isinstance(r[k],str) and len(r[k])<=100 for k in ('fromPrefix','toPrefix')) and r['fromPrefix']!=r['toPrefix'],'PREFIX')
            # Replace the exact paradigm prefix only; never a root substring.
            require(r['fromPrefix'] in forms[r['formRuleId']]['config']['prefixes'],'PREFIX_REFERENCE')
            validate_when(snapshot,r['when'])
    require(len(encoded(value))<=1024*1024,'SIZE_LIMIT')


def allowed(analysis,context):
    return (not analysis.get('requiredPosition') or context.get('position')==analysis['requiredPosition']) and all(context.get(k) in values for k,values in analysis.get('when',{}).items())


def expand(snapshot,compiled,total):
    if 'variation' not in snapshot:return total
    validate(snapshot)
    original={rid:deepcopy(r['surfaces']) for rid,r in compiled.items() if r['kind']=='forms'}
    for variant in snapshot['variation']['alternations']:
        rule=compiled[variant['formRuleId']]
        for surface,analyses in original[variant['formRuleId']].items():
            for a in analyses:
                if a['prefix']!=variant['fromPrefix']:continue
                total+=1;require(total<=100000,'COMPILE_LIMIT')
                new=variant['toPrefix']+surface[len(variant['fromPrefix']):]
                require(bool(new) and len(new)<=10000,'SURFACE_LIMIT')
                item=dict(a,prefix=variant['toPrefix'],when=deepcopy(variant['when']),variationId=variant['id'],variationStatus=variant['status'])
                target=rule['surfaces'].setdefault(new,[]);target.append(item);require(len(target)<=128,'AMBIGUITY_LIMIT')
    return total


def forms(snapshot,entry_id,features,context):
    from .forge_lab import compile_rules
    valid_context(context,modern(snapshot))
    require(entry_id in {r['id'] for r in snapshot['language']['lexicon']},'ENTRY_MISSING')
    require(isinstance(features,dict) and len(features)<=6 and all(isinstance(k,str) and isinstance(v,str) for k,v in features.items()),'FEATURES')
    rows=[]
    for rule in compile_rules(snapshot).values():
        if rule['kind']!='forms':continue
        for surface,analyses in rule['surfaces'].items():
            for a in analyses:
                if a['entryId']==entry_id and a['features']==features:
                    rows.append(dict(surface=surface,ruleId=rule['id'],allowed=allowed(a,context),analysis=a))
                    require(len(rows)<=10000,'FORMS_RESULT_LIMIT')
    require(len(encoded(rows))<=8*1024*1024,'FORMS_RESULT_LIMIT')
    return dict(entryId=entry_id,features=features,context=context,forms=rows,policy='Alternatives are available choices, never automatic substitutions. Context labels are supplied by the author.')


def audit(snapshot,test_id,watch=None,identity_snapshot=None):
    from .spelling import pairs
    identity_source=identity_snapshot or snapshot
    reverse={r['maxima']:lo for lo,r in pairs(identity_source).items()} if 'spelling' in identity_source else {}
    identity=lambda text:''.join(reverse.get(c,c) for c in text) if reverse else text
    test=next((t for t in snapshot['tests'] if t['id']==test_id),None)
    require(test is not None,'PAGE_MISSING')
    cases={c['id']:c for c in snapshot.get('laboratory',{}).get('cases',[])}
    tokens=[];clauses=[];bound=bool(test.get('caseIds'))
    if bound:
        for paragraph,ids in enumerate(test['caseIds']):
            for cid in ids:
                c=cases[cid];clause=[]
                for t in c['tokens']:
                    item=dict(caseId=cid,paragraph=paragraph,sourceStart=t['start'],sourceEnd=t['end'],surface=c['text'][t['start']:t['end']],entryId=t['entryId'],role=t['role'],context={**c.get('context',{}),**t.get('context',{}),'role':t['role']})
                    tokens.append(item);clause.append(item);require(len(tokens)<=10000,'AUDIT_TOKEN_LIMIT')
                if clause:clauses.append(clause)
    else:
        for i,pair in enumerate(test['paragraphs']):
            # Explicitly unannotated: Unicode scalars retained; apostrophes stay.
            for match in re.finditer(r'[^\s.,;:!?—–()“”"]+',pair['text']):
                tokens.append(dict(paragraph=i,sourceStart=match.start(),sourceEnd=match.end(),surface=match.group(),entryId=None,role=None,context={}));require(len(tokens)<=10000,'AUDIT_TOKEN_LIMIT')
    counts=Counter(t['surface'] for t in tokens);lexemes=Counter(t['entryId'] for t in tokens if t['entryId'])
    watches=deepcopy(watch if watch is not None else snapshot.get('variation',empty())['watch']);metrics=[];warnings=[]
    for item in watches:
        matches=[t for t in tokens if identity(t['surface']).startswith(identity(item['text']))];share=len(matches)/len(tokens) if tokens else 0
        openings=sum(identity(c[0]['surface']).startswith(identity(item['text'])) for c in clauses)
        chain=longest=0
        for t in tokens:
            chain=chain+1 if identity(t['surface']).startswith(identity(item['text'])) else 0;longest=max(longest,chain)
        metric=dict(**item,count=len(matches),tokenShare=share,clauseOpenings=openings,clauseCount=len(clauses),longestConsecutiveTokens=longest,locations=matches[:256],locationsTruncated=len(matches)>256)
        metrics.append(metric)
        if len(matches)>=item['minCount'] and share>=item['minShare']:
            warnings.append(dict(code='PREFIX_CONCENTRATION',watchId=item['id'],message=f"{item['label']}: {len(matches)}/{len(tokens)} tokens; {openings}/{len(clauses)} annotated clause openings. Review context and rhetorical intent, not just the count."))
    openings=Counter(c[0]['surface'] for c in clauses)
    report=dict(engineVersion='1.0.0',snapshotSha256=digest(snapshot),testId=test_id,testSha256=digest(test),watchSha256=digest(watches),boundToCases=bound,
                tokenCount=len(tokens),typeCount=len(counts),lexemeCount=len(lexemes),clauseCount=len(clauses),watched=metrics,warnings=warnings,
                repeatedWords=[dict(text=k,count=v) for k,v in counts.most_common(20) if v>1],repeatedLexemes=[dict(entryId=k,count=v) for k,v in lexemes.most_common(20) if v>1],
                repeatedOpenings=[dict(text=k,count=v) for k,v in openings.most_common(20) if v>1],
                contextCounts={k:dict(Counter(t['context'].get(k,'unspecified') for t in tokens)) for k in CONTEXT},
                status='Needs review' if warnings or not bound else 'Pass',scope='Advisory repetition inspection of this sample only. A low count does not certify naturalness; deliberate repetition, parallelism and morphology may be appropriate. No population frequency estimate or automatic rewriting.')
    require(len(encoded(report))<=8*1024*1024,'AUDIT_RESULT_LIMIT')
    if 'spelling' in (identity_snapshot or snapshot):
        from .spelling import pairs
        report.update(engineVersion='1.1.0',letterIdentitySha256=digest(pairs(identity_snapshot or snapshot)),countingPolicy='Watched prefixes fold only explicit Maxima/Minima pairs. Stored text and exact-word counts are unchanged.')
    return report


def compare(project,before,after,test_id):
    a=project.read(before)['snapshot'];b=project.read(after)['snapshot'];watch=b.get('variation',empty())['watch']
    aa=audit(a,test_id,watch,identity_snapshot=b);bb=audit(b,test_id,watch,identity_snapshot=b)
    return dict(beforeVersion=before,afterVersion=after,watchSha256=digest(watch),before=aa,after=bb,
                changes=[dict(id=x['id'],before=x['count'],after=y['count'],delta=y['count']-x['count']) for x,y in zip(aa['watched'],bb['watched'])],
                scope='Same watched prefixes and thresholds; each version supplies its own page text. This is a descriptive comparison, not a test regression or a naturalness score.')


def orders(snapshot,rule_id,context):
    valid_context(context,modern(snapshot));rule=next((r for r in snapshot.get('laboratory',{}).get('rules',[]) if r['id']==rule_id and r['kind']=='order'),None);require(rule is not None,'ORDER_RULE_MISSING')
    return dict(ruleId=rule_id,context=context,patterns=[dict(pattern=p,allowed=True,source='retained construction') for p in rule['config']['patterns']]+[dict(a,allowed=allowed(a,context)) for a in rule['config'].get('alternatives',[])],scope='Optional constructions with author-supplied discourse context. Role/case checks still apply; no automatic word reordering.')


def run(project,version,test_id,directory):
    from tools.m0.common import write_json
    out=Path(directory);require(not out.exists(),'RUN_DIRECTORY_EXISTS')
    report=audit(project.read(version)['snapshot'],test_id);out.mkdir(parents=True)
    report.update(runId=uuid.uuid4().hex,version=version,projectId=project.status()['projectId'],createdAt=stamp(),kind='variation-audit',document=None,manifestPath=str(out/'run.json'))
    write_json(out/'run.json',report);project.record_run(report);return report
