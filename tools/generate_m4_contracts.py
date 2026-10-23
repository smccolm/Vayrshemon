"""Publish M4 contracts, retaining every earlier milestone interface."""
from pathlib import Path
from tools.m0.common import write_json
from vayrshemon.api import obj
from vayrshemon.studio_api import METHODS,StudioAPI
from vayrshemon.studio_contracts import DOCUMENT
from vayrshemon.mcp import tools


def generate(root):
    root=Path(root);variants=[]
    for method,(description,mutation,params) in METHODS.items():
        fields=dict(apiVersion={'const':StudioAPI.version},method={'const':method},params=params)
        required=['apiVersion','method','params']
        if mutation:
            fields.update(documentId={'type':'string'},expectedRevision={'type':'integer','minimum':0},idempotencyKey={'type':'string','minLength':1,'maxLength':128})
            required+=['documentId','expectedRevision','idempotencyKey']
        variants.append(dict(obj(fields,required),description=description))
    write_json(root/'schemas/studio-command.schema.json',{'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:vayrshemon:schema:studio-command:0.5.0','oneOf':variants})
    write_json(root/'schemas/studio-document.schema.json',DOCUMENT)
    write_json(root/'data/studio-mcp-tools.json',dict(apiVersion=StudioAPI.version,protocolVersion='2024-11-05',tools=tools(METHODS)))
    write_json(root/'data/studio-capabilities.json',dict(schemaVersion='0.1.0',apiVersion=StudioAPI.version,milestone='M4',
        capabilities=[dict(method=m,description=d,mutation=mutation,transports=['python','cli','desktop','mcp'],requiresDesktop=m in ('ui.capture','selection.set')) for m,(d,mutation,_) in METHODS.items()]))


if __name__=='__main__': generate(Path(__file__).resolve().parents[1])
