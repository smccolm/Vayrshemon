"""Assemble and verify the complete duplex PDF with a bookmark for each alphabetical volume."""
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import json

from pypdf import PdfReader,PdfWriter
from tools.reciprocal_publication import FOLDER,STAGE,WORK,sha

NAME='Vayrshemon Dictionary and Thesaurus - Complete Duplex Print.pdf'

def contents(page):
    content=page.get_contents()
    return sha256(content.get_data() if content is not None else b'').hexdigest()

def main():
    cat=json.loads((WORK/'volumes.json').read_text('utf8'))
    target=FOLDER['print']/NAME
    writer=PdfWriter();sequence=[];ranges=[];padding=[]
    for v in cat:
        n=v['number'];source=FOLDER['print']/(v['name']+' - Duplex Print.pdf')
        rec=json.loads((WORK/'Publication'/f'print-{n:02d}.json').read_text('utf8'))
        assert rec['allPDFTextAndBoundsVerified'] and sha(source)==rec['pdfSha256']
        if len(sequence)%2:
            writer.add_blank_page(width=612,height=792);sequence.append((sha256(b'').hexdigest(),(0.,0.,612.,792.)));padding.append(len(sequence))
        begin=len(sequence)+1;label=v['name']+' · '+v['first']+' – '+v['last']
        r=PdfReader(source);assert len(r.pages)==rec['physicalPages']
        writer.append(r,outline_item=label,import_outline=True)
        sequence.extend((contents(p),tuple(map(float,p.mediabox))) for p in r.pages)
        ranges.append(dict(volume=n,firstPhysicalPage=begin,lastPhysicalPage=len(sequence),sourceSha256=rec['pdfSha256'],bookmark=label))
    writer.add_metadata({'/Title':'Vayrshemon Dictionary and Thesaurus','/Subject':'Reciprocal vocabulary · native Letter duplex edition'})
    writer.page_layout='/TwoPageLeft'
    with TemporaryDirectory(dir=STAGE) as t:
        staged=Path(t)/NAME
        with staged.open('wb') as fh:writer.write(fh)
        writer.close()
        with staged.open('rb') as fh:
            checked=PdfReader(fh);assert len(checked.pages)==len(sequence)
            for page,expected in zip(checked.pages,sequence,strict=True):assert (contents(page),tuple(map(float,page.mediabox)))==expected
            marks={m.title:checked.get_destination_page_number(m)+1 for m in checked.outline if not isinstance(m,list)}
            assert all(marks[r['bookmark']]==r['firstPhysicalPage'] for r in ranges)
        staged.replace(target)
    out=dict(file=NAME,physicalPDFPages=len(sequence),duplexSheets=(len(sequence)+1)//2,interVolumeBlanks=padding,volumes=ranges,sha256=sha(target),allPageContentsAndBoxesVerified=True,volumeBookmarksVerified=True)
    (WORK/'complete-pdf.json').write_text(json.dumps(out,ensure_ascii=False,indent=1),encoding='utf8')
    print(out['physicalPDFPages'],'pages,',out['duplexSheets'],'sheets,',len(padding),'binding blanks between volumes',out['sha256'])

if __name__=='__main__':main()
