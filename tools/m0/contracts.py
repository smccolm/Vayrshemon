"""Offline schema validation plus invariants JSON Schema cannot express."""

from collections import Counter
from pathlib import Path
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from .common import asset_id, load_json
from .mapping import build_mapping
from .schema_definitions import definitions


def validators(root):
    schemas = {path.name.removesuffix(".schema.json"): load_json(path) for path in (root / "schemas").glob("*.schema.json")}
    registry = Registry().with_resources((schema["$id"], Resource.from_contents(schema)) for schema in schemas.values())
    result = {}
    for name, schema in schemas.items():
        Draft202012Validator.check_schema(schema)
        result[name] = Draft202012Validator(schema, registry=registry)
    return result


def validate_document_semantics(document):
    issues = []
    ids = []
    fonts = {font["fontId"] for font in document["fonts"]}
    styles = {style["styleId"] for style in document["styles"]}
    stories = {story["storyId"] for story in document["stories"]}
    for font in document["fonts"]:
        ids.append(font["fontId"])
        if font["fontId"] != f"font:{font['sha256']}:{font['faceIndex']}":
            issues.append("FONT_ID_HASH_MISMATCH")
    for style in document["styles"]:
        ids.append(style["styleId"])
        if style["fontId"] is not None and style["fontId"] not in fonts:
            issues.append("STYLE_FONT_REFERENCE_MISSING")
    for page in document["pages"]:
        ids.append(page["pageId"])
        margins = page["marginsMicroPoints"]
        if int(margins["left"]) + int(margins["right"]) >= int(page["widthMicroPoints"]) or int(margins["top"]) + int(margins["bottom"]) >= int(page["heightMicroPoints"]):
            issues.append("PAGE_MARGINS_LEAVE_NO_CONTENT")
        for frame in page["frames"]:
            ids.append(frame["frameId"])
            if frame["storyId"] not in stories:
                issues.append("FRAME_STORY_REFERENCE_MISSING")
    for story in document["stories"]:
        ids.append(story["storyId"])
        for block in story["blocks"]:
            ids.append(block["blockId"])
            for run in block["runs"]:
                ids.append(run["runId"])
                if run["styleId"] not in styles:
                    issues.append("RUN_STYLE_REFERENCE_MISSING")
    if len(set(ids)) != len(ids):
        issues.append("DUPLICATE_DOCUMENT_ENTITY_ID")

    def walk(value, key=""):
        if isinstance(value, dict):
            for child_key, child in value.items():
                walk(child, child_key)
        elif isinstance(value, list):
            for child in value:
                walk(child, key)
        elif isinstance(value, str):
            if "MicroPoints" in key or key in ("top", "right", "bottom", "left", "microPoints"):
                if not -(2**63) <= int(value) <= 2**63 - 1:
                    issues.append("DIMENSION_OUT_OF_INT64_RANGE")
            if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
                issues.append("INVALID_UNICODE_SCALAR")
    walk(document)
    return sorted(set(issues))


def check_repository(root):
    root = Path(root)
    checks = validators(root)
    issues, checked = [], []
    for name, expected in definitions().items():
        if load_json(root / "schemas" / (name + ".schema.json")) != expected:
            issues.append("STALE_GENERATED_SCHEMA: " + name)
    bindings = {"data/assets.json": "asset-catalog", "data/fonts.json": "font-registry",
                "data/orthography/thimfora-79.json": "mapping", "data/fixtures.json": "fixtures", "data/capabilities.json": "capabilities"}
    for path in sorted((root / "tests/fixtures/documents").glob("*.json")):
        bindings[path.relative_to(root).as_posix()] = "document"
    for path in sorted((root / "tests/fixtures/commands").glob("*.json")):
        bindings[path.relative_to(root).as_posix()] = "command-result" if path.name.endswith("-result.json") else "command"
    for relative, schema in bindings.items():
        value = load_json(root / relative)
        failures = list(checks[schema].iter_errors(value))
        for error in failures:
            issues.append(f"SCHEMA: {relative} {list(error.absolute_path)} {error.message[:160]}")
        if schema == "document" and not failures:
            issues.extend(f"DOCUMENT: {relative}: {code}" for code in validate_document_semantics(value))
        checked.append(relative)
    if issues:
        return {"ok": False, "checked": checked, "issues": issues}
    catalog = load_json(root / "data/assets.json")
    fonts = load_json(root / "data/fonts.json")
    mapping = load_json(root / "data/orthography/thimfora-79.json")
    assets = {asset["assetId"]: asset for asset in catalog["assets"]}
    by_path = {asset["path"]: asset for asset in catalog["assets"]}
    if len(assets) != len(catalog["assets"]) or len(by_path) != len(catalog["assets"]):
        issues.append("DUPLICATE_ASSET_ID_OR_PATH")
    if any(asset_id(asset["path"]) != asset["assetId"] for asset in assets.values()):
        issues.append("ASSET_ID_PATH_MISMATCH")
    if catalog["summary"] != {"fileCount": len(assets), "totalBytes": sum(a["bytes"] for a in assets.values()),
                              "extensions": dict(sorted(Counter(a["extension"] for a in assets.values()).items()))}:
        issues.append("CATALOG_SUMMARY_MISMATCH")

    def check_ref(reference):
        actual = assets.get(reference["assetId"])
        if actual is None or any(actual[key] != reference[key] for key in ("path", "sha256")):
            issues.append("ASSET_REFERENCE_MISMATCH: " + reference["path"])
    for relation in catalog["relationships"]:
        if any(identity not in assets for identity in relation["assetIds"]):
            issues.append("RELATIONSHIP_REFERENCE_MISSING")
        if relation.get("evidenceAssetId") not in (None, *assets):
            issues.append("RELATIONSHIP_EVIDENCE_MISSING")
        if relation["type"] == "identical-content" and any(assets[identity]["sha256"] != relation["sha256"] for identity in relation["assetIds"] if identity in assets):
            issues.append("DUPLICATE_CONTENT_HASH_MISMATCH")
    for font in fonts["fonts"]:
        check_ref(font["asset"])
        if font["fontId"] != f"font:{font['asset']['sha256']}:{font['faceIndex']}":
            issues.append("FONT_ID_HASH_MISMATCH")
        if len({item["scalar"] for item in font["coverage"]}) != len(font["coverage"]):
            issues.append("DUPLICATE_FONT_CMAP_SCALAR")
        if any(item["glyphId"] >= font["glyphCount"] for item in font["coverage"]):
            issues.append("INVALID_GLYPH_ID")
    expected_mapping = build_mapping(load_json(root / "data/orthography/chart-transcription.json"), fonts, catalog)
    if mapping != expected_mapping:
        issues.append("STALE_OR_INCONSISTENT_MAPPING")
    known_fonts = {font["fontId"] for font in fonts["fonts"]}
    for fixture in load_json(root / "data/fixtures.json")["fixtures"]:
        for reference in fixture["assets"]:
            check_ref(reference)
        if any(font not in known_fonts for font in fixture["fontIds"]):
            issues.append("FIXTURE_FONT_REFERENCE_MISSING")
        if fixture["documentPath"] and not (root / fixture["documentPath"]).is_file():
            issues.append("FIXTURE_DOCUMENT_MISSING")
    requirements = load_json(root / "data/requirements.json")["requirements"]
    requirement_ids = {item["id"] for item in requirements}
    if len(requirement_ids) != len(requirements):
        issues.append("DUPLICATE_REQUIREMENT_ID")
    for requirement in requirements:
        for relative in requirement["evidence"]:
            if not (root / relative).is_file():
                issues.append("REQUIREMENT_EVIDENCE_MISSING: " + relative)
    for fixture in load_json(root / "data/fixtures.json")["fixtures"]:
        if any(identity not in requirement_ids for identity in fixture["requirements"]):
            issues.append("FIXTURE_REQUIREMENT_MISSING")
    decisions = load_json(root / "data/decisions.json")["decisions"]
    if len({item["id"] for item in decisions}) != len(decisions):
        issues.append("DUPLICATE_DECISION_ID")
    return {"ok": not issues, "checked": checked, "issues": issues,
            "counts": {"assets": len(assets), "fonts": len(fonts["fonts"]), "mappedSlots": sum(e["status"] == "mapped" for e in mapping["entries"]),
                       "unresolvedSlots": sum(e["status"] == "unresolved" for e in mapping["entries"])}}
