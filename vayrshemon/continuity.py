"""Explicit antecedents for a bounded, optional subject-ellipsis proposal."""

def validate_rule(snapshot,rule):
    from .variation import validate_when
    c=rule['config']
    if snapshot.get('variation',{}).get('formatVersion')!='1.2.0' or set(c)!={'omittedRole','when'} or c['omittedRole']!='subject':raise ValueError('CONTINUITY_RULE_INVALID')
    validate_when(snapshot,c['when'])


def check(case,rule):
    from .variation import allowed
    a=case.get('antecedent');detail=dict(antecedent=a,scope='Author-supplied participant identity; bound page requires the immediately preceding explicit subject. No discourse inference.')
    if case['kind']!='clause' or not a or not allowed(rule['config'],case.get('context',{})):return 'reject',detail
    prior=rule['antecedents'].get(a['caseId'])
    if not prior or prior.get('antecedent') or prior['expected']!='accept' or a['caseId']==case['id']:return 'reject',detail
    subjects=[t for t in prior['tokens'] if t['role']=='subject']
    valid=len(subjects)==1 and subjects[0]['entryId']==a['entryId'] and not any(t['role']=='subject' for t in case['tokens'])
    detail['participantMatches']=valid
    return ('accept' if valid else 'reject'),detail
