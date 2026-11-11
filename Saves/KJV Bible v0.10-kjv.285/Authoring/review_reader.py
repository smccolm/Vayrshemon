"""Open the saved publication in Reader and render selected pages."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from PySide6.QtWidgets import QApplication
from Reader.storage import build,cache_path
from Reader.render import Engine,read_image
from tools.kjv_native_vocabulary import OUT,COMPACT
from tools.kjv_archive import read
from tools.m0.common import file_hash,write_json

def main(compact):
    folder=COMPACT if compact else OUT
    target=next(folder.glob('*.vay'))
    before=file_hash(target)
    app=QApplication([])
    opened=build(target,lambda stage,pct:print(pct,stage,flush=True))
    engine=Engine(cache_path(target))
    if compact:
        report=read(folder/'review-validation.json')
        picks=[(p['firstPage']+side,p['name']) for p in report['previewSpreads']
               if p['name'] in ('frontispiece-opening','alpha-omega','first-and-last','final-spread')
               for side in (0,1)]
    else:
        index=read(OUT/'page-index.json')
        refs=('Genesis 1:13','Revelation 1:8','Revelation 22:13')
        picks=[(p[side],r) for p in index['spreads'] for r in refs if r in p['references']
               for side in ('leftPage','rightPage')]
        picks.append((index['pages'],'ending'))
    checks=[]
    for n,ref in picks:
        output=engine.render(n,'white','two',1.)
        im=read_image(output['path'])
        assert not im.isNull()
        dest=folder/('Previews' if compact else 'Proofs')/f'reader-page-{n}.png'
        assert im.save(str(dest))
        checks.append(dict(page=n,reading=ref,renderMilliseconds=output['milliseconds']))
    assert file_hash(target)==before
    write_json(folder/'reader-review.json',dict(sha256=before,pages=engine.index.meta['pageCount'],index=opened,checks=checks))
    print(checks,flush=True)

if __name__=='__main__':main(sys.argv[1]=='compact')
