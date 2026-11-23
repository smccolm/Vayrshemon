"""Set and verify the native Letter companion to the published four-column thesaurus."""
from collections import defaultdict
from itertools import groupby
from pathlib import Path
from tempfile import TemporaryDirectory

from PySide6.QtWidgets import QApplication

from tools import shakespeare_collected as sc
from tools import vayrshemon_thesaurus as progressive
from tools.compose_historical_book import texts
from tools.comprehensive_grammar_print import lines_for
from tools.dictionary_corpus import ROOT, sha
from tools.dictionary_print import BODY_BOTTOM
from tools.dictionary_rows import collate
from tools.idiom_print import IdiomVolume, body_lines, header_rule
from tools.shakespeare_collected_pdf import render_duplex


TITLE = 'Vayrshemon Thesaurus'
SOURCE = progressive.FOLDER / (progressive.TITLE + '.vay')
DEST = ROOT / 'Saves' / (TITLE + ' - Letter Print Edition')
STAGE = ROOT / '.local/thesaurus-print'
NATIVE = TITLE + '.vay'
PDF = TITLE + ' - Duplex Print.pdf'
MANIFEST = 'edition-manifest.json'
TOP = 89
INDEX_GUTTER = 22
INDEX_WIDTH = (sc.MEASURE-INDEX_GUTTER)/2


def read_source():
    receipt = sc.read(progressive.WORK/'publication.json')
    if sha(SOURCE) != receipt['sha256']:
        raise ValueError('Reconcile the progressive edition with its publication receipt.')
    state = sc.unpack(sc.read(SOURCE))['state']
    register = sc.read(progressive.WORK/'sense-register.json')
    spreads = sc.read(progressive.WORK/'page-index.json')
    assert len(state['pages']) == receipt['pages'] == 2*len(spreads)
    groups, heads, guides, index = [], [], {}, {}
    expected, words = {}, defaultdict(list)
    section_names = set()
    for spread in spreads:
        pair = state['pages'][spread['leftPage']-1:spread['rightPage']]
        frames = [f for page in pair for f in sorted(page['frames'], key=lambda f:int(f['x']))]
        assert [f['name'] for f in frames] == receipt['columns']
        for key, native, roman, gloss, english in zip(spread['ids'], *map(texts,frames), strict=True):
            assert native==roman and native.strip() and gloss and english
            if key.startswith('family-'):
                assert english not in section_names
                section_names.add(english)
                groups.append((english, []))
                heads.append(native)
                expected[f'section-{len(groups)}'] = native
            elif key.startswith('term-'):
                term = register[key[5:]]
                assert term['family']==groups[-1][0] and term['leftPage']==spread['leftPage']
                head, separator, rest = native.partition(': ')
                example = term['example']
                definition = rest.removesuffix(' '+example)
                assert head==term['form'] and separator and example.strip() and definition and definition!=rest
                assert english.endswith(term['exampleEnglish']) and definition.endswith('.')
                expected[key] = head+': '+definition
                expected[key+'-ex1'] = example
                assert expected[key]+' '+example==native
                groups[-1][1].append(dict(id=key,native=head,definition=dict(native=definition),
                                          examples=[dict(native=example)]))
                words[head].append((key,spread['leftPage']))
            elif key.startswith('index-'):
                head, rest = native.split(': ',1)
                parts = rest.removesuffix('.').split('. ')
                pointers = []
                for label,(term,leaf) in zip(parts,words[head],strict=True):
                    old = ' '+sc.digits(leaf)+', '+sc.digits(leaf+1)
                    assert label.endswith(old)
                    pointers.append((label.removesuffix(old),term))
                assert head not in index
                index[head] = pointers
            else:
                assert key in ('title','guide','use-guide','coinage-guide','index')
                guides[key] = native
    assert len(groups)==receipt['families'] and all(len(terms)>=2 for _,terms in groups)
    assert [e['id'][5:] for _,terms in groups for e in terms]==list(register)
    assert len(register)==receipt['senseExamples'] and len(index)==receipt['indexedSpellings']
    assert list(index)==sorted(words,key=collate)
    assert len({v['example'] for v in register.values()})==len(register)
    return receipt, state['language'], guides, heads, groups, expected, index


def entry_pages(lines):
    """Keep each definition with the opening of its example; flow long examples line by line."""
    pages, page = [], []
    bottom = TOP
    for i,line in enumerate(lines):
        top = bottom+(line.gap if page else 0)
        stop = i+1
        if line.heading or (line.start==0 and not line.key.endswith('-ex1')):
            first = i+int(line.heading)
            term = lines[first].key
            stop = first+1
            while lines[stop].key==term:
                stop += 1
            assert lines[stop].key==term+'-ex1'
            stop += 1
            # A two-line example reads best as one unit.
            if stop<len(lines) and lines[stop].key==term+'-ex1' and lines[stop].end==len(lines[stop].raw):
                stop += 1
        height = line.height+sum(l.gap+l.height for l in lines[i+1:stop])
        if top+height>BODY_BOTTOM:
            assert page
            pages.append(page)
            page,top = [],TOP
        assert top+height<=BODY_BOTTOM
        page.append((line,top))
        bottom = top+line.height
    if page:
        pages.append(page)
    return pages


class ThesaurusVolume(IdiomVolume):
    def running_head(self, left, right):
        folio = self.page['folio']
        # Both labels are native reading aids and have separate ink boundaries.
        for size in range(22,13,-1):
            if self.proof.ink(left,size).width()+self.proof.ink(right,size).width()+18 < sc.MEASURE:
                break
        self.label(f'nav/running-title/{folio}',left,size,66,align='left')
        self.label(f'nav/running-range/{folio}',right,size,66,align='right')
        header_rule(self,77)

    def plain_line(self, line, top, x=0):
        raw = line.row['text']
        part = raw[line.start:line.stop]
        if self.source and line.start==0:
            self.source+='\n'
        offset = len(self.source)
        self.source += part
        self.fragment(line.row['id'],raw,offset,len(self.source))
        visible = part.rstrip()
        self.place(offset,offset+len(visible),self.left+x+line.inset-line.ink.left(),
                   top-line.ink.top(),line.size,line.ink)

    def compose(self,guides,heads,groups,index,expected):
        self.start_body=3
        sheets = entry_pages(list(body_lines(self.proof,heads,groups)))
        folios = {}
        for n,sheet in enumerate(sheets,1):
            for line,_ in sheet:
                folios.setdefault(line.key,n)
        self.new_page('title','Title page')
        title = guides['title']
        self.label('title',title,53,285)
        y=346
        for key in ('guide','use-guide','coinage-guide'):
            # The rest of this last guide describes a column in the parallel edition.
            text=guides[key].split('. ',1)[0]+'.' if key=='coinage-guide' else guides[key]
            row=dict(id=key,kind='guide',text=text)
            for line in lines_for(self.proof,row,25,14,width=sc.MEASURE-14):
                self.plain_line(line,y)
                y+=line.ink.height()+4
            y+=7
        self.label('nav/index-folio',guides['index']+' · '+sc.digits(len(sheets)+1),24,y+14)
        self.new_page('blank','Blank')
        sections, tops = [], {}
        for n,sheet in enumerate(sheets,1):
            first = sheet[0][0].subject
            self.new_page('opening' if any(l.heading for l,_ in sheet) else 'body',groups[first-1][0])
            assert self.page['folio']==n
            self.running_head(title,heads[first-1])
            for line,top in sheet:
                if line.heading:
                    name = groups[line.subject-1][0]
                    sections.append(dict(name=name,number=line.subject,pageId=self.pid))
                    tops[name]=top
                if not self.source or line.start==0 or line is sheet[0][0]:
                    self.source+='\n'
                a=len(self.source)
                self.source+=line.raw[line.start:line.end]
                self.fragment(line.key,line.raw,a,len(self.source))
                diff=a-line.start
                for begin,end,size,x,y,ink in line.runs:
                    self.place(diff+begin,diff+end,self.left+x,top+y-line.top,size,ink)
        self.index_pages(guides['index'],index,folios,expected,sections,tops)
        self.finish_page()
        self.state['activeFrameId']=self.state['pages'][0]['frames'][0]['frameId']
        # Native section navigation is page-based. PDF bookmarks additionally target
        # the individual family headings sharing that page.
        self.edition['sections']=[next(g) for _,g in groupby(sections,key=lambda s:s['pageId'])]
        assert len(self.edition['sections'])<=100
        return folios,sections,tops,len(sheets)

    def index_pages(self,title,index,folios,expected,sections,tops):
        columns, column = [], []
        # The opening heading takes space on both columns of the first index page.
        y=TOP+36
        for n,(head,refs) in enumerate(index.items(),1):
            key=f'index-{n}'
            raw=head+': '+'. '.join(label+' '+sc.digits(folios[term]) for label,term in refs)+'.'
            expected[key]=raw
            row=dict(id=key,text=raw,kind='index-term')
            lines=list(lines_for(self.proof,row,23,width=INDEX_WIDTH))
            height=sum(l.ink.height() for l in lines)+2.7*(len(lines)-1)
            if y+height>BODY_BOTTOM:
                columns.append(column)
                column=[]
                y=TOP+36 if len(columns)<2 else TOP
            assert y+height<=BODY_BOTTOM
            for line in lines:
                column.append((head,line,y))
                y+=line.ink.height()+2.7
            y+=2.5
        if column:
            columns.append(column)
        for j in range(0,len(columns),2):
            pair=columns[j:j+2]
            self.new_page('opening' if j==0 else 'body','Alphabetical word index')
            self.running_head(title, pair[0][0][0]+' – '+pair[-1][-1][0])
            if j==0:
                sections.append(dict(name='Alphabetical word index',number=len(sections)+1,pageId=self.pid))
                tops['Alphabetical word index']=TOP
                ink=self.proof.ink(title,35)
                self.label('index',title,35,TOP-ink.top(),align='left')
            for i,col in enumerate(pair):
                for head,line,top in col:
                    self.plain_line(line,top,i*(INDEX_WIDTH+INDEX_GUTTER))


def verify(saved, guides, groups, expected, index, folios, body_count):
    sc.pe.validate(saved)
    ed=saved['printEdition']
    pages={p['pageId']:sc.pe.text_of(p) for p in saved['pages']}
    records={r['id']:r['fragments'] for r in ed['verses']}
    joined={k:''.join(pages[f['pageId']][f['start']:f['end']] for f in fs) for k,fs in records.items()}
    assert [k for k in joined if k in expected]==list(expected)
    assert all(joined[k]==v for k,v in expected.items())
    for pid,text in pages.items():
        painted=bytearray(len(text))
        for line in ed['pages'][pid]['lines']:
            a,b=line['start'],line['end']
            assert not any(painted[a:b])
            painted[a:b]=bytes([1])*(b-a)
        assert all(is_ink or char.isspace() for char,is_ink in zip(text,painted,strict=True)), pid
    for k in ('title','guide','use-guide','index'):
        assert joined[k]==guides[k]
    assert joined['coinage-guide']==guides['coinage-guide'].split('. ',1)[0]+'.'
    assert joined['nav/index-folio']==guides['index']+' · '+sc.digits(body_count+1)
    def first_folio(k):
        return ed['pages'][records[k][0]['pageId']]['folio']
    assert first_folio('index')==body_count+1
    for i,(_,terms) in enumerate(groups,1):
        assert first_folio(f'section-{i}')==first_folio(terms[0]['id'])
        for term in terms:
            key=term['id']
            assert first_folio(key)==folios[key]==first_folio(key+'-ex1')
            assert len(term['examples'])==1 and joined[key+'-ex1']==term['examples'][0]['native']
    for n,(head,refs) in enumerate(index.items(),1):
        assert joined[f'index-{n}']==head+': '+'. '.join(label+' '+sc.digits(first_folio(k)) for label,k in refs)+'.'


def build():
    app=QApplication.instance() or QApplication([])
    receipt,language,guides,heads,groups,expected,index=read_source()
    volume=ThesaurusVolume(language,receipt,title=TITLE,document_id='document.thesaurus.letter',
                           ledger_sha=receipt['ledgerSha256'])
    folios,sections,tops,body_count=volume.compose(guides,heads,groups,index,expected)
    STAGE.mkdir(parents=True,exist_ok=True)
    with TemporaryDirectory(dir=STAGE) as tmp:
        work=Path(tmp)
        session=sc.FileSession(ROOT,source_fonts=False,recovery=False)
        session.remember=lambda *a,**kw:None
        session.log.emit=lambda *a,**kw:None
        try:
            for f in volume.state['fontSources']:
                session.fonts.register(session.fonts.document_path(f['path'],f['sha256']),f['sha256'])
            session._restore(volume.state,take_ownership=True)
            session._state=volume.state
            session.save(work/NATIVE,preview_mode='two')
            before=session.capture()
            session.open(work/NATIVE,advance_revision=False)
            saved=session.capture()
            assert saved==before and session.saved_page_mode=='two'
            verify(saved,guides,groups,expected,index,folios,body_count)
        finally:
            session.finish()
        pdf_state=saved|{'printEdition':saved['printEdition']|{'sections':sections}}
        physical=render_duplex(pdf_state,work/PDF,TITLE,use_printed_folios=True,section_tops=tops)
        assert sha(SOURCE)==receipt['sha256']
        report=dict(title=TITLE, sourceSha256=receipt['sha256'],nativeSha256=sha(work/NATIVE),pdfSha256=sha(work/PDF),
                    nativePages=len(saved['pages']),physicalPages=physical,duplexSheets=(physical+1)//2,bindingBlank=1,
                    bodyFolios=body_count,indexStartsOnFolio=body_count+1,
                    families=len(groups),primaryEntriesWithExample=len(groups),nativeSenseExamples=receipt['senseExamples'],
                    indexedHeadwords=len(index),authoredWords=receipt['authoredWords'],verifiedIndexPointers=sum(map(len,index.values())),
                    pdfBookmarks=len(sections),nativeReopenIdentical=True,pdfTextAndGeometryVerified=True,
                    familyFolios={group[0]:folios[f'section-{i}'] for i,group in enumerate(groups,1)})
        sc.write(work/MANIFEST,report)
        DEST.mkdir(exist_ok=True,parents=True)
        prior=sc.read(DEST/MANIFEST) if (DEST/MANIFEST).exists() else {}
        for name,key in ((NATIVE,'nativeSha256'),(PDF,'pdfSha256')):
            if (DEST/name).exists() and sha(DEST/name)!=prior.get(key):
                raise ValueError('Independent edits in '+str(DEST/name))
        for name in (NATIVE,PDF,MANIFEST):
            (work/name).replace(DEST/name)
        print({k:v for k,v in report.items() if k!='familyFolios'},flush=True)


if __name__=='__main__':
    build()

