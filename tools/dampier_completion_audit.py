"""Independently reconcile Dampier's supplied text, aligned ledger and saved pages."""
import argparse
import base64
import codecs
import hashlib
import json
from pathlib import Path
import re
import zlib


ROOT = Path(__file__).resolve().parents[1]
TITLE = "A New Voyage Round the World"
EDITION = TITLE + " - Four-Column Progressive Edition"
BOOK = ROOT / "Saves" / EDITION
WORK = BOOK / "Working"
ARCHIVE = ROOT / "Saves/Archive/Previous editions/Before Dampier full source review" / EDITION
SOURCE = ROOT / "Inputs/Sources" / f"William Dampier - {TITLE}.txt"
PIN = "64cf3c4181bdf8fc463b8b532166dea398d5833294c0d99451b2032a8b1cc23d"
FONTS = ("a9bb4075285df9acf2bf75c08446d44cfd83b29f6940937671cc07bd68f9f6cc",
         "9ba7c6f12d40ea8a0aafb8f07a69f8b65b424e374c6da95235a45edeb6292c52")


def check(test, explanation):
    if not test:
        raise ValueError(explanation)


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    with path.open("rb") as handle:
        digest = hashlib.sha256()
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_report(ledger):
    raw = SOURCE.read_bytes()
    check(hashlib.sha256(raw).hexdigest() == PIN == ledger["sourceSha256"], "Source hash")
    text = raw.decode("utf-8-sig")
    lines = text.splitlines()
    nonblank = [n for n, line in enumerate(lines, 1) if line.strip()]
    notes = read(WORK / "source-treatments.json")
    readings = read(WORK / "catalogue-readings.json")
    for reading in readings:
        check(lines[reading["sourceLine"] - 1] == reading["supplied"] and
              reading["reading"] and reading["uncertainty"], f"Catalogue note {reading['sourceLine']}")
    front = {1: "Title", 15: "Dedication", 25: "Preface", 43: "Contents", 87: "World map",
             89: "Introduction", 2177: "Errata", 2257: "Bookseller’s catalogue"}
    sections, used_notes = {}, []
    damaged_marks = {mark: [] for mark in ("〈◊〉", "•…")}
    line_index = offset = segment = 0
    for unit in ledger["units"]:
        n = nonblank[line_index]
        line = lines[n - 1]
        if offset == 0:
            match = re.fullmatch(r"CHAP\.? ([IVX]+)\.", line.strip())
            if n in front or match:
                section = front[n] if n in front else "Chapter " + match[1]
            section_stats = sections.setdefault(section, {"firstLine": n, "passages": 0,
                "suppliedWords": 0, "directWords": 0, "wordsInSummaries": 0})
            section_stats["suppliedWords"] += len(line.split())
            section_stats["lastLine"] = n
        segment += 1
        uid = f"dampier.{n:04}.{segment:03}"
        start, end = unit["sourceOffsets"]
        check(unit["id"] == uid and unit["chapter"] == section and unit["sourceLine"] == n and
              start == offset and start < end <= len(line) and
              (end == len(line) or line[end].isspace()) and
              unit["continuesParagraph"] == bool(offset), f"Source range {uid}")
        check(not unit.get("translationPending") and unit["keys"] and all(
            s.strip() not in {"", "—", "[pending]"} for s in (unit["text"], unit["analysis"],
                unit["gloss"])), f"Missing target {uid}")
        original = line[start:end]
        words = len(original.split())
        for mark, locations in damaged_marks.items():
            for occurrence in re.finditer(re.escape(mark), original):
                locations.append(dict(unit=uid, sourceLine=n, offset=start + occurrence.start()))
        section_stats["passages"] += 1
        if uid in notes:
            note = notes[uid]
            check(note["originalSha256"] == hashlib.sha256(original.encode()).hexdigest() and
                  unit["sourceTreatment"] == "editorial summary" and unit["sourceWordCount"] == words,
                  f"Original source note {uid}")
            if "spans" in note:
                tokens = list(re.finditer(r"\S+", original))
                starts = {match.start(): i for i, match in enumerate(tokens)}
                ends = {match.end(): i + 1 for i, match in enumerate(tokens)}
                supplied, summarized, previous = original, 0, len(original)
                for span in reversed(note["spans"]):
                    a, b, replacement = span["start"], span["end"], span["replacement"]
                    check(a in starts and b in ends and a < b <= previous and
                          replacement.startswith("[") and replacement.endswith("]"), f"Bracket limits {uid}")
                    summarized += ends[b] - starts[a]
                    supplied = supplied[:a] + replacement + supplied[b:]
                    previous = a
                check(summarized > 0, f"Empty editorial mark {uid}")
            else:
                supplied, summarized = note["reading"], words
            check(supplied == unit["source"] and summarized == unit.get("summarizedSourceWords", words),
                  f"Published source reading {uid}")
            section_stats["wordsInSummaries"] += summarized
            section_stats["directWords"] += words - summarized
            used_notes.append(uid)
        else:
            check("sourceTreatment" not in unit and unit["source"] == original, f"Source wording {uid}")
            section_stats["directWords"] += words
        offset = end
        while offset < len(line) and line[offset].isspace():
            offset += 1
        if offset == len(line):
            line_index += 1
            offset = segment = 0
    words = len(text.split())
    direct = sum(s["directWords"] for s in sections.values())
    summarized = sum(s["wordsInSummaries"] for s in sections.values())
    by_id = {u["id"]: u for u in ledger["units"]}
    syntax = "Syntax and immediate context. The English reproduces the supplied spelling."
    damaged_numerals = {
        "dampier.0311.003": ("Heads of, or 4 men", "Heads of [quantity missing], or 4 men",
                             "— or unta_cardinal_e_over_b_digits",
                             "The first alternative is illegible. The native has a dash followed by the surviving four."),
        "dampier.0897.001": ("10 cure them", "to cure them", "prepare:cv", syntax),
        "dampier.0937.004": ("3 large head", "a large head", "large head", syntax),
    }
    body_readings = []
    for uid, (supplied, probable, analysis_phrase, basis) in damaged_numerals.items():
        u = by_id[uid]
        check(supplied in u["source"] and analysis_phrase in u["analysis"], "OCR reading " + uid)
        body_readings.append(dict(unit=uid, supplied=supplied, probableReading=probable, basis=basis))
    romans = "I II III IV V VI VII VIII IX X XI XII XIII XIV XV XVI XVII XVIII XIX XX".split()
    check([s for s in sections if s.startswith("Chapter ")] == ["Chapter " + r for r in romans],
          "Twenty consecutive chapters")
    check(line_index == len(nonblank) and offset == 0 and len(sections) == 28 and
          set(used_notes) == set(notes) and
          all(s["directWords"] + s["wordsInSummaries"] == s["suppliedWords"] for s in sections.values()),
          "Source coverage and editorial notes")
    check(ledger["status"] == "complete" and not ledger["pendingUnits"] and
          ledger["nextSourceLine"] is None and ledger["nextSourceOffset"] == 0 and
          ledger["sourceCharacters"] == len(text) and
          words == ledger["sourceWords"] == ledger["sourceWordsAccountedFor"] == direct + summarized and
          direct == ledger["translatedSourceWords"] and summarized == ledger["sourceWordsInSummaryPassages"],
          "Published source totals")
    check(all(len(locations) == text.count(mark) for mark, locations in damaged_marks.items()),
          "Source damage-marker indexing")
    return dict(sourceSha256=PIN, rawBytes=len(raw), characters=len(text), words=words,
                physicalLines=len(lines), nonblankLines=len(nonblank), directSourceWords=direct,
                sourceWordsInEditorialSummaries=summarized, editorialSummaryPassages=used_notes,
                sections=sections, catalogueReadings=readings, proseNumeralReadings=body_readings,
                markLocationConvention="Source lines are one-based. Offsets are zero-based Unicode characters within the original line.",
                sourceMarks={m: {"count": len(locations), "locations": locations}
                             for m, locations in damaged_marks.items()},
                standaloneBullets=text.count("•") - text.count("•…"), bracketedEllipses=text.count("[…]"))


def state_chunks(envelope):
    check(envelope["codec"] == "zlib-json-v1", "Native file encoding")
    compressed = envelope.pop("data")
    inflater, hasher = zlib.decompressobj(), hashlib.sha256()
    decoder = codecs.getincrementaldecoder("utf-8")()
    size = 0
    for pos in range(0, len(compressed), 65536):
        data = inflater.decompress(base64.b64decode(compressed[pos:pos + 65536], validate=True))
        size += len(data)
        hasher.update(data)
        yield decoder.decode(data)
    data = inflater.flush()
    hasher.update(data)
    yield decoder.decode(data, final=True)
    check(inflater.eof and not inflater.unused_data and size + len(data) == envelope["expandedBytes"] and
          hasher.hexdigest() == envelope["sha256"], "Native state checksum")


def saved_pages(path):
    """Walk the page array without holding thousands of deserialized pages in memory."""
    wrapper = read(path)
    if "stateEncoding" not in wrapper:
        yield from wrapper["state"]["pages"]
        return
    chunks = iter(state_chunks(wrapper.pop("stateEncoding")))
    del wrapper
    data = next(chunks)
    marker = re.search(r',\s*"pages"\s*:\s*\[', data[:4096])
    check(marker, "Native page array header")
    data = data[marker.end():]
    decoder = json.JSONDecoder()
    first = True
    while True:
        while not data.strip():
            data += next(chunks)
        data = data.lstrip()
        if data.startswith("]"):
            break
        if not first:
            check(data.startswith(","), "Native page separator")
            data = data[1:].lstrip()
        while True:
            try:
                page, end = decoder.raw_decode(data)
                break
            except json.JSONDecodeError:
                data = (data + next(chunks)).lstrip()
        yield page
        data, first = data[end:], False
    for _ in chunks:
        pass


def saved_report(path, ledger):
    rows = ledger["units"]
    labels = ("Vayrshemon", "Transliteration 7", "Construction gloss", ledger["sourceLabel"])
    offset = pages = 0
    saved = iter(saved_pages(path))
    for left in saved:
        right = next(saved, None)
        check(right is not None, f"Unpaired page {pages + 1}")
        frames = [f for p in (left, right) for f in sorted(p["frames"], key=lambda f: int(f["x"]))]
        check(tuple(f["name"] for f in frames) == labels, f"Columns at page {pages + 1}")
        columns = []
        for i, frame in enumerate(frames):
            stories = frame["content"]["document"]["stories"]
            check(len(stories) == 1, f"Story count, page {pages + 1}")
            paragraphs = []
            for block in stories[0]["blocks"]:
                runs = block["runs"]
                for run in runs:
                    if run["type"] == "legacy":
                        check(i < 2 and run["sourceFontSha256"] == FONTS[i],
                              f"Glyph font on page {pages + 1}")
                    else:
                        check(run["type"] == "unicode", f"Unexpected run on page {pages + 1}")
                value = "".join(r["sourceText"] if r["type"] == "legacy" else r["text"] for r in runs)
                if i < 2 and any(c.isalnum() for c in value):
                    check(any(r["type"] == "legacy" for r in runs), f"Missing native glyphs, page {pages + 1}")
                paragraphs.append(value)
            columns.append(paragraphs)
        check(len({len(c) for c in columns}) == 1 and columns[0], f"Alignment on page {pages + 1}")
        for values in zip(*columns):
            unit = rows[offset]
            check(values == (unit["text"], unit["text"], unit["gloss"], unit["source"]),
                  f"Saved columns differ at {unit['id']}, page {pages + 1}")
            offset += 1
        pages += 2
    check(offset == len(rows), "Missing native paragraphs")
    return dict(sha256=sha(path), pages=pages, alignedPassages=offset,
                verifiedParagraphsByColumn={label: offset for label in labels})


def archived():
    ledger_path, native = ARCHIVE / "Working/ledger.json", ARCHIVE / (EDITION + ".vay")
    pins = read(ARCHIVE.parent / "restoration-index.json")["files"]
    for path in (ledger_path, native):
        check(sha(path) == pins[path.relative_to(ARCHIVE.parent).as_posix()], "Archive pin " + path.name)
    old = read(ledger_path)
    check(len(old["units"]) == 605, "Archive opening count")
    report = saved_report(native, old)
    pending = [u["id"] for u in old["units"] if u.get("translationPending")]
    translated = sum(len(u["source"].split()) for u in old["units"] if not u.get("translationPending"))
    check(translated == old["translatedSourceWords"] and pending == old["pendingUnits"], "Archive totals")
    report.update(directSourceWords=translated, pendingUnits=pending,
                  sourceWordsPreviouslyOutstanding=old["sourceWords"] - translated,
                  lastUnit=old["units"][-1]["id"], nextSourceLine=old["nextSourceLine"])
    return old, report


def compare_opening(old, new):
    changes = {}
    for previous, current in zip(old["units"], new["units"]):
        uid = previous["id"]
        check(uid == current["id"], f"Opening order {uid}")
        changed = sorted(k for k in previous.keys() | current.keys() if previous.get(k) != current.get(k))
        if changed:
            changes[uid] = changed
    reference, quantity = "dampier.0033.006", "dampier.0227.006"
    repair, capitalization = "dampier.0173.010", "dampier.0173.011"
    check(set(changes) == {reference, quantity, repair, capitalization},
          f"Unexpected changes in old opening: {changes}")
    before = {u["id"]: u for u in old["units"]}
    after = {u["id"]: u for u in new["units"][:605]}
    for uid, (was, now) in {reference: ("either one or other", "either of these"),
                            quantity: ("one drama_native_boy", "unta_cardinal_b_over_b drama_native_boy")}.items():
        check(changes[uid] == ["analysis", "gloss", "keys", "text"] and
              before[uid]["analysis"].count(was) == 1 and
              before[uid]["analysis"].replace(was, now) == after[uid]["analysis"],
              "Opening lexical correction " + uid)
    check(before[repair]["translationPending"] and before[repair]["text"] == "—" and
          not after[repair].get("translationPending") and after[repair]["keys"] and
          after[repair]["analysis"] == "which with he at throw:psv:pa what aside strike:pr he." and
          not (set(changes[repair]) - {"translationPending", "analysis", "text", "gloss", "keys"}),
          "Former placeholder")
    check(changes[capitalization] == ["text"] and
          before[capitalization]["text"][0].upper() + before[capitalization]["text"][1:] ==
          after[capitalization]["text"], "Capitalization after repaired passage")
    reasons = {reference: "An inanimate pair of matters takes 'either of these'.",
               repair: "The archived dash is replaced by a translation of the supplied clause.",
               capitalization: "The restored preceding sentence ends in a full stop.",
               quantity: "The single boy in the source takes the cardinal numeral."}
    return {"fullyIdenticalUnits": 605 - len(changes), "reconciledUnits": {
        uid: {"sourceLine": before[uid]["sourceLine"], "sourceOffsets": before[uid]["sourceOffsets"],
              "sourceSha256": hashlib.sha256(before[uid]["source"].encode()).hexdigest(),
              "changedFields": fields, "reason": reasons[uid]}
        for uid, fields in changes.items()}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive-only", action="store_true")
    parser.add_argument("--source-ledger", type=Path, help="check a staged complete ledger against the TXT")
    args = parser.parse_args()
    old, old_saved = archived()
    if args.archive_only:
        print(json.dumps(old_saved, ensure_ascii=False))
        return
    ledger_path = args.source_ledger or WORK / "ledger.json"
    ledger = read(ledger_path)
    source = source_report(ledger)
    differences = compare_opening(old, ledger)
    if args.source_ledger:
        print(f"{source['words']} source words, {len(ledger['units'])} passages, {len(source['sections'])} sections")
        return
    current = saved_report(BOOK / (EDITION + ".vay"), ledger)
    result = dict(source=source, ledgerSha256=sha(ledger_path), progressive=current,
                  archivedProgressive=old_saved, originalOpening=differences)
    target = WORK / "completion-audit.json"
    temporary = target.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(target)
    print(f"{source['words']} source words, {current['pages']} native pages, {current['alignedPassages']} aligned passages")


if __name__ == "__main__":
    main()
