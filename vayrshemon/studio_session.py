"""Paint is document state: undoable, recoverable and independent of source text."""
from copy import deepcopy
from jsonschema import Draft202012Validator
from .typesetting_session import TypesettingSession
from .typesetting_contracts import DOCUMENT as M3_DOCUMENT
from .editor_contracts import EDITOR_DOCUMENT as M2_DOCUMENT
from .authoring import AuthoringSession
from .typesetting_contracts import initial as typesetting_initial
from .studio_contracts import STATE,DOCUMENT
from .paint import initial,Renderer,VERSION,ENGINE_VERSION
from . import __version__


class StudioSession(TypesettingSession):
    state_schema=STATE
    document_schema=DOCUMENT
    file_version='0.4.0'
    application_version=__version__

    def __init__(self,*args,**kwargs):
        self.paint_renderer=Renderer(self)
        super().__init__(*args,**kwargs)

    def new_state(self,*args,**kwargs):
        state=super().new_state(*args,**kwargs);state['paint']=initial();return state

    def fingerprint(self):
        value=super().fingerprint();value.update(paintVersion=VERSION,paintEngineVersion=ENGINE_VERSION,paintEngine='outline distance fields / NumPy 2.2.6 / SciPy 1.15.3',colorSpace='sRGB display proof; no CMYK/ICC conversion')
        return value

    def migrate(self,payload,path):
        version=payload.get('formatVersion')
        if payload.get('format')=='vayrshemon.document':
            if version==self.file_version:
                Draft202012Validator(DOCUMENT).validate(payload);return deepcopy(payload['state']),False
            if version in ('0.2.0','0.3.0'):
                Draft202012Validator(M3_DOCUMENT if version=='0.3.0' else M2_DOCUMENT).validate(payload)
                state=deepcopy(payload['state'])
            else: raise ValueError('UNSUPPORTED_DOCUMENT_VERSION')
        else: state,_=AuthoringSession.migrate(self,payload,path)
        state.setdefault('typesetting',typesetting_initial());state['paint']=initial();return state,True

    def validate(self,state):
        super().validate(state)
        bindings=state['paint']['bindings'];ids=[b['fontId'] for b in bindings]
        if len(ids)!=len(set(ids)): raise ValueError('DUPLICATE_PAINT_BINDING')
        declared={f['fontId'] for f in state['fontSources']}
        for binding in bindings:
            if not {binding[k] for k in ('fontId','glowFontId','interiorFontId') if k in binding}<=declared:
                raise ValueError('PAINT_FONT_SOURCE_MISSING')

    def validate_binding(self,binding):
        master=self.fonts.resolve(binding['fontId'])
        if binding['kind']=='layered':
            for key in ('glowFontId','interiorFontId'):
                layer=self.fonts.resolve(binding[key])
                if master.units_per_em!=layer.units_per_em or set(master.glyph_order)!=set(layer.glyph_order): raise ValueError('PAINT_LAYER_GLYPH_MISMATCH')
                if master.cmap!=layer.cmap: raise ValueError('PAINT_LAYER_CMAP_MISMATCH')
                if any(master.metrics[name][0]!=layer.metrics[name][0] for name in master.glyph_order): raise ValueError('PAINT_LAYER_ADVANCE_MISMATCH')

    def resolve_fonts(self,state,font_paths=None):
        state=super().resolve_fonts(state,font_paths)
        for binding in state['paint']['bindings']: self.validate_binding(binding)
        return state

    def configure_paint(self,**values):
        recipe=self.state['paint']['recipe'];recipe.update(values);recipe['revision']+=1
        self.invalidate_composition();return deepcopy(recipe)

    def bind_paint(self,**binding):
        self.validate_binding(binding)
        self.state['paint']['bindings']=[b for b in self.state['paint']['bindings'] if b['fontId']!=binding['fontId']]+[deepcopy(binding)]
        self.invalidate_composition();return deepcopy(binding)

    def composition(self,mode=None):
        from .studio_typesetting import StudioComposition
        mode=mode or self.view['mode']
        if mode not in self._composition_cache: self._composition_cache[mode]=StudioComposition(self,mode)
        return self._composition_cache[mode]
