"""Offline, standard-library inspection and verified backup recovery. No Qt needed."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path,PurePosixPath
import tempfile
import zipfile

VERSION='1.0.0'
MAX_DOCUMENT=16*1024*1024
MAX_BUNDLE=512*1024*1024


def sha(data): return hashlib.sha256(data).hexdigest()
def encoded(value): return json.dumps(value,ensure_ascii=True,indent=2,allow_nan=False).encode('utf-8')


def decode(data):
    def pairs(items):
        result={}
        for key,value in items:
            if key in result: raise ValueError('DUPLICATE_JSON_KEY: '+key)
            result[key]=value
        return result
    def reject(value): raise ValueError('NONFINITE_JSON_NUMBER: '+value)
    return json.loads(data,object_pairs_hook=pairs,parse_constant=reject)


def publish_new(temp,path):
    # Windows rename refuses replacement and also works on non-NTFS backup
    # drives. POSIX rename replaces, so use its exclusive same-directory link.
    if os.name=='nt': os.rename(temp,path)
    else: os.link(temp,path)


def read_document(path):
    path=Path(path)
    if path.stat().st_size>MAX_DOCUMENT: raise ValueError('DOCUMENT_TOO_LARGE')
    raw=path.read_bytes();value=decode(raw)
    if value.get('format')!='vayrshemon.document' or value.get('formatVersion') not in ('0.2.0','0.3.0','0.4.0','0.5.0'):
        raise ValueError('UNSUPPORTED_NATIVE_DOCUMENT')
    if not isinstance(value.get('state',{}).get('pages'),list): raise ValueError('INVALID_DOCUMENT_STRUCTURE')
    return value,raw


def inspect(path):
    value,raw=read_document(path);state=value['state']
    frames=[f for p in state['pages'] for f in p['frames']]
    text=lambda f:'\n'.join(''.join(r.get('text',r.get('sourceText','')) for r in b['runs']) for b in f['content']['document']['stories'][0]['blocks'])
    return dict(formatVersion=value['formatVersion'],documentId=state['documentId'],title=state['title'],revision=state['revision'],
        pages=len(state['pages']),frames=len(frames),scalars=sum(len(text(f)) for f in frames),sha256=sha(raw),
        fontSources=state['fontSources'],validation='Structural inspection only. Open in editor for full schema, semantic and font validation.')


def exclusive_write(path,data):
    """Publish completed bytes without replacing an existing destination."""
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,temp=tempfile.mkstemp(prefix='.pending-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream: stream.write(data);stream.flush();os.fsync(stream.fileno())
        # Same-directory hard link is atomic and refuses an existing name.
        publish_new(temp,path)
    finally: Path(temp).unlink(missing_ok=True)


def create_backup(document,directory,expected_sha256=None):
    value,raw=read_document(document);directory=Path(directory).resolve();directory.mkdir(parents=True,exist_ok=True)
    if expected_sha256 is not None and sha(raw)!=expected_sha256: raise ValueError('DOCUMENT_CHANGED_ON_DISK')
    files={'document.vay.json':raw};fonts=[]
    for source in value['state']['fontSources']:
        path=Path(source['path'])
        if path.stat().st_size>64*1024*1024: raise ValueError('FONT_TOO_LARGE')
        data=path.read_bytes()
        if sha(data)!=source['sha256']: raise ValueError('BACKUP_FONT_HASH_MISMATCH')
        name='fonts/'+source['sha256']+path.suffix.lower()
        files[name]=data;fonts.append(dict(fontId=source['fontId'],member=name,sha256=sha(data)))
    if sum(map(len,files.values()))>MAX_BUNDLE: raise ValueError('BACKUP_SIZE_LIMIT')
    manifest=dict(format='vayrshemon.backup',version=VERSION,createdAt=datetime.now(timezone.utc).isoformat(),
        documentId=value['state']['documentId'],revision=value['state']['revision'],fonts=fonts,
        files={name:dict(sha256=sha(data),bytes=len(data)) for name,data in files.items()})
    # Content addressing deduplicates repeated saves; all revisions are retained.
    target=directory/(sha(raw)+'.vaybackup')
    if not target.exists():
        fd,temp=tempfile.mkstemp(prefix='.backup-',dir=directory);os.close(fd)
        try:
            with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED) as archive:
                for name,data in files.items(): archive.writestr(name,data)
                archive.writestr('manifest.json',encoded(manifest))
            verify_backup(temp)
            try: publish_new(temp,target)
            except FileExistsError: pass
        finally: Path(temp).unlink(missing_ok=True)
    verified,_=verify_backup(target)
    return dict(path=str(target),documentSha256=verified['files']['document.vay.json']['sha256'],revision=verified['revision'],
        fonts=len(verified['fonts']),verified=True,retention='all distinct saved revisions; no automatic deletion',independentDevice=False)


def verify_backup(path):
    with zipfile.ZipFile(path) as archive:
        entries=archive.infolist();names=[e.filename for e in entries]
        if len(names)>1024 or len(set(names))!=len(names): raise ValueError('BACKUP_DUPLICATE_OR_TOO_MANY_MEMBERS')
        if sum(e.file_size for e in entries)>MAX_BUNDLE: raise ValueError('BACKUP_SIZE_LIMIT')
        for name in names:
            p=PurePosixPath(name)
            if p.is_absolute() or '..' in p.parts or '\\' in name or ':' in name: raise ValueError('UNSAFE_BACKUP_MEMBER')
        if archive.getinfo('manifest.json').file_size>MAX_DOCUMENT: raise ValueError('MANIFEST_TOO_LARGE')
        manifest=decode(archive.read('manifest.json'))
        if manifest.get('format')!='vayrshemon.backup' or manifest.get('version')!=VERSION: raise ValueError('UNSUPPORTED_BACKUP')
        if set(names)!={'manifest.json',*manifest['files']}: raise ValueError('BACKUP_MEMBER_MISMATCH')
        files={name:archive.read(name) for name in manifest['files']}
        for name,data in files.items():
            if manifest['files'][name]!=dict(sha256=sha(data),bytes=len(data)): raise ValueError('BACKUP_HASH_MISMATCH: '+name)
        raw=files['document.vay.json']
        if len(raw)>MAX_DOCUMENT: raise ValueError('DOCUMENT_TOO_LARGE')
        doc=decode(raw)
        if doc.get('format')!='vayrshemon.document' or doc.get('formatVersion') not in ('0.2.0','0.3.0','0.4.0','0.5.0'): raise ValueError('UNSUPPORTED_NATIVE_DOCUMENT')
        sources=doc['state']['fontSources'];indexed={f['fontId']:f for f in manifest['fonts']}
        if len(indexed)!=len(manifest['fonts']) or set(indexed)!={s['fontId'] for s in sources}: raise ValueError('BACKUP_FONT_INDEX_MISMATCH')
        if len(sources)!=len(indexed): raise ValueError('BACKUP_DUPLICATE_FONT')
        for source in sources:
            f=indexed[source['fontId']]
            if f['sha256']!=source['sha256'] or sha(files[f['member']])!=source['sha256']: raise ValueError('BACKUP_FONT_HASH_MISMATCH')
        if manifest['documentId']!=doc['state']['documentId'] or manifest['revision']!=doc['state']['revision']: raise ValueError('BACKUP_IDENTITY_MISMATCH')
        return manifest,files


def restore_backup(path,destination):
    manifest,files=verify_backup(path);destination=Path(destination).resolve()
    if destination.exists(): raise ValueError('RECOVERY_REQUIRES_NEW_DIRECTORY')
    destination.mkdir(parents=True)
    # Exact original is retained alongside a copy whose font paths are relocated.
    (destination/'original.vay.json').write_bytes(files['document.vay.json'])
    value=decode(files['document.vay.json']);indexed={f['fontId']:f for f in manifest['fonts']}
    for source in value['state']['fontSources']:
        entry=indexed[source['fontId']];name=Path(entry['member']).name
        target=destination/'fonts'/name;target.parent.mkdir(exist_ok=True)
        target.write_bytes(files[entry['member']]);source['path']=str(target)
    target=destination/'recovered.vay.json';target.write_bytes(encoded(value))
    report=dict(path=str(target),originalSha256=manifest['files']['document.vay.json']['sha256'],recoveredSha256=sha(target.read_bytes()),
        relocatedFonts=len(indexed),revision=manifest['revision'],sourceUnchanged=True)
    (destination/'recovery-report.json').write_bytes(encoded(report));return report


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    for name in ('inspect','verify','text'):
        q=sub.add_parser(name);q.add_argument('path',type=Path)
        if name=='text': q.add_argument('--out',type=Path,required=True)
    for name in ('backup','restore'):
        q=sub.add_parser(name);q.add_argument('path',type=Path);q.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    if args.command=='inspect': result=inspect(args.path)
    elif args.command=='verify': result=verify_backup(args.path)[0]
    elif args.command=='backup': result=create_backup(args.path,args.out)
    elif args.command=='restore': result=restore_backup(args.path,args.out)
    else:
        doc,_=read_document(args.path)
        result=dict(documentId=doc['state']['documentId'],pages=[dict(pageId=p['pageId'],frames=[dict(frameId=f['frameId'],name=f['name'],
            blocks=f['content']['document']['stories'][0]['blocks']) for f in p['frames']]) for p in doc['state']['pages']],
            note='Exact text/legacy slots with run metadata. No guessed transliteration or translation.')
        exclusive_write(args.out,encoded(result));result=dict(path=str(args.out))
    print(json.dumps(result,ensure_ascii=True,indent=2))


if __name__=='__main__': main()
