"""Verify the Dampier print release against its current source ledger and saved files."""
import argparse
from base64 import b64decode
from collections import defaultdict
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path

from PIL import Image
from pypdf import PdfReader

from tools.dampier_completion_audit import BOOK, ROOT, WORK, check, read, sha, source_report
from tools.dampier_concordance_pages import load_locations, verify_pdf_brackets
from tools import shakespeare_collected as sc

TITLE = "A New Voyage Round the World"
PRINT = BOOK.parent / (TITLE + " - Letter Print Edition")
ARCHIVE = BOOK.parent / "Archive/Previous editions/Before Dampier final sentence revisions"
ART = ROOT / "Inputs/Print artwork/A New Voyage Round the World - Title Page - Approved.png"


def checked_inputs(pin):
    path = WORK / "ledger.json"
    ledger = read(path)
    status = read(WORK / "translation-status.json")
    check(pin == status["publicationSha256"] == read(WORK / "layout-validation.json")["sha256"]
          == sha(BOOK / (BOOK.name + ".vay")), "Progressive publication hash")
    source = source_report(ledger)
    notes = read(WORK / "source-treatments.json")
    check(status["alignedPassages"] == len(ledger["units"]) and status["translatedWords"] == source["directSourceWords"]
          and status["sourceWordsInSummaryPassages"] == source["sourceWordsInEditorialSummaries"]
          and status["wordsAccountedFor"] == status["suppliedWords"] == source["words"], "Progressive accounting")
    return ledger, source, notes, sha(path)


def previous_units():
    before = ARCHIVE / BOOK.name / "Working"
    index = read(ARCHIVE / "restoration-index.json")["files"]
    for path in [before / "ledger.json", before / "source-treatments.json"]:
        check(sha(path) == index[path.relative_to(ARCHIVE).as_posix()], "Archived reading checksum")
    notes = read(before / "source-treatments.json")
    return [(unit, notes[unit["id"]]) for unit in read(before / "ledger.json")["units"] if unit["id"] in notes]


def affected_pages(ledger, locations, archived):
    """Find current physical samples by original TXT coordinates even if layout units split."""
    by_line = defaultdict(list)
    for unit in ledger["units"]:
        by_line[unit["sourceLine"]].append(unit)
    pages = defaultdict(list)
    for old, _ in archived:
        a, b = old["sourceOffsets"]
        overlapping = [u for u in by_line[old["sourceLine"]] if u["sourceOffsets"][0] < b and a < u["sourceOffsets"][1]]
        check(overlapping, "Missing source range formerly at " + old["id"])
        for n in sorted({n for u in overlapping for n in locations[u["id"]]["printNative"]}):
            pages[n].append(old["id"])
    return dict(sorted(pages.items()))


def review_intervals(archived, ledger, notes):
    old_ranges = defaultdict(list)
    for unit, note in archived:
        offset = unit["sourceOffsets"][0]
        for ordinal, span in enumerate(note["spans"], 1):
            old_ranges[unit["sourceLine"]].append((unit["id"], ordinal, offset + span["start"], offset + span["end"]))
    revised = defaultdict(list)
    for unit in ledger["units"]:
        if unit["id"] not in notes:
            continue
        offset = unit["sourceOffsets"][0]
        for ordinal, span in enumerate(notes[unit["id"]]["spans"], 1):
            a, b = offset + span["start"], offset + span["end"]
            enclosing = [r for r in old_ranges[unit["sourceLine"]] if r[2] <= a < b <= r[3]]
            check(len(enclosing) == 1, "Editorial change outside the preceding edition's scope " + unit["id"])
            revised[enclosing[0]].append((unit["id"], ordinal, a, b))
    results = defaultdict(int)
    for ranges in old_ranges.values():
        for key in ranges:
            parts = revised[key]
            if not parts:
                results["fullyRestored"] += 1
            elif len(parts) == 1 and parts[0][2:] == key[2:]:
                results["sameExtent"] += 1
            else:
                results["narrowed"] += 1
    return {k: results[k] for k in ("fullyRestored", "narrowed", "sameExtent")}


def check_print(pin, directory):
    ledger, source, notes, ledger_hash = checked_inputs(pin)
    directory = Path(directory)
    native = directory / (TITLE + ".vay")
    pdf = directory / (TITLE + " - Duplex Print.pdf")
    manifest = read(directory / "edition-manifest.json")
    proof = read(directory / "proof-validation.json")
    ids = source["editorialSummaryPassages"]
    span_count = sum(len(notes[uid]["spans"]) for uid in ids)
    expected = {
        "title": TITLE, "author": "William Dampier", "sourceProgressiveSha256": pin,
        "ledgerSha256": ledger_hash, "englishSourceSha256": source["sourceSha256"],
        "sourceUnits": len(ledger["units"]), "otherNativeUnitsExact": len(ledger["units"]) - 1,
        "suppliedWords": source["words"], "accountedSourceWords": source["words"],
        "translatedWords": source["directSourceWords"], "sourceWordsInSummaryPassages": source["sourceWordsInEditorialSummaries"],
        "editorialSummarySpans": span_count, "editorialSummaryUnits": ids, "pendingUnitPrintedFolios": {},
        "titleUnitsInArtwork": 1, "leadingBindingBlanks": 1, "saveReopenIdentical": True,
    }
    for key, value in expected.items():
        check(manifest[key] == value, "Print manifest " + key)
    for key, path in [("nativeSha256", native), ("pdfSha256", pdf)]:
        check(sha(path) == manifest[key] == proof[key], "Printed publication hash " + key)
    state = sc.unpack(sc.read(native))["state"]
    edition = state["printEdition"]
    pages = state["pages"]
    cover, = edition["pages"][pages[0]["pageId"]]["images"]
    image = b64decode(edition["assets"][cover["asset"]]["png"], validate=True)
    prior_manifest = ARCHIVE / PRINT.name / "edition-manifest.json"
    check(sha(prior_manifest) == read(ARCHIVE / "restoration-index.json")["files"][prior_manifest.relative_to(ARCHIVE).as_posix()],
          "Archived print manifest checksum")
    check(sha256(image).hexdigest() == manifest["titleArtwork"]["sha256"] == sha(ART) == cover["asset"]
          == read(prior_manifest)["titleArtwork"]["sha256"],
          "Print title differs from the approved original")
    pdf_reader = PdfReader(pdf)
    embedded_title, = pdf_reader.pages[1].images
    with Image.open(BytesIO(image)) as title:
        check(embedded_title.image.size == title.size and
              embedded_title.image.convert("RGB").tobytes() == title.convert("RGB").tobytes(), "PDF title pixels")
    pdf_reader.close()
    check(edition["sourceSha256"] == pin and edition["ledgerSha256"] == ledger_hash and
          manifest["nativePages"] == len(pages) and manifest["pdfPages"] == len(pages) + 1 and
          manifest["duplexSheets"] == (manifest["pdfPages"] + 1) // 2, "Print provenance or pagination")
    del state, edition, pages
    locations = load_locations(ledger, WORK / "page-index.json", native)
    rendered_brackets = verify_pdf_brackets(locations, pdf)
    per_id = {}
    for uid in ids:
        marked = locations[uid]["brackets"]
        check(len(marked) == len(notes[uid]["spans"]), "Printed editorial bracket count " + uid)
        per_id[uid] = [r["pdfPhysical"] for r in marked]
    archived = previous_units()
    return {
        "sourceProgressiveSha256": pin, "ledgerSha256": ledger_hash, "nativeSha256": manifest["nativeSha256"],
        "pdfSha256": manifest["pdfSha256"], "suppliedWords": source["words"], "directSourceWords": source["directSourceWords"],
        "wordsInEditorialSummaries": source["sourceWordsInEditorialSummaries"], "editorialSpans": span_count,
        "printedNativeUnitsCompared": manifest["otherNativeUnitsExact"], "nativePages": manifest["nativePages"],
        "physicalPDFPages": manifest["pdfPages"], "titlePlateSha256": sha(ART),
        "allPaintedBracketSigns": sum(rendered_brackets.values()), "editorialPhysicalPagesByBracket": per_id,
        "precedingEditionSpanComparison": review_intervals(archived, ledger, notes),
        "samplePrintNativePagesByFormerPassage": affected_pages(ledger, locations, archived),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("progressive_sha256")
    parser.add_argument("--directory", type=Path, default=PRINT)
    args = parser.parse_args()
    print(json.dumps(check_print(args.progressive_sha256, args.directory), ensure_ascii=False))
