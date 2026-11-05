"""Build a small named/icon-bearing Windows launcher using the system C# compiler."""
import hashlib,os,subprocess
from .storage import ROOT,LOCAL

def build():
    source=ROOT/'Reader/Launcher.cs';icon=ROOT/'data/icons/memon-color.ico';target=ROOT/'Reader/VayrshemonReader.exe'
    stamp=LOCAL/'launcher.sha256';signature=hashlib.sha256(source.read_bytes()+icon.read_bytes()).hexdigest()
    if target.exists() and stamp.exists() and stamp.read_text()==signature:return target
    compiler=next((p for arch in ('Framework64','Framework') if (p:=Path(os.environ.get('WINDIR',r'C:\Windows'))/'Microsoft.NET'/arch/'v4.0.30319/csc.exe').exists()),None)
    if compiler is None:raise RuntimeError('Windows .NET Framework C# compiler is missing; Reader can still run with launch.bat')
    subprocess.run([str(compiler),'/nologo','/target:winexe','/optimize+','/r:System.Windows.Forms.dll','/win32icon:'+str(icon),'/out:'+str(target),str(source)],check=True,creationflags=subprocess.CREATE_NO_WINDOW)
    stamp.parent.mkdir(parents=True,exist_ok=True);stamp.write_text(signature);return target

from pathlib import Path
if __name__=='__main__':print(build())
