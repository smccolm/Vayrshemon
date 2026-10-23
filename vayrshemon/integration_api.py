"""M9 language integration and release controls, shared by desktop/API/MCP."""
from copy import deepcopy
from .api import obj, STRING
from .forge_api import GUARD
from .laboratory_api import LaboratoryAPI, LaboratorySession, METHODS as BASE
from . import forge_merge, forge_release

METHODS = deepcopy(BASE)
METHODS.update({
 'forge.merge.preview': ('Plan a three-way merge from a branch frozen head into the active clean branch. Inspect base, parents and every conflict.', False, obj(dict(source=STRING), ('source',))),
 'forge.merge.apply': ('Atomically commit a reviewed merge with both parents. Require the exact preview, generation and every conflict resolution.', True, obj(dict(**GUARD, source=STRING, plan_id=STRING, label=STRING, resolutions={'type':'object'}), ('project_id','expected_generation','source','plan_id','label','resolutions'))),
 'forge.releases': ('List immutable named language releases and pinned versions; releases never follow a moving branch.', False, obj()),
 'forge.release.read': ('Read a named language release, embedded test evidence and outstanding review status.', False, obj(dict(name=STRING), ('name',))),
 'forge.release.create': ('Freeze a named release with matching suite and bound-page evidence. Experimental releases retain review gaps; stable gates require full passes and an accepting reviewer.', True, obj(dict(**GUARD, name=STRING, version=STRING, channel={'enum':['experimental','stable']}, notes=STRING, suite_run_id=STRING, workbench_run_id=STRING, reviewer=STRING), ('project_id','expected_generation','name','version','channel','notes','suite_run_id','workbench_run_id'))),
 'forge.release.export': ('Export a language release with its dictionary, wiki, assertions and embedded reports. Proof/font binaries remain separately hash-referenced.', True, obj(dict(name=STRING,path=STRING), ('name','path'))),
})
METHODS['ui.forge'][2]['properties']['section']['enum'] += ['Merges', 'Releases']
METHODS['ui.forge'][2]['properties'].update(merge_source=STRING,release_name=STRING)
METHODS['jobs.export'][2]['properties']['replace_sha256']={'type':'string','pattern':'^[0-9a-f]{64}$'}
METHODS['ui.workspace'][2]['properties'].update(fit_height={'type':'boolean'},fit_width={'type':'boolean'})


class IntegrationSession(LaboratorySession):
    application_version = '0.10.0'


class IntegrationAPI(LaboratoryAPI):
    version = '0.10.0'
    methods = METHODS

    def dispatch(self, method, params):
        if not (method.startswith('forge.merge.') or method.startswith('forge.release.') or method == 'forge.releases'):
            return super().dispatch(method, params)
        p = self.session.forge
        if not p: raise ValueError('FORGE_PROJECT_REQUIRED')
        params = dict(params)
        if 'expected_generation' in params and params.pop('project_id') != p.status()['projectId']:
            raise ValueError('FORGE_PROJECT_ID_MISMATCH')
        if method == 'forge.merge.preview': return forge_merge.preview(p, **params)
        if method == 'forge.merge.apply': result = forge_merge.apply(p, **params)
        elif method == 'forge.releases':
            return dict(releases=[{k:v for k,v in r.items() if k not in ('suite','workbench')} for r in forge_release.list_releases(p)])
        elif method == 'forge.release.read':
            result = next((r for r in forge_release.list_releases(p) if r['name'] == params['name']), None)
            if not result: raise ValueError('RELEASE_NOT_FOUND')
            return result
        elif method == 'forge.release.create': result = forge_release.create(p, **params)
        else:
            params['path'] = self.session.output_path(params['path']); result = forge_release.export(p, **params)
        if self.session.window: self.session.window.forge_panel.refresh()
        return result
