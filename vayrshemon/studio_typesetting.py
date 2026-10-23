"""M4 derives painted extents before collision solving and shares M3 placement."""
from .typesetting import Composition,box,numbers
from .paint import padding


class StudioComposition(Composition):
    def shape(self,story,enabled):
        super().shape(story,enabled)
        if self.mode!='color': return
        renderer=self.book.paint_renderer
        for glyph in story['glyphs']:
            binding=renderer.binding(glyph['fontId'])
            if not binding: continue
            paths=renderer.paths(binding,glyph['glyphId'],glyph['pixelSize'])
            area=paths[0].boundingRect().united(paths[2].boundingRect())
            if area.isEmpty(): continue
            glyph['inkBounds']=numbers(area.translated(*glyph['origin']))
            glyph['paintBinding']=binding['kind']
            glyph['_paintPadding']=padding(self.book.state['paint']['recipe'],glyph['pixelSize'])

    def place(self,gaps):
        glyphs,lines,warnings=super().place(gaps)
        for glyph in glyphs:
            if '_paintPadding' not in glyph: continue
            pad=glyph['_paintPadding']; area=box(glyph['inkBounds']).adjusted(-pad,-pad,pad,pad)
            glyph['effectBounds']=numbers(area.united(box(glyph['effectBounds'])))
        return glyphs,lines,warnings

    def collision_report(self,page_id=None):
        value=super().collision_report(page_id)
        value['boundsMeaning']['reservedEffectsArePainted']=False
        value['boundsMeaning']['paintEffects']='M4 bindings contribute actual finite paint support; additional M3 reserves are still unpainted'
        value['boundsMeaning']['effect']='union of actual M4 paint support and any manually reserved effect bounds'
        return value
