"""Pinned application fonts, independent of the optional private Inputs archive."""
import hashlib
import json
from pathlib import Path

DIRECTORY='data/runtime-fonts'
ROLES={'script-master','glow','interior','transliteration'}


def records(root):
    manifest=Path(root)/DIRECTORY/'manifest.json'
    if not manifest.is_file():return {}
    value=json.loads(manifest.read_text(encoding='utf-8'))
    if value.get('format')!='vayrshemon.runtime-fonts' or value.get('version')!='1.0.0':
        raise ValueError('RUNTIME_FONT_MANIFEST_INVALID')
    fonts=value['fonts']
    if len(fonts)!=len(ROLES) or {f['role'] for f in fonts}!=ROLES:
        raise ValueError('RUNTIME_FONT_ROLES_INVALID')
    for f in fonts:
        name=f['file'];sha=f['sha256']
        if not name or '/' in name or '\\' in name or ':' in name or not name.lower().endswith('.ttf'):
            raise ValueError('RUNTIME_FONT_PATH_INVALID')
        if len(sha)!=64 or any(c not in '0123456789abcdef' for c in sha) or f['fontId']!='font:'+sha+':0':
            raise ValueError('RUNTIME_FONT_ID_INVALID')
    result={f['fontId']:f for f in fonts}
    if len(result)!=len(fonts) or len({f['file'].lower() for f in fonts})!=len(fonts):
        raise ValueError('RUNTIME_FONT_DUPLICATE')
    return result


def path(root,record):return Path(root)/DIRECTORY/record['file']


def verify(root):
    root=Path(root);fonts=records(root)
    if not fonts:raise ValueError('RUNTIME_FONT_MANIFEST_MISSING')
    catalog={f['fontId']:f for f in json.loads((root/'data/fonts.json').read_text(encoding='utf-8'))['fonts']}
    for fid,record in fonts.items():
        asset=catalog[fid]['asset']
        if (asset['sha256'],asset['path'])!=(record['sha256'],record['source']):
            raise ValueError('RUNTIME_FONT_CATALOG_MISMATCH: '+record['file'])
        raw=path(root,record).read_bytes()
        if len(raw)!=record['bytes'] or hashlib.sha256(raw).hexdigest()!=record['sha256']:
            raise ValueError('RUNTIME_FONT_HASH_MISMATCH: '+record['file'])
    return dict(verified=True,fonts=len(fonts),bytes=sum(f['bytes'] for f in fonts.values()),directory=str(root/DIRECTORY))
