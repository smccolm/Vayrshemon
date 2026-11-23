"""Locate passages and individual native brackets in Dampier's saved editions."""
import json
from collections import Counter
from hashlib import sha256
from pathlib import Path
import re

from tools import shakespeare_collected as sc


# Reference forms rendered separately for "[" and "]" at the edition's body
# size with its saved punctuation font and VectorPrint. The page must actually
# paint these forms as well as give the right ActualText.
BRACKET_FORMS = {
    "fbba615f51bc3ec10b45f672c7ddaf1a2c6d76b43b653fd44de61e58244ec887": "[",
    "824b4215df69baad62257c141bd144d5b8ff635f65702da0cfa3827a35bff89f": "]",
}


def _json(value):
    if isinstance(value, dict):
        return value
    return json.loads(Path(value).read_text(encoding="utf-8-sig"))


def load_locations(ledger, progressive_index, print_path):
    """Map live passage IDs to one-based native, folio and duplex PDF pages.

    The first two arguments may be paths or loaded JSON objects. Native text
    ranges are zero-based, half-open offsets into each ledger passage. The
    title is an image and consequently has no native text fragments.
    """
    units = _json(ledger)["units"]
    spreads = _json(progressive_index)["spreads"]
    progressive = {}
    for spread in spreads:
        pair = [spread["leftPage"], spread["rightPage"]]
        for uid in spread["unitIds"]:
            if uid in progressive:
                raise ValueError(f"Repeated progressive passage {uid}")
            progressive[uid] = pair
    if list(progressive) != [unit["id"] for unit in units]:
        raise ValueError("Progressive page index and ledger have different passages or order")

    state = sc.unpack(sc.read(Path(print_path)))["state"]
    pages = state["pages"]
    edition = state["printEdition"]
    page_numbers = {page["pageId"]: n for n, page in enumerate(pages, 1)}
    page_texts = {page["pageId"]: sc.pe.text_of(page) for page in pages}
    folios = {n: edition["pages"][pid]["folio"] for pid, n in page_numbers.items()}
    if any(folio != (n - 4 if n > 4 else None) for n, folio in folios.items()):
        raise ValueError("Unexpected Dampier print folio offset")

    def numbers(native_pages):
        native = list(dict.fromkeys(native_pages))
        return {"printNative": native, "printFolios": [folios[n] for n in native],
                "pdfPhysical": [n + 1 for n in native]}

    title = units[0]["id"]
    first_page = pages[0]["pageId"]
    if page_texts[first_page] or not edition["pages"][first_page].get("images"):
        raise ValueError("Missing title artwork on print native page 1")
    result = {title: {"progressive": progressive[title], **numbers([1]),
                      "artwork": True, "brackets": [], "fragments": []}}
    records = [r for r in edition["verses"] if not r["id"].startswith("nav/")]
    if [r["id"] for r in records] != [u["id"] for u in units[1:]]:
        raise ValueError("Print records and the progressive ledger have different passages or order")
    for record, unit in zip(records, units[1:]):
        uid, original = unit["id"], unit["text"]
        offset = 0
        fragments = []
        for fragment in record["fragments"]:
            pid, a, b = fragment["pageId"], fragment["start"], fragment["end"]
            if not 0 <= a <= b <= len(page_texts[pid]):
                raise ValueError(f"Invalid fragment bounds in {uid} on {pid}")
            end = offset + b - a
            if original[offset:end] != page_texts[pid][a:b]:
                raise ValueError(f"Print text differs from {uid} at {offset} on {pid}")
            if end > offset:
                fragments.append({"range": [offset, end], "native": page_numbers[pid], "pageRange": [a, b]})
            offset = end
        if offset != len(original) or not fragments:
            raise ValueError(f"Partial or empty printed passage {uid}")
        brackets = []
        for i, match in enumerate(re.finditer(r"\[[^\[\]]+\]", original), 1):
            a, b = match.span()
            covered = [f["native"] for f in fragments if f["range"][0] < b and a < f["range"][1]]
            brackets.append({"ordinal": i, "range": [a, b], **numbers(covered),
                             "openingNative": covered[0], "closingNative": covered[-1]})
        if len(brackets) != original.count("[") or len(brackets) != original.count("]"):
            raise ValueError(f"Unpaired, empty or nested native bracket in {uid}")
        result[uid] = {"progressive": progressive[uid], **numbers(f["native"] for f in fragments),
                       "artwork": False, "brackets": brackets, "fragments": fragments}
    return result


def verify_pdf_brackets(locations, pdf_path):
    """Check logical brackets and the vector outlines painted on each physical PDF page."""
    from pypdf import PdfReader

    expected = Counter()
    for unit in locations.values():
        for bracket in unit["brackets"]:
            expected[bracket["openingNative"] + 1, "["] += 1
            expected[bracket["closingNative"] + 1, "]"] += 1
    reader = PdfReader(pdf_path)
    if len(reader.pages) != max(n for u in locations.values() for n in u["pdfPhysical"]):
        raise ValueError("Duplex PDF has different pagination from the print manuscript")
    observed = Counter()
    painted = Counter()
    form_marks = {}
    for n, page in enumerate(reader.pages, 1):
        contents = page.get_contents()
        if contents is None:
            continue
        payload = contents.get_data()
        # The PDF paints vector glyphs; logical text is stored on marked-content spans.
        for literal in re.findall(rb"/ActualText\s+<FEFF([\da-fA-F]+)>", payload):
            text = bytes.fromhex(literal.decode("ascii")).decode("utf-16-be")
            for mark in "[]":
                if mark in text:
                    observed[n, mark] += text.count(mark)
        resources = page["/Resources"].get("/XObject", {})
        for name, calls in Counter(re.findall(rb"(/FormXob\.g\d+) Do\b", payload)).items():
            form = resources.raw_get(name.decode("ascii"))
            key = (form.idnum, form.generation)
            if key not in form_marks:
                digest = sha256(form.get_object().get_data()).hexdigest()
                form_marks[key] = BRACKET_FORMS.get(digest)
            mark = form_marks[key]
            if mark:
                painted[n, mark] += calls
    if observed != expected:
        raise ValueError(f"PDF bracket mismatch, missing {expected - observed}, extra {observed - expected}")
    if painted != expected:
        raise ValueError(f"PDF bracket outline mismatch, missing {expected - painted}, extra {painted - expected}")
    return dict(sorted(observed.items()))
