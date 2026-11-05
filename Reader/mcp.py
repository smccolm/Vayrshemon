"""Read-only document controls over MCP stdio; uses the separate live Reader API."""
import argparse,json,sys
from pathlib import Path
if __package__ in (None,''):sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from Reader.control import call,METHODS

FIELDS={
 'open':({'path':{'type':'string'},'restore':{'type':'boolean'}},['path']),
 'page':({'page':{'type':'integer','minimum':1},'direction':{'enum':['next','previous']}},[]),
 'mode':({'mode':{'enum':['one','two']}},['mode']),
 'palette':({'palette':{'enum':['white','black','color']}},['palette']),
 'zoom':({'zoom':{'type':'number','minimum':.1,'maximum':3}},['zoom']),
 'fit':({'fit':{'enum':['height','width']}},['fit']),
 'pan':({'dx':{'type':'number'},'dy':{'type':'number'}},[]),
 'search':({'query':{'type':'string','maxLength':1000}},['query']),
 'capture':({'path':{'type':'string'}},['path']),
 'performance':({'limit':{'type':'integer','minimum':1,'maximum':3000}},[]),
}

def catalog():
    result=[]
    for method,description in METHODS.items():
        fields,required=FIELDS.get(method.split('.')[1],({},[]))
        result.append(dict(name=method.replace('.','_'),description=description,inputSchema=dict(type='object',properties=fields,required=required,additionalProperties=False)))
    return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--descriptor');args=parser.parse_args()
    for line in sys.stdin:
        request={}
        try:
            request=json.loads(line);method=request['method'];params=request.get('params',{})
            if 'id' not in request:continue
            if method=='initialize':
                result=dict(protocolVersion='2024-11-05',capabilities=dict(tools={}),serverInfo=dict(name='vayrshemon-reader',version='1.0.0'))
            elif method=='ping':result={}
            elif method=='tools/list':result=dict(tools=catalog())
            elif method=='tools/call':
                name=params['name'];method=name.replace('_','.',1)
                if method not in METHODS:raise ValueError('Unknown Reader control')
                try:result=dict(content=[dict(type='text',text=json.dumps(call(method,params.get('arguments',{}),args.descriptor),ensure_ascii=False))])
                except Exception as error:result=dict(isError=True,content=[dict(type='text',text=str(error))])
            else:raise ValueError('Unsupported MCP method')
            response=dict(jsonrpc='2.0',id=request['id'],result=result)
        except Exception as error:response=dict(jsonrpc='2.0',id=request.get('id'),error=dict(code=-32602,message=str(error)))
        print(json.dumps(response,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
