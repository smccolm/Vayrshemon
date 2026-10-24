"""Proposed topic variation and explicit Maxima policy, from private M10 data."""
from copy import deepcopy
from vayrshemon.archive_language import base
from vayrshemon.forge import validate
from vayrshemon import forge_lab,spelling


def propose(source):
    s=deepcopy(source);s['variation']['formatVersion']='1.1.0'
    # Correct the prior generator's default evidence label in this new revision.
    prior=next(r for r in s['language']['grammar'] if r['id']=='m10.rule.discourse');prior['status']='draft';prior['notes']+=' M11 metadata correction: M10 described this as a proposal but inherited an attested default. It is not attested; the earlier frozen record remains inspectable.'
    orth_id='m11.rule.maxima';topic_id='m11.rule.topic'
    for key,title,statement in [(orth_id,'Maxima at sentence initials','Use the paired Maxima letter at each mapped sentence initial. Preserve interior spelling, clitics, roots and suffixes. Physical line wrapping never introduces capitals. Letter identities come from the chart; this explicit prose policy is a proposal informed by the archived capitalized sentence openings, not a recovered complete capitalization grammar.'),(topic_id,'Established subject as topic','In literary narrative, an established, noncontrast subject topic may precede its nominal predicate and final verb. A predicate-associated only adverb remains with the predicate. Retain the earlier predicate-first construction as an available alternative; do not shuffle clauses for variety. Case endings remain authoritative. This is a new discourse proposal, not attested word-order evidence.')]:
        s['language']['grammar'].append(dict(base(key,title,None,'',status='draft'),topic='other',statement=statement,morphologyIds=[],exampleIds=[],alternatives=[]))
    s['spelling']=dict(formatVersion='1.0.0',orthographyId='thimfora-79',grammarId=orth_id,formRuleIds=[r['id'] for r in s['laboratory']['rules'] if r['kind']=='forms'],terminalCharacters='.!?',openingCharacters='"\'“”‘’()[]{}',initialForm='maxima')
    order=deepcopy(next(r for r in s['laboratory']['rules'] if r['id']=='clause'));order.update(id='m11.discourse-order',title='Retained order and established topic alternatives',grammarId=topic_id)
    when=dict(register=['literary'],topic=['subject'],givenness=['established'],focus=['neutral'])
    order['config']['alternatives']=[dict(id='subject-predicate',pattern=['subject','predicate','verb'],when=deepcopy(when),note='Established subject topic first; predicate remains new information.'),dict(id='subject-predicate-only',pattern=['subject','predicate','adverb','verb'],when=deepcopy(when),note='Maintain the established subject; predicate and its only adverb stay together.')]
    s['laboratory']['rules']+=[order,dict(id='spelling.initial-maxima',title='Sentence-initial Maxima',kind='letterforms',grammarId=orth_id,config={})]
    cases=s['laboratory']['cases'];lookup={r['id']:r for r in cases};test=next(t for t in s['tests'] if t['id']=='tempest-dreams')
    for group,paragraph in zip(test['caseIds'],test['paragraphs']):
        for i,key in enumerate(group):
            c=deepcopy(lookup[key]);c.update(id=key.replace('m10.','m11.',1),title='Topic reading · '+c['title'][:170]);c['ruleIds']=[order['id'] if rid=='clause' else rid for rid in c['ruleIds']]
            if key in ('m10.tempest.actors','m10.tempest.air'):
                roles=['subject','predicate','verb'] if key.endswith('actors') else ['subject','predicate','adverb','verb']
                c['context'].update(topic='subject',givenness='established',focus='neutral')
                original=deepcopy(c);original.update(id=c['id']+'.retained-order',title='Retained predicate-first construction with a topic');cases.append(original)
                tokens=[];pieces=[];offset=0
                for role in roles:
                    t=deepcopy(next(t for t in c['tokens'] if t['role']==role));surface=c['text'][t['start']:t['end']]
                    if role=='predicate':t.setdefault('context',{})['focus']='neutral'
                    t.update(start=offset,end=offset+len(surface));tokens.append(t);pieces.append(surface);offset+=len(surface)+1
                c.update(text=' '.join(pieces)+'.',tokens=tokens)
                for label,change in [('no-topic',dict(topic='none')),('formal',dict(register='formal')),('new-topic',dict(givenness='new')),('contrast',dict(focus='contrast'))]:
                    negative=deepcopy(c);negative.update(id=c['id']+'.'+label,title='Reject topic order · '+label,expected='reject');negative['context'].update(change);cases.append(negative)
                for field in when:
                    negative=deepcopy(c);negative.update(id=c['id']+'.missing-'+field,title='Reject topic order without '+field,expected='reject');del negative['context'][field];cases.append(negative)
            c['note']+=' M11: the actors remain an established topic in two adjoining clauses; other clause orders retain the earlier literary reading. Capitalization is a separate explicit review.'
            cases.append(c);lookup[c['id']]=c;group[i]=c['id']
        paragraph['text']=' '.join(lookup[k]['text'] for k in group);paragraph['analysis']+=' M11 auditions established-subject topic order in the actors/breath clauses; the existing order remains available. Maxima mark sentences, not printed lines.'
    test['ruleIds']+=[orth_id,topic_id]
    mapping=spelling.pairs(s)
    for lo,row in mapping.items():
        for label,text,expected in [('maxima',row['maxima'],'accept'),('missing',lo,'reject')]:
            cases.append(dict(id='m11.letter.'+str(ord(lo))+'.'+label,title=row['name']+' · '+label,kind='word',text=text,ruleIds=['spelling.initial-maxima'],expected=expected,tokens=[],note='Orthography probe of a chart identity; not a lexical utterance.'))
    s['wiki'].append(dict(id='m11-maxima-and-topics',title='0.5 · Maxima, sentence boundaries and topic variation',ruleIds=[orth_id,topic_id,'m10.rule.discourse'],body='''# Restore the Maxima

The 47 paired letter identities and all three aligned font layers already contain Maxima. The earlier generated examples used Minima roots and affixes without a sentence-initial spelling pass. This revision fixes that omission in the language text, not by enlarging letters or changing the paint.

## Evidence and proposal

The chart pairs are evidence-bound. Polished Examples paragraphs 0 and 17 begin with Maxima; the two sentences in paragraph 0 have distinct Maxima initials. Historical encodings still require care. M11 proposes an explicit prose convention: the first mapped letter at the beginning of a paragraph or after . ! ? uses its paired Maxima. Opening quotes/brackets and whitespace may precede it. Interior spelling is preserved. A wrapped line, comma or semicolon is not a new sentence. Abbreviations, quoted fragments, numeral-led sentences and proper-name conventions need editorial review; unknown initial scalars are reported rather than guessed.

The chart has non-Unicode case pairs: the Minima slot ß maps to the Maxima slot Þ, and the Minima slot á maps to à. Unicode upper() would produce wrong identities. The spelling preview displays the actual mapped letterforms, and applying it retains the old cases, clones reviewed cases and updates their page binding atomically. It never edits the English column. Maxima still pass through the exact 79 master, 81 interior and 80 glow rendering pipeline.

## Variation with a discourse purpose

The actors are a shared, established topic. Two clauses may now put that subject first, followed by its predicate and final verb. The breath predicate keeps its event nominalizer and associated only adverb. The older predicate-first order remains available, including when a topic is established. New or contrastive topics and formal register do not license the added orders. These are new proposals, with explicit author annotations and negative tests; the finite checker does not infer information structure or certify equivalent emphasis.

We retain full class marking for selected new images, including spirits, even where a shortened form would be permitted. Other clauses keep the earlier reading. This revision does not use random choices or a word-order diversity target. Meaning, rhythm and genre should guide later revisions.

## Review and provenance

The M10 discourse grammar was described as proposed but its record inherited an attested default. M11 corrects its status to draft. No evidence has been added to retroactively attest it; the old commit remains intact. Dictionary identities, lexical roots, English, original full forms, earlier case assertions and approved page formatting remain.

Repetition metrics now fold only the explicit Maxima/Minima identity pairs when counting watched prefixes. Otherwise capitalization would falsely hide recurring class markers. Exact spelling counts and source text remain visible. Test a coherent passage in several readings and registers before claiming preferences or frequencies for the language as a whole.
'''))
    s['decisions'].append(dict(id='m11-maxima-topic',status='proposed',choice='Explicit sentence-initial Maxima from mapped letter pairs, and optional established-subject topic order. No automatic source rewriting or random reordering.',evidence='Chart identity pairs and capitalized archived sentence openings support the forms. The complete prose capitalization convention and topic construction are new, reviewable proposals.'))
    validate(s);r=forge_lab.evaluate(s)
    if r['counts'].get('Fail'):raise ValueError([(c['caseId'],c['actual']) for c in r['results'] if c['status']=='Fail'])
    return s
