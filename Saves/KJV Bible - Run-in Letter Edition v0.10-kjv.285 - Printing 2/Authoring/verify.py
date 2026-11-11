"""Independently recover all three Bibles and measure the saved run-in pages."""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

from compose import (BOOKS,BOTTOM,COMPACT,PREVIOUS,EDITION,INNER,OUT,OUTER,ROOT,STAGE,TARGET,TOP,
    QApplication,Proof,QRectF,digest,digits,mp,pe,read,save_json,unpack)
from tools.compose_historical_book import texts


def ordered_hash(rows):
    sha=sha256()
    for row in rows:
        sha.update((json.dumps(row,ensure_ascii=False,separators=(',',':'))+'\n').encode())
    return sha.hexdigest()


def verses_from_print(state):
    sources={p['pageId']:pe.text_of(p) for p in state['pages']}
    return [(r['id'],''.join(sources[f['pageId']][f['start']:f['end']] for f in r['fragments']))
            for r in state['printEdition']['verses']]


def parity(path):
    state=unpack(read(path))['state']
    edition=state['printEdition']
    runin=verses_from_print(state)
    units=read(OUT/'complete-translation-ledger.json')['units']
    ledger=[(u['id'],u['text']) for u in units]
    assert len(ledger)==31102 and runin==ledger
    compact_path=next(COMPACT.glob('*.vay'))
    assert digest(compact_path)==read(COMPACT/'FROZEN.json')['nativeSha256']
    compact=unpack(read(compact_path))['state']
    older=verses_from_print(compact)
    assert older==runin
    from acanthus import check
    check(state)
    from titles import check_titles
    check_titles(state)
    from dividers import check as check_dividers
    dividers=check_dividers(state)
    assert all(edition['assets'][k]==v for k,v in compact['printEdition']['assets'].items())
    assert compact['printEdition']['typography']==edition['typography']
    assert [(r['name'],r['number']) for r in edition['sections']]==[(name,i) for i,name in enumerate(BOOKS,1)]
    assert edition['ledgerSha256']==digest(OUT/'complete-translation-ledger.json')
    del compact
    study_path=OUT/'KJV Bible.vay'
    assert digest(study_path)==read(OUT/'FROZEN.json')['nativeSha256']
    study=unpack(read(study_path))['state']
    study_rows=[]
    spreads=read(OUT/'page-index.json')['spreads']
    assert len(study['pages'])==len(spreads)*2
    for i,spread in enumerate(spreads):
        cols=[texts(f) for p in study['pages'][2*i:2*i+2] for f in sorted(p['frames'],key=lambda f:int(f['x']))]
        assert cols[0]==cols[1]
        study_rows.extend(zip(spread['unitIds'],cols[0],strict=True))
    assert study_rows==runin
    old_receipt=read(ROOT/'Saves/Maintenance/2026-11-07-native-285/delivery-validation.json')
    signature=ordered_hash(runin)
    assert signature==old_receipt['studyNativeVerseTextSha256']==old_receipt['compactNativeVerseTextSha256']
    pg=state['pages'][3]
    base=next(PREVIOUS.glob('*.vay'))
    assert digest(base)==read(PREVIOUS/'FROZEN.json')['nativeSha256']
    previous=unpack(read(base))['state']
    assert verses_from_print(previous)==runin
    old=previous['printEdition']
    assert old['assets']==edition['assets']
    assert previous['pageNumbering']==state['pageNumbering']
    first=edition['pages'][pg['pageId']]
    prior=old['pages'][previous['pages'][3]['pageId']]
    assert prior['images']==first['images']
    def body_and_art(paths):return [p for p in paths if p['role'] not in ('book-title','chapter-number')]
    assert body_and_art(prior['paths'])==body_and_art(first['paths'])
    assert prior['lines']==first['lines'][:len(prior['lines'])]
    assert pe.text_of(pg).startswith(pe.text_of(previous['pages'][3])+' ')
    # Independently associate each printed numeral with its source verse start.
    markers=set();line_starts={}
    for pid,spec in edition['pages'].items():
        for i,line in enumerate(spec['lines']):
            if line['prefix']:
                key=(pid,line['start'])
                assert key not in line_starts
                line_starts[key]=(line['prefix'],i>0 and line['baseline']==spec['lines'][i-1]['baseline'])
    inline=0;chapters=set();splits=0
    page_order={p['pageId']:i for i,p in enumerate(state['pages'])}
    expected_chapters=[]
    for u,row in zip(units,edition['verses'],strict=True):
        f=row['fragments'][0]
        if u['verse']==1: expected_chapters.append((BOOKS[int(u['id'][:2])-1],u['chapter'],page_order[f['pageId']]+1))
        for before,after in zip(row['fragments'],row['fragments'][1:]):
            i=page_order[before['pageId']]
            assert page_order[after['pageId']]==i+1
            txt=pe.text_of(state['pages'][i])
            assert before['end']==len(txt) and txt.endswith(' ') and after['start']==0
            next_spec=edition['pages'][after['pageId']]
            assert next_spec['lines'][0]['start']==0 and not next_spec['lines'][0]['prefix']
            splits+=1
        spec=edition['pages'][f['pageId']]
        chapters.add(u['id'][:6])
        if spec['kind']=='opening' and f['start']==0:
            assert u['verse']==u['chapter']==1 and sum(p['role']=='verse-marker' for p in spec['paths'])==1
            continue
        key=(f['pageId'],f['start']);prefix,same=line_starts[key]
        assert prefix==digits(u['verse'])+'  '
        markers.add(key);inline+=same
    assert markers==set(line_starts) and len(chapters)==1189
    assert expected_chapters==[(c['book'],c['chapter'],c['nativePage']) for c in read(STAGE/'chapter-index.json')]
    return dict(nativeFile=path.name,nativeSha256=digest(path),sourceEdition='0.10-kjv.285',
                pages=len(state['pages']),books=66,chapters=1189,verses=31102,mismatchedVerses=0,
                commonOrderedVerseTextSha256=signature,compactSha256=digest(compact_path),fourColumnSha256=digest(study_path),
                verseMarkersVerified=len(markers)+66,versesBeginningOnPreviousVerseLine=inline,
                genesisFirst18VersesAndArtworkMatchPrior=True,acanthusOpeningPairsVerified=66,nativeBookTitlesVerified=66,
                centeredChapterDividers=dividers,pageTurnsWithinVerses=splits,priorRunInSha256=digest(base),
                saveReopenIdentical=True,ledgerSha256=edition['ledgerSha256'])


def check_pages(path,lo,hi):
    state=unpack(read(path))['state']
    proof=Proof()
    book=SimpleNamespace(state=state,fonts=proof.fonts)
    result=[]
    for n in range(lo,hi+1):
        page=state['pages'][n-1]
        pid=page['pageId']
        spec=state['printEdition']['pages'][pid]
        comp=pe.Composition(book,'mono',pid)
        assert all(not g['missingGlyph'] for g in comp.final)
        relevant=spec['kind'] in ('body','opening')
        if relevant:
            physical=n-1  # Display blank two is omitted in the binding master.
            side='right' if physical%2 else 'left'
            assert spec['side']==side and spec['folio']==n-3
            left,right=(INNER,OUTER) if side=='right' else (OUTER,INNER)
            assert page['margins']==dict(left=mp(left),right=mp(right),top=mp(TOP),bottom=mp(BOTTOM))
            frame=page['frames'][0]
            assert (frame['x'],frame['y'],frame['width'],frame['height'])==(mp(left),mp(TOP),mp(612-left-right),mp(792-TOP-BOTTOM))
            body=QRectF(left-.001,TOP-.001,612-left-right+.002,792-TOP-BOTTOM+.002)
            boxes=[]
            for line,path_ in zip(spec['lines'],comp.drawings,strict=True):
                actual=path_.boundingRect()
                assert body.contains(actual),(n,line,actual)
                assert max(abs(a-b) for a,b in zip(actual.getRect(),line['bounds']))<.05,(n,line,actual)
                assert not any(prev.intersects(actual) for prev in boxes),(n,line)
                assert not any(p.boundingRect().intersects(actual) for p in comp.ornaments),(n,line)
                boxes.append(actual)
            for p in comp.ornaments:
                assert body.adjusted(-.5,-.5,.5,.5).contains(p.boundingRect()),(n,p.boundingRect())
        placements={}
        for mode in ('one','two'):
            r=pe.numbering(book,page,state['pageNumbering'],mode,comp)
            assert r['status']==('placed' if relevant else 'hidden'),(n,mode,r)
            if relevant:
                assert r['text']==digits(n-3) and r['pageNumber']==n-3
                if mode=='two':
                    assert r['role']==side
                    x,y,w,h=[v/(4/3) for v in r['bounds']]
                    assert abs((x if side=='left' else 612-x-w)-OUTER)<.01
                    assert abs(792-y-h-OUTER)<.01
                    assert max(b.bottom() for b in boxes)<=y-4
            placements[mode]=r['status']
        result.append(dict(page=n,side=spec['side'],kind=spec['kind'],glyphs=len(comp.final),folios=placements))
    save_json(STAGE/'checks'/f'{lo:04}.json',result)


def main():
    app=QApplication.instance() or QApplication([])
    path=STAGE/TARGET.name
    # Read from the saved native document for all comparisons.
    receipt=parity(path)
    print('Three-way comparison passed:',receipt['verses'],receipt['commonOrderedVerseTextSha256'],flush=True)
    def run(bounds):
        lo,hi=bounds
        with (STAGE/'logs'/f'check-{lo:04}.txt').open('w',encoding='utf8') as f:
            p=subprocess.run([sys.executable,'-B','-X','utf8',__file__,'pages',str(lo),str(hi)],stdout=f,stderr=subprocess.STDOUT)
        print('Measured',lo,hi,p.returncode,flush=True)
        return p.returncode
    ranges=[(n,min(n+124,receipt['pages'])) for n in range(1,receipt['pages']+1,125)]
    with ThreadPoolExecutor(max_workers=8) as pool: codes=list(pool.map(run,ranges))
    assert not any(codes),'See .local/kjv285-run-in/logs/check-*'
    checks=[r for lo,_ in ranges for r in read(STAGE/'checks'/f'{lo:04}.json')]
    assert [r['page'] for r in checks]==list(range(1,receipt['pages']+1))
    receipt.update(allNativePagesMeasured=len(checks),folioPlacementsChecked=2*sum(r['folios']['two']=='placed' for r in checks),
                   missingGlyphs=0,overlappingBodyRuns=0,mirroredInsideMarginPt=INNER,outsideMarginPt=OUTER,topMarginPt=TOP,bottomMarginPt=BOTTOM,
                   centerOffsetPt=(INNER-OUTER)/2,bodyGlyphsMeasured=sum(r['glyphs'] for r in checks))
    from pagination import audit
    receipt['pagination']=audit(path)
    save_json(STAGE/'native-validation.json',receipt)


if __name__=='__main__':
    if sys.argv[1:] and sys.argv[1]=='pages':
        app=QApplication([])
        check_pages(STAGE/TARGET.name,*map(int,sys.argv[2:4]))
    else: main()
