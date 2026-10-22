"""Build and consume evidence-bound mappings without normalizing source text."""

from .common import asset_ref


LAYER_PATHS = (
    "font files/Thimfora_79.ttf", "font files/Thimfora_80_Infill.ttf",
    "font files/Thimfora_81_Fragments.ttf",
)


def build_mapping(chart, registry, catalog):
    if len(chart["letters"]) != 47 or len(chart["numerals"]) != 12:
        raise ValueError("INCOMPLETE_CHART")
    master = next(font for font in registry["fonts"] if font["asset"]["path"] == LAYER_PATHS[0])
    coverage = {item["scalar"]: item for item in master["coverage"]}
    entries, inventory = [], []
    alphabet_evidence = asset_ref(catalog, chart["alphabetSource"])
    digit_evidence = asset_ref(catalog, chart["numeralSource"])
    unresolved = {item["ordinal"]: item["reason"] for item in chart["unresolvedTransliterations"]}
    for ordinal, maxima, minima, name, max_label, min_label in chart["letters"]:
        symbol_id = f"thimfora.letter.{ordinal:03d}"
        locator = f"{'left' if ordinal <= 24 else 'right'} column, row {ordinal if ordinal <= 24 else ordinal - 24}"
        evidence = [{"asset": alphabet_evidence, "locator": locator, "method": "visual-chart-transcription"}]
        inventory.append({"symbolId": symbol_id, "kind": "letter", "ordinal": ordinal,
                          "nameTranscription": name, "nameConfidence": "medium",
                          "transliterationStatus": "unresolved" if ordinal in unresolved else "transcribed",
                          "transliterationNote": unresolved.get(ordinal), "evidence": evidence})
        for form, scalar, label in (("maxima", maxima, max_label), ("minima", minima, min_label)):
            entries.append({"scalar": scalar, "symbolId": symbol_id, "form": form,
                            "kind": "letter", "status": "mapped", "confidence": "high",
                            "transliteration": label, "evidence": evidence, "unresolvedReason": None})
    for value, scalar, name in chart["numerals"]:
        symbol_id = f"unta.digit.{value:02d}"
        evidence = [{"asset": digit_evidence, "locator": f"row {value + 1}; decimal slot {scalar:04d}",
                     "method": "visual-chart-transcription"}]
        inventory.append({"symbolId": symbol_id, "kind": "digit", "value": value,
                          "nameTranscription": name, "nameConfidence": "high", "evidence": evidence})
        entries.append({"scalar": scalar, "symbolId": symbol_id, "form": "default", "kind": "digit",
                        "status": "mapped", "confidence": "high", "transliteration": None,
                        "evidence": evidence, "unresolvedReason": None})
    used = {entry["scalar"] for entry in entries}
    for scalar in sorted(set(coverage) - used):
        space = scalar in (32, 160)
        entries.append({"scalar": scalar,
                        "symbolId": ("separator.space" if scalar == 32 else "separator.no-break-space") if space else None,
                        "form": "default", "kind": "separator" if space else "punctuation",
                        "status": "mapped" if space else "unresolved", "confidence": "high" if space else "low",
                        "transliteration": None,
                        "evidence": [{"asset": master["asset"], "locator": f"cmap scalar U+{scalar:04X}",
                                      "method": "font-table-inspection"}],
                        "unresolvedReason": None if space else "Glyph and legacy slot are known; linguistic function is not verified. Glyph names are hints only."})
    if len({entry["scalar"] for entry in entries}) != len(entries):
        raise ValueError("DUPLICATE_LEGACY_SLOT")
    for entry in entries:
        if entry["scalar"] not in coverage:
            raise ValueError("CHART_SLOT_MISSING_FROM_FONT")
        entry["glyphId"] = coverage[entry["scalar"]]["glyphId"]
        entry["glyphNameHint"] = coverage[entry["scalar"]]["glyphName"]
    supported = [font for font in registry["fonts"] if font["asset"]["path"] in LAYER_PATHS]
    if len(supported) != 3:
        raise ValueError("COLOR_LAYER_FONT_MISSING")
    for font in supported:
        if {c["scalar"]: c["glyphId"] for c in font["coverage"]} != {c["scalar"]: c["glyphId"] for c in master["coverage"]}:
            raise ValueError("LAYER_CMAP_MISMATCH")
    return {"schemaVersion": "0.1.0", "profileId": "thimfora-79.chart-2", "revision": "0.1.0",
            "normalization": "none", "offsetUnit": "unicode-scalar", "unknownPolicy": "preserve",
            "fontSha256s": sorted(font["asset"]["sha256"] for font in supported),
            "inventory": inventory, "entries": sorted(entries, key=lambda entry: entry["scalar"])}


def decode_legacy(text, profile, font_sha256):
    if font_sha256 not in profile["fontSha256s"]:
        raise ValueError("MAPPING_FONT_MISMATCH")
    lookup = {entry["scalar"]: entry for entry in profile["entries"]}
    if len(lookup) != len(profile["entries"]):
        raise ValueError("DUPLICATE_LEGACY_SLOT")
    units, diagnostics = [], []
    for offset, character in enumerate(text):
        scalar = ord(character)
        if 0xD800 <= scalar <= 0xDFFF:
            raise ValueError("INVALID_UNICODE_SCALAR")
        entry = lookup.get(scalar)
        known = entry is not None and entry["status"] == "mapped"
        units.append({"offset": offset, "sourceScalar": scalar, "status": "mapped" if known else "unresolved",
                      "symbolId": entry["symbolId"] if known else None,
                      "form": entry["form"] if known else None,
                      "glyphId": entry["glyphId"] if entry else None})
        if not known:
            diagnostics.append({"code": "UNRESOLVED_SEMANTICS" if entry else "UNMAPPED_SCALAR",
                                "offset": offset, "sourceScalar": scalar})
    return {"schemaVersion": "0.1.0", "profileId": profile["profileId"], "profileRevision": profile["revision"],
            "fontSha256": font_sha256, "offsetUnit": "unicode-scalar", "originalText": text,
            "units": units, "diagnostics": diagnostics}


def restore_legacy(decoded):
    restored = "".join(chr(unit["sourceScalar"]) for unit in decoded["units"])
    if restored != decoded["originalText"]:
        raise ValueError("LEGACY_ROUNDTRIP_MISMATCH")
    return restored
