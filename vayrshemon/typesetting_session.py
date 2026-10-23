"""M3 settings share the existing document writer, undo and recovery journal."""
from copy import deepcopy
from jsonschema import Draft202012Validator
from PySide6.QtGui import QTextBlockUserData
from .session import BLOCK,checked_text
from .authoring import identity
from .authoring import AuthoringSession
from .editor_contracts import EDITOR_DOCUMENT as M2_DOCUMENT
from .typesetting_contracts import STATE,DOCUMENT,initial,settings


class TypesettingSession(AuthoringSession):
    state_schema=STATE
    document_schema=DOCUMENT
    file_version='0.3.0'
    application_version='0.4.0'

    def __init__(self,*args,**kwargs):
        self._composition_cache={}
        super().__init__(*args,**kwargs)
        self.changed.connect(self.invalidate_composition)

    def invalidate_composition(self): self._composition_cache={}

    def fingerprint(self):
        result=super().fingerprint()
        result.update(layout='native source documents + derived QTextLayout stories / M3',typesettingVersion='0.1.0',collisionGeometry='conservative layer-union bounds')
        return result

    def bind_editor(self):
        super().bind_editor()
        if self._editor: self._editor.setReadOnly(self.source_for(self.state['activeFrameId'])!=self.state['activeFrameId'])

    def _restore(self,state):
        self.invalidate_composition()
        super()._restore(state)

    def detach_deleted(self,ids):
        spec=self.state['typesetting']
        spec['frames']={k:v for k,v in spec['frames'].items() if k not in ids}
        spec['flows']=[dict(source=f['source'],targets=[t for t in f['targets'] if t not in ids]) for f in spec['flows'] if f['source'] not in ids]
        spec['flows']=[f for f in spec['flows'] if f['targets']]

    def delete_frame(self,frame_id):
        self.detach_deleted({frame_id})
        return super().delete_frame(frame_id)

    def delete_page(self,page_id):
        self.detach_deleted({f['frameId'] for p in self.state['pages'] if p['pageId']==page_id for f in p['frames']})
        return super().delete_page(page_id)

    def capture(self):
        # QTextBlockUserData adds stable paragraph identities without modifying
        # text/format or emitting recursive contentsChanged signals.
        for native in self.frames.values():
            blocks=[]; block=native.doc.begin()
            while block.isValid(): blocks.append(block); block=block.next()
            reserved={b.userData().identity for b in blocks if b.userData() is not None and hasattr(b.userData(),'identity')}
            for block in blocks:
                if block.userData() is not None and hasattr(block.userData(),'identity'): continue
                proposed=block.blockFormat().property(BLOCK)
                data=QTextBlockUserData(); data.identity=proposed if proposed and proposed not in reserved else identity('block')
                block.setUserData(data); reserved.add(data.identity)
        return super().capture()

    def new_state(self,*args,**kwargs):
        value=super().new_state(*args,**kwargs); value['typesetting']=initial(); return value

    def validate(self,state):
        super().validate(state)
        by_id={f['frameId']:f for p in state['pages'] for f in p['frames']}
        spec=state['typesetting']
        if not set(spec['frames'])<=by_id.keys(): raise ValueError('TYPESETTING_FRAME_MISSING: unlink settings before deleting a frame')
        languages=[p['languageId'] for p in spec['profiles']]
        if len(set(languages))!=len(languages): raise ValueError('DUPLICATE_LINE_BREAK_PROFILE')
        for p in spec['profiles']:
            for key in ('breakAfter','prohibitBefore','prohibitAfter'): checked_text(p[key])
        claimed=set()
        for flow in spec['flows']:
            chain=[flow['source'],*flow['targets']]
            if len(set(chain))!=len(chain) or claimed.intersection(chain): raise ValueError('FLOW_CYCLE_OR_SHARED_FRAME')
            if not set(chain)<=by_id.keys(): raise ValueError('FLOW_FRAME_MISSING: unlink before deletion')
            claimed.update(chain)
            if not spec['frames'].get(flow['source'],{}).get('enabled'): raise ValueError('FLOW_REQUIRES_TYPESETTING')
            for fid in flow['targets']:
                frame=by_id[fid]
                if frame['width']!=by_id[flow['source']]['width']: raise ValueError('M3_FLOW_REQUIRES_EQUAL_WIDTHS')
                blocks=frame['content']['document']['stories'][0]['blocks']
                if len(blocks)>1 or any(r.get('text',r.get('sourceText','')) for b in blocks for r in b['runs']):
                    raise ValueError('FLOW_TARGET_HAS_TEXT: targets must be empty')
        for fid,config in spec['frames'].items():
            ids=[r['blockId'] for r in config['paragraphs']]
            if len(ids)!=len(set(ids)): raise ValueError('DUPLICATE_PARAGRAPH_RULE')
            for rule in config['optical']:
                from .typesetting import boundaries
                for key in ('left','right'):
                    checked_text(rule[key])
                    if len(boundaries(rule[key]))!=2: raise ValueError('OPTICAL_RULE_REQUIRES_ONE_GRAPHEME_PER_SIDE')
                if rule['fontId'] is not None and rule['fontId'] not in {f['fontId'] for f in state['fontSources']}: raise ValueError('OPTICAL_FONT_SOURCE_MISSING')

    def migrate(self,payload,path):
        if payload.get('format')=='vayrshemon.document' and payload.get('formatVersion')==self.file_version:
            Draft202012Validator(DOCUMENT).validate(payload); return deepcopy(payload['state']),False
        if payload.get('format')=='vayrshemon.document':
            Draft202012Validator(M2_DOCUMENT).validate(payload)
            state=deepcopy(payload['state'])
        else:
            state,_=super().migrate(payload,path)
        state['typesetting']=initial()
        return state,True

    def source_for(self,fid):
        return next((f['source'] for f in self.state['typesetting']['flows'] if fid in f['targets']),fid)

    def configure_typesetting(self,frame_id=None,**values):
        fid=frame_id or self.state['activeFrameId']; self.locate(fid)
        if self.source_for(fid)!=fid: raise ValueError('FLOW_TARGET_READ_ONLY: configure its source frame')
        config=self.state['typesetting']['frames'].setdefault(fid,settings())
        for key,value in values.items():
            if key in ('grid','collision'): config[key].update(value)
            else: config[key]=deepcopy(value)
        self.invalidate_composition()
        return dict(frameId=fid,settings=deepcopy(config))

    def set_flow(self,source_frame_id,targets):
        self.locate(source_frame_id)
        spec=self.state['typesetting']
        spec['flows']=[f for f in spec['flows'] if f['source']!=source_frame_id]
        if targets:
            spec['frames'].setdefault(source_frame_id,settings())['enabled']=True
            spec['flows'].append(dict(source=source_frame_id,targets=targets))
        self.invalidate_composition()
        return dict(sourceFrameId=source_frame_id,targets=targets)

    def composition(self,mode=None):
        from .typesetting import Composition
        mode=mode or self.view['mode']
        if mode not in self._composition_cache: self._composition_cache[mode]=Composition(self,mode)
        return self._composition_cache[mode]

    def resolve_fonts(self,state,font_paths=None):
        if 'typesetting' not in state:
            state=deepcopy(state); state['typesetting']=initial()
        return super().resolve_fonts(state,font_paths)
