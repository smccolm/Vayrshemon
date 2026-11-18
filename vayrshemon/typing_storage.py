"""Frame-level undo and crash checkpoints for native keyboard edits."""
from dataclasses import dataclass
from hashlib import sha256
import json

from tools.m0.common import load_json
from .json_stream import byte_count, canonical_digest, write_atomic


def frame_locations(state):
    return {frame['frameId']: (p, f) for p, page in enumerate(state['pages'])
            for f, frame in enumerate(page['frames'])}


def replace_frames(state, locations, contents, active, fonts, revision):
    """Copy only changed branches. Committed frame packages are immutable."""
    pages = state['pages'].copy()
    copied = set()
    for fid, content in contents.items():
        p, f = locations[fid]
        if p not in copied:
            pages[p] = dict(pages[p], frames=pages[p]['frames'].copy())
            copied.add(p)
        frames = pages[p]['frames']
        frames[f] = dict(frames[f], content=content)
    return dict(state, pages=pages, activeFrameId=active, fontSources=fonts, revision=revision)


@dataclass
class FrameUndo:
    contents: dict
    active: str
    fonts: list
    selection: dict | None
    size: int


class TypingBaseline:
    def __init__(self, state):
        self.locations = frame_locations(state)
        self.line_metrics = {}
        self.size = byte_count(state)
        # Preserve the existing history SHA-256 byte for byte. In canonical
        # key order the large language graph precedes pages. SHA.copy() lets
        # every text edit reuse the hash of that already-validated prefix.
        fields = sorted(set(state) - {'revision', 'activeFrameId'})
        # Inserting the first character in a new font can extend fontSources.
        self.before_pages = fields[:fields.index('pages')]
        self.after_pages = fields[fields.index('pages')+1:]
        self.fonts = None
        self.rebuild_prefix(state)

    def rebuild_prefix(self, state):
        self.prefix = sha256(b'{')
        for key in self.before_pages:
            self.prefix.update(json.dumps(key).encode('ascii') + b': ')
            self.prefix.update(json.dumps(state[key], sort_keys=True, allow_nan=False).encode('ascii'))
            self.prefix.update(b', ')
        self.prefix.update(b'"pages": [')
        self.fonts = state['fontSources']

    def content_hash(self, state):
        if self.fonts != state['fontSources']:
            self.rebuild_prefix(state)
        result = self.prefix.copy()
        for i, page in enumerate(state['pages']):
            if i:
                result.update(b', ')
            result.update(json.dumps(page, sort_keys=True, allow_nan=False).encode('ascii'))
        result.update(b']')
        for key in self.after_pages:
            result.update(b', ')
            result.update(json.dumps(key).encode('ascii') + b': ')
            result.update(json.dumps(state[key], sort_keys=True, allow_nan=False).encode('ascii'))
        result.update(b'}')
        return result.hexdigest()


def write_frame_checkpoint(book, contents):
    if not book.recovery_enabled:
        return
    if not book.__dict__.get('_checkpoint_id') or book.recovery_error:
        book.checkpoint(snapshot=book._state)
        return
    changed = {**book._checkpoint_frames, **contents}
    data = dict(checkpointId=book._checkpoint_id, revision=book.revision,
                activeFrameId=book._state['activeFrameId'], frames=changed,
                fontSources=book._state['fontSources'], history=book.history)
    # Bound the sidecar when editing many different spreads. Publishing a new
    # base atomically changes its generation before its old sidecar is removed.
    if byte_count(data) > min(4 * 1024 * 1024, book.max_file_bytes):
        book.checkpoint(snapshot=book._state)
        return
    try:
        write_atomic(book.recovery_path.with_suffix('.typing'),
                     dict(data=data, sha256=canonical_digest(data)), limit=book.max_file_bytes)
        book._checkpoint_frames = changed
        book.durable_revision = book.revision
    except Exception as error:
        book.recovery_error = str(error)
        book.log.exception('recovery', error)


def read_checkpoint(path, limit):
    base = load_json(path)
    sidecar = path.with_suffix('.typing')
    if base.get('closed') or not base.get('checkpointId') or not sidecar.exists():
        return base
    if sidecar.stat().st_size > limit:
        raise ValueError('RECOVERY_TOO_LARGE')
    delta = load_json(sidecar)
    data = delta['data']
    if canonical_digest(data) != delta['sha256']:
        raise ValueError('RECOVERY_HASH_MISMATCH')
    if data['checkpointId'] != base['checkpointId']:
        return base
    if canonical_digest(base['state']) != base['sha256']:
        raise ValueError('RECOVERY_HASH_MISMATCH')
    state = replace_frames(base['state'], frame_locations(base['state']), data['frames'],
                           data['activeFrameId'], data['fontSources'], data['revision'])
    return dict(base, state=state, sha256=canonical_digest(state), history=data['history'],
                timestamp=data['history'][-1]['timestamp'])
