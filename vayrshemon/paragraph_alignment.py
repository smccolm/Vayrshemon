"""Match paragraph starts across independent columns without changing typography."""
from copy import deepcopy
from . import pages
from .session import SCALE,utf16_length


def without_before(frame):
    result=deepcopy(frame)
    for paragraph in result['content']['paragraphs']:paragraph.pop('before',None)
    return result


def align(book,frame_ids=None):
    if frame_ids is None:
        index=next(i for i,p in enumerate(book.state['pages']) if p['pageId']==book.current_page()['pageId'])
        pair=book.state['pages'][index//2*2:index//2*2+2]
        if len(pair)!=2 or any(len(p['frames'])!=2 for p in pair):
            raise ValueError('PARAGRAPH_ALIGNMENT_REQUIRES_FOUR_COLUMN_SPREAD')
        frame_ids=[f['frameId'] for p in pair for f in sorted(p['frames'],key=lambda f:int(f['x']))]
    if len(frame_ids)<2 or len(set(frame_ids))!=len(frame_ids):raise ValueError('PARAGRAPH_ALIGNMENT_FRAME_IDS')
    selected={f['frameId']:p['pageId'] for p in book.state['pages'] for f in p['frames'] if f['frameId'] in frame_ids}
    if len(selected)!=len(frame_ids):raise ValueError('FRAME_NOT_FOUND')
    if any(set(frame_ids)&{f['source'],*f['targets']} for f in book.state['typesetting']['flows']):
        raise ValueError('PARAGRAPH_ALIGNMENT_REQUIRES_INDEPENDENT_COLUMNS')
    natives=[book.frames[fid] for fid in frame_ids]
    if any(n.composing for n in natives):raise ValueError('COMPOSITION_ACTIVE')
    count=natives[0].doc.blockCount()
    if any(n.doc.blockCount()!=count or not n.text().strip() for n in natives):
        raise ValueError('PARAGRAPH_ALIGNMENT_COUNT_MISMATCH')

    def measure():
        book.invalidate_composition()
        reports={pid:pages.inspect(book,page_id=pid,max_glyphs=100000) for pid in set(selected.values())}
        frames={f['frameId']:f for r in reports.values() for f in r['frames'] if f['frameId'] in selected}
        starts={}
        for fid in frame_ids:
            seen=set();starts[fid]=[]
            for line in frames[fid]['layout']['lines']:
                if line['blockId'] not in seen:
                    seen.add(line['blockId']);starts[fid].append(line)
            if len(starts[fid])!=count:raise ValueError('PARAGRAPH_ALIGNMENT_INCOMPLETE_LAYOUT')
        return frames,starts

    before=book.capture()
    with book.command('Align paragraph starts'):
        # Replace previous pairwise spacing, so repeated alignment does not
        # accumulate whitespace. Existing after-spacing remains the minimum gap.
        for n in natives:n.paragraph_format(0,utf16_length(n.text()),before=1.)
        for i in range(count):
            _,starts=measure();target=max(starts[fid][i]['baseline'] for fid in frame_ids)
            for fid in frame_ids:
                line=starts[fid][i];delta=(target-line['baseline'])/SCALE
                if delta<=.00001:continue
                n=book.frames[fid];block=n.doc.findBlock(line['sourceUtf16'][0]);base=block.blockFormat().topMargin()/SCALE
                # Native QTextDocument collapses adjacent margins; the explicit
                # typesetter adds them. A spread can contain both layout modes.
                explicit=book.state['typesetting']['frames'].get(fid,{}).get('enabled',False)
                if not explicit and block.previous().isValid():base=max(base,block.previous().blockFormat().bottomMargin()/SCALE)
                n.paragraph_format(block.position(),block.position(),before=base+delta)
        frames,starts=measure()
        rows=[[starts[fid][i]['baseline']/SCALE for fid in frame_ids] for i in range(count)]
        if any(max(row)-min(row)>.02 for row in rows):raise ValueError('PARAGRAPH_ALIGNMENT_DID_NOT_CONVERGE')
        for frame in frames.values():
            x,y,w,h=frame['rect']
            if any(l['advanceBounds'][1]+l['advanceBounds'][3]>y+h+.02 for l in frame['layout']['lines']):
                raise ValueError('PARAGRAPH_ALIGNMENT_OVERSET: paragraph groups need more page height; font sizes were retained')
        final=book.capture()
        for old,new in zip(before['pages'],final['pages']):
            for a,b in zip(old['frames'],new['frames']):
                if without_before(a)!=without_before(b):raise ValueError('PARAGRAPH_ALIGNMENT_CHANGED_TYPOGRAPHY')
    return dict(frameIds=frame_ids,paragraphs=count,baselinesPt=rows,maxErrorPt=max(max(row)-min(row) for row in rows),revision=book.revision)
