"""Publish M2 contracts without changing the frozen M0/M1 interfaces."""
from pathlib import Path
from tools.m0.common import write_json
from vayrshemon.api import obj
from vayrshemon.editor_api import METHODS,EditorAPI
from vayrshemon.editor_contracts import EDITOR_DOCUMENT
from vayrshemon.mcp import tools


def generate(root):
    root=Path(root); variants=[]
    for method,(description,mutation,params) in METHODS.items():
        fields=dict(apiVersion={'const':EditorAPI.version},method={'const':method},params=params)
        required=['apiVersion','method','params']
        if mutation:
            fields.update(documentId={'type':'string'},expectedRevision={'type':'integer','minimum':0},idempotencyKey={'type':'string','minLength':1,'maxLength':128})
            required+=['documentId','expectedRevision','idempotencyKey']
        variants.append(dict(obj(fields,required),description=description))
    schema={'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:vayrshemon:schema:editor-command:0.3.0','oneOf':variants}
    write_json(root/'schemas/editor-command.schema.json',schema)
    write_json(root/'schemas/editor-document.schema.json',EDITOR_DOCUMENT)
    write_json(root/'data/editor-mcp-tools.json',dict(apiVersion=EditorAPI.version,protocolVersion='2024-11-05',tools=tools(METHODS)))
    write_json(root/'data/editor-capabilities.json',dict(schemaVersion='0.1.0',apiVersion=EditorAPI.version,milestone='M2',
        capabilities=[dict(method=m,description=d,mutation=mutation,transports=['python','cli','desktop','mcp'],requiresDesktop=m in ('ui.capture','selection.set'))
                      for m,(d,mutation,_) in METHODS.items()]))


if __name__=='__main__': generate(Path(__file__).resolve().parents[1])
