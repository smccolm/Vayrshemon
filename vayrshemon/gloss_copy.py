"""Add a gloss to a separate facing book; protect the other three columns."""
from copy import deepcopy
from pathlib import Path
import uuid
from tools.m0.common import write_json,file_hash
from tools.parallel_translation_fixture import paragraph_starts
from tools.approved_baseline import rgba_hash
from .authoring import identity,stamp
from .session import utf16_length,SCALE
from . import gloss,reading,pages,language
from .forge import digest


def create(book,project,version,test_id,directory):
    out=Path(directory);gloss.require(not out.exists(),'DIRECTORY_EXISTS')
    gloss.require(len(version)==64 and all(c in '0123456789abcdef' for c in version),'FROZEN_VERSION_REQUIRED')
    frozen=project.read(version)
    # read(version) resolves only immutable commits; the hash is carried in every result.
    snapshot=frozen['snapshot'];report=gloss.inspect(snapshot,test_id);source=book.capture()
    gloss.require(len(source['pages'])==2 and all(len(p['frames'])==2 for p in source['pages']),'TWO_PAGE_FOUR_FRAME_SOURCE_REQUIRED')
    left=sorted(source['pages'][0]['frames'],key=lambda f:int(f['x']));blank,english=sorted(source['pages'][1]['frames'],key=lambda f:int(f['x']))
    text=lambda f:'\n'.join(reading.text_blocks(f))
    expected='\n'.join(p['source'] for p in report['paragraphs'])
    gloss.require(text(left[0])==expected and text(left[1])==expected,'SOURCE_TEXT_MISMATCH')
    gloss.require(not text(blank).strip(),'RESERVED_COLUMN_NOT_EMPTY')
    gloss.require(text(english)=='\n'.join(' '.join(p['english'].split()) for p in report['paragraphs']),'ENGLISH_TEXT_MISMATCH')
    gloss.require(not report['issues'],'IMPLICIT_SUBJECT_REQUIRES_EXPLICIT_REVIEW')
    before_images=[pages.render(book,page_id=p['pageId'],mode='color',dpi=144)[0] for p in source['pages']]
    out.mkdir(parents=True)
    title=next(t['title'] for t in snapshot['tests'] if t['id']==test_id)
    payload=deepcopy(source);payload['documentId']=identity('document');payload['revision']=0;payload['title']=title+' · construction gloss · '+version[:10]
    for p in payload['pages']:
        for f in p['frames']:f['content']['document']['documentId']=payload['documentId']
    payload['language']=language.initial();language.append_revision(payload['language'],snapshot['language'],'Forge '+version)
    write_json(out/'scaffold.vay.json',dict(format='vayrshemon.document',formatVersion=book.file_version,state=payload,history=[],engine=book.fingerprint()))
    from .gloss_api import GlossSession,GlossAPI
    s=GlossSession(book.root,source_fonts=False,recovery=False);api=GlossAPI(s);transcript=[]
    def call(method,**params):
        result=api.call(method,params,expected_revision=s.revision,idempotency_key=uuid.uuid4().hex)
        transcript.append(dict(method=method,params=params,response=result));write_json(out/'api-transcript.json',transcript)
        if not result['ok']:raise ValueError(result['error']['message'])
        return result['result']
    try:
        s.open(out/'scaffold.vay.json');before=s.capture();fid=blank['frameId'];page_id=source['pages'][1]['pageId'];body='\n'.join(p['text'] for p in report['paragraphs'])
        call('frame.select',frame_id=fid);call('frame.configure',frame_id=fid,name='Construction gloss')
        call('document.edit',start=0,end=0,text=body)
        roman=reading.font(s,'transliteration')
        call('document.format',start=0,end=utf16_length(body),font_id=roman.font_id,size=22,color='#E4E9F0FF',language='language.en')
        call('paragraph.format',start=0,end=utf16_length(body),lineHeight=dict(mode='exact',value=38),before=1.,after=24.,alignment='left')
        call('paint.bind',**reading.roman_binding(roman.font_id))
        times=None;fallback=[];offset=0
        for c in body:
            end=offset+utf16_length(c)
            # Legacy non-ASCII slots may depict letters, not Unicode punctuation.
            if not c.isspace() and (c in '·()+-' or ord(c) not in roman.cmap):
                if times is None:
                    times=reading.font(s,'literal');call('fonts.load',path=str(times.path),sha256=times.sha256);call('paint.bind',**reading.roman_binding(times.font_id))
                gloss.require(ord(c) in times.cmap,'PUNCTUATION_UNSUPPORTED')
                fallback.append(dict(sourceUtf16=[offset,end],scalar=ord(c),fontSha256=times.sha256))
            offset=end
        if fallback:
            # This isolated copy owns the entire edit. One atomic transaction
            # avoids retaining a full-book undo snapshot for each parenthesis.
            with s.command('gloss.punctuation'):
                for run in fallback:s.active.format_range(*run['sourceUtf16'],font_id=times.font_id)
            transcript.append(dict(method='gloss.punctuation',ranges=fallback,revision=s.revision));write_json(out/'api-transcript.json',transcript)
        targets=paragraph_starts(pages.inspect(s,page_id=page_id,max_glyphs=20000),english['frameId']);delays=[]
        for i,target in enumerate(targets):
            line=paragraph_starts(pages.inspect(s,page_id=page_id,max_glyphs=20000),fid)[i]
            delta=(target['baseline']-line['baseline'])/SCALE
            if delta>0.00001:
                block=s.active.doc.findBlock(line['sourceUtf16'][0]);base=block.blockFormat().topMargin()/SCALE
                if block.previous().isValid():base=max(base,block.previous().blockFormat().bottomMargin()/SCALE)
                call('paragraph.format',start=line['sourceUtf16'][0],end=line['sourceUtf16'][0],before=base+delta)
            delays.append(max(0,-delta))
        layout=pages.inspect(s,page_id=page_id,max_glyphs=20000);write_json(out/'layout.json',layout)
        delays=[max(0,(a['baseline']-b['baseline'])/SCALE) for a,b in zip(paragraph_starts(layout,fid),targets)]
        frame=next(f for f in layout['frames'] if f['frameId']==fid);x,y,w,h=frame['rect']
        gloss.require(all(l['advanceBounds'][1]+l['advanceBounds'][3]<=y+h+.01 and l['advanceBounds'][0]+l['advanceBounds'][2]<=x+w+.01 for l in frame['layout']['lines']),'FRAME_OVERSET: shorten labels in the Forge glossary; the approved type size is retained')
        missing=[g for g in layout['glyphs'] if g['missingGlyph'] or g.get('fallbackReason')];gloss.require(not missing,'MISSING_GLYPHS')
        source_offset=gloss_offset=0
        for i,p in enumerate(report['paragraphs']):
            cid='gloss.'+uuid.uuid4().hex;lex_tokens=[]
            for clause in p['clauses']:
                for token in clause['tokens']:
                    lex_tokens.append(dict(start=token['sourceScalar'][0],end=token['sourceScalar'][1],surface=token['surface'],morphemes=[token['surface']],glosses=[token['gloss']],entryIds=[token['entryId']],senseIds=[token['senseId']],morphologyIds=[],status='draft'))
            corpus=dict(id=cid,label='Construction gloss '+str(i+1),status='draft',citations=[],notes='Forge '+version+'; profile '+report['profileSha256']+'; '+report['scope'],
                text=p['source'],translation=p['text'],transliteration='',rawGloss=p['text'],orthographyId=snapshot['reading']['orthographyId'],sourceFonts=[reading.SCRIPT_SHA],tokens=lex_tokens,offsetUnit='unicode-scalar')
            call('language.record.put',collection='corpus',record=corpus,label='M13 pinned construction gloss')
            call('corpus.link',corpus_id=cid,source=dict(frame_id=left[0]['frameId'],start=source_offset,end=source_offset+utf16_length(p['source'])),translation=dict(frame_id=fid,start=gloss_offset,end=gloss_offset+utf16_length(p['text'])),adaptation='Abbreviated construction gloss in source order; Forge '+version)
            source_offset+=utf16_length(p['source'])+1;gloss_offset+=utf16_length(p['text'])+1
        final=s.capture()
        for old,new in zip(before['pages'],final['pages']):
            gloss.require({k:v for k,v in old.items() if k!='frames'}=={k:v for k,v in new.items() if k!='frames'},'PAGE_GEOMETRY_CHANGED')
            for a,b in zip(old['frames'],new['frames']):
                if a['frameId']!=fid:gloss.require(a==b,'PROTECTED_COLUMN_CHANGED')
        call('frame.select',frame_id=left[0]['frameId']);saved=call('document.save-as',path=str(out/'Construction-spread.vay.json'))
        proofs=[]
        for i,p in enumerate(final['pages']):
            image,render=pages.render(s,page_id=p['pageId'],path=out/f'page-{i+1}.png',mode='color',dpi=144)
            protected=image if i==0 else image.copy(image.width()//2,0,image.width()-image.width()//2,image.height())
            old=before_images[i] if i==0 else before_images[i].copy(image.width()//2,0,image.width()-image.width()//2,image.height())
            gloss.require(rgba_hash(protected)==rgba_hash(old),'PROTECTED_PIXELS_CHANGED')
            proofs.append(dict(**render,rgbaSha256=rgba_hash(image),protectedPixelsIdentical=True))
        write_json(out/'gloss.json',report)
        result=dict(runId=uuid.uuid4().hex,kind='construction-gloss',createdAt=stamp(),version=version,projectId=project.status()['projectId'],testId=test_id,status='Needs review',
            document=saved['path'],documentSha256=saved['sha256'],manifestPath=str(out/'run.json'),sourceDocumentId=source['documentId'],sourceRevision=source['revision'],sourceUnchanged=book.capture()==source,
            sourceSha256=digest(source),glossResults=dict(path=str(out/'gloss.json'),sha256=file_hash(out/'gloss.json')),proofs=proofs,paragraphDelaysPt=delays,
            missingGlyphs=0,glossFrame=fid,punctuationOverrides=fallback,tokenCount=report['tokenCount'],checks=[dict(name='Other three columns and approved font treatment',status='Pass'),dict(name='Word-order and dictionary links',status='Pass'),dict(name='Gloss line advances fit',status='Pass')])
        write_json(out/'run.json',result);project.record_run(result);return result
    finally:s.finish()
