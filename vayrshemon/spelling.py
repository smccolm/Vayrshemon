"""Explicit, versioned Maxima spelling using paired script identities.

Never Unicode upper/casefold, glyph scaling, automatic typing or English edits.
"""
from copy import deepcopy
from collections import Counter
from pathlib import Path
import uuid
from .forge import digest,encoded,validate as validate_snapshot
from .authoring import stamp


def require(ok,code):
    if not ok:raise ValueError('SPELLING_'+code)


def validate(snapshot):
    p=snapshot['spelling']
    require(isinstance(p,dict) and set(p)=={'formatVersion','orthographyId','grammarId','formRuleIds','terminalCharacters','openingCharacters','initialForm'},'FIELDS')
    require(p['formatVersion']=='1.0.0' and p['initialForm']=='maxima','VERSION')
    require(p['grammarId'] in {r['id'] for r in snapshot['language']['grammar']},'GRAMMAR_REFERENCE')
    require('laboratory' in snapshot,'LAB_REQUIRED')
    ids={r['id'] for r in snapshot['laboratory']['rules'] if r['kind']=='forms'}
    require(isinstance(p['formRuleIds'],list) and 0<len(p['formRuleIds'])<=32 and all(isinstance(x,str) for x in p['formRuleIds']) and len(set(p['formRuleIds']))==len(p['formRuleIds']) and set(p['formRuleIds'])<=ids,'FORM_REFERENCE')
    for key,minimum in [('terminalCharacters',1),('openingCharacters',0)]:
        require(isinstance(p[key],str) and minimum<=len(p[key])<=32 and len(set(p[key]))==len(p[key]),'BOUNDARIES')
    require(not set(p['terminalCharacters'])&set(p['openingCharacters']),'BOUNDARIES_OVERLAP')
    pairs(snapshot)


def pairs(snapshot):
    p=snapshot['spelling'];orth=next((r for r in snapshot['language']['orthographies'] if r['id']==p['orthographyId']),None)
    require(orth is not None,'ORTHOGRAPHY_REFERENCE');result={};used=set()
    for symbol in orth['symbols']:
        if symbol['kind']!='letter':continue
        forms={f['form']:f['scalar'] for f in symbol['forms']}
        require(len(forms)==len(symbol['forms']) and 'maxima' in forms and 'minima' in forms,'PAIR_REQUIRED')
        hi,lo=forms['maxima'],forms['minima'];require(hi!=lo and not {hi,lo}&used,'AMBIGUOUS_PAIR');used.update((hi,lo))
        result[chr(lo)]=dict(maxima=chr(hi),symbolId=symbol['id'],name=symbol['name'])
    require(0<len(result)<=512,'PAIR_LIMIT');return result


def initial_positions(text,policy):
    pending=True;positions=[]
    for i,c in enumerate(text):
        if c in policy['terminalCharacters']:pending=True
        elif pending and not (c.isspace() or c in policy['openingCharacters']):positions.append(i);pending=False
    return positions


def inspect_text(text,policy,mapping):
    highs={r['maxima']:dict(minima=lo,**r) for lo,r in mapping.items()};changes=[];initials=[];unmapped=[]
    for i in initial_positions(text,policy):
        c=text[i]
        if c in mapping:
            row=mapping[c];changes.append(dict(offset=i,before=c,after=row['maxima'],symbolId=row['symbolId'],name=row['name']));initials.append(dict(offset=i,form='minima',symbolId=row['symbolId']))
        elif c in highs:initials.append(dict(offset=i,form='maxima',symbolId=highs[c]['symbolId']))
        else:unmapped.append(dict(offset=i,scalar=f'U+{ord(c):04X}'))
    result=list(text)
    for c in changes:result[c['offset']]=c['after']
    return dict(text=''.join(result),changes=changes,initials=initials,unmappedInitials=unmapped,counts=dict(maxima=sum(c in highs for c in text),minima=sum(c in mapping for c in text)),status='Fail' if changes else 'Needs review' if unmapped else 'Pass')


def expand(snapshot,compiled,total):
    if 'spelling' not in snapshot:return total
    policy=snapshot['spelling'];mapping=pairs(snapshot)
    for rid in policy['formRuleIds']:
        item=compiled[rid]
        for surface,analyses in list(item['surfaces'].items()):
            if not surface or surface[0] not in mapping:continue
            new=mapping[surface[0]]['maxima']+surface[1:]
            for a in list(analyses):
                total+=1;require(total<=100000,'COMPILE_LIMIT')
                target=item['surfaces'].setdefault(new,[]);target.append(dict(a,requiredPosition='sentence-initial',spelling=dict(baseSurface=surface,sourceScalar=ord(surface[0]),displayScalar=ord(new[0]),symbolId=mapping[surface[0]]['symbolId'])))
                require(len(target)<=128,'AMBIGUITY_LIMIT')
    for item in compiled.values():
        if item['kind'] in ('forms','analysis','letterforms'):item['spellingPolicy']=policy
        if item['kind']=='letterforms':item['letterPairs']=mapping
    return total


def audit(snapshot,test_id):
    require('spelling' in snapshot,'POLICY_REQUIRED');test=next((r for r in snapshot['tests'] if r['id']==test_id),None);require(test is not None,'PAGE_MISSING')
    mapping=pairs(snapshot);rows=[dict(paragraph=i,**inspect_text(p['text'],snapshot['spelling'],mapping)) for i,p in enumerate(test['paragraphs'])]
    # Text already lives in the page; evidence records exact hashes and changes.
    for row in rows:row.pop('text')
    return dict(engineVersion='1.0.0',testId=test_id,snapshotSha256=digest(snapshot),testSha256=digest(test),policySha256=digest(snapshot['spelling']),pairSha256=digest(mapping),paragraphs=rows,initialCount=sum(len(r['initials']) for r in rows),maximaInitialCount=sum(sum(i['form']=='maxima' for i in r['initials']) for r in rows),maximaCount=sum(r['counts']['maxima'] for r in rows),missingCount=sum(len(r['changes']) for r in rows),unmappedCount=sum(len(r['unmappedInitials']) for r in rows),status='Fail' if any(r['changes'] for r in rows) else 'Needs review' if any(r['unmappedInitials'] for r in rows) else 'Pass',scope='Mapped sentence initials only. Interior spelling is preserved. Line wrapping does not create a sentence. Abbreviations, names and sentence interpretation require editorial review.')


def preview(project,test_id,version=None):
    value=project.read(version);snapshot=value['snapshot'];report=audit(snapshot,test_id)
    body=dict(projectId=value['projectId'],generation=value['generation'],version=version,testId=test_id,snapshotSha256=digest(snapshot),audit=report)
    return dict(planId=digest(body),**body)


def apply(project,test_id,plan_id,expected_generation):
    plan=preview(project,test_id);require(plan['generation']==expected_generation,'STALE_GENERATION');require(plan['planId']==plan_id,'STALE_PLAN');require(plan['audit']['missingCount']>0,'NO_CHANGES');require(plan['audit']['unmappedCount']==0,'UNMAPPED_INITIAL')
    s=project.read()['snapshot'];test=next(t for t in s['tests'] if t['id']==test_id);require(bool(test.get('caseIds')),'BOUND_CASES_REQUIRED');cases={c['id']:c for c in s['laboratory']['cases']};policy=s['spelling'];mapping=pairs(s)
    rule_id='spelling.initial-maxima';rule=dict(id=rule_id,title='Sentence-initial Maxima',kind='letterforms',grammarId=policy['grammarId'],config={})
    existing=next((r for r in s['laboratory']['rules'] if r['id']==rule_id),None);require(existing is None or existing==rule,'RULE_ID_CONFLICT')
    if existing is None:s['laboratory']['rules'].append(rule)
    added=[]
    for group,paragraph in zip(test['caseIds'],test['paragraphs']):
        for i,cid in enumerate(group):
            c=deepcopy(cases[cid]);proof=inspect_text(c['text'],policy,mapping);require(not proof['unmappedInitials'],'UNMAPPED_INITIAL')
            if i and cases[group[i-1]]['text'].rstrip(' '+policy['openingCharacters'])[-1:] not in policy['terminalCharacters']:raise ValueError('SPELLING_SENTENCE_BOUNDARY_REQUIRED')
            key='spelling.'+digest(dict(case=c,policy=policy))[:24];c.update(id=key,title='Maxima · '+c['title'][:190],text=proof['text']);c['ruleIds']=list(dict.fromkeys(c['ruleIds']+[rule_id]));c['note']+=' Explicit Maxima review; prior source case retained.'
            # One mapped scalar replaces one scalar; annotation offsets are exact.
            if key not in cases:cases[key]=c;s['laboratory']['cases'].append(c);added.append(key)
            else:require(cases[key]==c,'CASE_ID_CONFLICT')
            group[i]=key
        paragraph['text']=' '.join(cases[cid]['text'] for cid in group)
    validate_snapshot(s);result=project.replace_draft(s,expected_generation)
    return dict(**result,addedCaseIds=added,audit=audit(s,test_id))


def run(project,version,test_id,directory):
    from tools.m0.common import write_json
    out=Path(directory);require(not out.exists(),'RUN_DIRECTORY_EXISTS');report=audit(project.read(version)['snapshot'],test_id);out.mkdir(parents=True)
    report.update(runId=uuid.uuid4().hex,version=version,projectId=project.status()['projectId'],createdAt=stamp(),kind='spelling-audit',document=None,manifestPath=str(out/'run.json'));write_json(out/'run.json',report);project.record_run(report);return report


def identity_text(snapshot,text):
    """Fold explicit script pairs for analytics only; never change stored text."""
    if 'spelling' not in snapshot:return text
    reverse={r['maxima']:lo for lo,r in pairs(snapshot).items()}
    return ''.join(reverse.get(c,c) for c in text)
