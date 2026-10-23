"""Reproducible COLR v0/CPAL fallback from verified TTF contours.

COLR v0 supports flat layers, not the M4 lighting. The caller must explicitly
choose this reduced treatment; the full reference treatment exports as a proof.
"""
from copy import deepcopy
from io import BytesIO
import hashlib
import json
from fontTools import __version__ as fonttools_version
from fontTools.ttLib import TTFont
from fontTools.colorLib.builder import buildCOLR,buildCPAL
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from .paint import signature,rgb
from . import pages
from .publication import atomic


def build(book,font_id,path,treatment):
    if treatment!='flat-colr-v0': raise ValueError('EXPLICIT_COLR_FALLBACK_REQUIRED')
    binding=book.paint_renderer.binding(font_id)
    if not binding or binding['kind']!='layered': raise ValueError('COLOR_FONT_REQUIRES_VERIFIED_LAYER_BINDING')
    book.validate_binding(binding);master=book.fonts.resolve(font_id);interior=book.fonts.resolve(binding['interiorFontId'])
    recipe=deepcopy(book.state['paint']['recipe']);identity=signature(dict(binding=binding,recipe=recipe,compiler=fonttools_version,treatment=treatment))
    output=pages.target(book,path);manifest=output.with_suffix(output.suffix+'.build.json')
    if manifest.exists(): raise ValueError('BUILD_MANIFEST_EXISTS')
    # Use original bytes, not Qt's private process-only renamed font.
    font=TTFont(master.path,recalcTimestamp=False);source=TTFont(interior.path,recalcTimestamp=False)
    before={tag:hashlib.sha256(font.getTableData(tag)).hexdigest() for tag in ('cmap','hmtx','GPOS','GSUB','kern') if tag in font}
    old_order=list(font.getGlyphOrder());layers={};mapping=[]
    if len(old_order)>2000: raise ValueError('COLOR_FONT_GLYPH_LIMIT: 2,000 base glyphs')
    for index,name in enumerate(old_order):
        pairs=[]
        for role,original,palette in [('interior',source,0),('rim',font,1)]:
            new_name=f'm4.{role}.{index}'
            if new_name in font['glyf'].glyphs: raise ValueError('COLOR_GLYPH_NAME_CONFLICT')
            glyphs=original.getGlyphSet();recording=DecomposingRecordingPen(glyphs);glyphs[name].draw(recording)
            pen=TTGlyphPen(None);recording.replay(pen);glyph=pen.glyph()
            font['glyf'][new_name]=glyph
            font['hmtx'][new_name]=(master.metrics[name][0],original['hmtx'][name][1])
            pairs.append((new_name,palette))
        layers[name]=pairs;mapping.append(dict(base=name,layers=pairs))
    font.setGlyphOrder(old_order+[name for pair in layers.values() for name,_ in pair])
    palette=[tuple(float(c) for c in rgb(recipe[key]))+(1.,) for key in ('recess','rim')]
    font['COLR']=buildCOLR(layers,version=0,glyphMap=font.getReverseGlyphMap());font['CPAL']=buildCPAL([palette])
    family='Vayrshemon Color '+identity[:12]
    for record in font['name'].names:
        if record.nameID in (1,3,4,6,16,21): record.string=family.replace(' ','').encode(record.getEncoding()) if record.nameID==6 else family.encode(record.getEncoding())
    for tag in ('DSIG',):
        if tag in font: del font[tag]
    font.recalcTimestamp=False;buffer=BytesIO();font.save(buffer,reorderTables=True);data=buffer.getvalue()
    check=TTFont(BytesIO(data),recalcTimestamp=False,checkChecksums=2)
    if check.getBestCmap()!=font.getBestCmap(): raise ValueError('COLOR_CMAP_CHANGED')
    if any(check['hmtx'][name]!=master.metrics[name] for name in old_order): raise ValueError('COLOR_ADVANCES_CHANGED')
    for tag in ('GPOS','GSUB','kern'):
        if tag in before and hashlib.sha256(check.getTableData(tag)).hexdigest()!=before[tag]: raise ValueError('COLOR_SHAPING_TABLE_CHANGED')
    report=dict(buildVersion='1.0.0',treatment=treatment,compiler=dict(fontTools=fonttools_version),sourceFonts=[dict(fontId=f.font_id,sha256=f.sha256) for f in (master,interior)],
        binding=binding,recipe=recipe,recipeHash=signature(recipe),palette=palette,glyphMapping=mapping,baseGlyphCount=len(old_order),outputSha256=hashlib.sha256(data).hexdigest(),
        monochromeFallback='Original base glyf outlines, cmap, advances and shaping tables retained.',
        unsupportedEffects=['bevel lighting','gradient','stroke','shadow','outer glow'],fullFidelityAlternative='publication.export with raster_policy=raster and explicit DPI',
        validation=dict(cmap=True,baseMetrics=True,shapingTables=True,colrVersion=check['COLR'].version),fsType=font['OS/2'].fsType if 'OS/2' in font else None)
    atomic(output,data)
    try: atomic(manifest,json.dumps(report,indent=2,ensure_ascii=True,sort_keys=True).encode()+b'\n')
    except Exception:
        # Never remove user data: only the file just produced by this operation.
        output.unlink();raise
    book.log.emit('fonts','COLOR_FONT_BUILT',path=str(output),sha256=report['outputSha256'],treatment=treatment)
    return dict(path=str(output),manifest=str(manifest),sha256=report['outputSha256'],baseGlyphCount=len(old_order),unsupportedEffects=report['unsupportedEffects'])
