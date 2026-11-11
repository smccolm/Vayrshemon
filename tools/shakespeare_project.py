"""Source accounting and authored analysis for the remaining Shakespeare corpus.

This tool never translates English. Missing analyses remain explicitly pending.
One shared project holds small lexical deltas; the published 0.13 stays intact.
"""
from pathlib import Path
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
import argparse,hashlib,html,json,re,shutil
from tools.editorial_language import ROOT,EditorialLanguage,load_current
from tools.unta_language import candidates,quantity,semantic_key

PROJECT=ROOT/'Saves/Shakespeare Project 0.13'
SOURCES=ROOT/'Inputs/Sources'
DONE={'a-midsummer-nights-dream','alls-well-that-ends-well'}
POEMS={'the-phoenix-and-turtle','venus-and-adonis','lucrece','shakespeares-sonnets'}
VERSION='0.14'
SEALED_BIBLE = {
    'version': '0.10-kjv.285',
    'package': 'data/language/archaic-kjv-285',
    'manifestSha256': '83e2e7907369b018bd1efe146e6d2992fc35469dc6e4466e397fb560e1205b13',
    'forgeHead': '96013d286fdcac0297b671bc9ca7974bb05f6dbbe73139eaba53863c2f049678',
}
SHAKESPEARE_JESUS = re.compile(r"(?<!\w)(?:[ij]h?es(?:hu|u)s?|cheshu)(?!\w)", re.I)
READING_LABELS={'dep':'dep.','add':'add.','cont':'cont.','subend':'sub.end.',
                'relpair':'rel.2','reltriple':'rel.3','relquad':'rel.4'}

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def source_units(path):
    lines=path.read_text(encoding='utf-8-sig').splitlines()
    slug=path.name.removesuffix('_TXT_FolgerShakespeare.txt')
    metadata_end=next(i for i,s in enumerate(lines) if s.startswith('Created on '))+1
    if slug in POEMS:
        start=next(i for i in range(metadata_end,len(lines)) if lines[i].strip())
    else:
        # The first triple-newline division after the dramatis personae ends
        # the editorial cast list. Include prologues/induction before Act 1.
        cast=next(i for i,s in enumerate(lines) if s=='Characters in the Play')
        end=next(i for i in range(cast+2,len(lines)-1) if not lines[i].strip() and not lines[i+1].strip())
        start=next(i for i in range(end,len(lines)) if lines[i].strip())
        if slug == 'troilus-and-cressida':
            # The quarto address follows the cast with just one blank line.
            # Its final double blank introduces the armored Prologue.
            address = 'A never writer to an ever reader: news.'
            start = next((i for i in range(cast+2,start) if lines[i].strip() == address), start)
    units=[];current=[];section='Opening';excluded=list(range(1,start+1))
    def flush():
        if not current:return
        nums,content=zip(*current)
        units.append(dict(id=f'{len(units)+1:05d}',section=section,lineStart=nums[0],lineEnd=nums[-1],
                          lineNumbers=list(nums),rawSource='\n'.join(content),source=' '.join(s.strip() for s in content)))
        current.clear()
    for i in range(start,len(lines)):
        line=lines[i]
        if not line.strip():flush();continue
        if re.fullmatch(r'[=]{3,}',line.strip()):excluded.append(i+1);continue
        if re.fullmatch(r'ACT \d+|INDUCTION|PROLOGUE|EPILOGUE|Threnos',line.strip()):
            flush();section=line.strip()
        current.append((i+1,line))
    flush()
    actual=[n for u in units for n in u['lineNumbers']]
    expected=[i+1 for i in range(start,len(lines)) if lines[i].strip() and i+1 not in excluded]
    assert actual==expected and len(actual)==len(set(actual))
    return dict(slug=slug,title=lines[0],sourcePath=str(path.relative_to(ROOT)).replace('\\','/'),
                sourceSha256=sha(path),bodyStartLine=start+1,excludedLineNumbers=excluded,
                exclusionReason='Modern editorial metadata/cast list before dramatic opening; decorative equals separators. Poems retain authorial dedication, argument, epigraph and attribution.',
                sourceBodyNonblankLines=len(expected),sourceWords=sum(len(u['source'].split()) for u in units),units=units)

def init():
    _,pin=load_current();assert pin['version']=='0.13'
    assert not (PROJECT/'project.json').exists(),'Already initialized'
    works=[]
    for path in sorted(SOURCES.glob('*_TXT_FolgerShakespeare.txt')):
        parsed=source_units(path)
        if parsed['slug'] in DONE:continue
        write(PROJECT/'Sources'/(parsed['slug']+'.json'),parsed)
        works.append({k:v for k,v in parsed.items() if k!='units'}|dict(sourceUnits=len(parsed['units']),translatedUnits=0,reviewedUnits=0,status='pending',output=None))
    write(PROJECT/'project.json',dict(status='incomplete',base=pin,workingVersion=VERSION,sealedBible=SEALED_BIBLE,
        scope='Every remaining Folger Shakespeare source file, including all four poetry sources; one complete native file per source.',
        publishedExisting=sorted(DONE),works=works,inheritReviewedBibleNames=True,inheritReviewedBibleVocabulary=True))
    write(PROJECT/'lexical-delta.json',dict(entries={},glosses={},decisions=[],sealedBible=SEALED_BIBLE,
         inheritReviewedBibleNames=True,inheritReviewedBibleVocabulary=True,normalizeStoredRomanSlots=True))
    (PROJECT/'README.txt').write_text('INCOMPLETE CORPUS PROJECT\nStarts from pinned 0.13. One shared language workspace and one ledger per source.\nSource indexing is not translation. project.json records exact translated/reviewed coverage.\nDo not duplicate full Forge history or Language Development folders per checkpoint.\nCompleted Bibles and prior 0.13 plays remain unchanged. Cleanup audit follows corpus verification.\n',encoding='utf-8')
    materialize();progress()

def materialize():
    project=read(PROJECT/'project.json');base=ROOT/project['base']['package']
    return write_working_language(base,read(PROJECT/'lexical-delta.json'),PROJECT/'Language')

@lru_cache(maxsize=4)
def sealed_name_readings(package, manifest_sha, head):
    manifest_path = package / 'manifest.json'
    if sha(manifest_path) != manifest_sha:
        raise ValueError('The sealed Bible manifest does not match its recorded hash')
    manifest = read(manifest_path)
    if manifest['forgeHead'] != head:
        raise ValueError('The sealed Bible language head has changed')
    for filename in ('name-forms.json', 'display-labels.json'):
        if sha(package / filename) != manifest['files'][filename]:
            raise ValueError('Bible name witness mismatch: ' + filename)
    labels = read(package / 'display-labels.json')
    names = read(package / 'name-forms.json')
    return ({key: (record, labels[key]['after']) for key, record in names.items()},
            {key: row['after'] for key, row in labels.items() if 'jesus' in key.split('_')})

@lru_cache(maxsize=4)
def reviewed_bible_names(package, manifest_sha, head):
    sealed_name_readings(package, manifest_sha, head)
    files = read(package/'manifest.json')['files']
    for filename in ('vocabulary-review.json', 'lexicon.json', 'morphology.json'):
        if sha(package/filename) != files[filename]:
            raise ValueError('Sealed vocabulary witness mismatch: ' + filename)
    lexicon = read(package/'lexicon.json')['entries']
    glosses = read(package/'morphology.json')['glosses']
    result = {}
    for key, change in read(package/'vocabulary-review.json')['entries'].items():
        if change['kind'] not in ('localized name', 'native affiliation'):
            continue
        # These two inherited dramatic identities are John Drum and Peter Quince.
        # Scripture's several Johns and Peters have separately keyed entries.
        if key in ('john', 'peter'):
            continue
        entry = lexicon[key]
        if (entry['form'], entry['roman']) != (change['after'], change['afterRoman']):
            raise ValueError('Inconsistent sealed name change: ' + key)
        result[key] = (entry, glosses.get(key, key.capitalize()))
    return result

def inherit_reviewed_bible_names(lexicon, glosses, witness):
    for key, (record, label) in reviewed_bible_names(ROOT/witness['package'], witness['manifestSha256'], witness['forgeHead']).items():
        entry = lexicon[key]
        if (entry['semanticId'],entry['pos']) != (record['semanticId'],record['pos']):
            raise ValueError('Biblical referent mismatch: ' + key)
        entry.update(form=record['form'], roman=record['roman'], nameWitness=witness['version'])
        glosses[key] = label

@lru_cache(maxsize=4)
def reviewed_bible_vocabulary(package, manifest_sha, head):
    reviewed_bible_names(package, manifest_sha, head)
    entries = read(package/'lexicon.json')['entries']
    reviewed = read(package/'vocabulary-review.json')['entries']
    return {key:(change,entries[key]) for key,change in reviewed.items()
            if change['kind'] not in ('localized name','native affiliation')}

def inherit_reviewed_bible_vocabulary(lexicon, witness):
    reviewed = reviewed_bible_vocabulary(ROOT/witness['package'], witness['manifestSha256'], witness['forgeHead'])
    updated = []
    for key,(change,record) in reviewed.items():
        item = lexicon.get(key)
        if item is None or item['form'] != change['before']:
            continue
        if item['semanticId'] != record['semanticId'] or record['form'] != change['after']:
            raise ValueError('Inconsistent sealed lexical correction: '+key)
        item.update(form=record['form'],roman=record['roman'],derivationKeys=record.get('derivationKeys',[]),
                    lexicalWitness=witness['version'])
        updated.append(key)
    return updated

def inherit_sealed_reading_slots(roman, witness):
    package = ROOT/witness['package']
    manifest = read(package/'manifest.json')
    path = package/'orthography.json'
    if sha(path) != manifest['files']['orthography.json'] or sha(package/'manifest.json') != witness['manifestSha256']:
        raise ValueError('Sealed Bible orthography has changed')
    for slot, reading in read(path)['romanBySlot'].items():
        if slot in roman and roman[slot] != reading:
            raise ValueError('Incompatible historical reading for slot '+slot)
        roman[slot] = reading

def check_shakespeare_name(source, native, gloss):
    count = len(SHAKESPEARE_JESUS.findall(source))
    if SHAKESPEARE_JESUS.search(native) or SHAKESPEARE_JESUS.search(gloss):
        raise ValueError('A translated column contains an unlocalized Jesus name')
    if native.count('YeÛça') < count or gloss.count('Yeshūa') < count:
        raise ValueError('An invocation in the Shakespeare source is missing the sealed Yeshūa reading')

def write_working_language(base,delta,target):
    target.mkdir(parents=True,exist_ok=True)
    lex=read(base/'lexicon.json');morph=read(base/'morphology.json')
    for key,entry in delta['entries'].items():
        assert key not in lex['entries'],'Never silently replace a published semantic key'
        lex['entries'][key]=entry
    morph['glosses'].update(delta['glosses']);lex['version']=VERSION
    # A checkpoint made before adoption of the sealed names must still reproduce byte for byte.
    witness = delta.get('sealedBible')
    if delta.get('inheritReviewedBibleVocabulary'):
        if not witness:
            raise ValueError('Reviewed biblical vocabulary requires a sealed Bible witness')
        inherit_reviewed_bible_vocabulary(lex['entries'], witness)
    if delta.get('inheritReviewedBibleNames'):
        if not witness:
            raise ValueError('Reviewed biblical names require a sealed Bible witness')
        inherit_reviewed_bible_names(lex['entries'], morph['glosses'], witness)
    if witness:
        readings, related_labels = sealed_name_readings(ROOT / witness['package'], witness['manifestSha256'], witness['forgeHead'])
        for key, (name, label) in readings.items():
            entry = lex['entries'][key]
            if entry['semanticId'] != name['semanticId'] or entry['pos'] != 'proper':
                raise ValueError('Bible name identity mismatch: ' + key)
            entry.update(form=name['after'], roman=name['afterRoman'], nameWitness=witness['version'])
            morph['glosses'][key] = label
        for key, label in related_labels.items():
            if lex['entries'][key]['pos'] != 'proper':
                raise ValueError('Expected a distinct biblical person: ' + key)
            morph['glosses'][key] = label
    # Reading-column labels are abbreviations, not internal research prose.
    # Only the new working package changes; published books stay immutable.
    for key,label in READING_LABELS.items():morph['suffixes'][key][1]=label
    if delta.get('inheritReviewedBibleNames'):
        orthography = read(base/'orthography.json')
        inherit_sealed_reading_slots(orthography['romanBySlot'], witness)
        if delta.get('normalizeStoredRomanSlots'):
            slots = orthography['romanBySlot']
            for record in lex['entries'].values():
                roman = record.get('roman', '')
                if 'Õ' in roman or 'Ô' in roman:
                    record['roman'] = roman.replace('Õ', slots['Õ']).replace('Ô', slots['Ô'])
        write(target/'orthography.json', orthography)
    else:
        shutil.copyfile(base/'orthography.json',target/'orthography.json')
    write(target/'lexicon.json',lex);write(target/'morphology.json',morph)
    return EditorialLanguage(target)

def authored_source_rows(source,authored):
    """Select a consecutive exact source prefix, at authored line or character boundaries."""
    byid={u['id']:u for u in source['units']};units=[];coverage={}
    order=[u['id'] for u in source['units']];source_index=0;next_offset=0
    assert len({u['id'] for u in authored})==len(authored)
    for row in authored:
        assert not set(row)&{'source','rawSource','lineNumbers','lineStart','lineEnd'},'Source text is selected by original lines, never overwritten'
        sid=row.get('sourceId',row['id']);u=deepcopy(byid[sid])
        raw=u['rawSource'];available=u['lineNumbers'];line_chunks=raw.splitlines(keepends=True)
        offsets=[0]
        for chunk in line_chunks:offsets.append(offsets[-1]+len(chunk))
        start,end=0,len(raw)
        assert not ('sourceLines' in row and 'sourceOffsets' in row),'Use one source selector'
        if 'sourceLines' in row:
            numbers=row['sourceLines']
            assert numbers and all(type(n)==int for n in numbers)
            first=available.index(numbers[0]);assert available[first:first+len(numbers)]==numbers
            start,end=offsets[first],offsets[first+len(numbers)]
            selected=dict(zip(available,u['rawSource'].splitlines()))
            u.update(id=row['id'],sourceId=sid,lineStart=numbers[0],lineEnd=numbers[-1],
                     lineNumbers=numbers,rawSource='\n'.join(selected[n] for n in numbers),
                     source=' '.join(selected[n].strip() for n in numbers))
        elif 'sourceOffsets' in row:
            span=row['sourceOffsets'];assert len(span)==2 and all(type(n)==int for n in span)
            start,end=span;assert 0<=start<end<=len(raw)
            # Do not permit a slice through a source token; punctuation-boundary
            # decisions still belong to the translator, never an automatic splitter.
            for boundary in (start,end):
                assert boundary in (0,len(raw)) or raw[boundary-1].isspace() or raw[boundary].isspace(),'SOURCE_TOKEN_SPLIT'
            numbers=[n for i,n in enumerate(available) if offsets[i]<end and offsets[i+1]>start]
            selected=raw[start:end];assert selected.strip()
            u.update(id=row['id'],sourceId=sid,lineStart=numbers[0],lineEnd=numbers[-1],
                     lineNumbers=numbers,rawSource=selected,
                     source=' '.join(line.strip() for line in selected.splitlines()).strip())
        else:assert row['id']==sid
        assert source_index<len(order) and sid==order[source_index] and start==next_offset,'Authored units must cover a consecutive, nonduplicated exact source prefix'
        coverage[sid]=end;next_offset=end
        if end==len(raw):source_index+=1;next_offset=0
        units.append((u,row))
    complete=sum(coverage.get(u['id'],0)==len(u['rawSource']) for u in source['units'])
    lines=0
    for u in source['units']:
        offset=0
        for chunk in u['rawSource'].splitlines(keepends=True):
            offset+=len(chunk)
            if offset<=coverage.get(u['id'],0):lines+=1
    return units,complete,lines

def source_number_notation(source, note):
    """Number words and figures retain their source notation in Unta."""
    text = note['text']
    if note.get('sourceNotation') != 'roman-regnal':
        return 'digits' if re.search(r'\d', text) else 'words'
    # Review the complete royal designation so the pronoun I and letter names
    # elsewhere in a speech are never interpreted as regnal numbers.
    match = re.fullmatch(r"([A-Z][A-Za-z'’-]*) ([IVXLCDM]+)", text)
    value = Fraction(note['value'])
    assert match and value.denominator == 1 and 1 <= value <= 3999, ('INVALID_REGNAL_FIGURE', text)
    assert re.search(r'(?<!\w)' + re.escape(text) + r'(?!\w)', source), ('REGNAL_NAME_NOT_IN_SOURCE', text)
    remainder = int(value)
    roman = ''
    for amount, letters in ((1000,'M'), (900,'CM'), (500,'D'), (400,'CD'), (100,'C'), (90,'XC'),
                            (50,'L'), (40,'XL'), (10,'X'), (9,'IX'), (5,'V'), (4,'IV'), (1,'I')):
        count, remainder = divmod(remainder, amount)
        roman += letters * count
    assert match[2] == roman, ('REGNAL_FIGURE_VALUE_MISMATCH', text, str(value))
    return 'digits'


def validate_numeric_review(source,row,lexicon):
    # Compare whole analysis keys: a word-form key is also the prefix of its
    # digit-form sibling. Possessive and inflected keys still count as uses.
    analysis_keys = set(re.findall(r'[A-Za-z_]+', row['analysis']))
    if 'kjv_three' in analysis_keys:
        raise ValueError(f"{row['id']}: use the chart-based Unta form for three in this translation")
    flagged=candidates(source)
    numeric=row.get('numericReview',[])
    assert [r['text'] for r in numeric]==[r['text'] for r in flagged],('NUMERIC_REVIEW_REQUIRED',row['id'],flagged)
    # Human review also finds quantitative senses outside the candidate regex
    # (for example, moiety). Validate those explicitly without claiming that
    # a scanner enumerates every possible numerical expression.
    semantic=row.get('semanticQuantityReview',[])
    for note in semantic:
        term=note.get('text','')
        assert term and re.search(r'(?<!\w)'+re.escape(term)+r'(?!\w)',source,re.I),('SEMANTIC_QUANTITY_NOT_IN_SOURCE',row['id'],term)
        assert term.casefold() not in {r['text'].casefold() for r in flagged},('DUPLICATE_QUANTITY_REVIEW',row['id'],term)
    for note in numeric+semantic:
        assert note.get('decision')
        if note.get('key'):
            key=note['key']
            assert key in analysis_keys and key in lexicon,('UNUSED_QUANTITY_KEY',row['id'],key)
            entry=lexicon[key]
            assert 'value' in note and 'numericValue' in entry,('QUANTITY_METADATA_REQUIRED',row['id'],key)
            assert Fraction(note['value'])==Fraction(entry['numericValue']),('QUANTITY_VALUE_MISMATCH',row['id'],note,entry['numericValue'])
            notation=source_number_notation(source,note)
            assert entry.get('numericNotation','words')==notation,('SOURCE_NUMBER_NOTATION_MISMATCH',row['id'],note['text'],key)

def compile_work(slug):
    lang=materialize();source=read(PROJECT/'Sources'/(slug+'.json'))
    assert sha(ROOT/source['sourcePath'])==source['sourceSha256']
    if 'drama_native_last' in lang.lexicon:
        work = next(w for w in read(PROJECT/'project.json')['works'] if w['slug'] == slug)
        if work['status'] != 'verified':
            from tools.shakespeare_native_vocabulary import prepare_manuscript_readings
            lang = prepare_manuscript_readings(slug, lang)
    authored=read(PROJECT/'Analyses'/(slug+'.json'))
    rows,complete,lines=authored_source_rows(source,authored)
    units=[]
    for u,row in rows:
        assert row.get('review') and row.get('backTranslation')
        validate_numeric_review(u['source'],row,lang.lexicon)
        assert not re.search(r'\d',row['analysis']),('USE_REVIEWED_UNTA_QUANTITY',row['id'])
        for key in ['twenty','thirty','forty','fifty','sixty','seventy','eighty','ninety','hundred','thousand','twice']:
            assert not re.search(r'(?<![A-Za-z_])'+key+r'(?![A-Za-z_])',row['analysis']),('USE_UNTA_DERIVATION',key)
        u.update(row);u['chapter']=u['section'];u['reference']=source['title']+' '+u['id']
        units.append(u)
    units=lang.compile_units(units)
    if lang.lexicon['kjv_jesus_matthew'].get('nameWitness'):
        from tools.shakespeare_endin import check_clean
        for unit in units:
            try:
                check_shakespeare_name(unit['source'], unit['text'], unit['gloss'])
                check_clean(unit,lang)
            except ValueError as error:
                raise ValueError(f"{slug} {unit['id']}: {error}") from error
    ledger=dict(book=source['title'],sourcePath=source['sourcePath'],sourceSha256=source['sourceSha256'],
        languageVersion=VERSION,editionLabel='Shakespeare from 0.13',sourceLabel='Shakespeare source',
        status='complete' if complete==len(source['units']) else 'incomplete',
        totalSourceUnits=len(source['units']),translatedUnits=complete,translatedSourceLines=lines,units=units)
    write(PROJECT/'Ledgers'/(slug+'.json'),ledger)
    p=read(PROJECT/'project.json');w=next(w for w in p['works'] if w['slug']==slug)
    reviewed=sum(all(row.get('reviewStatus')=='reviewed' for selected,row in rows
                     if selected.get('sourceId',selected['id'])==original['id'])
                 for original in source['units'][:complete])
    w.update(translatedUnits=complete,reviewedUnits=reviewed,
             status='translated-awaiting-layout' if ledger['status']=='complete' else 'translating')
    write(PROJECT/'project.json',p)
    # Keep the human-readable working resource current between complete-work commits.
    # This does not promote an unfinished source or pretend the additions are committed.
    wiki=PROJECT/'Wiki';wiki.mkdir(exist_ok=True)
    title=html.escape(source['title'])
    body='<meta charset="utf-8"><style>body{font:18px/1.6 Georgia;max-width:76ch;margin:3em auto}pre{white-space:pre-wrap}</style><h1>'+title+'</h1>'
    body+='<p>WORKING TRANSLATION · '+str(complete)+' / '+str(len(source['units']))+' source blocks. Native delivery and complete-work Forge commit are separate.</p>'
    for u in units:
        note=u['source']+'\n\nBack-translation: '+u['backTranslation']+'\n\nReview: '+u['review']
        if u.get('numericReview'):note+='\n\nNumeric decisions: '+json.dumps(u['numericReview'],ensure_ascii=False)
        if u.get('semanticQuantityReview'):note+='\n\nAdditional quantitative senses: '+json.dumps(u['semanticQuantityReview'],ensure_ascii=False)
        if u.get('research'):note+='\n\nResearch: '+json.dumps(u['research'],ensure_ascii=False)
        body+='<h2>'+html.escape(u['id'])+'</h2><pre>'+html.escape(note)+'</pre>'
    (wiki/(slug+'-working.html')).write_text(body,encoding='utf-8')
    delta=read(PROJECT/'lexical-delta.json')
    write(PROJECT/'Dictionary-working-delta.json',dict(version=VERSION,status='working additions; not a published language release',
        baseVersion=p['base']['version'],lastCommittedHead=p.get('forgeHead'),entries=delta['entries'],decisions=delta['decisions']))
    print(slug,complete,'/',len(source['units']),'source blocks compiled;',len(units),'authored layout units',flush=True)

def register_quantity(value,kind='cardinal',denominator=1,*,notation='words'):
    lang=materialize();q=quantity(value,kind,denominator,notation=notation);key=semantic_key(value,kind,denominator,notation=notation)
    delta=read(PROJECT/'lexical-delta.json')
    entry=dict(form=q['form'],roman=lang.reading(q['spokenForm']),meaning=f"Exact {kind} quantity {q['value']}; Unta {q['base12']}.",
        pos='numeral',semanticId='lex.'+key,usageScope='later-standard',status='authored',
        origin='Origins_3_Unta_2 chart and explicit quantitative construction; '+q['evidence'],
        numericValue=q['value'],numericKind=kind,numericNotation=notation,base12=q['base12'],historicalForms=[],derivationKeys=[])
    if key in delta['entries']:
        old=deepcopy(delta['entries'][key]);old.setdefault('numericNotation','words')
        assert old==entry
        if old!=delta['entries'][key]:
            delta['entries'][key]=old;write(PROJECT/'lexical-delta.json',delta)
    else:
        labels={'cardinal':q['value'],'ordinal':q['value']+'(ord.)',
                'times':q['value']+'×','fold':q['value']+'-fold','fraction':q['value']}
        delta['entries'][key]=entry;delta['glosses'][key]=labels[kind]
        write(PROJECT/'lexical-delta.json',delta)
    return key

def progress():
    p=read(PROJECT/'project.json');works=p['works']
    print(json.dumps(dict(remainingSources=len(works),sourceUnits=sum(w['sourceUnits'] for w in works),
        sourceWords=sum(w['sourceWords'] for w in works),translatedUnits=sum(w['translatedUnits'] for w in works),
        completedNativeFiles=sum(w['status']=='verified' for w in works)),indent=2))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['init','compile','progress']);ap.add_argument('--work')
    a=ap.parse_args()
    if a.action=='init':init()
    elif a.action=='compile':compile_work(a.work)
    else:progress()
