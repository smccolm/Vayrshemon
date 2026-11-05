"""M14 saves, legacy import, embedded previews and desktop/CLI/MCP controls."""
from copy import deepcopy
from contextlib import contextmanager
from pathlib import Path
from jsonschema import Draft202012Validator
from tools.m0.common import load_json,file_hash
from .api import obj,STRING
from .gloss_api import GlossSession,GlossAPI,METHODS as BASE
from .language_contracts import DOCUMENT as LEGACY_DOCUMENT
from .file_contracts import DOCUMENT,STATE
from .book_session import BookSession
from .book_frames import BookFrames
from . import saved_preview
from . import page_numbering
from .numbering_contracts import PATCH as NUMBERING_PATCH

METHODS=deepcopy(BASE)
METHODS['publication.edition.inspect']=('Inspect native fixed print edition provenance, complete verse/section counts, section page references and current page side/folio. Frozen text stays searchable and copyable; text/layout edits require a new generated edition.',False,obj(dict(page_id=STRING)))
METHODS['document.close']=('Close the current document and return to a clean Untitled page, keeping the application session open. Reject unsaved changes unless discardUnsaved is explicit; save first to retain them.',True,obj(dict(discardUnsaved={'type':'boolean'})))
METHODS['page.numbering.read']=('Read saved Unta page-number settings. New documents number multiple pages at 50 pt and 28 pt edge inset; older documents without settings remain hidden.',False,obj({}))
METHODS['page.numbering.configure']=('Set Unta numbering visibility, margin position, size, edge inset and minimumPages (1 or 2) in one undo step. Keep body frames and typography unchanged; unsafe numbers are withheld and block export.',True,NUMBERING_PATCH)
METHODS['page.numbering.inspect']=('Inspect actual base-12 glyphs, physical page numbers and collision-safe placements for the visible pages, one page, or all pages.',False,obj(dict(page_id=STRING,all_pages={'type':'boolean'},page_mode={'enum':['one','two']})))
for name in ('jobs.export','publication.export','publication.preflight','render.png','render.svg'):
    METHODS[name][2]['properties']['page_mode']={'enum':['one','two']}
METHODS['jobs.status']=('Inspect proof job state, revision, staleness, output and worker log. PDF progress includes stage, physical page, pageCount, completedUnits, totalUnits and percent; 100 means successfully published.',*METHODS['jobs.status'][1:])
METHODS['view.inspect']=('Read tool, origin, viewport, effective zoom, fitMode, pageNumber, pageCount, visiblePageNumbers and previous/next availability.',*METHODS['view.inspect'][1:])
METHODS['view.pages']=('Show the selected single page or its facing pair. Retain an explicit right-page target, manual zoom or automatic fit choice; preserve content and Undo history.',*METHODS['view.pages'][1:])
METHODS['jobs.export']=('Export one proof, or PNG/SVG pages from one immutable snapshot using page_ids and a common path stem; spread filenames end _Left and _Right. Both destinations are checked before publishing.',*METHODS['jobs.export'][1:])
for name in ('jobs.export','publication.export'):
    METHODS[name][2]['properties']['pdf_view']={'enum':['one','two']}
    METHODS[name]=(METHODS[name][0]+' PDF without page_id includes all separate numbered pages; pdf_view sets single or facing-page opening layout, defaulting to the desktop view or saved page mode.',*METHODS[name][1:])
for name in ('document.save','document.save-as'):
    METHODS[name][2]['properties']['preview_mode']={'enum':['one','two']}
    METHODS[name]=(METHODS[name][0]+' Embed the visible page/spread and saved color mode atomically. Headless saves reuse the saved page mode, or one page; preview_mode overrides it.',*METHODS[name][1:])
METHODS['document.saved-preview']=('Inspect embedded preview metadata from the saved file (never unsaved state). No rendering or external fonts required.',False,obj(dict(path=STRING)))
METHODS['shell.status']=('Inspect Windows .vay association and installed icon/thumbnail component; no registry changes.',False,obj({}))
METHODS['view.page']=('Go to a 1-based page or the previous/next visible page pair. Direct right-page targets retain their number. Viewing preserves text, formatting, dirty state and Undo history; selection advances the revision guard.',True,dict(obj(dict(page={'type':'integer','minimum':1},direction={'enum':['previous','next']})),oneOf=[{'required':['page'],'not':{'required':['direction']}},{'required':['direction'],'not':{'required':['page']}}]))
METHODS['page.transliteration.inspect']=('Preview which existing script/Roman pair an update will use, whether its text differs and a review guard. Works independently of one/two-page view.',False,obj({}))
METHODS['page.transliteration.update']=('Update the existing Transliteration 7 column from exact Thimfora slots and Maxima in one undo step; preserve destination styling and English/gloss text. Optional expected_plan rejects changes since inspection.',True,obj(dict(expected_plan={'type':'string','pattern':'^[0-9a-f]{64}$'})))


class FileSession(BookSession,GlossSession):
    application_version='0.15.34'
    file_version='0.6.0'
    document_schema=DOCUMENT
    state_schema=STATE

    def __init__(self,*args,**kwargs):
        self.saved_preview=None;self.preview_mode_override=None;self.saved_page_mode='one'
        super().__init__(*args,**kwargs)
        from .schema_validation import NativeDocumentValidator
        self.checks['document']=NativeDocumentValidator(self.checks['document'],
            [load_json(p) for p in (self.root/'schemas').glob('*.schema.json')])

    def new_state(self,*args,**kwargs):
        state=super().new_state(*args,**kwargs)
        # New documents start in the preferred reading palette. Opening a
        # saved file restores its own view without applying these defaults.
        state['view'].update(mode='mono',monochromePaper='white')
        from .numbering_contracts import new_document_defaults
        state['pageNumbering']=new_document_defaults()
        return state

    def add_page(self,*args,**kwargs):
        config=page_numbering.settings(self)
        if config['enabled'] and len(self.state['pages'])+1>=config.get('minimumPages',1):
            page_numbering.ensure_fonts(self)
        return super().add_page(*args,**kwargs)

    def initialize_startup_zoom(self,zoom):
        # A fresh document after New/Close has a nonzero session revision.
        # Require an untouched document instead, without creating an edit or
        # save-on-close prompt. Opened files retain their saved view exactly.
        if self.saved_path or self.history or self.dirty or self._undo or self._redo:
            return False
        if not .1<=zoom<=3:raise ValueError('STARTUP_ZOOM_RANGE')
        self.view['zoom']=zoom
        self._state=self.capture()
        self._saved_digest=self.content_digest(self._state)
        self.checkpoint();self.changed.emit()
        self.log.emit('workspace','INITIAL_PAGE_FIT',zoom=zoom,revision=self.revision)
        return True

    def migrate(self,payload,path):
        version=payload.get('formatVersion')
        if payload.get('format')=='vayrshemon.document' and version in ('0.6.0','0.5.0'):
            from .schema_validation import validate
            validate(DOCUMENT if version=='0.6.0' else LEGACY_DOCUMENT,payload)
            if payload.get('shellPreview'):saved_preview.validate(payload['shellPreview'],payload['state'])
            return deepcopy(payload['state']),False
        return super().migrate(payload,path)

    @contextmanager
    def reuse_open_preflight(self):
        # Only the paired UI preflight/open retains a prepared file.
        self._reuse_open_preflight=True;self._prepared_open=None
        try:yield
        finally:self._reuse_open_preflight=False;self._prepared_open=None

    def read_file(self,path):
        path=Path(path).resolve(strict=True)
        if path.stat().st_size>self.max_file_bytes:raise ValueError('DOCUMENT_TOO_LARGE')
        prepared=self.__dict__.get('_prepared_open')
        if prepared and prepared[0]==path and prepared[1]==file_hash(path):
            self._prepared_open=None
            return prepared[2]
        self.report_open('Reading compressed document',5)
        payload=load_json(path)
        version=payload.get('formatVersion')
        if payload.get('format')=='vayrshemon.document' and version in ('0.6.0','0.5.0'):
            from .schema_validation import validate
            self.report_open('Checking document structure',15)
            validate(DOCUMENT if version=='0.6.0' else LEGACY_DOCUMENT,payload)
            self.report_open('Verifying saved preview',25)
            if payload.get('shellPreview'):saved_preview.validate(payload['shellPreview'],payload['state'])
            # The freshly parsed state has no owner outside this open operation.
            state,migrated=payload['state'],False
        else:state,migrated=self.migrate(payload,path)
        self.report_open('Checking text, language and page references',35)
        self.validate(state)
        result=path,payload,state,migrated
        if self.__dict__.get('_reuse_open_preflight'):
            self._prepared_open=(path,file_hash(path),result)
        return result

    def prepare_save_payload(self,payload):
        mode=self.preview_mode_override or (self.window.preview.page_mode if self.window else self.saved_page_mode)
        preview=saved_preview.create(self,payload['state'],mode)
        # First field makes the shell reader's job predictable, while this is
        # still ordinary UTF-8 JSON and all document data lives in one file.
        return dict(shellPreview=preview,**payload)

    def save(self,path,preview_mode=None):
        if preview_mode is not None and preview_mode not in ('one','two'):raise ValueError('UNKNOWN_PAGE_VIEW_MODE')
        self.preview_mode_override=preview_mode
        try:result=super().save(path)
        finally:self.preview_mode_override=None
        self.saved_preview=self._last_saved_preview;self.saved_page_mode=self.saved_preview['pageMode']
        saved_preview.notify_saved(self.saved_path)
        self.log.emit('persistence','SAVED_PREVIEW_READY',**saved_preview.summary(self.saved_preview))
        return dict(result,preview=saved_preview.summary(self.saved_preview))

    def open(self,path,**kwargs):
        from .loading import loading_dialog
        with loading_dialog(self,path):
            result=super().open(path,**kwargs)
            self.saved_preview=self._last_opened_preview;self.saved_page_mode=self.saved_preview['pageMode'] if self.saved_preview else 'one'
            if self.window:self.window.restore_saved_arrangement()
            return result

    def new(self,*args,**kwargs):
        result=super().new(*args,**kwargs);self.saved_preview=None;self.saved_page_mode='one'
        if self.window:
            self.window.restore_saved_arrangement()
            self.window.fit_new_page()
        return result

    def fingerprint(self):
        return dict(super().fingerprint(),nativeCompatibility='0.7.0 compressed books; 0.6.0 editable state; reads 0.1–0.6',savedPreviewVersion=1)

    def validate(self,state):
        super().validate(state)
        from .print_edition import validate
        validate(state)
        if page_numbering.enabled_for(state):
            if not set(page_numbering.FONT_IDS)<={f['fontId'] for f in state['fontSources']}:
                raise ValueError('PAGE_NUMBER_FONT_SOURCE_MISSING')

    def bind_editor(self):
        super().bind_editor()
        if self._editor and self.state.get('printEdition'):
            self._editor.setReadOnly(True)

    def composition(self,mode=None,page_id=None):
        if not self.state.get('printEdition'):return super().composition(mode,page_id)
        from .print_edition import Composition
        from collections import OrderedDict
        mode=mode or self.view['mode'];page_id=page_id or self.current_page()['pageId'];key=(mode,page_id)
        if key not in self._composition_cache:
            self._composition_cache[key]=Composition(self,mode,page_id)
            while len(self._composition_cache)>2:self._composition_cache.pop(next(iter(self._composition_cache)))
        return self._composition_cache[key]


class FileAPI(GlossAPI):
    version='0.15.0'
    methods=METHODS

    def dispatch(self,method,params):
        from . import print_edition
        if method=='publication.edition.inspect':return print_edition.inspect(self.session,**params)
        if self.session.state.get('printEdition') and method=='view.configure' and (params.get('mode','mono')!='mono' or params.get('monochromePaper','white')!='white'):
            raise ValueError('FIXED_PRINT_PALETTE: this edition is black ink on white paper')
        if self.session.state.get('printEdition') and self.methods.get(method,(None,False))[1] and method not in print_edition.ALLOWED_MUTATIONS:
            raise ValueError('FIXED_PRINT_EDITION: text and page geometry are sealed to preserve this historical publication. Search, copy, save, navigation, numbering and export remain available.')
        if method=='document.close':
            if self.session.dirty and not params.get('discardUnsaved',False):
                raise ValueError('UNSAVED_CHANGES: save or explicitly discard')
            return self.session.new()
        if method=='page.numbering.read':return page_numbering.settings(self.session)
        if method=='page.numbering.inspect':return page_numbering.inspect(self.session,**params)
        if method in ('jobs.export','publication.export','publication.preflight','render.png','render.svg'):
            params=dict(params)
            params.setdefault('page_mode',params.get('pdf_view') or ('two' if params.get('page_ids') else page_numbering.page_mode(self.session)))
        if method=='performance.inspect':
            from .book_session import MAX_PAGES
            lazy=isinstance(self.session.frames,BookFrames)
            return dict(super().dispatch(method,params),maxPages=MAX_PAGES,
                        maxNativeFileBytes=self.session.max_file_bytes,lazyFrameEditors=lazy,
                        loadedFrameEditors=len(self.session.frames.loaded) if lazy else len(self.session.frames),
                        frameEditorCacheTarget=16 if lazy else None)
        if method=='frame.select' and isinstance(self.session.frames,BookFrames):
            return self.session.navigate_frame(params['frame_id'])
        if method=='view.page':
            if not self.session.window:raise ValueError('DESKTOP_REQUIRED')
            return self.session.window.page_navigator.navigate(**params)
        if method=='view.configure' and 'zoom' in params and self.session.window:
            # A deliberate zoom gesture leaves automatic fitting. Failed
            # requests must not change the current fit choice.
            result=super().dispatch(method,params)
            self.session.window.preview.fit_mode=None
            self.session.window.preview.update_page()
            return result
        if method in ('jobs.export','publication.export') and params['format']=='pdf':
            params=dict(params)
            params.setdefault('pdf_view',params['page_mode'])
        if method.startswith('page.transliteration.'):
            from . import transliteration_update
            return transliteration_update.inspect(self.session) if method.endswith('.inspect') else transliteration_update.update(self.session,**params)
        if method in ('document.save','document.save-as'):return self.session.save(**params)
        if method=='document.saved-preview':
            path=params.get('path') or self.session.saved_path
            if not path:return dict(path=None,preview=None)
            path,payload,_,_=self.session.read_file(path)
            return dict(path=str(path),preview=saved_preview.summary(payload.get('shellPreview')))
        if method=='shell.status':
            from tools.windows_shell import status
            return status(self.session.root)
        return super().dispatch(method,params)

    def mutate(self,method,params):
        if method=='page.numbering.configure':return page_numbering.configure(self.session,**params)
        return super().mutate(method,params)
