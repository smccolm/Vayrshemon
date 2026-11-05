"""Versioned compressed storage for the unchanged native 0.6 editable state.

The outer JSON keeps the existing shellPreview available without decompressing
document content. Both compressed and expanded sizes are bounded; a checksum
and exact stream termination are checked before the ordinary state validator.
"""
import base64
import hashlib
import json
import re
import zlib
from .json_stream import chunks

WIRE_VERSION = '0.7.0'
LOGICAL_VERSION = '0.6.0'
MAX_EXPANDED_BYTES = 1536 * 1024 * 1024
MAX_COMPRESSED_BYTES = 256 * 1024 * 1024
MAX_FILE_BYTES = 384 * 1024 * 1024
ENCODING_KEYS = {'codec', 'expandedBytes', 'sha256', 'data'}
WIRE_KEYS = {'shellPreview', 'format', 'formatVersion', 'stateEncoding', 'history', 'engine'}


def pack(payload, *, expanded_limit=MAX_EXPANDED_BYTES, compressed_limit=MAX_COMPRESSED_BYTES):
    if payload.get('format') != 'vayrshemon.document' or payload.get('formatVersion') != LOGICAL_VERSION:
        raise ValueError('PACKED_NATIVE_LOGICAL_VERSION')
    if set(payload) - (WIRE_KEYS - {'stateEncoding'} | {'state'}):
        raise ValueError('PACKED_NATIVE_UNKNOWN_FIELD')
    if not isinstance(payload.get('state'), dict):
        raise ValueError('PACKED_NATIVE_STATE_REQUIRED')
    compressor = zlib.compressobj(3)
    digest = hashlib.sha256()
    parts, expanded, compressed = [], 0, 0
    for chunk in chunks(payload['state'], compact=True):
        expanded += len(chunk)
        if expanded > expanded_limit:
            raise ValueError('PACKED_STATE_EXPANDED_LIMIT')
        digest.update(chunk)
        part = compressor.compress(chunk)
        compressed += len(part)
        if compressed > compressed_limit:
            raise ValueError('PACKED_STATE_COMPRESSED_LIMIT')
        parts.append(part)
    parts.append(compressor.flush())
    if sum(map(len, parts)) > compressed_limit:
        raise ValueError('PACKED_STATE_COMPRESSED_LIMIT')
    encoding = dict(codec='zlib-json-v1', expandedBytes=expanded,
                    sha256=digest.hexdigest(), data=base64.b64encode(b''.join(parts)).decode('ascii'))
    # Preserve the preview first for bounded native-shell header reading.
    wire = {}
    if 'shellPreview' in payload:
        wire['shellPreview'] = payload['shellPreview']
    wire.update(format='vayrshemon.document', formatVersion=WIRE_VERSION, stateEncoding=encoding,
                history=payload.get('history', []), engine=payload.get('engine', {}))
    return wire


def unpack(payload, *, expanded_limit=MAX_EXPANDED_BYTES, compressed_limit=MAX_COMPRESSED_BYTES):
    if not isinstance(payload, dict) or payload.get('format') != 'vayrshemon.document' or payload.get('formatVersion') != WIRE_VERSION:
        return payload
    if set(payload) - WIRE_KEYS or not {'format','formatVersion','stateEncoding','history','engine'} <= set(payload):
        raise ValueError('PACKED_NATIVE_FIELDS')
    encoded = payload['stateEncoding']
    if not isinstance(encoded, dict) or set(encoded) != ENCODING_KEYS or encoded.get('codec') != 'zlib-json-v1':
        raise ValueError('PACKED_STATE_CODEC')
    expected = encoded['expandedBytes']
    if type(expected) is not int or not 1 <= expected <= expanded_limit:
        raise ValueError('PACKED_STATE_EXPANDED_LIMIT')
    checksum = encoded['sha256']
    if not isinstance(checksum, str) or not re.fullmatch('[0-9a-f]{64}', checksum):
        raise ValueError('PACKED_STATE_CHECKSUM_FORMAT')
    text = encoded['data']
    if not isinstance(text, str) or len(text) > 4 * ((compressed_limit + 2) // 3):
        raise ValueError('PACKED_STATE_COMPRESSED_LIMIT')
    try:
        packed = base64.b64decode(text, validate=True)
    except (ValueError, TypeError) as error:
        raise ValueError('PACKED_STATE_BASE64') from error
    if not packed or len(packed) > compressed_limit:
        raise ValueError('PACKED_STATE_COMPRESSED_LIMIT')
    decoder = zlib.decompressobj()
    try:
        raw = decoder.decompress(packed, expected + 1)
    except zlib.error as error:
        raise ValueError('PACKED_STATE_ZLIB') from error
    if len(raw) > expected or decoder.unconsumed_tail:
        raise ValueError('PACKED_STATE_EXPANDED_LIMIT')
    if not decoder.eof or decoder.unused_data or len(raw) != expected:
        raise ValueError('PACKED_STATE_STREAM_LENGTH')
    if hashlib.sha256(raw).hexdigest() != checksum:
        raise ValueError('PACKED_STATE_CHECKSUM_MISMATCH')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('DUPLICATE_JSON_KEY: ' + key)
            result[key] = value
        return result
    def constant(value):
        raise ValueError('NONFINITE_JSON_NUMBER: ' + value)
    state = json.loads(raw, object_pairs_hook=unique, parse_constant=constant)
    if not isinstance(state, dict):
        raise ValueError('PACKED_NATIVE_STATE_REQUIRED')
    logical = {key:value for key,value in payload.items() if key != 'stateEncoding'}
    logical.update(formatVersion=LOGICAL_VERSION, state=state)
    return logical


def storage_payload(payload):
    """Small/legacy files stay ordinary JSON; native books use a bounded envelope."""
    state = payload.get('state', {})
    if not isinstance(state, dict) or len(state.get('pages', [])) < 100:
        return payload
    if payload.get('format') == 'vayrshemon.document' and payload.get('formatVersion') == LOGICAL_VERSION:
        return pack(payload)
    if payload.get('recoveryVersion') == '0.1.0':
        packed = pack(dict(format='vayrshemon.document', formatVersion=LOGICAL_VERSION,
                           state=state, history=[], engine={}))
        result = {key:value for key,value in payload.items() if key != 'state'}
        result.update(recoveryVersion='0.2.0', stateEncoding=packed['stateEncoding'])
        return result
    return payload


def logical_payload(payload):
    if isinstance(payload, dict) and payload.get('recoveryVersion') == '0.2.0':
        if 'state' in payload:
            raise ValueError('RECOVERY_DUPLICATE_STATE')
        native = unpack(dict(format='vayrshemon.document', formatVersion=WIRE_VERSION,
                             stateEncoding=payload.get('stateEncoding'), history=[], engine={}))
        result = {key:value for key,value in payload.items() if key != 'stateEncoding'}
        result.update(recoveryVersion='0.1.0', state=native['state'])
        return result
    return unpack(payload)
