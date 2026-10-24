"""Publish M14 file/API/MCP contracts without changing earlier contracts."""
from pathlib import Path
from tools.m0.common import write_json
from vayrshemon.api import obj
from vayrshemon.file_api import METHODS,FileAPI
from vayrshemon.file_contracts import DOCUMENT
from vayrshemon.mcp import tools


def generate(root):
    root=Path(root);variants=[]
    write_json(root/'schemas/file-document.schema.json',DOCUMENT)
    for method,(description,mutation,params) in METHODS.items():
        fields=dict(apiVersion={'const':FileAPI.version},method={'const':method},params=params);required=['apiVersion','method','params']
        if mutation:
            fields.update(documentId={'type':'string'},expectedRevision={'type':'integer','minimum':0},idempotencyKey={'type':'string','minLength':1,'maxLength':128});required+=['documentId','expectedRevision','idempotencyKey']
        variants.append(dict(obj(fields,required),description=description))
    write_json(root/'schemas/file-command.schema.json',{'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:vayrshemon:schema:file-command:'+FileAPI.version,'oneOf':variants})
    write_json(root/'data/file-mcp-tools.json',dict(apiVersion=FileAPI.version,protocolVersion='2024-11-05',tools=tools(METHODS)))
    write_json(root/'data/file-capabilities.json',dict(schemaVersion='0.1.0',apiVersion=FileAPI.version,milestone='M14',capabilities=[dict(method=m,description=d,mutation=mutation,transports=['python','cli','desktop','mcp']) for m,(d,mutation,_) in METHODS.items()]))


if __name__=='__main__':generate(Path(__file__).resolve().parents[1])
