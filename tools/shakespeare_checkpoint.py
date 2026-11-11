"""One shared Forge branch and small source-linked translation checkpoints."""
from copy import deepcopy
from pathlib import Path
import argparse,html,json
from tools.shakespeare_project import PROJECT,ROOT,VERSION,read,write,sha,materialize,sealed_name_readings,reviewed_bible_names

BRANCH='shakespeare-from-0.13'

def attach_bible_readings(snapshot, language, delta):
    from vayrshemon.archive_language import base
    witness = delta['sealedBible']
    snapshot['research']['sealedBible'] = deepcopy(witness)
    source_id = 'shakespeare014.bible.' + witness['version']
    if not any(row['id'] == source_id for row in snapshot['language']['sources']):
        snapshot['language']['sources'].append(dict(base(source_id, 'Sealed Vayrshemon Bible', None, '', status='draft'),
            kind='other', path=witness['package']+'/manifest.json', sha256=witness['manifestSha256']))
    args = ROOT/witness['package'], witness['manifestSha256'], witness['forgeHead']
    readings, related_labels = sealed_name_readings(*args)
    if delta.get('inheritReviewedBibleNames'):
        readings = {**reviewed_bible_names(*args), **readings}
    ids = {entry['id'] for entry in snapshot['language']['lexicon']}
    for key, (_, label) in readings.items():
        eid = 'shakespeare014.biblical-name.' + key
        if eid in ids:
            continue
        entry = language.lexicon[key]
        snapshot['language']['lexicon'].append(dict(base(eid, label, source_id, entry['meaning'], status='draft'),
            headword=entry['form'], orthographyId='thimfora-79', pronunciation=entry['roman'], ipa='',
            partOfSpeech=entry['pos'], senses=[dict(id=eid+'.sense', definition=entry['meaning'], status='draft',
                citations=[dict(sourceId=source_id, locator=entry['semanticId'])])],
            variants=[], etymology='Author-approved reading from the sealed Bible', exampleIds=[], audioLinks=[]))
    return readings, related_labels

def attach_bible_vocabulary(snapshot, language, witness):
    from vayrshemon.archive_language import base
    from tools.shakespeare_endin import correct_forge_headwords
    source_id = 'shakespeare014.bible.'+witness['version']
    ids = {e['id'] for e in snapshot['language']['lexicon']}
    lexical = {k:e for k,e in language.lexicon.items() if e.get('lexicalWitness')}
    if lexical:
        correct_forge_headwords(snapshot, {k:language.lexicon[k] for k in ('last','final','kjv_omega_letter_revelation')})
    for key, entry in lexical.items():
        eid = 'shakespeare014.biblical-vocabulary.'+key
        if eid not in ids:
            snapshot['language']['lexicon'].append(dict(base(eid,language.glosses.get(key,key),source_id,entry['semanticId'],status='draft'),
                headword=entry['form'],orthographyId='thimfora-79',pronunciation=entry['roman'],ipa='',
                partOfSpeech=entry['pos'],senses=[dict(id=eid+'.sense',definition=entry['meaning'],status='draft',
                citations=[dict(sourceId=source_id,locator=entry['semanticId'])])],
                variants=[],etymology='Sealed Bible vocabulary review',exampleIds=[],audioLinks=[]))
    return lexical

def review_sections(units, limit=18000):
    """Keep complete source records together in bounded, readable wiki sections."""
    sections=[];current=[];size=0
    for unit in units:
        text=unit['id']+' · '+unit['source']+'\n\nBack-translation: '+unit['backTranslation']+'\n\nReview: '+unit['review']
        if unit.get('numericReview'):text+='\n\nNumeric decisions: '+json.dumps(unit['numericReview'],ensure_ascii=False)
        if unit.get('semanticQuantityReview'):text+='\n\nAdditional quantitative senses: '+json.dumps(unit['semanticQuantityReview'],ensure_ascii=False)
        if unit.get('research'):text+='\n\nResearch: '+json.dumps(unit['research'],ensure_ascii=False)
        if len(text)>limit:raise ValueError('REVIEW_UNIT_TOO_LONG: '+unit['id'])
        if current and size+2+len(text)>limit:
            sections.append(current);current=[];size=0
        current.append((unit['id'],text));size+=len(text)+(2 if len(current)>1 else 0)
    if current:sections.append(current)
    return sections

def commit_work(slug):
    from vayrshemon.forge import ForgeProject,validate
    from vayrshemon.archive_language import base
    metadata=read(PROJECT/'project.json');pin=metadata['base']
    path=ROOT/pin['forgeProject'];project=ForgeProject(path);status=project.status()
    ledger_path=PROJECT/'Ledgers'/(slug+'.json');ledger=read(ledger_path)
    assert ledger['status']=='complete'
    assert all(u.get('reviewStatus')=='reviewed' for u in ledger['units'])
    receipt=PROJECT/'Checkpoints'/(slug+'.json');revision=1
    while receipt.exists():
        assert read(receipt)['ledgerSha256']!=sha(ledger_path),'This exact ledger already has a checkpoint'
        revision+=1;receipt=PROJECT/'Checkpoints'/(slug+'-r'+str(revision)+'.json')
    previous=metadata.get('forgeHead',pin['forgeHead'])
    s=deepcopy(project.read(previous)['snapshot']);lang=materialize()
    delta=read(PROJECT/'lexical-delta.json');sid='shakespeare014.source.'+slug+'.r'+str(revision)
    rid='shakespeare014.review.'+slug+'.r'+str(revision)
    s['language']['sources'].append(dict(base(sid,ledger['book'],None,'',status='draft'),
        kind='other',path=str(ledger_path.relative_to(ROOT)).replace('\\','/'),sha256=sha(ledger_path)))
    sections=review_sections(ledger['units'])
    notes='\n\n'.join(text for section in sections for _,text in section)
    review_index='Complete source-linked translation review: '+str(ledger['translatedUnits'])+' original source blocks; '+str(len(ledger['units']))+' layout units.\n'+ '\n'.join(
        'Wiki '+slug+' review '+str(i+1)+': '+section[0][0]+'–'+section[-1][0] for i,section in enumerate(sections))
    s['language']['grammar'].append(dict(base(rid,ledger['book']+' · source decisions',sid,
        'Complete authored source review',status='draft'),topic='construction',statement=review_index,
        morphologyIds=[],exampleIds=[],alternatives=[]))
    ids={e['id'] for e in s['language']['lexicon']};added=[]
    witness = delta.get('sealedBible')
    if witness:
        readings, related_labels = attach_bible_readings(s, lang, delta)
    lexical_witness = attach_bible_vocabulary(s,lang,witness) if delta.get('inheritReviewedBibleVocabulary') else {}
    if delta.get('normalizeStoredRomanSlots'):
        for item in s['language']['lexicon']:
            key = item['id'].removeprefix('shakespeare014.lex.')
            if key in delta['entries'] and item['headword'] == lang.lexicon[key]['form']:
                item['pronunciation'] = lang.lexicon[key]['roman']
    for key,e in delta['entries'].items():
        eid='shakespeare014.lex.'+key
        if eid in ids:continue
        s['language']['lexicon'].append(dict(base(eid,key,sid,e['origin'],status='draft'),
            headword=e['form'],orthographyId='thimfora-79',pronunciation=e['roman'],ipa='',
            partOfSpeech=e['pos'],senses=[dict(id=eid+'.sense',definition=e['meaning'],status='draft',
            citations=[dict(sourceId=sid,locator='Authored lexical decision')])],
            variants=[],etymology=e['origin'],exampleIds=[],audioLinks=[]))
        added.append(key)
    project_note=(ROOT/'docs/SHAKESPEARE_PROJECT.md').read_text(encoding='utf-8')
    reading_note=('Reading gloss abbreviations: cont. = unmarked continuation; add. = additive clause; '
        'dep. = dependent pronoun; sub.end. = dependent-clause ending; rel.2/3/4 = relational chain length. '
        'Exact quantity values, bases and semantic decisions remain in the dictionary and numericReview; '
        'the reading column shows 20, 3(ord.), 3×, 3-fold or 1/3 without a repeated Unta metadata label. '
        'Source notation is preserved: digits use Unta numeral glyphs; number words use Unta words. '
        'Third is venik’t; source 3rd uses the Unta 3 glyph plus the same ordinal ending. '
        'The original paired-triangle radix sign is the colon font slot. '
        'These policies apply to new working editions; frozen Bibles stay unchanged.')
    for wid,title,body in [('shakespeare014-project','Shakespeare from 0.13 · ongoing project',project_note),
                            ('shakespeare014-reading','Readable construction glosses',reading_note),
                            ('shakespeare014-'+slug,ledger['book']+' · translation decisions',review_index)]:
        s['wiki']=[w for w in s['wiki'] if w['id']!=wid]
        s['wiki'].insert(0,dict(id=wid,title=title,body=body,ruleIds=[rid]))
    prefix='shakespeare014-'+slug+'-review-'
    s['wiki']=[w for w in s['wiki'] if not w['id'].startswith(prefix)]
    for i,section in enumerate(sections):
        s['wiki'].append(dict(id=prefix+str(i+1),title=ledger['book']+' · '+section[0][0]+'–'+section[-1][0],
            body='\n\n'.join(text for _,text in section),ruleIds=[rid]))
    # A few contrasting fixtures; full source and review stay in the hashed ledger.
    selected=[u for u in ledger['units'] if u.get('numericReview') or u.get('semanticQuantityReview') or ':excl' in u['analysis']]
    selected=(ledger['units'][:1]+selected+ledger['units'][-1:])[:12]
    for u in selected:
        tid='shakespeare014.'+slug+'.'+u['id'];s['tests']=[t for t in s['tests'] if t['id']!=tid]
        s['tests'].append(dict(id=tid,title=ledger['book']+' '+u['id'],
            ruleIds=[rid],paragraphs=[dict(text=u['text'],translation=u['source'],analysis=u['gloss']+'\n'+u['analysis'])]))
    s['decisions'].append(dict(id=rid,status='proposed',choice='Authored source-linked translation; '+reading_note,
        evidence='Full ledger '+str(ledger_path.relative_to(ROOT))+' SHA256 '+sha(ledger_path)))
    s['research'].setdefault('shakespeare014',{})[slug]=dict(ledgerSha256=sha(ledger_path),
        sourceSha256=ledger['sourceSha256'],sourceUnits=ledger['translatedUnits'],
        layoutUnits=len(ledger['units']),status='translation reviewed; layout pending')
    validate(s)
    if BRANCH not in {b['name'] for b in status['branches']}:
        assert previous==pin['forgeHead']
        status=project.branch(BRANCH,status['generation'],version=previous)
    elif status['branch']!=BRANCH:status=project.checkout(BRANCH,status['generation'])
    assert status['head']==previous and not status['dirty'],'Do not replace unrecorded Forge work'
    status=project.replace_draft(s,status['generation'])
    status=project.commit(VERSION+' working · '+ledger['book']+' · reviewed source and Unta',status['generation'])
    head=status['head'];write(PROJECT/'current-snapshot.json',dict(head=head,snapshot=s))
    checkpoint=dict(work=slug,version=VERSION,head=head,parentHead=previous,baseVersion=pin['version'],
        ledgerSha256=sha(ledger_path),lexicalDeltaSha256=sha(PROJECT/'lexical-delta.json'),
        newSemanticKeys=added,compilerSha256=sha(ROOT/'tools/editorial_language.py'),
        untaHelperSha256=sha(ROOT/'tools/unta_language.py'),
        languageFiles={name:sha(PROJECT/'Language'/name) for name in ['lexicon.json','morphology.json','orthography.json']})
    if witness:
        checkpoint['sealedBible'] = witness
        if delta.get('inheritReviewedBibleNames'):
            checkpoint['inheritReviewedBibleNames'] = True
        if lexical_witness:
            checkpoint['inheritReviewedBibleVocabulary'] = True
    write(receipt,checkpoint)
    # Small deltas preserve the exact checkpoint package without copying base/history.
    write(receipt.with_name(receipt.stem+'-lexical-delta.json'),delta)
    metadata['forgeHead']=head;metadata['forgeProject']=pin['forgeProject'];metadata['forgeBranch']=BRANCH
    write(PROJECT/'project.json',metadata)
    wiki=PROJECT/'Wiki';wiki.mkdir(exist_ok=True)
    page='<!doctype html><meta charset="utf-8"><title>'+html.escape(ledger['book'])+'</title><style>body{max-width:75ch;margin:3em auto;font:18px/1.6 Georgia}pre{white-space:pre-wrap}a{color:#17628a}</style>'
    (wiki/(slug+'.html')).write_text(page+'<h1>'+html.escape(ledger['book'])+'</h1><pre>'+html.escape(notes)+'</pre>',encoding='utf-8')
    (wiki/'Index.html').write_text(page+'<h1>Shakespeare · working language '+VERSION+'</h1><p>Corpus incomplete. Complete source review is separate from verified native publication.</p><pre>'+html.escape(project_note+'\n\n'+reading_note)+'</pre><p>'+''.join('<a href="'+html.escape(p.name)+'">'+html.escape(p.stem)+'</a><br>' for p in wiki.glob('*.html') if p.name!='Index.html')+'</p>',encoding='utf-8')
    dictionary=dict(basePackage=pin['package'],version=VERSION,head=head,entries=delta['entries'])
    if witness:
        dictionary.update(sealedBible=witness, inheritedNameReadings={key:lang.lexicon[key] for key in readings},
                          inheritedNameLabels=related_labels)
    if lexical_witness:
        dictionary['inheritedVocabulary'] = lexical_witness
    write(PROJECT/'Dictionary-delta.json',dictionary)
    print(json.dumps(dict(work=slug,head=head,newSemanticEntries=len(added),
        sourceUnits=ledger['translatedUnits'],layoutUnits=len(ledger['units'])),indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('work');a=p.parse_args();commit_work(a.work)
