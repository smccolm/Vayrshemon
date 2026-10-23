"""Publish M3 contracts while retaining the M0, M1 and M2 interfaces."""
from pathlib import Path
from tools.m0.common import write_json
from vayrshemon.api import obj
from vayrshemon.typesetting_api import METHODS,TypesettingAPI
from vayrshemon.typesetting_contracts import DOCUMENT
from vayrshemon.mcp import tools


def generate(root):
    root=Path(root); variants=[]
    for method,(description,mutation,params) in METHODS.items():
        fields=dict(apiVersion={'const':TypesettingAPI.version},method={'const':method},params=params)
        required=['apiVersion','method','params']
        if mutation:
            fields.update(documentId={'type':'string'},expectedRevision={'type':'integer','minimum':0},idempotencyKey={'type':'string','minLength':1,'maxLength':128})
            required+=['documentId','expectedRevision','idempotencyKey']
        variants.append(dict(obj(fields,required),description=description))
    write_json(root/'schemas/typesetting-command.schema.json',{'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:vayrshemon:schema:typesetting-command:0.4.0','oneOf':variants})
    write_json(root/'schemas/typesetting-document.schema.json',DOCUMENT)
    write_json(root/'data/typesetting-mcp-tools.json',dict(apiVersion=TypesettingAPI.version,protocolVersion='2024-11-05',tools=tools(METHODS)))
    write_json(root/'data/typesetting-capabilities.json',dict(schemaVersion='0.1.0',apiVersion=TypesettingAPI.version,milestone='M3',
        capabilities=[dict(method=m,description=d,mutation=mutation,transports=['python','cli','desktop','mcp'],requiresDesktop=m in ('ui.capture','selection.set')) for m,(d,mutation,_) in METHODS.items()]))


if __name__=='__main__': generate(Path(__file__).resolve().parents[1])
