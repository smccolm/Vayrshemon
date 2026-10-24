"""M13 construction gloss controls shared by desktop, CLI and MCP."""
from copy import deepcopy
from .api import obj,STRING
from .forge_api import GUARD
from .reading_api import ReadingSession,ReadingAPI,METHODS as BASE
from . import gloss

METHODS=deepcopy(BASE)
METHODS.update({
 'forge.gloss.read':('Read the versioned compact glossary and abbreviation legend.',False,obj(dict(version=STRING))),
 'forge.gloss.prepare':('Suggest editable dictionary labels for an annotated test; does not save or infer grammatical features.',False,obj(dict(version=STRING,test_id=STRING),('test_id',))),
 'forge.gloss.put':('Validate and save compact labels to the guarded Forge draft; commit separately to freeze the glossary.',True,obj(dict(**GUARD,profile={'type':'object'}),('project_id','expected_generation','profile'))),
 'forge.gloss.inspect':('Explain every annotated token in exact source order, with senses, rules, spans, abbreviations and adaptation notes.',False,obj(dict(version=STRING,test_id=STRING),('test_id',))),
 'page.gloss.copy':('Create a separate four-column copy from a frozen language version, with corresponding paragraph starts aligned across the spread.',True,obj(dict(version=STRING,test_id=STRING,directory=STRING),('version','test_id','directory'))),
 'page.paragraphs.align':('Align corresponding paragraph first baselines across independent columns, changing only paragraph-before spacing in one undoable edit. Defaults to the current four-column spread.',True,obj(dict(frame_ids={'type':'array','items':STRING,'minItems':2,'maxItems':4,'uniqueItems':True}))),
})
METHODS['ui.forge'][2]['properties']['section']['enum'].append('Gloss')
METHODS['ui.forge'][2]['properties'].update(gloss_test=STRING,gloss_preview={'type':'boolean'})
METHODS['jobs.export'][2]['properties'].update(
 page_ids={'type':'array','items':STRING,'minItems':1,'maxItems':2,'uniqueItems':True},
 replace_sha256s={'type':'array','items':{'type':['string','null'],'pattern':'^[0-9a-f]{64}$'},'minItems':1,'maxItems':2})
METHODS['jobs.export']=('Export one proof, or PNG pages from one immutable snapshot using page_ids and a common path stem; spread filenames end _Left and _Right.',*METHODS['jobs.export'][1:])


class GlossSession(ReadingSession):
    application_version='0.14.2'


class GlossAPI(ReadingAPI):
    version='0.14.1'
    methods=METHODS

    def dispatch(self,method,params):
        if method=='page.paragraphs.align':
            from .paragraph_alignment import align
            return align(self.session,**params)
        if not method.startswith('forge.gloss.') and method!='page.gloss.copy':return super().dispatch(method,params)
        p=self.session.forge
        if not p:raise ValueError('FORGE_PROJECT_REQUIRED')
        if method=='page.gloss.copy':
            from .gloss_copy import create
            return create(self.session,p,params['version'],params['test_id'],self.session.output_path(params['directory']))
        snapshot=p.read(params.get('version'))['snapshot']
        if method=='forge.gloss.read':return dict(profile=snapshot['research'].get(gloss.KEY),legend=gloss.TAGS)
        if method=='forge.gloss.prepare':return gloss.prepare(snapshot,params['test_id'])
        if method=='forge.gloss.inspect':return gloss.inspect(snapshot,params['test_id'])
        if params['project_id']!=p.status()['projectId']:raise ValueError('FORGE_PROJECT_ID_MISMATCH')
        snapshot['research'][gloss.KEY]=deepcopy(params['profile']);gloss.profile(snapshot)
        result=p.replace_draft(snapshot,params['expected_generation'])
        if self.session.window:self.session.window.forge_panel.refresh()
        return result
