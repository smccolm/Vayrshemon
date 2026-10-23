"""M6 retains native 0.5 documents; reliability state is local, not language data."""
from collections import OrderedDict
from .language_session import LanguageSession
from .incremental import StoryCache


class ReliabilitySession(LanguageSession):
    application_version='0.7.1'

    def __init__(self,*args,**kwargs):
        self.story_cache=StoryCache();self.backup_error=None;self.last_backup=None;self.jobs=None
        super().__init__(*args,**kwargs)
        from .jobs import JobManager
        self.jobs=JobManager(self)

    def _restore(self,state):
        self.story_cache.clear()
        super()._restore(state)

    def invalidate_composition(self): self._composition_cache=OrderedDict()

    def composition(self,mode=None,page_id=None):
        from .studio_typesetting import StudioComposition
        mode=mode or self.view['mode'];page_id=page_id or self.current_page()['pageId'];key=(mode,page_id)
        if key not in self._composition_cache:
            self._composition_cache[key]=StudioComposition(self,mode,page_id)
            while len(self._composition_cache)>2: self._composition_cache.popitem(last=False)
        self._composition_cache.move_to_end(key)
        return self._composition_cache[key]

    def save(self,path):
        result=super().save(path)
        try:
            from tools.recovery import create_backup
            self.last_backup=create_backup(self.saved_path,self.root/'.local/backups',expected_sha256=self.saved_hash)
            self.backup_error=None
            self.log.emit('backup','BACKUP_VERIFIED',**self.last_backup)
        except Exception as error:
            self.backup_error=str(error);self.log.exception('backup',error)
        return dict(result,backup=self.last_backup if not self.backup_error else None,backupError=self.backup_error)

    def fingerprint(self):
        return dict(super().fingerprint(),reliabilityVersion='1.0.0',layoutScope='active page plus connected flow pages',nativeCompatibility='0.5.0 (M5) unchanged')

    def finish(self):
        if self.jobs: self.jobs.close()
        return super().finish()
