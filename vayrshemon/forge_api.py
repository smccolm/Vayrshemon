"""M7 Forge controls use the same API/MCP trace and document guard envelope."""
from copy import deepcopy
from pathlib import Path
from .api import obj, STRING, BOOL
from .reliability_api import ReliabilityAPI, METHODS as BASE
from .reliability_session import ReliabilitySession
from .forge import ForgeProject

GEN={'type':'integer','minimum':0}
GUARD=dict(expected_generation=GEN,project_id=STRING)
METHODS=deepcopy(BASE)
METHODS.update({
 'forge.create':('Create an independent local language project. Does not change the Workbench document.',True,obj(dict(path=STRING,title=STRING,archive=BOOL),('path','title'))),
 'forge.open':('Open a Forge SQLite project. Existing drafts are already durable.',True,obj(dict(path=STRING),('path',))),
 'forge.read':('Read an immutable version or the active autosaved draft, including dictionary, wiki and tests.',False,obj(dict(version=STRING))),
 'forge.status':('Read project identity, generation, active branch, head and draft status.',False,obj()),
 'forge.history':('List immutable language versions with parent hashes.',False,obj()),
 'forge.diff':('Compare stable records, wiki pages and tests between two versions.',False,obj(dict(before=STRING,after=STRING),('before','after'))),
 'forge.draft.replace':('Validate and atomically autosave an entire proposed snapshot. Commit separately to name its version.',True,obj(dict(**GUARD,snapshot={'type':'object'}),('expected_generation','snapshot'))),
 'forge.record.put':('Autosave a wiki page, test or typed language record with stable identity and a project generation guard.',True,obj(dict(**GUARD,collection={'enum':['wiki','tests','sources','orthographies','inputLayouts','transliterations','lexicon','morphology','grammar','corpus','numberConventions']},record={'type':'object'}),('expected_generation','collection','record'))),
 'forge.commit':('Atomically freeze the entire dictionary, wiki, grammar, decisions and test suite as a named version.',True,obj(dict(**GUARD,label=STRING),('expected_generation','label'))),
 'forge.branch':('Create and select a branch from an immutable version. Retains the old branch draft.',True,obj(dict(**GUARD,name=STRING,version=STRING),('expected_generation','name'))),
 'forge.checkout':('Select a branch without discarding either branch draft.',True,obj(dict(**GUARD,name=STRING),('expected_generation','name'))),
 'forge.export':('Export all committed versions, branch drafts and run records as a hashed portable bundle.',True,obj(dict(path=STRING),('path',))),
 'forge.restore':('Restore a verified Forge bundle to a NEW project path.',True,obj(dict(path=STRING,destination=STRING),('path','destination'))),
 'forge.test.run':('Render a frozen test into a NEW document using the approved page. Retain a run manifest; prose grammar needs review.',True,obj(dict(version=STRING,test_id=STRING,directory=STRING),('version','test_id','directory'))),
 'forge.runs':('Inspect test outcomes, pinned versions, diagnostics and output paths.',False,obj()),
 'forge.run.open':('Open a generated test in a separate Workbench process, preserving this document. Logs stdout/stderr.',True,obj(dict(run_id=STRING),('run_id',))),
 'ui.forge':('Show Workbench or Forge and select its workspace section/version or stable wiki/entry/test ID without modifying the document.',True,obj(dict(tab={'enum':['workbench','forge']},section={'enum':['Versions','Dictionary','Wiki','Tests','Research']},version=STRING,record_id=STRING,query=STRING))),
})
for _name,(_description,_mutation,_schema) in METHODS.items():
    if _name.startswith('forge.') and 'expected_generation' in _schema['properties']:
        _schema['required'].append('project_id')


class ForgeSession(ReliabilitySession):
    application_version='0.8.0'
    def __init__(self,*args,**kwargs):
        self.forge=None
        super().__init__(*args,**kwargs)


class ForgeAPI(ReliabilityAPI):
    version='0.8.0'
    methods=METHODS

    def dispatch(self,method,params):
        s=self.session
        if method=='session.status': return dict(super().dispatch(method,params),forge=s.forge.status() if s.forge else None)
        if method=='ui.forge':
            if not s.window or not hasattr(s.window,'show_forge'): raise ValueError('FORGE_DESKTOP_REQUIRED')
            return s.window.show_forge(**params)
        if not method.startswith('forge.'): return super().dispatch(method,params)
        p=s.forge
        if method=='forge.create':
            snapshot=None
            if params.get('archive'):
                from .forge_archive import archive_snapshot
                snapshot=archive_snapshot(s.root)
            s.forge=ForgeProject.create(s.output_path(params['path']),params['title'],snapshot)
            result=s.forge.status()
        elif method=='forge.open':
            s.forge=ForgeProject(params['path']);result=s.forge.status()
        elif method=='forge.restore':
            s.forge=ForgeProject.restore(params['path'],s.output_path(params['destination']));result=s.forge.status()
        else:
            if not p: raise ValueError('FORGE_PROJECT_REQUIRED')
            if 'expected_generation' in params:
                params=dict(params)
                if params.pop('project_id')!=p.status()['projectId']: raise ValueError('FORGE_PROJECT_ID_MISMATCH')
            if method=='forge.read': return p.read(**params)
            if method=='forge.status': return p.status()
            if method=='forge.history': return dict(versions=p.history())
            if method=='forge.diff': return p.diff(**params)
            if method=='forge.runs': return dict(runs=p.runs())
            if method=='forge.draft.replace': result=p.replace_draft(**params)
            elif method=='forge.record.put': result=p.put(**params)
            elif method=='forge.commit': result=p.commit(**params)
            elif method=='forge.branch': result=p.branch(**params)
            elif method=='forge.checkout': result=p.checkout(**params)
            elif method=='forge.export': result=p.export(s.output_path(params['path']))
            elif method=='forge.test.run':
                from .forge_runner import run
                result=run(s.root,p,params['version'],params['test_id'],s.output_path(params['directory']))
            elif method=='forge.run.open':
                import subprocess,sys,os
                from .forge import digest
                from tools.m0.common import load_json,file_hash
                record=next((r for r in p.runs() if r['runId']==params['run_id']),None)
                if not record or not record.get('document'): raise ValueError('FORGE_RUN_DOCUMENT_MISSING')
                path=Path(record['document'])
                if file_hash(path)!=record['documentSha256']: raise ValueError('FORGE_RUN_DOCUMENT_CHANGED: open the edited file explicitly')
                log=path.parent/('desktop-'+__import__('uuid').uuid4().hex+'.log')
                with log.open('xb') as output:
                    child=subprocess.Popen([sys.executable,'-m','vayrshemon','--root',str(s.root),'editor','--document',str(path),'--forge-project',str(p.path),'--page-focus'],cwd=s.root,stdout=output,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
                result=dict(pid=child.pid,document=str(path),logPath=str(log))
            else: raise ValueError('UNKNOWN_FORGE_METHOD')
        if s.window and hasattr(s.window,'forge_panel'): s.window.forge_panel.refresh()
        return result
