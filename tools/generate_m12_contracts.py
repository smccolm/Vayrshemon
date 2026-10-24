"""Publish M12 API/MCP contracts; native documents stay at 0.5.0."""
from pathlib import Path
from tools.m0.common import write_json
from vayrshemon.api import obj
from vayrshemon.reading_api import METHODS,ReadingAPI
from vayrshemon.mcp import tools


def generate(root):
    root=Path(root);variants=[]
    for method,(description,mutation,params) in METHODS.items():
        fields=dict(apiVersion={'const':ReadingAPI.version},method={'const':method},params=params)
        required=['apiVersion','method','params']
        if mutation:
            fields.update(documentId={'type':'string'},expectedRevision={'type':'integer','minimum':0},idempotencyKey={'type':'string','minLength':1,'maxLength':128})
            required+=['documentId','expectedRevision','idempotencyKey']
        variants.append(dict(obj(fields,required),description=description))
    write_json(root/'schemas/reading-command.schema.json',{'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:vayrshemon:schema:reading-command:'+ReadingAPI.version,'oneOf':variants})
    write_json(root/'data/reading-mcp-tools.json',dict(apiVersion=ReadingAPI.version,protocolVersion='2024-11-05',tools=tools(METHODS)))
    write_json(root/'data/reading-capabilities.json',dict(schemaVersion='0.1.0',apiVersion=ReadingAPI.version,milestone='M12',
        capabilities=[dict(method=m,description=d,mutation=mutation,transports=['python','cli','desktop','mcp'],requiresDesktop=m in ('ui.forge','ui.capture','selection.set','ui.workspace','ui.sidebar','ui.sidebar.inspect','view.tool','view.pan','view.center','view.inspect')) for m,(d,mutation,_) in METHODS.items()]))


if __name__=='__main__': generate(Path(__file__).resolve().parents[1])
