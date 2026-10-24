"""M11 Maxima and optional discourse-order controls."""
from copy import deepcopy
from .api import obj,STRING
from .forge_api import GUARD
from .variation_api import VariationAPI,VariationSession,METHODS as BASE
from . import spelling,variation,forge_lab

METHODS=deepcopy(BASE)
METHODS.update({
 'forge.spelling.read':('Read versioned Maxima policy and paired letter identities.',False,obj(dict(version=STRING))),
 'forge.spelling.replace':('Validate and save the guarded draft spelling policy; does not rewrite text.',True,obj(dict(**GUARD,policy={'type':'object'}),('project_id','expected_generation','policy'))),
 'forge.spelling.preview':('Preview exact sentence-initial Maxima edits on a selected page. No Unicode uppercase or automatic typing.',False,obj(dict(test_id=STRING,version=STRING),('test_id',))),
 'forge.spelling.apply':('Apply the exact reviewed draft preview; clone source cases, preserve earlier cases and update bound page atomically.',True,obj(dict(**GUARD,test_id=STRING,plan_id=STRING),('project_id','expected_generation','test_id','plan_id'))),
 'forge.spelling.audit':('Inspect mapped sentence initials, missing Maxima and unresolved initial scalars.',False,obj(dict(version=STRING,test_id=STRING),('test_id',))),
 'forge.spelling.run':('Freeze a spelling audit and its exact input hashes.',True,obj(dict(version=STRING,test_id=STRING,directory=STRING),('version','test_id','directory'))),
 'forge.variation.orders':('Inspect retained and conditional clause orders for explicit discourse context; does not reorder text.',False,obj(dict(version=STRING,rule_id=STRING,context={'type':'object'}),('rule_id','context'))),
})
METHODS['ui.forge'][2]['properties']['section']['enum'].append('Orthography')
METHODS['ui.forge'][2]['properties'].update(spelling_test=STRING,spelling_preview={'type':'boolean'},spelling_run=STRING)


class SpellingSession(VariationSession):
    application_version='0.12.0'


class SpellingAPI(VariationAPI):
    version='0.12.0'
    methods=METHODS

    def dispatch(self,method,params):
        if not method.startswith('forge.spelling.') and method not in ('forge.test.run','forge.variation.orders'):return super().dispatch(method,params)
        p=self.session.forge
        if not p:raise ValueError('FORGE_PROJECT_REQUIRED')
        params=dict(params)
        if 'expected_generation' in params and params.pop('project_id')!=p.status()['projectId']:raise ValueError('FORGE_PROJECT_ID_MISMATCH')
        if method=='forge.spelling.read':
            s=p.read(params.get('version'))['snapshot'];return dict(policy=s.get('spelling'),pairs=spelling.pairs(s) if 'spelling' in s else {})
        if method=='forge.spelling.preview':return spelling.preview(p,**params)
        if method=='forge.spelling.audit':return spelling.audit(p.read(params.pop('version',None))['snapshot'],**params)
        if method=='forge.variation.orders':return variation.orders(p.read(params.pop('version',None))['snapshot'],**params)
        if method=='forge.spelling.replace':
            s=p.read()['snapshot'];s['spelling']=params['policy'];result=p.replace_draft(s,params['expected_generation'])
        elif method=='forge.spelling.apply':result=spelling.apply(p,**params)
        elif method=='forge.spelling.run':
            params['directory']=self.session.output_path(params['directory']);result=spelling.run(p,**params)
        else:
            from .forge_runner import run
            snapshot=p.read(params['version'])['snapshot'];result=run(self.session.root,p,params['version'],params['test_id'],self.session.output_path(params['directory']),language_report=forge_lab.evaluate(snapshot),variation_report=variation.audit(snapshot,params['test_id']) if 'variation' in snapshot else None,spelling_report=spelling.audit(snapshot,params['test_id']) if 'spelling' in snapshot else None)
        if self.session.window:self.session.window.forge_panel.refresh()
        return result
