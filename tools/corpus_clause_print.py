from tools.corpus_clause_revision import *
from tools.corpus_clause_spreads import save_native
from tools import shakespeare_collected as sc
from vayrshemon.native_storage import unpack
from PySide6.QtWidgets import QApplication


def shakespeare():
    ws=sources()
    sc.STAGE=S/'collected-typesetting';sc.STAGE.mkdir(parents=True,exist_ok=True)
    for w in ws:
        us=read(edited(ledger(w)))['units']
        rows=[dict(id=u['id'],text=u['text'],english=u['source'],continuation=u.get('continuesParagraph',u.get('part',0)>0)) for u in us]
        write(sc.STAGE/'sources'/(w['slug']+'.json'),dict(ledgerHash=sha(edited(ledger(w))),rows=rows))
    ref=unpack(read(sc.REFERENCE))['state']
    state=sc.Volume(ref,sc.punctuation_source(ws),ws).compose()
    p=next(H.glob('*.vay'));data=unpack(read(p));oldstate=data['state']
    assert state['printEdition']['assets']==oldstate['printEdition']['assets']
    assert [s['name'] for s in state['printEdition']['sections']]==[s['name'] for s in oldstate['printEdition']['sections']]
    count=sc.verify(state,ws)
    data['state']=state
    save_native(data,p)
    print('Shakespeare print verified and staged',count,len(state['pages']),flush=True)
if __name__=='__main__':
    app=QApplication.instance() or QApplication([])
    shakespeare()

