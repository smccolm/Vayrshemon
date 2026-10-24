"""One Qt layout, positioned-glyph renderer, bounded raster surfaces."""
import hashlib
import json
import math
import time

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTextBoundaryFinder
from PySide6.QtGui import QColor, QGlyphRun, QImage, QPainter, QPen, QTextLayout

from .session import SCALE, STYLE, scalar_offset
from .monochrome import palette

MAX_PIXELS = 16_000_000


def rectangle(rect):
    return [round(rect.x(), 6), round(rect.y(), 6), round(rect.width(), 6), round(rect.height(), 6)]


def runs(session):
    session.doc.documentLayout().documentSize()
    block = session.doc.begin()
    while block.isValid():
        layout = block.layout()
        iterator = block.begin()
        while not iterator.atEnd():
            fragment = iterator.fragment()
            if fragment.isValid() and fragment.length():
                # Query each semantic format separately. Qt otherwise merges
                # same-font runs across color/language/feature boundaries.
                start = fragment.position()-block.position()
                for run in layout.glyphRuns(start, fragment.length(), QTextLayout.GlyphRunRetrievalFlag.RetrieveAll):
                    yield block, layout, run, fragment.charFormat()
            iterator += 1
        block = block.next()


def glyph_key(raw, gid, position):
    return raw.familyName(), raw.pixelSize(), gid, round(position.x(),6), round(position.y(),6)


def source_ranges(groups, limit):
    """Recover source coverage by querying native grapheme ranges.

    Qt 6.8.3's stringIndexes can return zero indexes after emoji font fallback.
    Range queries retain correct glyph positions. Union the queried graphemes
    sharing a glyph (including split ligatures), rather than inventing indexes.
    """
    targets, blocks, count = {}, {}, 0
    for block, text_layout, run, _ in groups:
        blocks[block.position()] = block, text_layout
        for gid, position in zip(run.glyphIndexes(),run.positions()):
            if count >= limit:
                break
            targets.setdefault(block.position(),set()).add(glyph_key(run.rawFont(),gid,position))
            count += 1
    mappings = {}
    for offset, wanted in targets.items():
        block, text_layout = blocks[offset]
        finder = QTextBoundaryFinder(QTextBoundaryFinder.BoundaryType.Grapheme,block.text())
        start = 0
        found = {}
        while True:
            end = finder.toNextBoundary()
            if end < 0:
                break
            touched = False
            for run in text_layout.glyphRuns(start,end-start,QTextLayout.GlyphRunRetrievalFlag.RetrieveGlyphIndexes |
                                             QTextLayout.GlyphRunRetrievalFlag.RetrieveGlyphPositions):
                for gid, position in zip(run.glyphIndexes(),run.positions()):
                    key = glyph_key(run.rawFont(),gid,position)
                    if key in wanted:
                        prior = found.get(key,(start,end))
                        found[key] = min(start,prior[0]),max(end,prior[1])
                        touched = True
            if not touched and wanted <= found.keys():
                break
            start = end
        mappings[offset] = found
    return mappings


def inspect(session, *, max_glyphs=5000):
    started = time.perf_counter()
    max_glyphs = max(1, min(int(max_glyphs), 100_000))
    glyphs, lines, warnings = [], [], []
    styles = {s['styleId']: s for s in session.model['styles']}
    spans = session.spans()
    groups = list(runs(session))
    source_map = source_ranges(groups,max_glyphs)
    for block, layout, run, fmt in groups:
        raw = run.rawFont()
        face = session.fonts.by_family.get(raw.familyName())
        indexes, positions, source_indexes = run.glyphIndexes(), run.positions(), run.stringIndexes()
        nominal = raw.advancesForGlyphIndexes(indexes)
        for index, (gid, position) in enumerate(zip(indexes, positions)):
            if len(glyphs) >= max_glyphs:
                break
            source_range = source_map.get(block.position(),{}).get(glyph_key(raw,gid,position))
            if source_range is None:
                warnings.append(dict(code='TRANSIENT_OR_UNMAPPED_GLYPH',message='Source mapping unavailable during preedit; no source index is asserted.'))
                continue
            local,end = source_range
            text = block.text()
            source = text[scalar_offset(text, local):scalar_offset(text, end)]
            origin = layout.position() + position
            line = layout.lineForTextPosition(local)
            leading = line.cursorToX(local)[0]
            trailing = line.cursorToX(end)[0]
            style_id = fmt.property(STYLE)
            expected = styles[style_id]['fontId'] if style_id in styles else None
            features = session.style_features.get(style_id, session.features)
            fallback = None
            if expected and (not face or face.font_id != expected):
                fallback = 'Requested font lacks coverage or Qt substituted a shaping font.'
            elif not expected:
                fallback = 'Explicit system-default font; geometry is scoped to the recorded platform font.'
            ink = raw.boundingRect(gid).translated(origin)
            glyphs.append(dict(glyphId=gid, fontId=face.font_id if face else None, family=raw.familyName(),
                               selectedFontId=expected, fallbackReason=fallback,
                               sourceUtf16=[block.position()+local, block.position()+end], source=source,
                               sourceScalars=[ord(c) for c in source], cluster=block.position()+local,
                               origin=[round(origin.x(), 6), round(origin.y(), 6)],
                               nominalAdvance=[round(nominal[index].x(), 6), round(nominal[index].y(), 6)],
                               clusterAdvance=round(abs(trailing-leading), 6),
                               offsetFromClusterCaret=[round(position.x()-leading, 6),
                                                       round(position.y()-(line.y()+line.ascent()), 6)],
                               inkBounds=rectangle(ink), rightToLeft=run.isRightToLeft(),
                               pixelSize=raw.pixelSize(), features=dict(features)))
    block = session.doc.begin()
    while block.isValid():
        layout = block.layout()
        for index in range(layout.lineCount()):
            line = layout.lineAt(index)
            p = layout.position() + line.position()
            lines.append(dict(sourceUtf16=[block.position()+line.textStart(), block.position()+line.textStart()+line.textLength()],
                              baseline=round(p.y()+line.ascent(), 6), x=round(p.x(), 6),
                              width=round(line.naturalTextWidth(), 6), height=round(line.height(), 6)))
        block = block.next()
    page = session.model['pages'][0]
    width = int(page['widthMicroPoints']) / 1_000_000 * SCALE
    height = int(page['heightMicroPoints']) / 1_000_000 * SCALE
    size = session.doc.size()
    if size.height() > height:
        warnings.append(dict(code='PAGE_OVERFLOW', message='Text extends below the page. It remains editable; page export clips to its declared height.'))
    if any(g['glyphId'] == 0 for g in glyphs):
        warnings.append(dict(code='MISSING_GLYPH', message='One or more source clusters have no glyph in the selected/fallback fonts.'))
    if session.composing:
        warnings.append(dict(code='COMPOSITION_ACTIVE', message='Preedit text is transient; commit or cancel it before saving or scripted edits.'))
    geometry = dict(page=[width, height], lines=lines, glyphs=glyphs)
    digest = hashlib.sha256(json.dumps(geometry, sort_keys=True, ensure_ascii=True).encode()).hexdigest()
    return dict(revision=session.revision, geometryHash=digest, units='logical-pixels-at-96-dpi',
                pagePoints=[width/SCALE, height/SCALE], contentSize=[size.width(), size.height()],
                glyphs=glyphs, lines=lines, truncated=len(glyphs) >= max_glyphs,
                diagnostics=warnings, elapsedMs=(time.perf_counter()-started)*1000,
                offsetDefinition='Glyph origin minus Qt cluster caret and line baseline; not raw HarfBuzz buffer offsets.',
                clusterDefinition='Union of native grapheme-range queries that return the same positioned glyph, including split ligatures.',
                engine=session.fingerprint())


def paint(session, painter, *, mode='color', clip=None, overlays=None, monochrome_ink=None):
    overlays = overlays or {}
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    if clip:
        painter.setClipRect(clip)
    recipe = session.fonts.recipe
    for block, layout, run, fmt in runs(session):
        origin = layout.position()
        if clip and not run.boundingRect().translated(origin).intersects(clip):
            continue
        face = session.fonts.by_family.get(run.rawFont().familyName())
        painter.save()
        if run.flags() & QGlyphRun.GlyphRunFlag.SplitLigature:
            painter.setClipRect(run.boundingRect().translated(origin),Qt.ClipOperation.IntersectClip)
        if mode == 'color' and recipe and face and face.font_id == recipe['master']:
            for layer in recipe['layers']:
                if not layer['enabled']:
                    continue
                colored = QGlyphRun(run)
                colored.setRawFont(session.fonts.raw(layer['fontId'], run.rawFont().pixelSize()))
                colored.setGlyphIndexes([layer['glyphMap'][gid] for gid in run.glyphIndexes()])
                painter.setPen(QColor(layer['color']))
                painter.drawGlyphRun(origin, colored)
        elif mode=='mono':
            # Fill the same positioned outlines with grayscale antialiasing;
            # native ClearType glyph runs can add colored edge pixels.
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(monochrome_ink if monochrome_ink is not None else palette(paper=getattr(session,'owner',session).view.get('monochromePaper','auto'))[1])
            raw=run.rawFont()
            for gid,position in zip(run.glyphIndexes(),run.positions()):
                path=raw.pathForGlyph(gid)
                if path.isEmpty() and not raw.boundingRect(gid).isEmpty():raise ValueError('VECTOR_GLYPH_HAS_NO_OUTLINE')
                painter.drawPath(path.translated(origin+position))
        else:
            painter.setPen(fmt.foreground().color())
            painter.drawGlyphRun(origin, run)
        painter.restore()
        if overlays.get('origins') or overlays.get('bounds'):
            for gid, position in zip(run.glyphIndexes(), run.positions()):
                p = origin + position
                if overlays.get('origins'):
                    painter.setPen(QPen(QColor('#df3752'), 0))
                    painter.drawLine(p + QPointF(-3, 0), p + QPointF(3, 0))
                    painter.drawLine(p + QPointF(0, -3), p + QPointF(0, 3))
                if overlays.get('bounds'):
                    painter.setPen(QPen(QColor('#c77716'), 0))
                    painter.drawRect(run.rawFont().boundingRect(gid).translated(p))
    if overlays.get('baselines'):
        painter.setPen(QPen(QColor('#44999c'), 0, Qt.PenStyle.DashLine))
        block = session.doc.begin()
        while block.isValid():
            layout = block.layout()
            for index in range(layout.lineCount()):
                line = layout.lineAt(index)
                p = layout.position() + line.position() + QPointF(0, line.ascent())
                painter.drawLine(p, p + QPointF(line.naturalTextWidth(), 0))
            block = block.next()


def render(session, path=None, *, mode='color', dpi=96, region=None, overlays=None):
    if mode not in ('mono', 'color') or not math.isfinite(dpi) or not 24 <= dpi <= 1200:
        raise ValueError('INVALID_RENDER_MODE_OR_DPI')
    page = session.model['pages'][0]
    page_rect = QRectF(0, 0, int(page['widthMicroPoints']) / 1_000_000 * SCALE,
                      int(page['heightMicroPoints']) / 1_000_000 * SCALE)
    area = QRectF(*region) if region else page_rect
    if not all(math.isfinite(v) for v in rectangle(area)) or area.width() <= 0 or area.height() <= 0:
        raise ValueError('INVALID_RENDER_REGION')
    if not page_rect.contains(area):
        raise ValueError('RENDER_REGION_OUTSIDE_PAGE')
    scale = dpi / 96
    width, height = math.ceil(area.width()*scale), math.ceil(area.height()*scale)
    if width * height > MAX_PIXELS or max(width, height) > 32767:
        raise ValueError('RASTER_LIMIT: request a region/tile; maximum 16 million pixels and 32767 pixels per edge')
    started = time.perf_counter()
    image = QImage(QSize(width, height), QImage.Format.Format_ARGB32_Premultiplied)
    if image.isNull():
        raise MemoryError('RASTER_ALLOCATION_FAILED')
    image.setDotsPerMeterX(round(dpi/0.0254))
    image.setDotsPerMeterY(round(dpi/0.0254))
    image.fill(palette(paper=getattr(session,'owner',session).view.get('monochromePaper','auto'))[0] if mode=='mono' else QColor('#ffffff'))
    painter = QPainter(image)
    try:
        painter.scale(scale, scale)
        painter.translate(-area.x(), -area.y())
        paint(session, painter, mode=mode, clip=area, overlays=overlays)
    finally:
        painter.end()
    if path:
        path = session.output_path(path)
        if path.exists():
            raise ValueError('RENDER_TARGET_EXISTS: choose a new path')
        path.parent.mkdir(parents=True, exist_ok=True)
        if not image.save(str(path), 'PNG'):
            raise OSError('PNG_SAVE_FAILED')
    result = dict(path=str(path) if path else None, width=width, height=height, dpi=dpi,
                  region=rectangle(area), bufferBytes=image.sizeInBytes(), elapsedMs=(time.perf_counter()-started)*1000)
    session.log.emit('renderer', 'RENDER_COMPLETED', revision=session.revision, **result)
    return image, result


def hit_test(session, x, y):
    if not math.isfinite(x) or not math.isfinite(y):
        raise ValueError('INVALID_POINT')
    offset = session.doc.documentLayout().hitTest(QPointF(x, y), Qt.HitTestAccuracy.FuzzyHit)
    return dict(offset=max(0, offset), offsetUnit='utf16-code-unit', revision=session.revision)
