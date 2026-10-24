"""Frozen Forge tests become separate books using the approved presentation."""
from copy import deepcopy
from pathlib import Path
import uuid
from tools.m0.common import load_json,write_json,file_hash
from tools.approved_baseline import MANIFEST,check_state,content_hash
from tools.parallel_translation_fixture import paragraph_starts
from .authoring import identity,stamp
from .session import utf16_length,SCALE
from .reliability_session import ReliabilitySession
from .reliability_api import ReliabilityAPI
from . import language,pages


def presentation(state):
    """Content-independent comparison; baseline pixel hashes remain untouched."""
    return dict(pages=[{k:deepcopy(v) for k,v in p.items() if k!='frames'}|dict(frames=[{k:deepcopy(v) for k,v in f.items() if k!='content'} for f in p['frames']]) for p in state['pages']],
                **{k:deepcopy(state[k]) for k in ('paint','recipe','features','styles','typesetting')},
                frameStyles=[f['content']['document']['styles'] for p in state['pages'] for f in p['frames']])


def align_paragraphs(session,count,call=None):
    if call is None:
        api=ReliabilityAPI(session)
        def call(method,**params):
            r=api.call(method,params,expected_revision=session.revision,idempotency_key=uuid.uuid4().hex,origin='python')
            if not r['ok']:raise ValueError(r['error']['message'])
            return r['result']
    frames=sorted(session.state['pages'][0]['frames'],key=lambda f:int(f['x']))
    for index in range(count):
        layout=pages.inspect(session,max_glyphs=20000);starts=[paragraph_starts(layout,f['frameId']) for f in frames]
        if any(len(lines)!=count for lines in starts):raise ValueError('FORGE_PARAGRAPH_LAYOUT_INCOMPLETE')
        target=max(lines[index]['baseline'] for lines in starts)
        for frame,lines in zip(frames,starts):
            line=lines[index];delta=(target-line['baseline'])/SCALE
            if delta>0.00001:
                call('frame.select',frame_id=frame['frameId']);call('paragraph.format',start=line['sourceUtf16'][0],end=line['sourceUtf16'][0],before=1+delta)


def run(root,project,version,test_id,directory,language_report=None,variation_report=None,spelling_report=None,reading_mode='translation'):
    root=Path(root);out=Path(directory)
    if out.exists(): raise ValueError('FORGE_RUN_DIRECTORY_EXISTS')
    snapshot=project.read(version)['snapshot']
    test=next((r for r in snapshot['tests'] if r['id']==test_id),None)
    if not test: raise ValueError('FORGE_TEST_NOT_FOUND')
    from . import reading
    if reading_mode not in reading.MODES:raise ValueError('READING_MODE_INVALID')
    reading_report=reading.inspect(snapshot,test_id,reading_mode) if reading_mode!='translation' or 'reading' in snapshot else None
    manifest=load_json(root/MANIFEST);source=root/manifest['source']['path']
    if file_hash(source)!=manifest['source']['sha256']: raise ValueError('APPROVED_REFERENCE_CHANGED')
    baseline=load_json(source);check_state(baseline['state'],manifest)
    out.mkdir(parents=True)
    report=dict(runId=uuid.uuid4().hex,version=version,projectId=project.status()['projectId'],testId=test_id,
                createdAt=stamp(),status='Error',baselineId=manifest['id'],checks=[],document=None,
                logPath=str(out/'api-transcript.json'),manifestPath=str(out/'run.json'))
    transcript=[];session=None
    if reading_report is not None:
        write_json(out/'reading-results.json',reading_report)
        report['readingResults']=dict(path=str(out/'reading-results.json'),sha256=file_hash(out/'reading-results.json'),mode=reading_mode,policySha256=reading_report['policySha256'])
    if language_report is not None:
        write_json(out/'language-results.json',language_report)
        report['languageResults']=dict(path=str(out/'language-results.json'),sha256=file_hash(out/'language-results.json'),status=language_report['status'],counts=language_report['counts'],suiteSha256=language_report['suiteSha256'],engineVersion=language_report['engineVersion'])
    if variation_report is not None:
        write_json(out/'variation-results.json',variation_report)
        report['variationResults']=dict(path=str(out/'variation-results.json'),sha256=file_hash(out/'variation-results.json'),status=variation_report['status'],watchSha256=variation_report['watchSha256'],engineVersion=variation_report['engineVersion'])
    if spelling_report is not None:
        write_json(out/'spelling-results.json',spelling_report)
        report['spellingResults']=dict(path=str(out/'spelling-results.json'),sha256=file_hash(out/'spelling-results.json'),status=spelling_report['status'],policySha256=spelling_report['policySha256'],engineVersion=spelling_report['engineVersion'])
    try:
        payload=deepcopy(baseline);state=payload['state'];state['documentId']=identity('document');state['title']=test['title']+' · '+version[:10];state['revision']=0;payload['history']=[]
        state['language']=language.initial();language.append_revision(state['language'],snapshot['language'],'Forge '+version)
        frames=sorted(state['pages'][0]['frames'],key=lambda f:int(f['x']))
        for frame,field in zip(frames,('text','translation')):
            content=frame['content'];doc=content['document'];doc['documentId']=state['documentId']
            prototype=deepcopy(doc['stories'][0]['blocks'][0]);blocks=[];characters=[];paragraphs=[];offset=0
            for pair in test['paragraphs']:
                block=deepcopy(prototype);block['blockId']=identity('block');run=deepcopy(prototype['runs'][0]);run['runId']=identity('run')
                text=pair['text' if reading_mode!='translation' and field=='translation' else field]
                # One test pair is one paragraph; embedded verse lines are soft
                # line separators, not extra paragraph objects or spacing runs.
                if language_report is not None: text=text.replace('\r\n','\n').replace('\r','\n').replace('\n','\u2028')
                run['sourceText' if run['type']=='legacy' else 'text']=text;block['runs']=[run];blocks.append(block)
                end=offset+utf16_length(text);characters.append(dict(start=offset,end=end,attributes=deepcopy(content['characters'][0]['attributes'])))
                paragraphs.append(dict(alignment='left',before=1.0,after=24.0,tabs=[]));offset=end+1
            doc['stories'][0]['blocks']=blocks;content['characters']=characters;content['paragraphs']=paragraphs
        if reading_mode!='translation':
            # Resolve the exact local file before a native document owns it.
            helper=ReliabilitySession(root,source_fonts=False,recovery=False)
            try:reading.apply_font(state,reading.font(helper,reading_mode))
            finally:helper.finish()
            state['title']=(state['title']+' · '+reading.MODES[reading_mode])[:200]
        write_json(out/'scaffold.vay.json',payload)
        session=ReliabilitySession(root,source_fonts=False,recovery=False);session.open(out/'scaffold.vay.json');api=ReliabilityAPI(session)
        def call(method,**params):
            result=api.call(method,params,expected_revision=session.revision,idempotency_key=uuid.uuid4().hex,origin='python')
            transcript.append(dict(method=method,params=params,response=result))
            if not result['ok']: raise ValueError(result['error']['message'])
            return result['result']
        align_paragraphs(session,len(test['paragraphs']),call)
        if not reading.presentation_matches(session.capture(),baseline['state'],reading_mode):raise ValueError('FORGE_PRESENTATION_CHANGED')
        call('frame.select',frame_id=frames[0]['frameId'])
        saved=call('document.save-as',path=str(out/'test.vay.json'))
        image,render=pages.render(session,path=out/'proof.png',mode='color',dpi=144)
        layout=pages.inspect(session,max_glyphs=20000);write_json(out/'layout.json',layout)
        overflow=sum(f['overflow'] for f in layout['frames']);collisions=layout['collisionReport']['afterCount']
        missing=[g for g in layout['glyphs'] if g['missingGlyph'] or ((reading_mode!='translation' or g['sourceFrameId']==frames[0]['frameId']) and g.get('fallbackReason'))]
        overhang=reading.sidebearing_review(layout,reading_mode)
        # These checks have different scopes. A page render cannot certify prose grammar.
        checks=[dict(name='Approved page geometry, fonts, type sizes, leading and paint',status='Pass',sha256=content_hash(presentation(session.capture()))),
                dict(name='Typed language references and immutable version hash',status='Pass'),
                dict(name='Frame overflow',status='Needs review' if overhang else 'Fail' if overflow else 'Pass',count=overflow,**(dict(sidebearing=overhang) if overhang else {})),
                dict(name='Missing glyphs or script font fallback',status='Fail' if missing else 'Pass',count=len(missing)),
                dict(name='Conservative glyph collision bounds',status='Needs review' if collisions else 'Pass',count=collisions),
                dict(name='Novel translation and proposed grammar',status='Needs review',details='Author-composed from versioned rules; no claim of automatic linguistic validation.'),
                dict(name='General prose grammar parser',status='Unsupported',details='M7 stores rules and derivations. A general parser is future work.')]
        if language_report is not None:
            checks[-1]['details']='M8 checks finite forms and author-annotated clauses; free prose and semantic equivalence remain unsupported.'
            checks.append(dict(name='Pinned executable language suite',status=language_report['status'],counts=language_report['counts'],suiteSha256=language_report['suiteSha256']))
            checks.append(dict(name='Displayed script bound to exact assertion inputs',status='Pass' if test.get('caseIds') else 'Unsupported',caseIds=test.get('caseIds',[]),details='Snapshot validation requires exact paragraph text from the ordered bound cases.' if test.get('caseIds') else 'No explicit clause bindings; suite coverage does not imply this prose was parsed.'))
        if variation_report is not None:
            checks.append(dict(name='Pinned advisory repetition inspection',status=variation_report['status'],warnings=variation_report['warnings'],details=variation_report['scope']))
        if spelling_report is not None:
            checks.append(dict(name='Sentence-initial Maxima',status=spelling_report['status'],initials=spelling_report['initialCount'],maxima=spelling_report['maximaInitialCount'],missing=spelling_report['missingCount'],unmapped=spelling_report['unmappedCount']))
        if reading_report is not None:
            if reading_mode!='translation':
                left,right=reading.pairs(session.capture())
                if reading.text_blocks(left)!=reading.text_blocks(right):raise ValueError('READING_OUTPUT_TEXT_MISMATCH')
                checks[0]['name']='Approved presentation with requested right-column font and Roman treatment'
            checks.append(dict(name='Parallel reading and exact symbol/case slots',status='Pass',mode=reading_mode,exactSlotsPreserved=reading_report['exactSlotsPreserved']))
        report.update(status='Fail' if (overflow and not overhang) or missing or (language_report is not None and language_report['status']=='Fail') or (spelling_report is not None and spelling_report['status']=='Fail') else 'Needs review',checks=checks,document=saved['path'],documentSha256=saved['sha256'],proof=str(out/'proof.png'),proofSha256=file_hash(out/'proof.png'),render=render,
                      engine=session.fingerprint(),templateSha256=manifest['source']['sha256'],languageRevision=session.state['language']['activeRevisionId'],test=deepcopy(test),wikiSha256=content_hash(snapshot['wiki']))
    except Exception as error:
        report['error']=str(error)
        if session: session.log.exception('forge-run',error)
    finally:
        if session: session.finish()
        write_json(out/'api-transcript.json',transcript);write_json(out/'run.json',report);project.record_run(report)
    return report
