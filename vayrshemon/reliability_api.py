"""M6 API/MCP additions, retaining the same revision and idempotency guards."""
from copy import deepcopy
from pathlib import Path
from .api import obj,STRING,NUMBER
from .language_api import LanguageAPI,METHODS as M5_METHODS
from .studio_api import EXPORT_FIELDS
from tools.recovery import create_backup,verify_backup,restore_backup

METHODS=deepcopy(M5_METHODS)
METHODS['ui.workspace'][2]['properties']['panel']['enum']+=['Reliability']
METHODS.update({
 'view.tool':('Choose Select to click a frame to edit, or Hand to drag the view. No document revision or undo entry.',True,obj(dict(tool={'enum':['select','hand']}),('tool',))),
 'view.pan':('Move the page by viewport logical pixels, without changing text, selection or document history.',True,obj(dict(dx={'type':'number','minimum':-100000,'maximum':100000},dy={'type':'number','minimum':-100000,'maximum':100000}),('dx','dy'))),
 'view.center':('Bring the current page back to the center of the viewport.',True,obj()),
 'view.inspect':('Read the active navigation tool, page origin, viewport and zoom.',False,obj()),
 'performance.inspect':('Read bounded shaping/cache counters and reliability limits.',False,obj()),
 'backup.create':('Back up the last saved file and exact font bytes into a verified portable bundle. Does not save unsaved edits.',True,obj(dict(directory=STRING))),
 'backup.verify':('Verify every bundle member and all source font identities without opening the document.',False,obj(dict(path=STRING),('path',))),
 'backup.restore':('Recover to a NEW directory, retaining the exact original and relocating verified font paths. Does not replace the open editor.',True,obj(dict(path=STRING,destination=STRING),('path','destination'))),
 'jobs.export':('Start an isolated cancellable PNG/SVG/PDF proof from the current immutable revision; inspect jobs.status for completion or errors.',True,obj(dict(path=STRING,**EXPORT_FIELDS),('path','format','mode','dpi','raster_policy'))),
 'jobs.status':('Inspect proof job state, phase, revision, staleness, output and full worker log path.',False,obj(dict(job_id=STRING))),
 'jobs.cancel':('Cancel this editor\u2019s proof worker before publication. Never writes a partial destination.',True,obj(dict(job_id=STRING),('job_id',))),
})


class ReliabilityAPI(LanguageAPI):
    version='0.7.0'
    methods=METHODS

    def dispatch(self,method,params):
        s=self.session
        if method in ('view.tool','view.pan','view.center','view.inspect'):
            if not s.window: raise ValueError('DESKTOP_REQUIRED')
            canvas=s.window.preview
            return {'view.tool':lambda:canvas.set_tool(**params),'view.pan':lambda:canvas.pan_by(**params),
                'view.center':canvas.center_page,'view.inspect':canvas.navigation_state}[method]()
        if method=='ui.inspect': return dict(super().dispatch(method,params),navigation=s.window.preview.navigation_state() if s.window else None)
        if method=='session.status': return dict(super().dispatch(method,params),lastBackup=s.last_backup,backupError=s.backup_error)
        if method=='performance.inspect': return dict(shaping=s.story_cache.info(),pageCompositions=len(s._composition_cache),
            maxPageCompositions=2,paintTileCacheBytes=96*1024*1024,maxDocumentScalars=200000,maxFrames=128,
            maxGlyphsPerConnectedPageComponent=20000,backgroundConcurrency=1)
        if method=='backup.create':
            if s.dirty or not s.saved_path: raise ValueError('SAVE_BEFORE_BACKUP: bundle only a known saved revision')
            directory=s.output_path(params['directory']) if params.get('directory') else s.root/'.local/backups'
            return create_backup(s.saved_path,directory,expected_sha256=s.saved_hash)
        if method=='backup.verify': return verify_backup(params['path'])[0]
        if method=='backup.restore': return restore_backup(params['path'],s.output_path(params['destination']))
        if method=='jobs.export': return s.jobs.start(**params)
        if method=='jobs.status': return s.jobs.status(**params)
        if method=='jobs.cancel': return s.jobs.cancel(**params)
        if method=='collision.inspect': return s.composition(page_id=params.get('page_id')).collision_report(params.get('page_id'))
        return super().dispatch(method,params)
