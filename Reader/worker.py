"""Qt rendering worker, separate from both Reader UI and Workbench."""
import json,sys,time,traceback,os
from PySide6.QtWidgets import QApplication
from .render import Engine

def main():
    app=QApplication([]);engine=Engine(sys.argv[1])
    print(json.dumps(dict(event='ready',pid=os.getpid())),flush=True)
    for line in sys.stdin:
        request=json.loads(line)
        try:
            started=time.perf_counter();op=request.get('op','render')
            if op=='render':result=engine.render(**request['params'])
            elif op=='search':result=engine.index.search(**request['params'])
            elif op=='text':result=engine.index.text(request['params']['number'])
            else:raise ValueError('Unknown reader worker operation')
            print(json.dumps(dict(event='result',id=request['id'],result=result,workerMs=(time.perf_counter()-started)*1000)),flush=True)
        except Exception as error:
            traceback.print_exc();print(json.dumps(dict(event='error',id=request['id'],message=str(error))),flush=True)
    return 0

if __name__=='__main__':sys.exit(main())
