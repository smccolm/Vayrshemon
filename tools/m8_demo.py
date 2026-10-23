"""Private M8 literary proposal, executable tests and approved-page demonstration.

The quoted public-domain English is the starting point. All current script forms
are derived locally from cited witnesses, never copied into a public fixture.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import uuid
from PySide6.QtWidgets import QApplication
from tools.m0.common import load_json,write_json,file_hash
from tools.approved_baseline import MANIFEST,check_state
from vayrshemon.forge import ForgeProject,validate
from vayrshemon.forge_archive import symbol_frequency
from vayrshemon.archive_language import base
from vayrshemon.laboratory_api import LaboratorySession,LaboratoryAPI
from vayrshemon.forge_lab import empty_lab,SEPARATORS

SOURCE='https://www.folger.edu/explore/shakespeares-works/the-tempest/read/4/1/'
ENGLISH=[
 'Our revels now are ended. These our actors,\nAs I foretold you, were all spirits and\nAre melted into air, into thin air;',
 'And like the baseless fabric of this vision,\nThe cloud-capped towers, the gorgeous palaces,\nThe solemn temples, the great globe itself,\nYea, all which it inherit, shall dissolve,\nAnd, like this insubstantial pageant faded,\nLeave not a rack behind.',
 'We are such stuff\nAs dreams are made on, and our little life\nIs rounded with a sleep.',
]


def proposal(previous,root):
    s=deepcopy(previous);d=s['language'];lex={r['id']:r for r in d['lexicon']};forms={}
    venik={236:195,238:197,239:199,241:201,243:203,242:205,244:207,246:209,245:211,250:213,249:215,251:217,252:219,8224:221,176:223,162:225,163:227,167:229,8226:231,182:233,223:235}
    for name,row in [('sleep',162),('live',113),('surround',173),('play',134),('become',19),('remain',167),('fly',78),('stand',165),('believe',21),('water',288),('ground',261),('form',257),('void',287),('man',270),('shade',279),('breathe',24),('say',150),('origin',243),('cease',32)]:
        old=lex[f'chart-1.t0.r{row}'];r=deepcopy(old);r['id']='m8.'+name;r['headword']=''.join(chr(venik.get(ord(c),ord(c))) for c in old['headword']);r['orthographyId']='thimfora-79';r['status']='draft'
        r['senses'][0].update(id=r['id']+'.sense1',status='draft');r['citations'] += [dict(sourceId='venik-instructions',locator='named letter inventory'),dict(sourceId='mapping-79',locator='chart-2 minima slots')]
        r['notes']='M8 proposed current spelling by named Venik letter identity; archive witness retained. Semantic extensions require the Tempest wiki.';d['lexicon'].append(r);forms[name]=r['headword']
    for name in ('be','we','I','see','build','beauty','fragile','learn','jewel'): forms[name]=lex['forge.'+name]['headword']
    compounds={
      'ourplay':('Our revels',forms['we']+'’'+forms['play'],'collective-we + play; revels interpreted as our enacted celebration'),
      'ouractors':('Our actors',forms['we']+'’'+forms['play']+forms['man'],'collective-we + play + human; stage-people, generic collective number'),
      'spirit':('Spirit',forms['shade']+forms['form'],'shade + form; a bodiless apparition, not a theological assertion'),
      'foretell':('Foretell',forms['origin']+forms['say'],'origin + say; proposed lexical anticipation, earlier speech'),
      'cloudtower':('Cloud-crowned tower',forms['water']+forms['fly']+forms['build']+forms['stand'],'water + fly + build + stand; lexical poetic compound, not a claim of attested tower terminology'),
      'palace':('Palace',forms['beauty']+forms['build'],'beauty + build; a splendid building, no assertion of royal ownership'),
      'temple':('Temple',forms['believe']+forms['build'],'believe + build; a house of reverence, no specified religion'),
      'inhabitant':('Earth-dweller',forms['ground']+forms['live'],'ground + live; a collective class of living inhabitants'),
      'dreamform':('Dream-substance',forms['sleep']+forms['see']+forms['form'],'sleep + see + form; dreamlike constitution, rather than a claim of literal physical material'),
      'ourlife':('Our life',forms['we']+'’'+forms['live'],'collective-we + boundary + live; proposed bound possessor and nominalized life'),
    }
    for key,(meaning,form,derivation) in compounds.items():
        rid='m8.'+key;r=dict(base(rid,meaning,'chart-1','M8 compound proposal; components listed in etymology','draft'),headword=form,orthographyId='thimfora-79',pronunciation='',ipa='',partOfSpeech='noun',senses=[dict(id=rid+'.sense1',definition=meaning,status='draft',citations=[])],variants=[],etymology=derivation,exampleIds=[],audioLinks=[])
        r['citations'].append(dict(sourceId='polished',locator='nominal constructions and collective we; M8 extension'));d['lexicon'].append(r);forms[key]=form
    # Frozen finite phrases make the poetic readings inspectable rather than
    # silently pretending the archive already contains a complete translator.
    fixed={'only':('Only','yib’ëw'),'afterplay':('After the pageant','ef’'+forms['play']+'’hëth')}
    for key,(meaning,form) in fixed.items():
        rid='m8.'+key;d['lexicon'].append(dict(base(rid,meaning,'polished' if key=='only' else 'chart-1','attested only; proposed after-play phrase','draft'),headword=form,orthographyId='thimfora-79',pronunciation='',ipa='',partOfSpeech='adverbial',senses=[dict(id=rid+'.sense1',definition=meaning,status='draft',citations=[])],variants=[],etymology='Only is from the polished gloss.' if key=='only' else 'ef- nominalizes play; -hëth is a NEW proposed temporal boundary clitic, chosen explicitly for this literary branch, not recovered from the sources.',exampleIds=[],audioLinks=[]));forms[key]=form
    grammar=[
      ('poetic','Poetic nominal classes and enumeration','construction','In this literary register, lexicalized compound noun heads use the thing determiner gßÑet’ and retain case: -get predicate/object and -lÉy subject. An asyndetic list of 1–8 nominative subjects shares the final verb. Number is generic collective here. This does not license arbitrary English word order. Existing explicit-class constructions remain available.'),
      ('metaphor','Tempest compounds and semantic choices','other','Lexicalize the proposed cloud-tower, beauty-building, belief-building, earth-dweller and sleep-see-form compounds. Interpret ly’ + life as collective-our life. Use sleep as the nominal agent of surround. The temporal after-play phrase and -hëth boundary are explicit new proposals. These meanings need author review; the compiler only checks declared forms.'),
    ]
    for key,title,topic,statement in grammar: d['grammar'].append(dict(base('m8.rule.'+key,title,'polished','M8 literary extrapolation','draft'),topic=topic,statement=statement,morphologyIds=[],exampleIds=[],alternatives=[]))
    lab=empty_lab();s['laboratory']=lab
    def rule(key,title,grammar,kind,config): lab['rules'].append(dict(id=key,title=title,grammarId=grammar,kind=kind,config=config))
    rule('inventory','Current display inventory','forge.rule.orthography','inventory',dict(orthographyId='thimfora-79',extraCharacters=SEPARATORS+'’'))
    verbs=['forge.'+w for w in ('be','see','learn')]+['m8.'+w for w in ('become','remain','surround','cease','foretell')]
    rule('finite','Seven tenses × three aspects','forge.rule.tense','forms',dict(entryIds=verbs,prefixes=[''],slots=[dict(feature='tense',values=dict(past='iz',present='ow',future='at',distantPast='diz',immediatePast='riz',immediateFuture='dat',distantFuture='rat')),dict(feature='aspect',values=dict(simple='ya',progressive='am',perfect='fu'))]))
    nouns=['m8.'+w for w in ('cloudtower','palace','temple','ground','inhabitant','void','dreamform','ourlife','sleep','ourplay','ouractors','spirit','breathe')]
    rule('nominal','Poetic nouns retain case','m8.rule.poetic','forms',dict(entryIds=nouns,prefixes=['gßÑet’'],slots=[dict(feature='case',values=dict(accusative='get',nominative='lÉy'))]))
    rule('closed','Pronouns and adverbial phrases','forge.rule.pronouns','forms',dict(entryIds=['forge.we','forge.I','m8.only','m8.afterplay'],prefixes=[''],slots=[]))
    rule('modifier','Postnominal count modifier','forge.rule.nominals','forms',dict(entryIds=['forge.fragile'],prefixes=[''],slots=[dict(feature='class',values=dict(count='’mç'))]))
    rule('analysis','Exhaustive declared word analyses','forge.rule.lexicon','analysis',dict(formRuleIds=['finite','nominal','closed','modifier']))
    rule('clause','Declared clause role sequences','forge.rule.order','order',dict(patterns=[['predicate','subject','verb'],['subject','verb'],['subject','adverb','verb','adjunct'],['object','modifier','subject','verb'],['predicate','adverb','subject','verb']]))
    lab['rules'][-1]['config'].update(roleFeatures=dict(predicate=[{'case':'accusative'}],object=[{'case':'accusative'}],subject=[{}, {'case':'nominative'}],modifier=[{'class':'count'}]),roleEntries=dict(predicate=nouns,object=nouns,subject=nouns+['forge.I','forge.we'],verb=verbs,adverb=['m8.only'],adjunct=['m8.afterplay'],modifier=['forge.fragile']))
    rule('interpretation','Literary interpretation requires review','m8.rule.metaphor','review',dict(reason='Spelling and structure do not establish Shakespearean semantic equivalence. Read the source, back-translation and loss notes in the wiki.'))
    def case(key,title,text,expected,rules,kind='word',tokens=None,note='Source-derived proposal; not attested language.'):
        row=dict(id=key,title=title,text=text,expected=expected,ruleIds=rules,kind=kind,tokens=tokens or [],note=note);lab['cases'].append(row);return row
    # Expectations are the source-table choices, separate from compiler output.
    for tense,suffix in [('past','iz'),('present','ow'),('future','at'),('distantPast','diz'),('immediatePast','riz'),('immediateFuture','dat'),('distantFuture','rat')]:
        for aspect,ending in [('simple','ya'),('progressive','am'),('perfect','fu')]: case('finite.'+tense+'.'+aspect,tense+' · '+aspect,forms['learn']+suffix+ending,'accept',['finite','inventory'])
    for n,bad in enumerate(['', 'ow', 'ya', 'yaow', 'zzya', 'owyaow', 'OWya']): case('finite.reject.'+str(n),'Reject malformed finite verb '+str(n),forms['learn']+bad,'reject',['finite'])
    for n in ('dreamform','ourlife','cloudtower'):
        case('noun.'+n,n+' with case','gßÑet’'+forms[n]+'get','accept',['nominal','inventory']);case('noun.reject.'+n,n+' missing case',forms[n],'reject',['nominal'])
    for rid,word in [('closed',forms['we']),('modifier',forms['fragile']+'’mç')]:
        case(rid+'.positive',rid+' valid',word,'accept',[rid]);case(rid+'.negative',rid+' unexpected suffix',word+'zz','reject',[rid])
    case('inventory.unknown','Unknown scalar is rejected','🙂','reject',['inventory'])
    clauses=[]
    def token(word,role,entry,**features): return dict(word=word,role=role,entryId=entry,features=features)
    def noun(name,role,case_name='nominative'):
        return token('gßÑet’'+forms[name]+('get' if case_name=='accusative' else 'lÉy'),role,'m8.'+name,case=case_name)
    def verb(name,tense='present',aspect='simple'):
        return token(forms[name]+({'future':'at','past':'iz','present':'ow'}[tense])+('fu' if aspect=='perfect' else 'ya'),'verb',('forge.' if name=='be' else 'm8.')+name,tense=tense,aspect=aspect)
    def clause(key,title,items):
        text=' '.join(t['word'] for t in items);tokens=[];offset=0
        for t in items:
            tokens.append(dict(start=offset,end=offset+len(t['word']),**{k:v for k,v in t.items() if k!='word'}));offset+=len(t['word'])+1
        case('tempest.'+key,title,text,'accept',['inventory','analysis','clause'],'clause',tokens);clauses.append(text+'.');return text,tokens
    clause('revels','Our revels have ended',[noun('ourplay','subject'),verb('cease',aspect='perfect')])
    clause('actors','Our actors were spirits',[noun('spirit','predicate','accusative'),noun('ouractors','subject'),verb('be','past')])
    clause('foretold','I foretold',[token(forms['I'],'subject','forge.I'),verb('foretell','past')])
    clause('air','Our actors have become only air',[noun('breathe','predicate','accusative'),token(forms['only'],'adverb','m8.only'),noun('ouractors','subject'),verb('become',aspect='perfect')])
    enumeration=[noun('void','predicate','accusative')]+[noun(n,'subject') for n in ('cloudtower','palace','temple','ground','inhabitant')]+[verb('become','future')]
    clause('world','The world becomes emptiness',enumeration)
    clause('trace','Only emptiness remains after the play',[noun('void','subject'),token(forms['only'],'adverb','m8.only'),verb('remain','future'),token(forms['afterplay'],'adjunct','m8.afterplay')])
    text,tokens=clause('dream','We are dream-substance',[noun('dreamform','predicate','accusative'),token(forms['we'],'subject','forge.we'),verb('be')])
    invalid=deepcopy(tokens);invalid[0]['role']='subject';invalid[1]['role']='predicate'
    case('clause.reject.order','Reject swapped clause roles',text,'reject',['analysis','clause'],'clause',invalid)
    invalid=deepcopy(tokens);invalid[-1]['features']['tense']='future'
    case('clause.reject.tense','Reject an incorrect tense annotation',text,'reject',['analysis'],'clause',invalid)
    case('clause.reject.unconsumed','Reject an unanalysed tail',text+' unknown','reject',['analysis'],'clause',tokens)
    # This surface is a valid inflection, but nominative cannot fill the
    # predicate role. An author cannot make it pass by relabeling its feature.
    wrong=text.replace('get','lÉy',1);invalid=deepcopy(tokens);invalid[0]['features']['case']='nominative'
    case('clause.reject.case','Reject nominative predicate despite valid word',wrong,'reject',['analysis','clause'],'clause',invalid)
    clause('sleep','Sleep encloses our fragile life',[noun('ourlife','object','accusative'),token(forms['fragile']+'’mç','modifier','forge.fragile',**{'class':'count'}),noun('sleep','subject'),verb('surround')])
    case('tempest.meaning','Shakespearean meaning is editorial',' / '.join(ENGLISH),'review',['interpretation'],'review')
    case('prose.unsupported','Free prose is not a parsed clause',text,'unsupported',['clause'],'review')
    interpretations=[
      'Back-translation: Our celebration has ended. Our stage-people were shadow-forms. I foretold. Our stage-people have become only breath. Revels is a collective enacted celebration; spirit becomes a nonphysical shadow-form; melted into thin air becomes a perfect-aspect transformation into mere breath. The explicit addressee you is omitted, and as I foretold becomes a parenthetical independent clause. These are recorded interpretive differences, not missing analysis.',
      'Back-translation: Cloud-towers, beauty-buildings, belief-buildings, the earth and earth-dwellers will become emptiness. Only emptiness will remain after the play. The baseless vision is conveyed through the later dream-form image rather than a separate simile. The enumeration is collective and poetic; grandeur, architectural solemnity and the visual image of a dissolving rack/cloud are compressed. Future -at- is retained. This is an adaptation, not a literal translation.',
      'Back-translation: We are dream-form. Sleep surrounds our fragile life. Sleep-see-form interprets shared dreamlike constitution, without asserting literal material. Fragile interprets the vulnerability and brevity of little; surround preserves the enclosing metaphor of rounded. Collective our uses a newly proposed bound possessor. Metre, rhyme and the original ambiguity are not reproduced.',
    ]
    s['tests'].append(dict(id='tempest-dreams',title='The Tempest · We are such stuff as dreams are made on',ruleIds=['m8.rule.poetic','m8.rule.metaphor','forge.rule.tense','forge.rule.order'],paragraphs=[dict(text=' '.join(clauses[a:b]),translation=ENGLISH[i],analysis=interpretations[i]) for i,(a,b) in enumerate([(0,4),(4,6),(6,8)])]))
    for key,title,body,rules in [
      ('m8-tempest','The Tempest: source, adaptation and losses','# Shakespeare as the starting point\n\nWilliam Shakespeare, The Tempest, Act 4 scene 1, Prospero, Folger lines 165–175 (ends before “Sir, I am vexed”). '+SOURCE+'\n\nPublic-domain dramatic text, verified 2026-10-23. English words and punctuation retained; verse line breaks reflow in the column, and paragraph boundaries separate the revels, world and final dream images. No claim of a perfect or automatic translation.\n\n'+ '\n\n'.join(interpretations)+'\n\n## Proposed compounds\n'+ '\n'.join('- '+k+': '+v[2] for k,v in compounds.items())+'\n\nAfter-play adds the explicitly new temporal boundary -hëth. This and the compounds need the author’s review; they are not retrospectively attributed to the archive.',['m8.rule.metaphor']),
      ('m8-lab','Executable test scope and interpretation','# Executable language laboratory\n\nFinite forms are compiled from dictionary IDs, literal prefixes and feature slots. Seven tenses × three aspects, case suffixes, pronouns and modifiers have positive and negative assertions. Annotated clauses supply Unicode-scalar spans and roles; the checker validates every word and rejects unconsumed text or mismatched features. It does not infer those roles from free prose.\n\nThe first experimental version excludes plural enumeration from its role patterns, so the literary enumeration test must fail. The second version explicitly admits a bounded list of 1–8 subjects. Compare uses exactly the first version’s test definitions against both grammars; changed expectations cannot erase a regression.\n\nA Pass is a mechanical assertion result. Literary meaning remains Needs review. Unsupported free-prose parsing never counts as covered grammar.',['m8.rule.poetic','forge.rule.tense']),
      ('m8-poetic','Poetic noun classes and clause enumeration','# Literary register 0.2\n\n'+grammar[0][3]+'\n\nThe ordinary adjective follows its noun. A predicate followed by several subject heads is treated as one collective enumeration. The declared role grammar deliberately leaves broader coordination, agreement, quantification and productive temporal constructions for later versions.',['m8.rule.poetic']),
    ]: s['wiki'].append(dict(id=key,title=title,body=body,ruleIds=rules))
    mapping=load_json(Path(root)/'data/orthography/thimfora-79.json')
    s['research']['tempest']=dict(source=SOURCE,author='William Shakespeare',work='The Tempest',scene='4.1',selection='Chosen famous passage; not random syllable generation.',english=ENGLISH,backTranslations=interpretations,letterFrequency=symbol_frequency(clauses,mapping),frequencyPolicy='Retain source roots and sound inventory; do not force a short literary text to match a 152-letter reference sample.')
    validate(s);return s


def review_nominalization(snapshot):
    """A separate language revision: retain the source's explicit v→n clitic."""
    s=deepcopy(snapshot);lab=s['laboratory'];lex={r['id']:r for r in s['language']['lexicon']}
    lex['m8.foretell']['partOfSpeech']='verb'
    lex['m8.foretell']['notes']+=' Revision 0.2.2: lexical compound is a verb, not a noun.'
    events=['m8.sleep','m8.breathe'];nominal=next(r for r in lab['rules'] if r['id']=='nominal')
    nominal['config']['entryIds']=[i for i in nominal['config']['entryIds'] if i not in events]
    lab['rules'].append(dict(id='events',title='Explicit verb-to-noun conversion',grammarId='forge.rule.nominals',kind='forms',config=dict(entryIds=events,prefixes=['gßÑet’ef’'],slots=[dict(feature='case',values=dict(accusative='get',nominative='lÉy'))])))
    next(r for r in lab['rules'] if r['id']=='analysis')['config']['formRuleIds'].append('events')
    for case in lab['cases']:
        if case['kind']!='clause': continue
        pieces=[];offset=0;new_tokens=[]
        for token in case['tokens']:
            pieces.append(case['text'][offset:token['start']]);start=len(''.join(pieces));word=case['text'][token['start']:token['end']]
            if token['entryId'] in events: word=word.replace('gßÑet’','gßÑet’ef’',1)
            pieces.append(word);new_tokens.append(dict(token,start=start,end=start+len(word)));offset=token['end']
        pieces.append(case['text'][offset:]);case['text']=''.join(pieces);case['tokens']=new_tokens
    for test in s['tests']:
        if test['id']!='tempest-dreams': continue
        for pair in test['paragraphs']:
            for key in events:
                for suffix in ('get','lÉy'):
                    pair['text']=pair['text'].replace('gßÑet’'+lex[key]['headword']+suffix,'gßÑet’ef’'+lex[key]['headword']+suffix)
            pair['analysis']+=' Revision 0.2.2 retains explicit ef’ verb-to-noun conversion for breath and sleep.'
    for key in events:
        for valid in (True,False):
            lab['cases'].append(dict(id='events.'+key+'.'+str(valid).lower(),title=('Accept explicit ' if valid else 'Reject missing ')+'nominalizer: '+key,kind='word',text=('gßÑet’ef’' if valid else 'gßÑet’')+lex[key]['headword']+'lÉy',expected='accept' if valid else 'reject',ruleIds=['events'],tokens=[],note='The polished wonder construction explicitly contains ef’ (verb-to-noun); retain it for new event nouns.'))
    next(w for w in s['wiki'] if w['id']=='m8-poetic')['body']+='\n\n## Revision 0.2.2 — nominalization review\nSleep and breath are event nouns derived from verbs. Retain the explicit ef’ conversion between the thing determiner and verb root, as in the polished wonder construction. Add positive and negative tests for this boundary. Correct foretell’s lexical category to verb. Earlier test inputs and language versions remain intact.'
    s['research']['tempest']['nominalizationReview']='0.2.2: explicit source-derived ef’ on sleep/breath; foretell is a verb.'
    validate(s);return s


def bind_demo_cases(snapshot):
    """Bind the displayed script to the exact complete clauses being tested."""
    s=deepcopy(snapshot);cases={c['id']:c for c in s['laboratory']['cases']}
    groups=[['tempest.'+key for key in keys] for keys in [('revels','actors','foretold','air'),('world','trace'),('dream','sleep')]]
    test=next(t for t in s['tests'] if t['id']=='tempest-dreams');test['caseIds']=groups
    for ids,pair in zip(groups,test['paragraphs']):
        for key in ids:
            if not cases[key]['text'].endswith('.'): cases[key]['text']+='.'
        pair['text']=' '.join(cases[key]['text'] for key in ids)
    next(w for w in s['wiki'] if w['id']=='m8-lab')['body']+='\n\n## Revision 0.2.3 — bind the proof to its assertions\nEach displayed script paragraph is now tied to ordered stable clause-case IDs, including sentence punctuation. Saving a page whose script differs from those frozen inputs fails validation. This also corrects a prefix-matching error in the 0.2.2 display test: the lexicalized dream-form compound must not receive the event nominalizer merely because its first root is sleep. The grammatical assertions already had the correct compound. Earlier versions remain inspectable.'
    validate(s);return s


def build(root,out):
    root,out=Path(root),Path(out)
    if out.exists(): raise ValueError('DEMO_DIRECTORY_EXISTS')
    out.mkdir(parents=True);app=QApplication.instance() or QApplication([])
    s=LaboratorySession(root,source_fonts=False,recovery=False);api=LaboratoryAPI(s);transcript=[]
    def call(method,**params):
        if 'expected_generation' in api.methods[method][2]['properties']:
            status=s.forge.status();params.update(expected_generation=status['generation'],project_id=status['projectId'])
        result=api.call(method,params,expected_revision=s.revision,document_id=s.state['documentId'],idempotency_key=uuid.uuid4().hex,origin='mcp');transcript.append(dict(method=method,params=params,response=result))
        if not result['ok']: raise ValueError(result['error']['message'])
        return result['result']
    try:
        manifest=load_json(root/MANIFEST);source=root/manifest['source']['path'];baseline=load_json(source)
        if file_hash(source)!=manifest['source']['sha256']: raise ValueError('APPROVED_REFERENCE_CHANGED')
        check_state(baseline['state'],manifest);write_json(out/'approved-workbench.vay.json',baseline);s.open(out/'approved-workbench.vay.json');original=s.capture()
        bundle=root/'.local/demos/m7-forge-v0.8.0/forge-history-final.json'
        call('forge.restore',path=str(bundle),destination=str(out/'Vayrshemon.vayforge'))
        old=s.forge.status()['head'];call('forge.branch',name='literary-0.2',version=old)
        draft=proposal(s.forge.read(old)['snapshot'],root);call('forge.draft.replace',snapshot=draft)
        first=call('forge.commit',label='Vayrshemon 0.2.0 · literary experiment before enumeration')['head']
        before=call('forge.lab.run',version=first,directory=str(out/'suite-before'))
        rule=deepcopy(next(r for r in draft['laboratory']['rules'] if r['id']=='clause'))
        rule['grammarId']='m8.rule.poetic';rule['config']['patterns'] += [['predicate']+['subject']*n+['verb'] for n in range(2,9)]
        call('forge.lab.put',collection='rules',record=rule)
        wiki=deepcopy(next(r for r in draft['wiki'] if r['id']=='m8-poetic'));wiki['body']+='\n\n## Revision 0.2.1\nThe executable rule now admits 2–8 co-subjects after the predicate, in addition to the existing one-subject clause. The test inputs and expectations are unchanged.';call('forge.record.put',collection='wiki',record=wiki)
        enumeration_version=call('forge.commit',label='Vayrshemon 0.2.1 · scoped poetic enumeration')['head']
        call('forge.draft.replace',snapshot=review_nominalization(s.forge.read(enumeration_version)['snapshot']))
        nominalization_version=call('forge.commit',label='Vayrshemon 0.2.2 · explicit event nominalization')['head']
        call('forge.draft.replace',snapshot=bind_demo_cases(s.forge.read(nominalization_version)['snapshot']))
        final=call('forge.commit',label='Vayrshemon 0.2.3 · proof bound to tested clauses')['head']
        suite=call('forge.lab.run',version=final,directory=str(out/'suite-after'));comparison=call('forge.lab.compare',before=first,after=enumeration_version);write_json(out/'comparison.json',comparison)
        if suite['counts'].get('Fail'): raise ValueError('DEMO_LANGUAGE_ASSERTION_FAILED: '+str([(r['caseId'],r['actual']) for r in suite['results'] if r['status']=='Fail']))
        report=call('forge.test.run',version=final,test_id='tempest-dreams',directory=str(out/'tempest'))
        if report['status'] in ('Error','Fail'): raise ValueError(report)
        call('forge.export',path=str(out/'forge-history.json'))
        if s.capture()!=original: raise ValueError('FORGE_CHANGED_OPEN_WORKBENCH')
        result=dict(project=str(s.forge.path),previousVersion=old,firstVersion=first,enumerationVersion=enumeration_version,nominalizationVersion=nominalization_version,finalVersion=final,run=report,suite=suite,comparison=str(out/'comparison.json'),openDocumentUnchanged=True)
        write_json(out/'demo.json',result)
        (out/'share-caption.txt').write_text('William Shakespeare · The Tempest, Act 4, scene 1. English source: '+SOURCE+'\nVayrshemon 0.2.3: a proposed literary adaptation, not a literal translation. Rendered in the Vayrshemon Language Workbench M8.\n',encoding='utf-8')
        return result
    finally: write_json(out/'api-transcript.json',transcript);s.finish()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args();result=build(Path(__file__).resolve().parents[1],args.out.resolve());print(json.dumps({k:result[k] for k in ('project','firstVersion','finalVersion','openDocumentUnchanged')}))
