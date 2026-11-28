"""Verify the saved anthology, render complete spreads, and write its source guide."""
from html import escape
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import quote, urlparse
from concurrent.futures import ThreadPoolExecutor
import re
import subprocess
import sys
from PIL import Image, ImageDraw
from PySide6.QtWidgets import QApplication
from vayrshemon.file_api import FileSession
from vayrshemon.native_storage import logical_payload
from vayrshemon import pages
from tools.compose_historical_book import mixed_persian_reading, texts
from tools.poetic_anthology import ROOT, WORK, BOOK, TARGET, TITLE, BREAK, read, write, digest
from tools.editorial_language import EditorialLanguage
from tools.prince_working import PARENT
from tools.unta_language import quantity

CREDIT = 'Song license.txt'


def overview_pages(out, total):
    folder=out/'Overview'
    folder.mkdir(exist_ok=True)
    overviews=[]
    for start in range(1,total+1,96):
        numbers=range(start,min(start+96,total+1))
        sheet=Image.new('RGB',(1248,((len(numbers)+11)//12)*142),'#ddd')
        draw=ImageDraw.Draw(sheet)
        for offset,n in enumerate(numbers):
            x=104*(offset%12);y=142*(offset//12)
            with Image.open(out/f'page-{n:03d}.png') as page:
                thumb=page.convert('RGB');thumb.thumbnail((99,124))
            sheet.paste(thumb,(x+2,y+15));draw.text((x+2,y),str(n),fill='#222')
        path=folder/f'overview-{len(overviews)+1:02d}.jpg'
        sheet.save(path,quality=86)
        overviews.append(path.name)
    return overviews


def render_range(native, out, staging, first, last):
    app=QApplication.instance() or QApplication([])
    session=FileSession(ROOT,source_fonts=False,recovery=False)
    session.remember=lambda _:None
    session.log.emit=lambda *args,**kwargs:None
    try:
        session.open(native,advance_revision=False)
        for number in range(first,last+1):
            page=session.state['pages'][number-1]
            filename=f'page-{number:03d}.png'
            staged=staging/filename
            pages.render(session,page_id=page['pageId'],path=staged,mode='mono',dpi=96,page_mode='two')
            staged.replace(out/filename)
    finally:
        session.finish()


def guide(works, spreads, counts):
    rows = []
    for r in works:
        key=r['id']
        pages_for_work = [s for s in spreads if any(u.startswith(key+'.') for u in s['unitIds'])]
        pages_label=f"{pages_for_work[0]['leftPage']}–{pages_for_work[-1]['rightPage']}"
        sources = [f'<a href="{escape(url,quote=True)}">{escape(urlparse(url).netloc.removeprefix("www."))}</a>' for url in r['sources']]
        witness = f'<a href="Working/Sources/{key}.txt">Edition text</a>'
        note = r['note'].replace('by Jayna Brown','of the recording')
        rows.append(f'<tr id="work-{key}"><td>{escape(r["date"])}</td><td><b>{escape(r["title"])}</b>'
                    f'<br>{escape(r["genre"])}<p>{escape(note)}</p>{witness} · {" · ".join(sources)}</td>'
                    f'<td>{pages_label}</td></tr>')
    (BOOK/CREDIT).write_text(
        'Copying Is Not Theft\n\n'
        'Lyrics and tune by Nina Paley. First published December 15, 2009.\n'
        'Original lyric sheet: https://ninapaley.com/2009/12/15/minute-meme-1-copying-is-not-theft/\n'
        'License record: https://commons.wikimedia.org/wiki/File:Copying_Is_Not_Theft.webm\n'
        'Creative Commons Attribution-ShareAlike 3.0 Unported.\n'
        'https://creativecommons.org/licenses/by-sa/3.0/\n\n'
        'The Vayrshemon translation, transliteration and construction gloss of this song are an adaptation '
        'distributed under the same license. The English lyrics reproduce the December 2009 text. '
        'The anthology includes the words alone. Keep this notice with distributed copies.\n\n'
        'Rent Strike\n\n'
        'David Rovics. From I Heard a Rumor, released July 16, 2024.\n'
        'Original lyric sheet: https://davidrovics.bandcamp.com/track/rent-strike\n'
        'Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International.\n'
        'https://creativecommons.org/licenses/by-nc-sa/4.0/\n\n'
        'The English column gives the complete published words. The Vayrshemon translation, '
        'transliteration and construction gloss are an adaptation distributed under the same '
        'noncommercial, share-alike license. Keep this notice with distributed copies.\n',
        encoding='utf8')
    with (BOOK/CREDIT).open('a',encoding='utf8') as credits:
        credits.write('\nAdditional texts, recordings and adaptations\n\n')
        for r in works:
            c=r.get('credit')
            if not c:continue
            credits.write(r['title']+'\n')
            if r.get('originalTitle') and r['originalTitle']!=r['title']:
                credits.write(r['originalTitle']+'\n')
            for field in ('name','journal','sourceEdition','notice','url','license'):
                if c.get(field):credits.write(c[field]+'\n')
            for url in r['sources']:
                if url!=c.get('url'):credits.write(url+'\n')
            credits.write('The native translation, construction gloss and any new English reading are adaptations distributed under the license above.\n\n')
    titles = {r['id']: r['title'] for r in works}
    paths = [
        ('Working for a living', ['plantain','harvestmeal','osageplant','flourprice','preacher','rentstrike']),
        ('Desire, insult and double standards', ['songofsongs','cat16','redondillas','westernrose','masochism','agnes']),
        ('What the living owe the dead', ['unas','brotherashes','deadlords','twacorbbies','cremation','brokenstring','lynching']),
        ('The answering voice', ['round','welcomesong','linky','hangingjohnny','womanlifefreedom']),
        ('An evening of bad company', ['doctorundertaker','purewine','swanroast','gallowsquatrain','bonanox','cremation','hand']),
        ('A market, a riot, a rent strike', ['atl4536','riotcity','allanar','atl5862','rentstrike']),
        ('After hours', ['firstmay','codemonkey','fuckxmas','punkworst','vn72079']),
    ]
    paths_html = ''.join('<p><b>' + name + '</b><br>' + ' · '.join(
        f'<a href="#work-{key}">{escape(titles[key])}</a>' for key in keys) + '</p>' for name, keys in paths)
    eras=[(-10000,0,'BCE'),(0,1000,'1–999 CE'),(1000,1500,'1000–1499'),(1500,1800,'1500–1799'),
          (1800,1900,'1800–1899'),(1900,1980,'1900–1979'),(1980,2000,'1980–1999'),
          (2000,2010,'2000–2009'),(2010,2020,'2010–2019'),(2020,2100,'2020 onward')]
    era_links=[]
    for lo,hi,label in eras:
        group=[r for r in works if lo<=r['sort']<hi]
        if group:era_links.append(f'<a href="#work-{group[0]["id"]}">{label}</a> ({len(group)})')
    html=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{TITLE} — Contents and sources</title>
<style>html{{color-scheme:light}}body{{color:#292622;background:#fbfaf7;max-width:54rem;margin:3rem auto;padding:0 1.2rem;font:1rem/1.5 Georgia,serif}}h1{{font-size:2.4rem;line-height:1.15;margin-bottom:.2rem}}h2{{font-size:1.35rem}}p{{margin:.45rem 0 .85rem}}table{{border-collapse:collapse;width:100%;text-align:left}}td,th{{border-bottom:1px solid #d9d3c7;padding:.75rem .5rem;vertical-align:top}}td:first-child{{width:19%}}td:last-child{{white-space:nowrap}}a{{color:#315361}}small{{color:#514e47}}@media(max-width:34rem){{body{{margin:1rem auto}}td,th{{padding:.5rem .25rem}}}}</style>
<h1>{TITLE}</h1><p><i>Poetic Anthology</i></p>
<p><a href="{quote(TARGET.name)}">Open the four-column manuscript</a> · {counts['pages']} native pages · {len(works)} complete works</p>
<p><i>Gimōvīv</i> joins <i>gimōv</i> (many) and <i>īv</i> (write). <i>Lilangsōlum’na</i> is the poet noun <i>lilangsōlum</i> with the adjective ending <i>’na</i>.</p>
<h2>Ways through the book</h2>
{paths_html}
<h2>Chronological contents and sources</h2>
<nav aria-label="Jump to a period"><p>{' · '.join(era_links)}</p></nav>
<p>Dates refer to composition, first publication or recording where known. A witness date identifies when a particular text was documented. Ancient ranges can overlap. The collection range is given when the individual poem cannot be dated more closely.</p>
<p>The rightmost column pairs the Nahuatl mourning song with its 1887 English translation. Selections in Chinese, Tamil, Greek, Latin, Japanese, Persian, Middle English, French, German, Spanish, Hawaiian and Kurdish also carry English readings where both texts are given. The ǀXam songs use the historical English witnesses identified below. The psalms and the eight chapters of the Song of Songs use King James English. In the Jamaican digging songs the spelling and the workers’ answers follow the collector’s transcript.</p>
<p>The Polish poems carry the full Polish witness and a new English reading. In the additional Japanese waka, the English verse alongside the romanized Japanese is the historical reading translated into Vayrshemon. The 1925 North American song collection supplies English versions of varying distance from their oral sources. Each entry names its community as recorded in that edition. Dates attached to those songs mark publication of the English witness.</p>
<table><thead><tr><th>Date</th><th>Work and witness</th><th>Pages</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
<p><a href="{quote(CREDIT)}">Credits and licenses for poems, songs and translations</a></p></html>'''
    (BOOK/'Contents and sources.html').write_text(html,encoding='utf8')


def verify():
    works=read(WORK/'works.json')
    ledger=read(WORK/'ledger.json')['units']
    proof=read(WORK/'layout-validation.json')
    source=read(WORK/'source-validation.json')
    index=read(WORK/'page-index.json')['spreads']
    assert proof['sha256']==source['sha256']==digest(TARGET)
    assert proof['allFourColumnsMatchLedger'] and proof['saveReopenIdentical'] and proof['maxBaselineErrorPt'] <= .02
    assert not proof['verticalOverset'] and not proof['missingGlyphs']
    assert len(read(WORK/'numbering-validation.json')) == proof['pages']*2
    assert len({u['id'] for u in ledger})==len(ledger)
    by_id={u['id']:u for u in ledger}
    native=logical_payload(read(TARGET))['state']
    assert native['title'].startswith(TITLE+' · ')
    orth=EditorialLanguage(PARENT/'Language')
    assert orth.reading(by_id['front.title']['text'])==TITLE
    assert by_id['front.title']['source']=='Poetic Anthology'
    assert [u['id'] for u in ledger if u['id'].endswith('.title') and not u['id'].startswith(('front.','contents.'))]==[r['id']+'.title' for r in works]
    for spread in index:
        frames=[f for page in native['pages'][spread['leftPage']-1:spread['rightPage']] for f in sorted(page['frames'],key=lambda f:int(f['x']))]
        assert len(frames)==4
        for frame,field in zip(frames,['text','text','gloss','source']):
            assert texts(frame)==[by_id[uid][field] for uid in spread['unitIds']]
        source_blocks=frames[-1]['content']['document']['stories'][0]['blocks']
        assert all(b['direction']=='ltr' for b,uid in zip(source_blocks,spread['unitIds'])
                   if mixed_persian_reading(by_id[uid]['source']))
    for r in works:
        k=r['id']; path=WORK/'Sources'/(k+'.txt')
        full=path.read_text(encoding='utf8').splitlines()
        body=[u for u in ledger if u['id'].startswith(k+'.') and 'lines' in u]
        assert digest(path)==source['sources'][k]['sha256']
        assert full==[line for u in body for line in u['originalSource'].split('\n')]
        assert full==[line for u in body for line in u['source'].split(BREAK)[:u['lines'][1]-u['lines'][0]+1]]
        assert all(u['text'].strip() and u['gloss'].strip() for u in body)
        if r['genre']=='Poland · contemporary poetry' or k.startswith('ogura'):
            assert all(u.get('englishReading') for u in body),k
        assert all('[…]' not in u['source'] and '[...]' not in u['text'] for u in body)
        folio=source['entryOpenings'][k]
        assert by_id['contents.'+k]['source'].endswith('p. '+str(folio))
        assert by_id['contents.'+k]['text'].endswith(quantity(folio,notation='digits')['form'])
    assert source['sources']['blues']['lines']==21 and source['sources']['many']['lines']==20
    assert by_id['psalm.9']['inheritedUnit']=='19.137.009'
    assert source['sources']['sonnet']['lines']==14
    assert [by_id['tequila.'+str(n)]['text'] for n in (1,2,3)]==[by_id['tequila.1']['text']]*3
    assert works[0]['id']=='unas' and works[-1]['id']=='atl5978'
    assert len(works)>=660 and [r['sort'] for r in works]==sorted(r['sort'] for r in works)
    prior=ROOT/'Saves/Archive/Previous editions/Poetic Anthology - 165 works/Working'
    oldworks=read(prior/'works.json')
    normalized={re.sub(r'\W','',(WORK/'Sources'/(r['id']+'.txt')).read_text(encoding='utf8')).casefold() for r in works}
    assert len(normalized)==len(works)>=4*len(oldworks)
    preserved=0
    for u in read(prior/'ledger.json')['units']:
        if u['id'].startswith('contents.'):continue
        assert all(by_id[u['id']][col]==u[col] for col in ('text','gloss','source')),u['id']
        preserved+=int('lines' in u)
    audit=read(WORK/'expansion-audit.json')
    audit.update(originalAlignedLiteraryUnitsPreserved=preserved,uniqueCompleteTexts=len(normalized),
                 fullPolishAndEnglishParallelReadings=sum(r['genre']=='Poland · contemporary poetry' for r in works),
                 nativeSha256=digest(TARGET))
    write(WORK/'expansion-audit.json',audit)
    assert [u['inheritedUnit'] for u in ledger if u['id'].startswith('songofsongs.') and 'lines' in u] == [
        f'22.{c:03}.{v:03}' for c,n in enumerate([17,17,11,16,16,13,13,14],1) for v in range(1,n+1)]
    for k,n in {'cremation':68,'redondillas':68,'bonanox':9,'rentstrike':28,'preacher':40,
                'cat16':14,'masochism':50,'agnes':33}.items():
        assert source['sources'][k]['lines']==n,(k,n)
    for k in ('cremation','cat16'):
        lines=(WORK/'Sources'/f'{k}.txt').read_text(encoding='utf8').splitlines()
        repeat=8 if k=='cremation' else 1
        assert [s.rstrip('.,!;:').casefold() for s in lines[:repeat]]==[
                s.rstrip('.,!;:').casefold() for s in lines[-repeat:]]
    guide(works,index,proof)

    out=WORK/'Proofs'
    out.mkdir(exist_ok=True)
    total=proof['pages']
    del native
    with TemporaryDirectory(dir=out) as staging:
        if total<1200:
            render_range(TARGET,out,Path(staging),1,total)
        else:
            step=(total+3)//4
            def render_section(first):
                last=min(first+step-1,total)
                subprocess.run([sys.executable,'-X','utf8','-m','tools.poetic_anthology_proof','--render-range',
                                str(TARGET),str(out),staging,str(first),str(last)],cwd=ROOT,check=True)
            with ThreadPoolExecutor(max_workers=4) as pool:
                list(pool.map(render_section,range(1,total+1,step)))
    rendered=[out/f'page-{n:03d}.png' for n in range(1,total+1)]
    assert all(p.is_file() for p in rendered)
    sheets=[]
    for start in range(0,len(rendered),10):
        subset=rendered[start:start+10]
        sheet=Image.new('RGB',(1440,((len(subset)+3)//4)*489),'#ddd')
        # Keep consecutive facing pages adjacent and one label outside the page image.
        for j,path in enumerate(subset):
            with Image.open(path) as im:
                thumb=im.convert('RGB');thumb.thumbnail((348,452))
            x=(j%4)*360+6; y=(j//4)*489+23
            sheet.paste(thumb,(x,y));ImageDraw.Draw(sheet).text((x,y-17),f'Page {start+j+1}',fill='#222')
        dest=out/f'spread-sheet-{start//10+1:02d}.jpg'
        sheet.save(dest,quality=88)
        sheets.append(dest.name)
    review_file=WORK/'visual-review.json'
    overviews=overview_pages(out,total)
    review=read(review_file) if review_file.is_file() else {}
    status='See visual-review.json' if review.get('nativeSha256')==proof['sha256'] and review.get('reviewedPages',0)>0 else 'pending'
    write(WORK/'publication-check.json',dict(nativeSha256=proof['sha256'],pages=proof['pages'],
          works=len(works),sourceLines=source['sourceLines'],units=len(ledger),proofSheets=sheets,overviewSheets=overviews,
          title=TITLE,titleEnglish='Poetic Anthology',fourReopenedColumns=True,allSourcesReconstructed=True,
          contentsVerified=True,renderedPages=len(rendered),visualReview=status))
    print('Verified',len(works),'works and',len(rendered),'saved pages.',flush=True)

if __name__=='__main__':
    if len(sys.argv)==7 and sys.argv[1]=='--render-range':
        render_range(Path(sys.argv[2]),Path(sys.argv[3]),Path(sys.argv[4]),int(sys.argv[5]),int(sys.argv[6]))
    else:
        verify()
