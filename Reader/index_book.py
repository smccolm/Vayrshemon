"""Background import process; machine-readable progress on stdout."""
import json,sys,traceback
from .storage import build

def main():
    def emit(value): print(json.dumps(value),flush=True)
    try:
        result=build(sys.argv[1],lambda stage,percent:emit(dict(event='progress',stage=stage,percent=percent)))
        emit(dict(event='ready',**result))
    except Exception as error:
        traceback.print_exc();emit(dict(event='error',message=str(error)));return 1
    return 0

if __name__=='__main__':sys.exit(main())
