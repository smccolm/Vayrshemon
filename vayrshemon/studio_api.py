"""M4 recipe, proof and publication controls across desktop / API / MCP."""
from copy import deepcopy
from .api import obj,BOOL,STRING
from .typesetting_api import TypesettingAPI,METHODS as M3_METHODS
from .studio_contracts import BINDING,RECIPE_FIELDS,PAINT,FONT
from . import publication

EXPORT_FIELDS=dict(format={'enum':['png','svg','pdf']},mode={'enum':['mono','color']},dpi={'type':'integer','minimum':72,'maximum':600},raster_policy={'enum':['reject','raster']},page_id=STRING)
METHODS=deepcopy(M3_METHODS)
METHODS.update({
 'ui.workspace':('Show or hide source/diagnostics, select a control panel, toggle guides and fit the page for visual review.',True,obj(dict(source=BOOL,diagnostics=BOOL,guides=BOOL,fit_page=BOOL,panel={'enum':['Document','Layout','Text','Color','Typeset','Flow','Breaks','Pairs','Paint','Publish']}))),
 'paint.read':('Read versioned lighting, source bindings, page background and raster settings.',False,obj()),
 'paint.configure':('Change the outline-derived paint recipe and advance its revision; source text is unchanged.',True,obj(RECIPE_FIELDS)),
 'paint.bind':('Bind an exact font identity to verified layer fonts or explicit derived historical treatment.',True,BINDING),
 'publication.configure':('Configure page background (#AARRGGBB) and default raster DPI.',True,obj({k:PAINT['properties'][k] for k in ('background','rasterDpi')})),
 'publication.preflight':('Inspect all pages, font identities, overset, effect clipping and extraction limitations.',False,obj(EXPORT_FIELDS)),
 'publication.export':('Export PNG, SVG or multipage PDF; decorative SVG/PDF requires explicit raster policy and DPI.',True,obj(dict(path=STRING,**EXPORT_FIELDS),('path','format','mode','dpi','raster_policy'))),
 'font.build':('Build the explicitly reduced flat COLR v0/CPAL font plus reproducible provenance manifest; retain mono outlines.',True,obj(dict(font_id=FONT,path=STRING,treatment={'const':'flat-colr-v0'}),('font_id','path','treatment'))),
 'glyph.proof':('Render an isolated painted glyph from its exact font/glyph identity on a chosen background.',True,obj(dict(font_id=FONT,glyph_id={'type':'integer','minimum':0},em={'type':'number','minimum':8,'maximum':1000},dpi={'type':'integer','minimum':72,'maximum':600},background=PAINT['properties']['background'],path=STRING),('font_id','glyph_id','em','dpi','background','path'))),
})


class StudioAPI(TypesettingAPI):
    version='0.5.0'
    methods=METHODS

    def dispatch(self,method,params):
        s=self.session
        if method=='ui.workspace':
            if not s.window: raise ValueError('DESKTOP_REQUIRED')
            return s.window.configure_workspace(**params)
        if method=='ui.inspect':
            value=super().dispatch(method,params)
            if s.window: value['workspace']=s.window.workspace_state()
            return value
        if method=='paint.read': return deepcopy(s.state['paint'])
        if method=='publication.preflight': return publication.preflight(s,**params)
        if method=='publication.export': return publication.export(s,**params)
        if method=='font.build':
            from .colorfont import build
            return build(s,**params)
        if method=='glyph.proof': return self.proof(**params)
        return super().dispatch(method,params)

    def mutate(self,method,params):
        if method=='paint.configure': return self.session.configure_paint(**params)
        if method=='paint.bind': return self.session.bind_paint(**params)
        if method=='publication.configure':
            self.session.state['paint'].update(params);self.session.invalidate_composition();return deepcopy(self.session.state['paint'])
        return super().mutate(method,params)

    def proof(self,font_id,glyph_id,em,dpi,background,path):
        import math
        from PySide6.QtCore import QRectF
        from PySide6.QtGui import QImage,QPainter,QColor
        from . import pages
        s=self.session;r=s.paint_renderer;binding=r.binding(font_id)
        if not binding: raise ValueError('PAINT_BINDING_REQUIRED')
        tile,area=r.tile(binding,glyph_id,em,dpi/96*2)
        if tile is None: raise ValueError('EMPTY_GLYPH')
        scale=dpi/96;image=QImage(math.ceil(area.width()*scale),math.ceil(area.height()*scale),QImage.Format.Format_ARGB32_Premultiplied)
        if image.isNull(): raise ValueError('PROOF_ALLOCATION_FAILED')
        image.fill(QColor(background));p=QPainter(image);p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.drawImage(QRectF(0,0,image.width(),image.height()),tile);p.end()
        target=pages.target(s,path);publication.atomic(target,publication.png_bytes(image))
        return dict(path=str(target),fontId=font_id,glyphId=glyph_id,em=em,dpi=dpi,background=background,bounds=[area.x(),area.y(),area.width(),area.height()],binding=deepcopy(binding),recipeHash=publication.signature(s.state['paint']['recipe']))
