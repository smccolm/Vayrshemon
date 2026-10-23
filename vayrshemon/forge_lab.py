"""Bounded declarative language laboratory. No executable user code or regexes.

The compiler enumerates finite affix paradigms, preserving source slots. Clause
tests consume author-supplied, exhaustive scalar spans: they are not a general
parser. Acceptance of a declared construction does not certify its meaning.
"""
from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
import uuid
from .forge import NAME, digest, encoded
from .authoring import stamp

ENGINE='1.0.0'
SEPARATORS=' \t\r\n.,;:!?—–-()“”"'


def empty_lab(): return dict(formatVersion='1.0.0',rules=[],cases=[])


def require(condition,code):
    if not condition: raise ValueError('LAB_'+code)


def string(value,limit=10000,empty=False):
    return isinstance(value,str) and (empty or bool(value)) and len(value)<=limit


def validate_lab(snapshot):
    lab=snapshot['laboratory'];data=snapshot['language']
    require(isinstance(lab,dict) and set(lab)=={'formatVersion','rules','cases'} and lab['formatVersion']=='1.0.0','FORMAT')
    for kind in ('rules','cases'):
        rows=lab[kind];require(isinstance(rows,list) and len(rows)<=1000,'LIMIT')
        ids=[]
        for r in rows:
            require(isinstance(r,dict) and isinstance(r.get('id'),str) and NAME.fullmatch(r['id']) and string(r.get('title'),200),'IDENTITY')
            ids.append(r['id'])
        require(len(ids)==len(set(ids)),'DUPLICATE_ID')
    grammar={r['id'] for r in data['grammar']};lexicon={r['id'] for r in data['lexicon']};orthographies={r['id'] for r in data['orthographies']}
    resolved_lexemes={r['id'] for r in data['lexicon'] if r['headword']}
    for r in lab['rules']:
        require(set(r)=={'id','title','grammarId','kind','config'} and r['grammarId'] in grammar,'RULE_FIELDS')
        c=r['config'];require(isinstance(c,dict),'CONFIG')
        if r['kind']=='inventory':
            require(set(c)=={'orthographyId','extraCharacters'} and c['orthographyId'] in orthographies and string(c['extraCharacters'],200,True),'INVENTORY')
        elif r['kind']=='forms':
            require(set(c)=={'entryIds','prefixes','slots'} and isinstance(c['entryIds'],list) and 0<len(c['entryIds'])<=2000 and set(c['entryIds'])<=lexicon,'LEXEME_REFERENCE')
            require(set(c['entryIds'])<=resolved_lexemes,'UNRESOLVED_HEADWORD')
            require(isinstance(c['prefixes'],list) and 0<len(c['prefixes'])<=16 and all(string(p,100,True) for p in c['prefixes']),'PREFIXES')
            require(isinstance(c['slots'],list) and len(c['slots'])<=6,'SLOTS')
            features=[];size=len(c['entryIds'])*len(c['prefixes'])
            for slot in c['slots']:
                require(isinstance(slot,dict) and set(slot)=={'feature','values'} and string(slot['feature'],80),'SLOT')
                values=slot['values'];require(isinstance(values,dict) and 0<len(values)<=32 and all(string(k,80) and string(v,100,True) for k,v in values.items()),'VALUES')
                features.append(slot['feature']);size*=len(values)
            require(len(features)==len(set(features)) and size<=50000,'COMPILE_LIMIT')
        elif r['kind']=='order':
            require({'patterns'}<=set(c)<={'patterns','roleFeatures','roleEntries'} and isinstance(c['patterns'],list) and 0<len(c['patterns'])<=32,'ORDER')
            require(all(isinstance(p,list) and 0<len(p)<=32 and all(string(role,40) for role in p) for p in c['patterns']),'PATTERNS')
            require(isinstance(c.get('roleEntries',{}),dict) and isinstance(c.get('roleFeatures',{}),dict),'ROLE_CONSTRAINTS')
            for role,entries in c.get('roleEntries',{}).items():
                require(string(role,40) and isinstance(entries,list) and 0<len(entries)<=2000 and set(entries)<=lexicon,'ROLE_ENTRIES')
            for role,options in c.get('roleFeatures',{}).items():
                require(string(role,40) and isinstance(options,list) and 0<len(options)<=32 and all(isinstance(f,dict) and len(f)<=6 and all(string(k,80) and string(v,80) for k,v in f.items()) for f in options),'ROLE_FEATURES')
        elif r['kind']=='analysis':
            form_ids={f['id'] for f in lab['rules'] if f['kind']=='forms'}
            require(set(c)=={'formRuleIds'} and isinstance(c['formRuleIds'],list) and 0<len(c['formRuleIds'])<=32 and set(c['formRuleIds'])<=form_ids,'FORM_REFERENCE')
        elif r['kind']=='review': require(set(c)=={'reason'} and string(c['reason']),'REVIEW_REASON')
        else: raise ValueError('LAB_UNSUPPORTED_RULE_KIND')
    rules={r['id'] for r in lab['rules']}
    for case in lab['cases']:
        require(set(case)=={'id','title','kind','text','ruleIds','expected','tokens','note'},'CASE_FIELDS')
        require(case['kind'] in ('word','clause','review') and string(case['text']) and string(case['note'],10000,True),'CASE_CONTENT')
        require(case['expected'] in ('accept','reject','review','unsupported'),'EXPECTATION')
        require(isinstance(case['ruleIds'],list) and 0<len(case['ruleIds'])<=32 and len(set(case['ruleIds']))==len(case['ruleIds']) and set(case['ruleIds'])<=rules,'RULE_REFERENCE')
        require(isinstance(case['tokens'],list) and len(case['tokens'])<=256,'TOKENS')
        previous=0
        for t in case['tokens']:
            require(isinstance(t,dict) and set(t)=={'start','end','role','entryId','features'},'TOKEN_FIELDS')
            require(type(t['start']) is int and type(t['end']) is int and previous<=t['start']<t['end']<=len(case['text']),'TOKEN_SPAN')
            require(string(t['role'],40) and t['entryId'] in lexicon and isinstance(t['features'],dict) and len(t['features'])<=6 and all(string(k,80) and string(v,80) for k,v in t['features'].items()),'TOKEN_ANALYSIS')
            previous=t['end']
        require(case['kind']=='clause' or not case['tokens'],'TOKEN_SCOPE')
    # Bound aggregate output and compilation, not just each individual rule.
    require(len(encoded(lab))<=4*1024*1024,'SIZE_LIMIT')
    compile_rules(snapshot)


def compile_rules(snapshot):
    data=snapshot['language'];lexicon={r['id']:r for r in data['lexicon']};orth={r['id']:r for r in data['orthographies']}
    compiled={};total=0
    for r in snapshot.get('laboratory',empty_lab())['rules']:
        item=deepcopy(r);c=r['config']
        if r['kind']=='inventory':
            item['characters']=set(c['extraCharacters'])|{chr(f['scalar']) for s in orth[c['orthographyId']]['symbols'] for f in s['forms']}
        elif r['kind']=='forms':
            surfaces={}
            for entry,prefix,choices in product(c['entryIds'],c['prefixes'],product(*(tuple(s['values'].items()) for s in c['slots']))):
                total+=1;require(total<=100000,'COMPILE_TOTAL_LIMIT')
                surface=prefix+lexicon[entry]['headword']+''.join(v for k,v in choices)
                require(len(surface)<=10000,'SURFACE_LIMIT')
                analysis=dict(entryId=entry,prefix=prefix,features={s['feature']:k for s,(k,v) in zip(c['slots'],choices)})
                surfaces.setdefault(surface,[]).append(analysis)
                require(len(surfaces[surface])<=128,'AMBIGUITY_LIMIT')
            item['surfaces']=surfaces
        compiled[r['id']]=item
    for item in compiled.values():
        if item['kind']=='analysis':
            surfaces={}
            for rid in item['config']['formRuleIds']:
                for form,analyses in compiled[rid]['surfaces'].items():
                    total+=len(analyses);require(total<=200000,'ANALYSIS_TOTAL_LIMIT')
                    surfaces.setdefault(form,[]).extend(analyses);require(len(surfaces[form])<=128,'AMBIGUITY_LIMIT')
            item['surfaces']=surfaces
    return compiled


def check_case(case,compiled):
    checks=[];text=case['text'];tokens=case['tokens']
    for rid in case['ruleIds']:
        rule=compiled.get(rid);detail={};outcome='accept'
        if rule is None: outcome='unsupported';detail['reason']='Rule absent in this language version.'
        elif rule['kind']=='inventory':
            unknown=[dict(offset=i,scalar=f'U+{ord(c):04X}') for i,c in enumerate(text) if c not in rule['characters']]
            if unknown: outcome='reject'
            detail.update(unknownScalars=unknown[:256],unknownCount=len(unknown),truncated=len(unknown)>256)
        elif rule['kind'] in ('forms','analysis'):
            if case['kind']=='word':
                detail['analyses']=rule['surfaces'].get(text,[])
                if not detail['analyses']: outcome='reject'
            elif case['kind']=='clause':
                # Every non-separator scalar must be consumed, not just convenient
                # recognized fragments. Unknown words therefore cannot disappear.
                covered=set(i for t in tokens for i in range(t['start'],t['end']))
                uncovered=[i for i,c in enumerate(text) if i not in covered and c not in SEPARATORS]
                invalid=[];analyses=[]
                for t in tokens:
                    surface=text[t['start']:t['end']];options=rule['surfaces'].get(surface,[])
                    matches=[a for a in options if a['entryId']==t['entryId'] and a['features']==t['features']]
                    analyses.append(dict(surface=surface,start=t['start'],end=t['end'],matches=matches))
                    if not matches: invalid.append(t['start'])
                if not tokens or uncovered or invalid: outcome='reject'
                detail.update(uncoveredOffsets=uncovered[:256],uncoveredCount=len(uncovered),invalidTokenOffsets=invalid,analyses=analyses)
            else: outcome='unsupported';detail['reason']='Supply a word or exhaustively annotated clause.'
        elif rule['kind']=='order':
            if case['kind']!='clause' or not tokens: outcome='unsupported';detail['reason']='Clause role annotations required.'
            else:
                roles=[t['role'] for t in tokens];detail['roles']=roles;detail['allowed']=rule['config']['patterns']
                if roles not in detail['allowed']: outcome='reject'
                violations=[]
                for t in tokens:
                    entries=rule['config'].get('roleEntries',{}).get(t['role'])
                    features=rule['config'].get('roleFeatures',{}).get(t['role'])
                    if (entries is not None and t['entryId'] not in entries) or (features is not None and t['features'] not in features): violations.append(t['start'])
                detail['roleConstraintViolations']=violations
                if violations: outcome='reject'
        else: outcome='review';detail['reason']=rule['config']['reason']
        checks.append(dict(ruleId=rid,outcome=outcome,detail=detail))
    outcomes={c['outcome'] for c in checks}
    actual=next((o for o in ('reject','unsupported','review') if o in outcomes),'accept')
    met=actual==case['expected']
    status=('Needs review' if actual=='review' else 'Unsupported' if actual=='unsupported' else 'Pass') if met else 'Fail'
    return dict(caseId=case['id'],title=case['title'],caseSha256=digest(case),expected=case['expected'],actual=actual,expectationMet=met,status=status,checks=checks,note=case['note'])


def evaluate(snapshot,cases=None):
    compiled=compile_rules(snapshot);lab=snapshot.get('laboratory',empty_lab());selected=lab['cases'] if cases is None else cases
    results=[];size=0;coverage=[]
    for c in selected:
        result=check_case(c,compiled);size+=len(encoded(result));require(size<=8*1024*1024,'RESULT_LIMIT');results.append(result)
    for rid,rule in compiled.items():
        matching=[r for r in results if rid in [c['ruleId'] for c in r['checks']]]
        # Only successful positive/negative assertions establish coverage. Review
        # acknowledgements and expected Unsupported never count as tested grammar.
        passing=[r for r in matching if r['status']=='Pass']
        coverage.append(dict(ruleId=rid,grammarId=rule['grammarId'],kind=rule['kind'],cases=len(matching),passed=len(passing),positive=sum(r['expected']=='accept' for r in passing),negative=sum(r['expected']=='reject' for r in passing),covered=bool(passing),bidirectional=all(any(r['expected']==o for r in passing) for o in ('accept','reject'))))
    counts=dict(Counter(r['status'] for r in results));status='Fail' if counts.get('Fail') else 'Needs review' if counts.get('Needs review') else 'Unsupported' if counts.get('Unsupported') or not results else 'Pass'
    grammar={r['id'] for r in snapshot['language']['grammar']};implemented={r['grammarId'] for r in lab['rules'] if r['kind']!='review'}
    return dict(engineVersion=ENGINE,status=status,snapshotSha256=digest(snapshot),suiteSha256=digest(selected),caseCount=len(results),counts=counts,results=results,coverage=coverage,
                unimplementedGrammar=sorted(grammar-implemented),scope='Finite forms and annotated clause constraints. No free-prose parser, semantic equivalence, phonology inference or automatic English translation.')


def compare(project,before,after,case_version=None):
    case_version=case_version or before
    cases=project.read(case_version)['snapshot'].get('laboratory',empty_lab())['cases']
    a=evaluate(project.read(before)['snapshot'],cases);b=evaluate(project.read(after)['snapshot'],cases)
    rows=[]
    for x,y in zip(a['results'],b['results']):
        rows.append(dict(caseId=x['caseId'],caseSha256=x['caseSha256'],before=x['actual'],after=y['actual'],beforeStatus=x['status'],afterStatus=y['status'],changed=x['actual']!=y['actual'],regression=x['expectationMet'] and not y['expectationMet'],improvement=not x['expectationMet'] and y['expectationMet']))
    return dict(beforeVersion=before,afterVersion=after,caseVersion=case_version,suiteSha256=digest(cases),cases=rows,before=a,after=b)


def run(project,version,directory):
    from tools.m0.common import write_json
    out=Path(directory)
    if out.exists(): raise ValueError('LAB_RUN_DIRECTORY_EXISTS')
    snapshot=project.read(version)['snapshot'];report=evaluate(snapshot);out.mkdir(parents=True)
    report.update(runId=uuid.uuid4().hex,version=version,projectId=project.status()['projectId'],testId='language-suite',createdAt=stamp(),kind='language-suite',document=None,manifestPath=str(out/'run.json'))
    write_json(out/'run.json',report);project.record_run(report);return report
