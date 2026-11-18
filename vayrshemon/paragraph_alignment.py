"""Match paragraph starts across independent columns without changing typography."""
from copy import deepcopy
from contextlib import contextmanager
from . import pages
from .session import SCALE,utf16_length


def spread_frames(book,page_id=None):
    page_id=page_id or book.current_page()['pageId']
    index=next(i for i,p in enumerate(book.state['pages']) if p['pageId']==page_id)
    pair=book.state['pages'][index//2*2:index//2*2+2]
    if len(pair)!=2 or any(len(p['frames'])!=2 for p in pair):
        raise ValueError('PARAGRAPH_ALIGNMENT_REQUIRES_FOUR_COLUMN_SPREAD')
    return [f['frameId'] for p in pair for f in sorted(p['frames'],key=lambda f:int(f['x']))]


def without_before(frame):
    result=deepcopy(frame)
    for paragraph in result['content']['paragraphs']:paragraph.pop('before',None)
    return result


@contextmanager
def alignment_edit(book, frame_ids, automatic):
    if automatic and book.__dict__.get('_editing_text_frames'):
        from .typing_edits import package, restore_packages
        before = {fid: package(book, fid) for fid in frame_ids}
        selection = book.selection()
        try:
            yield
            for fid, old in before.items():
                if without_before({'content': old}) != without_before({'content': package(book, fid)}):
                    raise ValueError('PARAGRAPH_ALIGNMENT_CHANGED_TYPOGRAPHY')
        except Exception:
            restore_packages(book, before)
            book.restore_selection(selection)
            raise
    else:
        before = book.capture()
        with book.command('Align paragraph starts'):
            yield
            final = book.capture()
            for old, new in zip(before['pages'], final['pages']):
                for a, b in zip(old['frames'], new['frames']):
                    if without_before(a) != without_before(b):
                        raise ValueError('PARAGRAPH_ALIGNMENT_CHANGED_TYPOGRAPHY')


def align(book,frame_ids=None,*,automatic=False,row=None):
    """Align all rows, or only the zero-based row chosen in the source editor."""
    if frame_ids is None:frame_ids=spread_frames(book)
    if len(frame_ids)<2 or len(set(frame_ids))!=len(frame_ids):raise ValueError('PARAGRAPH_ALIGNMENT_FRAME_IDS')
    selected={f['frameId']:p['pageId'] for p in book.state['pages'] for f in p['frames'] if f['frameId'] in frame_ids}
    if len(selected)!=len(frame_ids):raise ValueError('FRAME_NOT_FOUND')
    if any(set(frame_ids)&{f['source'],*f['targets']} for f in book.state['typesetting']['flows']):
        raise ValueError('PARAGRAPH_ALIGNMENT_REQUIRES_INDEPENDENT_COLUMNS')
    natives=[book.frames[fid] for fid in frame_ids]
    if any(n.composing for n in natives):raise ValueError('COMPOSITION_ACTIVE')
    count=natives[0].doc.blockCount()
    if row is not None and any(row < 0 or row >= n.doc.blockCount() for n in natives):
        raise ValueError('This paragraph number does not exist in every column.')
    if row is None and any(n.doc.blockCount()!=count or not n.text().strip() for n in natives):
        raise ValueError('PARAGRAPH_ALIGNMENT_COUNT_MISMATCH')
    indices=range(count) if row is None else (row,)

    def measure():
        if not automatic or not book.__dict__.get('_editing_text_frames'):
            book.invalidate_composition()
        configs=book.state['typesetting']['frames']
        repair=any(c.get('enabled') and c['collision']['mode']=='repair' for c in configs.values())
        if repair:
            book.invalidate_composition()
            reports={pid:pages.inspect(book,page_id=pid,max_glyphs=100000) for pid in set(selected.values())}
            frames={f['frameId']:f for r in reports.values() for f in r['frames'] if f['frameId'] in selected}
        else:
            from .typesetting import Composition,frame_rect,numbers
            frames={}
            baseline=book.__dict__.get('_typing_baseline') if automatic else None
            for pid in set(selected.values()):
                ids=[fid for fid in frame_ids if selected[fid]==pid]
                key=tuple((book.frames[fid],book.frames[fid].doc.revision()) for fid in ids)
                cached=baseline.line_metrics.get(pid) if baseline else None
                if cached and cached[0]==key:
                    frames.update(cached[1])
                    continue
                comp=Composition(book,page_id=pid,line_metrics=True)
                measured={}
                for fid,(_,frame) in comp.frames.items():
                    if fid in ids:measured[fid]=dict(rect=numbers(frame_rect(frame)),layout=dict(lines=[l for l in comp.lines if l['frameId']==fid]))
                if baseline:
                    if len(baseline.line_metrics)>=2 and pid not in baseline.line_metrics:
                        baseline.line_metrics.clear()
                    baseline.line_metrics[pid]=(key,measured)
                frames.update(measured)
        starts={}
        for fid in frame_ids:
            seen=set();starts[fid]=[]
            for line in frames[fid]['layout']['lines']:
                if line['blockId'] not in seen:
                    seen.add(line['blockId']);starts[fid].append(line)
            if len(starts[fid])!=book.frames[fid].doc.blockCount():raise ValueError('PARAGRAPH_ALIGNMENT_INCOMPLETE_LAYOUT')
        return frames,starts

    def result(starts):
        rows=[[starts[fid][i]['baseline']/SCALE for fid in frame_ids] for i in indices]
        return dict(frameIds=frame_ids,paragraphs=len(rows),baselinesPt=rows,maxErrorPt=max(max(values)-min(values) for values in rows),revision=book.revision)

    def fits(frames):
        return all(l['advanceBounds'][1]+l['advanceBounds'][3]<=frame['rect'][1]+frame['rect'][3]+.02
                   for frame in frames.values() for l in frame['layout']['lines'])

    if automatic or row is not None:
        frames,starts=measure();current=result(starts)
        # Most keystrokes keep the same wrapping. Retain exact spacing and
        # avoid resetting every QTextBlock or creating a second undo entry.
        if current['maxErrorPt']<=.02 and (row is not None or fits(frames)):return current
    edit=(book.typing_command('Align paragraph row',frame_ids=frame_ids) if row is not None
          else alignment_edit(book,frame_ids,automatic))
    with edit:
        # Replace previous pairwise spacing, so repeated alignment does not
        # accumulate whitespace. Existing after-spacing remains the minimum gap.
        if row is None:
            for n in natives:n.paragraph_format(0,utf16_length(n.text()),before=1.)
        for i in indices:
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
        if result(starts)['maxErrorPt']>.02:raise ValueError('PARAGRAPH_ALIGNMENT_DID_NOT_CONVERGE')
        if not fits(frames):raise ValueError('PARAGRAPH_ALIGNMENT_OVERSET: paragraph groups need more page height; font sizes were retained')
    return result(starts)
