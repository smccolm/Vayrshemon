"""Set the complete issued anthology as a continuous, one-column Letter book."""
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
import re
import shutil
import statistics

from PySide6.QtWidgets import QApplication
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ArrayObject, FloatObject, NameObject, NullObject

from tools import shakespeare_collected as sc
from tools.compose_historical_book import texts
from tools.idiom_print import IdiomVolume
from tools.poetic_anthology import BOOK, ROOT, TARGET, TITLE, WORK
from tools.shakespeare_collected_pdf import render_duplex


DEST = ROOT / "Saves/Poetic Anthology - Letter Print Edition"
STAGE = ROOT / ".local/poetic-anthology-print"
NATIVE = TITLE + ".vay"
PDF = TITLE + " - Duplex Print.pdf"
NOTICE = "Song license.txt"
MANIFEST = "edition-manifest.json"
TOP = sc.TOP + 1
BOTTOM = 792 - sc.BOTTOM - 1
WIDTH = sc.MEASURE
HANG = 12


def material():
    receipt = sc.read(WORK / "publication-check.json")
    assert sc.digest(TARGET) == receipt["nativeSha256"]
    state = sc.unpack(sc.read(TARGET))["state"]
    ledger = sc.read(WORK / "ledger.json")["units"]
    units = {u["id"]: u["text"] for u in ledger}
    works = sc.read(WORK / "works.json")
    index = sc.read(WORK / "page-index.json")["spreads"]
    ids = []
    for spread in index:
        page = state["pages"][spread["leftPage"]-1]
        frame = min(page["frames"], key=lambda f: int(f["x"]))
        assert texts(frame) == [units[k] for k in spread["unitIds"]]
        ids.extend(spread["unitIds"])
    assert ids == list(units)
    assert [w["sort"] for w in works] == sorted(w["sort"] for w in works)
    groups = {w["id"]: [] for w in works}
    for u in ledger:
        if "lines" in u:
            groups[u["id"].split(".")[0]].append(u["id"])
    assert all(groups.values())
    return receipt, state["language"], units, works, groups


@dataclass
class Run:
    key: str
    raw: str
    a: int
    b: int
    end: int
    pt: int
    x: float
    box: object


@dataclass
class Row:
    runs: list
    role: str
    work: str = ""

    @property
    def top(self):
        return min(r.box.top() for r in self.runs)

    @property
    def bottom(self):
        return max(r.box.bottom() for r in self.runs)


class AnthologyVolume(IdiomVolume):
    def new_page(self, kind, name):
        super().new_page(kind, name)
        # Native pages and physical Letter pages have the same folio parity.
        n = len(self.state["pages"]) + 1
        self.page["side"] = "center" if n == 1 else "right" if n % 2 else "left"
        self.left = (sc.INNER + sc.OUTER)/2 if n == 1 else sc.INNER if n % 2 else sc.OUTER

    def run(self, key, raw, a, b, end, pt, x=0):
        return Run(key, raw, a, b, end, pt, x, self.proof.ink(raw[a:b], pt))

    def wrapped(self, key, text, pt, width, indent=0):
        """Preserve the witness's line separators and spaces in the native record."""
        for hard in re.finditer(r"[^\u2028]+(?:\u2028|$)", text):
            words = list(re.finditer(r"\S+", hard.group()))
            i = 0
            while i < len(words):
                inset = indent if i else 0
                a = hard.start() + words[i].start()
                j = i + 1
                while j < len(words):
                    end = hard.start()+words[j].end()
                    if self.proof.ink(text[a:end],pt).width() > width-inset:
                        break
                    j += 1
                b = hard.start() + words[j-1].end()
                end = hard.start()+words[j].start() if j < len(words) else hard.end()
                run = self.run(key,text,a,b,end,pt,inset)
                assert run.box.width() <= width-inset, (key,text[a:b])
                yield run
                i = j

    def heading(self, key, title, date, width, *, toc=False):
        pt, small = (25,19) if toc else (33,22)
        tk = "nav/toc/"+key if toc else key+".title"
        dk = "nav/date/"+key if toc else key+".date"
        runs = list(self.wrapped(tk,title,pt,width))
        dr = self.run(dk,date,0,len(date),len(date),small)
        space = 8 if toc else 10
        tail = runs.pop()
        available = width - space - dr.box.width()
        # Start a long heading earlier on a second line so its complete date
        # can still sit beside its final words on the same baseline.
        if tail.box.width() > available:
            candidates = []
            for match in re.finditer(" ", title[tail.a:tail.b]):
                p = tail.a + match.start()
                l = self.run(tk,title,tail.a,p,p+1,pt)
                r = self.run(tk,title,p+1,tail.b,tail.end,pt)
                if r.box.width() <= available:
                    candidates.append((abs(l.box.width()-(r.box.width()+space+dr.box.width())), l, r))
            if candidates:
                _, first, tail = min(candidates, key=lambda item:item[0])
                runs.append(first)
        rows = [Row([run],"heading",key) for run in runs]
        if tail.box.width() > available:
            # Dates with long historical qualifiers can wrap after their first
            # words. Keep those words beside the title wherever they fit.
            x = tail.box.width()+space
            first = next((m.end() for m in reversed(list(re.finditer(r"\S+",date)))
                          if self.proof.ink(date[:m.end()],small).width() <= width-x),0)
            if first:
                rows.append(Row([tail,self.run(dk,date,0,first,first+1,small,x)],"heading",key))
                follow = self.run(dk,date,first+1,len(date),len(date),small)
                assert follow.box.width() <= width
                rows.append(Row([follow],"heading",key))
            else:
                rows.extend([Row([tail],"heading",key),Row([dr],"heading",key)])
        else:
            dr.x = tail.box.width()+space
            rows.append(Row([tail,dr],"heading",key))
        if not toc:
            for row in rows:
                line_width = max(run.x+run.box.width() for run in row.runs)
                inset = (width-line_width)/2
                for run in row.runs:
                    run.x += inset
        return rows

    def paint_row(self, row, baseline):
        for column,run in enumerate(row.runs):
            if self.source and not self.source[-1].isspace():
                self.source += " " if column else "\n"
            start = len(self.source)
            self.source += run.raw[run.a:run.end]
            self.fragment(run.key,run.raw,start,len(self.source))
            self.place(start,start+run.b-run.a,self.left+run.x-run.box.left(),baseline,run.pt,run.box)

    def body(self, units, works, groups):
        rows = []
        for w in works:
            k = w["id"]
            head = self.heading(k,units[k+".title"],units[k+".date"],WIDTH)
            head[0].role = "opening"
            rows.extend(head)
            for key in groups[k]:
                for i,run in enumerate(self.wrapped(key,units[key],sc.BODY,WIDTH,HANG)):
                    rows.append(Row([run],"unit" if i==0 else "verse",k))
        return rows

    @staticmethod
    def baseline(row, previous):
        if previous is None:
            return TOP-row.top
        before, y = previous
        foot = y+before.bottom
        if row.role == "opening":
            return foot+7-row.top
        if row.role == "heading":
            return foot+1.8-row.top
        if before.role in ("opening","heading"):
            return foot+2.7-row.top
        leading = 17.8+(.9 if row.role=="unit" else 0)
        return max(y+leading,foot+1.4-row.top)

    def paginate(self, rows):
        pages, page = [], []
        for i,row in enumerate(rows):
            y = self.baseline(row,page[-1] if page else None)
            fit = (row,y)
            if row.role == "opening":
                j = i+1
                while rows[j].role == "heading":
                    fit = (rows[j],self.baseline(rows[j],fit))
                    j += 1
                fit = (rows[j],self.baseline(rows[j],fit))
            if fit[1]+fit[0].bottom > BOTTOM:
                assert page and row.role!="heading"
                pages.append(page)
                page = []
                y = self.baseline(row,None)
            page.append((row,y))
        if page:
            pages.append(page)
        return pages

    def contents(self, units, works, folios):
        entries = []
        for w in works:
            k = w["id"]
            rows = self.heading(k,units[k+".title"],units[k+".date"],WIDTH-44,toc=True)
            value = sc.digits(folios[k])
            run = self.run("nav/folio/"+k,value,0,len(value),len(value),23)
            run.x = WIDTH-run.box.width()
            rows[-1].runs.append(run)
            # All rows have a common baseline; allow the tallest glyphs to grow the slot.
            heights = [max(16.5,r.bottom-r.top+1.5) for r in rows]
            entries.append((rows,heights))
        start_y, entry_gap = 78, .5
        full = BOTTOM-start_y
        lengths = [sum(h)+entry_gap for _,h in entries]
        # Balance actual typeset heights. Otherwise the last contents page may
        # carry only one or two titles even though all preceding pages are full.
        def cut_count(limit, start):
            total = 0
            stop = start
            while stop < len(entries) and total+lengths[stop] <= limit:
                total += lengths[stop]
                stop += 1
            return stop
        starts, index = [], 0
        while index < len(entries):
            starts.append(index)
            index = cut_count(full,index)
            assert index>starts[-1]
        index = 0
        for number in range(len(starts)):
            self.new_page("contents",f"Contents {number+1}")
            key = "contents.title" if number==0 else f"nav/contents/{number+1}"
            self.label(key,units["contents.title"],30,66,align="left")
            y = start_y
            capacity = BOTTOM-y
            remaining = len(starts)-number
            spare = capacity+(remaining-1)*full-sum(lengths[index:])
            stop = cut_count(min(capacity,capacity-spare/remaining+min(lengths)/2),index)
            # Leave only as many rows as can actually be packed on later pages.
            while stop < len(entries):
                end = stop
                for _ in range(remaining-1):
                    end = cut_count(full,end)
                if end == len(entries):
                    break
                assert stop < cut_count(capacity,index)
                stop += 1
            for lines,heights in entries[index:stop]:
                for row,height in zip(lines,heights,strict=True):
                    self.paint_row(row,y-row.top)
                    y += height
                y += entry_gap
            assert y <= BOTTOM+0.01
            index = stop
        assert index==len(entries)
        return len(starts)

    def compose_book(self, units, works, groups):
        pages = self.paginate(self.body(units,works,groups))
        folios = {row.work:i for i,page in enumerate(pages,1) for row,_ in page if row.role=="opening"}
        assert list(folios)==list(groups)
        self.new_page("title","Title page")
        self.label("front.title",units["front.title"],66,341)
        self.label("front.subtitle",units["front.subtitle"],29,379)
        contents_pages = self.contents(units,works,folios)
        front = 1+contents_pages
        self.start_body = front+1
        tops, sections = {}, {}
        names = Counter(w["title"] for w in works)
        by_id = {w["id"]:w for w in works}
        for i,page in enumerate(pages,1):
            heads = [r for r,y in page if r.role=="opening"]
            self.new_page("opening" if heads else "body",f"Folio {i}")
            assert self.page["folio"]==i
            for row,y in page:
                if row.role=="opening":
                    w = by_id[row.work]
                    name = w["title"]
                    if names[name]>1:
                        name += " ("+w["genre"].split(" · ")[0]+")"
                    tops[name] = row.top+y
                    sections[row.work] = dict(name=name,folio=i,physicalPage=front+i,topPt=row.top+y)
                    self.edition["sections"].append(dict(name=name,number=len(sections),pageId=self.pid))
                self.paint_row(row,y)
        self.finish_page()
        self.state["activeFrameId"] = self.state["pages"][0]["frames"][0]["frameId"]
        space = [BOTTOM-page[-1][1]-page[-1][0].bottom for page in pages[:-1]]
        inline = sum(any(r.key==k+".title" for r in row.runs) and any(r.key==k+".date" for r in row.runs)
                     for page in pages for row,_ in page for k in [row.work])
        stats = dict(titlePages=1,contentsPages=contents_pages,bodyPages=len(pages),works=len(works),
                     openingsBelowPreviousWork=sum(r.role=="opening" for page in pages for r,y in page[1:]),
                     datesBesideTitles=inline,medianUnusedBodyFootPt=round(statistics.median(space),2),
                     maximumUnusedBodyFootPt=round(max(space),2))
        return sections,tops,stats


def check_native(state, units, works, groups, sections):
    sc.pe.validate(state)
    pages = {p["pageId"]:sc.pe.text_of(p) for p in state["pages"]}
    edition = state["printEdition"]
    records = {r["id"]:"".join(pages[f["pageId"]][f["start"]:f["end"]] for f in r["fragments"])
               for r in edition["verses"]}
    wanted = ["front.title","front.subtitle","contents.title"]
    for w in works:
        k = w["id"]
        wanted.extend([k+".title",k+".date",*groups[k]])
        assert records["nav/toc/"+k]==units[k+".title"]
        assert records["nav/date/"+k]==units[k+".date"]
        assert records["nav/folio/"+k]==sc.digits(sections[k]["folio"])
    wanted_set = set(wanted)
    assert [k for k in records if k in wanted_set]==wanted
    assert all(records[k]==units[k] for k in wanted)
    links = sc.pe.contents_links(state)
    assert [l["page"] for p in pages for l in links.get(p,[])]==[s["physicalPage"] for s in sections.values()]
    return len(wanted)


def check_heading_positions(state, works, sections):
    """Measure each saved title/date line against its own page's text column."""
    pages = state["pages"]
    edition = state["printEdition"]
    fragments = {r["id"]:r["fragments"] for r in edition["verses"]}
    title_id = pages[0]["pageId"]
    title_page = edition["pages"][title_id]
    assert title_page["kind"]=="title" and title_page["folio"] is None
    assert sc.pe.text_of(pages[0])=="\n".join(
        sc.pe.text_of(pages[0])[span["start"]:span["end"]]
        for key in ("front.title","front.subtitle") for span in fragments[key] if span["pageId"]==title_id)
    assert len(title_page["lines"])==2
    for line in title_page["lines"]:
        x,_,width,_ = line["bounds"]
        assert abs(x+width/2-306)<.001

    count, max_error = 0, 0.
    for w in works:
        k = w["id"]
        pg = pages[sections[k]["physicalPage"]-1]
        pid = pg["pageId"]
        center = int(pg["margins"]["left"])/1e6 + WIDTH/2
        by_baseline = {}
        for key in (k+".title",k+".date"):
            for span in fragments[key]:
                assert span["pageId"]==pid
                parts = [line for line in edition["pages"][pid]["lines"]
                         if span["start"]<=line["start"] and line["end"]<=span["end"]]
                assert parts, key
                for line in parts:
                    x,_,width,_ = line["bounds"]
                    by_baseline.setdefault(line["baseline"],[]).append((x,x+width))
        for boxes in by_baseline.values():
            middle = (min(a for a,b in boxes)+max(b for a,b in boxes))/2
            error = abs(middle-center)
            assert error<.001,(k,error)
            max_error = max(max_error,error)
            count += 1
    return dict(centeredWorkHeadings=len(works),centeredHeadingLines=count,
                maxHeadingCenterErrorPt=round(max_error,6))


def finish_pdf(saved, staged, sections):
    """Embed the edition's credits and target the individual headings on shared pages."""
    before = PdfReader(staged)
    out = staged.with_suffix(".final.pdf")
    writer = PdfWriter(clone_from=before)
    writer.add_attachment(NOTICE,(BOOK/NOTICE).read_bytes())
    targets = iter(sections.values())
    for page in writer.pages:
        for ref in page.get("/Annots",[]):
            link = ref.get_object()
            target = next(targets)
            dest = writer.pages[target["physicalPage"]-1].indirect_reference
            link[NameObject("/Dest")] = ArrayObject([dest,NameObject("/XYZ"),NullObject(),
                                                     FloatObject(792-target["topPt"]+4),NullObject()])
    assert next(targets,None) is None
    writer.write(out)
    writer.close()
    with PdfReader(out) as final:
        assert list(final.attachments[NOTICE])==[(BOOK/NOTICE).read_bytes()]
        assert len(final.pages)==len(saved["pages"]) and final.page_labels==before.page_labels
        expected = iter(sections.values())
        for i,page in enumerate(final.pages):
            assert page.get_contents().get_data()==before.pages[i].get_contents().get_data()
            for ref in page.get("/Annots",[]):
                target=next(expected)
                dest=ref.get_object()["/Dest"]
                assert dest[0]==final.pages[target["physicalPage"]-1].indirect_reference
                assert dest[1]=="/XYZ" and abs(float(dest[3])-(792-target["topPt"]+4))<.001
        assert next(expected,None) is None
        for b,a in zip(before.outline,final.outline,strict=True):
            assert b.title==a.title and before.get_destination_page_number(b)==final.get_destination_page_number(a)
            assert b.top==a.top
    before.close()
    out.replace(staged)


def build(document_id="document.poetic-anthology.letter", target_pages=None):
    app = QApplication.instance() or QApplication([])
    receipt, language, units, works, groups = material()
    volume = AnthologyVolume(language,{"sha256":receipt["nativeSha256"]},title=TITLE,
                             document_id=document_id,ledger_sha=sc.digest(WORK/"ledger.json"))
    sections,tops,stats = volume.compose_book(units,works,groups)
    if target_pages is not None:
        assert stats["titlePages"] + stats["contentsPages"] + stats["bodyPages"] == target_pages, stats
    print(stats,flush=True)
    STAGE.mkdir(parents=True,exist_ok=True)
    with TemporaryDirectory(dir=STAGE) as temp:
        tmp = Path(temp)
        session = sc.FileSession(ROOT,source_fonts=False,recovery=False)
        session.remember = lambda *a,**kw: None
        session.log.emit = lambda *a,**kw: None
        try:
            for f in volume.state["fontSources"]:
                session.fonts.register(session.fonts.document_path(f["path"],f["sha256"]),f["sha256"])
            session._restore(volume.state,take_ownership=True)
            session._state = volume.state
            session.save(tmp/NATIVE,preview_mode="two")
            before = session.capture()
            session.open(tmp/NATIVE,advance_revision=False)
            saved = session.capture()
            assert saved == before and session.saved_page_mode=="two"
            records = check_native(saved,units,works,groups,sections)
            alignment = check_heading_positions(saved,works,sections)
        finally:
            session.finish()
        count = render_duplex(saved,tmp/PDF,TITLE,use_printed_folios=True,section_tops=tops,binding_blank=False)
        if target_pages is not None:
            assert count == target_pages
        finish_pdf(saved,tmp/PDF,sections)
        shutil.copyfile(BOOK/NOTICE,tmp/NOTICE)
        assert sc.digest(TARGET)==receipt["nativeSha256"]
        report = dict(title=TITLE,sourceSha256=receipt["nativeSha256"],nativeSha256=sc.digest(tmp/NATIVE),
                      pdfSha256=sc.digest(tmp/PDF),noticeSha256=sc.digest(tmp/NOTICE),physicalPages=count,
                      sourceUnitsChecked=records,sourceLines=receipt["sourceLines"],nativeReopenIdentical=True,
                      pdfTextAndGeometryVerified=True,linkedTitles=len(sections),embeddedSourceNotices=True,
                      **stats,**alignment,sections=sections)
        report.update(duplexSheets=(count+1)//2,extraBindingBlank=False)
        sc.write(tmp/MANIFEST,report)
        DEST.mkdir(parents=True,exist_ok=True)
        old = sc.read(DEST/MANIFEST) if (DEST/MANIFEST).exists() else {}
        for name,field in [(NATIVE,"nativeSha256"),(PDF,"pdfSha256"),(NOTICE,"noticeSha256")]:
            if (DEST/name).exists() and sc.digest(DEST/name)!=old.get(field):
                raise ValueError("Preserve independent edits in "+str(DEST/name))
        for name in (NATIVE,PDF,NOTICE,MANIFEST):
            (tmp/name).replace(DEST/name)
    print(f"Published {count} pages and {len(sections)} linked works.",flush=True)


if __name__=="__main__":
    build()
