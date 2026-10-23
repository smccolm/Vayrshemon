"""Visible, correlated diagnostics. Never put protocol data on stderr."""
from collections import deque
from contextvars import ContextVar
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import threading
import traceback
import uuid

CURRENT_TRACE = ContextVar('vayrshemon_trace', default=None)


class Diagnostics:
    def __init__(self, root, session_id):
        self.session_id = session_id
        self.path = Path(root) / '.local/logs' / (session_id + '.jsonl')
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.events = deque(maxlen=500)
        self.lock = threading.Lock()

    def emit(self, component, code, *, trace_id=None, level='info', **details):
        event = dict(timestamp=datetime.now(timezone.utc).isoformat(), sessionId=self.session_id,
                     traceId=trace_id or CURRENT_TRACE.get() or str(uuid.uuid4()), component=component,
                     code=code, level=level, **details)
        line = json.dumps(event, ensure_ascii=True, allow_nan=False)
        with self.lock:
            self.events.append(event)
            with self.path.open('a', encoding='utf-8') as stream:
                stream.write(line + '\n')
            print(line, file=sys.stderr, flush=True)
        return event

    def exception(self, component, error, trace_id=None):
        return self.emit(component, 'EXCEPTION', trace_id=trace_id, level='error',
                         message=str(error), traceback=traceback.format_exc())

    def tail(self, limit=100):
        with self.lock:
            return list(self.events)[-max(1, min(limit, 500)):]
