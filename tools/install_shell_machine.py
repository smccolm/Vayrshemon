"""Elevated, standard-library-only installation of the native thumbnail class.

File associations remain per-user. Only our CLSID and binaries are installed
machine-wide; Explorer policies and process isolation are never changed.
"""
import argparse,ctypes,hashlib,json,os,sys,traceback
from pathlib import Path
import winreg

CLSID='{7B6EA804-42E7-4BFC-A562-4295CCD27B61}'
KEY='Software\\Classes\\CLSID\\'+CLSID
FILES=('VayrshemonShell.dll','memon-color.ico','memon-mono-black.ico','memon-mono-white.ico')


def write_json(path,value):
    path=Path(path);temporary=path.with_name(path.name+'.tmp')
    with temporary.open('w',encoding='utf-8') as stream:
        json.dump(value,stream,indent=2);stream.flush();os.fsync(stream.fileno())
    os.replace(temporary,path)


def read_value(key,name=''):
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,key,0,winreg.KEY_READ|winreg.KEY_WOW64_64KEY) as h:
            value,kind=winreg.QueryValueEx(h,name);return dict(value=value,kind=kind)
    except FileNotFoundError:return None


def install(source,expected):
    if not ctypes.windll.shell32.IsUserAnAdmin():raise PermissionError('Windows administrator approval is required for the isolated thumbnail COM class.')
    source=Path(source).resolve(strict=True);project=Path(__file__).resolve().parents[1]
    if not source.is_relative_to(project/'.local/shell'):raise ValueError('BUILD_PATH_OUTSIDE_PROJECT')
    payloads={name:(source/name).read_bytes() for name in FILES}
    digest=hashlib.sha256(b''.join(payloads.values())).hexdigest()
    if digest!=expected:raise ValueError('SHELL_BUILD_CHANGED_BEFORE_INSTALL')
    base=Path(os.environ['ProgramFiles'])/'VayrshemonShell';target=base/digest[:16]
    target.mkdir(parents=True,exist_ok=True)
    for name,data in payloads.items():
        path=target/name
        if path.exists():
            if path.read_bytes()!=data:raise ValueError('INSTALLED_COMPONENT_HASH_MISMATCH')
        else:path.write_bytes(data)
    journal=base/'registration.json';prior=json.loads(journal.read_text()) if journal.exists() else {'values':[]}
    known={(r['key'],r['name']):r for r in prior['values']}
    values=[(KEY,'','Vayrshemon saved page thumbnails'),(KEY+r'\InprocServer32','',str(target/'VayrshemonShell.dll')),(KEY+r'\InprocServer32','ThreadingModel','Apartment')]
    records=[dict(key=k,name=n,previous=known.get((k,n),{}).get('previous',read_value(k,n)),installed=dict(value=v,kind=winreg.REG_SZ)) for k,n,v in values]
    write_json(journal,dict(version=1,values=records))
    for r in records:
        with winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE,r['key'],0,winreg.KEY_WRITE|winreg.KEY_WOW64_64KEY) as h:winreg.SetValueEx(h,r['name'],0,winreg.REG_SZ,r['installed']['value'])
    ctypes.windll.shell32.SHChangeNotify(0x08000000,0,None,None)
    return dict(installed=True,dll=str(target/'VayrshemonShell.dll'),sha256=hashlib.sha256(payloads['VayrshemonShell.dll']).hexdigest(),thumbnailIsolation=True)


def uninstall():
    if not ctypes.windll.shell32.IsUserAnAdmin():raise PermissionError('Windows administrator approval is required.')
    base=Path(os.environ['ProgramFiles'])/'VayrshemonShell';journal=base/'registration.json'
    if not journal.exists():return dict(unregistered=False)
    data=json.loads(journal.read_text());count=0
    for r in reversed(data['values']):
        if r['key'] not in (KEY,KEY+r'\InprocServer32'):raise ValueError('INVALID_REGISTRATION_JOURNAL')
        if read_value(r['key'],r['name'])!=r['installed']:continue
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r['key'],0,winreg.KEY_WRITE|winreg.KEY_WOW64_64KEY) as h:
            old=r['previous']
            if old is None:winreg.DeleteValue(h,r['name'])
            else:winreg.SetValueEx(h,r['name'],0,old['kind'],old['value'])
        count+=1
    journal.unlink();ctypes.windll.shell32.SHChangeNotify(0x08000000,0,None,None)
    # DLLs can still be loaded. Retain inert versioned files rather than
    # forcibly unloading another process or recursively deleting folders.
    return dict(unregistered=True,restoredValues=count,retainedFiles=str(base))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source');p.add_argument('--expected');p.add_argument('--uninstall',action='store_true');p.add_argument('--report',required=True);p.add_argument('--run-id',required=True);args=p.parse_args()
    try:result=dict(ok=True,result=uninstall() if args.uninstall else install(args.source,args.expected));code=0
    except Exception as error:result=dict(ok=False,error=str(error),traceback=traceback.format_exc());code=1
    result['runId']=args.run_id;write_json(args.report,result);sys.exit(code)
