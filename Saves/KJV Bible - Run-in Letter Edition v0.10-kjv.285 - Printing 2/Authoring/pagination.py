"""Audit the remaining measure at every page foot from the saved native books."""
from collections import defaultdict
from statistics import mean,median
from compose import (BODY,GAP,LEADING,MARKER,OUTER,PREVIOUS,STAGE,TOP,QApplication,
                     Proof,QRectF,digits,pe,read,save_json,unpack)


def probe_last_line(proof,state,index,last_id,next_id):
    """Try to fit the actual next word on the preceding page's final baseline."""
    pg=state['pages'][index]
    next_pg=state['pages'][index+1]
    spec=state['printEdition']['pages'][pg['pageId']]
    line=spec['lines'][-1]
    nxt=pe.text_of(next_pg).split()[0]
    source=pe.text_of(pg)
    text=line['prefix']+source[line['start']:line['end']]
    right=612-int(pg['margins']['right'])/1e6
    def measure(s,prefix):
        return proof.lines(s,10000,BODY,len(prefix),punctuation=True,verse_size=MARKER)[0]
    x=line['x']
    if last_id==next_id:
        new=measure(text+' '+nxt,line['prefix'])
        prior=spec['lines'][:-1]
    elif last_id[:6]==next_id[:6]:
        old=measure(text,line['prefix'])
        x+=max(old.width,old.path.boundingRect().right())+GAP
        prefix=digits(int(next_id.split('.')[-1]))+'  '
        new=measure(prefix+nxt,prefix)
        prior=spec['lines']
    else:
        # A chapter start needs both its separate numeral and the verse number.
        numeral=proof.word(digits(int(next_id.split('.')[1])),50)
        old=measure(text,line['prefix'])
        x+=max(old.width,old.path.boundingRect().right())+GAP+numeral.boundingRect().width()+18
        new=measure(digits(1)+'  '+nxt,digits(1)+'  ')
        prior=spec['lines']
    rect=new.path.boundingRect().translated(x,line['baseline'])
    if x+max(new.width,new.path.boundingRect().right())>right+.001: return
    if rect.bottom()>792-int(pg['margins']['bottom'])/1e6: return
    if any(rect.intersects(QRectF(*p['bounds'])) for p in (*prior,*spec['paths'])): return
    raise ValueError(f'Next word could still fit on native page {index+1}: {last_id} / {next_id}')


def inspect_file(proof,path,book_index,probe):
    state=unpack(read(path))['state']
    e=state['printEdition']
    ends={r['lastNativePage'] for r in book_index}
    spans=defaultdict(list)
    chapters=defaultdict(list)
    for verse in e['verses']:
        for f in verse['fragments']: spans[f['pageId']].append(verse['id'])
        _,chapter,verse_no=map(int,verse['id'].split('.'))
        if verse_no==1: chapters[verse['fragments'][0]['pageId']].append(chapter)
    reports=[]
    for i,pg in enumerate(state['pages']):
        pid=pg['pageId']
        spec=e['pages'][pid]
        if not spec['lines']: continue
        bottom=max(l['bounds'][1]+l['bounds'][3] for l in spec['lines'])
        folio_top=792-OUTER-proof.word(digits(spec['folio']),50).boundingRect().height()
        gap=folio_top-4-bottom
        final=i+1 in ends
        if probe:
            headings=[p for p in spec['paths'] if p['role']=='chapter-heading']
            expected=[n for n in chapters[pid] if n!=1]
            assert not any(p['role']=='chapter-number' for p in spec['paths'])
            if 1 in chapters[pid]:assert spec['kind']=='opening'
            for n,p in zip(expected,headings,strict=True):
                original=proof.word(digits(n),50)
                ox,oy,_,_=original.boundingRect().getRect()
                px,py,_,_=p['bounds']
                model=pe.encode_path(original.translated(px-ox,py-oy),p['role'])
                for a,b in zip(model['elements'],p['elements'],strict=True):
                    assert a[0]==b[0] and abs(a[1]-b[1])<1e-5 and abs(a[2]-b[2])<1e-5,(i+1,n)
        if probe and not final:
            next_id=spans[state['pages'][i+1]['pageId']][0]
            assert 0<=gap<LEADING,(i+1,gap)
            probe_last_line(proof,state,i,spans[pid][-1],next_id)
        reports.append(dict(nativePage=i+1,printPage=i,firstVerse=spans[pid][0],lastVerse=spans[pid][-1],
                            bookEnding=final,bodyBottomPt=bottom,folioTopPt=folio_top,unusedAboveClearancePt=gap))
    gaps=[r['unusedAboveClearancePt'] for r in reports if not r['bookEnding']]
    return reports,dict(scripturePages=len(reports),bookEndingPages=len(ends),continuingPages=len(gaps),
        meanUnusedPt=round(mean(gaps),3),medianUnusedPt=round(median(gaps),3),maxUnusedPt=round(max(gaps),3),
        continuingPagesWithRoomForWholeLine=sum(g>=LEADING for g in gaps))


def audit(path):
    app=QApplication.instance() or QApplication([])
    proof=Proof()
    old,old_summary=inspect_file(proof,next(PREVIOUS.glob('*.vay')),read(PREVIOUS/'book-index.json'),False)
    new,new_summary=inspect_file(proof,path,read(STAGE/'book-index.json'),True)
    example=[r for r in old if r['nativePage'] in (127,128)]
    assert example[0]['firstVerse']=='02.028.004' and example[-1]['lastVerse']=='02.028.042'
    matched=[r for r in new if r['firstVerse']<=example[-1]['lastVerse'] and r['lastVerse']>=example[0]['firstVerse']]
    result=dict(clearancePt=4,prior=old_summary,revised=new_summary,allPageFootWordProbesPassed=True,
                chapterNumeralsCheckedWithFirstVerses=1123,implicitFirstChapters=66,
                previousExodus28Pages=example,revisedExodus28Pages=matched)
    save_json(STAGE/'page-foot-audit.json',dict(summary=result,pages=new))
    return result
