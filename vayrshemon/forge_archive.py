"""Local archive research and an explicitly proposed first language branch.

Private inputs and derived texts are read locally, never bundled with the app.
The user authorized extrapolation for M7; source witnesses remain unchanged.
"""
from collections import Counter,defaultdict
from copy import deepcopy
from pathlib import Path
import re
from tools.m0.common import file_hash,load_json
from tools.m0.docx import extract_docx
from .archive_language import seed,base
from .forge import empty_snapshot,validate


def symbol_frequency(texts,mapping):
    slots={e['scalar']:e for e in mapping['entries']};counts=Counter();unknown=Counter();excluded=Counter()
    for text in texts:
        for char in text:
            item=slots.get(ord(char))
            if item and item['kind']=='letter' and item['symbolId']: counts[item['symbolId']]+=1
            elif not item or item['status']=='unresolved': unknown[f'U+{ord(char):04X}']+=1
            else: excluded[item['kind']]+=1
    total=sum(counts.values())
    return dict(letterCount=total,letters=[dict(symbolId=r['symbolId'],name=r['nameTranscription'],count=counts[r['symbolId']],fraction=counts[r['symbolId']]/total if total else 0) for r in mapping['inventory'] if r['kind']=='letter'],unknownSlots=dict(unknown),excluded=dict(excluded))


def archive_snapshot(root):
    root=Path(root);result=empty_snapshot();data=seed(root);result['language']=data
    inventory=[];buckets=defaultdict(Counter);seen=set()
    for path in sorted((root/'Inputs').rglob('*')):
        if not path.is_file() or path.name.startswith('~$') or path.suffix.lower() not in ('.docx','.doc','.txt','.pdf','.xps'): continue
        rel=path.relative_to(root/'Inputs').as_posix();row=dict(path=rel,sha256=file_hash(path),bytes=path.stat().st_size)
        synthetic=any(w in rel.lower() for w in ('kerning','test sequence','testsequence','full set','character set','abcdefghijklmnopqrstuvwxyz','thimfora test','thimfora venik - large'))
        if path.suffix.lower()=='.docx':
            evidence=extract_docx(path);row.update(paragraphs=len(evidence['paragraphs']),review='All textual runs extracted; inherited styles and embedded images unresolved',frequencyRole='excluded structural specimen' if synthetic else 'font-stratified source slots')
            if not synthetic:
                for paragraph in evidence['paragraphs']:
                    for run in paragraph['runs']:
                        text=''.join(t.get('text','') for t in run['tokens']);font=run['directFonts'].get('ascii','unresolved inherited style')
                        if not re.search(r'(?i)thimfora|test seven|test 7',font): continue
                        # Deduplicate exact run witnesses within each historical face.
                        key=(font,text)
                        if key in seen: continue
                        seen.add(key);buckets[font].update(text)
        elif path.suffix.lower()=='.pdf': row['review']='Dictionary inspiration; front matter and sampled pages reviewed separately, not a Vayrshemon corpus'
        elif path.suffix.lower()=='.txt': row['review']='Technical font/test text; excluded from natural-language frequency'
        else: row['review']='Legacy container retained; not decoded by DOCX extractor'
        inventory.append(row)
    for sid,path in [('aspect-chart','Origins_8_Aspect.jpg'),('pronoun-chart','Origins_6_Pronoun_Chart.jpg'),('correlative-chart','Origins_7_Table_of_Correlatives.jpg'),('clitic-chart','Inventory of Clitics.jpg'),('venik-instructions','Versions Best/Instructions - Venik.docx'),('scraps','Versions Rough/Scraps.docx'),('calque','Versions Rough/Calque - loan translation.docx')]:
        f=root/'Inputs'/path
        if f.exists(): data['sources'].append(dict(base(sid,path,None,''),path=path,sha256=file_hash(f),kind='docx' if f.suffix=='.docx' else 'image'))
    mapping=load_json(root/'data/orthography/thimfora-79.json')
    texts=[r['text'].replace(chr(190),chr(8217)) for r in data['corpus']]
    lexical=defaultdict(Counter)
    for r in data['lexicon']:
        group=' / '.join(r['variants'][0]['sourceFonts']) if r['variants'] else 'unknown'
        lexical[group].update(r['headword'])
    result['research']=dict(sourceInventory=inventory,
        scope='All substantive DOCX text inventoried. Native PSD/INDD/FontLab and legacy DOC containers retain unresolved content; four grammar charts visually reviewed. No claim that every raster or native file has been linguistically decoded.',
        frequencies=dict(method='Canonical letter identities fold maxima/minima only via the 79 mapping, never Unicode casefold. Two polished running-text witnesses counted once. Dictionary counts are type samples, not speech frequencies. Historical faces remain separate; unknowns are reported. Artificial kerning/alphabet specimens and English dictionary contents excluded.',
            polishedRunningText=symbol_frequency(texts,mapping),
            archiveSlotCounts={font:{f'U+{ord(c):04X}':n for c,n in counts.most_common()} for font,counts in buckets.items()},
            dictionarySlotCounts={font:{f'U+{ord(c):04X}':n for c,n in counts.most_common()} for font,counts in lexical.items()}))
    for r in data['grammar']:
        result['wiki'].append(dict(id=r['id'],title=r['label'],body='# '+r['label']+'\n\nEvidence status: **'+r['status']+'**. This is a source description, not editorial acceptance.\n\n'+r['statement']+'\n\n'+r['notes']+'\n\nSources: '+str(r['citations']),ruleIds=[r['id']]))
    validate(result);return result


def proposal(archive,root):
    """Extrapolation 0.1: a reversible editorial choice, never a silent correction."""
    result=deepcopy(archive);data=result['language'];lookup={r['id']:r for r in data['lexicon']}
    # Named historical letters (Instructions - Venik) -> chart-2 minima slots.
    # This is an editorial encoding adaptation; source records stay verbatim.
    venik={236:195,238:197,239:199,241:201,243:203,242:205,244:207,246:209,245:211,250:213,249:215,251:217,252:219,8224:221,176:223,162:225,163:227,167:229,8226:231,182:233,223:235}
    curated={}
    for word,rownum in [('learn',108),('read',142),('write',194),('remember',146),('see',151),('story',284),('build',27),('know',104)]:
        original=lookup[f'chart-1.t0.r{rownum}'];r=deepcopy(original);r['id']='forge.'+word
        r['headword']=''.join(chr(venik.get(ord(c),ord(c))) for c in original['headword']);r['orthographyId']='thimfora-79';r['status']='draft'
        r['citations'] += [dict(sourceId='venik-instructions',locator='named letter inventory'),dict(sourceId='mapping-79',locator='chart-2 minima slots')]
        r['senses'][0].update(id=r['id']+'.sense1',status='draft');r['notes']='Proposed chart-2 encoding adaptation by named letter identity. Meaning/root attested in cited chart; the current spelling is editorial. IPA is not inferred.'
        data['lexicon'].append(r);curated[word]=r['headword']
    # Promote selected polished forms into explicit proposed lexemes, with their
    # derivational segmentation documented rather than marked as attested roots.
    first=data['corpus'][0]['text'].replace(chr(190),chr(8217)).split();second=data['corpus'][1]['text'].replace(chr(190),chr(8217)).split()
    forms={'I':first[1],'we':first[4],'be':first[2][:-5], 'jewel':second[1].split('’')[1][:-3],
           'beauty':second[13].split('’')[1][:-3], 'it':second[15], 'possess':second[16][:-4],
           'for':second[12],'blue':second[2].split('’')[0],'fragile':second[14].split('’')[0]}
    # A finite form ends in ow+ya (four slots), punctuation is removed above.
    forms['be']=first[2].rstrip('.')[:-4]
    meanings={'I':'I, singular subject','we':'we, collective singular subject (proposed interpretation)','be':'be (copular verb)','jewel':'jewel','beauty':'beauty, a quality','it':'it, inanimate singular subject','possess':'possess','for':'for, because (causative conjunction)','blue':'blue','fragile':'fragile'}
    for word,form in forms.items():
        r=dict(base('forge.'+word,meanings[word],'polished','paragraphs 0/2 or 17/19; proposed segmentation','draft'),headword=form,orthographyId='thimfora-79',pronunciation='',ipa='',partOfSpeech='pronoun' if word in ('I','we','it') else 'verb' if word in ('be','possess') else 'noun' if word in ('jewel','beauty') else 'conjunction' if word=='for' else 'modifier',senses=[dict(id='forge.'+word+'.sense1',definition=meanings[word],status='draft',citations=[dict(sourceId='polished',locator='gloss paragraphs 2, 19')])],variants=[],etymology='Proposed extraction from an attested glossed construction.',exampleIds=[],audioLinks=[])
        data['lexicon'].append(r)
    curated.update(forms)
    rules=[
      ('order','Clause order and case','construction','Use object/predicate–subject–verb as the neutral order in this draft. Noun direct objects take -get; lexical subjects take -lÄy (chart-2 slots lÉy). Pronouns use their subjective forms. This generalizes the polished examples; it is not proof that other orders are impossible.','polished'),
      ('tense','Tense and aspect','tense','Verb = root + tense + aspect. Adopt -iz general past, -ow present, -at general future, -diz distant past, -riz immediate past, -dat immediate future, -rat distant future. Prefer the prose table and transliteration examples for the conflicting future pair. Use -ya simple, -am progressive, -fu perfect. The chart also lists compound aspect contractions; these remain under review. Bare infinitives are licensed only as dictionary citation forms in this draft.','hadthem'),
      ('nominals','Nominal classes and modifiers','construction','Retain noun classes and overt conversion clitics. Use the polished thing determiner with count nouns and the quality determiner with beauty; -get marks the object. Count-noun modifiers follow the noun and take the attested count-modifier clitic. The clitic chart distinguishes mass, count, collective and title nouns; do not collapse those distinctions into English articles.','polished'),
      ('pronouns','Collective we and pronoun paradigms','pronouns','Interpret the attested we(singular) as a collective singular speaker group for this branch. The pronoun chart explicitly distinguishes we(pr), we(d), we(s); their exact pragmatic scope is unresolved. Use only I, collective we and inanimate singular it in the first novel test. Do not infer the complete person/number paradigm from these three forms.','pronoun-chart'),
      ('orthography','Encoding and sound','phonology','Thimfora 79 chart 2 is the adopted display inventory: 47 letter identities with maxima/minima. Historical font slots are not Unicode phonetic values. Adapt U+00BE to U+2019 only in the review edition as in the approved page. Venik spellings used in the demo are mapped by named letter correspondence. Unresolved readings remain unknown; no invented IPA, stress rules or phonotactic constraints.','mapping-79'),
      ('correlatives','Correlatives, negation and open questions','construction','The correlative chart distinguishes action, quality, reason, time, location, manner, quantity, human association, thing identity and truth. Definitive and indefinite prefixes and an interrogative pattern are visible; several columns are blank. Retain the gaps. The polished clause supplies a causative conjunction. Internal/external negation and passive derivations need further source alignment before productive generalization.','correlative-chart'),
      ('lexicon','Dictionary policy and frequency','other','Keep original chart entries and stable sense IDs. Proposed current spellings are separate records with source links. Prefer attested roots and transparent inflections over randomly generated syllables. Measure running-text token frequencies separately from dictionary type counts and historical font slots. The tiny surviving corpus cannot establish population frequencies or justify smoothing away rare letters.','chart-1'),
    ]
    for key,title,topic,statement,source in rules:
        rid='forge.rule.'+key
        data['grammar'].append(dict(base(rid,title,source,'M7 source review and explicit branch proposal','draft'),topic=topic,statement=statement,morphologyIds=[],exampleIds=[],alternatives=[]))
        result['wiki'].append(dict(id=key,title=title,body='# '+title+'\n\n**Extrapolation 0.1 — proposed, not yet accepted by the language author.**\n\n'+statement+'\n\nSource: `'+source+'`. Historical witnesses remain in the dictionary and original archive version.\n\n## Test scope\nThe novel paragraph test exercises only its declared subset. Rendering success does not validate general grammar.',ruleIds=[rid]))
    result['decisions']=[dict(id='future-adjudication',choice='dat immediate / rat distant',evidence='hadthem table + transliteration; script example disagrees',status='proposed'),dict(id='collective-we',choice='collective singular reading, not a typo correction',evidence='polished gloss plus pronoun chart we(s)',status='proposed'),dict(id='dictionary-inspiration',choice='Stable senses, source witnesses, pronunciation separate from spelling, contextual examples and independent frequency measures; no wholesale vocabulary borrowing',status='proposed')]
    # Novel, compositional clauses; nothing here is claimed as archival prose.
    thing=second[1].split('’')[0]+'’';quality=second[13].split('’')[0]+'’';acc='get';nom=second[1][-3:];modifier='’'+second[2].split('’')[1]
    story=thing+curated['story']+acc;jewel=thing+curated['jewel']+acc
    I=curated['I'];we=curated['we'];it=curated['it']
    p1=f"{I} {curated['learn']}owya. {story} {I} {curated['read']}owya. {story} {we} {curated['write']}owya {curated['for']} {we} {curated['learn']}owya. {story} {we} {curated['remember']}owya. {story} {I} {curated['read']}atya. {story} {we} {curated['write']}atya {curated['for']} {we} {curated['learn']}atya. {story} {I} {curated['know']}owya."
    p2=f"{jewel} {curated['blue']+modifier} {I} {curated['see']}izya. {quality+curated['beauty']+acc} {curated['fragile']+modifier} {it} {curated['possess']}owya. {story} {we} {curated['remember']}owya. {story} {we} {curated['read']}owya {curated['for']} {jewel} {we} {curated['remember']}owya. {jewel} {curated['blue']+modifier} {I} {curated['see']}atya. {jewel} {we} {curated['remember']}atya. {we} {curated['learn']}owya."
    result['tests']=[dict(id='novel-learning-and-jewel',title='Learning, memory and a blue jewel',ruleIds=['forge.rule.'+k for k in ('order','tense','nominals','pronouns','orthography')],paragraphs=[
        dict(text=p1,translation='I learn. I read a story. We write a story, for we learn. We remember a story. I will read a story. We will write a story, for we will learn. I know a story.',analysis='I + learn-PRESENT-SIMPLE. THING-story-ACC + I + read-PRESENT-SIMPLE. THING-story-ACC + collective-we + write-PRESENT-SIMPLE + because + collective-we + learn-PRESENT-SIMPLE. Subsequent clauses use the same object-subject-verb order; -at- replaces -ow- for future simple. Root/encoding adaptations are proposed; no automated translator.'),
        dict(text=p2,translation='I saw a blue jewel. It possesses a fragile beauty. We remember a story. We read a story, for we remember a jewel. I will see a blue jewel. We will remember a jewel. We learn.',analysis='THING-jewel-ACC + blue-COUNT.MOD + I + see-PAST-SIMPLE. QUALITY-beauty-ACC + fragile-COUNT.MOD + it + possess-PRESENT-SIMPLE. THING-story-ACC + collective-we + remember-PRESENT-SIMPLE. Remaining clauses reuse the stated case/tense/aspect patterns; causative for links two complete clauses.')])]
    mapping=load_json(Path(root)/'data/orthography/thimfora-79.json');frequencies=result['research']['frequencies']
    frequencies['proposedNovelText']=symbol_frequency([p1,p2],mapping)
    frequencies['proposedDictionary']=symbol_frequency([r['headword'] for r in data['lexicon'] if r['id'].startswith('forge.')],mapping)
    running=frequencies['polishedRunningText'];rows=sorted(running['letters'],key=lambda r:-r['count'])
    table='\n'.join('| '+r['symbolId']+' | '+r['name']+' | '+str(r['count'])+' | '+f"{r['fraction']*100:.2f}%"+' |' for r in rows)
    result['wiki'].append(dict(id='frequency',title='Letter frequencies and evidence coverage',body='# Letter frequencies\n\n'+frequencies['method']+'\n\n'+str(running['letterCount'])+' mapped letters in two polished witnesses; not a language-wide estimate.\n\n| Identity | Name | Count | Share |\n|---|---|---:|---:|\n'+table+'\n\nNovel text and proposed dictionary distributions are frozen alongside this table in Research. New prose uses attested roots; it is not forced to imitate an unstable target distribution.',ruleIds=['forge.rule.lexicon']))
    validate(result);return result
