"""Replace only changed print page content and preserve the sealed PDF's navigation."""
import io,os
from tools.corpus_clause_revision import *
from PySide6.QtWidgets import QApplication
from vayrshemon.native_storage import unpack
from vayrshemon import print_edition as pe
from vayrshemon.page_numbering import digits
from pypdf import PdfReader,PdfWriter
from pypdf.generic import NameObject
sys.path.append(os.environ['VAYRSHEMON_PDF_LIBS'])
from reportlab.pdfgen.canvas import Canvas
from tools.shakespeare_collected import Typesetter
from tools.shakespeare_collected_pdf import VectorPrint
def play_page(c,printer,proof,state,pg,spec):
    c.saveState();c.translate(0,792);c.scale(1,-1)
    assert not spec['paths'] and not spec['images']
    txt=pe.text_of(pg)
    for line in spec['lines']:
        t=txt[line['start']:line['end']]
        bounds=printer.draw(t,line.get('sizePt',26),line['x'],line['baseline'],line.get('wordGapPt',0))
        assert max(abs(a-b) for a,b in zip(bounds.getRect(),line['bounds']))<.02,(pg['name'],line)
    cfg=state['pageNumbering']
    if spec['folio']:
        val=digits(spec['folio']);size=cfg['sizePt'];bounds=proof.ink(val,size)
        left=cfg[spec['side']]['horizontal']=='left'
        x=cfg['edgeInsetPt']-bounds.left() if left else 612-cfg['edgeInsetPt']-bounds.right()
        printer.draw(val,size,x,792-cfg['edgeInsetPt']-bounds.bottom())
    c.restoreState();c.showPage()
def render(group):
    folder=BP if group=='bible' else H
    src=next(folder.glob('*.vay'));pdf=next(folder.glob('*.pdf'))
    old,new=[unpack(read(p))['state'] for p in (src,edited(src))]
    ed=new['printEdition'];olded=old['printEdition']
    assert ed['sections']==olded['sections'] and len(new['pages'])==len(old['pages'])
    diff=[(n,pg,ed['pages'][pg['pageId']]) for n,pg in enumerate(new['pages'],1) if ed['pages'][pg['pageId']]!=olded['pages'][pg['pageId']]]
    assert all(spec['kind'] in ('opening','body') for n,p,spec in diff)
    proof=Typesetter(next(f for f in new['fontSources'] if f['fontId']==pe.DRAMA_PUNCT)) if group!='bible' else None
    out=io.BytesIO();c=Canvas(out,pagesize=(612,792),pageCompression=1)
    if group=='bible':
        sys.path.insert(0,str(BP/'Authoring'))
        from binding_pdf import Printer
        printer=Printer(c,new)
    else:printer=VectorPrint(c,proof)
    for n,pg,spec in diff:
        if group=='bible':printer.page(pg,spec)
        else:play_page(c,printer,proof,new,pg,spec)
    c.save();out.seek(0);changed=PdfReader(out)
    original=PdfReader(pdf);writer=PdfWriter(clone_from=original)
    target=revised(pdf);target.parent.mkdir(parents=True,exist_ok=True)
    for (n,pg,spec),page in zip(diff,changed.pages,strict=True):
        idx=n-2 if group=='bible' else n
        for key in ('/Contents','/Resources'):
            writer.pages[idx][NameObject(key)]=page.raw_get(key).clone(writer)
    with target.open('wb') as f:writer.write(f)
    check=PdfReader(target)
    assert len(check.pages)==len(original.pages) and check.page_layout==original.page_layout
    assert [(e.title,check.get_destination_page_number(e)) for e in check.outline]==[(e.title,original.get_destination_page_number(e)) for e in original.outline]
    if group=='shakespeare':
        for pg,pp in zip(new['pages'],check.pages[1:],strict=True):
            spec=ed['pages'][pg['pageId']];t=pe.text_of(pg)
            vals=[t[l['start']:l['end']] for l in spec['lines']]
            if spec['folio']:vals.append(digits(spec['folio']))
            actual=[bytes.fromhex(s.decode()).decode('utf-16-be') for s in re.findall(rb'/ActualText <FEFF([0-9a-f]+)>',pp.get_contents().get_data())]
            assert vals==actual,pg['pageId']
    else:
        for (n,pg,spec),page in zip(diff,changed.pages,strict=True):
            assert page.get_contents().get_data()==check.pages[n-2].get_contents().get_data()
    write(S/(group+'-pdf.json'),dict(nativePages=[n for n,p,s in diff],sha256=sha(target),pages=len(check.pages)))
    print(group,len(diff),'changed native pages',len(check.pages),'PDF pages',flush=True)
if __name__=='__main__':
    app=QApplication([]);render(sys.argv[1])

