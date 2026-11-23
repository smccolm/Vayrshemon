"""Typeset a native, editable four-column dictionary. Measures rows using the Reader engine."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import gzip
import inspect
from itertools import groupby

from PySide6.QtWidgets import QApplication
from tools.compose_historical_book import body, texts
from tools.dictionary_corpus import BOOK, EDITION, ROOT, WORK, page_stream, read, sha
from tools.dictionary_lexicon import load_gzip
from vayrshemon import page_numbering, reading, saved_preview
from vayrshemon.file_api import FileSession
from vayrshemon.json_stream import write_atomic
from vayrshemon.native_storage import MAX_FILE_BYTES, pack
from vayrshemon.numbering_contracts import new_document_defaults
from vayrshemon.session import SCALE
from vayrshemon.typesetting import Composition, frame_rect

STAGE=ROOT/'.local/dictionary-layout'
FIELDS=('text','text','gloss','source')
NAMES=('Vayrshemon','Transliteration 7','Construction gloss','English definition and source')


def page_label(first,last):
    def shorten(value,limit):
        if len(value)<=limit:return value
        tail=limit//3
        return value[:limit-tail-1].rstrip()+'…'+value[-tail:].lstrip()
    if first==last:return shorten(first,100)
    if len(first)+len(last)+3<=100:return first+' – '+last
    a=min(len(first),max(48,97-len(last)))
    return shorten(first,a)+' – '+shorten(last,97-a)


class DictionaryLayout:
    spread_window=16

    def __init__(self, *, title=EDITION, document_id='document.native-dictionary',
                 id_prefix='dictionary', column_names=NAMES, cache_root=STAGE):
        self.id_prefix=id_prefix
        self.column_names=column_names
        self.app=QApplication.instance() or QApplication([])
        self.session=FileSession(ROOT,source_fonts=False,recovery=False)
        session=self.session
        session.remember=lambda _:None
        session.log.emit=lambda *a,**kw:None
        session.open(ROOT/'Saves/Archive/Black on white.vay',advance_revision=False)
        page_numbering.ensure_fonts(session)
        proto=session.capture()
        proto.update(documentId=document_id,title=title,revision=0)
        for page in proto['pages']:
            for frame in page['frames']:
                frame['content']['document']['documentId']=proto['documentId']
        proto['pageNumbering']=new_document_defaults()
        session._restore(proto)
        page_numbering.ensure_fonts(session)
        self.proto=session.capture()
        settings=self.proto['typesetting']['frames']
        enabled=next(v for v in settings.values() if v.get('enabled'))
        for page in self.proto['pages']:
            for frame in page['frames']:
                settings[frame['frameId']]=deepcopy(enabled)
        self.fonts=[session.fonts.faces['font:'+reading.SCRIPT_SHA+':0'],
                    *[reading.font(session,'transliteration')]*3]
        self.literal=next(session.fonts.faces[f['fontId']] for f in self.proto['fontSources']
                          if Path(f['path']).name.lower()=='times.ttf')
        self.extra=session.fonts.register(Path(os.environ['WINDIR'])/'Fonts/malgun.ttf')
        if self.extra.font_id not in {f['fontId'] for f in self.proto['fontSources']}:
            self.proto['fontSources'].append(dict(fontId=self.extra.font_id,sha256=self.extra.sha256,path=str(self.extra.path)))
        self.configs=self.proto['typesetting']['frames']
        self.engine=session.fingerprint()
        template_id=sha(ROOT/'Saves/Archive/Black on white.vay')
        geometry_hash=hashlib.sha256((inspect.getsource(self.shape)+inspect.getsource(self.spread)+inspect.getsource(body)).encode()).hexdigest()
        self.cache=cache_root/('spreads-'+geometry_hash[:12]+'-'+template_id[:8])
        self.cache.mkdir(parents=True,exist_ok=True)

    def shape(self,rows,before=None,shrinks=None):
        shrinks=shrinks or {}
        state=deepcopy(self.proto)
        frames=[f for p in state['pages'] for f in sorted(p['frames'],key=lambda f:int(f['x']))]
        for i,(f,field,font) in enumerate(zip(frames,FIELDS,self.fonts)):
            body(f,[row[field] for row in rows],font,self.literal,i,extra_font=self.extra)
            f['name']=NAMES[i]
            doc=f['content']['document']
            doc['documentId']=state['documentId']
            for style in doc['styles']:
                if style.get('lineHeight',{}).get('mode')=='exact':
                    original=int(style['fontSizeMicroPoints'])
                    style['fontSizeMicroPoints']=str(32000000 if original==50000000 else 14500000)
                    style['lineHeight']['microPoints']='25500000'
            for j,p in enumerate(f['content']['paragraphs']):
                p.update(before=before[i][j] if before else 1.,after=8.)
                factor=shrinks.get((i,j),1.)
                if factor<1:
                    styles={s['styleId']:s for s in doc['styles']}
                    for run in doc['stories'][0]['blocks'][j]['runs']:
                        old=run['styleId'];sid=f'{old}.dictionary.{j}'
                        if sid not in styles:
                            style=dict(styles[old],styleId=sid,fontSizeMicroPoints=str(round(int(styles[old]['fontSizeMicroPoints'])*factor)))
                            styles[sid]=style;doc['styles'].append(style)
                            f['content']['styleFeatures'][sid]=dict(f['content']['styleFeatures'].get(old,{}))
                        run['styleId']=sid
        self.session._restore(state)
        self.session._state=state
        self.session.invalidate_composition()
        metrics={}
        retry={}
        for p in state['pages']:
            comp=Composition(self.session,page_id=p['pageId'],line_metrics=True)
            for f in p['frames']:
                lines=[l for l in comp.lines if l['frameId']==f['frameId']]
                blocks=f['content']['document']['stories'][0]['blocks']
                byblock={b['blockId']:[] for b in blocks}
                for line in lines:byblock[line['blockId']].append(line)
                rect=frame_rect(f)
                byrow=[]
                for values in byblock.values():
                    if not values:raise ValueError('Missing dictionary row')
                    bounds=[l['advanceBounds'] for l in values]
                    excess=max(x+w-rect.right() for x,y,w,h in bounds)
                    if excess>.15:
                        slot=(next(i for i,c in enumerate(frames) if c['frameId']==f['frameId']),len(byrow))
                        scale=shrinks.get(slot,1.)*min(.975,rect.width()/(rect.width()+excess+2))
                        if scale<.68:raise ValueError(f'Dictionary column width: {texts(f)[len(byrow)]}')
                        retry[slot]=scale
                    byrow.append(((values[0]['baseline']-rect.top())/SCALE,
                                  (max(y+h for x,y,w,h in bounds)-rect.top())/SCALE))
                metrics[f['frameId']]=byrow
        if retry:return self.shape(rows,before,shrinks|retry)
        return state,[metrics[f['frameId']] for f in frames]

    def spread(self,rows):
        initial,m=self.shape(rows)
        heights=[max(col[k][0]-col[k-1][0] for col in m) for k in range(1,len(rows))]
        starts=[max(col[0][0] for col in m)]
        for h in heights:starts.append(starts[-1]+h)
        available=int(initial['pages'][0]['frames'][0]['height'])/1e6
        count=0
        for k,start in enumerate(starts):
            if start+max(col[k][1]-col[k][0] for col in m)>available-1:break
            count+=1
        if count==0:raise ValueError(f'Dictionary entry needs division: {rows[0]["id"]}')
        adjustments=[]
        for col in m:
            prev=0.
            margins=[]
            for j in range(count):
                offset=starts[j]-col[j][0]
                margins.append(1.+offset-prev)
                prev=offset
            adjustments.append(margins)
        state,checked=self.shape(rows[:count],adjustments)
        err=max(max(v)-min(v) for v in zip(*[[r[0] for r in col] for col in checked]))
        bottom=max(r[1] for col in checked for r in col)
        if err>.035 or bottom>available+.05:
            raise ValueError(f'Dictionary spread alignment {rows[0]["id"]} {err=} {bottom=}')
        return count,state,err

    def measured(self,group):
        signature=hashlib.sha256(json.dumps(group,ensure_ascii=True,separators=(',',':')).encode()).hexdigest()
        cached=self.cache/(signature+'.json.gz')
        if cached.exists():
            with gzip.open(cached,'rt',encoding='utf8') as file:
                count,pages,error=json.load(file)
            return count,dict(self.proto,pages=pages),error
        count,state,error=self.spread(group)
        tmp=cached.with_suffix('.'+str(os.getpid())+'.writing')
        with gzip.open(tmp,'wt',encoding='utf8',compresslevel=2) as file:
            json.dump([count,state['pages'],error],file,separators=(',',':'))
        # Different refresh processes can measure the same immutable spread.
        # A reader on Windows may keep the first published cache file open.
        try:
            if not cached.exists():
                tmp.replace(cached)
        except PermissionError:
            if not cached.exists():
                raise
        finally:
            tmp.unlink(missing_ok=True)
        return count,state,error

    def build(self,rows,target,ledger_hash,language_data=None):
        STAGE.mkdir(parents=True,exist_ok=True)
        pages_out,index,profiles=[],[],{}
        position=0
        preview=None
        max_error=0.
        while position<len(rows):
            group=rows[position:position+self.spread_window]
            # Keep a new section at the head of a spread.
            for j in range(1,len(group)):
                if group[j]['section']!=group[0]['section']:
                    group=group[:j]
                    break
            count,state,error=self.measured(group)
            max_error=max(error,max_error)
            first=len(pages_out)+1
            for page_no,p in enumerate(state['pages'],first):
                p['pageId']=f'page.{self.id_prefix}.{page_no}'
                p['name']=page_label(group[0]['reference'],group[count-1]['reference'])
                for col,frame in enumerate(sorted(p['frames'],key=lambda f:int(f['x']))):
                    old=frame['frameId']
                    frame['name']=self.column_names[(page_no-first)*2+col]
                    frame['frameId']=f'frame.{self.id_prefix}.{page_no}.{col+1}'
                    profiles[frame['frameId']]=self.configs[old]
                pages_out.append(p)
            index.append(dict(leftPage=first,rightPage=first+1,first=group[0]['reference'],
                              last=group[count-1]['reference'],ids=[r['id'] for r in group[:count]]))
            if preview is None:
                opening=dict(state,pages=pages_out[:],typesetting=dict(state['typesetting'],frames=profiles.copy()),
                             activeFrameId=pages_out[0]['frames'][0]['frameId'])
                self.session._restore(opening)
                self.session._state=self.session.capture()
                self.session.invalidate_composition()
                preview=saved_preview.create(self.session,self.session.capture(),'two')
            position+=count
            if len(index)%100==0:print(position,'/',len(rows),'rows;',len(pages_out),'pages',flush=True)
        book=dict(self.proto,pages=pages_out,activeFrameId=pages_out[0]['frames'][0]['frameId'],
                  typesetting=dict(self.proto['typesetting'],frames=profiles))
        if language_data is not None:
            from vayrshemon import language
            book['language']=language.initial()
            language.append_revision(book['language'],language_data,'Native Vayrshemon dictionary',
                                     preserve_lexicon_order=True)
        preview.update(stateSha256=saved_preview.state_hash(book))
        payload=pack(dict(format='vayrshemon.document',formatVersion='0.6.0',state=book,
                          history=[],engine=self.engine,shellPreview=preview))
        write_atomic(target,payload,limit=MAX_FILE_BYTES)
        del payload
        actual=iter(page_stream(target))
        n=0
        for i,group in enumerate(index):
            pair=[next(actual),next(actual)]
            frames=[f for p in pair for f in sorted(p['frames'],key=lambda f:int(f['x']))]
            count=len(group['ids'])
            for field,frame in zip(FIELDS,frames,strict=True):
                if texts(frame)!=[r[field] for r in rows[n:n+count]]:raise ValueError('Saved dictionary column mismatch')
            n+=count
        assert n==len(rows) and next(actual,None) is None
        return dict(pages=len(pages_out),spreads=len(index),rows=n,sha256=sha(target),ledgerSha256=ledger_hash,
                    maxBaselineErrorPt=max_error,allFourSavedColumnsVerified=True),index


_worker_layout=None

def measure_section(rows):
    global _worker_layout
    if _worker_layout is None:_worker_layout=DictionaryLayout()
    start=0
    while start<len(rows):
        n,_,_=_worker_layout.measured(rows[start:start+16])
        start+=n
    return start

def premeasure(rows,workers):
    from concurrent.futures import ProcessPoolExecutor,as_completed
    sections=[list(group) for _,group in groupby(rows,key=lambda r:r['section'])]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        tasks=[pool.submit(measure_section,group) for group in sorted(sections,key=len,reverse=True)]
        total=0
        for job in as_completed(tasks):
            total+=job.result()
            print(f'Measured {total}/{len(rows)} dictionary rows',flush=True)

def insert_directory(rows,renderer):
    from tools.dictionary_lexicon import language_set
    from tools.dictionary_rows import collate
    from tools.unta_language import quantity
    language,_=language_set()
    num=lambda n:quantity(n,notation='digits')['form']
    def spread_count(group):
        pos=0;spreads=0
        while pos<len(group):
            count,_,_=renderer.measured(group[pos:pos+16])
            pos+=count;spreads+=1
        return spreads
    groups=[(key,list(items)) for key,items in groupby(rows,key=lambda r:r['section']) if key!='directory']
    initials={}
    next_page=1
    for key,group in groups:
        end=next_page+2*spread_count(group)
        if key!='opening':
            section,letter=key.split('-',1)
            initials.setdefault(letter,{})[section]=(next_page,end-1)
        next_page=end
    terms=[(s,en,language.compile(k,initial=False)['text']) for s,en,k in
           [('headwords','Headwords','word:pl'),('manuscript','Manuscript readings','written:m example:pl'),
            ('forms','Written forms','form:pl')]]
    offset=0
    for _ in range(8):
        directory=[]
        for letter,locations in sorted(initials.items(),key=lambda z:collate(z[0])):
            native=[];eng=[];gl=[]
            for section,label,word in terms:
                if section not in locations:continue
                a,b=locations[section]
                native.append(f'{word} {num(a+offset)}, {num(b+offset)}')
                eng.append(f'{label} pp. {a+offset}–{b+offset}')
                gl.append(f'{label.lower()} · {a+offset}–{b+offset}')
            directory.append(dict(id='directory-'+str(ord(letter)),section='directory',
                reference=language.reading(letter),text=letter+'. '+'. '.join(native)+'.',
                gloss=language.reading(letter)+'. '+'. '.join(gl)+'.',source='. '.join(eng)+'.'))
        size=2*spread_count(directory)
        if size==offset:return groups[0][1]+directory+[r for _,grp in groups[1:] for r in grp]
        offset=size
    raise ValueError('Dictionary directory pagination did not converge')

def publish():
    import shutil
    from tools.dictionary_corpus import TOKENIZATION
    src=WORK/'dictionary-rows.json.gz'
    ledger=load_gzip(src)
    if ledger['counts'].get('wordBoundaryConvention')!=TOKENIZATION:
        raise ValueError('Rebuild the entries from the revised manuscript word boundaries before issuing.')
    if ledger['counts']['definitionMethods'].get('requires paraphrase'):
        raise ValueError('Unfinished entries. Use the private proof build until all native definitions are ready.')
    target=BOOK/(EDITION+'.vay')
    receipt=WORK/'publication.json'
    if target.exists() and (not receipt.exists() or read(receipt)['sha256']!=sha(target)):
        raise ValueError('The native dictionary has independent edits. Reconcile them before refreshing it.')
    STAGE.mkdir(parents=True,exist_ok=True)
    stage=STAGE/'dictionary.vay'
    renderer=DictionaryLayout()
    from tools.dictionary_forge import forge_data
    from tools.dictionary_lexicon import save_gzip
    try:
        ledger['rows']=insert_directory(ledger['rows'],renderer)
        save_gzip(src,ledger)
        report,index=renderer.build(ledger['rows'],stage,sha(src),forge_data(ledger['rows']))
    finally:renderer.session.finish()
    report.update(ledger['counts'])
    validation=FileSession(ROOT,source_fonts=False,recovery=False)
    validation.remember=lambda *args:None
    validation.log.emit=lambda *args,**kwargs:None
    try:
        print('Reopening staged publication in the native editor',flush=True)
        validation.open(stage,advance_revision=False)
        if len(validation.state['pages'])!=report['pages'] or validation.saved_page_mode!='two':
            raise ValueError('Staged dictionary reopened with different pagination or spread mode')
        report['nativeReopenVerified']=True
    finally:
        validation.finish()
    if target.exists():
        backup=STAGE/('prior-'+sha(target)+'.vay')
        if not backup.exists():shutil.copy2(target,backup)
    stage.replace(target)
    write_atomic(receipt,report)
    write_atomic(WORK/'page-index.json',index)
    print(report,flush=True)


if __name__=='__main__':
    publish()
