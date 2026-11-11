"""Native, source-preserving fixed-layout editions for bound publications.

Text remains in ordinary native frames for search/copy. A sealed layout refers
to their exact scalar spans; it is not a PDF wrapper or a page screenshot.
Only the two supplied front-matter images are raster assets. Body text uses
the original TTF outlines, shaped lazily one visible page at a time.
"""
import base64
import hashlib
import re
from bisect import bisect_right
from copy import deepcopy
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QImage, QPaintEngine, QPainter, QPainterPath, QTextCharFormat, QTextLayout, QTextOption
from .api import obj
from .session import SCALE
from .page_numbering import MASTER, digits

PUNCTUATION='-()[]'
ROMAN='font:9ba7c6f12d40ea8a0aafb8f07a69f8b65b424e374c6da95235a45edeb6292c52:0'
DRAMA_PUNCT='font:931c5de5c70401d9324d5014c123802b4fb753000360ceb2f56c589403cd58c5:0'
COLLECTED='letter-collected.1'
LETTER_TYPE=dict(bodySizePt=36,leadingPt=28,verseSizePt=24,verseGapPt=4)
COMPACT_TYPE=dict(bodySizePt=26,leadingPt=18,verseSizePt=18,verseGapPt=2)


def typography(edition):
    return edition.get('typography',LETTER_TYPE)

HASH={'type':'string','pattern':'^[0-9a-f]{64}$'}
NUM={'type':'number','minimum':-10000,'maximum':10000}
RECT={'type':'array','items':NUM,'minItems':4,'maxItems':4}
SPAN=obj(dict(pageId={'type':'string'},start={'type':'integer','minimum':0},end={'type':'integer','minimum':0}),('pageId','start','end'))
LINE=obj(dict(start={'type':'integer','minimum':0},end={'type':'integer','minimum':0},prefix={'type':'string','maxLength':30},
              wordGapPt={'type':'number','minimum':0,'maximum':612},
              sizePt={'type':'integer','minimum':12,'maximum':100},x=NUM,baseline=NUM,width=NUM,bounds=RECT),('start','end','prefix','x','baseline','width','bounds'))
PATH=obj(dict(elements={'type':'array','maxItems':40000,'items':{'type':'array','items':NUM,'minItems':3,'maxItems':3}},
              fill={'enum':[0,1]},role={'type':'string'},bounds=RECT),('elements','fill','role','bounds'))
PAGE=obj(dict(kind={'enum':['title','blank','frontispiece','contents','opening','body']},side={'enum':['center','left','right']},
              folio={'type':['integer','null'],'minimum':1},sourceSha256=HASH,
              # Run-in verse starts can share a physical line. A dense genealogy
              # can need more than 80 positioned text segments on a Letter page.
              lines={'type':'array','maxItems':160,'items':LINE},paths={'type':'array','maxItems':150,'items':PATH},
              images={'type':'array','maxItems':2,'items':obj(dict(asset=HASH,rect=RECT),('asset','rect'))}),
         ('kind','side','folio','sourceSha256','lines','paths','images'))
SCHEMA=obj(dict(version={'const':1},layoutVersion={'enum':['letter-native.1','letter-compact.1',COLLECTED]},languageVersion={'type':'string'},
    typography=obj({key:{'type':'number','minimum':1,'maximum':100} for key in LETTER_TYPE},tuple(LETTER_TYPE)),
    sourceSha256=HASH,ledgerSha256=HASH,
    assets={'type':'object','maxProperties':8,'additionalProperties':obj(dict(png={'type':'string','maxLength':16777216},width={'type':'integer','minimum':1,'maximum':8192},height={'type':'integer','minimum':1,'maximum':8192}),('png','width','height'))},
    pages={'type':'object','maxProperties':32768,'additionalProperties':PAGE},
    verses={'type':'array','maxItems':40000,'items':obj(dict(id={'type':'string'},sha256=HASH,fragments={'type':'array','minItems':1,'maxItems':100,'items':SPAN}),('id','sha256','fragments'))},
    sections={'type':'array','maxItems':100,'items':obj(dict(name={'type':'string'},number={'type':'integer','minimum':1},pageId={'type':'string'}),('name','number','pageId'))}),
    ('version','layoutVersion','languageVersion','sourceSha256','ledgerSha256','assets','pages','verses','sections'))


def text_of(page):
    return '\n'.join(''.join(r.get('text',r.get('sourceText','')) for r in b['runs'])
                     for b in page['frames'][0]['content']['document']['stories'][0]['blocks'])


def hash_text(text):return hashlib.sha256(text.encode('utf-8')).hexdigest()


def encode_path(path,role):
    b=path.boundingRect()
    return dict(elements=[[int(path.elementAt(i).type.value),path.elementAt(i).x,path.elementAt(i).y] for i in range(path.elementCount())],
                fill=path.fillRule().value,role=role,bounds=[b.x(),b.y(),b.width(),b.height()])


def decode_path(value):
    path=QPainterPath();items=value['elements'];i=0
    while i<len(items):
        kind,x,y=items[i]
        if kind==0:path.moveTo(x,y)
        elif kind==1:path.lineTo(x,y)
        elif kind==2:
            if i+2>=len(items) or items[i+1][0]!=3 or items[i+2][0]!=3:raise ValueError('PRINT_PATH_CURVE')
            path.cubicTo(x,y,*items[i+1][1:],*items[i+2][1:]);i+=2
        else:raise ValueError('PRINT_PATH_ELEMENT')
        i+=1
    path.setFillRule(Qt.FillRule(value['fill']))
    return path


def validate(state):
    edition=state.get('printEdition')
    if not edition:return
    collected=edition['layoutVersion']==COLLECTED
    expected=COMPACT_TYPE if collected or edition['layoutVersion']=='letter-compact.1' else LETTER_TYPE
    if typography(edition)!=expected:raise ValueError('PRINT_TYPOGRAPHY_PROFILE')
    if edition['layoutVersion']=='letter-compact.1' and len(state['pages'])>2000:raise ValueError('PRINT_SHEET_LIMIT: compact editions allow at most 1000 duplex sheets')
    by_id={p['pageId']:p for p in state['pages']}
    if set(by_id)!=set(edition['pages']):raise ValueError('PRINT_PAGE_REFERENCE')
    texts={};coverage={pid:[] for pid in by_id}
    for pid,page in by_id.items():
        spec=edition['pages'][pid]
        if not collected and (spec['kind']=='contents' or any('sizePt' in line or 'wordGapPt' in line for line in spec['lines'])):
            raise ValueError('PRINT_TYPOGRAPHY_PROFILE')
        if len(page['frames'])!=1:raise ValueError('PRINT_SINGLE_SOURCE_FRAME')
        if [int(page[k]) for k in ('width','height')]!=[612000000,792000000]:raise ValueError('PRINT_LETTER_PAGE_REQUIRED')
        source=text_of(page);texts[pid]=source
        if hash_text(source)!=spec['sourceSha256']:raise ValueError('PRINT_SOURCE_CHANGED: regenerate the edition from its source')
        last=1 if spec['kind']=='opening' and not collected else 0
        if last and (not source or sum(p['role']=='illuminated-initial' for p in spec['paths'])!=1):raise ValueError('PRINT_INITIAL_REQUIRED')
        for line in spec['lines']:
            if not 0<=line['start']<=line['end']<=len(source):raise ValueError('PRINT_LINE_SPAN')
            if line['start']<last or source[last:line['start']].strip():raise ValueError('PRINT_UNPAINTED_SOURCE_TEXT')
            last=line['end']
            if not QRectF(17,17,578,750).contains(QRectF(*line['bounds'])):raise ValueError('PRINT_LINE_OUTSIDE_SAFE_AREA')
            if line['width']<=0:raise ValueError('PRINT_LINE_WIDTH')
        if source[last:].strip():raise ValueError('PRINT_UNPAINTED_SOURCE_TEXT')
        for item in spec['paths']:
            path=decode_path(item)
            if not QRectF(17,17,578,758).contains(path.boundingRect()):raise ValueError('PRINT_PATH_OUTSIDE_SAFE_AREA')
            if any(abs(a-b)>.01 for a,b in zip(item['bounds'],[path.boundingRect().x(),path.boundingRect().y(),path.boundingRect().width(),path.boundingRect().height()])):raise ValueError('PRINT_PATH_BOUNDS')
        for image in spec['images']:
            if image['asset'] not in edition['assets'] or not QRectF(0,0,612,792).contains(QRectF(*image['rect'])):raise ValueError('PRINT_IMAGE_REFERENCE')
    for key,asset in edition['assets'].items():
        raw=base64.b64decode(asset['png'],validate=True)
        if hashlib.sha256(raw).hexdigest()!=key:raise ValueError('PRINT_ASSET_CHECKSUM')
        image=QImage.fromData(raw,'PNG')
        if image.isNull() or [image.width(),image.height()]!=[asset['width'],asset['height']]:raise ValueError('PRINT_ASSET_DIMENSIONS')
    ids=set()
    for verse in edition['verses']:
        if verse['id'] in ids:raise ValueError('PRINT_DUPLICATE_VERSE')
        ids.add(verse['id']);parts=[]
        for fragment in verse['fragments']:
            pid=fragment['pageId'];start,end=fragment['start'],fragment['end']
            if pid not in texts or not 0<=start<end<=len(texts[pid]):raise ValueError('PRINT_VERSE_SPAN')
            parts.append(texts[pid][start:end]);coverage[pid].append((start,end))
        if hash_text(''.join(parts))!=verse['sha256']:raise ValueError('PRINT_VERSE_TEXT_CHANGED')
    for pid,spans in coverage.items():
        last=0
        for start,end in sorted(spans):
            if start<last or texts[pid][last:start].strip():raise ValueError('PRINT_SOURCE_COVERAGE')
            last=end
        if texts[pid][last:].strip():raise ValueError('PRINT_SOURCE_COVERAGE')
    for section in edition['sections']:
        if section['pageId'] not in by_id or edition['pages'][section['pageId']]['kind']!='opening':raise ValueError('PRINT_SECTION_REFERENCE')


def font(book,size):
    face=book.fonts.resolve(MASTER);result=QFont(face.family)
    result.setPixelSize(round(size));result.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
    result.setStyleStrategy(QFont.StyleStrategy.NoFontMerging)
    return result


def text_formats(book,text,size,prefix=0,verse_size=24,dramatic=False):
    ranges=[]
    if prefix:
        fmt=QTextCharFormat();fmt.setFont(font(book,verse_size));span=QTextLayout.FormatRange();span.start=0;span.length=prefix;span.format=fmt;ranges.append(span)
    if dramatic:
        # The issued four-column plays use their literal face for every scalar
        # absent from Thimfora, including foreign letters in quoted speech.
        cmap=book.fonts.resolve(MASTER).cmap
        punctuation={c for c in text if not c.isspace() and ord(c) not in cmap}
    else:
        punctuation=PUNCTUATION
    if any(c in punctuation for c in text):
        face=book.fonts.resolve(DRAMA_PUNCT if dramatic else ROMAN);punct=QFont(face.family);punct.setPixelSize(round(size*4/9))
        punct.setHintingPreference(QFont.HintingPreference.PreferNoHinting);punct.setStyleStrategy(QFont.StyleStrategy.NoFontMerging)
        for i,c in enumerate(text):
            if c not in punctuation:continue
            if ord(c) not in face.cmap and c!='-':raise ValueError('PRINT_PUNCTUATION_FONT_MISSING')
            fmt=QTextCharFormat();fmt.setFont(punct);span=QTextLayout.FormatRange();span.start=i;span.length=1;span.format=fmt;ranges.append(span)
    return ranges


def punctuation_paths(path,text,line,size):
    # The frozen ledger has one literal editorial hyphen, absent from both
    # supplied fonts. Retain its source scalar; paint a typographic rule in a
    # Roman-space advance. No font fallback or replacement language character.
    for i in range(line.textStart(),line.textStart()+line.textLength()):
        if text[i]=='-':
            x=line.cursorToX(i)[0];scale=size/36
            path.addRect(QRectF(x+.25*scale,-4*scale,3.5*scale,.65*scale))


def spaced_runs(layout,word_gap):
    """Shift shaped words, preserving glyph advances and the source's own spaces."""
    if not word_gap:
        return layout.glyphRuns()
    text=layout.text()
    # Qt returns UTF-16 source offsets. A run of several spaces is one gap.
    ends=[len(text[:m.end()].encode('utf-16-le'))//2 for m in re.finditer(r'(?<=\S)\s+(?=\S)',text)]
    flags=QTextLayout.GlyphRunRetrievalFlag
    runs=layout.glyphRuns(0,-1,flags.DefaultRetrievalFlags|flags.RetrieveStringIndexes)
    for run in runs:
        positions=run.positions()
        for pos,index in zip(positions,run.stringIndexes(),strict=True):
            pos.setX(pos.x()+word_gap*bisect_right(ends,index))
        run.setPositions(positions)
    return runs


def shape(book,text,size=36,prefix=0,verse_size=24,dramatic=False,word_gap=0):
    layout=QTextLayout(text if dramatic else text.replace('-',' '),font(book,size));option=QTextOption()
    option.setWrapMode(QTextOption.WrapMode.NoWrap);option.setTextDirection(Qt.LayoutDirection.LeftToRight);layout.setTextOption(option)
    layout.setFormats(text_formats(book,text,size,prefix,verse_size,dramatic))
    layout.beginLayout();line=layout.createLine();line.setLineWidth(100000);layout.endLayout()
    path=QPainterPath();glyphs=[]
    for run in spaced_runs(layout,word_gap):
        for gid,pos in zip(run.glyphIndexes(),run.positions()):
            if not gid:raise ValueError('PRINT_MISSING_GLYPH')
            p=run.rawFont().pathForGlyph(gid).translated(pos.x(),pos.y()-line.ascent());path.addPath(p)
            glyphs.append((gid,p.boundingRect()))
    if not dramatic:punctuation_paths(path,text,line,size)
    return path,glyphs


class Composition:
    def __init__(self,book,mode,page_id):
        self.book=book;self.page=next(p for p in book.state['pages'] if p['pageId']==page_id)
        self.spec=book.state['printEdition']['pages'][page_id];self.source=text_of(self.page)
        self.frames={self.page['frames'][0]['frameId']:(self.page,self.page['frames'][0])}
        self.drawings=[];self.final=[];self.lines=[];self.mode=mode
        type_spec=typography(book.state['printEdition'])
        fid=self.page['frames'][0]['frameId']
        for line in self.spec['lines']:
            text=line['prefix']+self.source[line['start']:line['end']]
            path,glyphs=shape(book,text,line.get('sizePt',type_spec['bodySizePt']),prefix=len(line['prefix']),
                              verse_size=type_spec['verseSizePt'],dramatic=book.state['printEdition']['layoutVersion']==COLLECTED,
                              word_gap=line.get('wordGapPt',0))
            path.translate(line['x'],line['baseline']);self.drawings.append(path)
            self.lines.append(dict(frameId=fid,x=line['x']*SCALE,baseline=line['baseline']*SCALE,start=line['start'],end=line['end']))
            for gid,b in glyphs:
                b.translate(line['x'],line['baseline']);bounds=[v*SCALE for v in (b.x(),b.y(),b.width(),b.height())]
                self.final.append(dict(pageId=page_id,frameId=fid,fontId=MASTER,glyphId=gid,missingGlyph=False,effectBounds=bounds,inkBounds=bounds,sourceUtf16=[line['start'],line['end']]))
        self.ornaments=[decode_path(item) for item in self.spec['paths']]
        self.before=self.final

    def report(self,page_id,max_glyphs=5000):
        return dict(revision=self.book.revision,pageId=page_id,pagePoints=[612,792],units='logical-pixels-at-96-dpi',
                    geometryHash=hash_text(str(self.spec)),beforeGeometryHash=hash_text(str(self.spec)),
                    frames=[],glyphs=self.final[:max_glyphs],lines=self.lines,diagnostics=[],truncated=len(self.final)>max_glyphs,
                    collisionReport=self.collision_report(page_id),fixedPrintLayout=True)

    def collision_report(self,page_id=None):
        boxes=[p.boundingRect() for p in self.drawings];collisions=[]
        for a,b in zip(boxes,boxes[1:]):
            if a.intersects(b):collisions.append(dict(code='PRINT_LINE_COLLISION'))
        return dict(beforeCount=len(collisions),afterCount=len(collisions),collisions=collisions,complete=True,
                    scope='actual print line bounds; decoration and folio safety checked separately')

    def paint(self,painter,page_id,mode=None,clip=None,overlays=None,guides=False,outlines=False):
        from .pages import page_rect
        painter.save()
        try:
            painter.setClipRect(page_rect(self.page) if clip is None else page_rect(self.page).intersected(clip))
            painter.fillRect(page_rect(self.page),QColor('white'))
            painter.setRenderHint(QPainter.RenderHint.Antialiasing,True)
            painter.setRenderHint(QPainter.RenderHint.TextAntialiasing,True)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform,True)
            painter.setRenderHint(QPainter.RenderHint.LosslessImageRendering,True)
            painter.scale(SCALE,SCALE);painter.setPen(Qt.PenStyle.NoPen);painter.setBrush(QColor('#111111'))
            cache=self.book.__dict__.setdefault('_print_images',{})
            for item in self.spec['images']:
                key=item['asset']
                if key not in cache:cache[key]=QImage.fromData(base64.b64decode(self.book.state['printEdition']['assets'][key]['png']),'PNG')
                source=cache[key]
                rect=QRectF(*item['rect'])
                if self.spec['kind']=='opening' and painter.paintEngine().type()==QPaintEngine.Type.Raster:
                    # Bilinear painting samples only a few source pixels. Area-filter
                    # fine engraving strokes when a large ornament is shown small.
                    size=painter.deviceTransform().mapRect(rect).size().toSize()
                    if not size.isEmpty() and size.width()*2<source.width() and size.height()*2<source.height():
                        scaled=self.book.__dict__.setdefault('_print_scaled_ornaments',{})
                        if key not in scaled or scaled[key].size()!=size:
                            scaled[key]=source.scaled(size,Qt.AspectRatioMode.IgnoreAspectRatio,Qt.TransformationMode.SmoothTransformation)
                        source=scaled[key]
                painter.drawImage(rect,source)
            for path in [*self.ornaments,*self.drawings]:painter.drawPath(path)
        finally:painter.restore()

    def hit_test(self,page_id,x,y):
        for line,path in zip(self.spec['lines'],self.drawings):
            if path.boundingRect().adjusted(-2,-3,2,3).contains(QPointF(x/SCALE,y/SCALE)):
                return dict(frameId=self.page['frames'][0]['frameId'],pageId=page_id,offset=line['start'],revision=self.book.revision,readOnly=True)
        return dict(frameId=None,pageId=page_id,offset=None,revision=self.book.revision)


def numbering(book,page,config,view,composition=None):
    spec=book.state['printEdition']['pages'][page['pageId']];role='single' if view=='one' else spec['side']
    role=role if role in ('single','left','right') else 'single';position=config[role]
    if role=='single' and book.state['printEdition']['layoutVersion']==COLLECTED and spec['side'] in ('left','right'):
        position=dict(position,horizontal=config[spec['side']]['horizontal'])
    number=spec['folio'];text=digits(number) if number else ''
    result=dict(pageId=page['pageId'],pageNumber=number,text=text,base12=text.translate(str.maketrans({'À':'A','Á':'B'})),role=role,pageMode=view,status='hidden',bounds=None,clearancePt=4)
    if not number or not config['enabled'] or not position['visible']:return result
    path,_=shape(book,text,config['sizePt']);b=path.boundingRect();inset=config['edgeInsetPt']
    dx=inset-b.left() if position['horizontal']=='left' else 612-inset-b.right()
    dy=inset-b.top() if position['vertical']=='top' else 792-inset-b.bottom()
    path.translate(dx,dy);box=path.boundingRect();comp=composition or book.composition(page_id=page['pageId'])
    if not QRectF(2,2,608,788).contains(box) or any(box.adjusted(-4,-4,4,4).intersects(p.boundingRect()) for p in [*comp.drawings,*comp.ornaments]):
        return dict(result,status='blocked',code='PAGE_NUMBER_NO_SPACE',message='Unta number overlaps the fixed print layout. Choose a clear margin position or smaller size.')
    result.update(status='placed',bounds=[v*SCALE for v in (box.x(),box.y(),box.width(),box.height())],origin=[dx*SCALE,dy*SCALE],adjusted=False,sizePt=config['sizePt'],glyphs=[])
    return result


def inspect(book,page_id=None):
    edition=book.state.get('printEdition')
    if not edition:return dict(present=False)
    page_id=page_id or book.current_page()['pageId'];spec=edition['pages'][page_id]
    return dict(present=True,version=edition['version'],layoutVersion=edition['layoutVersion'],readOnlyText=True,
                languageVersion=edition['languageVersion'],sourceSha256=edition['sourceSha256'],ledgerSha256=edition['ledgerSha256'],
                pageCount=len(edition['pages']),duplexSheets=(len(edition['pages'])+1)//2,typography=deepcopy(typography(edition)),verseCount=len(edition['verses']),sections=deepcopy(edition['sections']),
                page=dict(pageId=page_id,kind=spec['kind'],side=spec['side'],folio=spec['folio'],sourceSha256=spec['sourceSha256']))


ALLOWED_MUTATIONS={'document.open','document.new','document.close','document.save','document.save-as','document.title',
    'history.undo','history.redo','selection.set','frame.select','view.configure','view.tool','view.pan','view.center','view.page','view.pages',
    'ui.capture','ui.workspace','ui.sidebar','ui.forge','render.png','render.svg','publication.export','jobs.export','jobs.cancel',
    'page.numbering.configure','backup.create','backup.restore','recovery.restore','forge.open','forge.checkout','forge.test.run','forge.lab.run'}
