"""Inspect the pinned runtime closure and bundled license notices without network."""
import argparse
import hashlib
from importlib import metadata
import json
from pathlib import Path
import re


def pins(path):
    result={}
    for line in Path(path).read_text().splitlines():
        line=line.strip()
        if line.startswith('-r '): result.update(pins(Path(path).parent/line[3:]))
        elif line and not line.startswith('#'):
            name,version=line.split('==');result[name.lower().replace('_','-')]=version
    return result


def audit(root):
    required=pins(Path(root)/'requirements-m12.txt');items=[]
    for name,version in sorted(required.items()):
        dist=metadata.distribution(name)
        if dist.version!=version: raise ValueError('DEPENDENCY_VERSION_MISMATCH: '+name)
        notices=[]
        for file in dist.files or []:
            if any(word in str(file).lower() for word in ('license','copying','copyright','notice')) and not str(file).endswith(('.py','.pyc','.so','.dll')):
                path=Path(dist.locate_file(file))
                if path.is_file(): notices.append(dict(path=str(file).replace('\\','/'),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bytes=path.stat().st_size))
        license_value=dist.metadata.get('License-Expression') or dist.metadata.get('License') or 'See classifiers / bundled notices'
        classifiers=[v for v in dist.metadata.get_all('Classifier',[]) if v.startswith('License')]
        items.append(dict(name=name,version=version,license=license_value.splitlines()[0],licenseClassifiers=classifiers,
            home=dist.metadata.get('Home-page'),projectUrls=dist.metadata.get_all('Project-URL',[]),notices=notices,
            requires=dist.requires or []))
    return dict(version='1.0.0',scope='Pinned M0â€“M7 runtime and regression dependencies; excludes unrelated analysis packages and pip bootstrap',
        python='CPython 3.12 (PSF license; installed separately)',dependencies=items,
        packaging='Source release bundle does not redistribute Python or dependency wheels; setup installs the pinned upstream distributions with their notices intact.')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);args=p.parse_args()
    value=audit(Path(__file__).resolve().parents[1]);args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    print('Audited '+str(len(value['dependencies']))+' pinned distributions; inventory: '+str(args.out))


if __name__=='__main__': main()
