"""MCP 2024-11-05 stdio adapter; one shared API, no second editor model."""
import json
import sys

from . import __version__
from .api import METHODS, remote_call


def tools(methods=None):
    methods = methods or METHODS
    result = []
    for method, (description, mutation, schema) in methods.items():
        properties = dict(schema['properties'])
        required = list(schema['required'])
        if mutation:
            properties.update(expectedRevision={'type':'integer','minimum':0}, idempotencyKey={'type':'string','minLength':1,'maxLength':128}, documentId={'type':'string'})
            required += ['expectedRevision', 'idempotencyKey', 'documentId']
        result.append(dict(name=method.replace('.', '_').replace('-', '_'), description=description,
                           inputSchema=dict(type='object', properties=properties, required=required, additionalProperties=False)))
    return result


def serve(root, api=None, descriptor=None, methods=None):
    initialized = False
    negotiated = False
    methods = methods or (api.methods if api else METHODS)
    names = {method.replace('.', '_').replace('-', '_'): method for method in methods}
    while True:
        raw = sys.stdin.buffer.readline(1_048_578)
        if not raw:
            return
        identity = None
        try:
            if len(raw) > 1_048_576 or not raw.endswith(b'\n'):
                raise ValueError('MCP message exceeds 1 MiB or lacks its newline delimiter')
            request = json.loads(raw, parse_constant=lambda v: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))
            if not isinstance(request, dict) or request.get('jsonrpc') != '2.0' or not isinstance(request.get('method'), str):
                raise ValueError('Invalid JSON-RPC request')
            identity = request.get('id')
            method, params = request['method'], request.get('params', {})
            if method == 'notifications/initialized':
                initialized = negotiated
                continue
            if 'id' not in request:
                continue
            if method == 'initialize':
                negotiated = True
                result = dict(protocolVersion='2024-11-05', capabilities={'tools':{'listChanged':False}},
                              serverInfo={'name':'vayrshemon','version':__version__},
                              instructions='Read session_status before mutation. UTF-16 ranges follow grapheme boundaries. Use fresh idempotency keys and the current revision.')
            elif method == 'ping':
                result = {}
            elif not initialized:
                raise ValueError('Client must initialize and send notifications/initialized first')
            elif method == 'tools/list':
                result = {'tools':tools(methods)}
            elif method == 'tools/call':
                name = params.get('name')
                if name not in names:
                    raise KeyError('Unknown tool: ' + str(name))
                arguments = dict(params.get('arguments', {}))
                expected = arguments.pop('expectedRevision', None)
                key = arguments.pop('idempotencyKey', None)
                document_id = arguments.pop('documentId', None)
                try:
                    if api:
                        value = api.call(names[name], arguments, expected_revision=expected, idempotency_key=key, origin='mcp', document_id=document_id)
                    else:
                        value = remote_call(root, names[name], arguments, expected_revision=expected,
                                            idempotency_key=key, descriptor=descriptor, document_id=document_id)
                    result = dict(content=[dict(type='text', text=json.dumps(value, ensure_ascii=True))], isError=not value['ok'])
                except Exception as error:
                    result = dict(content=[dict(type='text', text=str(error))], isError=True)
            else:
                raise KeyError('Method not found: ' + method)
            response = dict(jsonrpc='2.0', id=identity, result=result)
        except Exception as error:
            code = -32700 if isinstance(error, (json.JSONDecodeError, UnicodeDecodeError)) else -32601 if isinstance(error, KeyError) else -32600
            response = dict(jsonrpc='2.0', id=identity, error=dict(code=code, message=str(error)))
            print(json.dumps(dict(component='mcp', code='PROTOCOL_ERROR', message=str(error))), file=sys.stderr, flush=True)
        print(json.dumps(response, ensure_ascii=True, allow_nan=False), flush=True)
