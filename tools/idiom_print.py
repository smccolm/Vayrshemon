"""Set the published native idiom inventory as a single-column Letter edition."""
from dataclasses import dataclass
from itertools import groupby
from math import ceil
from pathlib import Path
from tempfile import TemporaryDirectory
import json

from PySide6.QtCore import QRectF
from PySide6.QtGui import QPainterPath
from PySide6.QtWidgets import QApplication

from tools import shakespeare_collected as sc
from tools.compose_historical_book import texts
from tools.dictionary_print import BODY_BOTTOM, ENTRY_GAP, typeset_article
from tools.dictionary_corpus import ROOT, sha
from tools.shakespeare_collected_pdf import render_duplex
from tools.vayrshemon_idioms import FOLDER, GRIEF, TITLE as PROGRESSIVE, WORK


TITLE = 'Vayrshemon Idiom Inventory'
DEST = ROOT / 'Saves' / (TITLE + ' - Letter Print Edition')
STAGE = ROOT / '.local' / 'idiom-print'
NATIVE = TITLE + '.vay'
PDF = TITLE + ' - Duplex Print.pdf'
MANIFEST = 'edition-manifest.json'
BODY_TOP = 101


def source_material():
    receipt = sc.read(WORK / 'publication.json')
    book = FOLDER / (PROGRESSIVE + '.vay')
    if sha(book) != receipt['sha256']:
        raise ValueError('The progressive edition differs from its publication receipt')
    state = sc.unpack(sc.read(book))['state']
    native = []
    for page in state['pages'][::2]:
        frame, = [f for f in page['frames'] if f['name'] == 'Vayrshemon']
        native.extend(texts(frame))
    title, guide = native[:2]
    subjects = receipt['subjects']
    heads = []
    for item, line in zip(subjects, native[2:2+len(subjects)], strict=True):
        head, number = line.rsplit(' · ', 1)
        assert number == sc.digits(item['leftPage'])
        heads.append(head)
    entries = sc.read(WORK / 'entries.json')
    groups = [(name, list(articles)) for name, articles in groupby(entries, key=lambda e:e['section'])]
    assert [name for name, articles in groups] == [s['label'] for s in subjects]
    expected = {}
    for idx, ((name, articles), heading) in enumerate(zip(groups, heads, strict=True), 1):
        expected[f'section-{idx}'] = heading
        for e in articles:
            expected[e['id']] = e['native'] + ': ' + e['definition']['native']
            for j, example in enumerate(e['examples'], 1):
                expected[f"{e['id']}-ex{j}"] = example['native']
    assert list(expected.values()) == native[2+len(subjects):]
    assert len(entries) == receipt['idioms']
    assert sum(len(e['examples']) for e in entries) == receipt['examples']
    assert sum(t.count(GRIEF) for t in expected.values()) == receipt['ultimateGrief']['verifiedOccurrencesPerReadingColumn']
    return receipt, state['language'], title, guide, heads, groups, expected


@dataclass
class Line:
    subject: int
    key: str
    raw: str
    start: int
    end: int
    runs: list
    top: float
    height: float
    gap: float
    heading: bool = False


def body_lines(proof, heads, groups):
    for idx, (heading, (_, articles)) in enumerate(zip(heads, groups, strict=True), 1):
        key = f'section-{idx}'
        ink = proof.ink(heading, 35)
        assert ink.width() <= sc.MEASURE
        yield Line(idx,key,heading,0,len(heading),[(0,len(heading),35,-ink.left(),0,ink)],
                   ink.top(),ink.height(),13,True)
        for e in articles:
            examples = [ex['native'] for ex in e['examples']]
            raw, _, runs, _ = typeset_article(e['native'],
                [dict(id=e['id'], definition=e['definition']['native'], examples=examples)],
                proof, sc.digits, sc.MEASURE, 32, 26)
            # Each progressive row has its own identity even when it crosses a page.
            fields = [(e['id'], e['native'] + ': ' + e['definition']['native'])]
            fields += [(f"{e['id']}-ex{j}", ex) for j,ex in enumerate(examples,1)]
            assert raw == ' '.join(t for _,t in fields)
            offset = 0
            baselines = iter(groupby(runs, key=lambda r:r[4]))
            prev_bottom = None
            for key, field in fields:
                pos = 0
                while pos < len(field):
                    baseline, parts = next(baselines)
                    parts = list(parts)
                    top = baseline + min(r[5].top() for r in parts)
                    bottom = baseline + max(r[5].bottom() for r in parts)
                    end = parts[-1][1] - offset
                    assert parts[0][0]-offset == pos and 0 < end <= len(field)
                    # Retain the source space when wrapping a native sentence.
                    boundary = end + int(end < len(field) and field[end] == ' ')
                    converted = [(a-offset,b-offset,pt,x,y,ink) for a,b,pt,x,y,ink in parts]
                    yield Line(idx,key,field,pos,boundary,converted,top,bottom-top,
                               ENTRY_GAP if prev_bottom is None else top-prev_bottom)
                    prev_bottom, pos = bottom, boundary
                offset += len(field) + 1
            assert next(baselines, None) is None


def paginate(lines):
    pages = []
    page = []
    bottom = BODY_TOP
    for i, line in enumerate(lines):
        reserve = 0
        if line.heading:
            first = lines[i+1]
            reserve = first.gap + first.height
        top = bottom + (line.gap if page else 0)
        if top + line.height + reserve > BODY_BOTTOM:
            assert page
            pages.append(page)
            page, top = [], BODY_TOP
        page.append((line,top))
        bottom = top + line.height
    if page:
        pages.append(page)
    return pages


def header_rule(volume, y):
    rule = QPainterPath()
    rule.addRect(QRectF(volume.left, y, sc.MEASURE, .55))
    volume.page['paths'].append(sc.pe.encode_path(rule, 'dictionary-running-head-rule'))


class IdiomVolume(sc.Volume):
    def __init__(self, language, receipt, *, title=TITLE, document_id='document.idiom-inventory.letter',
                 ledger_sha=None):
        template = ROOT / 'Saves/Paradise Lost - Letter Print Edition/Paradise Lost.vay'
        self.state = sc.unpack(sc.read(template))['state']
        old = self.state['printEdition']
        fragments = next(r['fragments'] for r in old['verses'] if r['id']=='nav/contents')
        pages = {p['pageId']:p for p in self.state['pages']}
        self.contents_heading = ''.join(sc.pe.text_of(pages[f['pageId']])[f['start']:f['end']] for f in fragments)
        self.prototype = self.state['pages'][4]
        self.proof = sc.Typesetter(next(f for f in self.state['fontSources'] if f['fontId']==sc.pe.DRAMA_PUNCT))
        self.edition = dict(version=1, layoutVersion=sc.pe.COLLECTED, typography=dict(sc.pe.COMPACT_TYPE),
                            languageVersion=title, sourceSha256=receipt['sha256'],
                            ledgerSha256=ledger_sha or sha(WORK/'entries.json'), assets={}, pages={}, verses=[], sections=[])
        self.state.update(title=title, documentId=document_id, revision=0,
                          pages=[], language=language, printEdition=self.edition)
        self.records = {}
        self.page = None

    def guide_paragraph(self, text, y):
        layout = self.proof.layout(text,26,sc.MEASURE-6)
        for i in range(layout.lineCount()):
            line = layout.lineAt(i)
            start, length = line.textStart(), line.textLength()
            part = text[start:start+length]
            visible = part.rstrip()
            a = len(self.source)
            self.source += part
            self.fragment('guide',part,a,len(self.source))
            ink = self.proof.ink(visible,26)
            self.place(a,a+len(visible),self.left-ink.left(),y-ink.top(),26,ink)
            y += ink.height()+4
        self.records['guide']['sha256'] = sc.pe.hash_text(text)
        return y

    def compose(self, title, guide, heads, groups, pages):
        destinations = {line.subject:folio for folio, sheet in enumerate(pages,1)
                        for line,top in sheet if line.heading}
        self.new_page('title','Title page')
        self.label('title',title,58,323)
        self.new_page('blank','Blank')
        # An uninterrupted subject list on a facing spread, read left page first.
        start = 0
        side = 0
        guide_step = 25
        guide_top = 118
        full_capacity = 1 + int((BODY_BOTTOM-guide_top-guide_step)//guide_step)
        while start < len(heads):
            self.new_page('contents',f'Subject guide {side+1}')
            self.label(f'nav/contents-{side+1}',self.contents_heading,46,84)
            header_rule(self,99)
            y = guide_top
            if side == 0:
                self.source += '\n'
                y = self.guide_paragraph(guide,y) + 12
            capacity = 1 + int((BODY_BOTTOM-y-guide_step)//guide_step)
            remaining = len(heads)-start
            pages_left = 1 + ceil(max(0,remaining-capacity)/full_capacity)
            spare = capacity + (pages_left-1)*full_capacity - remaining
            stop = min(len(heads), start+capacity-spare//pages_left)
            for index in range(start,stop):
                key = f'section-{index+1}'
                self.label('nav/toc/'+key,heads[index],27,y+14,at=12,width=sc.MEASURE-62,align='left')
                self.label('nav/folio/'+key,sc.digits(destinations[index+1]),25,y+14,
                           at=sc.MEASURE-48,width=36,align='right')
                y += guide_step
            start = stop
            side += 1
        self.start_body = len(self.state['pages']) + 2
        tops = {}
        for folio, sheet in enumerate(pages,1):
            first = sheet[0][0].subject
            self.new_page('opening' if any(line.heading for line,_ in sheet) else 'body',groups[first-1][0])
            assert self.page['folio']==folio
            self.label(f'nav/running-title/{folio}',title,20,74,align='left')
            self.label(f'nav/running-subject/{folio}',heads[first-1],22,74,align='right')
            assert self.page['lines'][0]['bounds'][0]+self.page['lines'][0]['bounds'][2]+10 < self.page['lines'][1]['bounds'][0]
            header_rule(self,88)
            for position, (line, top) in enumerate(sheet):
                if line.heading:
                    name = groups[line.subject-1][0]
                    self.edition['sections'].append(dict(name=name,number=line.subject,pageId=self.pid))
                    tops[name] = top
                if position==0 or line.start==0:
                    self.source += '\n'
                start = len(self.source)
                self.source += line.raw[line.start:line.end]
                offset = start-line.start
                self.fragment(line.key,line.raw,start,len(self.source))
                for a,b,size,x,y,ink in line.runs:
                    self.place(offset+a,offset+b,self.left+x,top+y-line.top,size,ink)
        self.finish_page()
        self.state['activeFrameId'] = self.state['pages'][0]['frames'][0]['frameId']
        return tops, destinations


def verify(state, title, guide, expected, groups, folios):
    sc.pe.validate(state)
    edition = state['printEdition']
    source = {p['pageId']:sc.pe.text_of(p) for p in state['pages']}
    strings = {r['id']:''.join(source[f['pageId']][f['start']:f['end']] for f in r['fragments'])
               for r in edition['verses']}
    assert strings['title']==title and strings['guide']==guide
    assert {k:v for k,v in strings.items() if k in expected} == expected
    assert [k for k in strings if k in expected] == list(expected)
    sections = edition['sections']
    assert [s['name'] for s in sections] == [name for name,_ in groups]
    expected_pages = []
    page_numbers = {p['pageId']:n for n,p in enumerate(state['pages'],1)}
    for s in sections:
        folio = edition['pages'][s['pageId']]['folio']
        assert folio == folios[s['number']]
        assert strings[f"nav/folio/section-{s['number']}"] == sc.digits(folio)
        expected_pages.append(page_numbers[s['pageId']])
    links = sc.pe.contents_links(state)
    assert [link['page'] for pid in source for link in links.get(pid,[])] == expected_pages
    by_key = {r['id']:r['fragments'] for r in edition['verses']}
    return {str(edition['pages'][f['pageId']]['folio']) for key,val in expected.items()
            if GRIEF in val for f in by_key[key] if GRIEF in source[f['pageId']][f['start']:f['end']]}


def build():
    app = QApplication.instance() or QApplication([])
    receipt, language, title, guide, heads, groups, expected = source_material()
    volume = IdiomVolume(language,receipt)
    pages = paginate(list(body_lines(volume.proof,heads,groups)))
    tops, folios = volume.compose(title,guide,heads,groups,pages)
    print(f'Set {len(pages)} body pages and {len(folios)} subject openings',flush=True)
    STAGE.mkdir(parents=True,exist_ok=True)
    with TemporaryDirectory(dir=STAGE) as work:
        work = Path(work)
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
            assert saved==before and session.saved_page_mode=='two'
            grief = verify(saved,title,guide,expected,groups,folios)
        finally:
            session.finish()
        physical = render_duplex(saved,work/PDF,TITLE,use_printed_folios=True,section_tops=tops)
        assert sha(FOLDER/(PROGRESSIVE+'.vay'))==receipt['sha256']
        report = dict(title=TITLE,sourceSha256=receipt['sha256'],nativeSha256=sha(work/NATIVE),
                      pdfSha256=sha(work/PDF),nativePages=len(saved['pages']),physicalPages=physical,
                      duplexSheets=(physical+1)//2,bindingBlank=1,bodyFolios=len(pages),
                      idioms=receipt['idioms'],examples=receipt['examples'],
                      subjectGuide=[dict(name=name,folio=folios[i]) for i,(name,_) in enumerate(groups,1)],
                      nativeReopenIdentical=True,sourceRowsVerified=len(expected)+2,
                      linkedSubjectDestinationsVerified=len(folios),pdfTextAndGeometryVerified=True,
                      ultimateGrief=dict(reading='stēv',nativeLetters=4,
                                         occurrences=sum(v.count(GRIEF) for v in expected.values()),
                                         folios=sorted(map(int,grief))))
        sc.write(work/MANIFEST,report)
        DEST.mkdir(parents=True,exist_ok=True)
        prior = sc.read(DEST/MANIFEST) if (DEST/MANIFEST).exists() else {}
        for name,key in ((NATIVE,'nativeSha256'),(PDF,'pdfSha256')):
            if (DEST/name).exists() and sha(DEST/name)!=prior.get(key):
                raise ValueError('Preserve independent edits in '+str(DEST/name))
        for name in (NATIVE,PDF,MANIFEST):
            (work/name).replace(DEST/name)
        print(json.dumps({k:v for k,v in report.items() if k!='subjectGuide'},ensure_ascii=True),flush=True)


if __name__=='__main__':
    build()
