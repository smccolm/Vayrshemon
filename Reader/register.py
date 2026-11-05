"""Per-user Reader association. Preserve Workbench editing and shell thumbnails."""
import argparse,ctypes,json,os
from pathlib import Path
from .storage import ROOT,LOCAL,dumps

PROGID='Vayrshemon.Reader.Document'
CLSID='{7B6EA804-42E7-4BFC-A562-4295CCD27B61}'
THUMBNAIL='{E357FCCD-A995-4576-B01F-234630154E96}'

def read(key,name=''):
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,key) as h:
            value,kind=winreg.QueryValueEx(h,name);return dict(value=value,kind=kind)
    except FileNotFoundError:return None

def install():
    import winreg
    python=ROOT/'.venv/Scripts/pythonw.exe';launch=ROOT/'Reader/launch.py';icon=ROOT/'data/icons/memon-color.ico'
    if not all(p.exists() for p in (python,launch,icon)):raise RuntimeError('Run project setup first')
    from .build_launcher import build
    executable=build();command=f'"{executable}" "%1"'
    edit=f'"{python}" "{ROOT / "tools/open_document.py"}" "%1"'
    base='Software\\Classes\\';key=base+PROGID
    values=[(key,'','Vayrshemon book'),(key,'FriendlyTypeName','Vayrshemon book'),(key+'\\DefaultIcon','',str(icon)+',0'),(key+'\\shell\\open','FriendlyAppName','Vayrshemon Reader'),
            (key+'\\shell\\open\\command','',command),(key+'\\shell\\edit','','Edit in Vayrshemon Workbench'),(key+'\\shell\\edit\\command','',edit),
            (key+'\\shellex\\IconHandler','',CLSID),(key+'\\shellex\\'+THUMBNAIL,'',CLSID),
            (base+'.vay\\OpenWithProgids',PROGID,''),(base+'Vayrshemon.Document\\shell\\read','','Read in Vayrshemon Reader'),(base+'Vayrshemon.Document\\shell\\read\\command','',command),
            (base+'Applications\\VayrshemonReader.exe','FriendlyAppName','Vayrshemon Reader'),(base+'Applications\\VayrshemonReader.exe\\DefaultIcon','',str(icon)+',0'),
            (base+'Applications\\VayrshemonReader.exe\\shell\\open\\command','',command),(base+'Applications\\VayrshemonReader.exe\\SupportedTypes','.vay',''),
            (base+'Applications\\VayrshemonReader.exe\\shell\\edit','','Edit in Vayrshemon Workbench'),(base+'Applications\\VayrshemonReader.exe\\shell\\edit\\command','',edit),
            (base+'Applications\\VayrshemonReader.exe\\shellex\\IconHandler','',CLSID),(base+'Applications\\VayrshemonReader.exe\\shellex\\'+THUMBNAIL,'',CLSID),
            ('Software\\VayrshemonReader\\Capabilities','ApplicationName','Vayrshemon Reader'),('Software\\VayrshemonReader\\Capabilities','ApplicationDescription','Fast read-only Vayrshemon books'),
            ('Software\\VayrshemonReader\\Capabilities','ApplicationIcon',str(icon)+',0'),
            ('Software\\VayrshemonReader\\Capabilities\\FileAssociations','.vay',PROGID),('Software\\RegisteredApplications','Vayrshemon Reader','Software\\VayrshemonReader\\Capabilities')]
    # Honor an explicit Windows UserChoice. This PC's previous association was
    # our per-user Workbench default; no protected association hash is touched.
    choice=read(r'Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.vay\UserChoice','ProgId')
    current=read(base+'.vay')
    if current is None or current['value'] in ('Vayrshemon.Document',PROGID):values.append((base+'.vay','',PROGID))
    journal=LOCAL/'association.json';journal.parent.mkdir(parents=True,exist_ok=True)
    old=json.loads(journal.read_bytes()) if journal.exists() else {'values':[]};previous={(r['key'],r['name']):r for r in old['values']}
    records=[dict(key=k,name=n,previous=previous.get((k,n),{}).get('previous',read(k,n)),installed=dict(value=v,kind=winreg.REG_SZ)) for k,n,v in values]
    journal.write_bytes(dumps(dict(values=records)))
    for r in records:
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER,r['key'],0,winreg.KEY_SET_VALUE) as h:winreg.SetValueEx(h,r['name'],0,winreg.REG_SZ,r['installed']['value'])
    ctypes.windll.shell32.SHChangeNotify(0x08000000,0,None,None)
    size=ctypes.c_ulong(4096);resolved=ctypes.create_unicode_buffer(size.value)
    status=ctypes.windll.shlwapi.AssocQueryStringW(0,1,'.vay','open',resolved,ctypes.byref(size))
    default=status==0 and str(executable).lower() in resolved.value.lower()
    return dict(installed=True,progId=PROGID,command=command,userChoice=choice['value'] if choice else None,defaultForVay=default,resolvedCommand=resolved.value,workbenchEditAvailable=True)

def uninstall():
    import winreg
    journal=LOCAL/'association.json'
    if not journal.exists():return dict(restored=0)
    records=json.loads(journal.read_bytes())['values'];count=0
    for r in reversed(records):
        if read(r['key'],r['name'])!=r['installed']:continue
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r['key'],0,winreg.KEY_SET_VALUE) as h:
            if r['previous'] is None:winreg.DeleteValue(h,r['name'])
            else:winreg.SetValueEx(h,r['name'],0,r['previous']['kind'],r['previous']['value'])
        count+=1
    journal.unlink();ctypes.windll.shell32.SHChangeNotify(0x08000000,0,None,None);return dict(restored=count)

if __name__=='__main__':
    parser=argparse.ArgumentParser();g=parser.add_mutually_exclusive_group(required=True);g.add_argument('--install',action='store_true');g.add_argument('--uninstall',action='store_true');args=parser.parse_args()
    print(json.dumps(install() if args.install else uninstall(),indent=2))

