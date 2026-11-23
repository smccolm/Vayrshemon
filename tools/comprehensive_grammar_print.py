"""Set the issued native grammar, including a repaginated chapter guide and subject index."""
from collections import Counter
from dataclasses import dataclass
from math import ceil
from pathlib import Path
from tempfile import TemporaryDirectory

from PySide6.QtWidgets import QApplication

from tools import comprehensive_grammar as grammar
from tools import shakespeare_collected as sc
from tools.compose_historical_book import texts
from tools.dictionary_corpus import ROOT, sha
from tools.dictionary_rows import collate
from tools.idiom_print import header_rule
from tools.shakespeare_collected_pdf import render_duplex


TITLE = grammar.NAME
SOURCE = grammar.FOLDER / (grammar.TITLE + '.vay')
DEST = ROOT / 'Saves' / (TITLE + ' - Letter Print Edition')
STAGE = ROOT / '.local/grammar-print'
NATIVE = TITLE + '.vay'
PDF = TITLE + ' - Duplex Print.pdf'
MANIFEST = 'edition-manifest.json'
TOP, BOTTOM = 90, 719


def source_rows():
    receipt = sc.read(grammar.WORK / 'publication.json')
    if sha(SOURCE) != receipt['sha256']:
        raise ValueError('Progressive publication has independent changes')
    state = sc.unpack(sc.read(SOURCE))['state']
    rows, _, _ = grammar.compile_book()
    by_id = {row['id']: row for row in rows}
    locations = {}
    for spread in sc.read(grammar.WORK / 'page-index.json'):
        pair = state['pages'][spread['leftPage']-1:spread['rightPage']]
        frames = [f for p in pair for f in sorted(p['frames'], key=lambda f:int(f['x']))]
        assert [f['name'] for f in frames] == receipt['columns']
        for key, native, roman, gloss, english in zip(spread['ids'], *map(texts, frames), strict=True):
            assert native == roman, key
            if key.startswith('guide-'):
                section = by_id[key[6:]]
                head, page = native.rsplit(' · ', 1)
                assert head == section['text']
                locations[key] = page
                continue
            row = by_id[key]
            if 'pointsTo' in row:
                old = locations[row['pointsTo']]
                assert native == row['text'] + ' · ' + sc.digits(old)
                assert gloss == row['gloss'] + ' · ' + str(old)
                assert english == row['source'] + ' · ' + str(old)
            else:
                assert (native, gloss, english) == (row['text'], row['gloss'], row['source']), key
                row['text'] = native
            locations[key] = spread['leftPage']
    assert len(locations) == receipt['rows']
    assert all(locations['guide-'+r['id']] == sc.digits(locations[r['id']])
               for r in rows if r['kind']=='section')
    first_term = next(i for i,r in enumerate(rows) if r['kind']=='index-term')
    assert all(r['kind']=='index-term' for r in rows[first_term:])
    rows[first_term:] = sorted(rows[first_term:],key=lambda r:collate(r['text']))
    return rows, state['language'], receipt


@dataclass
class Line:
    row: dict
    start: int
    stop: int
    size: int
    inset: int
    ink: object
    gap: float
    justify: bool


def lines_for(proof, row, size, inset=0, gap=3, width=None):
    raw = row['text']
    measure = (sc.MEASURE if width is None else width) - inset
    layout = proof.layout(raw, size, measure-4)
    for i in range(layout.lineCount()):
        segment = layout.lineAt(i)
        start = segment.textStart()
        stop = start + segment.textLength()
        visible = raw[start:stop].strip()
        ink = proof.ink(visible, size)
        if not visible or ink.width() > measure:
            raise ValueError(f'Unprintable line in {row["id"]}: {visible!r}')
        spaces = len(visible.split())-1
        justify = (row['kind']=='exposition' and i+1 < layout.lineCount() and spaces > 0
                   and (measure-ink.width())/spaces < 5)
        yield Line(row, start, stop, size, inset, ink, gap if i==0 else 3, justify)


def body_lines(proof, rows):
    lines = []
    for r in rows:
        kind = r['kind']
        if kind=='section':
            style = (32, 0, 12)
        elif kind=='verse-line':
            style = (27, 22, 5 if r['verseLine']==1 else 2)
        elif kind in ('example','idiom-example','witness','calculation'):
            style = (26, 14, 4)
        elif kind in ('technical-term','idiom-witness'):
            style = (30, 8, 6)
        else:
            style = (26, 0, 4)
        lines.extend(lines_for(proof, r, *style))
    return lines


def flow(lines):
    pages, sheet = [], []
    bottom = TOP
    for i, line in enumerate(lines):
        top = bottom + (line.gap if sheet else 0)
        last = i + 1
        row = line.row
        if line.start==0 and row['kind'] in ('section','index-term'):
            while last < len(lines) and lines[last].row is row:
                last += 1
            if row['kind']=='section':
                last = min(last+1, len(lines))
        next_row = lines[last-1].row
        if line.start==0 and next_row.get('verseLine')==1:
            # Keep a scored stanza on one page, including wrapped verse lines.
            while last < len(lines) and lines[last].row.get('verseLine',0):
                if lines[last].start==0 and lines[last].row is not next_row and lines[last].row['verseLine']==1:
                    break
                last += 1
        need = line.ink.height()+sum(l.gap+l.ink.height() for l in lines[i+1:last])
        if sheet and top+need > BOTTOM:
            pages.append(sheet)
            sheet, top = [], TOP
        if top+need > BOTTOM:
            raise ValueError('A heading or stanza exceeds one page: '+row['id'])
        sheet.append((line,top))
        bottom = top+line.ink.height()
    if sheet:
        pages.append(sheet)
    return pages


def folio_map(pages):
    folios = {}
    for n,sheet in enumerate(pages,1):
        for line,_ in sheet:
            folios.setdefault(line.row['id'],n)
    return folios


class GrammarVolume(sc.Volume):
    def __init__(self, language, receipt):
        template = ROOT/'Saves/Vayrshemon Idiom Inventory - Letter Print Edition/Vayrshemon Idiom Inventory.vay'
        self.state = sc.unpack(sc.read(template))['state']
        old = self.state['printEdition']
        heading = next(r for r in old['verses'] if r['id']=='nav/contents-1')
        pages = {p['pageId']:p for p in self.state['pages']}
        self.contents_title = ''.join(sc.pe.text_of(pages[f['pageId']])[f['start']:f['end']]
                                      for f in heading['fragments'])
        self.prototype = next(p for p in pages.values() if old['pages'][p['pageId']]['kind']=='body')
        self.proof = sc.Typesetter(next(f for f in self.state['fontSources'] if f['fontId']==sc.pe.DRAMA_PUNCT))
        self.edition = dict(version=1,layoutVersion=sc.pe.COLLECTED,typography=dict(sc.pe.COMPACT_TYPE),
                            languageVersion=TITLE,sourceSha256=receipt['sha256'],ledgerSha256=receipt['ledgerSha256'],
                            assets={},pages={},verses=[],sections=[])
        self.state.update(title=TITLE,documentId='document.comprehensive-grammar.letter',
                          language=language,revision=0,pages=[],printEdition=self.edition)
        self.page, self.records, self.start_body = None, {}, 1

    def draw_line(self, line, top, key=None):
        raw = line.row['text']
        if self.source and line.start==0:
            self.source += '\n'
        a = len(self.source)
        part = raw[line.start:line.stop]
        self.source += part
        self.fragment(key or line.row['id'],raw,a,len(self.source))
        visible = part.strip()
        start = a+len(part)-len(part.lstrip())
        ink = line.ink
        x, baseline = self.left+line.inset-ink.left(), top-ink.top()
        extra = sc.MEASURE-ink.width() if line.justify else 0
        gap = extra/(len(visible.split())-1) if line.justify else 0
        self.place(start,start+len(visible),x,baseline,line.size,ink.adjusted(0,0,extra,0),gap)

    def compose(self, rows):
        title, guide, *body = rows
        cut = next(i for i,r in enumerate(body) if r['id']=='subject-index')
        main_lines = body_lines(self.proof,body[:cut])
        folios = folio_map(flow(main_lines))
        for r in body[cut+1:]:
            r['text'] += ' · '+sc.digits(folios[r['pointsTo']])
        book = flow(main_lines + body_lines(self.proof,body[cut:]))
        folios = folio_map(book)
        sections = [r for r in body if r['kind']=='section']
        self.new_page('title','Title page')
        self.label('title',title['text'],56,317)
        self.new_page('blank','Blank')
        self.make_contents(sections,guide,folios)
        self.start_body = len(self.state['pages'])+2
        full_sections, tops = [], {}
        for n,sheet in enumerate(book,1):
            first = sheet[0][0].row
            self.new_page('opening' if any(line.row['kind']=='section' for line,_ in sheet) else 'body',first['reference'])
            assert self.page['folio']==n
            self.label(f'nav/running-title/{n}',title['text'],20,65,align='left')
            first_section,last_section = first['section'],sheet[-1][0].row['section']
            if first_section=='subject-index':
                label=sections[-1]['text']
            else:
                label=sc.digits(int(first_section[2:]))
                if last_section=='subject-index':
                    label+=' · '+sections[-1]['text']
                elif last_section!=first_section:
                    label+=' · '+sc.digits(int(last_section[2:]))
            self.label(f'nav/running-section/{n}',label,20,65,align='right')
            header_rule(self,77)
            for line,top in sheet:
                r = line.row
                if r['kind']=='section' and line.start==0:
                    name = r['reference']
                    full_sections.append(dict(name=name,number=len(full_sections)+1,pageId=self.pid))
                    tops[name] = top
                self.draw_line(line,top)
        self.finish_page()
        # Older readers store up to 100 native opening pages. Adjacent chapters
        # sharing a page use a single page destination and separate contents rows.
        for s in full_sections:
            if not self.edition['sections'] or self.edition['sections'][-1]['pageId']!=s['pageId']:
                self.edition['sections'].append(s.copy())
        self.state['activeFrameId']=self.state['pages'][0]['frames'][0]['frameId']
        return sections,full_sections,tops,folios,len(book)

    def make_contents(self, sections, guide, folios):
        num_pages = 0
        def new_contents():
            nonlocal num_pages
            num_pages += 1
            self.new_page('contents',f'Chapter guide {num_pages}')
            self.label(f'nav/contents/{num_pages}',self.contents_title,42,78)
            header_rule(self,91)
            return 103
        y = new_contents()
        for line in lines_for(self.proof,guide,25):
            self.draw_line(line,y)
            y += line.ink.height()+3
        y += 7
        for r in sections:
            number = sc.digits(folios[r['id']])
            lines = list(lines_for(self.proof,r,25,width=sc.MEASURE-42))
            number_box = self.proof.ink(number,24)
            heights = [max(lines[0].ink.height(),number_box.height()),*[l.ink.height() for l in lines[1:]]]
            if y+sum(heights)+3*(len(lines)-1)>BOTTOM:
                y=new_contents()
            first_y = y
            for line,h in zip(lines,heights,strict=True):
                self.draw_line(line,y,'nav/toc/'+r['id'])
                y += h+3
            self.label('nav/folio/'+r['id'],number,24,first_y-number_box.top(),
                       at=sc.MEASURE-36,width=36,align='right')
            y += 2


def verify(state, rows, folios, sections):
    sc.pe.validate(state)
    edition = state['printEdition']
    pages = {p['pageId']:sc.pe.text_of(p) for p in state['pages']}
    fragments = {r['id']:r['fragments'] for r in edition['verses']}
    rebuilt = {k:''.join(pages[f['pageId']][f['start']:f['end']] for f in fs) for k,fs in fragments.items()}
    expected = {r['id']:r['text'] for r in rows}
    assert {k:v for k,v in rebuilt.items() if k in expected}==expected
    assert [k for k in rebuilt if k in expected]==list(expected)
    for i,r in enumerate(rows[2:],2):
        f = fragments[r['id']][0]
        assert edition['pages'][f['pageId']]['folio']==folios[r['id']]
        if 'pointsTo' in r:
            assert rebuilt[r['id']].rsplit(' · ',1)[1]==sc.digits(folios[r['pointsTo']])
        if r['kind']=='section':
            assert folios[r['id']]==folios[rows[i+1]['id']]
        if r.get('verseLine')==1:
            last = rows[i+r['verseLength']-1]['id']
            assert f['pageId']==fragments[last][-1]['pageId']
    terms = [r['text'].rsplit(' · ',1)[0] for r in rows if r['kind']=='index-term']
    assert terms==sorted(terms,key=collate)
    by_folio = {edition['pages'][pid]['folio']:n for n,pid in enumerate(pages,1)}
    links = sc.pe.contents_links(state)
    assert [l['page'] for pid in pages for l in links.get(pid,[])]==[by_folio[folios[r['id']]] for r in sections]
    for r in sections:
        assert rebuilt['nav/toc/'+r['id']]==r['text']
        assert rebuilt['nav/folio/'+r['id']]==sc.digits(folios[r['id']])


def build():
    app = QApplication.instance() or QApplication([])
    rows,language,receipt = source_rows()
    volume = GrammarVolume(language,receipt)
    sections,full_sections,tops,folios,body_pages = volume.compose(rows)
    STAGE.mkdir(parents=True,exist_ok=True)
    print(f'Set {body_pages} body folios, {len(sections)} guide rows.',flush=True)
    with TemporaryDirectory(dir=STAGE) as temp:
        work = Path(temp)
        session = sc.FileSession(ROOT,source_fonts=False,recovery=False)
        session.remember = lambda *a,**kw:None
        session.log.emit = lambda *a,**kw:None
        try:
            for font in volume.state['fontSources']:
                session.fonts.register(session.fonts.document_path(font['path'],font['sha256']),font['sha256'])
            session._restore(volume.state,take_ownership=True)
            session._state = volume.state
            session.save(work/NATIVE,preview_mode='two')
            before = session.capture()
            session.open(work/NATIVE,advance_revision=False)
            saved = session.capture()
            assert before==saved and session.saved_page_mode=='two'
            verify(saved,rows,folios,sections)
        finally:
            session.finish()
        # PDF outlines can also target the exact heights of multiple chapter
        # headings on one sheet. All painted pages come from the reopened master.
        pdf_state = saved | {'printEdition':saved['printEdition'] | {'sections':full_sections}}
        physical = render_duplex(pdf_state,work/PDF,TITLE,use_printed_folios=True,section_tops=tops)
        assert sha(SOURCE)==receipt['sha256']
        kinds = Counter(r['kind'] for r in rows)
        report = dict(title=TITLE,sourceSha256=receipt['sha256'],nativeSha256=sha(work/NATIVE),pdfSha256=sha(work/PDF),
                      publication='Native text and examples',nativePages=len(saved['pages']),physicalPages=physical,
                      bindingBlank=1,duplexSheets=ceil(physical/2),bodyFolios=body_pages,nativeReopenIdentical=True,
                      verifiedProgressiveRows=receipt['rows'],verifiedPrintContentRows=len(rows),rowKinds=dict(kinds),
                      verifiedIndexEntries=kinds['index-term'],indexFiling='Thimfora, letter by letter',
                      verifiedContentsLinks=len(sections),
                      pdfTextAndGeometryVerified=True,chapterGuide=[dict(chapter=r['id'],heading=r['reference'],
                      folio=folios[r['id']]) for r in sections],
                      subjectIndex=[dict(entry=r['id'],term=r['source'],target=r['pointsTo'],
                      folio=folios[r['pointsTo']]) for r in rows if 'pointsTo' in r])
        sc.write(work/MANIFEST,report)
        DEST.mkdir(parents=True,exist_ok=True)
        old = sc.read(DEST/MANIFEST) if (DEST/MANIFEST).exists() else {}
        for name,key in ((NATIVE,'nativeSha256'),(PDF,'pdfSha256')):
            if (DEST/name).exists() and sha(DEST/name)!=old.get(key):
                raise ValueError('Independent edits in '+str(DEST/name))
        for name in (NATIVE,PDF,MANIFEST):
            (work/name).replace(DEST/name)
        print(f'Published {len(saved["pages"])} native pages and {physical} PDF pages.',flush=True)


if __name__=='__main__':
    build()
