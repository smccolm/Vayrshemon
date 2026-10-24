"""Add the requested blank/English facing page through the existing authoring API."""
from copy import deepcopy
from pathlib import Path
import argparse
import json
import uuid
from PySide6.QtWidgets import QApplication
from tools.m0.common import load_json,write_json,file_hash
from tools.approved_baseline import rgba_hash
from tools.parallel_translation_fixture import paragraph_starts
from vayrshemon import pages,reading
from vayrshemon.forge import ForgeProject
from vayrshemon.reading_api import ReadingSession,ReadingAPI
from vayrshemon.session import utf16_length,SCALE


def build(root,source,project,version,test_id,out):
    root,source,out=Path(root),Path(source),Path(out)
    out.mkdir(parents=True,exist_ok=False)
    s=ReadingSession(root,source_fonts=False,recovery=False);api=ReadingAPI(s);transcript=[]
    def call(method,**params):
        result=api.call(method,params,expected_revision=s.revision,idempotency_key=uuid.uuid4().hex)
        transcript.append(dict(method=method,params=params,response=result));write_json(out/'api-transcript.json',transcript)
        if not result['ok']:raise ValueError(result['error']['message'])
        return result['result']
    try:
        s.open(source);before=s.capture();left_page=deepcopy(before['pages'][0]);left,right=reading.pairs(before)
        snapshot=ForgeProject(project).read(version)['snapshot'];test=next(t for t in snapshot['tests'] if t['id']==test_id)
        assert reading.text_blocks(left)==[p['text'] for p in test['paragraphs']]
        english=[' '.join(p['translation'].split()) for p in test['paragraphs']]
        face=s.fonts.resolve('font:'+reading.ROMAN_SHA+':0')
        call('document.title',title='The Tempest · facing reading pages')
        call('page.add',width=int(left_page['width'])/1e6,height=int(left_page['height'])/1e6)
        right_page=s.current_page()['pageId'];blank=s.state['activeFrameId']
        call('page.configure',margins={k:int(v)/1e6 for k,v in left_page['margins'].items()})
        call('frame.configure',frame_id=blank,name='Reserved · blank',**{k:int(left[k])/1e6 for k in ('x','y','width','height')})
        call('document.format',start=0,end=0,font_id='font:'+reading.SCRIPT_SHA+':0',size=50,language='language.vayrshemon')
        call('paragraph.format',start=0,end=0,lineHeight=dict(mode='exact',value=38))
        frame=call('frame.add',name='English',**{k:int(right[k])/1e6 for k in ('x','y','width','height')})['frameId']
        text='\n'.join(english);call('document.edit',start=0,end=0,text=text)
        call('document.format',start=0,end=utf16_length(text),font_id=face.font_id,size=22,color='#E4E9F0FF',language='language.en')
        call('paragraph.format',start=0,end=utf16_length(text),lineHeight=dict(mode='exact',value=38),before=1.,after=24.)
        # Preserve exact English punctuation. The original custom font lacks
        # the ASCII hyphen; explicit same-size Times glyphs cover only missing
        # scalars and receive the identical Roman relief profile.
        fallback=[];offset=0;times=None
        for char in text:
            end=offset+utf16_length(char)
            if not char.isspace() and ord(char) not in face.cmap:
                if times is None:
                    times=reading.font(s,'literal')
                    call('fonts.load',path=str(times.path),sha256=times.sha256)
                    call('paint.bind',**reading.roman_binding(times.font_id))
                if ord(char) not in times.cmap:raise ValueError('ENGLISH_PUNCTUATION_UNSUPPORTED')
                call('document.format',start=offset,end=end,font_id=times.font_id)
                fallback.append(dict(scalar=ord(char),sourceUtf16=[offset,end],fontSha256=times.sha256))
            offset=end
        starts=paragraph_starts(pages.inspect(s,page_id=left_page['pageId'],max_glyphs=20000),right['frameId'])
        offsets=[]
        for i,target in enumerate(starts):
            line=paragraph_starts(pages.inspect(s,page_id=right_page,max_glyphs=20000),frame)[i]
            delta=(target['baseline']-line['baseline'])/SCALE
            if delta>0:call('paragraph.format',start=line['sourceUtf16'][0],end=line['sourceUtf16'][0],before=1+delta)
            offsets.append(max(0,-delta))
        assert s.frames[blank].text()==''
        assert s.frames[frame].text()==text
        assert s.capture()['pages'][0]==left_page
        call('frame.select',frame_id=left['frameId'])
        path=out/'Facing-reading-pages.vay.json';call('document.save-as',path=str(path))
        layouts=[];proofs=[]
        for i,p in enumerate(s.state['pages']):
            layout=pages.inspect(s,page_id=p['pageId'],max_glyphs=20000);write_json(out/f'page-{i+1}-layout.json',layout);layouts.append(layout)
            for f in layout['frames']:
                x,y,w,h=f['rect']
                if any(l['advanceBounds'][1]+l['advanceBounds'][3]>y+h+.01 for l in f['layout']['lines']):raise ValueError('ENGLISH_VERTICAL_OVERFLOW')
            image,render=pages.render(s,page_id=p['pageId'],path=out/f'page-{i+1}.png',mode='color',dpi=144)
            proofs.append(dict(**render,rgbaSha256=rgba_hash(image)))
        report=dict(document=str(path),documentSha256=file_hash(path),sourceSha256=file_hash(source),version=version,testId=test_id,blankFrame=blank,englishFrame=frame,englishParagraphsUnchangedExceptVerseReflow=True,explicitPunctuationFallback=fallback,paragraphDelaysPt=offsets,leftPageUnchanged=True,proofs=proofs,missingGlyphs=sum(bool(g['missingGlyph'] or g.get('fallbackReason')) for layout in layouts for g in layout['glyphs']))
        write_json(out/'review.json',report);return report
    finally:s.finish()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True);parser.add_argument('--project',type=Path,required=True);parser.add_argument('--version',required=True);parser.add_argument('--test',default='tempest-reading-coda');parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    app=QApplication.instance() or QApplication([])
    print(json.dumps(build(Path.cwd(),args.source,args.project,args.version,args.test,args.out),ensure_ascii=True))
