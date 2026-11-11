"""Export the saved collected edition's measured lines at full Letter size."""
import base64
from io import BytesIO
import os
import re
import sys
from pypdf import PdfReader
from PIL import Image
from PySide6.QtCore import QRectF
if os.environ.get('VAYRSHEMON_PDF_LIBS'):
    sys.path.append(os.environ['VAYRSHEMON_PDF_LIBS'])
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.utils import ImageReader

from tools.shakespeare_collected import (BODY, DEST, MEASURE, STAGE, TITLE, Typesetter, digest,
                                        pe, read, sources, unpack, verify, write)
from vayrshemon.page_numbering import digits


TARGET = DEST.with_name(TITLE + ' - Duplex Print.pdf')


class VectorPrint:
    def __init__(self, canvas, proof):
        self.canvas=canvas
        self.proof=proof
        self.glyphs={}
        self.form_count=0

    def glyph(self, raw, gid, cache):
        if gid not in cache:
            if not gid:
                raise ValueError('Missing PDF glyph')
            path=raw.pathForGlyph(gid)
            b=path.boundingRect()
            name=None
            if not path.isEmpty():
                name=f'g{self.form_count}'
                self.form_count+=1
                c=self.canvas
                c.beginForm(name,b.left()-.01,b.top()-.01,b.right()+.01,b.bottom()+.01)
                p=c.beginPath()
                i=0
                while i<path.elementCount():
                    a=path.elementAt(i)
                    if a.isMoveTo(): p.moveTo(a.x,a.y)
                    elif a.isLineTo(): p.lineTo(a.x,a.y)
                    else:
                        b1,b2=path.elementAt(i+1),path.elementAt(i+2)
                        p.curveTo(a.x,a.y,b1.x,b1.y,b2.x,b2.y)
                        i+=2
                    i+=1
                c.setFillColorRGB(17/255,17/255,17/255)
                c.drawPath(p,stroke=0,fill=1,fillMode=path.fillRule().value)
                c.endForm()
            cache[gid]=(name,b)
        return cache[gid]

    def draw(self,text,size,x,y,word_gap=0):
        c=self.canvas
        layout=self.proof.layout(text,size)
        ascent=layout.lineAt(0).ascent()
        total=QRectF()
        c.addLiteral('/Span << /ActualText <FEFF'+text.encode('utf-16-be').hex()+'> >> BDC')
        c.saveState()
        last_x=last_y=0
        for run in pe.spaced_runs(layout,word_gap):
            raw=run.rawFont()
            cache=self.glyphs.setdefault((raw.familyName(),raw.pixelSize()),{})
            for gid,pos in zip(run.glyphIndexes(),run.positions(),strict=True):
                name,rect=self.glyph(raw,gid,cache)
                if not name: continue
                dx,dy=x+pos.x(),y+pos.y()-ascent
                c.translate(dx-last_x,dy-last_y)
                c.doForm(name)
                last_x,last_y=dx,dy
                total=total.united(rect.translated(dx,dy))
        c.restoreState()
        c.addLiteral('EMC')
        return total


def export():
    state = unpack(read(DEST))['state']
    count = verify(state, sources())
    edition = state['printEdition']
    proof = Typesetter(next(f for f in state['fontSources'] if f['fontId'] == pe.DRAMA_PUNCT))
    staged=STAGE/TARGET.name
    pdf=Canvas(str(staged),pagesize=(612,792),pageCompression=1,pdfVersion=(1,6))
    pdf.setTitle(TITLE)
    pdf.setCreator('Vayrshemon Workbench')
    pdf.setViewerPreference('Duplex','DuplexFlipLongEdge')
    pdf.setViewerPreference('PrintScaling','None')
    pdf._doc.Catalog.setPageLayout('TwoPageRight')
    # Sheet 1 recto is the binding blank. Native spreads 1|2, 3|4, ...
    # then occupy facing verso|recto pages both in Acrobat and in the binding.
    pdf.addPageLabel(0,prefix='Binding blank')
    pdf.showPage()
    pdf.addPageLabel(1,style='ARABIC',start=1)
    pdf._doc.Catalog.OpenAction=pdf.bookmarkPage('native-title-spread')
    printer=VectorPrint(pdf,proof)
    cfg = state['pageNumbering']
    section_names = {s['pageId']:s['name'] for s in edition['sections']}
    bookmarks = []
    for n,page in enumerate(state['pages'],1):
        pid=page['pageId']
        spec=edition['pages'][pid]
        text=pe.text_of(page)
        assert spec['side']==('center' if n==1 else 'left' if n%2 else 'right')
        left=int(page['margins']['left'])/1e6
        if pid in section_names:
            bookmarks.append((section_names[pid],pdf.getPageNumber()-1))
            pdf.bookmarkPage(pid)
            pdf.addOutlineEntry(section_names[pid],pid)
        for item in spec['images']:
            x,y,w,h=item['rect']
            image=edition['assets'][item['asset']]
            raw=BytesIO(base64.b64decode(image['png']))
            pdf.addLiteral('/Figure << /Alt (The Collected Works of William Shakespeare. Illustrated title page.) >> BDC')
            pdf.drawImage(ImageReader(raw),x,792-y-h,w,h,mask='auto')
            pdf.addLiteral('EMC')
        pdf.translate(0,792)
        pdf.scale(1,-1)
        bounds=[]
        for rule in spec['paths']:
            assert rule['role']=='contents-column-divider'
            x,y,width,height=rule['bounds']
            pdf.setFillColorRGB(17/255,17/255,17/255)
            pdf.rect(x,y,width,height,stroke=0,fill=1)
        for line in spec['lines']:
            visible=text[line['start']:line['end']]
            size=line.get('sizePt',BODY)
            gap=line.get('wordGapPt',0)
            rect=printer.draw(visible,size,line['x'],line['baseline'],gap)
            assert max(abs(a-b) for a,b in zip(rect.getRect(),line['bounds']))<.01,(n,visible)
            if gap:
                assert abs(rect.right()-left-MEASURE)<.01 and abs(rect.left()-left)<.01,(n,visible)
            bounds.append(rect)
        if spec['folio']:
            value=digits(spec['folio'])
            size=cfg['sizePt']
            rect=proof.ink(value,size)
            position=cfg[spec['side']]
            assert position['visible'] and position['vertical']=='bottom'
            on_left=position['horizontal']=='left'
            assert on_left==(pdf.getPageNumber()%2==0)
            x=cfg['edgeInsetPt']-rect.left() if on_left else 612-cfg['edgeInsetPt']-rect.right()
            y=792-cfg['edgeInsetPt']-rect.bottom()
            obstacle=rect.translated(x,y).adjusted(-4,-4,4,4)
            assert all(not obstacle.intersects(r) for r in bounds), f'Folio overlap on page {n}'
            folio_box=printer.draw(value,size,x,y)
            assert abs((folio_box.left() if on_left else 612-folio_box.right())-cfg['edgeInsetPt'])<.01,n
        pdf.showPage()
        if n%250==0: print(f'{n} PDF pages checked against native ink bounds',flush=True)
    pdf.save()
    check=PdfReader(staged)
    physical_pages=len(check.pages)
    assert physical_pages==len(state['pages'])+1
    assert check.page_layout=='/TwoPageRight'
    assert check.page_labels==['Binding blank', *map(str,range(1,physical_pages))]
    assert check.get_destination_page_number(check.open_destination)==1
    assert all(tuple(map(float,p.mediabox))==(0,0,612,792) for p in check.pages)
    assert [(b.title,check.get_destination_page_number(b)) for b in check.outline]==bookmarks
    assert check.viewer_preferences.duplex=='/DuplexFlipLongEdge' and check.viewer_preferences.print_scaling=='/None'
    assert not check.pages[0].extract_text().strip() and not check.pages[2].extract_text().strip()
    title_art,=edition['pages'][state['pages'][0]['pageId']]['images']
    asset=edition['assets'][title_art['asset']]
    embedded,=check.pages[1].images
    with Image.open(BytesIO(base64.b64decode(asset['png']))) as original:
        assert original.size==embedded.image.size
        assert original.convert('RGB').tobytes()==embedded.image.convert('RGB').tobytes()
    for page,printed in zip(state['pages'],check.pages[1:],strict=True):
        spec=edition['pages'][page['pageId']]
        source=pe.text_of(page)
        expected=[source[line['start']:line['end']] for line in spec['lines']]
        if spec['folio']: expected.append(digits(spec['folio']))
        material=printed['/Contents'].get_object().get_data()
        actual=[bytes.fromhex(s.decode()).decode('utf-16-be') for s in re.findall(rb'/ActualText <FEFF([0-9a-f]+)>',material)]
        assert actual==expected,page['pageId']
    check.close()
    staged.replace(TARGET)
    write(DEST.parent/'edition-manifest.json',dict(title=TITLE, nativeSha256=digest(DEST),
          pdfSha256=digest(TARGET), typeSizePt=BODY, leadingPt=18, marginsPt=dict(inside=72,outside=54,top=48,bottom=71),
          pages=len(state['pages']), physicalPrintPages=physical_pages, sheets=(physical_pages+1)//2,
          leadingBindingBlanks=1, plays=38, poetryWorks=4,
          sourceUnits=count, contentsNumbers='Unta folios of all 42 work openings', bodyAlignment='Justified wrapped lines; natural paragraph endings',
          titleArtwork=dict(sha256=title_art['asset'],rectPt=title_art['rect'],pixels=[asset['width'],asset['height']]),
          folios='Outside in native spreads and physical duplex order', sources=[
              dict(title=w['title'], file=w['output'], sha256=w['sha256']) for w in sources()]))
    print(f'Passed duplex PDF checks for {len(state["pages"])} pages and {count} native source units.',flush=True)
