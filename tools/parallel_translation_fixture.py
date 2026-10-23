"""Reconstruct the approved bilingual specimen through the shared API.

Call only with a new isolated test session. Original source material stays local.
This is fixture support, not automatic translation alignment in the application.
"""
from pathlib import Path
import hashlib
import json
from tools.m0.docx import extract_docx
from vayrshemon.session import SCALE, utf16_length


def definition(root):
    return json.loads((Path(root)/'data/formatting/parallel-translation.json').read_text(encoding='utf-8'))


def local_material(root, call):
    spec=definition(root)['localFixture']; archive=Path(root)/'Inputs'
    # Verify all inputs before loading fonts or interpreting source offsets.
    for item in [spec['source'],*spec['fonts']]:
        if hashlib.sha256((archive/item['path']).read_bytes()).hexdigest()!=item['sha256']:
            raise ValueError('PARALLEL_TRANSLATION_SOURCE_HASH_MISMATCH: '+item['path'])
    evidence=extract_docx(archive/spec['source']['path'])
    if evidence['sourceSha256']!=spec['source']['sha256']:
        raise ValueError('PARALLEL_TRANSLATION_SOURCE_CHANGED')
    fonts={f['name']:call('fonts.load',path=str(archive/f['path']),sha256=f['sha256'])['fontId'] for f in spec['fonts']}
    def runs(index):
        result=[]
        for run in evidence['paragraphs'][index]['runs']:
            # Word's cached pagination marker carries no source character and
            # must not impose the old Word page break on this portrait specimen.
            tokens=[t for t in run['tokens'] if not (t['kind']=='unsupported' and t.get('tag')=='lastRenderedPageBreak')]
            if any(t['kind']!='t' for t in tokens):
                raise ValueError('PARALLEL_TRANSLATION_UNEXPECTED_SOURCE_TOKEN')
            text=''.join(t['text'] for t in tokens)
            if text: result.append(dict(text=text,font=run['directFonts'].get('ascii')))
        return result
    pairs=[]
    for pair in spec['paragraphPairs']:
        original=runs(pair['original']); english=runs(pair['translation'])
        if any(r['font'] not in fonts for r in original):
            raise ValueError('PARALLEL_TRANSLATION_UNRESOLVED_FONT')
        pairs.append(dict(original=original,translation=''.join(r['text'] for r in english)))
    return pairs,fonts


def paragraph_starts(report, frame_id):
    frame=next(f for f in report['frames'] if f['frameId']==frame_id)
    seen=set(); result=[]
    for line in frame['layout']['lines']:
        if line['blockId'] not in seen:
            seen.add(line['blockId']); result.append(line)
    return result


def compose(root, call, pairs, fonts, typography=None):
    spec=definition(root); style=typography or spec['referenceTypography']
    call('page.configure',**spec['page'])
    text={
        'original':'\n'.join(''.join(r['text'] for r in p['original']) for p in pairs),
        'translation':'\n'.join(p['translation'] for p in pairs),
    }
    ids={}
    for i,column in enumerate(spec['columns']):
        role=column['role']; dimensions={k:column[k] for k in ('name','x','y','width','height')}
        if i==0:
            call('frame.configure',**dimensions)
            fid=call('document.read')['document']['activeFrameId']
        else:
            fid=call('frame.add',**dimensions)['frameId']
        ids[role]=fid
        call('document.edit',start=0,end=0,text=text[role])
        call('document.format',start=0,end=utf16_length(text[role]),size=style[role]['size'],
             color=style[role]['color'],font_id=None,language=column['language'])
        if role=='original':
            offset=0
            for pair in pairs:
                for run in pair['original']:
                    end=offset+utf16_length(run['text'])
                    call('document.format',start=offset,end=end,font_id=fonts[run['font']])
                    offset=end
                offset+=1  # paragraph separator; never rewrite a source run
        call('paragraph.format',start=0,end=utf16_length(text[role]),before=style['before'],after=style['after'],
             lineHeight=dict(mode='exact',value=style[role]['lineHeight']))
        call('typesetting.configure',enabled=True,grid=dict(enabled=False,step=12,offset=0))
        call('collision.configure',mode=style['collisionMode'])
    # Align each pair after measuring actual font metrics. These are ordinary
    # paragraph-spacing commands; later user edits do not auto-realign stories.
    for index in range(len(pairs)):
        report=call('layout.inspect')
        starts={role:paragraph_starts(report,fid) for role,fid in ids.items()}
        if any(len(lines)!=len(pairs) for lines in starts.values()):
            raise ValueError('PARALLEL_TRANSLATION_PARAGRAPH_COUNT')
        target=max(lines[index]['baseline'] for lines in starts.values())
        for role,fid in ids.items():
            line=starts[role][index]; delta=(target-line['baseline'])/SCALE
            if delta>0.00001:
                call('frame.select',frame_id=fid)
                call('paragraph.format',start=line['sourceUtf16'][0],end=line['sourceUtf16'][0],before=style['before']+delta)
    call('frame.select',frame_id=ids['original'])
    call('view.configure',mode=style['previewMode'],baselines=False,bounds=False,origins=False)
    return ids,text
