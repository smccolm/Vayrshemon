"""Bounded serialization chunks for native books without changing JSON values.

The large array is pages, not individual characters. Each page uses the fast
standard encoder; a whole-book string and its second encoded copy are avoided.
Canonical hashing retains the exact historical json.dumps byte convention.
"""
import hashlib
import json


def chunks(value, *, compact=False, sort_keys=False):
    options = dict(ensure_ascii=True, allow_nan=False, sort_keys=sort_keys)
    if compact:
        options['separators'] = (',', ':')
    item_separator, key_separator = (',', ':') if compact else (', ', ': ')

    def encode(item):
        return json.dumps(item, **options)

    def emit(item, *, split_list=False):
        if isinstance(item, dict):
            if any(not isinstance(key, str) for key in item):
                # Preserve the standard encoder's key coercion/error behavior
                # for generic digest callers outside the native state schema.
                yield encode(item)
                return
            yield '{'
            keys = sorted(item) if sort_keys else item
            first = True
            for key in keys:
                if not first:
                    yield item_separator
                first = False
                yield encode(key)
                yield key_separator
                child = item[key]
                if key == 'state' and isinstance(child, dict):
                    yield from emit(child)
                elif key == 'pages' and isinstance(child, list):
                    yield from emit(child, split_list=True)
                else:
                    yield encode(child)
            yield '}'
        elif split_list:
            yield '['
            for index, child in enumerate(item):
                if index:
                    yield item_separator
                yield encode(child)
            yield ']'
        else:
            yield encode(item)

    for part in emit(value):
        yield part.encode('ascii')


def byte_count(value, *, limit=None):
    total = 0
    for part in chunks(value, compact=True):
        total += len(part)
        if limit is not None and total > limit:
            raise ValueError('JSON_BYTE_LIMIT')
    return total


def canonical_digest(value):
    result = hashlib.sha256()
    for part in chunks(value, sort_keys=True):
        result.update(part)
    return result.hexdigest()


def compact_digest(value):
    result = hashlib.sha256()
    for part in chunks(value, compact=True, sort_keys=True):
        result.update(part)
    return result.hexdigest()


def write_atomic(path, value, *, replace=True, limit=None):
    """Publish only a complete bounded JSON stream, preserving existing targets."""
    import os
    from pathlib import Path
    import tempfile
    from tools.recovery import publish_new
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.name + '.', suffix='.tmp', dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, 'wb') as stream:
            total = 0
            for part in chunks(value, compact=True):
                total += len(part)
                if limit is not None and total > limit:
                    raise ValueError('DOCUMENT_TOO_LARGE')
                stream.write(part)
            stream.flush()
            os.fsync(stream.fileno())
        if replace:
            temporary.replace(path)
        else:
            publish_new(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
