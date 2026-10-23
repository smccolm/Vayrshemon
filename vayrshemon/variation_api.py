"""M10 context-conditioned language alternatives and reproducible inspection."""
from copy import deepcopy
from .api import obj,STRING
from .forge_api import GUARD
from .integration_api import IntegrationAPI,IntegrationSession,METHODS as BASE
from . import variation,forge_lab

METHODS=deepcopy(BASE)
METHODS.update({
 'forge.variation.read':('Read versioned optional forms and repetition watch definitions.',False,obj(dict(version=STRING))),
 'forge.variation.replace':('Validate and save variation proposals in the guarded draft; commit separately to freeze them.',True,obj(dict(**GUARD,variation={'type':'object'}),('project_id','expected_generation','variation'))),
 'forge.variation.forms':('Inspect full and optional forms with explicit author-supplied context. No automatic rewriting.',False,obj(dict(version=STRING,entry_id=STRING,features={'type':'object'},context={'type':'object'}),('entry_id','features','context'))),
 'forge.variation.audit':('Inspect repetition in a versioned page. Advisory counts cannot certify natural language.',False,obj(dict(version=STRING,test_id=STRING),('test_id',))),
 'forge.variation.run':('Save a frozen repetition audit with snapshot, page and watch hashes.',True,obj(dict(version=STRING,test_id=STRING,directory=STRING),('version','test_id','directory'))),
 'forge.variation.compare':('Compare page text in two versions with identical watch definitions from the after version.',False,obj(dict(before=STRING,after=STRING,test_id=STRING),('before','after','test_id'))),
})
METHODS['ui.forge'][2]['properties']['section']['enum'].append('Variation')
METHODS['ui.forge'][2]['properties'].update(variation_before=STRING,variation_after=STRING,variation_test=STRING,variation_run=STRING)


class VariationSession(IntegrationSession):
    application_version='0.11.0'


class VariationAPI(IntegrationAPI):
    version='0.11.0'
    methods=METHODS

    def dispatch(self,method,params):
        if not method.startswith('forge.variation.') and method!='forge.test.run': return super().dispatch(method,params)
        p=self.session.forge
        if not p: raise ValueError('FORGE_PROJECT_REQUIRED')
        params=dict(params)
        if 'expected_generation' in params and params.pop('project_id')!=p.status()['projectId']: raise ValueError('FORGE_PROJECT_ID_MISMATCH')
        if method=='forge.variation.read': return p.read(params.get('version'))['snapshot'].get('variation',variation.empty())
        if method=='forge.variation.forms': return variation.forms(p.read(params.pop('version',None))['snapshot'],**params)
        if method=='forge.variation.audit': return variation.audit(p.read(params.pop('version',None))['snapshot'],**params)
        if method=='forge.variation.compare': return variation.compare(p,**params)
        if method=='forge.variation.replace':
            snapshot=p.read()['snapshot'];snapshot['variation']=params['variation']
            result=p.replace_draft(snapshot,params['expected_generation'])
        elif method=='forge.variation.run':
            params['directory']=self.session.output_path(params['directory']);result=variation.run(p,**params)
        else:
            from .forge_runner import run
            snapshot=p.read(params['version'])['snapshot']
            result=run(self.session.root,p,params['version'],params['test_id'],self.session.output_path(params['directory']),language_report=forge_lab.evaluate(snapshot),variation_report=variation.audit(snapshot,params['test_id']) if 'variation' in snapshot else None)
        if self.session.window: self.session.window.forge_panel.refresh()
        return result
