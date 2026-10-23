"""Versioned local Windows source installs with atomic activation and rollback.

Bundles contain application sources, public fixtures and pinned requirements.
Python 3.12 x64 is the bootstrap prerequisite; setup downloads binary wheels.
Only install bundles from a trusted source: integrity hashes are not signatures.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path,PurePosixPath
import subprocess
import sys
import tempfile
import zipfile
from tools.recovery import encoded,exclusive_write


def digest(data): return hashlib.sha256(data).hexdigest()


def build(root,out):
    root=Path(root).resolve()
    names=subprocess.check_output(['git','ls-files','-z','--cached','--others','--exclude-standard'],cwd=root).decode().split('\0')
    folders={'vayrshemon','tools','data','schemas','tests','docs'}
    top={'setup.bat','launch.bat','installed.bat','README.md','AGENTS.md','CHANGELOG.md'}
    files={}
    for name in sorted(set(filter(None,names))):
        p=PurePosixPath(name)
        if not (p.parts[0] in folders or name in top or (len(p.parts)==1 and name.startswith('requirements-') and name.endswith('.txt'))): continue
        path=root/name
        if path.is_symlink() or not path.is_file(): continue
        files[name]=path.read_bytes()
    from vayrshemon import __version__
    manifest=dict(format='vayrshemon.release',version='1.0.0',application=__version__,nativeFormat='0.5.0',
        files={name:dict(sha256=digest(data),bytes=len(data)) for name,data in files.items()})
    import io
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as z:
        for name,data in files.items():
            info=zipfile.ZipInfo(name,(2026,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,data)
        z.writestr(zipfile.ZipInfo('release.json',(2026,1,1,0,0,0)),encoded(manifest))
    exclusive_write(out,stream.getvalue())
    return dict(path=str(Path(out).resolve()),sha256=digest(stream.getvalue()),files=len(files),application=__version__)


def verify(bundle):
    bundle=Path(bundle)
    if bundle.stat().st_size>64*1024*1024: raise ValueError('RELEASE_SIZE_LIMIT')
    with zipfile.ZipFile(bundle) as z:
        entries=z.infolist();names=[e.filename for e in entries]
        if len(names)>5000 or len(names)!=len(set(names)) or sum(e.file_size for e in entries)>128*1024*1024: raise ValueError('RELEASE_MEMBER_LIMIT')
        for name in names:
            p=PurePosixPath(name)
            if p.is_absolute() or '..' in p.parts or '\\' in name or ':' in name: raise ValueError('UNSAFE_RELEASE_PATH')
            if p.parts[0].lower() in ('.local','inputs','.venv','.git'): raise ValueError('PRIVATE_RELEASE_CONTENT')
        manifest=json.loads(z.read('release.json'))
        if manifest.get('format')!='vayrshemon.release' or manifest.get('version')!='1.0.0': raise ValueError('UNSUPPORTED_RELEASE')
        if set(names)!={'release.json',*manifest['files']}: raise ValueError('RELEASE_MEMBERS_MISMATCH')
        files={name:z.read(name) for name in manifest['files']}
        for name,data in files.items():
            if manifest['files'][name]!=dict(sha256=digest(data),bytes=len(data)): raise ValueError('RELEASE_HASH_MISMATCH: '+name)
        required={'setup.bat','tools/setup.ps1','requirements-m6.txt','vayrshemon/__main__.py'}
        if not required<=files.keys(): raise ValueError('INCOMPLETE_RELEASE')
        return manifest,files


def write_pointer(directory,value):
    from tools.m0.common import write_json
    write_json(Path(directory)/'active.json',value)


def release_path(directory,key):
    directory=Path(directory).resolve();path=(directory/'releases'/key).resolve()
    if path.parent!=directory/'releases': raise ValueError('INVALID_RELEASE_ID')
    return path


def check_installed(directory,key):
    path=release_path(directory,key);manifest=json.loads((path/'release.json').read_text())
    for name,record in manifest['files'].items():
        target=(path/name).resolve()
        if not target.is_relative_to(path) or digest(target.read_bytes())!=record['sha256']: raise ValueError('INSTALLED_RELEASE_MODIFIED: '+name)
    if not (path/'.local/install-verified.json').is_file(): raise ValueError('RELEASE_NOT_VALIDATED')
    return path


def activate(directory,key):
    directory=Path(directory).resolve();check_installed(directory,key)
    current=json.loads((directory/'active.json').read_text()) if (directory/'active.json').exists() else {}
    if current.get('active')==key: return current
    value=dict(version='1.0.0',active=key,previous=current.get('active'));write_pointer(directory,value);return value


def install(bundle,directory,wheelhouse=None):
    if os.name!='nt': raise ValueError('WINDOWS_INSTALLER_REQUIRED')
    manifest,files=verify(bundle);key=manifest['application']+'-'+digest(Path(bundle).read_bytes())[:12]
    directory=Path(directory).resolve();target=release_path(directory,key)
    if not target.exists():
        target.mkdir(parents=True)
        for name,data in files.items():
            p=target/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        (target/'release.json').write_bytes(encoded(manifest))
    else:
        # A failed setup is resumable, but never silently repair altered source.
        for name,data in files.items():
            if (target/name).read_bytes()!=data: raise ValueError('INSTALL_TARGET_MODIFIED')
    env=dict(os.environ)
    if wheelhouse: env['VAYRSHEMON_WHEELHOUSE']=str(Path(wheelhouse).resolve(strict=True))
    subprocess.run(['cmd.exe','/d','/c',str(target/'setup.bat'),'--no-pause'],cwd=target,env=env,check=True)
    (target/'.local/install-verified.json').write_bytes(encoded(dict(bundleSha256=digest(Path(bundle).read_bytes()),application=manifest['application'],checks='setup: dependencies, evidence, full public tests')))
    result=activate(directory,key)
    return dict(result,path=str(target),documentsMoved=False)


def rollback(directory):
    directory=Path(directory).resolve();value=json.loads((directory/'active.json').read_text())
    if not value.get('previous'): raise ValueError('NO_PREVIOUS_RELEASE')
    check_installed(directory,value['previous'])
    result=dict(version='1.0.0',active=value['previous'],previous=value['active']);write_pointer(directory,result);return result


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    b=sub.add_parser('build');b.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);b.add_argument('--out',type=Path,required=True)
    v=sub.add_parser('verify');v.add_argument('bundle',type=Path)
    for name in ('install','rollback','status','launch'):
        q=sub.add_parser(name);q.add_argument('--directory',type=Path,required=True)
        if name=='install': q.add_argument('bundle',type=Path);q.add_argument('--wheelhouse',type=Path)
        if name=='launch': q.add_argument('--document',type=Path);q.add_argument('--page-focus',action='store_true')
    args=p.parse_args()
    if args.command=='build': result=build(args.root,args.out)
    elif args.command=='verify': result=verify(args.bundle)[0]
    elif args.command=='install': result=install(args.bundle,args.directory,args.wheelhouse)
    elif args.command=='rollback': result=rollback(args.directory)
    elif args.command=='status': result=json.loads((args.directory/'active.json').read_text())
    else:
        value=json.loads((args.directory/'active.json').read_text());path=check_installed(args.directory,value['active'])
        command=[str(path/'.venv/Scripts/python.exe'),'-u','-m','vayrshemon','editor']
        if args.document: command+=['--document',str(args.document.resolve())]
        if args.page_focus: command+=['--page-focus']
        process=subprocess.Popen(command,cwd=path,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        result=dict(pid=process.pid,release=value['active'],path=str(path))
    print(json.dumps(result,indent=2))


if __name__=='__main__': main()
