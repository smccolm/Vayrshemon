"""Private full-Bible comparison against the unchanged Workbench renderer."""
import json,time
from pathlib import Path
from PySide6.QtWidgets import QApplication
from .storage import ROOT,LOCAL,cache_path,file_hash,dumps
from .render import Engine,read_image

def main():
    from vayrshemon.file_api import FileSession
    from vayrshemon import pages,page_numbering
    source=ROOT/'Saves/KJV Bible v0.10-kjv.281/KJV Bible.vay'
    before=file_hash(source);app=QApplication([]);started=time.perf_counter()
    reference=FileSession(ROOT,recovery=False);reference.log.emit=lambda *a,**k:None
    reference.open(source,advance_revision=False)
    print('Reference full book opened in',round(time.perf_counter()-started,2),'seconds',flush=True)
    engine=Engine(cache_path(source));rows=[];folder=LOCAL/'verification';folder.mkdir(parents=True,exist_ok=True)
    for number in sorted({1,2,len(reference.state['pages'])//2+1,len(reference.state['pages'])}):
        for palette in ('white','black','color'):
            for view in ('one','two'):
                started=time.perf_counter();mode='color' if palette=='color' else 'mono'
                reference.view.update(mode=mode,monochromePaper='black' if palette=='black' else 'white')
                pid=reference.state['pages'][number-1]['pageId']
                expected,_=pages.render(reference,page_id=pid,mode=mode,dpi=62.4,page_mode=view)
                result=engine.render(number,palette,view,.65);actual=read_image(result['path'])
                equal=bytes(expected.constBits())==bytes(actual.constBits()) and expected.size()==actual.size()
                row=dict(page=number,palette=palette,view=view,pixelIdentical=equal,ms=round((time.perf_counter()-started)*1000,2))
                rows.append(row);print(json.dumps(row),flush=True)
                if number in (1,2) and view=='two':actual.save(str(folder/f'page-{number}-{palette}.png'))
                if not equal:
                    expected.save(str(folder/f'mismatch-{number}-{palette}-{view}-reference.png'));actual.save(str(folder/f'mismatch-{number}-{palette}-{view}-reader.png'))
                    raise AssertionError(str(row))
    assert file_hash(source)==before
    report=dict(source=str(source),sha256=before,pages=len(reference.state['pages']),sourceUnchanged=True,comparisons=rows,allPixelIdentical=all(r['pixelIdentical'] for r in rows))
    (folder/'fidelity.json').write_bytes(dumps(report));reference.finish();print('FIDELITY PASSED',flush=True)

if __name__=='__main__':main()

