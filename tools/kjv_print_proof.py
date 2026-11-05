"""A separate Letter/duplex design proof. Never compiles or changes the Bible.

All body text is copied verbatim from the sealed 280 ledger. Qt shapes the
hash-verified Thimfora master; body text retains original vector outlines.
Supplied title/frontispiece PNGs are placed intact at their native resolution.
This deliberately small proof is not a complete single-column Bible edition.
"""
from dataclasses import dataclass, field
from pathlib import Path
import argparse
import hashlib
import json
import math
import tempfile

from PySide6.QtCore import QPointF, QRectF, QSizeF, Qt
from PySide6.QtGui import (QColor, QFont, QImage, QPageLayout, QPageSize, QPainter,
                          QPainterPath, QPdfWriter, QTextCharFormat,
                          QTextLayout, QTextOption, QTransform)
from PySide6.QtWidgets import QApplication
from pypdf import PdfReader, PdfWriter

from vayrshemon.fonts import FontRegistry
from vayrshemon.page_numbering import MASTER, digits

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'Saves/KJV Bible v0.10-kjv.280'
SOURCE_SHA = 'a70a7e00b9f915dd9126668dc2af3c0c3078632bd5b5aa72ad50789b7f437754'
LEDGER_SHA = '76cd000f2b8b6ec7b8850dbada9cf3deacb9e2239d9b7dafd1e89016b79081f6'
PROOF_VERSION = 'letter-proof.3'
WIDTH, HEIGHT = 612., 792.
INNER, OUTER, TOP = 45., 27., 27.
BINDING_OFFSET = (INNER-OUTER)/2  # Exactly +/- 9 pt from the physical center.
ART_DIRECTORY = ROOT/'Inputs/Print artwork'
TITLE_ART = ART_DIRECTORY/'Title Page.png'
FRONTIS_ART = ART_DIRECTORY/'Engraved acanthus frontispiece with foliate knot.png'
BODY_SIZE, LEADING, VERSE_SIZE = 36., 28., 24.
BODY_BOTTOM, FOLIO_INSET, FOLIO_SIZE = 729., 28., 50.
INK, BLUE, GOLD = '#111111', '#153c57', '#957535'


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write_json(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


class QuietLog:
    def emit(self, *args, **kwargs):
        pass


@dataclass
class Line:
    start: int
    end: int
    path: QPainterPath
    width: float


@dataclass
class Page:
    kind: str
    physical: int
    folio: int | None = None
    elements: list = field(default_factory=list)
    records: list = field(default_factory=list)
    images: list = field(default_factory=list)

    @property
    def left(self):
        return INNER if self.physical % 2 else OUTER

    @property
    def right(self):
        return WIDTH - (OUTER if self.physical % 2 else INNER)

    @property
    def center(self):
        return (self.left+self.right)/2

    @property
    def binding_offset(self):
        return self.center-WIDTH/2


class Proof:
    def __init__(self,title_art=None,frontispiece_art=None):
        self.fonts = FontRegistry(ROOT, QuietLog())
        self.face = self.fonts.resolve(MASTER)
        self.pages = []
        self.coverage = []
        self._paths = {}
        if bool(title_art)!=bool(frontispiece_art):
            raise ValueError('Supply both title and frontispiece artwork')
        self.artwork={}
        for role,path in [('title-page',title_art),('frontispiece',frontispiece_art)]:
            if path:
                path=Path(path).resolve(strict=True)
                image=QImage(str(path))
                if image.isNull():raise ValueError('Cannot decode supplied artwork: '+str(path))
                self.artwork[role]=(image,dict(source=str(path),sha256=digest(path),
                                             pixelSize=[image.width(),image.height()]))

    def font(self, size):
        font = QFont(self.face.family)
        font.setPixelSize(round(size))  # Canvas coordinates are physical points.
        font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
        font.setStyleStrategy(QFont.StyleStrategy.NoFontMerging)
        return font

    def lines(self, text, width, size=BODY_SIZE, prefix=0, emergency=False, punctuation=False, verse_size=VERSE_SIZE):
        if any(ord(c) not in self.face.cmap and not c.isspace() and not (punctuation and c in '-()[]') for c in text):
            raise ValueError('Proof text contains an unsupported Thimfora scalar')
        if any(ord(c) > 0xffff for c in text):
            raise ValueError('Proof source needs explicit UTF-16 index conversion')
        layout = QTextLayout(text.replace('-',' ') if punctuation else text, self.font(size))
        option = QTextOption()
        option.setWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere if emergency else QTextOption.WrapMode.WordWrap)
        option.setTextDirection(Qt.LayoutDirection.LeftToRight)
        layout.setTextOption(option)
        if prefix:
            fmt = QTextCharFormat()
            fmt.setFont(self.font(verse_size))
            span = QTextLayout.FormatRange()
            span.start, span.length, span.format = 0, prefix, fmt
            layout.setFormats([span])
        if punctuation:
            from vayrshemon.print_edition import text_formats
            layout.setFormats(text_formats(self,text,size,prefix,verse_size))
        layout.beginLayout()
        native = []
        while True:
            line = layout.createLine()
            if not line.isValid():
                break
            line.setLineWidth(width)
            line.setPosition(QPointF(0, len(native) * LEADING))
            native.append(line)
        layout.endLayout()
        result = []
        for line in native:
            path = QPainterPath()
            for run in layout.glyphRuns(line.textStart(), line.textLength()):
                raw = run.rawFont()
                if raw.familyName() != self.face.family and not (punctuation and raw.familyName()==self.fonts.resolve('font:9ba7c6f12d40ea8a0aafb8f07a69f8b65b424e374c6da95235a45edeb6292c52:0').family):
                    raise ValueError('Unexpected font substitution')
                for gid, pos in zip(run.glyphIndexes(), run.positions()):
                    if not gid:
                        raise ValueError('Missing glyph')
                    glyph = raw.pathForGlyph(gid)
                    path.addPath(QTransform.fromTranslate(pos.x(), pos.y() - line.y() - line.ascent()).map(glyph))
            if punctuation:
                from vayrshemon.print_edition import punctuation_paths
                punctuation_paths(path,text,line,size)
            if line.naturalTextWidth() > width + .1:
                raise ValueError('Unbreakable word exceeds the print measure')
            result.append(Line(line.textStart(), line.textStart() + line.textLength(), path, line.naturalTextWidth()))
        return result

    def word(self, text, size):
        key = (text, size)
        if key not in self._paths:
            lines = self.lines(text, 10000, size)
            assert len(lines) == 1
            self._paths[key] = lines[0].path
        return self._paths[key]

    def put(self, page, path, x=0., y=0., color=INK, role='ornament', **metadata):
        placed = QTransform.fromTranslate(x, y).map(path)
        bounds = placed.boundingRect()
        if not bounds.isEmpty() and not QRectF(18, 18, WIDTH-36, HEIGHT-36).contains(bounds):
            raise ValueError(f'Outside printable safety box: {role} {bounds}')
        page.elements.append((placed, color))
        record = dict(role=role, bounds=[bounds.x(), bounds.y(), bounds.width(), bounds.height()], **metadata)
        page.records.append(record)
        return bounds

    def centered(self, page, text, size, y, color=INK, role='heading'):
        path = self.word(text, size)
        bounds = path.boundingRect()
        return self.put(page, path, page.center-bounds.width()/2-bounds.x(), y-bounds.y(), color, role, text=text)

    def art_page(self,role,physical):
        """Place the entire supplied canvas; never crop, repaint or regenerate it."""
        import numpy as np
        page=Page(role,physical);self.pages.append(page)
        image,provenance=self.artwork[role]
        scale=min((WIDTH-18)/image.width(),(HEIGHT-18)/image.height())
        width,height=image.width()*scale,image.height()*scale
        rect=QRectF(page.center-width/2,(HEIGHT-height)/2,width,height)
        if not QRectF(0,0,WIDTH,HEIGHT).contains(rect):
            raise ValueError('Artwork canvas would be clipped')
        # The supplied canvases include white borders. Check the dark artwork
        # itself against the printer-safe region, without removing those borders.
        rgba=image.convertToFormat(QImage.Format.Format_RGBA8888)
        pixels=np.frombuffer(rgba.constBits(),dtype=np.uint8).reshape(rgba.height(),rgba.bytesPerLine())
        pixels=pixels[:,:rgba.width()*4].reshape(rgba.height(),rgba.width(),4)
        visible=(pixels[:,:,:3].min(axis=2)<180)&(pixels[:,:,3]>128)
        yy,xx=np.nonzero(visible)
        if not len(xx):raise ValueError('Supplied artwork has no visible ink')
        ink=QRectF(rect.x()+int(xx.min())*scale,rect.y()+int(yy.min())*scale,
                   (int(xx.max())-int(xx.min())+1)*scale,(int(yy.max())-int(yy.min())+1)*scale)
        if not QRectF(18,18,WIDTH-36,HEIGHT-36).contains(ink):
            raise ValueError('Supplied artwork leaves the printer-safe region')
        page.images.append((image,rect))
        page.records.append(dict(role='supplied-artwork',bounds=[rect.x(),rect.y(),rect.width(),rect.height()],
                                 inkBounds=[ink.x(),ink.y(),ink.width(),ink.height()],
                                 effectiveDpi=72/scale,bindingOffsetPt=page.binding_offset,**provenance))

    def fitted_glyph(self, page, text, box, color=INK, role='ornament'):
        original = self.word(text, 200)
        b = original.boundingRect()
        scale = min(box.width()/b.width(), box.height()/b.height())
        shaped = QTransform.fromScale(scale, scale).map(original)
        b = shaped.boundingRect()
        self.put(page, shaped, box.center().x()-b.center().x(), box.center().y()-b.center().y(), color, role, text=text)

    def stroke(self, page, path, width=.6, color=INK):
        from PySide6.QtGui import QPainterPathStroker
        stroker = QPainterPathStroker()
        stroker.setWidth(width)
        self.put(page, stroker.createStroke(path), color=color)

    def rule(self, page, x1, y1, x2, y2, color=INK, width=.6):
        path = QPainterPath(QPointF(x1, y1))
        path.lineTo(x2, y2)
        self.stroke(page, path, width, color)

    def diamond(self, page, cx, cy, radius=3., color=INK):
        path = QPainterPath(QPointF(cx, cy-radius))
        for x,y in [(cx+radius,cy),(cx,cy+radius),(cx-radius,cy)]:
            path.lineTo(x,y)
        path.closeSubpath()
        self.put(page,path,color=color)

    def border(self, page, box, color=BLUE):
        outer=QPainterPath();outer.addRect(box)
        inner=QPainterPath();inner.addRect(box.adjusted(5,5,-5,-5))
        self.stroke(page,outer,.8,color);self.stroke(page,inner,.35,color)
        for x in (box.left(),box.right()):
            for y in (box.top(),box.bottom()):
                self.diamond(page,x,y,3,color)

    def rosette(self, page, cx, cy, radius, petals=12, color=GOLD):
        # Engraved geometric ornament; no invented script characters.
        for i in range(petals):
            angle=math.tau*i/petals
            path=QPainterPath(QPointF(0,-radius))
            path.cubicTo(radius*.28,-radius*.72,radius*.22,-radius*.16,0,0)
            path.cubicTo(-radius*.22,-radius*.16,-radius*.28,-radius*.72,0,-radius)
            trans=QTransform().translate(cx,cy).rotate(math.degrees(angle))
            self.stroke(page,trans.map(path),.55,color)
        ring=QPainterPath();ring.addEllipse(QPointF(cx,cy),radius,radius)
        self.stroke(page,ring,.6,color)

    def vine(self, page, x, y, length, rotation=0, color=GOLD):
        """A small engraved stem with paired leaves and fine vein strokes."""
        transform=QTransform().translate(x,y).rotate(rotation)
        stem=QPainterPath(QPointF(0,0))
        stem.cubicTo(length*.3,-12,length*.65,12,length,0)
        self.stroke(page,transform.map(stem),.7,color)
        for index in range(1,8):
            px=length*index/9
            for sign in (-1,1):
                leaf=QPainterPath(QPointF(px,0))
                leaf.cubicTo(px-3,sign*8,px+4,sign*20,px+12,sign*22)
                leaf.cubicTo(px+16,sign*10,px+9,sign*3,px,0)
                self.stroke(page,transform.map(leaf),.5,color)
                vein=QPainterPath(QPointF(px,0));vein.lineTo(px+12,sign*22)
                self.stroke(page,transform.map(vein),.3,color)

    def cover(self):
        if self.artwork:
            self.art_page('title-page',1)
            return
        page=Page('cover',1);self.pages.append(page)
        self.border(page,QRectF(36,36,540,720))
        for x,y,angle in [(66,65,0),(546,65,180),(66,727,0),(546,727,180)]:
            self.vine(page,x,y,90,angle)
        self.centered(page,'Govis',105,91,BLUE,'cover-title')
        self.rule(page,228,161,384,161,GOLD)
        self.rosette(page,306,389,156,24)
        self.rosette(page,306,389,135,12,BLUE)
        # Memon, the user's chosen book/app emblem, optically centered by ink.
        self.fitted_glyph(page,'M',QRectF(221,310,170,158),BLUE,'Memon')
        self.centered(page,'TÍnvÅl',56,607,BLUE,'cover-subtitle')
        self.diamond(page,306,690,4,GOLD)

    def frontispiece(self):
        if self.artwork:
            self.art_page('frontispiece',len(self.pages)+1)
            return
        page=Page('frontispiece',len(self.pages)+1);self.pages.append(page)
        # One enclosure contains three distinct centers and twelve paths.
        # An original plurality/singularity emblem, not a newly attested glyph.
        self.border(page,QRectF(36,36,540,720))
        self.vine(page,109,101,157,0)
        self.vine(page,503,101,157,180)
        self.vine(page,109,702,157,0)
        self.vine(page,503,702,157,180)
        self.rosette(page,306,351,188,24,BLUE)
        for i in range(12):
            a=math.tau*i/12
            x,y=306+188*math.sin(a),351+188*math.cos(a)
            self.diamond(page,x,y,3,GOLD)
        centers=[(306,266),(232.4,394),(379.6,394)]
        for cx,cy in centers:
            self.rosette(page,cx,cy,58,12,GOLD)
        path=QPainterPath(QPointF(306,266))
        path.cubicTo(155,254,135,438,232.4,394)
        path.cubicTo(306,535,465,438,379.6,394)
        path.cubicTo(477,280,324,167,306,266)
        self.stroke(page,path,1.2,BLUE)
        self.fitted_glyph(page,'M',QRectF(282,319,48,64),BLUE)
        # Exact attested pronouns: plural-I and singular-we, supplied below.
        self.centered(page,self.plural_i+'   '+self.singular_we,54,608,BLUE,'frontispiece-caption')
        self.rule(page,234,658,378,658,GOLD)

    def new_body_page(self, opening=False):
        folio=1+sum(p.folio is not None for p in self.pages)
        page=Page('illuminated-opening' if opening else 'body',len(self.pages)+1,folio)
        self.pages.append(page)
        if opening:
            self.border(page,QRectF(page.left,30,page.right-page.left,112))
            self.vine(page,page.left+26,87,132)
            self.vine(page,page.right-26,87,132,180)
            self.centered(page,'Pá',100,53,BLUE,'book-title')
            self.centered(page,digits(1),42,107,GOLD,'chapter-number')
            return page,175.
        return page,TOP+20

    def folio(self,page):
        path=self.word(digits(page.folio),FOLIO_SIZE)
        b=path.boundingRect()
        x=WIDTH-FOLIO_INSET-b.right() if page.physical%2 else FOLIO_INSET-b.left()
        y=HEIGHT-FOLIO_INSET-b.bottom()
        bounds=self.put(page,path,x,y,role='folio',value=page.folio,unta=digits(page.folio))
        for record in page.records:
            if record['role'] in ('body','verse-marker','illuminated-initial','chapter-heading'):
                other=QRectF(*record['bounds'])
                if bounds.adjusted(-4,-4,4,4).intersects(other):
                    raise ValueError('Folio collides with body text')

    def compose(self,units):
        self.cover();self.frontispiece()
        page,baseline=self.new_body_page(True)
        last_chapter=1
        for index,unit in enumerate(units):
            if unit['chapter']!=last_chapter:
                # Keep the compact chapter heading with at least three lines.
                if baseline+112>BODY_BOTTOM:
                    page,baseline=self.new_body_page()
                heading=self.word(digits(unit['chapter']),50)
                self.put(page,heading,page.left,baseline+12,role='chapter-heading',value=unit['chapter'])
                self.rule(page,page.left+48,baseline+9,page.right,baseline+9,width=.45)
                baseline+=56
                last_chapter=unit['chapter']
            initial = unit['text'][0] if index==0 else ''
            source = unit['text'][1:] if initial else unit['text']
            prefix='' if initial else digits(unit['verse'])+'  '
            display=prefix+source
            indent=100 if initial else 0
            shaped=self.lines(display,page.right-page.left-indent,prefix=len(prefix))
            if initial:
                # Verse marker precedes the actual enlarged first letter;
                # it must not interrupt the first word after that letter.
                self.put(page,self.word(digits(unit['verse']),VERSE_SIZE),page.left,baseline,
                         role='verse-marker',verseId=unit['id'],value=unit['verse'])
                box=QRectF(page.left+22,baseline-19,66,66)
                self.border(page,box)
                self.fitted_glyph(page,initial,box.adjusted(10,10,-10,-10),BLUE,'illuminated-initial')
            fragments=[]
            position=0
            while position<len(shaped):
                remaining=shaped[position:]
                capacity=sum(1 for i,line in enumerate(remaining)
                             if baseline+i*LEADING+line.path.boundingRect().bottom()<=BODY_BOTTOM)
                if capacity<len(remaining) and len(remaining)-capacity==1:
                    capacity-=1  # No isolated final line of a continued verse.
                if capacity<=0 or (capacity==1 and len(remaining)>1):
                    page,baseline=self.new_body_page()
                    continue
                for line_index,line in enumerate(remaining[:capacity],position):
                    bounds=self.put(page,line.path,page.left+indent,baseline,role='body',
                                    verseId=unit['id'],line=line_index,sourceSpan=[line.start,line.end])
                    if bounds.top()<TOP-1 or bounds.bottom()>BODY_BOTTOM+.01:
                        raise ValueError('Body leaves its reserved region')
                    fragments.append(dict(physicalPage=page.physical,folio=page.folio,
                                          start=line.start,end=line.end,baseline=baseline))
                    baseline+=LEADING
                position+=capacity
            if initial:
                baseline=max(baseline,175+66+6)
            baseline+=4
            reconstructed=initial+''.join(display[f['start']:f['end']] for f in fragments)[len(prefix):]
            if reconstructed!=unit['text']:
                raise ValueError('Proof changed verse text or case: '+unit['id'])
            self.coverage.append(dict(id=unit['id'],reference=unit['reference'],chapter=unit['chapter'],
                verse=unit['verse'],untaVerse=digits(unit['verse']),textSha256=hashlib.sha256(unit['text'].encode()).hexdigest(),
                illuminatedInitial=initial,fragments=fragments))
        for page in self.pages:
            if page.folio is not None:self.folio(page)
        # Even sheet count means the last back is deliberate and documented.
        if len(self.pages)%2:
            self.pages.append(Page('blank-duplex-back',len(self.pages)+1))
        self.validate_regions()

    def validate_regions(self):
        """Print acceptance uses actual outline bounds, not nominal em boxes."""
        for page in self.pages:
            body=[r for r in page.records if r['role']=='body']
            for previous,current in zip(body,body[1:]):
                if QRectF(*previous['bounds']).intersects(QRectF(*current['bounds'])):
                    raise ValueError('Overlapping print lines')
            for record in body:
                box=QRectF(*record['bounds'])
                # Historic glyph bearings may extend slightly before the
                # advance origin; the actual printer-safe box still governs.
                if box.left()<page.left-1 or box.right()>page.right+1:
                    raise ValueError('Ink extends outside the full-width column')
            if page.folio is not None:
                folios=[r for r in page.records if r['role']=='folio']
                if len(folios)!=1 or folios[0]['unta']!=digits(page.folio):
                    raise ValueError('Missing or incorrect folio')

    def render(self,path):
        writer=QPdfWriter(str(path));writer.setResolution(144)
        writer.setTitle('KJV - Vayrshemon Letter print proof 3 - Genesis 1-2 only')
        writer.setCreator('Vayrshemon / '+PROOF_VERSION)
        writer.setPageSize(QPageSize(QSizeF(WIDTH,HEIGHT),QPageSize.Unit.Point,'Letter',QPageSize.SizeMatchPolicy.ExactMatch))
        layout=writer.pageLayout();layout.setMode(QPageLayout.Mode.FullPageMode);writer.setPageLayout(layout)
        painter=QPainter(writer);painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.LosslessImageRendering,True)
        for index,page in enumerate(self.pages):
            if index and not writer.newPage():raise OSError('Cannot create PDF page')
            painter.save();painter.scale(2,2)
            painter.fillRect(QRectF(0,0,WIDTH,HEIGHT),Qt.GlobalColor.white)
            for image,rect in page.images:
                painter.drawImage(rect,image)
            painter.setPen(Qt.PenStyle.NoPen)
            for shape,color in page.elements:
                painter.setBrush(QColor(color));painter.drawPath(shape)
            painter.restore()
        painter.end();del writer


def configure_pdf(raw,target,proof):
    writer=PdfWriter(clone_from=PdfReader(raw))
    writer.pdf_header='%PDF-1.7'  # Duplex/print-scaling preferences need a modern PDF version.
    writer.page_layout='/TwoPageRight'
    writer.create_viewer_preferences()
    writer.viewer_preferences.direction='/L2R'
    writer.viewer_preferences.print_scaling='/None'
    writer.viewer_preferences.duplex='/DuplexFlipLongEdge'
    title_index=next(i for i,p in enumerate(proof.pages) if p.kind in ('title-page','cover'))
    frontis_index=next(i for i,p in enumerate(proof.pages) if p.kind=='frontispiece')
    body_index=next(i for i,p in enumerate(proof.pages) if p.folio==1)
    writer.set_page_label(title_index,title_index,prefix='Title page')
    writer.set_page_label(frontis_index,frontis_index,prefix='Frontispiece')
    # Labels use decimal for PDF UI accessibility; printed folios are Unta.
    end=next((i-1 for i,p in enumerate(proof.pages) if p.kind=='blank-duplex-back'),len(proof.pages)-1)
    writer.set_page_label(body_index,end,style='/D',start=1)
    if end<len(proof.pages)-1:writer.set_page_label(end+1,len(proof.pages)-1,prefix='Blank back')
    writer.add_outline_item('Title page',title_index)
    writer.add_outline_item('Frontispiece',frontis_index)
    writer.add_outline_item('Genesis 1 - illuminated opening',body_index)
    chapter2=next(c for c in proof.coverage if c['chapter']==2)
    writer.add_outline_item('Genesis 2',chapter2['fragments'][0]['physicalPage']-1)
    writer.open_destination=writer.pages[0]
    with Path(target).open('wb') as stream:writer.write(stream)


def reading_copy(print_path,target):
    """A display-only inside-cover blank for viewers that pair from page one.

The physical print master keeps its right-hand title and all page-side artwork.
The reading companion adds a leading virtual verso, leaving every real page's
content and dimensions intact. Do not recompose or invert the binding offsets.
"""
    from pypdf.generic import ArrayObject, NameObject, NumberObject
    reader=PdfReader(print_path)
    before=[hashlib.sha256(p.get_contents().get_data()).hexdigest() for p in reader.pages]
    writer=PdfWriter(clone_from=reader)
    writer.insert_blank_page(width=WIDTH,height=HEIGHT,index=0)
    writer.pdf_header='%PDF-1.7'
    writer.page_layout='/TwoPageLeft'
    writer.open_destination=writer.pages[0]
    writer.add_metadata({'/Title':'KJV - Letter reading proof 3 - leading display blank'})
    writer.root_object.pop(NameObject('/PageLabels'),None)
    writer.set_page_label(0,0,prefix='Display blank')
    for i,label in enumerate(reader.page_labels,1):
        writer.set_page_label(i,i,prefix=label)
    # A suggestion only: not every PDF viewer honors PrintPageRange. The
    # separate PRINT PDF is the reliable home-duplex deliverable.
    writer.viewer_preferences[NameObject('/PrintPageRange')]=ArrayObject([
        NumberObject(1),NumberObject(len(writer.pages)-1)])
    with Path(target).open('wb') as stream:writer.write(stream)
    after=PdfReader(target)
    assert len(after.pages)==len(reader.pages)+1
    assert after.pages[0].get_contents() is None
    assert [hashlib.sha256(p.get_contents().get_data()).hexdigest() for p in after.pages[1:]]==before
    assert after.page_labels==['Display blank',*reader.page_labels]
    return dict(path=str(target),sha256=digest(target),pages=len(after.pages),
                leadingBlank='display-only inside cover; not part of the physical print master',
                pairedLayout='/TwoPageLeft',printPages=[2,len(after.pages)],
                physicalPages=[dict(readingPage=i+2,printPage=i+1) for i in range(len(reader.pages))])


def check_runtime():
    """Setup probe: bundled fonts/print primitives only, no private Bible reads."""
    app=QApplication.instance() or QApplication([])
    proof=Proof()
    assert (WIDTH,HEIGHT)==(612,792)
    assert Page('body',1).binding_offset==9 and Page('body',2).binding_offset==-9
    assert [digits(v) for v in (0,10,11,12,144)]==['0','À','Á','10','100']
    assert proof.word('M',50).boundingRect().height()>0
    assert proof.word('0123456789ÀÁ',50).boundingRect().width()>0
    print('Letter print proof runtime ready: mirrored binding offset, bundled Thimfora, Unta and PDF; no private files rebuilt.')


def main(out,title_art=TITLE_ART,frontispiece_art=FRONTIS_ART):
    out=Path(out).resolve()
    if out==SOURCE.resolve() or SOURCE.resolve() in out.parents:
        raise ValueError('Frozen edition is not an output directory')
    if out.exists():raise FileExistsError('Use a new proof folder; earlier proofs are retained')
    frozen=SOURCE/'KJV Bible.vay'
    if digest(frozen)!=SOURCE_SHA:raise ValueError('Frozen Bible identity changed')
    ledger_path=SOURCE/'complete-translation-ledger.json'
    ledger_hash=digest(ledger_path)
    if ledger_hash!=LEDGER_SHA:raise ValueError('Sealed historical ledger identity changed')
    ledger=json.loads(ledger_path.read_text(encoding='utf-8'))
    units=[u for u in ledger['units'] if u['id'].startswith('01.') and u['chapter']<=2]
    if [u['id'] for u in units]!=[f'01.{c:03}.{v:03}' for c,n in [(1,31),(2,25)] for v in range(1,n+1)]:
        raise ValueError('Expected complete Genesis 1-2 in canonical order')
    app=QApplication.instance() or QApplication([])
    proof=Proof(title_art,frontispiece_art)
    lex=json.loads((ROOT/'data/language/archaic-kjv-280/lexicon.json').read_text(encoding='utf-8'))['entries']
    # These are captions copied from historical lexical entries, not verse edits.
    if 'ipl' not in lex:
        raise ValueError('Find the explicit historical plural-I entry before rendering')
    proof.plural_i=lex['ipl']['form'];proof.singular_we=lex['we']['form']
    proof.compose(units)
    out.mkdir(parents=True)
    target=out/'PRINT - KJV Letter proof 3.pdf'
    with tempfile.TemporaryDirectory(prefix='vay-print-',dir=ROOT/'.local') as temp:
        raw=Path(temp)/'raw.pdf';proof.render(raw);configure_pdf(raw,target,proof)
    reading=reading_copy(target,out/'READ - KJV Letter proof 3.pdf')
    reader=PdfReader(target)
    assert len(reader.pages)==len(proof.pages) and len(reader.pages)%2==0
    assert all(float(p.mediabox.width)==WIDTH and float(p.mediabox.height)==HEIGHT for p in reader.pages)
    if digest(frozen)!=SOURCE_SHA or digest(ledger_path)!=ledger_hash:
        raise ValueError('Source changed during proof generation')
    for image,provenance in proof.artwork.values():
        if digest(provenance['source'])!=provenance['sha256']:
            raise ValueError('Supplied artwork changed during proof generation')
    report=dict(proofVersion=PROOF_VERSION,completeBible=False,scope='Genesis 1:1-2:25; 56/31,102 verses',
        source=str(frozen),sourceSha256=SOURCE_SHA,ledgerSha256=ledger_hash,sourceUnchanged=True,
        languageVersion='0.10-kjv.280',pdf=str(target),pdfSha256=digest(target),
        readingCopy=reading,
        pageSizePt=[WIDTH,HEIGHT],print=dict(scale='100% / Actual size',duplex='long edge',
        paper='US Letter',sheets=len(proof.pages)//2,innerMarginPt=INNER,outerMarginPt=OUTER,topMarginPt=TOP,
        bindingOffsetPt=BINDING_OFFSET,bodyBottomPt=BODY_BOTTOM,folioInsetPt=FOLIO_INSET,folioSizePt=FOLIO_SIZE,
        bodySizePt=BODY_SIZE,leadingPt=LEADING,verseSizePt=VERSE_SIZE),
        fontSha256=proof.face.sha256,bodyVectorOutlines=True,suppliedArtworkUnchanged=True,
        artwork={k:v[1] for k,v in proof.artwork.items()},
        pages=[dict(kind=p.kind,physical=p.physical,folio=p.folio,side='right' if p.physical%2 else 'left',
                    bindingOffsetPt=p.binding_offset,elements=p.records) for p in proof.pages],coverage=proof.coverage)
    write_json(out/'proof-manifest.json',report)
    instructions=f'''VAYRSHEMON - LETTER DUPLEX PRINT PROOF 3

INCOMPLETE DESIGN EXCERPT: Genesis 1:1 through 2:25, all 56 verses.
This is not a replacement for the complete frozen Bible.
Language: 0.10-kjv.280, copied exactly; no modernization or spelling edits.

READ - KJV Letter proof 3.pdf is for the screen. It starts with a display-only
blank to show blank | title, then frontispiece | illuminated opening in a
two-page viewer. Choose paired view with "show cover separately" OFF.
Its 11 viewer pages include the virtual blank; printed Unta folios are unchanged.

PRINT - KJV Letter proof 3.pdf is the physical book. It omits the virtual blank
so the title prints on the first sheet's right-hand face, its reverse is the
left frontispiece, and the next sheet begins with the right chapter opening.
Print THIS file on US Letter (8.5 x 11 inches), Actual size / 100%,
double-sided, flip on LONG edge. Do not select Booklet or multiple pages
per sheet. PDF preferences request these settings; check your printer dialog.
{len(proof.pages)} PDF pages / {len(proof.pages)//2} sheets. Title page is the first right-hand face;
frontispiece is its reverse and faces the illuminated Genesis opening.
Body folios begin at Unta 1 on PDF page 3; all chapter and verse numbers
are Unta base 12. PDF navigation labels stay decimal for accessibility.

Body: 36 pt Thimfora 79 / 28 pt leading, 24 pt verse markers.
This is a new print design, not a change to the approved workbench layout.
Binding: left pages are centered 9 pt LEFT of the sheet center; right pages
are centered 9 pt RIGHT. Equal 1/8-inch outward offsets protect the gutter.
Margins: 0.625 inch at the binding, 0.375 inch outside/top. Folio ink
stays 28 pt from the bottom/outside edge; a separate footer band is reserved.
Verify printer clipping on this proof before a longer print run.

Title page and frontispiece use the user's supplied PNGs, placed whole,
with identical opposite offsets, no cropping or distortion, and lossless
image embedding. The supplied resolution is retained (approximately 134 DPI
at this print size); the body and Unta numbers remain crisp vector outlines.
The illuminated Genesis opening retains its original vector design and Maxima.
Body text is unchanged, 36 pt / 28 pt; only its measure adjusts to the gutter.
The first two proofs remain preserved in their own folders.

proof-manifest.json records every verse fragment, page, glyph bounds and
source hashes. The original four-column Bible and its ledger are untouched.
'''
    (out/'READ ME - printing.txt').write_text(instructions,encoding='utf-8')
    print(json.dumps(dict(pdf=str(target),readingPdf=reading['path'],pages=len(proof.pages),
                         readingPages=reading['pages'],verses=len(units),sourceUnchanged=True)))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=ROOT/'Exports/KJV Letter proof 3')
    parser.add_argument('--title-art',type=Path,default=TITLE_ART)
    parser.add_argument('--frontispiece-art',type=Path,default=FRONTIS_ART)
    parser.add_argument('--check',action='store_true',help='Check the bundled print runtime without reading the Bible')
    args=parser.parse_args()
    check_runtime() if args.check else main(args.out,args.title_art,args.frontispiece_art)
