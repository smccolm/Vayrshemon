"""Build an explicitly proposed discourse revision from the private M9 snapshot.

This generator contains no private font or corpus. It preserves lexical roots,
inflection, English and formal cases; a human must judge its discourse reading.
"""
from copy import deepcopy
from vayrshemon.archive_language import base
from vayrshemon import variation,forge_lab
from vayrshemon.forge import validate


def propose(source):
    s=deepcopy(source);v=variation.empty();s['variation']=v
    grammar='m10.rule.discourse'
    s['language']['grammar'].append(dict(base(grammar,'Optional classification in discourse',None,''),topic='other',statement='NEW PROPOSAL for literary register: the full thing-class form remains available in every context. Optionally suppress only its outer class marker on an established, noncontrast subject/object; on a neutral predicative nominal; or on a continuing same-class nominal subject in a coordinated enumeration. First items, new subject/object referents and contrast focus retain full marking. Case and ef’ event nominalization remain. These conditions supplement the M8 full-form paradigm; they are not attested facts or a universal deletion rule.',morphologyIds=[],exampleIds=[],alternatives=[dict(statement='Retain full marking for deliberate anaphora, solemnity or ambiguity avoidance.',status='draft',citations=[]),dict(statement='Reject these proposals if human reading finds the short forms unclear.',status='draft',citations=[])]))
    contexts=[('known','Established subject or object',dict(register=['literary'],givenness=['established'],focus=['neutral'],role=['subject','object'])),('predicate','Neutral nominal predicate',dict(register=['literary'],focus=['neutral'],role=['predicate'])),('list','Continuing same-class subject list',dict(register=['literary'],focus=['neutral'],coordination=['continuation'],role=['subject']))]
    rules={r['id']:r for r in s['laboratory']['rules']}
    # Derive the exact outer prefix from the retained paradigm, never from glyphs.
    prefix=rules['nominal']['config']['prefixes'][0];event=rules['events']['config']['prefixes'][0]
    assert event.startswith(prefix)
    for rid,from_prefix,to_prefix in [('nominal',prefix,''),('events',event,event[len(prefix):])]:
        for key,title,when in contexts:
            v['alternations'].append(dict(id=f'm10.{rid}.{key}',title=title+' · '+rid,grammarId=grammar,formRuleId=rid,fromPrefix=from_prefix,toPrefix=to_prefix,when=deepcopy(when),note='New optional surface alternative. Author annotations are explicit interpretation, not inferred discourse. Preserve the full form, lexical root and inflection; preserve the inner event nominalizer.',status='proposed'))
    v['watch']=[dict(id='thing',label='Outer thing-class prefix',text=prefix,minCount=6,minShare=.15)]
    s['wiki'].append(dict(id='m10-lived-discourse',title='0.4 · Optional marking, discourse and repetition',ruleIds=[grammar,'m8.rule.poetic','forge.rule.nominals'],body='''# A lived-in language is not a randomizer

This is a proposed revision, not a claim recovered from the small historical sample. The old complete forms and the original Shakespeare assertions remain valid. No roots, case endings, tense, aspect, font mapping or English text are replaced. Dictionary identities and historical letter-frequency evidence stay intact.

## Three optional constructions

In literary register, a neutral established subject or object may omit the outer thing-class marker. A neutral predicative nominal may do the same. In a same-class subject enumeration, the first item carries full marking; continuing items may omit the outer marker. An event noun still requires its inner ef’ nominalizer. Case endings remain on every noun. Formal and citation contexts use the earlier full paradigm. Contrast focus blocks these shortened alternatives. Full forms remain available even where shortening is licensed; rhetorical repetition is not an error.

The compiler checks only the declared context labels. It cannot establish whether a referent really is given, whether a list shares a class, or where contrast belongs. An editor must supply and review those interpretations. This milestone does not add a free-prose parser.

## Reading the Tempest passage

The revels and actors are treated as shared scene participants; their later mentions are established. Breath is a neutral result predicate, retaining ef’. The first emptiness, the initial tower in the list, the dream-form metaphor and sleep retain full marking. Palaces, temples, earth and inhabitants continue the same collective enumeration. Later emptiness and our life are established. This is one defensible reading to audition, not the only reading. Metre and Shakespeare’s ambiguity are still not reproduced.

## Review practice

Compare the same watched prefix in each version’s actual page text. Inspect exact repetitions, lexical identities, clause openings and locations. A shorter or more diverse sample does not prove naturalness; no automatic diversity target is enforced. Tests include full-form acceptance, shortened-form acceptance and rejection when each required condition is absent or wrong. Negative boundary, case and nominalizer checks remain.

Next: collect contrasting dialogues, narrative and ceremonial samples; annotate speaker, register and information structure with provenance; review collocations, polysemy and lexical alternatives; then test variant choices across genres. Do not assign frequencies from this tiny demonstration or manufacture synonyms to hit a quota.
'''))
    s['decisions'].append(dict(id='m10-contextual-variation',choice='Optional context-conditioned surface forms; no random rewriting or naturalness score.',status='proposed',evidence='User identified repeated word openings in the M9 proof. Conditions and short forms are new proposals requiring author review.'))
    cases=s['laboratory']['cases'];original={c['id']:c for c in cases}
    # Key each explicit interpretation to a clause and stable lexical identity.
    choices={
      ('revels','m8.ourplay'):dict(givenness='established',focus='neutral'),
      ('actors','m8.ouractors'):dict(givenness='established',focus='neutral'),
      ('air','m8.breathe'):dict(focus='neutral'),
      ('air','m8.ouractors'):dict(givenness='established',focus='neutral'),
      ('world','m8.palace'):dict(coordination='continuation',focus='neutral'),
      ('world','m8.temple'):dict(coordination='continuation',focus='neutral'),
      ('world','m8.ground'):dict(coordination='continuation',focus='neutral'),
      ('world','m8.inhabitant'):dict(coordination='continuation',focus='neutral'),
      ('trace','m8.void'):dict(givenness='established',focus='neutral'),
      ('sleep','m8.ourlife'):dict(givenness='established',focus='neutral'),
    }
    test=next(t for t in s['tests'] if t['id']=='tempest-dreams');used=set()
    for group in test['caseIds']:
        for index,old_id in enumerate(group):
            c=deepcopy(original[old_id]);c.update(id='m10.'+old_id,title='Discourse reading · '+c['title'],context={'register':'literary'})
            source_text=c['text'];pieces=[];offset=0;previous=0
            for t in c['tokens']:
                gap=source_text[previous:t['start']];pieces.append(gap);offset+=len(gap)
                surface=source_text[t['start']:t['end']];previous=t['end'];key=(old_id.removeprefix('tempest.'),t['entryId'])
                if key in choices:
                    t['context']=choices[key];assert surface.startswith(prefix);surface=surface[len(prefix):];used.add(key)
                elif surface.startswith(prefix):t['context']=dict(givenness='new',focus='contrast') if t['role']=='predicate' else dict(givenness='new',focus='neutral',coordination='first' if t['entryId']=='m8.cloudtower' else 'independent')
                t['start']=offset;offset+=len(surface);t['end']=offset;pieces.append(surface)
            pieces.append(source_text[previous:]);c['text']=''.join(pieces);c['note']+=' M10: explicit proposed literary discourse reading; context choices are human-reviewable, not automatically inferred.';cases.append(c);group[index]=c['id']
    assert used==set(choices),set(choices)-used
    by_id={c['id']:c for c in cases}
    for paragraph,group in zip(test['paragraphs'],test['caseIds']):
        paragraph['text']=' '.join(by_id[c]['text'] for c in group);paragraph['analysis']+=' M10 proposes optional outer-class suppression for declared discourse contexts; all meanings and prior interpretive limitations remain. See the versioned discourse wiki.'
    test['ruleIds'].append(grammar)
    # Each variant is exercised with minimal context, so another variant cannot
    # accidentally make a negative assertion pass through a different license.
    for a in v['alternations']:
        rule=rules[a['formRuleId']];entry=rule['config']['entryIds'][0];context={k:values[0] for k,values in a['when'].items()};features={'case':'nominative'}
        options=variation.forms(s,entry,features,context)['forms'];short=next(r['surface'] for r in options if r['analysis'].get('variationId')==a['id']);full=next(r['surface'] for r in options if not r['analysis'].get('variationId'))
        def add(suffix,text,expected,ctx):cases.append(dict(id=a['id']+'.'+suffix,title=a['title']+' · '+suffix,kind='word',text=text,ruleIds=[a['formRuleId']],expected=expected,tokens=[],context=ctx,note='Mechanical assertion of a newly proposed context license; does not certify the discourse reading.'))
        add('short',short,'accept',context);add('full',full,'accept',context);add('formal-full',full,'accept',dict(register='formal'))
        for key in context:
            missing=dict(context);del missing[key];add('missing-'+key,short,'reject',missing)
        add('formal-short',short,'reject',dict(context,register='formal'));add('contrast',short,'reject',dict(context,focus='contrast'));add('boundary',short+'¤','reject',context)
        if a['formRuleId']=='events':add('lost-nominalizer',short[len(event)-len(prefix):],'reject',context)
    validate(s);report=forge_lab.evaluate(s)
    if report['counts'].get('Fail'):raise ValueError([(r['caseId'],r['actual']) for r in report['results'] if r['status']=='Fail'])
    return s
