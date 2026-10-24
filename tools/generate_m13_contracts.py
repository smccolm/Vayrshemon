"""Publish M13 API/MCP contracts; native documents stay at 0.5.0."""
from pathlib import Path
from tools.m0.common import write_json
from vayrshemon.api import obj
from vayrshemon.gloss_api import METHODS,GlossAPI
from vayrshemon.mcp import tools
from vayrshemon.language_contracts import DOCUMENT
from vayrshemon.studio_contracts import DOCUMENT as STUDIO_DOCUMENT


def generate(root):
    root=Path(root);variants=[]
    write_json(root/'schemas/language-document.schema.json',DOCUMENT)
    write_json(root/'schemas/studio-document.schema.json',STUDIO_DOCUMENT)
    for method,(description,mutation,params) in METHODS.items():
        fields=dict(apiVersion={'const':GlossAPI.version},method={'const':method},params=params)
        required=['apiVersion','method','params']
        if mutation:
            fields.update(documentId={'type':'string'},expectedRevision={'type':'integer','minimum':0},idempotencyKey={'type':'string','minLength':1,'maxLength':128})
            required+=['documentId','expectedRevision','idempotencyKey']
        variants.append(dict(obj(fields,required),description=description))
    write_json(root/'schemas/gloss-command.schema.json',{'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:vayrshemon:schema:gloss-command:'+GlossAPI.version,'oneOf':variants})
    write_json(root/'data/gloss-mcp-tools.json',dict(apiVersion=GlossAPI.version,protocolVersion='2024-11-05',tools=tools(METHODS)))
    write_json(root/'data/gloss-capabilities.json',dict(schemaVersion='0.1.0',apiVersion=GlossAPI.version,milestone='M13',
        capabilities=[dict(method=m,description=d,mutation=mutation,transports=['python','cli','desktop','mcp'],requiresDesktop=m in ('ui.forge','ui.capture','selection.set','ui.workspace','ui.sidebar','ui.sidebar.inspect','view.tool','view.pan','view.center','view.inspect','view.pages')) for m,(d,mutation,_) in METHODS.items()]))


if __name__=='__main__': generate(Path(__file__).resolve().parents[1])
