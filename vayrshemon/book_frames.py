"""Load native frame editors on demand; retain every page's serialized content."""
from collections import OrderedDict
from collections.abc import Mapping
from .frame import FrameSession


def loaded_items(frames):
    return frames.loaded.items() if isinstance(frames, BookFrames) else frames.items()


def loaded_values(frames):
    return frames.loaded.values() if isinstance(frames, BookFrames) else frames.values()


class BookFrames(Mapping):
    def __init__(self, owner, state):
        self.owner = owner
        self.state = state
        self.records = {f['frameId']: f for p in state['pages'] for f in p['frames']}
        self.loaded = OrderedDict()

    def __len__(self): return len(self.records)
    def __iter__(self): return iter(self.records)
    def __contains__(self, key): return key in self.records

    def __getitem__(self, key):
        if key not in self.loaded:
            record = self.records[key]
            owner = self.owner
            runtime = FrameSession(owner.root, owner.fonts, record['content'], owner.checks, self.state['features'])
            runtime.owner = owner
            runtime.changed.connect(owner.frame_changed)
            self.loaded[key] = runtime
        self.loaded.move_to_end(key)
        return self.loaded[key]

    def trim(self, keep=(), limit=16):
        keep = set(keep) | {self.state['activeFrameId']}
        for key in list(self.loaded):
            if len(self.loaded) <= limit: break
            if key in keep: continue
            runtime = self.loaded.pop(key)
            package = runtime.package()
            package['document']['documentId'] = self.state['documentId']
            package['document']['revision'] = 0
            self.records[key]['content'] = package
            cache = self.owner.__dict__.get('story_cache')
            if cache:
                for cache_key in list(cache.entries):
                    if cache_key[0] == key: cache.entries.pop(cache_key)
            runtime.editor = None
            runtime.deleteLater()
