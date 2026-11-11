"""Set the 285 historical text in the approved run-in Letter layout."""
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import json
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
EDITION = HERE.parent
ROOT = EDITION.parents[1]
sys.path.insert(0, str(ROOT))
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QTextLayout, QTextOption
from PySide6.QtWidgets import QApplication
from tools.kjv_archive import BOOKS, read
from tools.kjv_native_vocabulary import COMPACT, OUT
from tools.kjv_print_edition import mp
from tools.kjv_print_proof import Page, Proof, digest
from tools.m0.synthetic import unicode_run
from vayrshemon.authoring import blank_content
from vayrshemon.file_api import FileSession
from vayrshemon.native_storage import unpack
from vayrshemon.page_numbering import digits
from vayrshemon import print_edition as pe

PREVIOUS = ROOT/'Saves/KJV Bible - Run-in Letter Edition v0.10-kjv.285'
TITLE = 'KJV Bible - Vayrshemon Run-in Letter Edition - Printing 2'
TARGET = EDITION/(TITLE+'.vay')
STAGE = ROOT/'.local/kjv285-run-in-printing2'
# The Unta folio's ink starts at 725.1 pt. Leave over 4 pt of clear paper.
INNER, OUTER, TOP, BOTTOM = 72., 54., 48., 71.
RIGHT, BASE_LIMIT = 612.-OUTER, 792.-BOTTOM
BODY, MARKER, LEADING, GAP = 26, 18, 18, 6


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, separators=(',',':')), encoding='utf8')
    tmp.replace(path)


def main_inputs():
    ledger = OUT/'complete-translation-ledger.json'
    assert digest(ledger)==read(OUT/'edition-manifest.json')['ledgerSha256']
    compact = next(COMPACT.glob('*.vay'))
    assert digest(compact)==read(COMPACT/'FROZEN.json')['nativeSha256']
    s = unpack(read(compact))['state']
    text = {p['pageId']:pe.text_of(p) for p in s['pages']}
    units = read(ledger)['units']
    by_book = defaultdict(list)
    for u,r in zip(units,s['printEdition']['verses'],strict=True):
        src = ''.join(text[f['pageId']][f['start']:f['end']] for f in r['fragments'])
        assert (r['id'],src)==(u['id'],u['text']) and pe.hash_text(src)==r['sha256']
        number = int(u['id'].split('.')[0])
        by_book[number].append({k:u[k] for k in ('id','reference','chapter','verse','text')})
    assert len(units)==31102 and len(by_book)==66
    for n,rows in by_book.items():
        save_json(STAGE/'input'/f'{n:02}.json',rows)


class Sheet(Page):
    @property
    def left(self): return INNER
    @property
    def right(self): return RIGHT


class Metrics(Proof):
    @lru_cache(maxsize=4096)
    def advance(self,text,prefix):
        layout = QTextLayout(text.replace('-',' '),self.font(BODY))
        option = QTextOption()
        option.setTextDirection(Qt.LayoutDirection.LeftToRight)
        option.setWrapMode(QTextOption.WrapMode.NoWrap)
        layout.setTextOption(option)
        layout.setFormats(pe.text_formats(self,text,BODY,len(prefix),MARKER))
        layout.beginLayout()
        line=layout.createLine()
        line.setLineWidth(100000)
        layout.endLayout()
        return line.naturalTextWidth()

    def fit(self,text,words,i,start,prefix,width,align_left,depth):
        # Advance bounds allow a fast search; the emitted line must fit by ink as well.
        lo,hi=i,len(words)
        while lo<hi:
            mid=(lo+hi+1)//2
            display=prefix+text[start:words[mid-1].end()]
            if self.advance(display,prefix)<=width+.001: lo=mid
            else: hi=mid-1
        for count in range(lo,i,-1):
            end=words[count-1].end()
            display=prefix+text[start:end]
            line=self.lines(display,10000,BODY,len(prefix),punctuation=True,verse_size=MARKER)[0]
            used=max(line.width,line.path.boundingRect().right())
            correction=max(0.,-line.path.boundingRect().left()) if align_left else 0.
            if used+correction<=width+.001 and line.path.boundingRect().bottom()<=depth:
                return count,end,line,used,correction
        return None


class BodyPage:
    def __init__(self, proof, book, opening_text=None):
        self.proof = proof
        self.sheet = Sheet('opening' if opening_text else 'body',0)
        self.text = ''
        self.lines = []
        self.rows = []
        self.chapters = []
        self.initial = None
        # A regular body page starts on the same 18 pt grid that puts its
        # lowest baseline at 714 pt, immediately above the protected folio.
        self.y = TOP+LEADING
        if opening_text:
            banner=QRectF(INNER+3,TOP+3,RIGHT-INNER-6,94)
            proof.border(self.sheet,banner)
            proof.vine(self.sheet,INNER+22,banner.center().y(),110)
            proof.vine(self.sheet,RIGHT-22,banner.center().y(),110,180)
            from acanthus import expected_images
            from titles import catalog,shape_title
            panel=dict(kind='opening',side='right')
            panel['images']=expected_images(panel)
            panel['paths']=[pe.encode_path(self.sheet.elements[0][0],'ornament')]
            title,_=shape_title(proof,catalog()[book-1]['slots'],panel)
            proof.put(self.sheet,pe.decode_path(title),role='book-title')
            self.chapters.append(1)
            self.y=banner.bottom()+28
            self.initial=QRectF(INNER+18,self.y-16,66,66)
            proof.border(self.sheet,self.initial)
            proof.fitted_glyph(self.sheet,opening_text[0],self.initial.adjusted(10,10,-10,-10),role='illuminated-initial')
            proof.put(self.sheet,proof.word(digits(1),MARKER),INNER,self.y,role='verse-marker')
        self.x=self.left()

    def left(self):
        if self.initial and self.y-13<self.initial.bottom()+4: return self.initial.right()+12
        return INNER

    def next_row(self):
        self.y+=LEADING
        self.x=self.left()

    def place(self,u,words,i):
        """Retain the longest printable prefix and resume at the first unprinted word."""
        text=u['text']
        pos=len(self.text)+bool(self.rows)
        first=i
        origin=words[i].start()
        illumination=self.initial is not None and not self.rows and i==0
        while i<len(words) and self.y-13<BASE_LIMIT:
            start=words[i].start()+(i==0 and illumination)
            prefix=digits(u['verse'])+'  ' if i==0 and not illumination else ''
            line=self.proof.fit(text,words,i,start,prefix,RIGHT-self.x,self.x==self.left(),BASE_LIMIT-self.y)
            if line is None:
                if self.x==INNER and self.y<BASE_LIMIT-18: raise ValueError('Unbreakable word: '+u['reference'])
                self.next_row()
                continue
            count,end,shape,used,correction=line
            bounds=shape.path.boundingRect()
            x=self.x+correction
            rect=bounds.translated(x,self.y)
            overlaps=[QRectF(*l['bounds']) for l in reversed(self.lines) if l['baseline']>=self.y-2*LEADING]
            overlaps.extend(p.boundingRect() for p,_ in self.sheet.elements)
            if any(r.intersects(rect) for r in overlaps):
                self.next_row()
                continue
            assert rect.right()<=RIGHT+.001 and rect.bottom()<=BASE_LIMIT
            self.lines.append(dict(start=pos+start-origin,end=pos+end-origin,prefix=prefix,x=x,baseline=self.y,
                                   width=RIGHT-x,bounds=list(rect.getRect())))
            i=count
            if i<len(words): self.next_row()
            else: self.x=x+used+GAP
        if i>first:
            # Give the inter-word space to the preceding fragment. Concatenating
            # fragments from the native file must reproduce the exact verse.
            stop=words[i].start() if i<len(words) else len(text)
            piece=text[origin:stop]
            self.text+=(' ' if self.rows else '')+piece
            self.rows.append(dict(id=u['id'],start=pos,end=pos+len(piece),
                                  sourceStart=origin,sourceEnd=stop,sha256=pe.hash_text(text)))
        return i

    def chapter(self,u,words):
        """Keep the numeral with its first word. Use a short rule near a page foot."""
        number=u['chapter']
        numeral=self.proof.word(digits(number),50)
        b=numeral.boundingRect()
        saved=(self.x,self.y)
        count=len(self.sheet.records)
        for style in ('separate','inline','next row'):
            self.x,self.y=saved
            if style=='separate':
                # Put the divider between body baselines. Restarting the grid
                # after a divider would lose up to a line at the foot of the page.
                top=max((l['bounds'][1]+l['bounds'][3] for l in self.lines),default=TOP-2)+3
                if self.lines: top=max(top,self.y+9)
                y=top-b.top()
                x=INNER
                self.x=INNER
                self.y+=2*LEADING if self.lines else LEADING
                if self.y-13>=BASE_LIMIT: continue
                self.proof.rule(self.sheet,INNER+48,top+b.height()/2,RIGHT-.25,top+b.height()/2,width=.45)
            else:
                if style=='next row': self.next_row()
                x=self.x
                # At body size the text descends up to 6.656 pt. The larger
                # chapter numeral ascends 14.4 pt, so lower it within this row.
                y=self.y+4
                self.x=x+b.width()+18
                if self.x>=RIGHT or y+b.bottom()>BASE_LIMIT: continue
                # Only commit a compact heading if a complete first word fits next to it.
                first=self.proof.fit(u['text'],words,0,0,digits(1)+'  ',RIGHT-self.x,False,BASE_LIMIT-self.y)
                if first is None: continue
                self.proof.rule(self.sheet,self.x-13,self.y-4,self.x-4,self.y-4,width=.45)
            body_y=self.y
            heading_bounds=b.translated(x-b.left(),y)
            assert not any(heading_bounds.intersects(QRectF(*l['bounds'])) for l in self.lines),u['reference']
            self.proof.put(self.sheet,numeral,x-b.left(),y,role='chapter-heading')
            nlines=len(self.lines)
            last=self.place(u,words,0)
            if last:
                assert style=='separate' or self.lines[nlines]['baseline']==body_y,(u['reference'],style)
                self.chapters.append(number)
                return last
            del self.sheet.records[count:]
            del self.sheet.elements[count:]
        self.x,self.y=saved
        return 0

    def result(self):
        assert self.rows and len(self.sheet.elements)==len(self.sheet.records)
        paths=[pe.encode_path(p,r['role']) for (p,_),r in zip(self.sheet.elements,self.sheet.records)]
        return dict(kind=self.sheet.kind,text=self.text,rows=self.rows,lines=self.lines,paths=paths,chapters=self.chapters)


def compose_book(n):
    input_path=STAGE/'input'/f'{n:02}.json'
    output_path=STAGE/'books'/f'{n:02}.json'
    units=read(input_path)
    proof=Metrics()
    result=[]
    chapter=1
    page=BodyPage(proof,n,units[0]['text'])
    for u in units:
        words=list(re.finditer(r'\S+',u['text']))
        assert u['text']==' '.join(w[0] for w in words)
        i=0
        while i<len(words):
            if i==0 and chapter!=u['chapter']: i=page.chapter(u,words)
            else: i=page.place(u,words,i)
            if i==len(words): break
            assert page.rows,u['reference']
            result.append(page.result())
            page=BodyPage(proof,n)
        chapter=u['chapter']
    result.append(page.result())
    save_json(output_path,dict(inputSha256=digest(input_path),pages=result))
    print(n,BOOKS[n-1],len(result),'pages',flush=True)


def run_books():
    main_inputs()
    def run(n):
        log=STAGE/'logs'/f'{n:02}.txt'
        log.parent.mkdir(exist_ok=True)
        with log.open('w',encoding='utf8') as f:
            task=subprocess.run([sys.executable,'-B','-X','utf8',__file__,'book',str(n)],stdout=f,stderr=subprocess.STDOUT)
        print(n,BOOKS[n-1],task.returncode,flush=True)
        return task.returncode
    with ThreadPoolExecutor(max_workers=10) as pool:
        codes=list(pool.map(run,range(1,67)))
    if any(codes): raise RuntimeError('Inspect the individual book logs')


if __name__=='__main__':
    if sys.argv[1]=='book':
        app=QApplication([])
        compose_book(int(sys.argv[2]))
    elif sys.argv[1]=='all': run_books()
