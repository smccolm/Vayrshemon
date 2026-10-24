"""M14 saves, legacy import, embedded previews and desktop/CLI/MCP controls."""
from copy import deepcopy
from jsonschema import Draft202012Validator
from tools.m0.common import load_json
from .api import obj,STRING
from .gloss_api import GlossSession,GlossAPI,METHODS as BASE
from .language_contracts import DOCUMENT as LEGACY_DOCUMENT
from .file_contracts import DOCUMENT
from . import saved_preview

METHODS=deepcopy(BASE)
for name in ('document.save','document.save-as'):
    METHODS[name][2]['properties']['preview_mode']={'enum':['one','two']}
    METHODS[name]=(METHODS[name][0]+' Embed the visible page/spread and saved color mode atomically. Headless saves reuse the saved page mode, or one page; preview_mode overrides it.',*METHODS[name][1:])
METHODS['document.saved-preview']=('Inspect embedded preview metadata from the saved file (never unsaved state). No rendering or external fonts required.',False,obj(dict(path=STRING)))
METHODS['shell.status']=('Inspect Windows .vay association and installed icon/thumbnail component; no registry changes.',False,obj({}))


class FileSession(GlossSession):
    application_version='0.15.6'
    file_version='0.6.0'
    document_schema=DOCUMENT

    def __init__(self,*args,**kwargs):
        self.saved_preview=None;self.preview_mode_override=None;self.saved_page_mode='one'
        super().__init__(*args,**kwargs)

    def migrate(self,payload,path):
        version=payload.get('formatVersion')
        if payload.get('format')=='vayrshemon.document' and version in ('0.6.0','0.5.0'):
            Draft202012Validator(DOCUMENT if version=='0.6.0' else LEGACY_DOCUMENT).validate(payload)
            if payload.get('shellPreview'):saved_preview.validate(payload['shellPreview'],payload['state'])
            return deepcopy(payload['state']),False
        return super().migrate(payload,path)

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
        self.saved_preview=load_json(self.saved_path)['shellPreview'];self.saved_page_mode=self.saved_preview['pageMode']
        saved_preview.notify_saved(self.saved_path)
        self.log.emit('persistence','SAVED_PREVIEW_READY',**saved_preview.summary(self.saved_preview))
        return dict(result,preview=saved_preview.summary(self.saved_preview))

    def open(self,path,**kwargs):
        result=super().open(path,**kwargs)
        self.saved_preview=load_json(path).get('shellPreview');self.saved_page_mode=self.saved_preview['pageMode'] if self.saved_preview else 'one'
        if self.window:self.window.restore_saved_arrangement()
        return result

    def new(self,*args,**kwargs):
        result=super().new(*args,**kwargs);self.saved_preview=None;self.saved_page_mode='one';return result

    def fingerprint(self):
        return dict(super().fingerprint(),nativeCompatibility='0.6.0; reads 0.1–0.5',savedPreviewVersion=1)


class FileAPI(GlossAPI):
    version='0.15.0'
    methods=METHODS

    def dispatch(self,method,params):
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
