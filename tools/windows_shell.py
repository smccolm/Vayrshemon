"""Build/register .vay integration with an isolated native thumbnail component.

Run through setup.bat, or use --unregister to restore only values we installed.
Native build outputs are content addressed so an Explorer-loaded DLL is never
overwritten. No changes to .json, UserChoice, or thumbnail privacy preferences.
"""
import argparse,ctypes,hashlib,json,os,shutil,subprocess,sys,time,uuid
from pathlib import Path
from tools.m0.common import write_json,load_json

CLSID='{7B6EA804-42E7-4BFC-A562-4295CCD27B61}'
THUMBNAIL='{E357FCCD-A995-4576-B01F-234630154E96}'
PROGID='Vayrshemon.Document'
BASE='Software\\Classes\\'
COMPONENT_FILES=('VayrshemonShell.dll','memon-color.ico','memon-mono-black.ico','memon-mono-white.ico')


def compiler_environment():
    vswhere=Path(os.environ.get('ProgramFiles(x86)',r'C:\Program Files (x86)'))/'Microsoft Visual Studio/Installer/vswhere.exe'
    if not vswhere.exists():raise RuntimeError('MSVC_REQUIRED: run setup.bat to install the C++ build tools.')
    found=subprocess.check_output([str(vswhere),'-latest','-products','*','-requires','Microsoft.VisualStudio.Component.VC.Tools.x86.x64','-property','installationPath'],text=True).strip()
    if not found:raise RuntimeError('MSVC_REQUIRED: Visual Studio C++ x64 tools and a Windows SDK are required; run setup.bat.')
    script=Path(found)/'VC/Auxiliary/Build/vcvars64.bat'
    output=subprocess.check_output(f'cmd.exe /d /s /c ""{script}" >nul && set"',text=True,errors='replace')
    return dict(line.split('=',1) for line in output.splitlines() if '=' in line and not line.startswith('='))


def build(root):
    if os.name!='nt':raise RuntimeError('WINDOWS_REQUIRED')
    root=Path(root).resolve();sources=[root/'tools/shell/vay_shell.cpp',root/'tools/shell/vay_shell.def']
    icons=sorted((root/'data/icons').glob('*.ico'))
    if len(icons)!=3:raise RuntimeError('MEMON_ICONS_MISSING')
    signature=hashlib.sha256(b''.join(p.read_bytes() for p in sources+icons)).hexdigest()[:16]
    folder=root/'.local/shell'/signature;dll=folder/'VayrshemonShell.dll'
    if not dll.exists():
        folder.mkdir(parents=True,exist_ok=True);env=compiler_environment()
        args=['cl.exe','/nologo','/std:c++17','/O2','/MT','/EHsc','/W4','/utf-8','/DUNICODE','/D_UNICODE','/LD',str(sources[0]),'/Fe:'+str(dll),'/Fo:'+str(folder/'vay_shell.obj'),'/link','/DEF:'+str(sources[1]),'/DYNAMICBASE','/NXCOMPAT','/GUARD:CF','ole32.lib','shell32.lib','shlwapi.lib','windowscodecs.lib','uuid.lib','crypt32.lib','gdi32.lib']
        args[0]=shutil.which('cl.exe',path=next(v for k,v in env.items() if k.lower()=='path')) or 'cl.exe'
        subprocess.run(args,cwd=folder,env=env,check=True)
    for source in icons:shutil.copy2(source,folder/source.name)
    write_json(folder/'build.json',dict(version='0.15.0',sourceSha256=signature,dll=str(dll),dllSha256=hashlib.sha256(dll.read_bytes()).hexdigest()))
    return folder


def registry_read(key,name=''):
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,BASE+key) as handle:
            value,kind=winreg.QueryValueEx(handle,name);return dict(value=value,kind=kind)
    except FileNotFoundError:return None


def notify():ctypes.windll.shell32.SHChangeNotify(0x08000000,0,None,None)


def machine_status():
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,BASE+'CLSID\\'+CLSID+r'\InprocServer32',0,winreg.KEY_READ|winreg.KEY_WOW64_64KEY) as handle:
            return winreg.QueryValueEx(handle,'')[0]
    except FileNotFoundError:return None


def elevate(root,arguments):
    root=Path(root).resolve();run_id=str(uuid.uuid4());report=root/'.local/shell'/('elevation-'+run_id+'.json')
    report.parent.mkdir(parents=True,exist_ok=True)
    args=['-I','-S',str(root/'tools/install_shell_machine.py'),*arguments,'--report',str(report),'--run-id',run_id]
    quoted=lambda value:"'"+value.replace("'","''")+"'"
    command=('Start-Process -FilePath '+quoted(sys.executable)+' -ArgumentList '+quoted(subprocess.list2cmdline(args))+
        ' -Verb RunAs -WindowStyle Hidden -Wait -PassThru | ForEach-Object { exit $_.ExitCode }')
    print('Windows administrator approval: install/remove the isolated Vayrshemon thumbnail component.',flush=True)
    result=subprocess.run(['powershell.exe','-NoProfile','-Command',command])
    # Some venv launchers exit before their elevated interpreter has finished.
    # The unique report is the completion handshake; never reuse an old result.
    deadline=time.monotonic()+30
    while not report.exists() and result.returncode==0 and time.monotonic()<deadline:time.sleep(.1)
    data=load_json(report) if report.exists() else {}
    if result.returncode or not data.get('ok') or data.get('runId')!=run_id:
        raise RuntimeError('SHELL_COMPONENT_INSTALL_FAILED: '+str(data.get('error','Windows administrator approval was cancelled or the installer did not finish.')))
    return data['result']


def ensure_machine(root,folder):
    expected=hashlib.sha256(b''.join((folder/name).read_bytes() for name in COMPONENT_FILES)).hexdigest()
    existing=machine_status()
    if existing:
        installed=Path(existing).parent
        if all((installed/name).is_file() for name in COMPONENT_FILES):
            actual=hashlib.sha256(b''.join((installed/name).read_bytes() for name in COMPONENT_FILES)).hexdigest()
            if actual==expected:return dict(installed=True,dll=existing,unchanged=True)
    return elevate(root,['--source',str(folder),'--expected',expected])


def register(root,folder):
    import winreg
    root=Path(root).resolve();folder=Path(folder).resolve();manifest=root/'.local/shell/registration.json'
    python=root/'.venv/Scripts/pythonw.exe';launcher=root/'tools/open_document.py'
    if not python.is_file():raise RuntimeError('PYTHONW_MISSING')
    values=[
        (PROGID,'','Vayrshemon document'),(PROGID,'FriendlyTypeName','Vayrshemon document'),
        (PROGID+r'\DefaultIcon','',str(folder/'memon-color.ico')+',0'),
        (PROGID+r'\shell\open\command','',f'"{python}" "{launcher}" "%1"'),
        (PROGID+r'\shellex\IconHandler','',CLSID),
        (PROGID+'\\shellex\\'+THUMBNAIL,'',CLSID),
        ('.vay\\shellex\\'+THUMBNAIL,'',CLSID),
        ('CLSID\\'+CLSID,'','Vayrshemon Memon and saved-page previews'),
        ('CLSID\\'+CLSID+r'\InprocServer32','',str(folder/'VayrshemonShell.dll')),
        ('CLSID\\'+CLSID+r'\InprocServer32','ThreadingModel','Apartment'),
        (r'.vay\OpenWithProgids',PROGID,''),
    ]
    current=registry_read('.vay')
    # Existing user associations are left intact; ours remains in Open With.
    if current is None or current['value']==PROGID:values.append(('.vay','',PROGID))
    old=load_json(manifest) if manifest.exists() else {'values':[]}
    known={(v['key'],v['name']):v for v in old['values']}
    records=[]
    for key,name,value in values:
        prior=registry_read(key,name);record=dict(key=key,name=name,previous=known.get((key,name),{}).get('previous',prior),installed=dict(value=value,kind=winreg.REG_SZ));records.append(record)
    # Journal first, so a partial installation can always be unregistered.
    write_json(manifest,dict(version=1,root=str(root),folder=str(folder),values=records))
    for record in records:
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER,BASE+record['key'],0,winreg.KEY_SET_VALUE) as handle:
            winreg.SetValueEx(handle,record['name'],0,winreg.REG_SZ,record['installed']['value'])
    notify();return status(root)


def unregister(root):
    import winreg
    manifest=Path(root)/'.local/shell/registration.json'
    if not manifest.exists():return dict(unregistered=False,reason='No registration journal')
    data=load_json(manifest);restored=0
    for record in reversed(data['values']):
        if registry_read(record['key'],record['name'])!=record['installed']:continue
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,BASE+record['key'],0,winreg.KEY_SET_VALUE) as handle:
            prior=record['previous']
            if prior is None:winreg.DeleteValue(handle,record['name'])
            else:winreg.SetValueEx(handle,record['name'],0,prior['kind'],prior['value'])
        restored+=1
    # Remove empty owned keys only. Registry/file data from other apps survives.
    for key in sorted({v['key'] for v in data['values']},key=len,reverse=True):
        while key:
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER,BASE+key) as handle:
                    subkeys,value_count,_=winreg.QueryInfoKey(handle)
                if subkeys or value_count:break
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER,BASE+key)
            except OSError:break
            key=key.rpartition('\\')[0]
    manifest.unlink();notify();return dict(unregistered=True,restoredValues=restored,restartRequired=False)


def status(root):
    if os.name!='nt':return dict(available=False,reason='Windows Explorer integration')
    handler=registry_read('CLSID\\'+CLSID+r'\InprocServer32');association=registry_read('.vay')
    icon=registry_read(PROGID+r'\shellex\IconHandler');thumb=registry_read(PROGID+'\\shellex\\'+THUMBNAIL)
    machine=machine_status()
    return dict(available=True,installed=bool(machine and Path(machine).is_file() and handler and Path(handler['value']).is_file() and icon and icon['value']==CLSID and thumb and thumb['value']==CLSID),
        association=association['value'] if association else None,dll=handler['value'] if handler else None,
        machineDll=machine,scope='current-user associations; machine thumbnail COM class',thumbnailIsolation=True,extension='.vay')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group();group.add_argument('--build',action='store_true');group.add_argument('--install',action='store_true');group.add_argument('--unregister',action='store_true');group.add_argument('--uninstall',action='store_true');args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    if args.install:
        folder=build(root);ensure_machine(root,folder);result=register(root,folder)
    elif args.build:result=dict(folder=str(build(root)))
    elif args.unregister:result=unregister(root)
    elif args.uninstall:result=dict(machine=elevate(root,['--uninstall']),user=unregister(root))
    else:result=status(root)
    print(json.dumps(result,indent=2))
