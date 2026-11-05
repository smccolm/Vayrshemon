"""Keep complete four-column spreads aligned within the user's text edit."""
from copy import deepcopy
from time import perf_counter
from .paragraph_alignment import align,spread_frames
from .book_frames import loaded_items


def text_of(frame):
    return '\n'.join(''.join(r.get('text',r.get('sourceText','')) for r in b['runs'])
                     for b in frame['content']['document']['stories'][0]['blocks'])


class AutomaticAlignment:
    def __init__(self,*args,**kwargs):
        self.automatic_alignment=dict(enabled=True,status='ready',message='Paragraph starts align automatically when text changes.')
        self._aligning_text=False
        super().__init__(*args,**kwargs)

    def _restore(self,state,**kwargs):
        super()._restore(state,**kwargs)
        self.automatic_alignment=dict(enabled=True,status='ready',message='Paragraph starts align automatically when text changes.')
        pages=self.state['pages']
        for index in range(0,len(pages)-1,2):
            pair=pages[index:index+2]
            if any(len(p['frames'])!=2 for p in pair):continue
            # We already have each page and frame. Searching the whole book
            # again for every column makes opening quadratic in page count.
            columns=[f for p in pair for f in sorted(p['frames'],key=lambda f:int(f['x']))]
            ids=[f['frameId'] for f in columns]
            if all(text_of(n).strip() for n in columns) and len({len(n['content']['document']['stories'][0]['blocks']) for n in columns})>1:
                issues=[dict(frameIds=ids,reason='PARAGRAPH_ALIGNMENT_COUNT_MISMATCH')]
                self.automatic_alignment=dict(enabled=True,status='paused',message=message(issues),issues=issues)
                break

    def commit(self,label):
        if not self._aligning_text and not self._restoring and not self.composing:
            old={f['frameId']:text_of(f) for p in self._state['pages'] for f in p['frames']}
            changed={fid for fid,n in loaded_items(self.frames) if fid in old and n.text()!=old[fid]}
            groups=[]
            for p in self.state['pages']:
                if not any(f['frameId'] in changed for f in p['frames']):continue
                try:ids=spread_frames(self,p['pageId'])
                except ValueError:continue
                if ids not in groups:groups.append(ids)
            if groups:
                started=perf_counter();results=[];issues=[]
                self._aligning_text=True;self._depth+=1
                try:
                    for ids in groups:
                        try:results.append(align(self,ids,automatic=True))
                        except Exception as error:
                            # align's transaction restores the just-edited text
                            # with its prior spacing. Never reject a user's text
                            # because its companion paragraphs are unfinished.
                            issues.append(dict(frameIds=ids,reason=str(error)))
                            self.log.exception('automatic-alignment',error)
                finally:self._depth-=1;self._aligning_text=False
                self.automatic_alignment=dict(enabled=True,status='paused' if issues else 'aligned',
                    message=message(issues),issues=issues,results=results,elapsedMs=(perf_counter()-started)*1000)
                self.log.emit('automatic-alignment','ALIGNMENT_PAUSED' if issues else 'PARAGRAPHS_ALIGNED',
                              **deepcopy(self.automatic_alignment))
        return super().commit(label)

def message(issues):
    if not issues:return 'Paragraph starts aligned automatically.'
    reason=issues[0]['reason']
    if 'COUNT_MISMATCH' in reason:return 'Alignment paused: paragraph counts differ. It resumes when all four columns match.'
    if 'OVERSET' in reason:return 'Alignment paused: the text needs more page height. Your text and font sizes are preserved.'
    return 'Alignment paused; your text is preserved. '+reason
