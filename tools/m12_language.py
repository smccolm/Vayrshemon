"""M12 retains Tempest exactly and proposes an independently tested ellipsis."""
from copy import deepcopy
from vayrshemon.archive_language import base
from vayrshemon.forge import validate
from vayrshemon import forge_lab,reading,spelling


def propose(source):
    s=deepcopy(source);s['reading']=reading.policy();s['variation']['formatVersion']='1.2.0'
    gid='m12.rule.continuity';s['language']['grammar'].append(dict(base(gid,'Optional continuous subject',None,'',status='draft'),topic='other',statement='A literary continuation may leave its immediately preceding explicit subject unspoken when the same lexical participant remains established and noncontrast. Preserve predicate, adverb scope and finite tense. Use an explicit subject at a topic change, after an interruption, for contrast or when reference is unclear. Full subject clauses remain available. This is a new proposal, not an attested rule.',morphologyIds=[],exampleIds=[],alternatives=[]))
    when=dict(register=['literary'],topic=['subject'],givenness=['established'],focus=['neutral'])
    rules=s['laboratory']['rules'];order=deepcopy(next(r for r in rules if r['id']=='m11.discourse-order'));order.update(id='m12.continuity-order',title='Full clauses and continuous subject ellipsis',grammarId=gid)
    order['config']['alternatives'].append(dict(id='implicit-subject',pattern=['predicate','adverb','verb'],when=deepcopy(when),note='Only with the separately checked explicit antecedent. Full subject remains available.'))
    rules.extend([order,dict(id='m12.continuity',title='Same immediately preceding subject',grammarId=gid,kind='continuity',config=dict(omittedRole='subject',when=deepcopy(when)))])
    cases=s['laboratory']['cases'];lookup={c['id']:c for c in cases};tempest=next(t for t in s['tests'] if t['id']=='tempest-dreams')
    actor=deepcopy(lookup[tempest['caseIds'][0][1]]);actor.update(id='m12.continuity.actors',title='Explicit actors antecedent');cases.append(actor)
    full=deepcopy(lookup[tempest['caseIds'][0][3]]);full.update(id='m12.continuity.full',title='Retained explicit subject continuation');cases.append(full)
    reduced=deepcopy(full);reduced.update(id='m12.continuity.implicit',title='Implicit actors continuation',antecedent=dict(caseId=actor['id'],entryId=next(t['entryId'] for t in actor['tokens'] if t['role']=='subject')))
    pieces=[];tokens=[];offset=0
    for t in reduced['tokens']:
        if t['role']=='subject':continue
        surface=reduced['text'][t['start']:t['end']];token=deepcopy(t);token.update(start=offset,end=offset+len(surface));pieces.append(surface);tokens.append(token);offset+=len(surface)+1
    reduced['text']=spelling.inspect_text(' '.join(pieces)+'.',s['spelling'],spelling.pairs(s))['text'];reduced['tokens']=tokens
    reduced['ruleIds']=[order['id'] if r=='m11.discourse-order' else r for r in reduced['ruleIds']]+['m12.continuity'];reduced['note']+=' M12 proposed continuous-subject reading; referent remains explicit in the preceding assertion.'
    cases.append(reduced)
    for key,value in [('register','formal'),('topic','none'),('givenness','new'),('focus','contrast')]:
        c=deepcopy(reduced);c.update(id=reduced['id']+'.'+key,title='Reject ellipsis · '+key,expected='reject');c['context'][key]=value;cases.append(c)
        c=deepcopy(reduced);c.update(id=reduced['id']+'.missing-'+key,title='Reject ellipsis without '+key,expected='reject');c['context'].pop(key,None);cases.append(c)
    c=deepcopy(reduced);c.update(id=reduced['id']+'.missing-reference',title='Reject absent antecedent',expected='reject');c.pop('antecedent');cases.append(c)
    c=deepcopy(reduced);c.update(id=reduced['id']+'.wrong-reference',title='Reject a different preceding subject',expected='reject');c['antecedent']['caseId']=tempest['caseIds'][0][0];cases.append(c)
    c=deepcopy(reduced);c.update(id=reduced['id']+'.wrong-identity',title='Reject mismatched participant identity',expected='reject');c['antecedent']['entryId']='m8.spirit';cases.append(c)
    c=deepcopy(full);c.update(id='m12.continuity.not-omitted',title='Reject ellipsis annotation on an explicit subject',expected='reject',antecedent=deepcopy(reduced['antecedent']));c['ruleIds'].append('m12.continuity');cases.append(c)
    for ending,second in [('full',full),('implicit',reduced)]:
        s['tests'].append(dict(id='actors-continuity-'+ending,title='The actors · '+('explicit subject' if ending=='full' else 'continuous subject'),ruleIds=[gid,'m11.rule.maxima'],caseIds=[[actor['id'],second['id']]],paragraphs=[dict(text=actor['text']+' '+second['text'],translation='Our actors are spirits. They have become only breath.',analysis='Coherent two-sentence adaptation of the existing Tempest reading. The same actors remain the subject; the implicit version omits their second nominal expression. The full version remains available. Lexical identity is author-supplied; discourse naturalness requires review.')]))
    s['wiki'].append(dict(id='m12-reading-and-continuity',title='0.6 · Roman reading and continuous subjects',ruleIds=[gid,'m11.rule.maxima'],body='''# Parallel reading

The user selected the original transliteration 7 font for the right column. The left remains Thimfora 79 with the registered 81 interior and 80 glow. Every scalar, punctuation mark and Maxima/Minima choice is copied exactly; there is no Unicode uppercasing, normalization or guessed phonemic respelling. The custom Roman font supplies marked vowels and digraphs at the corresponding legacy positions. Its SHA-256 is 9ba7c6f12d40ea8a0aafb8f07a69f8b65b424e374c6da95235a45edeb6292c52. Literal Times New Roman slots and the English translation remain separate available readings. A font reading is not an IPA pronunciation or a Unicode transliteration; copying its plain text gives the legacy slots. An exported PNG faithfully shows the Roman glyphs.

## Continuous subject, optional

An explicit actors clause can establish the participant for an immediately following clause. A literary writer may omit that repeated subject when it remains established and noncontrast. Predicate, only-adverb scope, event nominalizer and finite tense stay expressed. The complete clause is still acceptable. Contrast, a new subject, an interruption or uncertain reference calls for the explicit expression. This is a new proposal, not an archival discovery or an instruction to maximize omissions.

The new paired tests use coherent English: “Our actors are spirits. They have become only breath.” The finite compiler checks the omitted role, explicit antecedent case and lexical identity, the antecedent clause's own assertions, and context restrictions. A bound page additionally requires that the antecedent be the immediately previous case in the same paragraph. It cannot infer real-world reference, rhetorical effectiveness or semantic equivalence. Negative tests keep absence, wrong identity and topic shifts visible.

## Preserve accepted work

The existing three-paragraph Tempest test, its Maxima, English, dictionary and prior assertions remain byte-for-byte unchanged. The new continuity reading has separate case and page IDs, so it can be compared, revised or rejected without erasing the fuller reading. Source frequency evidence is retained; no naturalness score or random synonym replacement is introduced. The right-column font is the only intentional presentation change in reading mode; sizes, margins, leading, paper and left-column paint remain approved values.
'''))
    s['decisions'].append(dict(id='m12-reading-continuity',status='proposed',choice='Use the user-selected original transliteration 7 font for parallel reading; separately audition optional continuous subject ellipsis.',evidence='Direct user preference and original font file/chart; ellipsis is a new proposal with explicit antecedent tests, not attested evidence.'))
    validate(s);report=forge_lab.evaluate(s)
    if report['counts'].get('Fail'):raise ValueError([(r['caseId'],r['actual']) for r in report['results'] if r['status']=='Fail'])
    return s
