"""Write a physical-order duplex PDF from the saved .vay's measured vectors.

Identical glyph outlines share PDF form objects. Positions, marks, artwork and
folio bounds come from the same native typefaces and placements as Workbench.
"""
from base64 import b64decode
from io import BytesIO
import os
from pathlib import Path
import sys
from types import SimpleNamespace
if os.environ.get('VAYRSHEMON_PDF_LIBS'): sys.path.append(os.environ['VAYRSHEMON_PDF_LIBS'])
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas
from pypdf import PdfReader
from PySide6.QtCore import QRectF,Qt
from PySide6.QtGui import QPainterPath,QTextLayout,QTextOption
from compose import EDITION, OUTER, STAGE, TARGET, QApplication,Proof,digest,pe,read,save_json,unpack

PDF_NAME='KJV Bible - Run-in Letter - Printing 2 - Duplex Print.pdf'


def draw_path(canvas,path):
    if path.isEmpty(): return
    pdf=canvas.beginPath()
    i=0
    while i<path.elementCount():
        p=path.elementAt(i)
        if p.isMoveTo(): pdf.moveTo(p.x,p.y)
        elif p.isLineTo(): pdf.lineTo(p.x,p.y)
        else:
            assert p.isCurveTo()
            b,c=path.elementAt(i+1),path.elementAt(i+2)
            pdf.curveTo(p.x,p.y,b.x,b.y,c.x,c.y)
            i+=2
        i+=1
    canvas.drawPath(pdf,stroke=0,fill=1,fillMode=path.fillRule().value)


class Printer:
    def __init__(self,canvas,state):
        self.canvas=canvas
        self.book=SimpleNamespace(state=state,fonts=Proof().fonts)
        self.forms={}

    def glyph(self,raw,gid):
        key=(raw.familyName(),raw.pixelSize(),gid)
        if key not in self.forms:
            assert gid,'Missing print glyph'
            shape=raw.pathForGlyph(gid)
            bounds=shape.boundingRect()
            name=None
            if not shape.isEmpty():
                name=f'g{len(self.forms)}'
                self.canvas.beginForm(name,bounds.left()-.02,bounds.top()-.02,bounds.right()+.02,bounds.bottom()+.02)
                self.canvas.setFillColorRGB(17/255,17/255,17/255)
                draw_path(self.canvas,shape)
                self.canvas.endForm()
            self.forms[key]=(name,bounds)
        return self.forms[key]

    def text(self,text,size,prefix,x,y):
        layout=QTextLayout(text.replace('-',' '),pe.font(self.book,size))
        option=QTextOption()
        option.setWrapMode(QTextOption.WrapMode.NoWrap)
        option.setTextDirection(Qt.LayoutDirection.LeftToRight)
        layout.setTextOption(option)
        layout.setFormats(pe.text_formats(self.book,text,size,prefix,18))
        layout.beginLayout()
        line=layout.createLine()
        line.setLineWidth(100000)
        layout.endLayout()
        total=QRectF()
        for run in layout.glyphRuns():
            raw=run.rawFont()
            for gid,pos in zip(run.glyphIndexes(),run.positions(),strict=True):
                name,bounds=self.glyph(raw,gid)
                if name is None: continue
                dx,dy=x+pos.x(),y+pos.y()-line.ascent()
                self.canvas.saveState()
                self.canvas.translate(dx,dy)
                self.canvas.doForm(name)
                self.canvas.restoreState()
                total=total.united(bounds.translated(dx,dy))
        if '-' in text:
            stroke=QPainterPath()
            pe.punctuation_paths(stroke,text,line,size)
            stroke.translate(x,y)
            draw_path(self.canvas,stroke)
            total=total.united(stroke.boundingRect())
        return total

    def page(self,page,spec):
        c=self.canvas
        c.saveState()
        c.translate(0,792)
        c.scale(1,-1)
        c.setFillColorRGB(17/255,17/255,17/255)
        for item in spec['images']:
            data=self.book.state['printEdition']['assets'][item['asset']]
            x,y,w,h=item['rect']
            c.saveState()
            c.translate(x,y+h)
            c.scale(1,-1)
            c.drawImage(ImageReader(BytesIO(b64decode(data['png']))),0,0,w,h,mask='auto')
            c.restoreState()
        for p in spec['paths']: draw_path(c,pe.decode_path(p))
        src=pe.text_of(page)
        for line in spec['lines']:
            display=line['prefix']+src[line['start']:line['end']]
            rect=self.text(display,26,len(line['prefix']),line['x'],line['baseline'])
            assert max(abs(a-b) for a,b in zip(rect.getRect(),line['bounds']))<.05,(page['name'],line,rect)
        if spec['folio']:
            config=self.book.state['pageNumbering']
            placement=pe.numbering(self.book,page,config,'two',SimpleNamespace(drawings=[],ornaments=[]))
            assert placement['status']=='placed'
            dx,dy=(v/(4/3) for v in placement['origin'])
            actual=self.text(placement['text'],config['sizePt'],0,dx,dy)
            assert max(abs(a-b/(4/3)) for a,b in zip(actual.getRect(),placement['bounds']))<.05
            assert abs((actual.left() if spec['side']=='left' else 612-actual.right())-OUTER)<.01
        c.restoreState()
        c.showPage()


def main():
    app=QApplication([])
    source=STAGE/TARGET.name if (STAGE/TARGET.name).exists() else TARGET
    state=unpack(read(source))['state']
    edition=state['printEdition']
    output=STAGE/PDF_NAME
    c=Canvas(str(output),pagesize=(612,792),pageCompression=1,pdfVersion=(1,5))
    c.setTitle('KJV Bible · Vayrshemon run-in Letter edition · printing 2')
    c.setCreator('Vayrshemon Workbench · duplex binding master')
    c.setPageSize((612,792))
    c.setViewerPreference('Duplex','DuplexFlipLongEdge')
    c.setViewerPreference('PrintScaling','None')
    # Facing display starts with the title alone on the right.
    c._doc.Catalog.setPageLayout('TwoPageRight')
    bookmarks={s['pageId']:s for s in edition['sections']}
    from titles import catalog
    titles={r['book']:r['roman'] for r in catalog()}
    series=[]
    printer=Printer(c,state)
    for n,page in enumerate(state['pages'],1):
        pid=page['pageId']
        spec=edition['pages'][pid]
        if spec['kind']=='blank':
            assert n in (2,len(state['pages'])) and not pe.text_of(page) and not spec['lines']
            continue
        physical=len(series)+1
        if n>1: assert physical==n-1
        if physical==1: assert spec['kind']=='title'
        else: assert spec['side']==('right' if physical%2 else 'left')
        if physical==2: assert spec['kind']=='frontispiece'
        if physical==3: assert spec['kind']=='opening' and spec['folio']==1
        if pid in bookmarks:
            c.bookmarkPage(pid)
            name=bookmarks[pid]['name']
            c.addOutlineEntry(name+' · '+titles[name],pid)
        printer.page(page,spec)
        series.append(n)
        if physical%200==0: print('Printed physical page',physical,flush=True)
    c.save()
    doc=PdfReader(output)
    assert len(doc.pages)==len(series)
    assert all([float(v) for v in p.mediabox]==[0.,0.,612.,792.] for p in doc.pages)
    assert doc.trailer['/Root']['/PageLayout']=='/TwoPageRight'
    prefs=doc.trailer['/Root']['/ViewerPreferences']
    assert prefs['/Duplex']=='/DuplexFlipLongEdge' and prefs['/PrintScaling']=='/None'
    assert len(doc.outline)==66
    assert [b.title for b in doc.outline]==[r['book']+' · '+r['roman'] for r in catalog()]
    receipt=dict(nativeSha256=digest(source),pdfSha256=digest(output),physicalPages=len(series),duplexSheets=(len(series)+1)//2,
        printToNativePage=series,pageSizePt=[612,792],insidePt=72,outsidePt=54,verifiedVectorBounds=True,
        glyphOutlines=len(printer.forms),duplex='long-edge',printScaling='none',firstFaces=['Title (recto)','Frontispiece (verso)','Genesis opening (recto)'])
    save_json(STAGE/'print-validation.json',receipt)
    print('Verified binding master',len(series),'pages',receipt['duplexSheets'],'sheets',receipt['pdfSha256'],flush=True)


if __name__=='__main__': main()
