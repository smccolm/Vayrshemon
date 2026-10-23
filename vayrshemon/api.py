"""Versioned commands and current-user-only local transport."""
from collections import OrderedDict
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import secrets
import time
import uuid

from jsonschema import Draft202012Validator
from PySide6.QtCore import QObject, QTimer
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtGui import QTextCursor

from tools.m0.common import load_json, write_json
from . import API_VERSION
from . import layout
from .diagnostics import CURRENT_TRACE


def obj(properties=None, required=()):
    return dict(type='object', properties=properties or {}, required=list(required), additionalProperties=False)


STRING = {'type': 'string'}
NUMBER = {'type': 'number'}
BOOL = {'type': 'boolean'}
OFFSET = {'type': 'integer', 'minimum': 0, 'maximum': 200000}
RANGE = dict(start=OFFSET, end=OFFSET)
METHODS = {
    'session.status': ('Inspect the current document, revision, capabilities and engine.', False, obj()),
    'document.read': ('Read the complete semantic document and source text.', False, obj()),
    'document.edit': ('Replace a UTF-16 range on grapheme boundaries. Revision and idempotency key are required.', True,
                      obj(dict(**RANGE, text={'type': 'string', 'maxLength': 100000}), ('start', 'end', 'text'))),
    'document.format': ('Set font, language and size for a range or the next typed text.', True,
                        obj(dict(**RANGE, font_id={'type': ['string', 'null']}, language={'type':'string','pattern':r'^language\.[A-Za-z0-9._-]+$'},
                                 size={'type':'number','minimum':1,'maximum':1000}, color={'type':'string','pattern':'^#[0-9a-fA-F]{8}$'}), ('start','end'))),
    'document.save': ('Atomically save a lab document; detects external changes and protects source files.', True, obj({'path': STRING}, ('path',))),
    'document.open': ('Open a validated lab document. Explicit discard is required for unsaved edits.', True,
                      obj({'path': STRING, 'discardUnsaved': BOOL}, ('path',))),
    'page.configure': ('Set independent physical page width and height.', True,
                       obj(dict(width=NUMBER, height=NUMBER, unit={'enum':['pt','mm','in']}), ('width','height'))),
    'history.undo': ('Undo the last text/format edit; page and lab settings are outside M1 text undo.', True, obj()),
    'history.redo': ('Redo a text/format edit.', True, obj()),
    'fonts.list': ('Inspect loaded font identities and the registered layer recipe.', False, obj()),
    'fonts.load': ('Privately load a local static TTF without a system font install.', True,
                   obj({'path':STRING, 'sha256':{'type':'string','pattern':'^[0-9a-f]{64}$'}}, ('path',))),
    'layout.inspect': ('Inspect glyph IDs, source clusters, positions, bounds, features and fallback.', False,
                       obj({'max_glyphs':{'type':'integer','minimum':1,'maximum':100000}})),
    'layout.hit-test': ('Map a point in 96-DPI document coordinates to a UTF-16 caret.', False, obj(dict(x=NUMBER,y=NUMBER), ('x','y'))),
    'render.png': ('Render the shared glyph layout to PNG, optionally a bounded tile for a huge page.', True,
                   obj(dict(path=STRING, mode={'enum':['mono','color']}, dpi={'type':'number','minimum':24,'maximum':1200},
                            region={'type':'array','items':NUMBER,'minItems':4,'maxItems':4},
                            overlays=obj(dict(baselines=BOOL,origins=BOOL,bounds=BOOL))), ('path',))),
    'view.configure': ('Control layer visibility, flat layer colors, preview mode, zoom and overlays.', True,
                       obj(dict(mode={'enum':['mono','color']}, baselines=BOOL, origins=BOOL, bounds=BOOL,
                                zoom={'type':'number','minimum':.1,'maximum':3}, layer={'type':'integer','minimum':0,'maximum':2},
                                enabled=BOOL, color={'type':'string','pattern':'^#[0-9a-fA-F]{6}$'}))),
    'features.configure': ('Toggle kerning and standard ligatures; reuses the same text source.', True, obj(dict(kern=BOOL,liga=BOOL))),
    'selection.set': ('Select a grapheme-aligned UTF-16 range in the live editor.', True, obj(RANGE, ('start','end'))),
    'ui.inspect': ('Read native accessibility, selection and UI state.', False, obj()),
    'ui.capture': ('Save a PNG of the lab widget for local troubleshooting.', True, obj({'path':STRING},('path',))),
    'reference.load': ('Display an image as a read-only visual reference.', True, obj({'path':STRING}, ('path',))),
    'diagnostics.tail': ('Read recent correlated diagnostics.', False, obj({'limit':{'type':'integer','minimum':1,'maximum':500}})),
}


class API:
    version = API_VERSION
    methods = METHODS
    def __init__(self, session):
        self.session = session
        self.requests = OrderedDict()

    def call(self, method, params=None, *, expected_revision=None, idempotency_key=None, origin='python', trace_id=None, document_id=None):
        session = self.session
        trace_id = trace_id or str(uuid.uuid4())
        trace_token = CURRENT_TRACE.set(trace_id)
        params = params or {}
        try:
            if method not in self.methods:
                raise ValueError('UNKNOWN_METHOD: ' + method)
            _, mutation, schema = self.methods[method]
            Draft202012Validator(schema).validate(params)
            digest = hashlib.sha256(json.dumps([method, params, expected_revision, document_id], sort_keys=True, allow_nan=False).encode()).hexdigest()
            if mutation:
                if origin == 'desktop' and not idempotency_key:
                    idempotency_key = uuid.uuid4().hex
                if not isinstance(idempotency_key, str) or not 1 <= len(idempotency_key) <= 128:
                    raise ValueError('IDEMPOTENCY_KEY_REQUIRED')
                if idempotency_key in self.requests:
                    previous_digest, previous_result = self.requests[idempotency_key]
                    if previous_digest != digest:
                        raise ValueError('IDEMPOTENCY_KEY_REUSED_WITH_DIFFERENT_REQUEST')
                    return deepcopy(previous_result)
                if len(self.requests) >= 4096:
                    raise ValueError('IDEMPOTENCY_CAPACITY: start a new session after saving; keys are never silently evicted')
                if origin in ('local-api','mcp') and document_id != session.model['documentId']:
                    raise ValueError('DOCUMENT_ID_MISMATCH: pass the documentId from session.status')
                if type(expected_revision) is not int or expected_revision != session.revision:
                    raise ValueError(f'STALE_REVISION: expected {expected_revision}, current {session.revision}')
                if session.composing:
                    raise ValueError('COMPOSITION_ACTIVE: finish or cancel native IME input first')
            session.log.emit('api', 'COMMAND_STARTED', trace_id=trace_id, method=method, origin=origin, revision=session.revision)
            started = time.perf_counter()
            value = self.dispatch(method, params)
            result = dict(ok=True, apiVersion=self.version, traceId=trace_id, sessionId=session.session_id,
                          revision=session.revision, result=value)
            if mutation:
                self.requests[idempotency_key] = digest, deepcopy(result)
            session.log.emit('api', 'COMMAND_COMPLETED', trace_id=trace_id, method=method,
                              revision=session.revision, elapsedMs=(time.perf_counter()-started)*1000)
            return result
        except Exception as error:
            session.log.exception('api', error, trace_id)
            return dict(ok=False, apiVersion=self.version, traceId=trace_id, sessionId=session.session_id,
                        revision=session.revision, error=dict(code=str(error).split(':')[0][:80], message=str(error)))
        finally:
            CURRENT_TRACE.reset(trace_token)

    def dispatch(self, method, params):
        s = self.session
        if method == 'session.status':
            return dict(sessionId=s.session_id, documentId=s.model['documentId'], revision=s.revision,
                        engine=s.fingerprint(), composing=s.composing, savedPath=str(s.saved_path) if s.saved_path else None,
                        logPath=str(s.log.path), capabilities=list(METHODS), transport='current-user QLocalServer + stdio MCP',
                        selection=self.selection())
        if method == 'document.read':
            return dict(document=s.snapshot(), text=s.text(), offsetUnit='utf16-code-unit')
        if method == 'document.edit':
            return s.edit(**params)
        if method == 'document.format':
            return s.format_range(**params)
        if method == 'page.configure':
            return s.set_page(**params)
        if method == 'document.save':
            return s.save(params['path'])
        if method == 'document.open':
            if s.revision > 0 and s.revision != s.saved_revision and not params.get('discardUnsaved', False):
                raise ValueError('UNSAVED_CHANGES: save first or pass discardUnsaved=true')
            return s.open(params['path'], advance_revision=True)
        if method in ('history.undo', 'history.redo'):
            getattr(s.doc, method.split('.')[1])()
            return dict(revision=s.revision, undoAvailable=s.doc.isUndoAvailable(), redoAvailable=s.doc.isRedoAvailable())
        if method == 'fonts.list':
            return dict(fonts=s.fonts.describe(), recipe=s.fonts.recipe)
        if method == 'fonts.load':
            face = s.fonts.register(params['path'], params.get('sha256'))
            s.changed.emit()
            return dict(fontId=face.font_id, family=face.original_family)
        if method == 'layout.inspect':
            return layout.inspect(s, **params)
        if method == 'layout.hit-test':
            return layout.hit_test(s, **params)
        if method == 'render.png':
            return layout.render(s, **params)[1]
        if method == 'diagnostics.tail':
            return dict(path=str(s.log.path), events=s.log.tail(params.get('limit', 100)))
        if method == 'selection.set':
            if not s.editor:
                raise ValueError('DESKTOP_REQUIRED')
            s.editor.setTextCursor(s.range_cursor(**params))
            s.editor.setFocus()
            return self.selection()
        if method == 'ui.inspect':
            from .desktop import accessibility
            return dict(desktop=bool(s.editor), selection=self.selection(), view=s.view,
                        accessibility=accessibility(s.editor) if s.editor else None)
        if method == 'ui.capture':
            if not s.window:
                raise ValueError('DESKTOP_REQUIRED')
            path=s.output_path(params['path'])
            if path.exists():
                raise ValueError('CAPTURE_TARGET_EXISTS')
            path.parent.mkdir(parents=True,exist_ok=True)
            if not s.window.grab().save(str(path),'PNG'):
                raise OSError('CAPTURE_FAILED')
            return dict(path=str(path),kind='Qt widget capture')
        if method == 'view.configure':
            values = dict(params)
            if 'layer' in values:
                if not s.fonts.recipe:
                    raise ValueError('NO_LAYER_RECIPE')
                layer = s.fonts.recipe['layers'][values.pop('layer')]
                for key in ('enabled', 'color'):
                    if key in values:
                        layer[key] = values.pop(key)
            elif 'enabled' in values or 'color' in values:
                raise ValueError('LAYER_INDEX_REQUIRED')
            s.view.update(values)
            s._contents_changed()
            return dict(view=s.view, recipe=s.fonts.recipe)
        if method == 'features.configure':
            s.features.update(params)
            # Reapply existing font formats in one native undo group.
            from .session import STYLE, LANGUAGE, KIND, SOURCE, MAPPING, RUN
            formats = list(s.spans())
            with s.transaction():
                for start, length, text, fmt in formats:
                    old = next(style for style in s.model['styles'] if style['styleId'] == fmt.property(STYLE))
                    style = deepcopy(old)
                    style.pop('styleId')
                    style['styleId'] = 'style.' + hashlib.sha256(json.dumps([style,s.features],sort_keys=True).encode()).hexdigest()[:16]
                    if style['styleId'] not in {v['styleId'] for v in s.model['styles']}:
                        s.model['styles'].append(style)
                    s.style_features[style['styleId']] = deepcopy(s.features)
                    run = dict(runId=fmt.property(RUN), styleId=style['styleId'], languageId=fmt.property(LANGUAGE), type=fmt.property(KIND))
                    if run['type'] == 'legacy':
                        run.update(sourceFontSha256=fmt.property(SOURCE),mappingProfileRef=json.loads(fmt.property(MAPPING)))
                    s.range_cursor(start, start+length, grapheme=False).setCharFormat(s.format_for(run))
            return dict(features=s.features, revision=s.revision)
        if method == 'reference.load':
            if not s.window:
                raise ValueError('DESKTOP_REQUIRED')
            s.window.set_reference(params['path'])
            return dict(path=params['path'])
        raise ValueError('UNIMPLEMENTED_METHOD')

    def selection(self):
        if not self.session.editor:
            return None
        c = self.session.editor.textCursor()
        return dict(start=c.selectionStart(), end=c.selectionEnd(), caret=c.position(), offsetUnit='utf16-code-unit')


class LocalServer(QObject):
    """A bounded, non-web transport. All commands execute on the Qt GUI thread."""
    def __init__(self, api, *, publish=True):
        super().__init__()
        self.api = api
        self.server = QLocalServer(self)
        self.server.setSocketOptions(QLocalServer.SocketOption.UserAccessOption)
        self.name = 'Vayrshemon-' + api.session.session_id
        self.token = secrets.token_hex(32)
        if not self.server.listen(self.name):
            raise OSError(self.server.errorString())
        self.clients = {}
        self.publish = publish
        self.server.newConnection.connect(self.connected)
        folder = api.session.root / '.local/run'
        self.descriptor = folder / (api.session.session_id + '.json')
        self.active = folder / 'active.json'
        payload = dict(apiVersion=api.version, sessionId=api.session.session_id, serverName=self.name, token=self.token, pid=os.getpid())
        self.previous_active = load_json(self.active) if self.active.exists() else None
        write_json(self.descriptor, payload)
        if publish:
            write_json(self.active, payload)
        if os.name != 'nt':
            self.descriptor.chmod(0o600)
            if publish:
                self.active.chmod(0o600)
        api.session.transport_active = True
        api.session.changed.emit()
        api.session.log.emit('transport', 'LOCAL_API_LISTENING', serverName=self.name,
                             descriptor=str(self.descriptor), access='operating-system-current-user-only')

    def connected(self):
        while self.server.hasPendingConnections():
            socket = self.server.nextPendingConnection()
            if len(self.clients) >= 16:
                socket.abort()
                socket.deleteLater()
                continue
            socket.setReadBufferSize(1_048_577)
            self.clients[socket] = bytearray()
            socket.readyRead.connect(lambda sock=socket: self.read(sock))
            socket.disconnected.connect(lambda sock=socket: self.release(sock))
            timer = QTimer(socket)
            timer.setSingleShot(True)
            timer.timeout.connect(socket.abort)
            timer.start(15000)

    def release(self, socket):
        self.clients.pop(socket, None)
        socket.deleteLater()

    def read(self, socket):
        buffer = self.clients.get(socket)
        if buffer is None:
            return
        buffer.extend(bytes(socket.readAll()))
        if len(buffer) > 1_048_576:
            socket.abort()
            return
        if b'\n' not in buffer:
            return
        try:
            request = json.loads(bytes(buffer).decode('utf-8'), parse_constant=lambda value: (_ for _ in ()).throw(ValueError('NONFINITE_JSON')))
            if not isinstance(request, dict) or not secrets.compare_digest(str(request.get('token', '')), self.token):
                raise ValueError('UNAUTHORIZED')
            if request.get('apiVersion') != self.api.version or request.get('sessionId') != self.api.session.session_id:
                raise ValueError('SESSION_OR_API_VERSION_MISMATCH')
            result = self.api.call(request['method'], request.get('params'), expected_revision=request.get('expectedRevision'),
                                   idempotency_key=request.get('idempotencyKey'), origin='local-api', trace_id=request.get('traceId'),
                                   document_id=request.get('documentId'))
        except Exception as error:
            result = dict(ok=False, error=dict(code='INVALID_TRANSPORT_REQUEST', message=str(error)))
        socket.write(json.dumps(result, ensure_ascii=True, allow_nan=False).encode()+b'\n')
        socket.disconnectFromServer()

    def close(self):
        self.api.session.transport_active = False
        self.server.close()
        for socket in list(self.clients):
            socket.abort()
        if self.descriptor.exists():
            self.descriptor.unlink()
        if self.active.exists() and load_json(self.active).get('sessionId') == self.api.session.session_id:
            previous = self.previous_active
            if previous and (self.active.parent/(previous['sessionId']+'.json')).exists():
                write_json(self.active,previous)
            else:
                self.active.unlink()


def remote_call(root, method, params=None, *, expected_revision=None, idempotency_key=None, descriptor=None, document_id=None):
    from PySide6.QtCore import QCoreApplication
    app = QCoreApplication.instance() or QCoreApplication([])
    info = load_json(Path(descriptor) if descriptor else Path(root)/'.local/run/active.json')
    if info.get('apiVersion') not in ('0.2.0','0.3.0','0.4.0'):
        raise ValueError('API_VERSION_MISMATCH')
    socket = QLocalSocket()
    socket.connectToServer(info['serverName'])
    if not socket.waitForConnected(5000):
        raise ConnectionError('No live lab session: ' + socket.errorString())
    request = dict(apiVersion=info['apiVersion'], sessionId=info['sessionId'], token=info['token'], method=method,
                   params=params or {}, expectedRevision=expected_revision, idempotencyKey=idempotency_key,
                   traceId=str(uuid.uuid4()), documentId=document_id)
    socket.write(json.dumps(request, ensure_ascii=True, allow_nan=False).encode()+b'\n')
    if not socket.waitForBytesWritten(5000):
        raise ConnectionError('LOCAL_API_WRITE_FAILED')
    data = bytearray()
    deadline = time.monotonic() + 30
    while b'\n' not in data:
        if socket.bytesAvailable() or socket.waitForReadyRead(max(1, int((deadline-time.monotonic())*1000))):
            data.extend(bytes(socket.readAll()))
        if len(data) > 32*1024*1024:
            raise ValueError('LOCAL_API_RESPONSE_TOO_LARGE')
        if time.monotonic() >= deadline or socket.state() == QLocalSocket.LocalSocketState.UnconnectedState:
            if b'\n' not in data:
                raise TimeoutError('LOCAL_API_RESPONSE_TIMEOUT')
    socket.disconnectFromServer()
    return json.loads(data)
