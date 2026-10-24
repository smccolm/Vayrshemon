"""M12 parallel font readings and continued language development."""
from copy import deepcopy
from .api import obj,STRING
from .forge_api import GUARD
from .spelling_api import SpellingSession,SpellingAPI,METHODS as BASE
from . import reading,spelling,variation,forge_lab

METHODS=deepcopy(BASE)
MODE={'enum':list(reading.MODES)}
METHODS.update({
 'forge.reading.read':('Read the versioned parallel reading profile and modes.',False,obj(dict(version=STRING))),
 'forge.reading.enable':('Enable the verified Thimfora 79 / transliteration 7 reading profile in the guarded draft.',True,obj(dict(**GUARD),('project_id','expected_generation'))),
 'forge.reading.inspect':('Inspect exact parallel text, Maxima/Minima counts and font-reading evidence.',False,obj(dict(test_id=STRING,version=STRING,mode=MODE),('test_id',))),
 'page.reading.copy':('Create a separate editable transliteration or literal Roman copy of this two-column page. Source stays unchanged.',True,obj(dict(mode={'enum':['transliteration','literal']},directory=STRING),('mode','directory'))),
})
METHODS['forge.test.run'][2]['properties']['reading_mode']=MODE
METHODS['ui.forge'][2]['properties']['section']['enum'].append('Reading')
METHODS['ui.forge'][2]['properties'].update(reading_test=STRING,reading_mode=MODE,reading_preview={'type':'boolean'})


class ReadingSession(SpellingSession):
    application_version='0.13.1'


class ReadingAPI(SpellingAPI):
    version='0.13.0'
    methods=METHODS

    def dispatch(self,method,params):
        if method=='page.reading.copy':return reading.copy(self.session,params['mode'],self.session.output_path(params['directory']))
        if not method.startswith('forge.reading.') and method!='forge.test.run':return super().dispatch(method,params)
        p=self.session.forge
        if not p:raise ValueError('FORGE_PROJECT_REQUIRED')
        params=dict(params)
        if method=='forge.reading.read':return dict(policy=p.read(params.get('version'))['snapshot'].get('reading'),modes=reading.MODES)
        if method=='forge.reading.inspect':return reading.inspect(p.read(params.pop('version',None))['snapshot'],**params)
        if method=='forge.reading.enable':
            if params['project_id']!=p.status()['projectId']:raise ValueError('FORGE_PROJECT_ID_MISMATCH')
            s=p.read()['snapshot'];s['reading']=reading.policy();result=p.replace_draft(s,params['expected_generation'])
        else:
            from .forge_runner import run
            s=p.read(params['version'])['snapshot'];result=run(self.session.root,p,params['version'],params['test_id'],self.session.output_path(params['directory']),language_report=forge_lab.evaluate(s),variation_report=variation.audit(s,params['test_id']) if 'variation' in s else None,spelling_report=spelling.audit(s,params['test_id']) if 'spelling' in s else None,reading_mode=params.get('reading_mode','translation'))
        if self.session.window:self.session.window.forge_panel.refresh()
        return result
