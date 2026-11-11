"""Check the delivered native file in Reader and compare printed ink at page scale."""
from pathlib import Path
import subprocess
import sys
from PIL import Image, ImageChops, ImageFilter, ImageDraw, ImageFont
from compose import (PREVIOUS,EDITION,STAGE,TARGET,QApplication,digest,read,save_json,unpack)
from Reader.storage import build,cache_path
from Reader.render import Engine,read_image


def reader_samples():
    path=STAGE/TARGET.name
    receipt=read(STAGE/'native-validation.json')
    assert digest(path)==receipt['nativeSha256']
    if not TARGET.exists():
        # The checked file and the edition are on the same volume.
        from shutil import copyfile
        tmp=TARGET.with_suffix('.partial')
        copyfile(path,tmp)
        assert digest(tmp)==receipt['nativeSha256']
        if TARGET.exists(): raise FileExistsError(TARGET)
        tmp.rename(TARGET)
    assert digest(TARGET)==receipt['nativeSha256']
    app=QApplication([])
    build(TARGET,lambda step,pct: print(pct,step,flush=True))
    engine=Engine(cache_path(TARGET))
    assert engine.index.meta['pageCount']==receipt['pages'] and len(engine.index.meta['sections'])==66
    state=unpack(read(TARGET))['state']
    edition=state['printEdition']
    positions={p['pageId']:i for i,p in enumerate(state['pages'],1)}
    section=next(s for s in edition['sections'][1:] if positions[s['pageId']]%2==1)
    left_open=positions[section['pageId']]
    omega=next(r for r in edition['verses'] if r['id']=='66.022.013')
    omega_page=positions[omega['fragments'][0]['pageId']]
    psalm=next(s for s in read(STAGE/'chapter-index.json') if s['book']=='Psalms' and s['chapter']==119)['nativePage']
    exodus=receipt['pagination']['revisedExodus28Pages']
    exodus_left=exodus[0]['nativePage']
    assert exodus_left%2 and exodus[-1]['nativePage']==exodus_left+1
    genesis21=next(s['nativePage'] for s in read(STAGE/'chapter-index.json') if s['book']=='Genesis' and s['chapter']==21)
    assert genesis21==27
    samples=sorted({1,2,3,4,5,6,7,14,genesis21,genesis21+1,left_open,left_open+1,psalm,psalm+1,omega_page,exodus_left,exodus_left+1,
                    len(state['pages'])-2,len(state['pages'])-1,len(state['pages'])}|
                   {positions[s['pageId']] for s in edition['sections']})
    dest=STAGE/'reader'; dest.mkdir(exist_ok=True)
    for n in samples:
        rendered=engine.render(n,'white','two',1.)
        image=read_image(rendered['path'])
        assert not image.isNull() and image.save(str(dest/f'{n:04}.png'))
    # The opening now flows past verse 18. Compare the art and all completed
    # physical rows above the old final row. Its new right-hand tail is in use.
    original=next(PREVIOUS.glob('*.vay'))
    build(original,lambda *args:None)
    previous_engine=Engine(cache_path(original))
    old_state=unpack(read(original))['state']
    old_spec=old_state['printEdition']['pages'][old_state['pages'][3]['pageId']]
    cutoff=int((old_spec['lines'][-1]['baseline']-13)*4/3)
    old=read_image(previous_engine.render(4,'white','two',1.)['path'])
    actual=read_image(engine.render(4,'white','two',1.)['path'])
    # Compare the same art and text, excluding just the central title field.
    from PySide6.QtGui import QPainter,QColor
    for image in (old,actual):
        painter=QPainter(image)
        painter.fillRect(292,76,257,108,QColor('white'))
        painter.end()
    assert old.copy(0,0,old.width(),cutoff)==actual.copy(0,0,actual.width(),cutoff)
    save_json(STAGE/'reader-validation.json',dict(nativeSha256=digest(TARGET),pages=engine.index.meta['pageCount'],
        sampleNativePages=samples,genesisArtworkAndLeadingRowsMatchPrior=True,titleFieldExcludedFromPriorComparison=True,leftOpening=left_open,leftOpeningBook=section['name'],
        psalmsPage=psalm,omegaPage=omega_page,exodusExampleLeftNative=exodus_left))


def print_samples():
    reader=read(STAGE/'reader-validation.json')
    report=read(STAGE/'print-validation.json')
    dest=STAGE/'pdf-proofs';dest.mkdir(exist_ok=True)
    pdf=STAGE/'KJV Bible - Run-in Letter - Printing 2 - Duplex Print.pdf'
    results=[]
    ordered=report['printToNativePage']
    for n in reader['sampleNativePages']:
        if n not in ordered: continue
        physical=ordered.index(n)+1
        prefix=dest/f'{physical:04}'
        subprocess.run(['pdftoppm','-f',str(physical),'-l',str(physical),'-r','96','-singlefile','-png',str(pdf),str(prefix)],check=True)
        a=Image.open(STAGE/'reader'/f'{n:04}.png').convert('L')
        b=Image.open(prefix.with_suffix('.png')).convert('L')
        assert a.size==b.size==(816,1056)
        def ink(img): return img.point(lambda p:255 if p<185 else 0)
        a,b=ink(a),ink(b)
        def missing(img,against):
            return sum(ImageChops.subtract(img,against.filter(ImageFilter.MaxFilter(3))).histogram()[1:])/sum(img.histogram()[1:])
        native_only,print_only=missing(a,b),missing(b,a)
        assert max(native_only,print_only)<.01,(n,physical,native_only,print_only)
        results.append(dict(nativePage=n,physicalPage=physical,nativeUnmatchedInk=native_only,printUnmatchedInk=print_only))
    save_json(STAGE/'visual-comparison.json',results)
    make_title_proofs(dest)
    physical=[(2,3),(4,5),(reader['leftOpening']-1,reader['leftOpening']),
              (reader['psalmsPage']-1,reader['psalmsPage']), (len(ordered)-1,len(ordered)),
              (reader['exodusExampleLeftNative']-1,reader['exodusExampleLeftNative'])]
    for i,pair in enumerate(physical,1):
        out=Image.new('RGB',(880,600),'#dadcde')
        draw=ImageDraw.Draw(out)
        for j,n in enumerate(pair):
            im=Image.open(dest/f'{n:04}.png').convert('RGB')
            im.thumbnail((428,558),Image.Resampling.LANCZOS)
            x=4+440*j
            draw.text((x,6),f'Print page {n}',fill='black')
            out.paste(im,(x,29))
        out.save(dest/f'sheet-{i}.jpg',quality=94)


def make_title_proofs(dest):
    books=read(STAGE/'book-index.json')
    titles=read(STAGE/'book-titles.json')
    font=ImageFont.truetype('segoeui.ttf',15)
    for start in range(0,len(books),12):
        subset=list(zip(books[start:start+12],titles[start:start+12],strict=True))
        board=Image.new('RGB',(1200,135*((len(subset)+1)//2)),'#e5e4e1')
        draw=ImageDraw.Draw(board)
        for i,(book,title) in enumerate(subset):
            n=book['firstPrintPage']
            assert book['name']==title['book']
            a=96 if n%2 else 72
            with Image.open(dest/f'{n:04}.png') as p:
                strip=p.crop((a-3,61,a+651,202)).convert('RGB')
            strip.thumbnail((590,107),Image.Resampling.LANCZOS)
            x=600*(i%2);y=135*(i//2)
            draw.text((x+8,y+2),f"{title['book']}  /  {title['roman']}",font=font,fill='black')
            board.paste(strip,(x+8,y+23))
        board.save(dest/f'titles-{1+start//12}.png')


if __name__=='__main__':
    if sys.argv[1]=='reader': reader_samples()
    else: print_samples()
