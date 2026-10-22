"""Project-authored fixtures; no original font or document bytes are copied."""

from pathlib import Path
from .common import load_json, write_json


def make_font(path, advance=600):
    """Create a minimal, reproducible TTF for public font-registry tests."""
    from fontTools.fontBuilder import FontBuilder
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    builder = FontBuilder(1000, isTTF=True)
    builder.setupGlyphOrder([".notdef", "space", "A"])
    builder.setupCharacterMap({32: "space", 65: "A"})
    glyphs = {}
    for name in (".notdef", "space", "A"):
        pen = TTGlyphPen(None)
        if name != "space":
            pen.moveTo((40, 0))
            pen.lineTo((advance // 2, 700))
            pen.lineTo((advance - 40, 0))
            pen.closePath()
        glyphs[name] = pen.glyph()
    builder.setupGlyf(glyphs)
    builder.setupHorizontalMetrics({".notdef": (600, 40), "space": (300, 0), "A": (advance, 40)})
    builder.setupHorizontalHeader(ascent=800, descent=-200)
    builder.setupNameTable({"familyName": "Vayrshemon M0 Synthetic", "styleName": "Regular",
                           "uniqueFontIdentifier": "Vayrshemon-M0-Synthetic", "fullName": "Vayrshemon M0 Synthetic Regular",
                           "psName": "VayrshemonM0Synthetic-Regular", "version": "Version 0.1"})
    builder.setupOS2(sTypoAscender=800, sTypoDescender=-200, usWinAscent=800, usWinDescent=200)
    builder.setupPost()
    builder.setupMaxp()
    builder.font.recalcTimestamp = False
    builder.font["head"].created = builder.font["head"].modified = 2082844800
    builder.save(path)


def document(document_id, runs, width="612000000", height="792000000"):
    return {"schemaVersion": "0.1.0", "documentId": document_id, "revision": 0, "title": "Synthetic M0 specimen",
            "layoutProfile": "layout.provisional-m0", "languageRevision": None, "fonts": [],
            "styles": [{"styleId": "style.body", "fontId": None, "fontSizeMicroPoints": "12000000",
                        "lineHeight": {"mode": "at-least", "microPoints": "14000000"}, "color": "#000000FF"}],
            "pages": [{"pageId": "page.1", "widthMicroPoints": width, "heightMicroPoints": height,
                       "marginsMicroPoints": {edge: "18000000" for edge in ("top", "right", "bottom", "left")},
                       "frames": [{"frameId": "frame.1", "storyId": "story.1", "xMicroPoints": "18000000", "yMicroPoints": "18000000",
                                   "widthMicroPoints": str(int(width) - 36000000), "heightMicroPoints": str(int(height) - 36000000), "overflow": "show"}]}],
            "stories": [{"storyId": "story.1", "blocks": [{"blockId": "block.1", "type": "paragraph", "direction": "auto", "runs": runs}]}]}


def unicode_run(text, identity="run.1", language="language.en"):
    return {"runId": identity, "languageId": language, "styleId": "style.body", "type": "unicode", "text": text, "normalization": "none"}


def generate(root):
    root = Path(root)
    mapping = load_json(root / "data/orthography/thimfora-79.json")
    master_sha = next(font["asset"]["sha256"] for font in load_json(root / "data/fonts.json")["fonts"]
                      if font["asset"]["path"] == "font files/Thimfora_79.ttf")
    documents = {
        "unicode": document("document.unicode", [unicode_run("A\u0301 and Á stay distinct. Emoji: 😀.\tSpace\u00a0kept.\n", "run.english"),
                                                  unicode_run("العربية", "run.arabic", "language.ar")]),
        "symbols": document("document.symbols", [unicode_run("Alphabet and numerals: ", "run.heading"),
                     {"runId": "run.symbols", "languageId": "language.vayrshemon", "styleId": "style.body", "type": "symbols",
                      "orthographyRef": {"profileId": mapping["profileId"], "revision": mapping["revision"]},
                      "symbols": [{"symbolId": entry["symbolId"], "form": entry["form"]} for entry in mapping["entries"] if entry["kind"] in ("letter", "digit")]},
                     {"runId": "run.unresolved", "languageId": "language.undetermined", "styleId": "style.body", "type": "legacy",
                      "sourceText": "Jj\u00be\u0301😀", "sourceFontSha256": master_sha, "mappingProfileRef": None, "normalization": "none"}]),
        "spacing": document("document.spacing", [unicode_run("Ágjy Ágjy\nA\u0301A\u0301\nWide line: WWWWWWWWWWWW\n", "run.spacing")], "327375000", "123456789"),
    }
    documents["spacing"]["styles"][0]["lineHeight"] = {"mode": "exact", "microPoints": "6000000"}
    # A second page exercises a large but bounded dimension without allocating pixels.
    documents["spacing"]["pages"].append({"pageId": "page.2", "widthMicroPoints": "1000000000000", "heightMicroPoints": "72000000",
                                         "marginsMicroPoints": {edge: "0" for edge in ("top", "right", "bottom", "left")}, "frames": []})
    for name, value in documents.items():
        write_json(root / "tests/fixtures/documents" / (name + ".json"), value)
    command = {"apiVersion": "0.1.0", "requestId": "request.demo", "sessionId": "session.demo", "command": "document.apply",
               "documentId": "document.unicode", "expectedRevision": 0, "idempotencyKey": "demo-edit-1", "dryRun": False,
               "operations": [{"type": "insert-text", "position": {"blockId": "block.1", "runId": "run.english", "offset": 2,
                                                                       "offsetUnit": "unicode-scalar", "affinity": "after"}, "text": " revised"}]}
    write_json(root / "tests/fixtures/commands/transaction.json", command)
    write_json(root / "tests/fixtures/commands/conflict-result.json",
               {"apiVersion": "0.1.0", "requestId": "request.demo", "traceId": "trace.demo", "status": "rejected",
                "code": "STALE_REVISION", "currentRevision": 2,
                "diagnostics": [{"code": "STALE_REVISION", "message": "Expected revision 0; current revision is 2.", "severity": "error"}]})


if __name__ == "__main__":
    generate(Path(__file__).resolve().parents[2])
