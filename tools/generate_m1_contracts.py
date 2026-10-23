"""Regenerate published laboratory file/API and MCP discovery contracts."""
from pathlib import Path

from tools.m0.common import write_json
from vayrshemon.api import METHODS, obj
from vayrshemon.contracts import LAB_DOCUMENT
from vayrshemon.mcp import tools
from vayrshemon import API_VERSION


def generate(root):
    root = Path(root)
    variants = []
    for method, (description, mutation, params) in METHODS.items():
        fields = dict(apiVersion={'const':API_VERSION}, method={'const':method}, params=params)
        required = ['apiVersion','method','params']
        if mutation:
            fields.update(documentId={'type':'string'}, expectedRevision={'type':'integer','minimum':0},
                          idempotencyKey={'type':'string','minLength':1,'maxLength':128})
            required += ['documentId','expectedRevision','idempotencyKey']
        variants.append(dict(obj(fields,required), description=description))
    schema = {'$schema':'https://json-schema.org/draft/2020-12/schema',
              '$id':'urn:vayrshemon:schema:lab-command:0.2.0','oneOf':variants}
    write_json(root/'schemas/lab-command.schema.json',schema)
    write_json(root/'schemas/lab-document.schema.json',LAB_DOCUMENT)
    write_json(root/'data/mcp-tools.json',dict(apiVersion=API_VERSION,protocolVersion='2024-11-05',tools=tools()))
    write_json(root/'data/lab-capabilities.json',dict(schemaVersion='0.1.0',apiVersion=API_VERSION,milestone='M1',
        capabilities=[dict(method=method,description=description,mutation=mutation,transports=['python','cli','desktop','mcp'],
                           requiresDesktop=method in ('ui.capture','selection.set','reference.load'))
                      for method,(description,mutation,_) in METHODS.items()]))


if __name__=='__main__':
    generate(Path(__file__).resolve().parents[1])
