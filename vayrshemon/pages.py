"""Page composition and portable outline SVG from the native frame layouts."""
import hashlib
import json
import math
import time
import xml.etree.ElementTree as ET
from PySide6.QtCore import QRectF,QPointF,QSize,QByteArray,QBuffer,QIODevice,QSaveFile,Qt
from PySide6.QtGui import QPainter,QColor,QImage,QPen,QGlyphRun,QPainterPath
from PySide6.QtSvg import QSvgGenerator
from . import layout
from .session import SCALE


def selected_page(book,page_id=None):
    if page_id is None: return book.current_page()
    page=next((p for p in book.state['pages'] if p['pageId']==page_id),None)
    if page is None: raise ValueError('PAGE_NOT_FOUND')
    return page


def rect(frame): return QRectF(*(int(frame[k])/1_000_000*SCALE for k in ('x','y','width','height')))
def page_rect(page): return QRectF(0,0,int(page['width'])/1_000_000*SCALE,int(page['height'])/1_000_000*SCALE)


def inspect(book,*,page_id=None,max_glyphs=5000):
    page=selected_page(book,page_id)
    if hasattr(book,'composition') and ('paint' in book.state or any(c['enabled'] for c in book.state['typesetting']['frames'].values())):
        return book.composition().report(page['pageId'],max_glyphs)
    records=[]; diagnostics=[]; remaining=max_glyphs
    for frame in page['frames']:
        native=book.frames[frame['frameId']]
        info=layout.inspect(native,max_glyphs=max(1,remaining))
        position=rect(frame)
        for glyph in info['glyphs']:
            glyph['origin']=[glyph['origin'][0]+position.x(),glyph['origin'][1]+position.y()]
            glyph['inkBounds'][0]+=position.x(); glyph['inkBounds'][1]+=position.y()
            glyph['frameId']=frame['frameId']
        for line in info['lines']: line['x']+=position.x(); line['baseline']+=position.y()
        overset=info['contentSize'][1]>position.height()+.01 or any(g['inkBounds'][0]<position.x()-.01 or g['inkBounds'][0]+g['inkBounds'][2]>position.right()+.01 or g['inkBounds'][1]<position.y()-.01 or g['inkBounds'][1]+g['inkBounds'][3]>position.bottom()+.01 for g in info['glyphs'])
        info['diagnostics']=[d for d in info['diagnostics'] if d['code']!='PAGE_OVERFLOW']
        if overset: info['diagnostics'].append(dict(code='FRAME_OVERFLOW',message='Text exceeds this frame; all source text is retained.',policy=frame['overflow']))
        for warning in info['diagnostics']: diagnostics.append(dict(warning,frameId=frame['frameId']))
        records.append(dict(frameId=frame['frameId'],name=frame['name'],rect=layout.rectangle(position),overflow=overset,layout=info))
        remaining-=len(info['glyphs'])
        if remaining<=0: break
    geometry=dict(page=[page['width'],page['height']],frames=[dict(frameId=r['frameId'],rect=r['rect'],glyphs=r['layout']['glyphs'],lines=r['layout']['lines']) for r in records])
    return dict(revision=book.revision,pageId=page['pageId'],pagePoints=[int(page['width'])/1_000_000,int(page['height'])/1_000_000],
                geometryHash=hashlib.sha256(json.dumps(geometry,sort_keys=True).encode()).hexdigest(),frames=records,
                glyphs=[g for r in records for g in r['layout']['glyphs']],diagnostics=diagnostics,truncated=remaining<=0,
                units='logical-pixels-at-96-dpi',engine=book.fingerprint())


def outline_paint(native,painter,mode,clip):
    recipe=native.fonts.recipe
    for block,text_layout,run,fmt in layout.runs(native):
        face=native.fonts.by_family.get(run.rawFont().familyName())
        layers=recipe['layers'] if mode=='color' and recipe and face and face.font_id==recipe['master'] else None
        clip_path=QPainterPath(); clip_path.addRect(clip)
        if run.flags() & QGlyphRun.GlyphRunFlag.SplitLigature:
            split=QPainterPath(); split.addRect(run.boundingRect().translated(text_layout.position()))
            clip_path=clip_path.intersected(split)
        paints=[(native.fonts.raw(layer['fontId'],run.rawFont().pixelSize()),[layer['glyphMap'][g] for g in run.glyphIndexes()],QColor(layer['color'])) for layer in layers if layer['enabled']] if layers else [(run.rawFont(),run.glyphIndexes(),fmt.foreground().color())]
        painter.setPen(Qt.PenStyle.NoPen)
        for raw,indexes,color in paints:
            painter.setBrush(color)
            for gid,position in zip(indexes,run.positions()):
                path=raw.pathForGlyph(gid)
                if path.isEmpty() and not raw.boundingRect(gid).isEmpty():
                    raise ValueError('VECTOR_GLYPH_HAS_NO_OUTLINE: bitmap/color fallback requires PNG; glyph '+str(gid))
                origin=text_layout.position()+position
                # Bake clipping into paths; SVG paint engines need not support
                # the raster painter's clip state.
                painter.drawPath(path.translated(origin).intersected(clip_path))


def paint(book,painter,*,page_id=None,mode=None,clip=None,overlays=None,guides=False,outlines=False):
    page=selected_page(book,page_id); boundary=page_rect(page)
    if hasattr(book,'composition') and ('paint' in book.state or any(c['enabled'] for c in book.state['typesetting']['frames'].values())):
        return book.composition(mode).paint(painter,page['pageId'],mode,clip,overlays,guides,outlines)
    mode=mode or book.view['mode']; overlays=overlays or {}
    painter.save()
    painter.setClipRect(boundary if clip is None else boundary.intersected(clip))
    painter.fillRect(boundary,QColor('white'))
    for frame in page['frames']:
        area=rect(frame); native=book.frames[frame['frameId']]
        painter.save()
        if frame['overflow']=='clip': painter.setClipRect(area,Qt.ClipOperation.IntersectClip)
        painter.translate(area.topLeft())
        local_clip=(boundary if clip is None else boundary.intersected(clip)).translated(-area.topLeft())
        if frame['overflow']=='clip': local_clip=local_clip.intersected(QRectF(0,0,area.width(),area.height()))
        if outlines: outline_paint(native,painter,mode,local_clip)
        else: layout.paint(native,painter,mode=mode,clip=local_clip,overlays=overlays)
        painter.restore()
        if guides:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor('#3d7499' if frame['frameId']==book.state['activeFrameId'] else '#a8b3ba'),0,Qt.PenStyle.DashLine))
            painter.drawRect(area)
            if native.doc.size().height()>area.height():
                painter.setPen(QPen(QColor('#c83242'),0)); painter.drawText(area.bottomLeft()+QPointF(2,-3),'OVERFLOW')
    if guides:
        margins=page['margins']
        inset=QRectF(int(margins['left'])/1e6*SCALE,int(margins['top'])/1e6*SCALE,
                      (int(page['width'])-int(margins['left'])-int(margins['right']))/1e6*SCALE,
                      (int(page['height'])-int(margins['top'])-int(margins['bottom']))/1e6*SCALE)
        painter.setPen(QPen(QColor('#c1b49a'),0,Qt.PenStyle.DotLine)); painter.drawRect(inset)
    painter.restore()


def target(book,path):
    path=book.output_path(path)
    if path.exists(): raise ValueError('EXPORT_TARGET_EXISTS')
    path.parent.mkdir(parents=True,exist_ok=True)
    return path


def render(book,path=None,*,page_id=None,mode='color',dpi=96,region=None,overlays=None):
    if not math.isfinite(dpi) or not 24<=dpi<=1200 or mode not in ('mono','color'): raise ValueError('INVALID_RENDER_SETTINGS')
    page=selected_page(book,page_id); boundary=page_rect(page)
    area=QRectF(*region) if region else boundary
    if not all(math.isfinite(v) for v in layout.rectangle(area)) or area.width()<=0 or area.height()<=0 or not boundary.contains(area): raise ValueError('INVALID_RENDER_REGION')
    scale=dpi/96; width,height=math.ceil(area.width()*scale),math.ceil(area.height()*scale)
    if width*height>layout.MAX_PIXELS or max(width,height)>32767: raise ValueError('RASTER_LIMIT: use a bounded region')
    started=time.perf_counter()
    image=QImage(width,height,QImage.Format.Format_ARGB32_Premultiplied)
    if image.isNull(): raise MemoryError('RASTER_ALLOCATION_FAILED')
    image.setDotsPerMeterX(round(dpi/.0254)); image.setDotsPerMeterY(round(dpi/.0254)); image.fill(Qt.GlobalColor.transparent if 'paint' in book.state else QColor('white'))
    painter=QPainter(image)
    try:
        painter.scale(scale,scale); painter.translate(-area.topLeft())
        paint(book,painter,page_id=page['pageId'],mode=mode,clip=area,overlays=overlays)
    finally: painter.end()
    if path:
        path=target(book,path)
        if not image.save(str(path),'PNG'): raise OSError('PNG_SAVE_FAILED')
    report=dict(path=str(path) if path else None,pageId=page['pageId'],width=width,height=height,dpi=dpi,bufferBytes=image.sizeInBytes(),elapsedMs=(time.perf_counter()-started)*1000)
    book.log.emit('renderer','PAGE_RENDERED',**report)
    return image,report


def export_svg(book,path,*,page_id=None,mode='color'):
    path=target(book,path); page=selected_page(book,page_id); boundary=page_rect(page)
    data=QByteArray(); buffer=QBuffer(data); buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    generator=QSvgGenerator(); generator.setOutputDevice(buffer); generator.setResolution(96)
    generator.setSize(QSize(math.ceil(boundary.width()),math.ceil(boundary.height()))); generator.setViewBox(boundary)
    generator.setTitle(book.state['title']); generator.setDescription('Vayrshemon outline proof. Text semantics remain in the source document.')
    painter=QPainter(generator)
    try: paint(book,painter,page_id=page['pageId'],mode=mode,outlines=True)
    finally: painter.end(); buffer.close()
    root=ET.fromstring(bytes(data))
    if any(e.tag.split('}')[-1] in ('text','image') for e in root.iter()): raise ValueError('SVG_NOT_PURE_OUTLINES')
    root.set('width',str(int(page['width'])/1e6)+'pt'); root.set('height',str(int(page['height'])/1e6)+'pt')
    payload=ET.tostring(root,encoding='utf-8',xml_declaration=True)
    output=QSaveFile(str(path))
    if not output.open(QIODevice.OpenModeFlag.WriteOnly) or output.write(payload)!=len(payload) or not output.commit(): raise OSError('SVG_SAVE_FAILED')
    result=dict(path=str(path),pageId=page['pageId'],kind='outline-svg',searchableText=False,sha256=hashlib.sha256(payload).hexdigest())
    book.log.emit('renderer','SVG_EXPORTED',**result)
    return result


def hit_test(book,x,y,page_id=None):
    page=selected_page(book,page_id)
    if not all(math.isfinite(v) for v in (x,y)): raise ValueError('INVALID_POINT')
    if hasattr(book,'composition') and ('paint' in book.state or any(c['enabled'] for c in book.state['typesetting']['frames'].values())):
        return book.composition().hit_test(page['pageId'],x,y)
    for frame in reversed(page['frames']):
        area=rect(frame)
        if area.contains(QPointF(x,y)):
            result=layout.hit_test(book.frames[frame['frameId']],x-area.x(),y-area.y())
            result.update(frameId=frame['frameId'],pageId=page['pageId'],revision=book.revision)
            return result
    return dict(frameId=None,pageId=page['pageId'],offset=None,revision=book.revision)
