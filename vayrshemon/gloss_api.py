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
 'page.gloss.copy':('Create a separate four-column copy of the open facing spread, filling only its empty reserved column from a frozen language version.',True,obj(dict(version=STRING,test_id=STRING,directory=STRING),('version','test_id','directory'))),
})
METHODS['ui.forge'][2]['properties']['section']['enum'].append('Gloss')
METHODS['ui.forge'][2]['properties'].update(gloss_test=STRING,gloss_preview={'type':'boolean'})


class GlossSession(ReadingSession):
    application_version='0.14.0'


class GlossAPI(ReadingAPI):
    version='0.14.0'
    methods=METHODS

    def dispatch(self,method,params):
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
