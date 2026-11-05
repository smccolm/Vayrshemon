"""Compose the entire frozen KJV into one native Letter publication.

No translation compiler or Forge writes. Text is copied from the sealed ledger;
the complete original native Bible and all earlier proofs remain untouched.
"""
import argparse
import base64
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import time
from PySide6.QtCore import QRectF
from PySide6.QtWidgets import QApplication
from tools.kjv_print_proof import (Proof,Page,ROOT,SOURCE,SOURCE_SHA,LEDGER_SHA,TITLE_ART,FRONTIS_ART,
    WIDTH,HEIGHT,INNER,OUTER,TOP,BODY_SIZE,LEADING,VERSE_SIZE,BODY_BOTTOM,digest,write_json)
from tools.kjv_archive import BOOKS
from vayrshemon.authoring import blank_content
from vayrshemon.file_api import FileSession
from vayrshemon.page_numbering import MASTER,digits
from vayrshemon.print_edition import encode_path,hash_text,text_of,LETTER_TYPE,COMPACT_TYPE

EDITION='letter-native.1'
DEFAULT_OUT=ROOT/'Saves/KJV Bible - Letter Edition v0.10-kjv.280'
COMPACT_OUT=ROOT/'Saves/KJV Bible - Compact Letter Edition v0.10-kjv.280'


class BoundPage(Page):
    @property
    def left(self):
        if self.physical==1:return (WIDTH-540)/2
        return OUTER if self.physical%2 else INNER
    @property
    def right(self):return self.left+540


def mp(value):return str(round(value*1_000_000))


class Composer(Proof):
    def __init__(self,state,title_art=None,frontispiece_art=None,compact=False,right_openings=False,
                 language_version='0.10-kjv.280',ledger_sha256=LEDGER_SHA):
        super().__init__(title_art,frontispiece_art)
        self.state=state;self.state['pages']=[];self.current=None;self.warning_verses=[]
        self.right_openings=right_openings
        self.edition=dict(version=1,layoutVersion=EDITION,languageVersion=language_version,
            sourceSha256=SOURCE_SHA,ledgerSha256=ledger_sha256,assets={},pages={},verses=[],sections=[])
        self.state['printEdition']=self.edition
        self.type_spec=dict(COMPACT_TYPE if compact else LETTER_TYPE)
        if compact:self.edition.update(layoutVersion='letter-compact.1',typography=self.type_spec)
        for role,(_,provenance) in self.artwork.items():
            data=Path(provenance['source']).read_bytes();w,h=provenance['pixelSize']
            self.edition['assets'][provenance['sha256']]=dict(png=base64.b64encode(data).decode(),width=w,height=h)

    def lines(self,text,width,size=None,prefix=0,emergency=False):
        return super().lines(text,width,self.type_spec['bodySizePt'] if size is None else size,prefix,emergency,punctuation=True,verse_size=self.type_spec['verseSizePt'])

    def begin(self,kind):
        self.finish_page()
        physical=len(self.state['pages'])+1
        self.current=BoundPage(kind,physical,physical-3 if kind in ('opening','body') else None)
        self.page_id=f'page.kjvprint.{physical:05d}'
        self.source='';self.native_lines=[];self.native_images=[]
        return self.current

    def finish_page(self):
        if self.current is None:return
        page=self.current;fid=f'frame.kjvprint.{page.physical:05d}';pid=self.page_id
        content=blank_content(self.state['documentId'],mp(540),mp(BODY_BOTTOM-TOP),self.source)
        model=content['document'];model['fonts']=[dict(fontId=MASTER,sha256=self.face.sha256,faceIndex=0)]
        model['title']='Frozen historical publication source'
        model['styles'][0].update(fontId=MASTER,fontSizeMicroPoints=mp(self.type_spec['bodySizePt']),lineHeight=dict(mode='exact',microPoints=mp(self.type_spec['leadingPt'])),color='#111111FF')
        # Stable source paragraphs keep native search/copy and save/reopen exact.
        from tools.m0.synthetic import unicode_run
        model['stories'][0]['blocks']=[dict(blockId=f'block.{i}',type='paragraph',direction='ltr',runs=[unicode_run(t,f'run.{i}','language.vayrshemon')]) for i,t in enumerate(self.source.split('\n'))]
        frame=dict(frameId=fid,name='Frozen print text',x=mp(page.left),y=mp(TOP),width=mp(540),height=mp(BODY_BOTTOM-TOP),overflow='show',content=content)
        native=dict(pageId=pid,name={'title':'Title page','frontispiece':'Frontispiece','blank':'Blank'}.get(page.kind,f'Page {page.folio}'),
                    width=mp(WIDTH),height=mp(HEIGHT),margins=dict(left=mp(page.left),right=mp(WIDTH-page.right),top=mp(TOP),bottom=mp(HEIGHT-BODY_BOTTOM)),frames=[frame])
        ornaments=[]
        for (path,color),record in zip(page.elements,page.records):
            if record['role']!='body':ornaments.append(encode_path(path,record['role']))
        self.edition['pages'][pid]=dict(kind=page.kind,side='center' if page.physical==1 else ('left' if page.physical%2 else 'right'),
            folio=page.folio,sourceSha256=hash_text(self.source),lines=self.native_lines,paths=ornaments,images=self.native_images)
        self.state['pages'].append(native);self.current=None

    def artwork_page(self,kind,role):
        page=self.begin(kind)
        if self.artwork:
            image,provenance=self.artwork[role];scale=min((WIDTH-18)/image.width(),(HEIGHT-18)/image.height())
            w,h=image.width()*scale,image.height()*scale
            self.native_images.append(dict(asset=provenance['sha256'],rect=[page.center-w/2,(HEIGHT-h)/2,w,h]))

    def body_page(self,section=None):
        page=self.begin('opening' if section else 'body')
        if section:
            number,name=section
            self.edition['sections'].append(dict(number=number,name=name,pageId=self.page_id))
            self.border(page,QRectF(page.left,30,540,112))
            self.vine(page,page.left+26,87,132);self.vine(page,page.right-26,87,132,180)
            # The proof's attested Genesis heading; subsequent sections use the
            # existing native 'book' word and exact Unta canonical ordinal.
            title='Pá' if number==1 else 'Govis '+digits(number)
            self.centered(page,title,100 if number==1 else 70,53,role='book-title')
            self.centered(page,digits(1),42,107,role='chapter-number')
            return page,175.
        return page,TOP+20

    def append_line(self,unit,line,prefix,initial,indent,baseline,fragments,display):
        page=self.current
        if not fragments or fragments[-1]['pageId']!=self.page_id:
            if self.source:self.source+='\n'
            start=len(self.source)
            if initial and not fragments:self.source+=initial
            fragments.append(dict(pageId=self.page_id,start=start,end=len(self.source)))
        # Generated verse digits are separate from the unchanged source text.
        prefix_part=display[line.start:min(line.end,len(prefix))] if line.start<len(prefix) else ''
        source_piece=display[max(line.start,len(prefix)):line.end]
        start=len(self.source);self.source+=source_piece;end=len(self.source)
        fragments[-1]['end']=end
        bounds=self.put(page,line.path,page.left+indent,baseline,role='body',verseId=unit['id'])
        if bounds.top()<TOP-1 or bounds.bottom()>BODY_BOTTOM+.01:raise ValueError('PRINT_BODY_BOUNDS: '+unit['id'])
        self.native_lines.append(dict(start=start,end=end,prefix=prefix_part,x=page.left+indent,baseline=baseline,width=540-indent,
            bounds=[bounds.x(),bounds.y(),bounds.width(),bounds.height()]))

    def compose_all(self,units,progress=print):
        leading=self.type_spec['leadingPt']
        self.artwork_page('title','title-page');self.begin('blank');self.artwork_page('frontispiece','frontispiece')
        section=None;last_chapter=None;page=None;baseline=0.
        for index,unit in enumerate(units):
            number=int(unit['id'].split('.')[0]);opening=number!=section
            if opening:
                # Optional legacy parity for reproducing an earlier layout.
                # New editions use the next page on either side without padding.
                if self.right_openings and self.current and self.current.kind!='frontispiece' and self.current.physical%2==0:self.begin('blank')
                page,baseline=self.body_page((number,BOOKS[number-1]));section=number;last_chapter=1
                progress(f'Composing {number}/66 {BOOKS[number-1]} - {index:,}/{len(units):,} verses, page {page.physical}',flush=True)
            if unit['chapter']!=last_chapter:
                if baseline+112>BODY_BOTTOM:page,baseline=self.body_page()
                self.put(page,self.word(digits(unit['chapter']),50),page.left,baseline+12,role='chapter-heading')
                self.rule(page,page.left+48,baseline+9,page.right,baseline+9,width=.45);baseline+=56;last_chapter=unit['chapter']
            initial=unit['text'][0] if opening else ''
            source=unit['text'][1:] if initial else unit['text'];prefix='' if initial else digits(unit['verse'])+'  '
            display=prefix+source;indent=100 if initial else 0
            try:shaped=self.lines(display,540-indent,prefix=len(prefix))
            except ValueError as error:
                if 'Unbreakable word' not in str(error):raise
                shaped=self.lines(display,540-indent,prefix=len(prefix),emergency=True)
                self.warning_verses.append(dict(id=unit['id'],reason='Long compound wrapped at a glyph boundary without adding/removing any character'))
            if initial:
                self.put(page,self.word(digits(unit['verse']),self.type_spec['verseSizePt']),page.left,baseline,role='verse-marker')
                box=QRectF(page.left+22,baseline-19,66,66);self.border(page,box)
                self.fitted_glyph(page,initial,box.adjusted(10,10,-10,-10),role='illuminated-initial')
            fragments=[];position=0
            while position<len(shaped):
                remaining=shaped[position:]
                capacity=sum(1 for i,line in enumerate(remaining) if baseline+i*leading+line.path.boundingRect().bottom()<=BODY_BOTTOM)
                if capacity<len(remaining) and len(remaining)-capacity==1:capacity-=1
                if capacity<=0 or (capacity==1 and len(remaining)>1):page,baseline=self.body_page();continue
                for line in remaining[:capacity]:
                    self.append_line(unit,line,prefix,initial,indent,baseline,fragments,display);baseline+=leading
                position+=capacity
            if initial:baseline=max(baseline,175+66+6)
            baseline+=self.type_spec['verseGapPt']
            self.edition['verses'].append(dict(id=unit['id'],sha256=hash_text(unit['text']),fragments=fragments))
        self.finish_page()
        if len(self.state['pages'])%2:self.begin('blank');self.finish_page()
        self.state['activeFrameId']=self.state['pages'][0]['frames'][0]['frameId']
        self.state['typesetting']['frames']={};self.state['typesetting']['flows']=[]
        self.state['view'].update(mode='mono',monochromePaper='white',zoom=.77,baselines=False,origins=False,bounds=False)
        self.state['paint']['background']='#FFFFFFFF';self.state['paint']['bindings']=[]
        from vayrshemon.numbering_contracts import new_document_defaults
        self.state['pageNumbering']=new_document_defaults()
        return self.state


def main(out,compact=False,ledger_path=None,right_openings=False):
    out=Path(out).resolve()
    if out.exists() and (ledger_path is None or any(out.glob('*.vay')) or (out/'edition-manifest.json').exists()):
        raise FileExistsError('Use a new publication folder; existing editions are preserved')
    if not out.is_relative_to(ROOT/'Saves'):raise ValueError('Output must be a new folder within Saves')
    frozen=SOURCE/'KJV Bible.vay';parent_ledger=SOURCE/'complete-translation-ledger.json'
    if digest(frozen)!=SOURCE_SHA or digest(parent_ledger)!=LEDGER_SHA:raise ValueError('FROZEN_SOURCE_IDENTITY')
    ledger_path=Path(ledger_path) if ledger_path else parent_ledger
    ledger_sha=digest(ledger_path)
    ledger=json.loads(ledger_path.read_text(encoding='utf-8'));units=ledger['units']
    version=ledger['version']
    if ledger_path.resolve()!=parent_ledger.resolve():
        from tools.kjv_archive import verify_register
        verify_register(version)
        parent=json.loads(parent_ledger.read_text(encoding='utf-8'))
        if [(u['id'],u['source']) for u in units]!=[(u['id'],u['source']) for u in parent['units']]:raise ValueError('CORRECTION_SOURCE_COVERAGE')
    if len(units)!=31102 or len({u['id'].split('.')[0] for u in units})!=66:raise ValueError('COMPLETE_BIBLE_REQUIRED')
    app=QApplication.instance() or QApplication([]);book=FileSession(ROOT,recovery=False)
    book.log.emit=lambda *a,**k:None
    state=book.capture();state['title']='KJV Bible - Vayrshemon '+('Compact ' if compact else '')+'Letter Edition'
    composer=Composer(state,TITLE_ART,FRONTIS_ART,compact=compact,right_openings=right_openings,
                      language_version=version,ledger_sha256=ledger_sha);started=time.monotonic()
    state=composer.compose_all(units)
    if compact and len(state['pages'])>2000:raise ValueError(f'PRINT_SHEET_LIMIT: {len(state["pages"])} pages exceeds 2000')
    print(f'Validating all {len(state["pages"]):,} pages and all 31,102 exact verse hashes',flush=True)
    book._restore(state,take_ownership=True);book._state=book.capture()
    from vayrshemon import page_numbering
    verified=[]
    with page_numbering.scope(book,'two'):
        for i,page in enumerate(state['pages']):
            comp=book.composition('mono',page_id=page['pageId'])
            if comp.collision_report()['afterCount']:raise ValueError('PRINT_LINES_COLLIDE: '+page['pageId'])
            for line,path in zip(comp.spec['lines'],comp.drawings):
                actual=path.boundingRect();expected=QRectF(*line['bounds'])
                if max(abs(a-b) for a,b in zip([actual.x(),actual.y(),actual.width(),actual.height()],line['bounds']))>.05:
                    raise ValueError('PRINT_RESHAPING_DIFFERS: '+page['pageId']+' '+str(line))
            number=page_numbering.placement(book,page,'mono',comp)
            if number['status']=='blocked':raise ValueError('PRINT_NUMBER_COLLISION: '+page['pageId'])
            verified.append(dict(page=i+1,pageId=page['pageId'],folio=number['pageNumber'],status=number['status']))
            if i%100==0:print(f'Verified page {i+1:,}/{len(state["pages"]):,}',flush=True)
    out.mkdir(parents=True,exist_ok=True);target=out/(state['title']+'.vay')
    result=book.save(target,preview_mode='two')
    before=book.capture();book.open(target,advance_revision=False);after=book.capture()
    if book.content_digest(before)!=book.content_digest(after):raise ValueError('PRINT_SAVE_REOPEN_CHANGED')
    if digest(frozen)!=SOURCE_SHA or digest(parent_ledger)!=LEDGER_SHA or digest(ledger_path)!=ledger_sha:raise ValueError('FROZEN_SOURCE_CHANGED')
    report=dict(layoutVersion=composer.edition['layoutVersion'],typography=composer.type_spec,languageVersion=version,completeBible=True,verses=31102,sections=66,
        pages=len(state['pages']),native=str(target),sha256=digest(target),sourceSha256=SOURCE_SHA,ledgerSha256=ledger_sha,
        duplexSheets=len(state['pages'])//2,paperThicknessInches=round(len(state['pages'])/2*.004,3),maximumPages=2000 if compact else None,
        sourceUnchanged=True,exactVerseHashesVerified=31102,saveReopenIdentical=True,pageMode=book.saved_page_mode,
        palette='monochrome black on white',pageOrder=['Title','Blank','Frontispiece','Genesis illuminated opening'],
        bindingOffsetsPt=dict(title=0,left=-9,right=9),bookOpeningSide='right' if right_openings else 'next available',numbering=verified,longCompoundWraps=composer.warning_verses,
        elapsedSeconds=round(time.monotonic()-started,2))
    write_json(out/'edition-manifest.json',report)
    (out/'READ ME.txt').write_text('COMPLETE VAYRSHEMON-ONLY KJV BIBLE\n31,102 verses; 66 books. Historical language 0.10-kjv.280, unchanged.\n\nOpen the .vay with the updated launch.bat. It opens black on white in two-page mode.\nOrder: Title | Blank, then Frontispiece | Genesis opening. Every later book opens on the right.\nLeft/right and binding offsets follow those Workbench spreads, exactly as requested.\nThis supersedes the earlier PDF-proof page order; confirm sheet/cover assembly before physical duplex production.\n\nLetter 612 x 792 pt; full-width 36 pt Thimfora, 28 pt leading; verse numerals 24 pt.\nMirrored inside/outside margins 45/27 pt. Title centered; following centers shift 9 pt outward.\nUnta folios 50 pt, 28 pt from the bottom/outside, body folio 1 at Genesis.\n\nThis is a fixed print edition: its source text is searchable/copyable and its layout is sealed.\nNumber visibility/position, viewing, save/save-as and exports remain available.\nChanging historical text or typesetting requires a separately generated edition.\nThe native file embeds both supplied artworks and retains vector TTF text. No PDF or artwork sidecar is required.\nThe complete earlier four-column Bible remains untouched.\n',encoding='utf-8')
    readme=out/'READ ME.txt'
    text=readme.read_text(encoding='utf-8').replace('full-width 36 pt Thimfora, 28 pt leading; verse numerals 24 pt.',f'full-width {composer.type_spec["bodySizePt"]} pt Thimfora, {composer.type_spec["leadingPt"]} pt leading; verse numerals {composer.type_spec["verseSizePt"]} pt.')
    text=text.replace('Historical language 0.10-kjv.280, unchanged.',f'Historical language {version}; exact text from this edition\'s versioned ledger.')
    if not right_openings:text=text.replace('Every later book opens on the right.','Every later book opens on the next available page, on either side; no inter-book blank pages.')
    text+=f'\n{report["pages"]:,} pages / {report["duplexSheets"]:,} duplex sheets. Paper stack about {report["paperThicknessInches"]:.3f} inches at 0.004 inches per sheet, excluding covers, thread and glue.\n'
    readme.write_text(text,encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('numbering','longCompoundWraps')},indent=2),flush=True)
    book.finish()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path);parser.add_argument('--compact',action='store_true');parser.add_argument('--check',action='store_true');parser.add_argument('--ledger',type=Path);parser.add_argument('--legacy-right-openings',action='store_true');args=parser.parse_args()
    if args.check:
        app=QApplication.instance() or QApplication([])
        from tools.kjv_print_proof import check_runtime
        check_runtime();print('Native print edition runtime available; no private edition regenerated.')
    else:main(args.out or (COMPACT_OUT if args.compact else DEFAULT_OUT),compact=args.compact,ledger_path=args.ledger,right_openings=args.legacy_right_openings)
