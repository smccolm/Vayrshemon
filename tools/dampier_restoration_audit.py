"""Audit the Dampier passage restoration against the preceding edition and original TXT."""
import argparse
from collections import Counter
from hashlib import sha256
from itertools import zip_longest
import json
import os
from pathlib import Path
import re

from tools.dampier_completion_audit import (
    BOOK, EDITION, FONTS, PIN, ROOT, SOURCE, WORK, check, read, saved_pages, sha,
)

ARCHIVE = ROOT / "Saves/Archive/Previous editions/Before Dampier passage restoration"
SENTENCE_ARCHIVE = ARCHIVE.parent / "Before Dampier final sentence revisions"
SENTENCE_REVISION = {
    f"dampier.{number}" for number in (
        "0275.006", "0275.007", "0299.009", "0299.010", "0305.002",
        "0319.007", "0447.005", "0461.011", "0749.003", "0959.003",
        "1359.001", "1391.001", "1837.004", "2067.009", "2161.004",
    )
}
EXTRA = {
    "dampier.0681.003": ("8 · indian(pl.)", "7 · man(pl.) · with · canoe"),
    "dampier.0749.002": ("king · of · ship(pl.) · of · 3 · or · 4",),
    "dampier.0763.010": ("5 · or · 6 · man(pl.) · canoe",),
    "dampier.0763.011": ("Knight · of · this · bark · in · 40 · or · 50 · storage-jar(pl.) · of · brandy",),
}
SPLITS = {
    "dampier.0447.004": "among the English.",
    "dampier.0531.029": "a shot among them.",
    "dampier.0629.003": "at night on Horse-back.",
    "dampier.0647.018": "which is the narrowest.",
    "dampier.0739.002": "the Watch word we had agreed upon.",
    "dampier.0813.006": "this was only a stratagem of theirs;",
    "dampier.1415.008": "to go to Sea without a Surgeon:",
}
CONTEXT_CORRECTION = "dampier.0959.004"
FORMER_COUNT = 104
BOUNDARY = re.compile(r"[.!?]\s*\]?\s*$")
FIELDS = ("text", "text", "gloss", "source")


def text_hash(value):
    return sha256(value.encode("utf-8")).hexdigest()


def read_archive(archive=ARCHIVE):
    prior_dir = archive / EDITION
    old_work = prior_dir / "Working"
    files = read(archive / "restoration-index.json")["files"]
    paths = [old_work / "ledger.json", old_work / "source-treatments.json", prior_dir / (EDITION + ".vay"),
             old_work / "page-index.json"]
    for path in paths:
        check(sha(path) == files[path.relative_to(archive).as_posix()], "Archive checksum: " + str(path))
    return read(paths[0]), read(paths[1]), paths[2]


def index_by_source(units, lines):
    """Each nonblank TXT line must be covered in order at its original character offsets."""
    by_line = {}
    for u in units:
        line = u["sourceLine"]
        check(line not in by_line or next(reversed(by_line)) == line, f"Source order {u['id']}")
        by_line.setdefault(line, []).append(u)
    check(list(by_line) == [n for n, line in enumerate(lines, 1) if line.strip()], "Missing or reordered source line")
    for n, group in by_line.items():
        line, pos = lines[n - 1], 0
        for number, u in enumerate(group, 1):
            a, b = u["sourceOffsets"]
            uid = u["id"]
            check(uid == f"dampier.{n:04}.{number:03}" and pos == a < b <= len(line), "Source position " + uid)
            check(b == len(line) or line[b].isspace(), "Source boundary " + uid)
            check(bool(a) == u["continuesParagraph"], "Paragraph continuation " + uid)
            while b < len(line) and line[b].isspace():
                b += 1
            pos = b
        check(pos == len(line), f"Uncovered text on line {n}")
    return by_line


def bracket_contents(value, expected, uid):
    interiors = re.findall(r"\[([^\[\]]+)\]", value)
    check(value.count("[") == value.count("]") == len(interiors) == expected and
          all(re.search(r"\w", x) for x in interiors), "Bracket alignment " + uid)


def verify_reading(unit, original, note, marked):
    uid = unit["id"]
    count = 0
    if note is None:
        check(unit["source"] == original and not unit.get("sourceTreatment"), "Direct source " + uid)
        spans = []
    else:
        check(marked and unit["sourceTreatment"] == "editorial summary" and
              text_hash(original) == note["originalSha256"], "Restoration scope/hash " + uid)
        spans = note["spans"]
        check(bool(spans), "Whole-passage or empty note remains at " + uid)
        source = []
        end = 0
        for s in spans:
            a, b, replacement = s["start"], s["end"], s["replacement"]
            check(end <= a < b <= len(original) and (a == 0 or original[a-1].isspace()) and
                  (b == len(original) or original[b].isspace()) and not original[a].isspace()
                  and not original[b-1].isspace(), "Source edit is not a whole-word range: " + uid)
            check(re.fullmatch(r"\[[^\[\]]+\]", replacement), "Unmarked replacement " + uid)
            source.extend((original[end:a], replacement))
            end = b
            count += len(original[a:b].split())
        source.append(original[end:])
        check("".join(source) == unit["source"], "English outside brackets changed: " + uid)
        check(unit["sourceWordCount"] == len(original.split()) and
              unit["summarizedSourceWords"] == count, "Historical source word accounting " + uid)
    if marked:
        # Brackets in unrelated figure captions and damaged source readings predate this restoration.
        check("[" not in original and "]" not in original, "Review pre-existing source brackets " + uid)
        for field in ("analysis", "text", "gloss", "source"):
            bracket_contents(unit[field], len(spans), uid + " " + field)
    return len(spans), count


def starts_sentence(unit, previous):
    return not unit["continuesParagraph"] or bool(BOUNDARY.search(previous["analysis"]))


def exact_case_exception(old, current, old_prev, new_prev, previous_changed, maxima):
    if not previous_changed or old_prev is None or new_prev is None:
        return False
    before, after = old["text"], current["text"]
    old_initial = starts_sentence(old, old_prev)
    new_initial = starts_sentence(current, new_prev)
    if old_initial == new_initial or len(before) != len(after):
        return False
    small, capital = (before, after) if new_initial else (after, before)
    for pos, glyph in enumerate(small):
        if glyph in maxima or glyph in maxima.values():
            return small[:pos] + maxima.get(glyph, glyph) + small[pos+1:] == capital
        if glyph.isalnum():
            return False
    return False


def compare_ledgers(before, old_notes, after, notes, lines, maxima):
    check(before["sourceSha256"] == after["sourceSha256"] == PIN, "Ledger source hashes")
    original = index_by_source(before["units"], lines)
    revised = index_by_source(after["units"], lines)
    check(len(old_notes) == FORMER_COUNT, "Unexpected number of preceding editorial summaries")
    check(set(old_notes) == {u["id"] for u in before["units"] if u.get("sourceTreatment")}, "Archive treatment IDs")
    check(set(notes) == {u["id"] for u in after["units"] if u.get("sourceTreatment")}, "Current treatment IDs")
    result = {"sourceSha256": PIN, "originalPassages": len(before["units"]), "revisedPassages": len(after["units"]),
              "formerlySummarizedPassages": {}, "alsoCorrected": {}, "adjacentSourceCorrections": {},
              "splits": {}, "adjacentCapitalization": {}}
    counts = Counter()
    changed = False
    old_prev = new_prev = None
    for n, archived_units in original.items():
        pos = 0
        line = lines[n - 1]
        for old in archived_units:
            uid = old["id"]
            a, b = old["sourceOffsets"]
            children = []
            while pos < len(revised[n]) and revised[n][pos]["sourceOffsets"][0] < b:
                children.append(revised[n][pos])
                pos += 1
            check(children and children[0]["sourceOffsets"][0] == a and children[-1]["sourceOffsets"][1] == b,
                  "Archive boundaries do not enclose current passages: " + uid)
            check(all(u["chapter"] == old["chapter"] for u in children), "Changed section " + uid)
            if len(children) > 1:
                check(uid in SPLITS and len(children) == 2 and
                      line[a:children[0]["sourceOffsets"][1]].endswith(SPLITS[uid]), "Unexpected division " + uid)
                result["splits"][uid] = {"after": SPLITS[uid], "current": [u["id"] for u in children]}
            src = line[a:b]
            marked = uid in old_notes
            if marked:
                previous_note = old_notes[uid]
                check(previous_note["originalSha256"] == text_hash(src) and previous_note["reading"] == old["source"]
                      and old["sourceWordCount"] == len(src.split()), "Archived reading " + uid)
            else:
                check(src == old["source"], "Archived direct source " + uid)
            spans = words = 0
            published_spans = []
            for u in children:
                start, stop = u["sourceOffsets"]
                note = notes.get(u["id"])
                span_count, word_count = verify_reading(u, line[start:stop], note, marked)
                spans += span_count
                words += word_count
                if note:
                    published_spans.extend({"unit": u["id"], "lineOffsets": [start+s["start"], start+s["end"]],
                                            "replacementSha256": text_hash(s["replacement"])} for s in note["spans"])
            counts["allSourceWords"] += len(src.split())
            if marked:
                counts["formerSourceWords"] += len(src.split())
                counts["wordsStillSummarized"] += words
                counts["bracketedSpans"] += spans
                counts["fullyRestored" if not spans else "partiallyRestored"] += 1
                result["formerlySummarizedPassages"][uid] = {
                    "line": n, "originalOffsets": [a, b], "current": [u["id"] for u in children],
                    "sourceSha256": text_hash(src), "originalWords": len(src.split()),
                    "directWords": len(src.split()) - words, "bracketedSpans": spans,
                    "interventions": published_spans,
                }
            elif uid in EXTRA:
                check(len(children) == 1, "Count correction was split: " + uid)
                current = children[0]
                check(all(term in current["gloss"] for term in EXTRA[uid]) and current["text"] != old["text"]
                      and current["analysis"] != old["analysis"], "Missing separate count correction " + uid)
                result["alsoCorrected"][uid] = list(EXTRA[uid])
            elif uid == CONTEXT_CORRECTION and old["analysis"] != children[0]["analysis"]:
                old_phrase = "town or dam_plantation:pl:a seek:inf"
                new_phrase = "some town or dam_plantation:pl:a around seek:inf"
                current = children[0]
                check(len(children) == 1 and "to search about for some Town or Plantations" in src and
                      old["analysis"].count(old_phrase) == 1 and
                      old["analysis"].replace(old_phrase, new_phrase) == current["analysis"],
                      "Unexpected change in the adjacent provisions sentence")
                result["adjacentSourceCorrections"][uid] = "Restored ‘some’ and ‘about’ in the search for provisions."
            else:
                current = children[0]
                check(len(children) == 1 and all(current[k] == old[k] for k in ("analysis", "keys", "gloss", "source")),
                      "Unaffected analysis, gloss or English changed: " + uid)
                if old["text"] != current["text"]:
                    check(exact_case_exception(old, current, old_prev, new_prev, changed, maxima),
                          "Unaffected native wording changed: " + uid)
                    result["adjacentCapitalization"][uid] = "The edited preceding unit changed its sentence boundary."
                else:
                    counts["identicalUnaffectedPassages"] += 1
            changed = marked or uid in EXTRA
            old_prev, new_prev = old, children[-1]
        check(pos == len(revised[n]), f"Unaccounted revised passage on TXT line {n}")
    check(result["splits"].keys() == SPLITS.keys() and result["alsoCorrected"].keys() == EXTRA.keys(),
          "Missing authorized split or corrected number")
    check(counts["fullyRestored"] + counts["partiallyRestored"] == FORMER_COUNT, "Missing former passage")
    counts["formerWordsRestoredVerbatim"] = counts["formerSourceWords"] - counts["wordsStillSummarized"]
    counts["wholeBookVerbatimSourceWords"] = counts["allSourceWords"] - counts["wordsStillSummarized"]
    result["counts"] = dict(counts)
    return result


def verify_bracket_font(font_id):
    from fontTools.ttLib import TTFont
    from vayrshemon.fonts import FontRegistry
    digest = font_id.split(":")[1]
    roman = ROOT / "data/runtime-fonts/transliteration 7.ttf"
    face = roman if digest == FONTS[1] else FontRegistry(ROOT, None).document_path(
        Path(os.environ["WINDIR"]) / "Fonts/times.ttf", digest)
    check(sha(face) == digest, "Unresolved saved bracket font: " + font_id)
    with TTFont(face) as font:
        for character, expected in (("[", "bracketleft"), ("]", "bracketright")):
            name = font.getBestCmap().get(ord(character))
            check(name == expected, "Incorrect printed bracket glyph: " + font_id)
            glyph = font["glyf"][name]
            check(glyph.numberOfContours != 0 and glyph.xMin < glyph.xMax and glyph.yMin < glyph.yMax
                  and font["hmtx"][name][0] > 0, "Empty bracket glyph: " + font_id)
    return {"sha256": digest, "file": face.name, "bothBracketOutlinesHaveInkAndAdvance": True}


def compare_sentence_revision(archived, archived_notes, ledger, notes, lines):
    before, after = archived["units"], ledger["units"]
    check(len(before) == len(after), "Unexpected change in aligned passage count")
    check(sum(len(n["spans"]) for n in archived_notes.values()) == 23, "Wrong 23-substitution archive")
    report = {"identicalPassages": 0, "editedPassages": {}, "oldSourceWordsInBrackets": 0,
              "newSourceWordsInBrackets": 0, "oldBracketedUnits": len(archived_notes),
              "newBracketedUnits": len(notes), "oldBracketedSpans": 0, "newBracketedSpans": 0}
    fixed_fields = ("id", "sourceOffsets", "sourceLine", "chapter", "reference", "continuesParagraph")
    for old, new in zip(before, after, strict=True):
        uid = old["id"]
        check(all(old[k] == new[k] for k in fixed_fields), "Changed source anchor or section " + uid)
        a, b = old["sourceOffsets"]
        src = lines[old["sourceLine"]-1][a:b]
        old_note, new_note = archived_notes.get(uid), notes.get(uid)
        old_spans, old_words = verify_reading(old, src, old_note, old_note is not None)
        new_spans, new_words = verify_reading(new, src, new_note, old_note is not None)
        for version, spans, words in (("old", old_spans, old_words), ("new", new_spans, new_words)):
            report[version + "BracketedSpans"] += spans
            report[version + "SourceWordsInBrackets"] += words
        if uid not in SENTENCE_REVISION:
            check(old == new and old_note == new_note, "Unapproved revision in " + uid)
            report["identicalPassages"] += 1
            continue
        check(old_note is not None and old["analysis"] != new["analysis"] and old["text"] != new["text"]
              and old["gloss"] != new["gloss"] and new_words <= old_words, "Missing expected revision " + uid)
        if new_note:
            for span in new_note["spans"]:
                check(any(prior["start"] <= span["start"] and prior["end"] >= span["end"]
                          for prior in old_note["spans"]), "Newly generalized wording " + uid)
        report["editedPassages"][uid] = {
            "sourceLine": old["sourceLine"], "offsets": [a, b], "oldBracketedSpans": old_spans,
            "newBracketedSpans": new_spans, "oldBracketedWords": old_words, "newBracketedWords": new_words,
            "restoredOriginalWords": old_words - new_words, "directEnglishReadingChanged": old["source"] != new["source"],
            "oldNativeSha256": text_hash(old["text"]), "newNativeSha256": text_hash(new["text"]),
        }
    check(set(report["editedPassages"]) == SENTENCE_REVISION, "Missing a sentence revision")
    report["restoredOriginalWords"] = report["oldSourceWordsInBrackets"] - report["newSourceWordsInBrackets"]
    return report


def verify_visual_brackets(receipt, notes, native_digest):
    """Link the current visual receipt to the exact native and the rendered bracket pixels."""
    check(receipt["nativeSha256"] == native_digest, "The visual receipt belongs to a different publication")
    seen_units = set()
    expected_pairs = sum(len(n["spans"]) for n in notes.values())
    marks = Counter()
    min_coverage = 1.0
    for sample in receipt["samples"]:
        seen_units.update(sample["selectedPassages"])
        check(bool(sample["visualObservation"].strip()), "Missing visual inspection")
        for p in sample["proofs"]:
            check(sha(WORK / p["path"]) == p["sha256"], "Visual proof checksum")
        tally = Counter()
        for glyph in sample["bracketGlyphs"]:
            key = glyph["unit"], glyph["column"], glyph["character"]
            tally[key] += 1
            marks[key[1:]] += 1
            check(glyph["interiorPixels"] >= 2 and glyph["matchingPixels"] / glyph["interiorPixels"] >= 0.94,
                  "A printed bracket lost its outline")
            min_coverage = min(min_coverage, glyph["matchingPixels"] / glyph["interiorPixels"])
        for uid in sample["selectedPassages"]:
            for col in range(1, 5):
                for ch in "[]":
                    check(tally[uid, col, ch] == len(notes.get(uid, {}).get("spans", [])), "Missing raster bracket " + uid)
    check(set(notes) | SENTENCE_REVISION <= seen_units, "Missing affected spread in visual review")
    check(all(marks[col, ch] == expected_pairs for col in range(1, 5) for ch in "[]"), "Incomplete raster review")
    check(sum(s["pairs"] for s in receipt["bracketContactSheets"]) == expected_pairs and
          all(sha(WORK / s["path"]) == s["sha256"] for s in receipt["bracketContactSheets"]),
          "The bracket contact sheets do not match the reviewed publication")
    return {"receipt": "completion-visual-proof.json", "receiptSha256": sha(WORK / "completion-visual-proof.json"),
            "reviewedSpreads": receipt["reviewedSpreads"], "reviewedPages": receipt["reviewedPages"],
            "visibleEditorialBracketPairsPerColumn": expected_pairs, "checkedBracketGlyphs": sum(marks.values()),
            "minimumExpectedOutlinePixelCoverage": min_coverage}


def check_native(native, ledger, treated, index):
    """Check actual style runs in both script readings as well as the source and gloss."""
    original_digest = sha(native)
    units = iter(ledger["units"])
    pages = iter(saved_pages(native))
    labels = ["Vayrshemon", "Transliteration 7", "Construction gloss", ledger["sourceLabel"]]
    fonts = {}
    visible_pairs = Counter()
    marked_spreads = {}
    spreads = iter(index["spreads"])
    page_count = passage_count = 0
    for left in pages:
        right = next(pages, None)
        check(right is not None, "Incomplete facing spread")
        page_count += 2
        frames = [frame for page in (left, right) for frame in sorted(page["frames"], key=lambda f: int(f["x"]))]
        check([f["name"] for f in frames] == labels, f"Four column labels at page {page_count-1}")
        stories = [f["content"]["document"]["stories"] for f in frames]
        check(all(len(s) == 1 for s in stories), f"Story count at page {page_count-1}")
        styles = [{s["styleId"]: s for s in f["content"]["document"]["styles"]} for f in frames]
        spread_ids = []
        for blocks in zip_longest(*(s[0]["blocks"] for s in stories)):
            unit = next(units, None)
            check(unit is not None and None not in blocks, f"Unaligned passage on page {page_count-1}")
            passage_count += 1
            spread_ids.append(unit["id"])
            if unit["id"] in treated:
                marked_spreads[unit["id"]] = [page_count - 1, page_count]
            for i, (block, field) in enumerate(zip(blocks, FIELDS)):
                pieces = []
                native_run = False
                for run in block["runs"]:
                    if run["type"] == "legacy":
                        check(i < 2 and run["sourceFontSha256"] == FONTS[i], "Incorrect native font: " + unit["id"])
                        piece = run["sourceText"]
                        native_run = True
                    else:
                        check(run["type"] == "unicode", "Unknown saved run type")
                        piece = run["text"]
                    pieces.append(piece)
                    if unit["id"] in treated and ("[" in piece or "]" in piece):
                        font_id = styles[i][run["styleId"]]["fontId"]
                        if font_id not in fonts:
                            fonts[font_id] = verify_bracket_font(font_id)
                        visible_pairs[labels[i]] += piece.count("[")
                value = "".join(pieces)
                check(value == unit[field], f"Saved {labels[i]} differs at {unit['id']}")
                check(i > 1 or native_run or not any(c.isalnum() for c in value), "Lost glyph run " + unit["id"])
        indexed = next(spreads, None)
        check(indexed and [indexed["leftPage"], indexed["rightPage"]] == [page_count - 1, page_count] and
              indexed["unitIds"] == spread_ids, f"Progressive page index differs for native pages {page_count-1}–{page_count}")
    check(next(spreads, None) is None, "Extraneous spread in progressive page index")
    check(next(units, None) is None and passage_count == len(ledger["units"]), "Incomplete saved manuscript")
    if treated:
        expected = sum(len(t["spans"]) for t in treated.values())
        check(all(visible_pairs[label] == expected for label in labels), "Missing visible intervention brackets")
    check(sha(native) == original_digest, f"Manuscript changed during audit: {native}")
    return {"sha256": original_digest, "pages": page_count, "alignedPassages": passage_count,
            "verifiedParagraphsByColumn": dict.fromkeys(labels, passage_count),
            "editorialBracketPairsByColumn": dict(visible_pairs), "verifiedBracketFonts": fonts,
            "editorialPassageSpreads": marked_spreads, "verifiedSpreadsAgainstPageIndex": page_count // 2}


def main():
    from tools.editorial_language import load_current
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staged-ledger", type=Path, help="Dry-run source and target checks, without writing a receipt.")
    args = parser.parse_args()
    old, old_notes, previous_native = read_archive()
    recent, recent_notes, recent_native = read_archive(SENTENCE_ARCHIVE)
    check(sha(SOURCE) == PIN, "Original TXT hash")
    ledger_path = args.staged_ledger or WORK / "ledger.json"
    ledger_digest = sha(ledger_path)
    notes_digest = sha(WORK / "source-treatments.json")
    new = read(ledger_path)
    notes = read(WORK / "source-treatments.json")
    lines = SOURCE.read_text(encoding="utf-8-sig").splitlines()
    language, _ = load_current()
    report = compare_ledgers(old, old_notes, new, notes, lines, language.pairs)
    revision = compare_sentence_revision(recent, recent_notes, new, notes, lines)
    report["comparisonWith23SubstitutionEdition"] = revision
    if not args.staged_ledger:
        index_path = WORK / "page-index.json"
        index_digest = sha(index_path)
        report["previousNative"] = check_native(previous_native, old, {}, read(previous_native.parent / "Working/page-index.json"))
        revision["archivedNative"] = check_native(recent_native, recent, recent_notes,
                                                  read(recent_native.parent / "Working/page-index.json"))
        report["revisedNative"] = check_native(BOOK / (EDITION + ".vay"), new, notes, read(index_path))
        report["visualReview"] = verify_visual_brackets(read(WORK / "completion-visual-proof.json"), notes,
                                                        report["revisedNative"]["sha256"])
        check(sha(ledger_path) == ledger_digest and sha(WORK / "source-treatments.json") == notes_digest,
              "Ledger or treatment manifest changed during audit")
        check(sha(index_path) == index_digest, "Progressive page index changed during audit")
        report["currentPageIndexSha256"] = index_digest
        report["currentLedgerSha256"] = ledger_digest
        report["currentSourceTreatmentsSha256"] = notes_digest
        dest = WORK / "passage-restoration-audit.json"
        temp = dest.with_suffix(".tmp")
        temp.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temp.replace(dest)
    print(json.dumps(report["counts"]))


if __name__ == "__main__":
    main()
