"""Source accounting and authored analysis for the remaining Shakespeare corpus.

This tool never translates English. Missing analyses remain explicitly pending.
One shared project holds small lexical deltas; the published 0.13 stays intact.
"""
from pathlib import Path
from copy import deepcopy
from fractions import Fraction
import argparse,hashlib,html,json,re,shutil
from tools.editorial_language import ROOT,EditorialLanguage,load_current
from tools.unta_language import candidates,quantity,semantic_key

PROJECT=ROOT/'Saves/Shakespeare Project 0.13'
SOURCES=ROOT/'Inputs/Sources'
DONE={'a-midsummer-nights-dream','alls-well-that-ends-well'}
POEMS={'the-phoenix-and-turtle','venus-and-adonis','lucrece','shakespeares-sonnets'}
VERSION='0.14'
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
    write(PROJECT/'project.json',dict(status='incomplete',base=pin,workingVersion=VERSION,
        scope='Every remaining Folger Shakespeare source file, including all four poetry sources; one complete native file per source.',
        publishedExisting=sorted(DONE),works=works))
    write(PROJECT/'lexical-delta.json',dict(entries={},glosses={},decisions=[]))
    (PROJECT/'README.txt').write_text('INCOMPLETE CORPUS PROJECT\nStarts from pinned 0.13. One shared language workspace and one ledger per source.\nSource indexing is not translation. project.json records exact translated/reviewed coverage.\nDo not duplicate full Forge history or Language Development folders per checkpoint.\nCompleted Bibles and prior 0.13 plays remain unchanged. Cleanup audit follows corpus verification.\n',encoding='utf-8')
    materialize();progress()

def materialize():
    project=read(PROJECT/'project.json');base=ROOT/project['base']['package']
    return write_working_language(base,read(PROJECT/'lexical-delta.json'),PROJECT/'Language')

def write_working_language(base,delta,target):
    lex=read(base/'lexicon.json');morph=read(base/'morphology.json')
    for key,entry in delta['entries'].items():
        assert key not in lex['entries'],'Never silently replace a published semantic key'
        lex['entries'][key]=entry
    morph['glosses'].update(delta['glosses']);lex['version']=VERSION
    # Reading-column labels are abbreviations, not internal research prose.
    # Only the new working package changes; published books stay immutable.
    for key,label in READING_LABELS.items():morph['suffixes'][key][1]=label
    write(target/'lexicon.json',lex);write(target/'morphology.json',morph)
    shutil.copyfile(base/'orthography.json',target/'orthography.json')
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
            notation='digits' if re.search(r'\d',note['text']) else 'words'
            assert entry.get('numericNotation','words')==notation,('SOURCE_NUMBER_NOTATION_MISMATCH',row['id'],note['text'],key)

def compile_work(slug):
    lang=materialize();source=read(PROJECT/'Sources'/(slug+'.json'))
    assert sha(ROOT/source['sourcePath'])==source['sourceSha256']
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
