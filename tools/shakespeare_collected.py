"""Set the issued Shakespeare native columns as a single Letter reading edition."""
from copy import deepcopy
from bisect import bisect_right
from functools import lru_cache
from pathlib import Path
import base64
import hashlib
from io import BytesIO
import json
import re
import argparse
from PIL import Image
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QPainterPath, QTextLayout, QTextOption
from PySide6.QtWidgets import QApplication

from tools.compose_historical_book import texts
from tools.kjv_print_proof import digest, Proof
from tools.kjv_print_edition import mp
from tools.editorial_language import EditorialLanguage
from tools.m0.synthetic import unicode_run
from tools.shakespeare_project import POEMS, PROJECT as ORIGINAL_PROJECT, ROOT, read
from vayrshemon.native_storage import unpack
from vayrshemon.page_numbering import digits
from vayrshemon import print_edition as pe
from vayrshemon.authoring import blank_content
from vayrshemon.file_api import FileSession


def saved_source(path):
    """Resolve the original paths recorded in the sealed edition manifests."""
    source = ROOT / path
    saves = ROOT / 'Saves'
    if source.exists() or not source.is_relative_to(saves):
        return source
    archived = saves / 'Archive' / source.relative_to(saves)
    return archived if archived.exists() else source


PROJECT = saved_source(ORIGINAL_PROJECT)
TITLE = 'The Collected Works of William Shakespeare'
DEST = ROOT / 'Saves' / (TITLE + ' v0.14') / (TITLE + '.vay')
STAGE = ROOT / '.local/shakespeare-collected'
TITLE_ART = ROOT / 'Inputs' / 'Print artwork' / 'Shakespeare Title Page - With Text.png'
REFERENCE = ROOT / 'Saves/KJV Bible - Run-in Letter Edition v0.10-kjv.285 - Printing 2/KJV Bible - Vayrshemon Run-in Letter Edition - Printing 2.vay'
OLDER = {'a-midsummer-nights-dream': "A Midsummer Night's Dream",
         'alls-well-that-ends-well': "All's Well That Ends Well"}
INNER, OUTER, TOP, BOTTOM, MEASURE = 72, 54, 48, 71, 486
BODY, LEADING = 26, 18
PLAYS, VERSES = 'stage+writing:pl', 'verse+writing:pl'
HEADING = re.compile(r'^(?:ACT\s+\d|Scene\s+\d|(?:THE )?(?:PROLOGUE|EPILOGUE|INDUCTION)\b)', re.I)
# Analyses author navigation only. Issued passage strings never go through the compiler.
TITLES = {
    'alls-well-that-ends-well': 'well end:pr what, all well be:pr',
    'antony-and-cleopatra': 'antony and cleopatra',
    'as-you-like-it': 'as it:a like:pr you',
    'the-comedy-of-errors': 'error:pl/comedy',
    'coriolanus': 'coriolanus_name', 'cymbeline': 'cymbeline_king', 'hamlet': 'hamlet_prince',
    'julius-caesar': 'julius_given_name caesar_julius',
    'king-john': 'king john_plantagenet_king', 'king-lear': 'king lear_british_king',
    'loves-labors-lost': 'love/labour lose:psv:pp',
    'macbeth': 'macbeth_scottish_thane', 'measure-for-measure': 'measure for measure',
    'the-merchant-of-venice': 'venice_lagoon_city/merchant',
    'the-merry-wives-of-windsor': 'merry:m windsor_seat/wife:pl',
    'a-midsummer-nights-dream': 'midsummer/night/vision',
    'much-ado-about-nothing': 'about nothing much pother_commotion',
    'othello': 'othello_venetian_general', 'pericles': 'pericles_tyrian_prince, tyre_princes_city/prince',
    'romeo-and-juliet': 'romeo_montague_son and juliet_capulet_daughter',
    'the-taming-of-the-shrew': 'scold:ag:a tame:inf', 'the-tempest': 'tempest',
    'timon-of-athens': 'timon_misanthrope of athens', 'titus-andronicus': 'titus_andronici_father andronicus_roman_family',
    'troilus-and-cressida': 'troilus and cressida', 'twelfth-night': 'unta_ordinal_bc_over_b night',
    'the-two-gentlemen-of-verona': 'verona_city/gentleman:du',
    'the-two-noble-kinsmen': 'noble:m kinsman:du', 'the-winters-tale': 'winter/tale',
    'lucrece': 'lucrece', 'the-phoenix-and-turtle': 'phoenix_symbol and turtle_symbol',
    'shakespeares-sonnets': 'sonnet:pl', 'venus-and-adonis': 'venus and adonis',
}
REGNAL = [('henry-iv', 'henry_bolingbroke', 'e', 2), ('henry-v', 'henry_accession', 'f', 0),
          ('henry-vi', 'henry_vi_infant', 'g', 3), ('henry-viii', 'henry_eighth_king', 'i', 0),
          ('richard-ii', 'richard_deposed', 'c', 0), ('richard-iii', 'richard_york_son', 'd', 0)]
for slug, name, ordinal, parts in REGNAL:
    reign = name + ' unta_ordinal_' + ordinal + '_over_b'
    if parts:
        for n in range(1, parts+1):
            TITLES[f'{slug}-part-{n}'] = reign + ', part unta_cardinal_' + 'bcd'[n-1] + '_over_b_digits'
    else:
        TITLES[slug] = reign


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.writing')
    tmp.write_text(json.dumps(value, ensure_ascii=False, separators=(',', ':')), encoding='utf8')
    tmp.replace(path)


def place_title_art(edition, title):
    raw = TITLE_ART.read_bytes()
    key = hashlib.sha256(raw).hexdigest()
    with Image.open(BytesIO(raw)) as image:
        width, height = image.size
        # Measure the engraved border, including the ornament above the frame.
        # Its white surround remains part of the embedded original PNG.
        x0,y0,x1,y1 = image.convert('L').point(lambda v: 255 if v < 96 else 0).getbbox()
    available = 792 - TOP - BOTTOM
    scale = min(MEASURE/(x1-x0), available/(y1-y0))
    rect = [306-scale*(x0+x1)/2, TOP+(available-scale*(y0+y1))/2, width*scale, height*scale]
    prior = {item['asset'] for item in title['images']}
    title['images'] = [dict(asset=key, rect=rect)]
    edition['assets'][key] = dict(png=base64.b64encode(raw).decode('ascii'),width=width,height=height)
    for page in edition['pages'].values():
        prior.difference_update(item['asset'] for item in page['images'])
    for unused in prior:
        del edition['assets'][unused]


def replace_title(state):
    page = state['pages'][0]
    edition = state['printEdition']
    title = edition['pages'][page['pageId']]
    assert title['kind']=='title'
    # Earlier impressions set the title and author as two navigation labels.
    # The approved plate includes both lines of lettering.
    records = [r for r in edition['verses'] if any(f['pageId']==page['pageId'] for f in r['fragments'])]
    assert {r['id'] for r in records} in (set(), {'nav/title','nav/author'})
    edition['verses'] = [r for r in edition['verses'] if r['id'] not in ('nav/title','nav/author')]
    blank=state['pages'][1]
    assert edition['pages'][blank['pageId']]['kind']=='blank' and not pe.text_of(blank)
    frame=page['frames'][0]
    frame['content']=deepcopy(blank['frames'][0]['content'])
    frame['content']['document']['title']=page['name']
    title.update(lines=[],sourceSha256=pe.hash_text(''))
    place_title_art(edition,title)


def sources():
    project = read(PROJECT / 'project.json')
    works = [*project['works'], *(dict(slug=s, title=OLDER[s], **w)
             for s, w in project['existingPlayImpressions'].items())]
    assert len(works) == len({w['slug'] for w in works}) == 42
    return sorted(works, key=lambda w: (w['slug'] in POEMS,
                  re.sub(r'^(the|an|a)-', '', w['slug']) if w['slug'] != 'shakespeares-sonnets' else 'sonnets'))


def issued_columns(path):
    pages=unpack(read(path))['state']['pages']
    for i in range(0,len(pages),2):
        columns=[texts(f) for page in pages[i:i+2] for f in sorted(page['frames'],key=lambda f:int(f['x']))]
        if len(columns)!=4:
            raise ValueError(f'{path}, spread {i//2+1}: four columns required')
        yield from zip(*columns,strict=True)


def extract():
    for work in sources():
        slug = work['slug']
        path = saved_source(work['output'])
        ledger = saved_source(work['currentLedger']) if work.get('currentLedger') else PROJECT / 'Ledgers' / (slug + '.json')
        if digest(path) != work['sha256']:
            raise ValueError('Unexpected issued manuscript: ' + str(path))
        ledger_hash = digest(ledger)
        cache = STAGE / 'sources' / (slug + '.json')
        if cache.exists():
            old = read(cache)
            if (old['nativeHash'], old['ledgerHash']) == (work['sha256'], ledger_hash):
                continue
        rows = []
        units = iter(read(ledger)['units'])
        for native, roman, gloss, english in issued_columns(path):
            u = next(units)
            if native != u['text'] or roman != native or english != u['source'] or not native.strip():
                raise ValueError(f'{slug}/{u["id"]}: source alignment')
            rows.append(dict(id=u['id'], text=native, english=english,
                             continuation=u.get('continuesParagraph', u.get('part', 0) > 0)))
        if next(units, None) is not None:
            raise ValueError('Unconsumed ledger: ' + slug)
        write(cache, dict(nativeHash=work['sha256'], ledgerHash=ledger_hash, rows=rows))
        print(f'{slug}: {len(rows)} paragraphs checked against the saved native column', flush=True)


class Typesetter(Proof):
    def __init__(self, punctuation):
        super().__init__()
        self.fonts.register(punctuation['path'], punctuation['sha256'])
        self.glyph_bounds = {}

    def layout(self, text, size, width=None):
        layout = QTextLayout(text, pe.font(self, size))
        opt = QTextOption()
        opt.setTextDirection(Qt.LayoutDirection.LeftToRight)
        opt.setWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere if width else QTextOption.WrapMode.NoWrap)
        layout.setTextOption(opt)
        layout.setFormats(pe.text_formats(self, text, size, dramatic=True))
        layout.beginLayout()
        while True:
            line = layout.createLine()
            if not line.isValid():
                break
            line.setLineWidth(width or 100000)
        layout.endLayout()
        return layout

    @lru_cache(maxsize=4096)
    def ink(self, text, size):
        layout = self.layout(text, size)
        bounds = QRectF()
        ascent = layout.lineAt(0).ascent()
        for run in layout.glyphRuns():
            raw = run.rawFont()
            cache = self.glyph_bounds.setdefault((raw.familyName(), raw.pixelSize()), {})
            for gid, pos in zip(run.glyphIndexes(), run.positions(), strict=True):
                if not gid:
                    raise ValueError('Missing print glyph: ' + repr(text))
                if gid not in cache:
                    cache[gid] = raw.pathForGlyph(gid).boundingRect()
                rect = cache[gid]
                if not rect.isEmpty():
                    bounds = bounds.united(rect.translated(pos.x(), pos.y()-ascent))
        return bounds


class Volume:
    def __init__(self, reference, punctuation, works):
        self.proof = Typesetter(punctuation)
        self.lang = EditorialLanguage(PROJECT/'Language')
        self.works = works
        self.headings = {s:self.native(a) for s,a in TITLES.items()}
        assert set(self.headings) == {w['slug'] for w in works}
        self.state = reference
        self.prototype = reference['pages'][0]
        self.edition = dict(version=1, layoutVersion=pe.COLLECTED,
                            typography=dict(pe.COMPACT_TYPE), languageVersion='Shakespeare 0.13 and 0.14, issued texts',
                            sourceSha256=pe.hash_text('\n'.join(w['sha256'] for w in works)),
                            ledgerSha256=pe.hash_text('\n'.join(read(STAGE/'sources'/(w['slug']+'.json'))['ledgerHash'] for w in works)),
                            assets={}, pages={}, verses=[], sections=[])
        reference.update(title=TITLE, documentId='document.shakespeare.collected', pages=[], revision=0,
                         printEdition=self.edition)
        reference['fontSources'].append(punctuation)
        self.records = {}
        self.page = None
        self.work = None
        self.start_body = 5

    def native(self, analysis):
        return self.lang.compile(analysis)['text']

    def new_page(self, kind, name):
        if self.page:
            self.finish_page()
        n = len(self.state['pages'])+1
        self.pid = f'page.collected.{n:05}'
        # The printed spreads follow the native two-page view: 1|2, 3|4, etc.
        self.left = (INNER+OUTER)/2 if kind=='title' else (OUTER if n%2 else INNER)
        self.page = dict(kind=kind, side='center' if kind=='title' else ('left' if n%2 else 'right'),
                         folio=n-self.start_body+1 if kind in ('opening','body') else None, lines=[], paths=[], images=[])
        self.name, self.source, self.y = name, '', TOP+LEADING
        self.last_bottom = TOP

    def finish_page(self):
        page = deepcopy(self.prototype)
        page.update(pageId=self.pid, name=self.name, margins=dict(left=mp(self.left), right=mp(612-self.left-MEASURE),
                    top=mp(TOP), bottom=mp(BOTTOM)))
        f = page['frames'][0]
        f.update(frameId=self.pid.replace('page.', 'frame.'), name=self.name, x=mp(self.left), y=mp(TOP),
                 width=mp(MEASURE), height=mp(792-TOP-BOTTOM))
        old = f['content']['document']
        content = f['content'] = blank_content(self.state['documentId'], f['width'], f['height'], '')
        doc = content['document']
        doc.update(title=self.name, fonts=old['fonts'], styles=old['styles'])
        doc['stories'][0]['blocks']=[dict(blockId='block.1', type='paragraph', direction='ltr',
              runs=[unicode_run(self.source, 'run.1', 'language.vayrshemon')])]
        self.page['sourceSha256'] = pe.hash_text(self.source)
        self.edition['pages'][self.pid] = self.page
        self.state['pages'].append(page)
        self.page = None

    def fragment(self, key, text, a, b):
        if key not in self.records:
            rec = dict(id=key, sha256=pe.hash_text(text), fragments=[])
            self.records[key] = rec
            self.edition['verses'].append(rec)
        spans = self.records[key]['fragments']
        if spans and spans[-1]['pageId']==self.pid and spans[-1]['end']==a:
            spans[-1]['end'] = b
        else:
            spans.append(dict(pageId=self.pid, start=a, end=b))

    def place(self, start, end, x, baseline, size, bounds, word_gap=0):
        r = bounds.translated(x, baseline)
        if r.left()<self.left-.005 or r.right()>self.left+MEASURE+.005 or r.top()<TOP-.005 or r.bottom()>792-BOTTOM+.005:
            raise ValueError(f'Outside print area at {self.name}: {r}, {self.source[start:end]}')
        line = dict(start=start, end=end, x=x, baseline=baseline, width=max(1.,r.width()),
                    bounds=list(r.getRect()), prefix='')
        if size != BODY:
            line['sizePt'] = size
        if word_gap:
            line['wordGapPt'] = word_gap
        self.page['lines'].append(line)
        self.last_bottom = r.bottom()

    def label(self, key, text, size, baseline, at=0, width=MEASURE, align='center'):
        bounds = self.proof.ink(text,size)
        if bounds.width()>width:
            raise ValueError(f'Label exceeds {width} pt: {key}, {bounds.width():.2f} pt')
        offset = {'left':0, 'center':(width-bounds.width())/2, 'right':width-bounds.width()}[align]
        if self.source:
            self.source += '\n'
        start=len(self.source)
        self.source+=text
        self.fragment(key,text,start,len(self.source))
        self.place(start,len(self.source),self.left+at+offset-bounds.left(),baseline,size,bounds)

    def front_matter(self):
        self.new_page('title','Title page')
        place_title_art(self.edition,self.page)
        self.new_page('blank','Blank')
        self.new_page('frontispiece','Frontispiece')
        rows=read(STAGE/'sources/as-you-like-it.json')['rows']
        u,=[u for u in rows if "all the world's a stage" in u['english'].lower()]
        quote=u['text'].split(': ',1)[1].split('. ',1)[0]+'.'
        first,second=quote.split(', ',1)
        self.label('nav/frontis/1',first+',',40,327)
        self.label('nav/frontis/2',second,32,361)
        self.label('nav/frontis/credit',u['text'].split(':')[0]+', '+self.headings['as-you-like-it'],28,408)
        self.new_page('contents','Contents')
        self.label('nav/contents',self.native('writing:pl/list'),50,93)
        entries = [(w['slug'],w['slug'] in POEMS) for w in self.works]
        cols = [entries[:21], entries[21:]]
        for col, group in enumerate(cols):
            x=col*251
            y=146
            for idx,(slug,poem) in enumerate(group):
                if (col==0 and idx==0) or (poem and (idx==0 or not group[idx-1][1])):
                    if idx: y+=9
                    self.label('nav/toc/'+('poems' if poem else 'plays'),self.native(VERSES if poem else PLAYS),
                               34,y,at=x,width=235,align='left')
                    y+=27
                elif col==1 and idx==0:
                    y+=27
                self.label('nav/toc/'+slug,self.headings[slug],24,y,at=x,width=211,align='left')
                self.label('nav/placeholder/'+slug,'—',24,y,at=x+214,width=21,align='right')
                y+=23

    def paragraph(self, items, centered=False, keep_next=False):
        # Offsets belong to the original units. Only the space BETWEEN two units
        # is editorial; a fragment crossing a line or page keeps its own spaces.
        starts,ends,pieces=[],[],[]
        length=0
        for key,row in items:
            if pieces:
                gap=' ' if row['continuation'] else '   '
                pieces.append(gap)
                length+=len(gap)
            starts.append(length)
            pieces.append(row['text'])
            length+=len(row['text'])
            ends.append(length)
        paragraph=''.join(pieces)
        layout=self.proof.layout(paragraph,BODY,MEASURE-2)
        for i in range(layout.lineCount()):
            line=layout.lineAt(i)
            a=line.textStart()
            b=a+line.textLength()
            segment=paragraph[a:b]
            visible=segment.strip()
            bounds=self.proof.ink(visible,BODY)
            baseline=max(self.y,self.last_bottom+.25-bounds.top())
            reserve=LEADING if keep_next and i==layout.lineCount()-1 else 0
            if baseline+bounds.bottom()+reserve>792-BOTTOM:
                self.new_page('body',self.work['title'])
                baseline=max(self.y,TOP-bounds.top())
            if self.source and i==0:
                self.source+='\n'
            start=len(self.source)
            self.source+=segment
            row_index=bisect_right(ends,a)
            while row_index<len(items) and starts[row_index]<b:
                key,row=items[row_index]
                first=max(a,starts[row_index])
                last=min(b,ends[row_index])
                if first<last:
                    self.fragment(key,row['text'], start+first-a,start+last-a)
                row_index+=1
            trim=len(segment)-len(segment.lstrip())
            x=self.left + ((MEASURE-bounds.width())/2-bounds.left() if centered else max(0.,-bounds.left()))
            gap=0.
            if i+1<layout.lineCount() and not centered:
                gaps=len(visible.split())-1
                if gaps:
                    x=self.left-bounds.left()
                    extra=MEASURE-bounds.width()
                    gap=extra/gaps
                    bounds=bounds.adjusted(0,0,extra,0)
            self.place(start+trim,start+trim+len(visible),x,baseline,BODY,bounds,gap)
            self.y=baseline+LEADING

    def compose_work(self, work):
        self.work=work
        slug=work['slug']
        self.new_page('opening',work['title'])
        self.edition['sections'].append(dict(number=len(self.edition['sections'])+1,name=work['title'],pageId=self.pid))
        rows=read(STAGE/'sources'/(slug+'.json'))['rows']
        first_source_title=(rows[0]['text']==self.headings[slug])
        title_key=(slug+'/'+rows[0]['id']) if first_source_title else 'nav/work/'+slug
        self.label(title_key,self.headings[slug],46,99)
        self.y=135
        group=[]
        for row in rows[int(first_source_title):]:
            key=slug+'/'+row['id']
            heading=bool(HEADING.match(row['english'])) if slug not in POEMS else row['english'].strip().isdigit()
            if heading or (slug in POEMS and not row['continuation']):
                if group:
                    self.paragraph(group)
                    group=[]
                if heading:
                    self.paragraph([(key,row)],centered=len(row['text'])<48,keep_next=True)
                    continue
            group.append((key,row))
        if group: self.paragraph(group)
        print(f'{work["title"]} set through page {len(self.state["pages"])+1}', flush=True)

    def compose(self):
        self.front_matter()
        for work in self.works:
            self.compose_work(work)
        self.finish_page()
        number_contents(self.state,self.works,self.proof)
        self.state['activeFrameId']=self.state['pages'][0]['frames'][0]['frameId']
        return self.state


def contents_divider(page, spec):
    frame=page['frames'][0]
    center=(int(frame['x'])+int(frame['width'])/2)/1e6
    columns=[QRectF(*line['bounds']) for line in spec['lines'][1:]]
    top=min(box.top() for box in columns)
    bottom=max(box.bottom() for box in columns)
    rule=QPainterPath()
    rule.addRect(QRectF(center-.2,top,.4,bottom-top))
    return pe.encode_path(rule,'contents-column-divider')


def number_contents(state, works, proof):
    """Finish the two-column contents page once the printed opening folios are known."""
    edition=state['printEdition']
    page,=(p for p in state['pages'] if edition['pages'][p['pageId']]['kind']=='contents')
    pid=page['pageId']
    spec=edition['pages'][pid]
    source=pe.text_of(page)
    records={r['fragments'][0]['start']:r for r in edition['verses'] if r['fragments'][0]['pageId']==pid}
    folios={}
    for work,section in zip(works,edition['sections'],strict=True):
        assert section['name']==work['title']
        opening=edition['pages'][section['pageId']]
        assert opening['kind']=='opening' and opening['folio'] is not None
        folios[work['slug']]=digits(opening['folio'])

    parts=[]
    length=0
    previous=''
    for line in spec['lines']:
        a,b=line['start'],line['end']
        record=records[a]
        fragment,=record['fragments']
        assert fragment==dict(pageId=pid,start=a,end=b)
        text=source[a:b]
        if record['id'].startswith(('nav/placeholder/','nav/folio/')):
            slug=record['id'].split('/')[-1]
            assert previous=='nav/toc/'+slug
            text=folios.pop(slug)
            ink=proof.ink(text,line['sizePt'])
            right=QRectF(*line['bounds']).right()
            x=right-ink.right()
            line.update(x=x,width=ink.width(),bounds=list(ink.translated(x,line['baseline']).getRect()))
            record.update(id='nav/folio/'+slug,sha256=pe.hash_text(text))
        if parts:
            parts.append('\n')
            length+=1
        line.update(start=length,end=length+len(text))
        fragment.update(start=line['start'],end=line['end'])
        parts.append(text)
        length=line['end']
        previous=record['id']
    assert not folios
    story,=page['frames'][0]['content']['document']['stories']
    block,=story['blocks']
    run,=block['runs']
    assert run['text']==source
    run['text']=''.join(parts)
    spec['sourceSha256']=pe.hash_text(run['text'])
    spec['paths']=[contents_divider(page,spec)]


def punctuation_source(works):
    state=unpack(read(saved_source(works[0]['output'])))['state']
    return next(f for f in state['fontSources'] if f['fontId']==pe.DRAMA_PUNCT)


def publish_state(state, works):
    if (DEST.parent/'FROZEN.json').exists():
        raise ValueError(f'The collected Letter edition is sealed: {DEST}')
    pe.validate(state)
    stage=STAGE/DEST.name
    book=FileSession(ROOT,recovery=False)
    book.remember=lambda path: None
    book.log.emit=lambda *a,**kw: None
    try:
        for font in state['fontSources']:
            book.fonts.register(book.fonts.document_path(font['path'],font['sha256']),font['sha256'])
        book._restore(state,take_ownership=True)
        book._state=book.capture()
        book.save(stage,preview_mode='two')
        before=book.capture()
        book.open(stage,advance_revision=False)
        assert before==book.capture() and book.saved_page_mode=='two'
    finally:
        book.finish()
    verify(unpack(read(stage))['state'], works, compare_issued=True)
    DEST.parent.mkdir(exist_ok=True)
    stage.replace(DEST)
    print(f'Published {len(state["pages"])} pages in {DEST}',flush=True)


def publish():
    works=sources()
    volume=Volume(unpack(read(REFERENCE))['state'],punctuation_source(works),works)
    state=volume.compose()
    publish_state(state,works)


def verify(state, works, compare_issued=False):
    ed=state['printEdition']
    pe.validate(state)
    pages={p['pageId']:pe.text_of(p) for p in state['pages']}
    records={r['id']:''.join(pages[f['pageId']][f['start']:f['end']] for f in r['fragments']) for r in ed['verses']}
    ids=[]
    for w in works:
        rows=read(STAGE/'sources'/(w['slug']+'.json'))['rows']
        for u in rows:
            k=w['slug']+'/'+u['id']
            ids.append(k)
            assert records[k]==u['text'],k
        if compare_issued:
            path=saved_source(w['output'])
            assert digest(path)==w['sha256']
            for row,cols in zip(rows,issued_columns(path),strict=True):
                assert records[w['slug']+'/'+row['id']]==cols[0], (w['title'],row['id'])
    assert ids==[k for k in records if not k.startswith('nav/')]
    assert [s['name'] for s in ed['sections']]==[w['title'] for w in works]
    toc=next(p for p in state['pages'] if ed['pages'][p['pageId']]['kind']=='contents')
    toc_spec=ed['pages'][toc['pageId']]
    toc_lines={line['start']:line for line in toc_spec['lines']}
    refs={r['id']:r['fragments'][0] for r in ed['verses'] if r['fragments'][0]['pageId']==toc['pageId']}
    assert not any(k.startswith('nav/placeholder/') for k in refs)
    assert [k for k in refs if k.startswith('nav/folio/')]==['nav/folio/'+w['slug'] for w in works]
    for w,section in zip(works,ed['sections'],strict=True):
        key='nav/folio/'+w['slug']
        opening=ed['pages'][section['pageId']]
        label='nav/toc/'+w['slug']
        title=opening['lines'][0]
        assert records[label]==pages[section['pageId']][title['start']:title['end']]
        assert records[key]==digits(opening['folio'])
        name_line=toc_lines[refs[label]['start']]
        number_line=toc_lines[refs[key]['start']]
        assert name_line['baseline']==number_line['baseline']
        assert QRectF(*number_line['bounds']).left()-QRectF(*name_line['bounds']).right()>=4
    assert [s['kind'] for s in list(ed['pages'].values())[:4]]==['title','blank','frontispiece','contents']
    title_id=state['pages'][0]['pageId']
    title=ed['pages'][title_id]
    plate,=title['images']
    assert not title['lines'] and not pages[title_id] and not list(pages.values())[1]
    assert set(ed['assets'])=={plate['asset']} and not any(p['images'] for pid,p in ed['pages'].items() if pid!=title_id)
    assert not any(p['paths'] for pid,p in ed['pages'].items() if pid!=toc['pageId'])
    assert toc_spec['paths']==[contents_divider(toc,toc_spec)]
    rule_box=QRectF(*toc_spec['paths'][0]['bounds'])
    assert all(not rule_box.intersects(QRectF(*line['bounds'])) for line in toc_spec['lines'])
    return len(ids)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=['extract','publish','contents','title-page','pdf'],default='extract',nargs='?')
    args=parser.parse_args()
    if args.operation=='extract':
        extract()
    else:
        app=QApplication([])
        if args.operation=='publish':
            extract()
            publish()
        elif args.operation=='title-page':
            state=unpack(read(DEST))['state']
            replace_title(state)
            publish_state(state,sources())
        elif args.operation=='contents':
            state=unpack(read(DEST))['state']
            works=sources()
            proof=Typesetter(next(f for f in state['fontSources'] if f['fontId']==pe.DRAMA_PUNCT))
            number_contents(state,works,proof)
            publish_state(state,works)
        else:
            from tools.shakespeare_collected_pdf import export
            export()
