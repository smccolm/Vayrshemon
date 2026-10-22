"""Source for the initial, explicitly versioned JSON Schema contracts.

Run ``python -m tools.m0.schema_definitions`` to regenerate schemas/. The
repository check also detects divergence between these definitions and JSON.
"""

from pathlib import Path
from .common import write_json

BASE = "urn:vayrshemon:schema:"
VERSION = "0.1.0"
DRAFT = "https://json-schema.org/draft/2020-12/schema"
TEXT = {"type": "string"}
NONEMPTY = {"type": "string", "minLength": 1}
INTEGER = {"type": "integer", "minimum": 0, "maximum": 9007199254740991}
BOOL = {"type": "boolean"}


def ref(name, definition=None):
    return {"$ref": BASE + name + ":" + VERSION + ("#/$defs/" + definition if definition else "")}


def enum(*values):
    return {"enum": list(values)}


def const(value):
    return {"const": value}


def array(items, minimum=0):
    return {"type": "array", "items": items, "minItems": minimum}


def nullable(schema):
    return {"anyOf": [schema, {"type": "null"}]}


def obj(properties, optional=()):
    return {"type": "object", "properties": properties,
            "required": [key for key in properties if key not in optional], "additionalProperties": False}


def definitions():
    ID = {"type": "string", "pattern": "^[A-Za-z][A-Za-z0-9._:-]{0,127}$"}
    SHA = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
    SCALAR = {"type": "integer", "minimum": 0, "maximum": 0x10FFFF,
              "not": {"minimum": 0xD800, "maximum": 0xDFFF}}
    UNSIGNED = {"type": "string", "pattern": "^(0|[1-9][0-9]*)$", "maxLength": 19}
    POSITIVE = {"type": "string", "pattern": "^[1-9][0-9]*$", "maxLength": 19}
    SIGNED = {"type": "string", "pattern": "^(0|-?[1-9][0-9]*)$", "maxLength": 20}
    PATH = {"type": "string", "pattern": r"^(?!/)(?!.*(?:^|/)\.\.?(/|$))(?!.*[\\:])[^\r\n]+$"}
    ASSET = obj({"assetId": ID, "path": PATH, "sha256": SHA})
    EVIDENCE = obj({"asset": ASSET, "locator": NONEMPTY, "method": NONEMPTY})
    SYMBOL = obj({"symbolId": ID, "form": enum("maxima", "minima", "default")})
    common = {"$defs": {"id": ID, "sha256": SHA, "scalar": SCALAR, "asset": ASSET,
                         "evidence": EVIDENCE, "symbol": SYMBOL, "revision": INTEGER,
                         "positiveMicroPoints": POSITIVE, "unsignedMicroPoints": UNSIGNED,
                         "signedMicroPoints": SIGNED}}

    source_asset = obj({**ASSET["properties"], "bytes": INTEGER, "extension": TEXT,
                        "reviewStatus": enum("catalogued", "metadata-reviewed", "text-reviewed",
                                             "reference-preview-reviewed", "reviewed-for-m0"),
                        "roles": array(NONEMPTY)})
    relation = {"oneOf": [
        obj({"type": const("identical-content"), "status": const("verified"), "sha256": SHA, "assetIds": array(ID, 2)}),
        obj({"type": const("same-stem-candidate"), "status": const("unverified"), "stem": NONEMPTY, "assetIds": array(ID, 2)}),
        obj({"type": const("color-layer-of"), "status": const("source-attested"),
             "assetIds": {**array(ID, 2), "maxItems": 2}, "evidenceAssetId": ID, "locator": NONEMPTY}),
        obj({"type": const("font-name-candidate"), "status": const("unverified"),
             "assetIds": {**array(ID, 2), "maxItems": 2}, "evidenceAssetId": ID, "locator": NONEMPTY}),
    ]}
    catalog = obj({"schemaVersion": const(VERSION), "archiveRoot": const("Inputs"),
                   "summary": obj({"fileCount": INTEGER, "totalBytes": INTEGER,
                                   "extensions": {"type": "object", "additionalProperties": INTEGER}}),
                   "assets": array(source_asset), "relationships": array(relation)})

    glyph = obj({"scalar": SCALAR, "glyphId": INTEGER, "glyphName": TEXT,
                 "advance": INTEGER, "leftSideBearing": {"type": "integer"}})
    font = obj({"fontId": ID, "faceIndex": INTEGER, "asset": ASSET,
                "names": obj({key: nullable(TEXT) for key in ("family", "subfamily", "fullName", "version", "postscriptName")}),
                "glyphCount": INTEGER, "unitsPerEm": {"type": "integer", "minimum": 16, "maximum": 16384},
                "verticalMetrics": obj({key: {"type": "integer"} for key in ("ascender", "descender", "lineGap")}),
                "embeddingFlags": nullable(INTEGER), "tableTags": array(TEXT),
                "tableHashes": {"type": "object", "additionalProperties": SHA},
                "cmapSelection": const("fontTools.getBestCmap"), "coverage": array(glyph),
                "unencodedGlyphs": array(obj({"glyphId": INTEGER, "glyphName": TEXT})),
                "mappingStatus": enum("unreviewed", "chart-mapped"), "mappingProfileIds": array(ID)})
    fonts = obj({"schemaVersion": const(VERSION), "fonts": array(font),
                 "familyCollisions": array(obj({"familyKey": TEXT, "fontIds": array(ID, 2), "paths": array(PATH, 2)}))})

    inventory = {"oneOf": [
        obj({"symbolId": ID, "kind": const("letter"), "ordinal": {"type": "integer", "minimum": 1, "maximum": 47},
             "nameTranscription": NONEMPTY, "nameConfidence": enum("low", "medium", "high"),
             "transliterationStatus": enum("transcribed", "unresolved"), "transliterationNote": nullable(NONEMPTY), "evidence": array(EVIDENCE, 1)}),
        obj({"symbolId": ID, "kind": const("digit"), "value": {"type": "integer", "minimum": 0, "maximum": 11},
             "nameTranscription": NONEMPTY, "nameConfidence": enum("low", "medium", "high"), "evidence": array(EVIDENCE, 1)}),
    ]}
    entry = obj({"scalar": SCALAR, "symbolId": nullable(ID), "form": enum("maxima", "minima", "default"),
                 "kind": enum("letter", "digit", "separator", "punctuation"), "status": enum("mapped", "unresolved"),
                 "confidence": enum("low", "medium", "high"), "transliteration": nullable(NONEMPTY),
                 "evidence": array(EVIDENCE, 1), "unresolvedReason": nullable(NONEMPTY), "glyphId": INTEGER, "glyphNameHint": TEXT})
    entry["allOf"] = [
        {"if": {"properties": {"status": const("mapped")}}, "then": {"properties": {"symbolId": ID, "unresolvedReason": {"type": "null"}}}},
        {"if": {"properties": {"status": const("unresolved")}}, "then": {"properties": {"symbolId": {"type": "null"}, "unresolvedReason": NONEMPTY}}},
    ]
    mapping = obj({"schemaVersion": const(VERSION), "profileId": ID, "revision": const(VERSION),
                   "normalization": const("none"), "offsetUnit": const("unicode-scalar"), "unknownPolicy": const("preserve"),
                   "fontSha256s": {**array(SHA, 1), "uniqueItems": True}, "inventory": array(inventory), "entries": array(entry)})

    run_common = {"runId": ID, "languageId": ID, "styleId": ID}
    run = {"oneOf": [
        obj({**run_common, "type": const("unicode"), "text": TEXT, "normalization": const("none")}),
        obj({**run_common, "type": const("symbols"), "orthographyRef": obj({"profileId": ID, "revision": NONEMPTY}), "symbols": array(SYMBOL)}),
        obj({**run_common, "type": const("legacy"), "sourceText": TEXT, "sourceFontSha256": SHA,
             "mappingProfileRef": nullable(obj({"profileId": ID, "revision": NONEMPTY})), "normalization": const("none")}),
    ]}
    line_height = {"oneOf": [
        obj({"mode": enum("exact", "at-least"), "microPoints": POSITIVE}),
        obj({"mode": const("multiple"), "factor": {"type": "number", "exclusiveMinimum": 0, "maximum": 100}}),
    ]}
    frame = obj({"frameId": ID, "storyId": ID, "xMicroPoints": SIGNED, "yMicroPoints": SIGNED,
                 "widthMicroPoints": POSITIVE, "heightMicroPoints": POSITIVE, "overflow": enum("flow", "show", "clip")})
    document = obj({"schemaVersion": const(VERSION), "documentId": ID, "revision": INTEGER, "title": TEXT,
                    "layoutProfile": ID, "languageRevision": nullable(ID),
                    "fonts": array(obj({"fontId": ID, "sha256": SHA, "faceIndex": INTEGER})),
                    "styles": array(obj({"styleId": ID, "fontId": nullable(ID), "fontSizeMicroPoints": POSITIVE,
                                         "lineHeight": line_height, "color": {"type": "string", "pattern": "^#[0-9A-Fa-f]{8}$"}}), 1),
                    "pages": array(obj({"pageId": ID, "widthMicroPoints": POSITIVE, "heightMicroPoints": POSITIVE,
                                        "marginsMicroPoints": obj({edge: UNSIGNED for edge in ("top", "right", "bottom", "left")}),
                                        "frames": array(frame)}), 1),
                    "stories": array(obj({"storyId": ID, "blocks": array(obj({"blockId": ID, "type": const("paragraph"),
                                                                                 "direction": enum("ltr", "rtl", "auto"), "runs": array(run)}))}))})
    position = obj({"blockId": ID, "runId": ID, "offset": INTEGER, "offsetUnit": const("unicode-scalar"), "affinity": enum("before", "after")})
    operation = {"oneOf": [
        obj({"type": const("insert-text"), "position": position, "text": TEXT}),
        obj({"type": const("delete-text"), "blockId": ID, "runId": ID, "start": INTEGER, "end": INTEGER, "offsetUnit": const("unicode-scalar")}),
        obj({"type": const("set-page-dimensions"), "pageId": ID, "widthMicroPoints": POSITIVE, "heightMicroPoints": POSITIVE}),
    ]}
    request = {"oneOf": [
        obj({"apiVersion": const(VERSION), "requestId": ID, "sessionId": ID, "command": const("document.apply"),
             "documentId": ID, "expectedRevision": INTEGER, "idempotencyKey": NONEMPTY,
             "dryRun": BOOL, "operations": array(operation, 1)}),
        obj({"apiVersion": const(VERSION), "requestId": ID, "sessionId": ID, "command": enum("document.read", "layout.inspect", "diagnostics.query"),
             "documentId": ID, "revision": INTEGER}),
    ]}
    diagnostic = obj({"code": NONEMPTY, "message": TEXT, "severity": enum("info", "warning", "error")})
    response = {"oneOf": [
        obj({"apiVersion": const(VERSION), "requestId": ID, "traceId": ID, "status": const("applied"),
             "documentId": ID, "previousRevision": INTEGER, "revision": INTEGER, "undoGroupId": ID, "diagnostics": array(diagnostic)}),
        obj({"apiVersion": const(VERSION), "requestId": ID, "traceId": ID, "status": const("rejected"),
             "code": enum("STALE_REVISION", "INVALID_COMMAND", "UNSUPPORTED_CAPABILITY", "ASSET_MISSING"),
             "currentRevision": nullable(INTEGER), "diagnostics": array(diagnostic)}),
    ]}
    fixture = obj({"fixtureId": ID, "kind": enum("alphabet", "digits", "mixed-language", "kerning", "line-spacing", "color", "font-identity"),
                   "availability": enum("public-synthetic", "local-archive"), "assets": array(ASSET),
                   "fontIds": array(ID), "requirements": array(NONEMPTY, 1), "assertions": array(NONEMPTY, 1),
                   "documentPath": nullable(PATH), "notes": TEXT})
    fixtures = obj({"schemaVersion": const(VERSION), "fixtures": array(fixture, 1)})
    capabilities = obj({"schemaVersion": const(VERSION), "apiVersion": const(VERSION), "milestone": const("M0"),
                        "capabilities": array(obj({"capabilityId": ID, "status": enum("implemented", "contract-only", "planned"),
                                                   "transports": array(enum("python", "cli", "desktop", "mcp")),
                                                   "cliCommand": nullable(NONEMPTY), "milestone": enum("M0", "M1", "M2", "M3", "M4", "M5"),
                                                   "notes": TEXT}), 1)})
    schemas = {"common": common, "asset-catalog": catalog, "font-registry": fonts, "mapping": mapping,
               "document": document, "command": request, "command-result": response,
               "fixtures": fixtures, "capabilities": capabilities}
    return {name: {"$schema": DRAFT, "$id": BASE + name + ":" + VERSION,
                   "title": "Vayrshemon " + name + " " + VERSION, **schema} for name, schema in schemas.items()}


def main():
    root = Path(__file__).resolve().parents[2]
    for name, schema in definitions().items():
        write_json(root / "schemas" / (name + ".schema.json"), schema)


if __name__ == "__main__":
    main()
