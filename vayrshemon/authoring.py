"""M2 document writer: independent frames, complete undo, durable recovery, migrations."""
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import uuid

from jsonschema import Draft202012Validator
from PySide6.QtCore import QObject, Signal, QLockFile
from PySide6.QtGui import QTextCursor, QTextDocumentFragment

from tools.m0.common import load_json, write_json, json_text
from tools.m0.synthetic import document, unicode_run
from .diagnostics import Diagnostics
from .fonts import FontRegistry
from .frame import FrameSession
from .session import Session, checked_text, micro_points, scalar_offset, utf16_length, SCALE, STYLE
from .editor_contracts import EDITOR_DOCUMENT, PACKAGE, STATE, FONT_SOURCE
from tools.m0.contracts import validators,validate_document_semantics

MIME = 'application/vnd.vayrshemon.fragment+json'
HISTORY_LIMIT = 80
HISTORY_BYTES = 64*1024*1024


def identity(prefix): return prefix+'.'+uuid.uuid4().hex
def stamp(): return datetime.now(timezone.utc).isoformat()
def digest(value): return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=True,allow_nan=False).encode()).hexdigest()
def point(value): return int(value)/1_000_000
def nonnegative(value):
    if value == 0: return '0'
    return micro_points(value)


def blank_content(document_id,width,height,text=''):
    value=document(document_id,[unicode_run(checked_text(text))])
    value['layoutProfile']='layout.qt-6.8.3-m2'
    value['pages'][0].update(widthMicroPoints=width,heightMicroPoints=height,marginsMicroPoints={s:'0' for s in ('top','right','bottom','left')})
    value['pages'][0]['frames'][0].update(xMicroPoints='0',yMicroPoints='0',widthMicroPoints=width,heightMicroPoints=height)
    return dict(document=value,styleFeatures={},characters=[],paragraphs=[])


class AuthoringSession(QObject):
    changed = Signal()
    state_schema=STATE
    document_schema=EDITOR_DOCUMENT
    file_version='0.2.0'
    application_version='0.3.0'

    def __init__(self,root,*,source_fonts=True,recovery=True):
        super().__init__()
        self.root=Path(root).resolve()
        self.session_id=identity('editor')
        self.log=Diagnostics(self.root,self.session_id)
        self.fonts=FontRegistry(self.root,self.log)
        self.checks=validators(self.root)
        self.frames={}
        self.window=None
        self._editor=None
        self._depth=0
        self._restoring=False
        self._pending=False
        self._undo=[]
        self._redo=[]
        self.history=[]
        self.revision=0
        self.saved_path=None
        self.saved_hash=None
        self.saved_revision=None
        self._saved_digest=None
        self.migrated_from=None
        self.durable_revision=-1
        self.recovery_error=None
        self.recovery_enabled=recovery
        self.recovery_path=self.root/'.local/recovery'/(self.session_id+'.json')
        self.recovery_path.parent.mkdir(parents=True,exist_ok=True)
        self.lock=QLockFile(str(self.recovery_path.with_suffix('.lock')))
        self.lock.setStaleLockTime(0)
        if recovery and not self.lock.tryLock(0): raise OSError('RECOVERY_LOCK_FAILED')
        if source_fonts and (self.root/'Inputs/font files/Thimfora_79.ttf').exists(): self.fonts.load_source_recipe()
        self.state=self.new_state()
        self._restore(self.state)
        self._state=self.capture()
        self._saved_digest=self.content_digest(self._state)
        self.checkpoint()
        self.log.emit('editor','SESSION_STARTED',revision=self.revision,engine=self.fingerprint())

    def __getattr__(self,name):
        # The M1 text/layout adapter operates on the selected frame only.
        if name.startswith('__'): raise AttributeError(name)
        frames=self.__dict__.get('frames',{})
        state=self.__dict__.get('state',{})
        active=frames.get(state.get('activeFrameId'))
        if active is not None: return getattr(active,name)
        raise AttributeError(name)

    @property
    def active(self): return self.frames[self.state['activeFrameId']]
    @property
    def model(self): return self.active.model
    @model.setter
    def model(self,value): self.active.model=value
    @property
    def view(self): return self.state['view']
    @property
    def features(self): return self.state['features']
    @property
    def editor(self): return self._editor
    @property
    def composing(self): return any(frame.composing for frame in self.frames.values())
    @property
    def dirty(self): return self._saved_digest != self.content_digest(self.capture())

    def fingerprint(self):
        result=self.active.fingerprint()
        result.update(application=self.application_version,formatVersion=self.file_version,layout='one QTextDocument/QTextLayout per independent frame')
        return result

    def new_state(self,title='Untitled',width=612,height=792):
        did=identity('document')
        page=self.make_page(did,width,height)
        return dict(documentId=did,title=title,revision=self.revision,pages=[page],activeFrameId=page['frames'][0]['frameId'],
                    fontSources=self.font_sources(),recipe=deepcopy(self.fonts.recipe),features={'kern':True,'liga':True},
                    view=dict(mode='color',baselines=False,origins=False,bounds=False,zoom=.8),styles=[])

    def make_page(self,did,width,height):
        w,h=micro_points(width),micro_points(height)
        if min(int(w),int(h)) <= 36_000_000: raise ValueError('PAGE_TOO_SMALL_FOR_DEFAULT_MARGINS')
        fw,fh=str(int(w)-36_000_000),str(int(h)-36_000_000)
        frame=dict(frameId=identity('frame'),name='Body',x='18000000',y='18000000',width=fw,height=fh,overflow='show',content=blank_content(did,fw,fh))
        return dict(pageId=identity('page'),name='Page',width=w,height=h,margins={s:'18000000' for s in ('top','right','bottom','left')},frames=[frame])

    def font_sources(self): return [dict(fontId=f.font_id,sha256=f.sha256,path=str(f.path)) for f in self.fonts.faces.values()]

    def current_page(self):
        return next(page for page in self.state['pages'] if any(f['frameId']==self.state['activeFrameId'] for f in page['frames']))

    def locate(self,frame_id=None):
        frame_id=frame_id or self.state['activeFrameId']
        for page in self.state['pages']:
            for frame in page['frames']:
                if frame['frameId']==frame_id: return page,frame
        raise ValueError('FRAME_NOT_FOUND')

    def capture(self):
        result=deepcopy(self.state)
        result['revision']=self.revision
        result['recipe']=deepcopy(self.fonts.recipe)
        # Runtime font caches may retain undo/deleted fonts, but files contain
        # only the catalog owned by this document revision.
        result['fontSources']=[dict(source,path=str(self.fonts.faces[source['fontId']].path)) for source in self.state['fontSources']]
        for page in result['pages']:
            for frame in page['frames']:
                if frame['frameId'] in self.frames:
                    frame['content']=self.frames[frame['frameId']].package()
                    frame['content']['document']['documentId']=result['documentId']
                    frame['content']['document']['revision']=0  # Global revision is the sole writer clock.
        required={f['fontId'] for p in result['pages'] for frame in p['frames'] for f in frame['content']['document']['fonts']}
        required.update(s['format']['font_id'] for s in result['styles'] if s['format'].get('font_id'))
        if result['recipe']:
            required.add(result['recipe']['master']); required.update(layer['fontId'] for layer in result['recipe']['layers'])
        declared={source['fontId'] for source in result['fontSources']}
        result['fontSources'].extend(dict(fontId=fid,sha256=self.fonts.faces[fid].sha256,path=str(self.fonts.faces[fid].path)) for fid in sorted(required-declared))
        return result

    @staticmethod
    def content_digest(state):
        value=deepcopy(state)
        value.pop('revision',None)
        value.pop('activeFrameId',None)
        return digest(value)

    def validate(self,state):
        if len(json_text(state).encode('utf-8'))>8*1024*1024: raise ValueError('DOCUMENT_STATE_LIMIT: 8 MiB')
        Draft202012Validator(self.state_schema).validate(state)
        ids=set(); frame_ids=set()
        total=0
        count=0
        for page in state['pages']:
            if page['pageId'] in ids: raise ValueError('DUPLICATE_PAGE_ID')
            ids.add(page['pageId'])
            for field in ('width','height'): micro_points(point(page[field]))
            margins={k:int(v) for k,v in page['margins'].items()}
            if margins['left']+margins['right']>=int(page['width']) or margins['top']+margins['bottom']>=int(page['height']):
                raise ValueError('PAGE_MARGINS_LEAVE_NO_CONTENT')
            for frame in page['frames']:
                count+=1
                if frame['frameId'] in ids: raise ValueError('DUPLICATE_FRAME_ID')
                ids.add(frame['frameId'])
                frame_ids.add(frame['frameId'])
                if int(frame['x'])+int(frame['width'])>int(page['width']) or int(frame['y'])+int(frame['height'])>int(page['height']):
                    raise ValueError('FRAME_OUTSIDE_PAGE')
                content=frame['content']; model=content['document']
                # Reuse the M0 schema and M1 one-story preservation constraints.
                validator=self.frames[next(iter(self.frames))] if self.frames else None
                if validator: validator.validate_model(model)
                else:
                    self.checks['document'].validate(model)
                    errors=validate_document_semantics(model)
                    if errors: raise ValueError(str(errors))
                if len(model['pages'])!=1 or len(model['stories'])!=1: raise ValueError('ONE_STORY_PER_FRAME_REQUIRED')
                mp=model['pages'][0]
                if mp['widthMicroPoints']!=frame['width'] or mp['heightMicroPoints']!=frame['height'] or any(int(v) for v in mp['marginsMicroPoints'].values()):
                    raise ValueError('FRAME_LAYOUT_DIMENSION_MISMATCH')
                if model['documentId']!=state['documentId']: raise ValueError('FRAME_DOCUMENT_ID_MISMATCH')
                text='\n'.join(''.join(run.get('text',run.get('sourceText','')) for run in b['runs']) for b in model['stories'][0]['blocks'])
                checked_text(text); total+=len(text)
                if content['paragraphs'] and len(content['paragraphs'])!=len(model['stories'][0]['blocks']): raise ValueError('PARAGRAPH_COUNT_MISMATCH')
                previous_end=0
                for char in content['characters']:
                    if char['start']<previous_end or char['end']<char['start']: raise ValueError('OVERLAPPING_CHARACTER_ATTRIBUTES')
                    scalar_offset(text,char['start']); scalar_offset(text,char['end']); previous_end=char['end']
        if count>128 or total>200_000: raise ValueError('DOCUMENT_LIMIT: 128 frames and 200,000 total scalars')
        if state['activeFrameId'] not in frame_ids: raise ValueError('ACTIVE_FRAME_MISSING')
        if len({s['name'].casefold() for s in state['styles']})!=len(state['styles']): raise ValueError('DUPLICATE_STYLE_NAME')
        declared={f['fontId'] for f in state['fontSources']}
        required={f['fontId'] for p in state['pages'] for frame in p['frames'] for f in frame['content']['document']['fonts']}
        required.update(s['format']['font_id'] for s in state['styles'] if s['format'].get('font_id'))
        if state['recipe']:
            required.add(state['recipe']['master']); required.update(layer['fontId'] for layer in state['recipe']['layers'])
        if not required<=declared: raise ValueError('FONT_SOURCE_MISSING')

    def _restore(self,state):
        self.validate(state)
        previous=self.frames
        prepared={}
        try:
            for page in state['pages']:
                for frame in page['frames']:
                    runtime=FrameSession(self.root,self.fonts,frame['content'],self.checks,state['features'])
                    runtime.owner=self
                    prepared[frame['frameId']]=runtime
        except Exception:
            for frame in prepared.values(): frame.deleteLater()
            raise
        self._restoring=True
        try:
            self.state=deepcopy(state)
            self.fonts.recipe=deepcopy(state['recipe'])
            self.frames=prepared
            for frame in self.frames.values(): frame.changed.connect(self.frame_changed)
            self.bind_editor()
            for old in previous.values():
                old.editor=None
                old.deleteLater()
        finally: self._restoring=False

    def bind_editor(self):
        if self._editor:
            for frame in self.frames.values(): frame.editor=None
            self._editor.session=self.active
            self._editor.setDocument(self.active.doc)
            self.active.editor=self._editor
            self.active.configure_layout()

    def frame_changed(self):
        if self._restoring: return
        if self._depth:
            self._pending=True
            return
        self.commit('Typing or text formatting')

    def _contents_changed(self): self.frame_changed()

    @contextmanager
    def command(self,label):
        before=self.capture()
        selection=self.selection()
        self._depth+=1
        try:
            yield
            self.validate(self.capture())
        except Exception:
            self._restore(before)
            self.restore_selection(selection)
            self.changed.emit()
            raise
        finally:
            self._depth-=1
            self._pending=False
        if not self._depth: self.commit(label)

    def commit(self,label):
        current=self.capture()
        if current==self._state: return
        self._undo.append(deepcopy(self._state))
        self._redo.clear()
        while len(self._undo)>HISTORY_LIMIT or sum(len(json.dumps(s)) for s in self._undo)>HISTORY_BYTES:
            self._undo.pop(0)
        self.revision+=1
        current['revision']=self.revision
        self.state['revision']=self.revision
        self._state=current
        self.history.append(dict(revision=self.revision,label=label,timestamp=stamp(),sha256=self.content_digest(current)))
        self.history=self.history[-256:]
        self.checkpoint()
        self.log.emit('document','REVISION_COMMITTED',revision=self.revision,label=label,durableRevision=self.durable_revision)
        self.changed.emit()

    def history_move(self,redo=False):
        source,target=(self._redo,self._undo) if redo else (self._undo,self._redo)
        if not source: return dict(changed=False)
        next_state=source[-1]
        current=self.capture()
        self._restore(next_state)
        source.pop(); target.append(current)
        self.revision+=1
        self.state['revision']=self.revision
        self._state=self.capture()
        self.history.append(dict(revision=self.revision,label='Redo' if redo else 'Undo',timestamp=stamp(),sha256=self.content_digest(self._state)))
        self.history=self.history[-256:]
        self.checkpoint(); self.changed.emit()
        return dict(revision=self.revision,undoAvailable=bool(self._undo),redoAvailable=bool(self._redo))

    def selection(self):
        if not self.editor: return None
        c=self.editor.textCursor()
        return dict(frameId=self.state['activeFrameId'],start=c.selectionStart(),end=c.selectionEnd())

    def restore_selection(self,value):
        if value and self.editor and value['frameId']==self.state['activeFrameId']:
            end=min(value['end'],utf16_length(self.text()))
            self.editor.setTextCursor(self.active.range_cursor(min(value['start'],end),end,grapheme=False))

    def checkpoint(self,*,closed=False):
        if not self.recovery_enabled: return
        state=self.capture()
        entry=dict(recoveryVersion='0.1.0',sessionId=self.session_id,timestamp=stamp(),closed=closed,
                   state=state,sha256=digest(state),history=self.history[-256:],
                   savedPath=str(self.saved_path) if self.saved_path else None,savedHash=self.saved_hash,
                   savedDigest=self._saved_digest,migratedFrom=self.migrated_from)
        try:
            write_json(self.recovery_path,entry)
            self.durable_revision=self.revision
            self.recovery_error=None
        except Exception as error:
            self.recovery_error=str(error)
            self.log.exception('recovery',error)

    def recovery_list(self):
        results=[]
        for path in sorted((self.root/'.local/recovery').glob('editor.*.json')):
            if path==self.recovery_path: continue
            lock=QLockFile(str(path.with_suffix('.lock'))); lock.setStaleLockTime(0)
            if not lock.tryLock(0): continue
            lock.unlock()
            try:
                if path.stat().st_size>16*1024*1024: raise ValueError('RECOVERY_TOO_LARGE')
                value=load_json(path)
                if value.get('recoveryVersion')!='0.1.0': raise ValueError('UNSUPPORTED_RECOVERY_VERSION')
                if value.get('closed'): continue
                if digest(value['state'])!=value['sha256']: raise ValueError('RECOVERY_HASH_MISMATCH')
                if value.get('savedDigest')==self.content_digest(value['state']): continue
                results.append(dict(path=str(path),title=value['state']['title'],revision=value['state']['revision'],timestamp=value['timestamp']))
            except Exception as error:
                results.append(dict(path=str(path),error=str(error)))
        return results

    def recover(self,path,font_paths=None):
        path=Path(path).resolve()
        if path.parent!=self.recovery_path.parent: raise ValueError('RECOVERY_PATH_OUTSIDE_STORE')
        lock=QLockFile(str(path.with_suffix('.lock'))); lock.setStaleLockTime(0)
        if not lock.tryLock(0): raise ValueError('RECOVERY_SESSION_STILL_RUNNING')
        try:
            if path.stat().st_size>16*1024*1024: raise ValueError('RECOVERY_TOO_LARGE')
            entry=load_json(path)
            if entry.get('recoveryVersion')!='0.1.0': raise ValueError('UNSUPPORTED_RECOVERY_VERSION')
            if digest(entry['state'])!=entry['sha256']: raise ValueError('RECOVERY_HASH_MISMATCH')
            state=self.resolve_fonts(entry['state'],font_paths)
            self._restore(state)
            self.revision=max(self.revision,state['revision'])+1
            self.saved_path=Path(entry['savedPath']) if entry.get('savedPath') else None
            self.saved_hash=entry.get('savedHash'); self._saved_digest=entry.get('savedDigest')
            self.migrated_from=entry.get('migratedFrom')
            self.history=entry.get('history',[])[-256:]
            self._undo=[]; self._redo=[]; self._state=self.capture()
            self.checkpoint()
            if self.recovery_error: raise OSError(self.recovery_error)
            entry['closed']=True
            write_json(path,entry)
            self.changed.emit()
            return dict(recoveredRevision=state['revision'],revision=self.revision,savedPath=str(self.saved_path) if self.saved_path else None)
        finally: lock.unlock()

    def finish(self):
        try: self.checkpoint(closed=True)
        finally: self.lock.unlock()

    def output_path(self,path): return self.active.output_path(path)

    def save(self,path):
        path=self.output_path(path)
        if self.migrated_from and path==Path(self.migrated_from): raise ValueError('MIGRATION_REQUIRES_NEW_PATH: retain the original file')
        if path.exists():
            if path!=self.saved_path: raise ValueError('SAVE_AS_TARGET_EXISTS')
            if hashlib.sha256(path.read_bytes()).hexdigest()!=self.saved_hash: raise ValueError('DOCUMENT_CHANGED_ON_DISK')
        state=self.capture(); self.validate(state)
        self.resolve_fonts(state)
        payload=dict(format='vayrshemon.document',formatVersion=self.file_version,state=state,history=self.history[-256:],engine=self.fingerprint())
        Draft202012Validator(self.document_schema).validate(payload)
        if len(json_text(payload).encode('utf-8'))>16*1024*1024: raise ValueError('DOCUMENT_TOO_LARGE')
        if path.exists():
            prior=load_json(path)
            backup=self.root/'.local/history'/self.state['documentId']/(self.saved_hash+'.vay.json')
            if not backup.exists(): write_json(backup,prior)
        write_json(path,payload)
        self.saved_path=path; self.saved_hash=hashlib.sha256(path.read_bytes()).hexdigest()
        self.saved_revision=self.revision; self._saved_digest=self.content_digest(state)
        self.checkpoint(); self.remember(path); self.changed.emit()
        self.log.emit('persistence','DOCUMENT_SAVED',path=str(path),revision=self.revision,sha256=self.saved_hash)
        return dict(path=str(path),sha256=self.saved_hash,revision=self.revision)

    def recent(self):
        path=self.root/'.local/recent.json'
        return load_json(path) if path.exists() else []

    def remember(self,path):
        entries=[e for e in self.recent() if e['path']!=str(path)]
        write_json(self.root/'.local/recent.json',[dict(path=str(path),title=self.state['title'],openedAt=stamp())]+entries[:19])

    def migrate(self,payload,path):
        if payload.get('format')=='vayrshemon.document':
            Draft202012Validator(EDITOR_DOCUMENT).validate(payload)
            return deepcopy(payload['state']),False
        from .contracts import LAB_DOCUMENT
        Draft202012Validator(LAB_DOCUMENT).validate(payload)
        model=deepcopy(payload['document']); page=model['pages'][0]
        self.active.validate_model(model)
        old_frame=page['frames'][0]; lab=payload['lab']
        outer=dict(pageId=page['pageId'],name='Imported M1 page',width=page['widthMicroPoints'],height=page['heightMicroPoints'],
                   margins=deepcopy(page['marginsMicroPoints']),frames=[])
        width,height=old_frame['widthMicroPoints'],old_frame['heightMicroPoints']
        x,y=old_frame['xMicroPoints'],old_frame['yMicroPoints']
        page.update(widthMicroPoints=width,heightMicroPoints=height,marginsMicroPoints={s:'0' for s in ('top','right','bottom','left')})
        old_frame.update(xMicroPoints='0',yMicroPoints='0',widthMicroPoints=width,heightMicroPoints=height)
        frame=dict(frameId=identity('frame'),name='Imported body',x=x,y=y,width=width,height=height,overflow='show',
                   content=dict(document=model,styleFeatures=lab['styleFeatures'],characters=[],paragraphs=[]))
        outer['frames'].append(frame)
        state=dict(documentId=model['documentId'],title=model['title'],revision=model['revision'],pages=[outer],activeFrameId=frame['frameId'],
                   fontSources=lab['fontSources'],recipe=lab['recipe'],features=lab['features'],view=lab['view'],styles=[])
        return state,True

    def read_file(self,path):
        path=Path(path).resolve(strict=True)
        if path.stat().st_size>16*1024*1024: raise ValueError('DOCUMENT_TOO_LARGE')
        payload=load_json(path)
        state,migrated=self.migrate(payload,path)
        self.validate(state)
        return path,payload,state,migrated

    def preflight(self,path):
        path,payload,state,migrated=self.read_file(path)
        missing=[]
        for source in state['fontSources']:
            candidate=Path(source['path'])
            try: found=candidate.is_file() and candidate.stat().st_size<=64*1024*1024 and hashlib.sha256(candidate.read_bytes()).hexdigest()==source['sha256']
            except OSError: found=False
            if not found: missing.append(source)
        return dict(path=str(path),migrationRequired=migrated,missingFonts=missing,title=state['title'],pages=len(state['pages']))

    def resolve_fonts(self,state,font_paths=None):
        state=deepcopy(state)
        self.validate(state)
        missing=[]
        for source in state['fontSources']:
            source['path']=(font_paths or {}).get(source['fontId'],source['path'])
            if source['fontId']!='font:'+source['sha256']+':0': raise ValueError('FONT_ID_HASH_MISMATCH')
            try: self.fonts.register(source['path'],source['sha256'])
            except (OSError,ValueError) as error: missing.append(dict(**source,reason=str(error)))
        if missing: raise ValueError('MISSING_FONTS: '+json.dumps(missing))
        for page in state['pages']:
            for frame in page['frames']:
                for font in frame['content']['document']['fonts']: self.fonts.resolve(font['fontId'])
        recipe=state['recipe']
        if recipe:
            expected=self.fonts.recipe_for(self.fonts.resolve(recipe['master']),[self.fonts.resolve(layer['fontId']) for layer in recipe['layers']])
            if any(a['glyphMap']!=b['glyphMap'] for a,b in zip(expected['layers'],recipe['layers'])): raise ValueError('INVALID_COLOR_RECIPE')
        return state

    def open(self,path,*,font_paths=None,advance_revision=True):
        path,payload,state,migrated=self.read_file(path)
        state=self.resolve_fonts(state,font_paths)
        self._restore(state)
        self.revision=max(self.revision,state['revision'])+1 if advance_revision else state['revision']
        self.saved_path=None if migrated else path
        self.saved_hash=None if migrated else hashlib.sha256(path.read_bytes()).hexdigest()
        self.saved_revision=None if migrated else self.revision
        self.migrated_from=str(path) if migrated else None
        self._saved_digest=None if migrated else self.content_digest(self.capture())
        self._undo=[]; self._redo=[]; self.history=payload.get('history',[])[-256:]
        self._state=self.capture(); self.checkpoint(); self.remember(path); self.changed.emit()
        self.log.emit('persistence','DOCUMENT_OPENED',path=str(path),revision=self.revision,migrated=migrated)
        return dict(path=str(path),revision=self.revision,migrated=migrated)

    def new(self,title='Untitled',width=612,height=792):
        self._restore(self.new_state(title,width,height))
        self.revision+=1
        self.saved_path=None; self.saved_hash=None; self.saved_revision=None; self._saved_digest=None; self.migrated_from=None
        self._undo=[]; self._redo=[]; self.history=[]
        self._state=self.capture(); self._saved_digest=self.content_digest(self._state); self.checkpoint(); self.changed.emit()
        return dict(documentId=self.state['documentId'],revision=self.revision)

    def select_frame(self,frame_id):
        self.locate(frame_id)
        self.state['activeFrameId']=frame_id
        self.bind_editor()
        return dict(frameId=frame_id,pageId=self.current_page()['pageId'])

    def add_page(self,width=612,height=792):
        state=self.capture(); page=self.make_page(state['documentId'],width,height)
        page['name']='Page '+str(len(state['pages'])+1)
        state['pages'].append(page); state['activeFrameId']=page['frames'][0]['frameId']
        self._restore(state)
        return dict(pageId=page['pageId'],frameId=state['activeFrameId'])

    def delete_page(self,page_id):
        state=self.capture()
        if len(state['pages'])==1: raise ValueError('CANNOT_DELETE_LAST_PAGE')
        matches=[p for p in state['pages'] if p['pageId']==page_id]
        if not matches: raise ValueError('PAGE_NOT_FOUND')
        state['pages']=[p for p in state['pages'] if p['pageId']!=page_id]
        if any(f['frameId']==state['activeFrameId'] for f in matches[0]['frames']): state['activeFrameId']=state['pages'][0]['frames'][0]['frameId']
        self._restore(state)
        return dict(pageId=page_id)

    def configure_page(self,width=None,height=None,unit='pt',margins=None,page_id=None):
        state=self.capture()
        page_id=page_id or self.current_page()['pageId']
        page=next((p for p in state['pages'] if p['pageId']==page_id),None)
        if page is None: raise ValueError('PAGE_NOT_FOUND')
        previous=deepcopy(page)
        if width is not None: page['width']=micro_points(width,unit)
        if height is not None: page['height']=micro_points(height,unit)
        if margins is not None: page['margins']={k:nonnegative(v) if unit=='pt' else ('0' if v==0 else micro_points(v,unit)) for k,v in margins.items()}
        # A frame exactly matching the old content area follows new margins/size.
        for frame in page['frames']:
            if (int(frame['x'])==int(previous['margins']['left']) and int(frame['y'])==int(previous['margins']['top']) and
                int(frame['width'])==int(previous['width'])-int(previous['margins']['left'])-int(previous['margins']['right']) and
                int(frame['height'])==int(previous['height'])-int(previous['margins']['top'])-int(previous['margins']['bottom'])):
                frame.update(x=page['margins']['left'],y=page['margins']['top'],
                             width=str(int(page['width'])-int(page['margins']['left'])-int(page['margins']['right'])),
                             height=str(int(page['height'])-int(page['margins']['top'])-int(page['margins']['bottom'])))
                self.resize_content(frame)
        self._restore(state)
        return dict(pageId=page_id)

    @staticmethod
    def resize_content(frame):
        page=frame['content']['document']['pages'][0]
        page.update(widthMicroPoints=frame['width'],heightMicroPoints=frame['height'])
        page['frames'][0].update(widthMicroPoints=frame['width'],heightMicroPoints=frame['height'])

    def add_frame(self,x=36,y=36,width=200,height=100,name='Text frame'):
        state=self.capture(); page=next(p for p in state['pages'] if p['pageId']==self.current_page()['pageId'])
        w,h=micro_points(width),micro_points(height)
        frame=dict(frameId=identity('frame'),name=name,x=nonnegative(x),y=nonnegative(y),width=w,height=h,overflow='show',content=blank_content(state['documentId'],w,h))
        page['frames'].append(frame); state['activeFrameId']=frame['frameId']
        self._restore(state)
        return dict(frameId=frame['frameId'])

    def configure_frame(self,frame_id=None,**values):
        state=self.capture(); frame_id=frame_id or state['activeFrameId']
        frame=next((f for p in state['pages'] for f in p['frames'] if f['frameId']==frame_id),None)
        if frame is None: raise ValueError('FRAME_NOT_FOUND')
        for k,v in values.items(): frame[k]=nonnegative(v) if k in ('x','y') else micro_points(v) if k in ('width','height') else v
        self.resize_content(frame); self._restore(state)
        return dict(frameId=frame_id)

    def delete_frame(self,frame_id):
        state=self.capture()
        page,original=self.locate(frame_id)
        if len(page['frames'])==1: raise ValueError('CANNOT_DELETE_LAST_FRAME_ON_PAGE')
        page=next(p for p in state['pages'] if p['pageId']==page['pageId'])
        page['frames']=[f for f in page['frames'] if f['frameId']!=frame_id]
        if state['activeFrameId']==frame_id: state['activeFrameId']=page['frames'][0]['frameId']
        self._restore(state)
        return dict(frameId=frame_id)

    def find(self,text,case_sensitive=False,whole_word=False,all_frames=True):
        if not text: raise ValueError('EMPTY_SEARCH')
        pattern=re.escape(text)
        if whole_word: pattern=r'(?<!\w)'+pattern+r'(?!\w)'
        regex=re.compile(pattern,0 if case_sensitive else re.IGNORECASE)
        result=[]
        for fid,frame in self.frames.items():
            if not all_frames and fid!=self.state['activeFrameId']: continue
            source=frame.text()
            for match in regex.finditer(source):
                start,end=utf16_length(source[:match.start()]),utf16_length(source[:match.end()])
                try: frame.range_cursor(start,end)
                except ValueError: continue
                result.append(dict(frameId=fid,start=start,end=end,text=match.group()))
                if len(result)>=10000: raise ValueError('SEARCH_RESULT_LIMIT: narrow the search')
        return dict(matches=result,count=len(result))

    def replace(self,text,replacement,**options):
        checked_text(replacement)
        found=self.find(text,**options)['matches']
        for match in reversed(found): self.frames[match['frameId']].edit(match['start'],match['end'],replacement)
        return dict(replacements=len(found))

    def copy_fragment(self,start,end):
        self.active.range_cursor(start,end)
        temporary=FrameSession(self.root,self.fonts,self.active.package(),self.checks)
        try:
            temporary.edit(end,utf16_length(temporary.text()),'')
            temporary.edit(0,start,'')
            return dict(format='vayrshemon.fragment',version='0.1.0',content=temporary.package(),fontSources=self.font_sources(),text=temporary.text())
        finally: temporary.deleteLater()

    def paste_fragment(self,start,end,fragment):
        if fragment.get('format')!='vayrshemon.fragment' or fragment.get('version')!='0.1.0': raise ValueError('UNSUPPORTED_CLIPBOARD_FORMAT')
        content=deepcopy(fragment['content']); Draft202012Validator(PACKAGE).validate(content)
        sources=fragment['fontSources']
        Draft202012Validator({'type':'array','maxItems':128,'items':FONT_SOURCE}).validate(sources)
        for source in sources:
            if source['fontId']!='font:'+source['sha256']+':0': raise ValueError('FONT_ID_HASH_MISMATCH')
            self.fonts.register(source['path'],source['sha256'])
            if source['fontId'] not in {s['fontId'] for s in self.state['fontSources']}: self.state['fontSources'].append(deepcopy(source))
        model=content['document']
        replacements={}
        features={}
        for style in model['styles']:
            old=style['styleId']; new='style.clip.'+digest([style,content['styleFeatures'].get(old)])[:20]
            replacements[old]=new; style['styleId']=new
            features[new]=content['styleFeatures'].get(old,deepcopy(self.features))
        content['styleFeatures']=features
        for block in model['stories'][0]['blocks']:
            block['blockId']=identity('block')
            for run in block['runs']: run['styleId']=replacements[run['styleId']]; run['runId']=identity('run')
        temporary=FrameSession(self.root,self.fonts,content,self.checks)
        try:
            before=self.text(); a,b=scalar_offset(before,start),scalar_offset(before,end)
            checked_text(before[:a]+temporary.text()+before[b:])
            for font in model['fonts']:
                if font not in self.model['fonts']: self.model['fonts'].append(font)
            existing={s['styleId'] for s in self.model['styles']}
            self.model['styles'].extend(s for s in model['styles'] if s['styleId'] not in existing)
            self.active.style_features.update(features)
            source=QTextCursor(temporary.doc); source.select(QTextCursor.SelectionType.Document)
            target=self.active.range_cursor(start,end)
            target.insertFragment(QTextDocumentFragment(source))
            if self.editor: self.editor.setTextCursor(target)
        finally: temporary.deleteLater()
        return dict(revision=self.revision)
