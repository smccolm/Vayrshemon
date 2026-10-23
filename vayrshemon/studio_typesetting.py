"""M4 derives painted extents before collision solving and shares M3 placement."""
from .typesetting import Composition,box,numbers,frame_rect


class StudioComposition(Composition):
    def paint_underlay(self,painter,page_id,visible,outlines):
        if self.mode!='color' or self.book.state['paint']['recipe'].get('lightingModel')!='individual-glyphs-1': return False
        # All glow precedes all ink, including adjacent glyphs and English.
        # Screen blending must see the page, not an opaque black tile.
        renderer=self.book.paint_renderer
        for glyph in self.final:
            if glyph['pageId']!=page_id or not renderer.binding(glyph['fontId']): continue
            if outlines: raise ValueError('PAINT_REQUIRES_RASTER_FALLBACK: use explicit raster policy and DPI')
            frame=self.frames[glyph['frameId']][1]
            clip=visible.intersected(frame_rect(frame)) if frame['overflow']=='clip' else visible
            if glyph['_clip'] is not None: clip=clip.intersected(glyph['_clip'])
            painter.save();painter.setClipRect(clip)
            try: renderer.paint(painter,glyph,component='glow')
            finally: painter.restore()
        return True

    def shape(self,story,enabled):
        super().shape(story,enabled)
        if self.mode!='color': return
        renderer=self.book.paint_renderer
        for glyph in story['glyphs']:
            binding=renderer.binding(glyph['fontId'])
            if not binding: continue
            paths=renderer.paths(binding,glyph['glyphId'],glyph['pixelSize'])
            area=paths[0].boundingRect().united(paths[2].boundingRect())
            if not area.isEmpty(): glyph['inkBounds']=numbers(area.translated(*glyph['origin']))
            glyph['paintBinding']=binding['kind']
            glyph['_paintRegistration']=renderer.registration(binding,glyph['glyphId'],glyph['pixelSize'])
            support=renderer.bounds(binding,glyph['glyphId'],glyph['pixelSize'])
            if not support.isEmpty(): glyph['_paintSupport']=numbers(support)

    def place(self,gaps):
        glyphs,lines,warnings=super().place(gaps)
        for glyph in glyphs:
            if '_paintRegistration' in glyph:
                glyph['paintRegistration']=dict(glyph['_paintRegistration'],layers=[dict(layer,origin=list(glyph['origin']),transform=[1,0,0,1,*glyph['origin']]) for layer in glyph['_paintRegistration']['layers']])
            if '_paintSupport' not in glyph: continue
            area=box(glyph['_paintSupport']).translated(*glyph['origin'])
            glyph['effectBounds']=numbers(area.united(box(glyph['effectBounds'])))
        return glyphs,lines,warnings

    def collision_report(self,page_id=None):
        value=super().collision_report(page_id)
        value['boundsMeaning']['reservedEffectsArePainted']=False
        value['boundsMeaning']['paintEffects']='M4 bindings contribute actual finite paint support; additional M3 reserves are still unpainted'
        value['boundsMeaning']['effect']='union of actual M4 paint support and any manually reserved effect bounds'
        return value
