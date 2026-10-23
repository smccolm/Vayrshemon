"""Publish M5 schemas and the shared API/MCP surface without changing M1–M4."""
from pathlib import Path
from tools.m0.common import write_json
from vayrshemon.api import obj
from vayrshemon.language_api import METHODS,LanguageAPI
from vayrshemon.language_contracts import DOCUMENT,PACKAGE
from vayrshemon.mcp import tools


def generate(root):
    root=Path(root);variants=[]
    for method,(description,mutation,params) in METHODS.items():
        fields=dict(apiVersion={'const':LanguageAPI.version},method={'const':method},params=params)
        required=['apiVersion','method','params']
        if mutation:
            fields.update(documentId={'type':'string'},expectedRevision={'type':'integer','minimum':0},idempotencyKey={'type':'string','minLength':1,'maxLength':128})
            required+=['documentId','expectedRevision','idempotencyKey']
        variants.append(dict(obj(fields,required),description=description))
    write_json(root/'schemas/language-command.schema.json',{'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:vayrshemon:schema:language-command:0.6.0','oneOf':variants})
    write_json(root/'schemas/language-document.schema.json',DOCUMENT)
    write_json(root/'schemas/language-package.schema.json',dict(PACKAGE,**{'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:vayrshemon:schema:language-package:1.0.0'}))
    write_json(root/'data/language-mcp-tools.json',dict(apiVersion=LanguageAPI.version,protocolVersion='2024-11-05',tools=tools(METHODS)))
    write_json(root/'data/language-capabilities.json',dict(schemaVersion='0.1.0',apiVersion=LanguageAPI.version,milestone='M5',
        capabilities=[dict(method=m,description=d,mutation=mutation,transports=['python','cli','desktop','mcp'],requiresDesktop=m in ('ui.capture','selection.set','ui.workspace')) for m,(d,mutation,_) in METHODS.items()]))


if __name__=='__main__': generate(Path(__file__).resolve().parents[1])
