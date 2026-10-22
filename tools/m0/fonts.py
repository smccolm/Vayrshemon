"""File-scoped font identities and explicit cmap/metric inspection."""

from collections import defaultdict
import hashlib
from fontTools.ttLib import TTFont

from .common import confined_path, file_hash


def inspect_font(path, asset):
    if file_hash(path) != asset["sha256"]:
        raise ValueError("FONT_HASH_MISMATCH: " + asset["path"])
    with TTFont(path, lazy=False, recalcBBoxes=False, recalcTimestamp=False) as font:
        names = {}
        for name_id, label in ((1, "family"), (2, "subfamily"), (4, "fullName"), (5, "version"), (6, "postscriptName")):
            record = font["name"].getDebugName(name_id)
            names[label] = record
        cmap = font.getBestCmap() or {}
        order = font.getGlyphOrder()
        encoded = set(cmap.values())
        coverage = []
        for scalar, glyph_name in sorted(cmap.items()):
            advance, lsb = font["hmtx"].metrics[glyph_name]
            coverage.append({"scalar": scalar, "glyphId": font.getGlyphID(glyph_name),
                             "glyphName": glyph_name, "advance": advance, "leftSideBearing": lsb})
        return {
            "fontId": "font:" + asset["sha256"] + ":0", "faceIndex": 0,
            "asset": {key: asset[key] for key in ("assetId", "path", "sha256")},
            "names": names, "glyphCount": len(order), "unitsPerEm": font["head"].unitsPerEm,
            "verticalMetrics": {"ascender": font["hhea"].ascent, "descender": font["hhea"].descent,
                                "lineGap": font["hhea"].lineGap},
            "embeddingFlags": font["OS/2"].fsType if "OS/2" in font else None,
            "tableTags": sorted(str(tag) for tag in font.reader.keys()),
            "tableHashes": {str(tag): hashlib.sha256(font.reader[tag]).hexdigest() for tag in sorted(font.reader.keys())},
            "cmapSelection": "fontTools.getBestCmap", "coverage": coverage,
            "unencodedGlyphs": [{"glyphId": i, "glyphName": name} for i, name in enumerate(order) if name not in encoded],
            "mappingStatus": "unreviewed", "mappingProfileIds": [],
        }


def font_registry(archive, catalog, progress=lambda **event: None):
    from .mapping import LAYER_PATHS
    fonts = []
    for asset in catalog["assets"]:
        if asset["extension"] == ".ttf":
            record = inspect_font(confined_path(archive, asset["path"]), asset)
            if asset["path"] in LAYER_PATHS:
                record["mappingStatus"] = "chart-mapped"
                record["mappingProfileIds"] = ["thimfora-79.chart-2"]
            fonts.append(record)
    groups = defaultdict(list)
    for font in fonts:
        groups[(font["names"]["family"] or "").casefold()].append(font)
    collisions = []
    for family, members in sorted(groups.items()):
        if len({font["fontId"] for font in members}) > 1:
            collisions.append({"familyKey": family, "fontIds": sorted({font["fontId"] for font in members}),
                               "paths": [font["asset"]["path"] for font in members]})
    progress(code="FONT_REGISTRY_COMPLETE", files=len(fonts), familyCollisions=len(collisions))
    return {"schemaVersion": "0.1.0", "fonts": fonts, "familyCollisions": collisions}
