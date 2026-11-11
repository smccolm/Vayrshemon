"""Assemble the book-local layouts into Workbench spreads and publish one file."""
from copy import deepcopy
from pathlib import Path
import sys
from uuid import uuid4
from compose import (BOOKS, BOTTOM, COMPACT, INNER, OUTER, ROOT, STAGE, TARGET, TITLE, TOP,
                     QApplication, blank_content, digest, mp, pe, read, save_json, unicode_run, unpack, FileSession)


def make_page(prototype,document_id,n,text,name,kind):
    native=deepcopy(prototype)
    side='right' if n%2==0 else 'left'
    left,right=(INNER,OUTER) if side=='right' else (OUTER,INNER)
    if kind=='title': left=right=(INNER+OUTER)/2
    pid=f'page.runin.{n:05}'
    native.update(pageId=pid,name=name,margins=dict(left=mp(left),right=mp(right),top=mp(TOP),bottom=mp(BOTTOM)))
    frame=native['frames'][0]
    frame.update(frameId=f'frame.runin.{n:05}',name=name,x=mp(left),y=mp(TOP),
                 width=mp(612-left-right),height=mp(792-TOP-BOTTOM))
    old=frame['content']['document']
    frame['content']=blank_content(document_id,frame['width'],frame['height'],text)
    model=frame['content']['document']
    model['fonts'],model['styles']=deepcopy(old['fonts']),deepcopy(old['styles'])
    model['title']=name
    model['stories'][0]['blocks']=[dict(blockId='block.1',type='paragraph',direction='ltr',
                                  runs=[unicode_run(text,'run.1','language.vayrshemon')])]
    return native,side


def shift(item,dx):
    for line in item['lines']:
        line['x']+=dx
        line['bounds'][0]+=dx
    for path in item['paths']:
        path['bounds'][0]+=dx
        for element in path['elements']: element[1]+=dx


def assemble():
    state=unpack(read(next(COMPACT.glob('*.vay'))))['state']
    previous=state['printEdition']
    proto=state['pages'][3]
    old_front=state['pages'][:3]
    edition=dict(previous,pages={},verses=[],sections=[])
    state.update(title=TITLE,documentId='document.'+uuid4().hex,pages=[],printEdition=edition,revision=0)
    state['pageNumbering'].update(edgeInsetPt=OUTER)
    state['view'].update(zoom=.8)
    for n,p in enumerate(old_front,1):
        spec=deepcopy(previous['pages'][p['pageId']])
        pg,side=make_page(proto,state['documentId'],n,'',p['name'],spec['kind'])
        spec['side']='center' if n==1 else side
        for image in spec['images']:
            asset=edition['assets'][image['asset']]
            scale=min((612-INNER-OUTER)/asset['width'],(792-TOP-BOTTOM)/asset['height'])
            w,h=asset['width']*scale,asset['height']*scale
            cx=306 if n==1 else (306-(INNER-OUTER)/2)
            image['rect']=[cx-w/2,TOP+(792-TOP-BOTTOM-h)/2,w,h]
        edition['pages'][pg['pageId']]=spec
        state['pages'].append(pg)
    chapters=[];books=[]
    for number,name in enumerate(BOOKS,1):
        book=read(STAGE/'books'/f'{number:02}.json')
        assert book['inputSha256']==digest(STAGE/'input'/f'{number:02}.json')
        source=read(STAGE/'input'/f'{number:02}.json')
        units={u['id']:u for u in source}
        records={u['id']:dict(id=u['id'],sha256=pe.hash_text(u['text']),fragments=[]) for u in source}
        offsets={k:0 for k in units}
        IDs=[r['id'] for page in book['pages'] for r in page['rows']]
        assert [v for i,v in enumerate(IDs) if i==0 or v!=IDs[i-1]]==list(units)
        first=len(state['pages'])+1
        for item in book['pages']:
            n=len(state['pages'])+1
            refs=[units[r['id']]['reference'] for r in item['rows']]
            pg,side=make_page(proto,state['documentId'],n,item['text'],refs[0]+' – '+refs[-1],item['kind'])
            pid=pg['pageId']
            if side=='left': shift(item,OUTER-INNER)
            spec=dict(side=side,kind=item['kind'],folio=n-3,lines=item['lines'],paths=item['paths'],
                      images=[],sourceSha256=pe.hash_text(item['text']))
            edition['pages'][pid]=spec
            if spec['kind']=='opening':
                edition['sections'].append(dict(name=name,number=number,pageId=pid))
            for c in item['chapters']: chapters.append(dict(book=name,chapter=c,nativePage=n))
            for row in item['rows']:
                k=row['id']
                a,b=row['sourceStart'],row['sourceEnd']
                assert a==offsets[k] and a<b
                assert item['text'][row['start']:row['end']]==units[k]['text'][a:b]
                assert records[k]['sha256']==row['sha256']
                records[k]['fragments'].append(dict(pageId=pid,start=row['start'],end=row['end']))
                offsets[k]=b
            state['pages'].append(pg)
        assert all(offsets[k]==len(u['text']) for k,u in units.items())
        edition['verses'].extend(records.values())
        books.append(dict(number=number,name=name,firstNativePage=first,lastNativePage=len(state['pages']),
                          verses=len(units),firstPrintPage=first-1))
    if len(state['pages'])%2:
        pg,side=make_page(proto,state['documentId'],len(state['pages'])+1,'','Blank','blank')
        edition['pages'][pg['pageId']]=dict(side=side,kind='blank',folio=None,lines=[],paths=[],images=[],sourceSha256=pe.hash_text(''))
        state['pages'].append(pg)
    assert len(chapters)==1189 and len(edition['sections'])==66 and len(edition['verses'])==31102
    state['activeFrameId']=state['pages'][0]['frames'][0]['frameId']
    from acanthus import apply, check
    apply(state)
    check(state)
    from dividers import center, check as check_dividers
    center(state)
    check_dividers(state)
    from titles import apply_titles,check_titles
    save_json(STAGE/'book-titles.json',apply_titles(state))
    check_titles(state)
    save_json(STAGE/'book-index.json',books)
    save_json(STAGE/'chapter-index.json',chapters)
    return state


def main():
    if TARGET.exists(): raise FileExistsError(TARGET)
    app=QApplication([])
    state=assemble()
    book=FileSession(ROOT,recovery=False)
    book.remember=lambda p:None
    book.log.emit=lambda *a,**k:None
    try:
        book._restore(state,take_ownership=True)
        book._state=book.capture()
        path=STAGE/TARGET.name
        if not path.exists(): book.save(path,preview_mode='two')
        before=book.capture()
        book.open(path,advance_revision=False)
        assert book.capture()==before and book.saved_page_mode=='two'
        print('Verified save/reopen',len(state['pages']),'native pages',digest(path),flush=True)
    finally: book.finish()


if __name__=='__main__': main()
