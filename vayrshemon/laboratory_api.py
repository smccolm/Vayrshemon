"""M8 language tests share the guarded, traced desktop/API/MCP dispatcher."""
from copy import deepcopy
from .api import obj,STRING
from .forge_api import ForgeAPI,ForgeSession,METHODS as BASE,GUARD
from . import forge_lab

METHODS=deepcopy(BASE)
METHODS.update({
 'forge.lab.read':('Read the versioned rule and test definitions; omit version for the durable draft.',False,obj(dict(version=STRING))),
 'forge.lab.put':('Validate and autosave a declarative rule or test case; commit separately to freeze it.',True,obj(dict(**GUARD,collection={'enum':['rules','cases']},record={'type':'object'}),('project_id','expected_generation','collection','record'))),
 'forge.lab.remove':('Remove a draft case or unreferenced rule. Frozen versions retain the original.',True,obj(dict(**GUARD,collection={'enum':['rules','cases']},record_id=STRING),('project_id','expected_generation','collection','record_id'))),
 'forge.lab.evaluate':('Evaluate finite forms, scalar inventory and explicitly annotated clauses. Draft previews are not frozen runs.',False,obj(dict(version=STRING))),
 'forge.lab.run':('Run the frozen language suite and retain coverage, expected/actual results and content hashes in a new directory.',True,obj(dict(version=STRING,directory=STRING),('version','directory'))),
 'forge.lab.compare':('Run exactly the same pinned cases against two frozen language versions. Defaults to the before version suite.',False,obj(dict(before=STRING,after=STRING,case_version=STRING),('before','after'))),
})
METHODS['ui.forge'][2]['properties']['section']['enum'].append('Laboratory')
METHODS['ui.forge'][2]['properties']['draft']={'type':'boolean'}
METHODS['ui.forge'][2]['properties'].update(run_id=STRING,compare_before=STRING,compare_after=STRING)
METHODS['ui.forge'][2]['properties']['lab_view']={'enum':['Results','Coverage','Diagnostics','Version comparison']}
METHODS['forge.test.run']=('Run language assertions and render a frozen bilingual test with the approved presentation. Meaning still requires review.',*METHODS['forge.test.run'][1:])


class LaboratorySession(ForgeSession):
    application_version='0.9.0'


class LaboratoryAPI(ForgeAPI):
    version='0.9.0'
    methods=METHODS

    def dispatch(self,method,params):
        if not method.startswith('forge.lab.') and method!='forge.test.run': return super().dispatch(method,params)
        p=self.session.forge
        if not p: raise ValueError('FORGE_PROJECT_REQUIRED')
        params=dict(params)
        if 'expected_generation' in params and params.pop('project_id')!=p.status()['projectId']: raise ValueError('FORGE_PROJECT_ID_MISMATCH')
        if method=='forge.lab.read': return p.read(params.get('version'))['snapshot'].get('laboratory',forge_lab.empty_lab())
        if method=='forge.lab.evaluate':
            value=p.read(params.get('version'));return dict(forge_lab.evaluate(value['snapshot']),version=value['selectedVersion'],draft=value['selectedVersion'] is None,generation=value['generation'])
        if method=='forge.lab.compare': return forge_lab.compare(p,**params)
        if method=='forge.lab.put': result=p.lab_edit(**params)
        elif method=='forge.lab.remove': result=p.lab_edit(**params)
        elif method=='forge.lab.run': result=forge_lab.run(p,params['version'],self.session.output_path(params['directory']))
        else:
            from .forge_runner import run
            result=run(self.session.root,p,params['version'],params['test_id'],self.session.output_path(params['directory']),language_report=forge_lab.evaluate(p.read(params['version'])['snapshot']))
        if self.session.window and hasattr(self.session.window,'forge_panel'): self.session.window.forge_panel.refresh()
        return result
