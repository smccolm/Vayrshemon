"""Native text transactions for the Workbench's physical and touch keyboards."""
from contextlib import contextmanager

from .authoring import PACKAGE, stamp
from .json_stream import byte_count
from .paragraph_alignment import spread_frames
from .schema_validation import validate
from .typing_storage import FrameUndo, TypingBaseline, replace_frames, write_frame_checkpoint


def package(book, fid):
    native = book.frames[fid]
    book.ensure_block_ids(native)
    content = native.package()
    content['document'].update(documentId=book.state['documentId'], revision=0)
    return content


def restore_packages(book, contents):
    # load_package emits frame changes while reconstructing QTextDocuments.
    # The caller holds a transaction, so these cannot create extra undo steps.
    for fid, content in contents.items():
        native = book.frames[fid]
        native.load_package(content)
        native.insertion_format = None
    if book.__dict__.get('_typing_baseline') is not None:
        book._typing_baseline.line_metrics.clear()
    book.invalidate_composition()


def spread(book):
    try:
        return spread_frames(book)
    except ValueError:
        return []


def snapshot_changes(book, ids):
    baseline = book._typing_baseline
    changed, previous = {}, {}
    for fid in ids:
        p, f = baseline.locations[fid]
        frame = book._state['pages'][p]['frames'][f]
        new = package(book, fid)
        if new == frame['content']:
            continue
        validate(PACKAGE, new)
        book.validate_frame_content(dict(frame, content=new), book.state['documentId'])
        changed[fid], previous[fid] = new, frame['content']
    return changed, previous


def commit(book, label, changed, previous, selection, history_target, fonts_override=None, history_source=None):
    old = book._state
    baseline = book._typing_baseline
    active = book.state['activeFrameId']
    fonts = old['fontSources'] if fonts_override is None else fonts_override
    declared = {s['fontId'] for s in fonts}
    required = {font['fontId'] for c in changed.values() for font in c['document']['fonts']}
    if required - declared:
        fonts = fonts + [dict(fontId=fid, path=str(book.fonts.faces[fid].path),
                              sha256=book.fonts.faces[fid].sha256) for fid in sorted(required-declared)]
    if len(fonts) > book.state_schema['properties']['fontSources']['maxItems']:
        raise ValueError('FONT_SOURCE_LIMIT')
    current = replace_frames(old, baseline.locations, changed, active, fonts, book.revision+1)
    before_bytes = sum(map(byte_count, previous.values()))
    size = (baseline.size + sum(map(byte_count, changed.values())) - before_bytes
            + byte_count(fonts) - byte_count(old['fontSources'])
            + len(str(current['revision'])) - len(str(old['revision']))
            + len(active) - len(old['activeFrameId']))
    if size > book.max_state_bytes:
        raise ValueError('DOCUMENT_STATE_LIMIT')
    checksum = baseline.content_hash(current)
    if history_source is not None:
        history_source.pop()
    history_target.append(FrameUndo(previous, selection['frameId'] if selection else old['activeFrameId'], old['fontSources'], selection,
                                    before_bytes + byte_count(old['fontSources'])))
    if label not in ('Undo', 'Redo'):
        book._redo.clear()
    if history_target is book._undo:
        book.trim_undo()
    baseline.size = size
    book._state = current
    book.revision = current['revision']
    book.state['revision'] = book.revision
    book.history = (book.history + [dict(revision=book.revision, label=label,
                                        timestamp=stamp(), sha256=checksum)])[-256:]
    book._navigation_dirty = (book.revision, checksum != book._saved_digest)
    write_frame_checkpoint(book, changed)
    book.log.emit('document', 'REVISION_COMMITTED', revision=book.revision, label=label,
                  durableRevision=book.durable_revision)
    book.changed.emit()


class TypingEdits:
    def typing_baseline(self):
        if self.__dict__.get('_typing_baseline') is None:
            self._typing_baseline = TypingBaseline(self._state)
        return self._typing_baseline

    @contextmanager
    def typing_command(self, label='Typing', *, frame_ids=None):
        fid = self.state['activeFrameId']
        if self._depth or self.state.get('printEdition') or self.source_for(fid) != fid:
            with self.command(label):
                yield
            return
        baseline = self.typing_baseline()
        old_text = self.active.text()
        selection = self.selection()
        ids = list(frame_ids) if frame_ids is not None else [fid]
        self._editing_text_frames = True
        self._depth += 1
        try:
            yield
            if not self._pending:
                return
            if self.active.text() != old_text and not self.composing:
                group = spread(self)
                if group:
                    ids = group
                    self.align_groups([group])
            changed, previous = snapshot_changes(self, ids)
            if changed:
                if self.text_scalar_count() > self.max_document_scalars:
                    raise ValueError('DOCUMENT_LIMIT: total scalars')
                commit(self, label, changed, previous, selection, self._undo)
        except Exception:
            old = {}
            for frame_id in ids:
                p, f = baseline.locations[frame_id]
                old[frame_id] = self._state['pages'][p]['frames'][f]['content']
            restore_packages(self, old)
            self.restore_selection(selection)
            raise
        finally:
            self._editing_text_frames = False
            self._depth -= 1
            self._pending = False

    def history_move(self, redo=False):
        source, target = (self._redo, self._undo) if redo else (self._undo, self._redo)
        if not source or not isinstance(source[-1], FrameUndo):
            return super().history_move(redo)
        entry = source[-1]
        baseline = self.typing_baseline()
        selection = self.selection()
        old = self._state
        previous = {}
        for fid in entry.contents:
            p, f = baseline.locations[fid]
            previous[fid] = old['pages'][p]['frames'][f]['content']
        self._depth += 1
        try:
            restore_packages(self, entry.contents)
            self.select_frame(entry.active)
            self.restore_selection(entry.selection)
            commit(self, 'Redo' if redo else 'Undo', entry.contents, previous, selection, target,
                   fonts_override=entry.fonts, history_source=source)
        except Exception:
            restore_packages(self, previous)
            self.select_frame(old['activeFrameId'])
            self.restore_selection(selection)
            raise
        finally:
            self._depth -= 1
            self._pending = False
        return dict(revision=self.revision, undoAvailable=bool(self._undo), redoAvailable=bool(self._redo))
