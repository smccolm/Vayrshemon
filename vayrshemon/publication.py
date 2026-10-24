"""Deliberate sRGB proof export with honest extraction and rasterization reports."""
import base64
import hashlib
import math
from pathlib import Path
from fontTools.ttLib import TTFont
from PySide6.QtCore import QByteArray,QBuffer,QIODevice,QSaveFile,QSizeF,QRectF,Qt
from PySide6.QtGui import QImage,QPainter,QColor,QPdfWriter,QPageSize,QPageLayout
from . import pages,layout
from .session import SCALE
from .paint import signature,ENGINE_VERSION


def atomic(path,data):
    file=QSaveFile(str(path))
    if not file.open(QIODevice.OpenModeFlag.WriteOnly): raise OSError(file.errorString())
    if file.write(data)!=len(data): file.cancelWriting();raise OSError('SHORT_WRITE')
    if not file.commit(): raise OSError(file.errorString())


def preflight(book,format='pdf',mode='color',dpi=300,raster_policy='reject',page_id=None):
    chosen=[pages.selected_page(book,page_id)] if page_id else book.state['pages']
    result=[]; issues=[]; fonts=[]
    for source in book.capture()['fontSources']:
        path=Path(source['path']); valid=path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==source['sha256']
        flags=None
        if valid:
            with TTFont(path) as f: flags=f['OS/2'].fsType if 'OS/2' in f else None
        fonts.append(dict(fontId=source['fontId'],available=valid,fsType=flags,embedded=False))
        if not valid: issues.append(dict(code='MISSING_OR_CHANGED_FONT',severity='error',fontId=source['fontId']))
    painted=0;fonts_valid=not any(i['severity']=='error' for i in issues)
    for page in chosen:
        pid=page['pageId']; area=pages.page_rect(page)
        comp=None
        if fonts_valid:
            try: comp=book.composition(mode,page_id=pid)
            except (ValueError,OSError) as error: issues.append(dict(code='LAYOUT_UNAVAILABLE',severity='error',pageId=pid,message=str(error)))
        w,h=math.ceil(area.width()*dpi/96),math.ceil(area.height()*dpi/96)
        if comp is None:
            result.append(dict(pageId=pid,points=[int(page[k])/1e6 for k in ('width','height')],pixels=[w,h],geometryHash=None,collisionCount=None));continue
        report=comp.report(pid,20000)
        for diagnostic in report['diagnostics']: issues.append(dict(diagnostic,severity='warning',pageId=pid))
        if any(g['missingGlyph'] for g in report['glyphs']): issues.append(dict(code='MISSING_GLYPHS',severity='error',pageId=pid))
        for glyph in report['glyphs']:
            if mode!='color' or not book.paint_renderer.binding(glyph['fontId']): continue
            painted+=1
            bounds=QRectF(*glyph['effectBounds'])
            frame=next(f for f in page['frames'] if f['frameId']==glyph['frameId'])
            clip=area.intersected(pages.rect(frame)) if frame['overflow']=='clip' else area
            if not bounds.isEmpty() and not clip.contains(bounds): issues.append(dict(code='PAINT_CLIPPED',severity='warning',pageId=pid,frameId=glyph['frameId'],sourceUtf16=glyph['sourceUtf16']))
        result.append(dict(pageId=pid,points=report['pagePoints'],pixels=[w,h],geometryHash=report['geometryHash'],collisionCount=report['collisionReport']['afterCount']))
    fallback=bool(painted and format in ('svg','pdf'))
    if format=='png' or fallback:
        for page in result:
            w,h=page['pixels']
            if w>32767 or h>32767 or w*h>layout.MAX_PIXELS: issues.append(dict(code='RASTER_SIZE_LIMIT',severity='error',pageId=page['pageId']))
    if fallback and raster_policy!='raster': issues.append(dict(code='RASTER_APPROVAL_REQUIRED',severity='error',message='Bevel, shadow and glow require raster_policy=raster and explicit DPI.'))
    if painted and mode=='color': issues.append(dict(code='DECORATIVE_RASTER',severity='info',message='Color effects are rasterized at export DPI; native document retains editable source text.'))
    if format=='pdf' and QColor(book.state['paint']['background']).alpha()<255: issues.append(dict(code='PDF_TRANSPARENCY_ON_WHITE',severity='warning',message='PDF proof uses white paper behind transparent page pixels.'))
    return dict(ok=not any(i['severity']=='error' for i in issues),format=format,mode=mode,dpi=dpi,pages=result,issues=issues,fonts=fonts,
        rasterFallback=fallback,rasterPolicy=raster_policy,searchable=False,textExtraction='No semantic text is embedded: raster or outline proof. Use native document for copy/search.',
        colorSpace='sRGB proof; no CMYK or ICC conversion',recipeHash=signature(book.state['paint']['recipe']),bindingProfiles=[dict(fontId=b['fontId'],profileId=b['profile'],profileHash=signature(book.paint_renderer.profile(b))) for b in book.state['paint']['bindings'] if b.get('profile') and b['enabled']],paintEngineVersion=ENGINE_VERSION,revision=book.revision)


def raster(book,page,mode,dpi):
    area=pages.page_rect(page);w,h=math.ceil(area.width()*dpi/96),math.ceil(area.height()*dpi/96)
    if w>32767 or h>32767 or w*h>layout.MAX_PIXELS: raise ValueError('RASTER_SIZE_LIMIT')
    image=QImage(w,h,QImage.Format.Format_ARGB32_Premultiplied)
    if image.isNull(): raise ValueError('RASTER_ALLOCATION_FAILED')
    image.fill(Qt.GlobalColor.transparent);image.setDotsPerMeterX(round(dpi/.0254));image.setDotsPerMeterY(round(dpi/.0254))
    painter=QPainter(image)
    try: painter.scale(dpi/96,dpi/96);pages.paint(book,painter,page_id=page['pageId'],mode=mode)
    finally: painter.end()
    return image


def png_bytes(image):
    data=QByteArray();buffer=QBuffer(data);buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    if not image.save(buffer,'PNG'): raise OSError('PNG_ENCODE_FAILED')
    return bytes(data)


def export(book,path,format='pdf',mode='color',dpi=300,raster_policy='reject',page_id=None):
    check=preflight(book,format,mode,dpi,raster_policy,page_id)
    if not check['ok']: raise ValueError('PUBLICATION_PREFLIGHT_FAILED: '+str([i['code'] for i in check['issues'] if i['severity']=='error']))
    chosen=[pages.selected_page(book,page_id)] if page_id else book.state['pages']
    if format!='pdf' and len(chosen)!=1: raise ValueError('SINGLE_PAGE_FORMAT: provide page_id')
    target=pages.target(book,path)
    if format=='png': atomic(target,png_bytes(raster(book,chosen[0],mode,dpi)))
    elif format=='svg':
        if not check['rasterFallback']: return dict(pages.export_svg(book,path,page_id=chosen[0]['pageId'],mode=mode),preflight=check)
        page=chosen[0];w,h=(int(page[k])/1e6 for k in ('width','height'))
        encoded=base64.b64encode(png_bytes(raster(book,page,mode,dpi))).decode()
        atomic(target,(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}pt" height="{h}pt" viewBox="0 0 {w} {h}"><title>Vayrshemon raster proof at {dpi} DPI; no searchable text</title><image width="{w}" height="{h}" href="data:image/png;base64,{encoded}"/></svg>').encode())
    else:
        # QSaveFile gives all-or-nothing multi-page output, including on a later
        # page render failure. No native source-font subset is embedded.
        file=QSaveFile(str(target))
        if not file.open(QIODevice.OpenModeFlag.WriteOnly): raise OSError(file.errorString())
        writer=QPdfWriter(file);writer.setResolution(dpi);writer.setTitle(book.state['title']);writer.setCreator('Vayrshemon M4 / raster or outline proof')
        def size(page):
            writer.setPageSize(QPageSize(QSizeF(int(page['width'])/1e6,int(page['height'])/1e6),QPageSize.Unit.Point,'Custom',QPageSize.SizeMatchPolicy.ExactMatch))
            layout_=writer.pageLayout();layout_.setMode(QPageLayout.Mode.FullPageMode);writer.setPageLayout(layout_)
        size(chosen[0]);painter=QPainter(writer)
        try:
            for index,page in enumerate(chosen):
                if index: size(page);assert writer.newPage(),'PDF_NEW_PAGE_FAILED'
                if check['rasterFallback']:
                    image=raster(book,page,mode,dpi);area=pages.page_rect(page)
                    painter.drawImage(QRectF(0,0,area.width()*dpi/96,area.height()*dpi/96),image)
                else:
                    painter.save();painter.scale(dpi/96,dpi/96)
                    pages.paint(book,painter,page_id=page['pageId'],mode=mode,outlines=True);painter.restore()
            painter.end();del writer
            if not file.commit(): raise OSError(file.errorString())
        except Exception:
            if painter.isActive(): painter.end()
            file.cancelWriting();raise
    data=target.read_bytes();result=dict(path=str(target),bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),preflight=check)
    book.log.emit('publication','EXPORTED',**result);return result
