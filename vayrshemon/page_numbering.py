"""Unta folios: derived margin artwork, never editable body frames or reflow."""
from contextlib import contextmanager
from copy import deepcopy
from functools import wraps
import math
from PySide6.QtCore import QRectF,Qt
from PySide6.QtGui import QPainter
from .numbering_contracts import defaults
from .session import SCALE
from .monochrome import palette
from .paint import signature

MASTER='font:a9bb4075285df9acf2bf75c08446d44cfd83b29f6940937671cc07bd68f9f6cc:0'
BINDING=dict(fontId=MASTER,kind='layered',enabled=True,
             glowFontId='font:2e195f255b0f53042a0a05b693f94bafa41505dbaab475d7379549ccdaff59dd:0',
             interiorFontId='font:182d49f4e1677afd607696ad9506fbdb377e6d1d77fd5e53974ca74a0d378325:0')
FONT_IDS=tuple(BINDING[k] for k in ('fontId','glowFontId','interiorFontId'))
DIGITS='0123456789\u00c0\u00c1'
CLEARANCE=4*SCALE


def settings(book):return deepcopy(book.state.get('pageNumbering',defaults()))


def enabled_for(state):
    config=state.get('pageNumbering',{})
    return bool(config.get('enabled') and len(state['pages'])>=config.get('minimumPages',1))


def ensure_fonts(book):
    declared={s['fontId'] for s in book.state['fontSources']}
    for fid in FONT_IDS:
        face=book.fonts.resolve(fid)
        if fid not in declared:book.state['fontSources'].append(dict(fontId=fid,sha256=face.sha256,path=str(face.path)))
    book.validate_binding(BINDING)


def page_mode(book):
    override=getattr(book,'_numbering_page_mode',None)
    preview=getattr(getattr(book,'window',None),'preview',None)
    return override or (getattr(preview,'page_mode','one') if preview else getattr(book,'saved_page_mode','one'))


@contextmanager
def scope(book,mode=None):
    if mode is not None and mode not in ('one','two'):raise ValueError('UNKNOWN_PAGE_VIEW_MODE')
    previous=getattr(book,'_numbering_page_mode',None)
    book._numbering_page_mode=mode or page_mode(book)
    try:yield
    finally:book._numbering_page_mode=previous


def render_context(function):
    @wraps(function)
    def run(book,*args,page_mode=None,**kwargs):
        pdf_view=kwargs.get('pdf_view')
        if page_mode and pdf_view and page_mode!=pdf_view:raise ValueError('PAGE_NUMBERING_VIEW_MISMATCH')
        with scope(book,page_mode or pdf_view):return function(book,*args,**kwargs)
    return run


def digits(number):
    if type(number) is not int or number<0:raise ValueError('UNTA_NONNEGATIVE_INTEGER_REQUIRED')
    result=[]
    while number:number,remainder=divmod(number,12);result.append(DIGITS[remainder])
    return ''.join(reversed(result)) or DIGITS[0]


def configure(book,**values):
    result=settings(book)
    for key,value in values.items():
        if key in ('single','left','right'):result[key].update(value)
        else:result[key]=value
    if result==settings(book):return dict(settings=result,changed=False)
    if result['enabled']:
        ensure_fonts(book)
    book.state['pageNumbering']=result
    book.invalidate_composition()
    return dict(settings=deepcopy(result),changed=True)


def rectangle(value):return [value.x(),value.y(),value.width(),value.height()]


def placement(book,page,mode=None,composition=None):
    if book.state.get('printEdition'):
        from .print_edition import numbering
        return numbering(book,page,settings(book),page_mode(book),composition)
    config=settings(book);index=next(i for i,p in enumerate(book.state['pages']) if p['pageId']==page['pageId'])
    view=page_mode(book);role='single' if view=='one' else ('left' if index%2==0 else 'right')
    position=config[role];text=digits(index+1)
    result=dict(pageId=page['pageId'],pageNumber=index+1,base12=text.translate(str.maketrans({'À':'A','Á':'B'})),
                text=text,role=role,pageMode=view,status='hidden',bounds=None,clearancePt=4)
    if not enabled_for(book.state) or not position['visible']:return result
    mode=mode or book.view['mode'];comp=composition or book.composition(mode,page_id=page['pageId'])
    key=(signature(config),view,page['pageId'])
    cache=getattr(comp,'_page_numbering',{})
    if key in cache:return cache[key]
    try:
        for fid in FONT_IDS:book.fonts.resolve(fid)
        em=config['sizePt']*SCALE;raw=book.fonts.raw(MASTER,em)
        ids=raw.glyphIndexesForString(text)
        if len(ids)!=len(text) or not all(ids):raise ValueError('UNTA_GLYPH_MISSING')
        advances=raw.advancesForGlyphIndexes(ids);x=0.;bounds=QRectF();glyphs=[]
        # Reserve the complete colored support in every mode, so changing the
        # palette does not change numeral alignment or clip its later glow.
        for gid,advance in zip(ids,advances):
            support=book.paint_renderer.bounds(BINDING,gid,em).translated(x,0)
            bounds=bounds.united(support);glyphs.append((gid,x));x+=advance.x()
        from .pages import page_rect,rect
        area=page_rect(page);margin={k:int(v)/1e6*SCALE for k,v in page['margins'].items()}
        obstacles=[rect(f) for f in page['frames']]
        by_id={f['frameId']:f for f in page['frames']}
        for glyph in comp.final:
            if glyph['pageId']!=page['pageId']:continue
            ink=QRectF(*glyph['effectBounds']);frame=by_id[glyph['frameId']]
            if frame['overflow']=='clip':ink=ink.intersected(rect(frame))
            if glyph.get('_clip') is not None:ink=ink.intersected(glyph['_clip'])
            if not ink.isEmpty():obstacles.append(ink)
        # The whole frame is protected, including currently blank lines. Actual
        # overset/overhanging paint is protected outside it as well.
        obstacles=[r.adjusted(-CLEARANCE,-CLEARANCE,CLEARANCE,CLEARANCE) for r in obstacles]
        w,h=bounds.width(),bounds.height()
        left=margin['left'] if position['horizontal']=='left' else area.width()-margin['right']-w
        edge=2*SCALE
        low=edge if position['vertical']=='top' else max(edge,area.height()-margin['bottom'])
        high=min(area.height()-edge,margin['top']) if position['vertical']=='top' else area.height()-edge
        preferred=config['edgeInsetPt']*SCALE if position['vertical']=='top' else area.height()-config['edgeInsetPt']*SCALE-h
        candidates={preferred,low,high-h}
        for obstacle in obstacles:
            if obstacle.right()>left and obstacle.left()<left+w:
                candidates.update((obstacle.top()-h,obstacle.bottom()))
        candidate=None
        for y in sorted(candidates,key=lambda value:(abs(value-preferred),value)):
            test=QRectF(left,y,w,h)
            if y<low-1e-7 or y+h>high+1e-7 or left<edge or left+w>area.width()-edge:continue
            if any(test.intersects(obstacle) for obstacle in obstacles):continue
            candidate=test;break
        if candidate is None:
            result.update(status='blocked',code='PAGE_NUMBER_NO_SPACE',message=f'Page {index+1}: no safe {position["vertical"]}-{position["horizontal"]} margin space for its Unta number. Choose another position, reduce the number size, or enlarge the margin.')
        else:
            origin=[candidate.x()-bounds.x(),candidate.y()-bounds.y()]
            result.update(status='placed',bounds=rectangle(candidate),origin=origin,sizePt=config['sizePt'],
                          adjusted=abs(candidate.y()-preferred)>1e-6,
                          glyphs=[dict(glyphId=gid,origin=[origin[0]+x,origin[1]]) for gid,x in glyphs])
    except (ValueError,OSError,KeyError) as error:
        result.update(status='blocked',code='PAGE_NUMBER_FONT_UNAVAILABLE',message=f'Page {index+1}: {error}')
    cache[key]=result;comp._page_numbering=cache
    return result


def inspect(book,page_id=None,all_pages=False,page_mode=None):
    from . import pages,page_view
    if page_id and all_pages:raise ValueError('CHOOSE_PAGE_OR_ALL_PAGES')
    with scope(book,page_mode):
        selected=book.state['pages'] if all_pages else ([pages.selected_page(book,page_id)] if page_id else [p for p,_ in page_view.arrangement(book,book._numbering_page_mode)])
        results=[deepcopy(placement(book,p)) for p in selected]
    return dict(settings=settings(book),pages=results,ok=all(r['status']!='blocked' for r in results))


def require_space(book,page,mode=None):
    if enabled_for(book.state):
        result=placement(book,page,mode)
        if result['status']=='blocked':raise ValueError(result['code']+': '+result['message'])


def paint(book,painter,page,mode=None,clip=None,outlines=False):
    if not enabled_for(book.state):return
    from .pages import page_rect
    mode=mode or book.view['mode'];result=placement(book,page,mode)
    if result['status']!='placed':return
    if book.state.get('printEdition'):
        from .print_edition import shape
        from PySide6.QtGui import QColor
        path,_=shape(book,result['text'],result['sizePt'])
        painter.save()
        try:
            painter.setClipRect(page_rect(page) if clip is None else page_rect(page).intersected(clip))
            painter.setRenderHint(QPainter.RenderHint.Antialiasing,True)
            painter.scale(SCALE,SCALE);painter.setPen(Qt.PenStyle.NoPen);painter.setBrush(QColor('#111111'))
            painter.drawPath(path.translated(result['origin'][0]/SCALE,result['origin'][1]/SCALE))
        finally:painter.restore()
        return
    if mode=='color' and outlines:raise ValueError('PAINT_REQUIRES_RASTER_FALLBACK: Unta page number')
    painter.save()
    try:
        painter.setClipRect(page_rect(page) if clip is None else page_rect(page).intersected(clip))
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        em=result['sizePt']*SCALE
        if mode=='color':
            transform=painter.deviceTransform();scale=max(math.hypot(transform.m11(),transform.m12()),math.hypot(transform.m21(),transform.m22()))
            for component in ('glow','surface') if book.state['paint']['recipe'].get('lightingModel')=='individual-glyphs-1' else ('composite',):
                for glyph in result['glyphs']:book.paint_renderer.draw(painter,BINDING,glyph['glyphId'],em,scale*2,glyph['origin'],component)
        else:
            _,ink=palette(book.state['paint']['background'],book.view.get('monochromePaper','auto'))
            raw=book.fonts.raw(MASTER,em);painter.setPen(Qt.PenStyle.NoPen);painter.setBrush(ink)
            for glyph in result['glyphs']:painter.drawPath(raw.pathForGlyph(glyph['glyphId']).translated(*glyph['origin']))
    finally:painter.restore()
