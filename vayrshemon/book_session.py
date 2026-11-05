"""Large native books use the same editing/painting pipeline, with lazy frames."""
from contextlib import contextmanager
import re
from PySide6.QtCore import QTextBoundaryFinder
from .authoring import digest
from .book_frames import BookFrames, loaded_items

from .native_storage import MAX_EXPANDED_BYTES as MAX_STATE_BYTES, MAX_FILE_BYTES

MAX_PAGES = 32768
MAX_FRAMES = 65536
MAX_SCALARS = 32_000_000


class BookSession:
    lazy_book_frames = True
    max_frames = MAX_FRAMES
    max_document_scalars = MAX_SCALARS
    max_state_bytes = MAX_STATE_BYTES
    max_file_bytes = MAX_FILE_BYTES

    def validate(self, state):
        signature = digest(state) if len(state.get('pages', [])) > 100 else None
        if signature and signature == self.__dict__.get('_validated_book'): return
        super().validate(state)
        self._validated_book = signature

    def _restore(self, state, **kwargs):
        self._navigation_dirty = None
        return super()._restore(state, **kwargs)

    @property
    def dirty(self):
        cached = self.__dict__.get('_navigation_dirty')
        if cached and cached[0] == self.revision: return cached[1]
        return super().dirty

    @contextmanager
    def command(self, label):
        self._navigation_dirty = None
        with super().command(label): yield

    def frame_changed(self):
        self._navigation_dirty = None
        return super().frame_changed()

    def commit(self, label):
        self._navigation_dirty = None
        result = super().commit(label)
        if isinstance(self.frames, BookFrames):
            self._navigation_dirty = (self.revision, self._saved_digest != self.content_digest(self._state))
        return result

    def save(self, *args, **kwargs):
        self._navigation_dirty = None
        result = super().save(*args, **kwargs)
        if isinstance(self.frames, BookFrames): self._navigation_dirty = (self.revision, False)
        return result

    def open(self, *args, **kwargs):
        result = super().open(*args, **kwargs)
        if isinstance(self.frames, BookFrames): self._navigation_dirty = (self.revision, bool(self.migrated_from))
        return result

    def navigate_frame(self, frame_id):
        # Selecting a page changes only the guard clock and reading position.
        # Never serialize a complete book/recovery snapshot on each page turn.
        dirty = self.dirty
        result = self.select_frame(frame_id)
        self.revision += 1
        self.state['revision'] = self.revision
        self._state['revision'] = self.revision
        self._state['activeFrameId'] = frame_id
        self._navigation_dirty = (self.revision, dirty)
        self.changed.emit()
        self.frames.trim()
        return result

    def composition(self, mode=None, page_id=None):
        result = super().composition(mode, page_id)
        if isinstance(self.frames, BookFrames):
            keep = {fid for comp in self._composition_cache.values() for fid in comp.frames}
            self.frames.trim(keep)
        return result

    def text_scalar_count(self):
        from .automatic_alignment import text_of
        loaded = dict(loaded_items(self.frames))
        return sum(len(loaded[f['frameId']].text()) if f['frameId'] in loaded else len(text_of(f))
                   for p in self.state['pages'] for f in p['frames'])

    def find(self, text, case_sensitive=False, whole_word=False, all_frames=True):
        if not isinstance(self.frames, BookFrames):
            return super().find(text, case_sensitive, whole_word, all_frames)
        from .automatic_alignment import text_of
        from .session import utf16_length
        if not text: raise ValueError('EMPTY_SEARCH')
        pattern = re.escape(text)
        if whole_word: pattern = r'(?<!\w)' + pattern + r'(?!\w)'
        regex = re.compile(pattern, 0 if case_sensitive else re.IGNORECASE)
        matches = []
        for fid, record in self.frames.records.items():
            if not all_frames and fid != self.state['activeFrameId']: continue
            native = self.frames.loaded.get(fid)
            source = native.text() if native else text_of(record)
            boundaries = QTextBoundaryFinder(QTextBoundaryFinder.BoundaryType.Grapheme, source)
            for match in regex.finditer(source):
                start, end = utf16_length(source[:match.start()]), utf16_length(source[:match.end()])
                boundaries.setPosition(start)
                if not boundaries.isAtBoundary(): continue
                boundaries.setPosition(end)
                if not boundaries.isAtBoundary(): continue
                matches.append(dict(frameId=fid, start=start, end=end, text=match.group()))
                if len(matches) >= 10000: raise ValueError('SEARCH_RESULT_LIMIT: narrow the search')
        return dict(matches=matches, count=len(matches))
