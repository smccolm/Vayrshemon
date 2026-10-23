"""Local M4 reference coverage, reproducible proofs and the approved live specimen.

Original artwork, corpus, font binaries and generated artifacts remain in ignored
locations. No historical source is reinterpreted through a newer cmap.
"""
import argparse
from contextlib import closing
from datetime import datetime
import hashlib
import html
import json
import math
from pathlib import Path
import uuid
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import pypdfium2 as pdfium
from PySide6.QtCore import QRectF
from PySide6.QtGui import QImage,QPainter,QColor
from PySide6.QtWidgets import QApplication
from tools.m0.common import write_json
from tools.layered_translation_fixture import compose_layered
from vayrshemon.studio_session import StudioSession
from vayrshemon.studio_api import StudioAPI
from vayrshemon.publication import png_bytes
from vayrshemon.paint import signature

ROOT=Path(__file__).resolve().parents[1]


def references(book,out,call):
    mapping=json.loads((ROOT/'data/orthography/thimfora-79.json').read_text())
    catalog=json.loads((ROOT/'data/assets.json').read_text())
    assets={a['path']:a for a in catalog['assets']}
    master=book.fonts.resolve(book.fonts.recipe['master']);r=book.paint_renderer;b=r.binding(master.font_id)
    records=[];panels=[];gallery=[]
    directory=ROOT/'Inputs/Versions Best/Individual Glyphs'
    files=sorted(directory.glob('*.jpg'),key=lambda p:(p.name.split('_')[0],int(p.name.split('_')[1]) if p.name.split('_')[1].isdigit() else 999,p.name))
    for index,path in enumerate(files):
        relative=path.relative_to(ROOT/'Inputs').as_posix();asset=assets[relative]
        sha=hashlib.sha256(path.read_bytes()).hexdigest()
        if sha!=asset['sha256']: raise ValueError('REFERENCE_HASH_MISMATCH: '+relative)
        parts=path.stem.split('_');form=parts[0].lower();entry=None
        if form in ('maxima','minima'):
            symbol=f'thimfora.letter.{int(parts[1]):03}'
            entry=next((e for e in mapping['entries'] if e['symbolId']==symbol and e['form']==form),None)
        elif form=='unta': entry=next((e for e in mapping['entries'] if e['symbolId']==f'unta.digit.{int(parts[1]):02}'),None)
        # A punctuation filename does not establish a legacy keyboard slot.
        # Period has a visually inspectable candidate; it is still labeled.
        candidate=False
        if path.stem=='Punctuation_3_Period': entry=next(e for e in mapping['entries'] if e['scalar']==46);candidate=True
        record=dict(reference=relative,assetId=asset['assetId'],sha256=sha,status='candidate-slot' if candidate else 'mapped' if entry else 'unresolved',
                    mappingProfile=mapping['profileId'],mappingRevision=mapping['revision'])
        ref=Image.open(path).convert('RGB');width,height=ref.size
        ref_path=out/(path.stem+'-reference.png');ref.save(ref_path)
        rendered=Image.new('RGB',ref.size,'black')
        if entry:
            gid=entry['glyphId'];raw=master.raw(1000);bounds=raw.pathForGlyph(gid).boundingRect()
            array=np.asarray(ref).astype(float)
            saturated=(array[:,:,2]>array[:,:,0]*1.5)&(array[:,:,2]>array[:,:,1]*1.12)&(array[:,:,2]>65)
            yy,xx=np.where(saturated)
            if not len(xx): raise ValueError('REFERENCE_ALIGNMENT_UNAVAILABLE: '+path.name)
            box=(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1))
            factor=(box[3]-box[1])/bounds.height();em=1000*factor
            tile,area=r.tile(b,gid,em,1)
            x=(box[0]+box[2])/2-bounds.center().x()*factor;y=(box[1]+box[3])/2-bounds.center().y()*factor
            canvas=QImage(width,height,QImage.Format.Format_ARGB32);canvas.fill(QColor('black'))
            painter=QPainter(canvas);painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform);painter.drawImage(area.translated(x,y),tile);painter.end()
            from io import BytesIO
            rendered=Image.open(BytesIO(png_bytes(canvas))).convert('RGB')
            record.update(glyphId=gid,glyphName=master.glyph_order[gid],sourceScalar=entry['scalar'],fontId=master.font_id,
                alignment=dict(method='uniform height fit and center of saturated-blue reference bounds; no contour warp',referenceBounds=box,em=em,origin=[x,y],
                               aspectRatioDelta=(box[2]-box[0])/(box[3]-box[1])-bounds.width()/bounds.height()))
            delta=np.abs(np.asarray(rendered).astype(float)-array)
            # Whole-canvas MAE is diagnostic only; black margins cannot award a pass.
            roi=(slice(box[1],box[3]),slice(box[0],box[2]));record['glyphBoxRgbMae']=float(delta[roi].mean())
            record['visualAcceptance']='pending-user-review'
        else:
            record['reason']='No verified correspondence to a current 79/80/81 slot; historical artwork retained for review.'
            draw=ImageDraw.Draw(rendered);draw.text((30,height//2),'No verified font-slot mapping',fill='#c5d4df')
        render_path=out/(path.stem+'-render.png');rendered.save(render_path)
        overlay=Image.blend(ref,rendered,.5);overlay.save(out/(path.stem+'-overlay.png'))
        panel=Image.new('RGB',(480,280),'#0b1019');d=ImageDraw.Draw(panel);d.text((12,8),path.stem,fill='white')
        d.text((12,26),'REFERENCE',fill='#8fc0cc');d.text((250,26),'M4  /  '+record['status'],fill='#8fc0cc')
        for x,image in [(0,ref),(240,rendered)]:
            preview=image.copy();preview.thumbnail((230,225),Image.Resampling.LANCZOS);panel.paste(preview,(x+(240-preview.width)//2,49+(225-preview.height)//2))
        panels.append(panel);records.append(record)
        gallery.append(f'<article><h2>{html.escape(path.stem)}</h2><p>{record["status"]}</p><div><figure><img src="{ref_path.name}"><figcaption>Reference</figcaption></figure><figure><img src="{render_path.name}"><figcaption>M4</figcaption></figure><figure><img src="{path.stem}-overlay.png"><figcaption>50% overlay</figcaption></figure></div></article>')
        if (index+1)%16==0 or index+1==len(files):
            batch=panels[-((index%16)+1):];sheet=Image.new('RGB',(1920,math.ceil(len(batch)/4)*280),'#0b1019')
            for j,panel in enumerate(batch): sheet.paste(panel,((j%4)*480,(j//4)*280))
            sheet.save(out/f'contact-{index//16+1:02}.png')
        print(f'REFERENCE {index+1}/{len(files)} {path.stem}: {record["status"]}',flush=True)
    (out/'gallery.html').write_text('<!doctype html><meta charset="utf-8"><title>M4 Individual Glyphs review</title><style>body{background:#10151e;color:#e4e9f2;font:16px system-ui;margin:32px}h1{font-size:28px}article{margin:35px 0;border-top:1px solid #394551}article>div{display:flex;gap:16px}figure{margin:0;flex:1}img{width:100%;background:black}figcaption{padding:8px}p{color:#b7c9d9}</style><h1>Individual Glyphs — reference / M4 / overlay</h1><p>Uniform alignment, no shape warping. This is a review candidate, not an approved visual baseline. Historical punctuation with no verified font slot stays unresolved.</p>'+''.join(gallery),encoding='utf-8')
    summary=dict(referenceCount=len(records),mapped=sum(r['status']=='mapped' for r in records),candidates=sum(r['status']=='candidate-slot' for r in records),unresolved=sum(r['status']=='unresolved' for r in records),
        recipe=book.state['paint']['recipe'],recipeHash=signature(book.state['paint']['recipe']),acceptance='pending-user-review',records=records)
    write_json(out/'reference-audit.json',summary);return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path);parser.add_argument('--document',type=Path);parser.add_argument('--skip-references',action='store_true');args=parser.parse_args()
    out=(args.out or ROOT/'.local/demos'/('m4-'+datetime.now().strftime('%Y%m%d-%H%M%S'))).resolve();out.mkdir(parents=True,exist_ok=False)
    app=QApplication.instance() or QApplication([]);book=StudioSession(ROOT,recovery=False);api=StudioAPI(book)
    transcript=[]
    def call(method,**params):
        result=api.call(method,params,expected_revision=book.revision,document_id=book.state['documentId'],idempotency_key=uuid.uuid4().hex,origin='verification')
        transcript.append(dict(method=method,params=params,response=result))
        if not result['ok']: raise RuntimeError(result)
        return result['result']
    try:
        recipe=book.fonts.recipe
        call('paint.bind',fontId=recipe['master'],glowFontId=recipe['layers'][0]['fontId'],interiorFontId=recipe['layers'][1]['fontId'],kind='layered',enabled=True)
        review=references(book,out,call) if not args.skip_references else None
        for em,dpi in [(41.333,96),(41.333,192),(400,96)]:
            for label,bg in [('white','#FFFFFFFF'),('black','#FF000000'),('transparent','#00000000')]:
                call('glyph.proof',font_id=recipe['master'],glyph_id=book.fonts.resolve(recipe['master']).glyph_order.index('J'),em=em,dpi=dpi,background=bg,path=str(out/f'jiam-{em:g}-{dpi}-{label}.png'))
        call('font.build',font_id=recipe['master'],path=str(out/'Thimfora-M4-flat-color.ttf'),treatment='flat-colr-v0')
        font=ImageFont.truetype(str(out/'Thimfora-M4-flat-color.ttf'),500)
        independent=Image.new('RGB',(1000,500),'white');ImageDraw.Draw(independent).text((30,30),'Jj0.',font=font,embedded_color=True);independent.save(out/'colr-freetype.png')
        conversion=None
        if args.document:
            call('document.open',path=str(args.document),discardUnsaved=True)
            ids=dict(original=book.current_page()['frames'][0]['frameId'],translation=book.current_page()['frames'][1]['frameId'])
        else:
            call('document.new',discardUnsaved=True);ids,_,conversion=compose_layered(ROOT,call)
            write_json(out/'source-adaptation.json',conversion)
        source_before={fid:n.text() for fid,n in book.frames.items()}
        # Never silently simulate three-font artwork with a one-font binding.
        used={g['fontId'] for g in call('layout.inspect')['glyphs'] if g['frameId']==ids['original']}
        if used!={recipe['master']}: raise ValueError('THREE_FONT_MASTER_REQUIRED: use a separate explicitly adapted Thimfora 79 review copy')
        call('paint.bind',fontId=recipe['master'],glowFontId=recipe['layers'][0]['fontId'],interiorFontId=recipe['layers'][1]['fontId'],kind='layered',enabled=True)
        for char in 'r\u00e1.ly':
            gid=book.fonts.raw(recipe['master'],200).glyphIndexesForString(char)[0]
            for layer in ('outline','interior','glow-mask','composite'):
                proof=call('glyph.proof',font_id=recipe['master'],glyph_id=gid,em=600,dpi=144,background='#FF000000',path=str(out/f'layer-{ord(char)}-{layer}.png'),layer=layer)
                write_json(out/f'layer-{ord(char)}-{layer}.json',proof)
        call('collision.configure',frame_id=ids['original'],bounds='effect',mode='warn')
        call('document.title',title='Vayrshemon / English — three-font color review')
        call('view.configure',mode='color',zoom=.57,baselines=False,origins=False,bounds=False)
        call('frame.select',frame_id=ids['original'])
        call('document.save',path=str(out/'Vayrshemon-English-M4.vay.json'))
        for kind,dpi in [('png',144),('svg',300),('pdf',300)]: call('publication.export',path=str(out/('standard.'+kind)),format=kind,mode='color',dpi=dpi,raster_policy='raster')
        check=call('publication.preflight',format='pdf',mode='color',dpi=300,raster_policy='raster');write_json(out/'preflight.json',check)
        with closing(pdfium.PdfDocument(str(out/'standard.pdf'))) as pdf:
            page=pdf[0];page.render(scale=2).to_pil().save(out/'standard-pdf-independent.png')
            extracted=page.get_textpage().get_text_range();dimensions=page.get_size()
        assert extracted=='' and dimensions==(612,792)
        assert source_before=={fid:n.text() for fid,n in book.frames.items()}
        write_json(out/'layout.json',call('layout.inspect'))
        # Additional black-paper comparison; undo every formatting change before
        # returning, preserving the saved standard and its source text.
        call('publication.configure',background='#FF000000')
        call('frame.select',frame_id=ids['translation'])
        from vayrshemon.session import utf16_length
        call('document.format',start=0,end=utf16_length(book.text()),color='#E4E9F0FF')
        call('publication.export',path=str(out/'standard-black.png'),format='png',mode='color',dpi=144,raster_policy='raster')
        call('history.undo');call('history.undo');call('frame.select',frame_id=ids['original'])
        summary=dict(output=str(out),nativeDocument=str(out/'Vayrshemon-English-M4.vay.json'),apiVersion=api.version,referenceCounts={k:review[k] for k in ('referenceCount','mapped','candidates','unresolved')} if review else None,
                     sourceTextUnchangedAfterAdaptation=True,sourceAdaptation=conversion,paintBinding='layered',engine=book.fingerprint(),pdfPoints=dimensions,pdfExtractedCharacters=len(extracted),visualAcceptance='pending-user-review',preflightIssues=check['issues'])
        write_json(out/'verification.json',summary);print(json.dumps(summary,indent=2))
    finally:
        write_json(out/'api-transcript.json',transcript);book.finish()


if __name__=='__main__': main()
