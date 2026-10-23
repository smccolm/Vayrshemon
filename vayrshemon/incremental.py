"""Bounded, owner-thread Qt shaping reuse. Placement remains a page operation."""
from collections import OrderedDict
from .typesetting import hash_value,MAX_GLYPHS


class StoryCache:
    max_entries=64
    max_glyphs=20000
    max_lines=10000

    def __init__(self):
        self.entries=OrderedDict();self.hits=0;self.misses=0;self.evictions=0

    def clear(self): self.entries.clear()

    def info(self):
        return dict(entries=len(self.entries),glyphs=sum(len(e['story']['glyphs']) for e in self.entries.values()),
            lines=sum(len(e['story']['lines']) for e in self.entries.values()),hits=self.hits,misses=self.misses,evictions=self.evictions,
            limits=dict(entries=self.max_entries,glyphs=self.max_glyphs,lines=self.max_lines),scope='shaping; placement and collisions recompute for affected page/flow component')

    def shape(self,comp,story,enabled):
        native=story['native'];fid=story['source']
        key=(fid,comp.mode)
        signature=(id(native),native.doc.revision(),hash_value([comp.frames[fid][1]['width'],story['config'],
            comp.profiles,comp.book.features,comp.book.fonts.recipe,comp.book.state.get('paint'),native.model['styles']]))
        old=self.entries.pop(key,None)
        if old and old['signature']==signature:
            self.hits+=1
            chain=story['chain'];story.update(old['story']);story['chain']=chain
            comp.layouts.extend(old['layouts']);comp.optical.extend(old['optical']);comp.warnings.extend(old['warnings'])
            comp.glyph_count+=len(story['glyphs'])
            self.entries[key]=old
        else:
            self.misses+=1
            start=(len(comp.layouts),len(comp.optical),len(comp.warnings))
            comp.shape(story,enabled)
            self.entries[key]=dict(signature=signature,story=dict(story),layouts=comp.layouts[start[0]:],optical=comp.optical[start[1]:],warnings=comp.warnings[start[2]:])
        if comp.glyph_count>MAX_GLYPHS: raise ValueError('TYPESETTING_GLYPH_LIMIT: 20,000 positioned glyphs per page/linked component')
        while self.entries:
            info=self.info()
            if info['entries']<=self.max_entries and info['glyphs']<=self.max_glyphs and info['lines']<=self.max_lines: break
            self.entries.popitem(last=False);self.evictions+=1
