"""Quoted pythonw entry point for Explorer; retains all troubleshooting output."""
from datetime import datetime
from pathlib import Path
import sys,traceback

root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
if __name__=='__main__':
    directory=root/'.local/logs';directory.mkdir(parents=True,exist_ok=True)
    log=directory/('open-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'.log')
    with log.open('w',encoding='utf-8',buffering=1) as output:
        sys.stdout=sys.stderr=output
        try:
            if len(sys.argv)!=2:raise ValueError('One document path is required')
            path=Path(sys.argv[1]).resolve(strict=True)
            sys.argv=[sys.argv[0],'--root',str(root),'editor','--document',str(path)]
            from vayrshemon.__main__ import main
            raise SystemExit(main())
        except Exception:
            traceback.print_exc()
            import ctypes
            ctypes.windll.user32.MessageBoxW(None,'The document could not be opened.\n\nDetails: '+str(log),'Vayrshemon',0x10)
            raise SystemExit(1)
