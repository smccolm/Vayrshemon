"""Reflow the changed books with the original Printing 2 compositor."""
import sys,subprocess
from concurrent.futures import ThreadPoolExecutor
from tools.corpus_clause_revision import *
from tools.corpus_clause_spreads import save_native
sys.path.insert(0,str(BP/'Authoring'))
import compose as layout
from publish import shift
from dividers import rule
from verify import verses_from_print
from PySide6.QtWidgets import QApplication
from vayrshemon import print_edition as pe
from vayrshemon.native_storage import unpack
layout.STAGE=S/'bible-typesetting'
def centered(paths,page):
    output=[]
    for item in paths:
        if item['role']!='chapter-heading':
            output.append(item);continue
        prev=output.pop();assert prev['role']=='ornament'
        rx,_,rw,weight=prev['bounds'];x,y,w,h=item['bounds'];mid=y+h/2
        if rw>100:
            a=int(page['margins']['left'])/1e6;b=612-int(page['margins']['right'])/1e6;gap=8.
        else:a,b,gap=x,rx+rw,3.
        origin=(a+b-w)/2
        glyph=pe.encode_path(pe.decode_path(item).translated(origin-x,0),'chapter-heading')
        output.extend((rule(a,origin-gap,mid,weight,'chapter-rule-left'),glyph,rule(origin+w+gap,b,mid,weight,'chapter-rule-right')))
    return output
def book(n):
    app=QApplication([]);layout.compose_book(n)
def build():
    p=next(BP.glob('*.vay'));data=unpack(read(p));state=data['state'];ed=state['printEdition']
    datafile=edited(B/'complete-translation-ledger.json');units=read(datafile)['units']
    changes=read(S/'changes.json')['bible'];books=sorted({int(k[:2]) for k in changes})
    for n in books:
        rows=[{k:u[k] for k in ('id','reference','chapter','verse','text')} for u in units if int(u['id'][:2])==n]
        write(layout.STAGE/'input'/f'{n:02}.json',rows)
    def launch(n):
        file=layout.STAGE/'books'/f'{n:02}.json'
        if file.exists() and read(file)['inputSha256']==sha(layout.STAGE/'input'/f'{n:02}.json'):return
        subprocess.run([sys.executable,'-B','-u','-m','tools.corpus_clause_bible_print',str(n)],check=True)
    with ThreadPoolExecutor(max_workers=7) as pool:list(pool.map(launch,books))
    docindex=read(BP/'book-index.json');chapterindex=read(BP/'chapter-index.json')
    indices={r['number']:r for r in docindex};cu={(r['book'],r['chapter']):r for r in chapterindex}
    target={u['id']:u for u in units};records={r['id']:r for r in ed['verses']}
    baseline=read(BP/'book-index.json')
    for n in books:
        index=indices[n];first=index['firstNativePage'];last=index['lastNativePage'];newpages=read(layout.STAGE/'books'/f'{n:02}.json')['pages']
        assert len(newpages)==last-first+1,(n,len(newpages),last-first+1)
        for id,r in records.items():
            if int(id[:2])==n:r.update(sha256=pe.hash_text(target[id]['text']),fragments=[])
        for position,item in enumerate(newpages,first):
            pg=state['pages'][position-1];pid=pg['pageId'];spec=ed['pages'][pid]
            for ch in item['chapters']:cu[index['name'],ch]['nativePage']=position
            assert spec['kind']==item['kind']
            if spec['side']=='left':shift(item,layout.OUTER-layout.INNER)
            if item['kind']=='opening':
                headers=spec['paths'];stop=next((j for j,it in enumerate(headers) if it['role']=='chapter-rule-left'),len(headers))
                paths=item['paths'];start=next((j-1 for j,it in enumerate(paths) if it['role']=='chapter-heading'),len(paths))
                paths=headers[:stop]+centered(paths[start:],pg)
            else:paths=centered(item['paths'],pg)
            t=item['text'];spec.update(paths=paths,lines=item['lines'],sourceSha256=pe.hash_text(t))
            refs=[target[r['id']]['reference'] for r in item['rows']];pg['name']=refs[0]+' – '+refs[-1]
            frame=pg['frames'][0];frame['name']=frame['content']['document']['title']=pg['name']
            run,=frame['content']['document']['stories'][0]['blocks'][0]['runs'];run['text']=t
            for r in item['rows']:
                assert t[r['start']:r['end']]==target[r['id']]['text'][r['sourceStart']:r['sourceEnd']]
                records[r['id']]['fragments'].append(dict(pageId=pid,start=r['start'],end=r['end']))
    write(revised(BP/'chapter-index.json'),chapterindex)
    ed['ledgerSha256']=sha(datafile);assert verses_from_print(state)==[(u['id'],u['text']) for u in units]
    pe.validate(state);save_native(data,p)
    print('Verified all Bible print verses after reflow',books,flush=True)
if __name__=='__main__':
    if len(sys.argv)>1:book(int(sys.argv[1]))
    else:build()

