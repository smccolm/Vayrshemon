"""Windowless separate application launcher, with native/Python crash logs."""
from pathlib import Path
from datetime import datetime
import os,subprocess,sys,time,traceback

def main():
    root=Path(__file__).resolve().parents[1];folder=root/'Reader/.local/logs';folder.mkdir(parents=True,exist_ok=True)
    log=folder/('launch-'+datetime.now().strftime('%Y%m%d-%H%M%S')+f'-{os.getpid()}.log')
    args=[str(root/'.venv/Scripts/python.exe'),'-u','-X','utf8','-X','faulthandler','-m','Reader.app','--started',str(time.perf_counter()),*sys.argv[1:]]
    code=1
    with log.open('wb',buffering=0) as f:
        try:code=subprocess.run(args,cwd=root,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW).returncode
        except Exception:f.write(traceback.format_exc().encode())
    if code:
        import ctypes
        ctypes.windll.user32.MessageBoxW(None,'Reader stopped with an error.\n\n'+str(log),'Vayrshemon Reader',0x10)
    return code

if __name__=='__main__':sys.exit(main())

