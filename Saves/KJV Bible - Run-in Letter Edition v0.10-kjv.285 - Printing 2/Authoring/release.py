"""Seal printing 2 and point the library's run-in entry to the corrected pages."""
from html import escape
from base64 import b64encode
import json
from shutil import copyfile
from urllib.parse import quote
from PIL import Image
from compose import COMPACT,EDITION,OUT,PREVIOUS,ROOT,STAGE,TARGET,digest,read
from tools.kjv_archive import verify_seal,write_new

PDF='KJV Bible - Run-in Letter - Printing 2 - Duplex Print.pdf'


def write(p,obj):
    tmp=p.with_suffix(p.suffix+'.tmp')
    tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    tmp.replace(p)


def spread(name,physical_left):
    assert physical_left%2==0
    images=[Image.open(STAGE/'pdf-proofs'/f'{n:04}.png').convert('RGB') for n in (physical_left,physical_left+1)]
    canvas=Image.new('RGB',(1648,1056),'#e1e3e4')
    for im,x in zip(images,(0,832)): canvas.paste(im,(x,0))
    canvas.save(EDITION/'Previews'/name)


def title_guide():
    rows=read(STAGE/'book-titles.json')
    index=read(STAGE/'book-index.json')
    assert len(rows)==len(index)==66
    copyfile(STAGE/'book-titles.json',EDITION/'book-titles.json')
    headings=[]
    for r,b in zip(rows,index,strict=True):
        assert r['book']==b['name']
        headings.append('<tr>'+''.join('<td>'+escape(str(v))+'</td>' for v in
                      (r['book'],r['roman'],r['meaning'],b['firstNativePage'],b['firstPrintPage']))+'</tr>')
    header='''<!doctype html><meta charset="utf-8"><title>Vayrshemon book titles</title>
<style>body{max-width:68em;margin:3em auto;padding:0 1em;font:18px/1.5 Georgia}table{width:100%;border-collapse:collapse}td,th{padding:.4em;border-bottom:1px solid #ddd;text-align:left}th{vertical-align:bottom}p{max-width:52em}</style>
<h1>Vayrshemon book titles</h1><p>The second column gives the Roman reading of each printed banner. Community letters use the native dative for their destination. The first volume is implicit, and later volumes carry Unta figures. <i>Yōn</i> is the Gospel and <i>Yōn’īvton</i> is John’s letter. Names use historical Vayrshemon spellings or localized title forms. The headings identify the traditional books.</p>
<table><thead><tr><th>Book</th><th>Vayrshemon</th><th>English sense</th><th>Native page</th><th>Print page</th></tr></thead><tbody>'''
    gallery=[]
    for i in range(0,len(rows),12):
        pic=STAGE/'pdf-proofs'/f'titles-{1+i//12}.png'
        group=rows[i:i+12]
        label=group[0]['book']+' through '+group[-1]['book']
        data=b64encode(pic.read_bytes()).decode('ascii')
        gallery.append('<details><summary>'+escape(label)+'</summary><img style="max-width:100%;height:auto" alt="'
            +escape(label)+' printed banners" src="data:image/png;base64,'+data+'"></details>')
    (EDITION/'Book titles.html').write_text(header+''.join(headings)+'</tbody></table><h2>Printed banners</h2>'+''.join(gallery),encoding='utf8')


def main(package_only=False):
    previous=read(PREVIOUS/'edition-manifest.json')
    native=read(STAGE/'native-validation.json')
    master=read(STAGE/'print-validation.json')
    reader=read(STAGE/'reader-validation.json')
    visual=read(STAGE/'visual-comparison.json')
    assert native['nativeSha256']==reader['nativeSha256']==master['nativeSha256']==digest(TARGET)
    assert native['mismatchedVerses']==0 and native['verseMarkersVerified']==31102
    assert reader['genesisArtworkAndLeadingRowsMatchPrior'] and len(visual)==len(set(reader['sampleNativePages'])&set(master['printToNativePage']))
    assert master['pdfSha256']==digest(STAGE/PDF)
    assert native['pagination']['revised']['continuingPagesWithRoomForWholeLine']==0
    for folder in (PREVIOUS,OUT,COMPACT): verify_seal(folder)
    if not (EDITION/'FROZEN.json').exists():
        copyfile(STAGE/PDF,EDITION/PDF)
        assert digest(EDITION/PDF)==master['pdfSha256']
        (EDITION/'Previews').mkdir(exist_ok=True)
        spread('Frontispiece and Genesis.png',2)
        spread('Genesis continuation.png',4)
        spread('Exodus 28.png',reader['exodusExampleLeftNative']-1)
        spread('Genesis 21.png',26)
        # Crop from the rendered binding PDF around the screenshot's divider.
        with Image.open(STAGE/'pdf-proofs'/'0026.png') as rendered:
            assert rendered.size==(816,1056)
            rendered.crop((48,866,748,995)).save(EDITION/'Previews'/'Genesis 21 divider.png')
        title_guide()
        revelation=read(STAGE/'book-index.json')[-1]
        copyfile(STAGE/'pdf-proofs'/f'{revelation["firstPrintPage"]:04}.png',EDITION/'Previews'/'Revelation opening.png')
        for name in ('book-index.json','chapter-index.json','page-foot-audit.json'): copyfile(STAGE/name,EDITION/name)
        if (STAGE/'title-comparison.json').exists():
            comparison=read(STAGE/'title-comparison.json')
            assert comparison['nativeSha256']==native['nativeSha256']
            native['bookTitleRevision']=comparison
        write(EDITION/'edition-manifest.json',dict(title='KJV Bible · run-in Letter edition, printing 2',
            **native,artwork=previous['artwork'],native=TARGET.name,printMaster=PDF,physicalPages=master['physicalPages'],
            duplexSheets=master['duplexSheets'],printSha256=master['pdfSha256'],previousPrinting=PREVIOUS.name,
            reader=reader,printComparison=visual,verifiedVectorBounds=master['verifiedVectorBounds']))
        guide=(f"Open {TARGET.name} in Workbench or Reader. The file has {native['pages']:,} pages and all 31,102 verses in the same order and spelling as the compact and four-column editions.\n\n"
               f"Verses run continuously across pages. {native['pageTurnsWithinVerses']:,} verse continuations use the space at page ends. A verse number appears only at the beginning of the verse. A centered chapter numeral separates two equal rules, including in the shorter inline dividers. Each biblical book opens on a fresh page.\n\n"
               "The inside margin is 1 inch and the outside margin is ¾ inch. The text stays on 18 pt baselines with a 48 pt top margin. The bottom of the text area is 71 pt above the sheet edge. The folio sits outside the text, with at least 4 pt of clearance.\n\n"
               f"For binding, print {PDF} at 100% on US Letter, double-sided, flipping on the long edge. Print all {master['physicalPages']:,} pages, one page per side, with no added gutter. This uses {master['duplexSheets']} sheets. The title is on the first recto. The frontispiece faces the Genesis opening.\n\n"
               "Book-index.json and chapter-index.json locate passages. Page-foot-audit.json records the ink position on every scripture page and compares both printings of the Exodus 28 example.\n")
        (EDITION/'READ ME.txt').write_text(guide,encoding='utf8')
        links=[('Open the native Bible',TARGET.name),('Print the binding master',PDF),('All 66 Vayrshemon titles','Book titles.html'),('Revelation opening','Previews/Revelation opening.png'),('Centered chapter divider in Genesis 21','Previews/Genesis 21.png'),
               ('Genesis opening','Previews/Frontispiece and Genesis.png'),('Genesis continuation','Previews/Genesis continuation.png'),
               ('Exodus 28 spread','Previews/Exodus 28.png'),('Book index','book-index.json'),
               ('Page-foot measurements','page-foot-audit.json'),('Verification','edition-manifest.json'),('Local library','../Start here.html')]
        page='<meta charset="utf-8"><title>Run-in Letter Bible · printing 2</title><style>body{max-width:50em;margin:3em auto;font:18px/1.6 Georgia}</style><h1>Run-in Letter Bible · printing 2</h1>'
        page+='<ul>'+''.join(f'<li><a href="{quote(p,safe="/")}">{escape(label)}</a></li>' for label,p in links)+'</ul>'
        (EDITION/'Start here.html').write_text(page+''.join('<p>'+escape(s)+'</p>' for s in guide.split('\n\n')[1:]),encoding='utf8')
        files={p.relative_to(EDITION).as_posix():digest(p) for p in sorted(EDITION.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
        write_new(EDITION/'FROZEN.json',dict(book='KJV Bible - Run-in Letter Edition v0.10-kjv.285 - Printing 2',version='0.10-kjv.285',policy='never-modernize',verses=31102,
            majorSections=66,pages=native['pages'],nativeSha256=native['nativeSha256'],files=files,scope='Run-in Letter printing 2 and its duplex master, verification, proofs and authoring sources.'))
    assert verify_seal(EDITION)['nativeSha256']==native['nativeSha256']
    if package_only:return
    saves=ROOT/'Saves';lib=read(saves/'library.json')
    old=(PREVIOUS/previous['native']).relative_to(saves).as_posix()
    rel=TARGET.relative_to(saves).as_posix()
    row,=[r for r in lib['books'] if r['path'] in (old,rel)]
    row.update(title='KJV Bible · run-in Letter edition, printing 2',path=rel,guide=EDITION.name+'/Start here.html',
               pages=native['pages'],sha256=native['nativeSha256'],duplexMaster=EDITION.name+'/'+PDF,
               physicalPrintPages=master['physicalPages'],duplexSheets=master['duplexSheets'])
    if not any(r['path']==old for r in lib['earlierEditions']):lib['earlierEditions'].append(dict(label='Run-in Letter Bible · first printing with final acanthus artwork',path=old))
    write(saves/'library.json',lib)
    home=saves/'Start here.html';html=home.read_text(encoding='utf8')
    if quote(old,safe='/') in html:
        i=html.rindex('<li>',0,html.index(quote(old,safe='/')));j=html.index('</li>',i)+5
        li=(f'<li><a href="{quote(rel,safe="/")}">KJV Bible · run-in Letter edition, printing 2</a> — {native["pages"]:,} native pages. '
            f'<a href="{quote(row["duplexMaster"],safe="/")}">Duplex binding master</a> · <a href="{quote(row["guide"],safe="/")}">Edition details</a></li>')
        home.write_text(html[:i]+li+html[j:],encoding='utf8')
    before=f"The run-in Letter edition has {previous['pages']:,} native pages and a binding master of {previous['physicalPages']:,} printable pages on {previous['duplexSheets']} duplex sheets."
    after=f"The second printing of the run-in Letter edition has {native['pages']:,} native pages and a binding master of {master['physicalPages']:,} printable pages on {master['duplexSheets']} duplex sheets."
    for p in (saves/'README.txt',ROOT/'AGENTS.md',ROOT/'README.md',ROOT/'docs/CURRENT_LANGUAGE.md',ROOT/'docs/KJV_ARCHIVE.md'):
        s=p.read_text(encoding='utf8');updated=s.replace(before,after,1)
        if p==saves/'README.txt': updated=updated.replace('\n  '+old+'\n','\n  '+rel+'\n')
        if p==ROOT/'docs/KJV_ARCHIVE.md' and native['nativeSha256'] not in updated:
            updated=updated.replace('The run-in native SHA-256 is','Printing 2 allows page breaks within verses. Its native SHA-256 is `'+native['nativeSha256']+'`. Its page-foot audit and print master are in `Saves/'+EDITION.name+'/`.\n\nThe first-printing run-in native SHA-256 is',1)
        if updated!=s:p.write_text(updated,encoding='utf8')
    print(after,flush=True)


if __name__=='__main__':
    import sys
    main(package_only='--package-only' in sys.argv)
