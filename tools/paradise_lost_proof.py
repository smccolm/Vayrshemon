from pathlib import Path
import json
from tempfile import TemporaryDirectory
from shutil import copy2
from collections import Counter
from hashlib import sha256
from PySide6.QtWidgets import QApplication
from tools.paradise_lost_working import BOOK,WORK,ROOT,read,write,digest,source_inventory,load_language,SOURCE_HASH
from vayrshemon.file_api import FileSession
from vayrshemon import pages

b=read(WORK/'ledger.json');r=read(WORK/'layout-validation.json');index=read(WORK/'page-index.json')
native=BOOK/(BOOK.name+'.vay')
assert r['sha256']==digest(native)
assert b['sourceWords']==82597
assert not b['nextSourceOffset'], 'Proof a complete passage milestone'
lines,rows=source_inventory()
lastline=max(u['sourceLines'][1] for u in b['units'])
covered=[u['originalSource'] for u in b['units']]
assert '\n'.join(covered).split()=='\n'.join(lines[:lastline]).split()
assert len('\n'.join(covered).split())==b['translatedSourceWords']
expected=Counter(x['section'] for x in rows if x['kind']=='verse')
actual=Counter()
for u in b['units']:actual[u['chapter']]+=len(u['verseLines'])
completed=[k for k,v in expected.items() if actual[k]==v]
assert all(actual[k]==expected[k] for k in actual if actual[k]), 'Only issue full-book proof milestones'
verified_prefixes=[]
for checkpoint in sorted((WORK/'Milestones').glob('book-*.json')):
    baseline=read(checkpoint)
    assert len(b['units'])>=baseline['units'], ('MILESTONE_TRUNCATED',checkpoint.name)
    assert sha256(json.dumps(b['units'][:baseline['units']],sort_keys=True).encode()).hexdigest()==baseline['unitsSha256'], ('PUBLISHED_PREFIX_CHANGED',checkpoint.name)
    verified_prefixes.append(checkpoint.name)
assert all(u['source'].replace('\u2028','\n')==u['originalSource'] for u in b['units'])
assert not any('[Abridged]' in u['source'] or '[…]' in u['source'] or '[...]' in u['source'] for u in b['units'])
assert r['allFourColumnsMatchLedger'] and r['saveReopenIdentical'] and not r['missingGlyphs'] and not r['verticalOverset']
nums=read(WORK/'unta-readings.json')
assert any(n['kind']=='fraction' and n['denominator']==2 for n in nums)
assert any(n['kind']=='fold' and n['value']==3 for n in nums)
assert any(n['notation']=='digits' and n['value']==1 for n in nums)
headings={u['id'] for u in b['units'] if u['kind']=='heading'}
assert all(n['notation']=='words' for n in nums if n['unit'] not in headings)
target_lines=[1,823,825,831,833,886,956,1068,1151,1274,1340,1422,1496,1536,1612,1634,1643,1656,1705,1746,1791,1825,1869,1910,1916]
target_lines.extend([1944,2041,2104,2224,2418,2428,2462,2532,2585,2628,2661])
target_lines.extend([2702,2760,2767,2804,2840,2942,2984,3008,3111,3146,3187,3193,3265,3283,3379,3408,3427,3448,3462,3496,3513,3526,3615,3639,3683,3693,3726,3742])
target_lines.extend([3756,3814,3841,3855,3877,3919,3966,3985,4002,4043,4051,4114,4155,4185,4207,4217,4248,4262,4272,4302,4313,4365,4386,4426,4442,4496,4506,4549,4562,4601,4646,4657,4672,4692])
target_lines.extend([4711,4745,4831,4875,4892,4911,4916,4985,5021,5048,5054,5069,5075,5087,5095,5125,5147,5183,5207,5213,5233,5244,5269,5291,5316,5334,5356,5381,5390,5418,5448,5470,5493,5500,5507,5542,5573,5586,5595,5601,5610,5623,5637,5652])
target_lines.extend([5666,5670,5688,5714,5739,5780,5801,5821,5833,5846,5865,5898,5906,5918,5937,5953,5960,5978,5990,6009,6017,6036,6059,6066,6091,6106,6129,6143,6149,6160,6165,6170,6185,6200,6205,6212,6221,6246,6269,6275,6289,6301,6307,6315,6324])
target_lines += [6332,6348,6413,6454,6466,6502,6587,6634,6661,6696,6720,6761,6780,6809,6836,6846,6875,6886,6908,6943,6967,6973,6994,7006]
target_lines += [7014,7035,7087,7154,7180,7232,7307,7348,7387,7413,7452,7487,7515,7537,7568,7599,7634,7688,7732,7744,7775,7824,7835,7862,7885,7934,7945,7957,7972,8007,8047,8053,8071,8089,8097,8113,8129,8156,8176,8208,8222,8248]

target_lines += [8254,8300,8344,8400,8440,8488,8527,8547,8589,8654,8717,8745,8770,8800,8844,8880,8916,8978,9002,9020,9071,9109,9125,9170,9196,9231,9280,9310,9350,9407]
target_lines += [9411,9423,9445,9493,9550,9608,9660,9732,9780,9808,9832,9873,9901,9945,9990,10006,10065,10103,10158,10190,10213,10260,10303,10315,10339,10357,10364]
target_lines += [10366,10372,10402,10438,10454,10480,10503,10522,10532,10539,10548,10555,10562,10570,10598,10618,10626,10640,10662,10684,10699,10721,10739,10754,10766,10782,10791,10804,10811,10816,10831,10851,10868,10890,10904,10919,10936,10966,10973,10992,11003,11012,11025,11034,11039]
target_lines=[n for n in target_lines if n<=lastline]
if completed[-1] not in ('Book I','Book II'):
    focus=[u for u in b['units'] if u['chapter']==completed[-1]]
    target_lines.extend(u['sourceLines'][0] for i,u in enumerate(focus)
                        if i%12==0 or u['kind']!='verse')
    target_lines.append(lastline)
selected=set()
for n in target_lines:
    unit=next(u for u in b['units'] if u['sourceLines'][0]<=n<=u['sourceLines'][1])
    spread=next(x for x in index['spreads'] if unit['id'] in x['unitIds'])
    selected.update([spread['leftPage'],spread['rightPage']])
app=QApplication.instance() or QApplication([])
s=FileSession(ROOT,source_fonts=False,recovery=False);s.remember=lambda path:None
out=WORK/'Proofs';out.mkdir(exist_ok=True)
try:
    s.open(native,advance_revision=False)
    assert len(s.state['pages'])==r['pages']
    with TemporaryDirectory(dir=ROOT/'.local') as scratch:
        for n in sorted(selected):
            rendered=Path(scratch)/f'page-{n:03d}.png'
            pages.render(s,page_id=s.state['pages'][n-1]['pageId'],path=rendered,mode='mono',dpi=96,page_mode='two')
            copy2(rendered,out/rendered.name)
finally:s.finish()
from PIL import Image,ImageOps,ImageDraw
ordered=sorted(selected)
sheets=[]
for start in range(0,len(ordered),8):
    sheet=Image.new('RGB',(1400,980),'#ddd')
    for k,n in enumerate(ordered[start:start+8]):
        im=Image.open(out/f'page-{n:03d}.png').convert('RGB');im.thumbnail((342,448))
        x=(k%4)*350+(350-im.width)//2;y=(k//4)*490+24
        sheet.paste(im,(x,y));ImageDraw.Draw(sheet).text((x,y-18),f'Page {n}',fill='black')
    name=out/f'contact-{start//8+1}.png';sheet.save(name);sheets.append(str(name))
write(WORK/'publication-validation.json',dict(status=b['status'],completedBooks=completed,nextSourceLine=b['nextSourceLine'],sha256=digest(native),sourceSha256=SOURCE_HASH,pages=r['pages'],units=len(b['units']),translatedSourceWords=b['translatedSourceWords'],sourceWords=82597,verseLines=sum(actual.values()),verseLinesByBook=dict(actual),exactSourcePrefix=True,sourceLineBreaksPreserved=True,omittedPassagesInCompletedBooks=0,bookIPrefixUnchanged=True,unchangedMilestonePrefixes=verified_prefixes,allFourColumnsMatchLedger=True,saveReopenIdentical=True,untaConstructions=len(nums),proofPages=ordered,contactSheets=sheets,visualReview='pending'))
print('VERIFIED',r['pages'],'pages;',len(ordered),'proof pages;',len(nums),'Unta constructions',flush=True)
