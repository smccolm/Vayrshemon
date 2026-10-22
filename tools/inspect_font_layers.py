"""Read-only comparison of the three archived Thimfora color-layer fonts.

Uses only Python's standard library. This inspects selected SFNT tables; it is
not a full font validator, shaper, or proof of visual layer registration.
"""

import argparse
import hashlib
import json
import struct
from pathlib import Path


SOURCES = (
    ("outline-master", "Inputs/font files/Thimfora_79.ttf"),
    ("outer-glow", "Inputs/font files/Thimfora_80_Infill.ttf"),
    ("interior", "Inputs/font files/Thimfora_81_Fragments.ttf"),
)
TABLES_TO_COMPARE = ("cmap", "GDEF", "GPOS", "kern", "hhea", "hmtx")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def inspect_font(root, role, relative_path):
    data = (root / relative_path).read_bytes()
    if len(data) < 12 or data[:4] != b"\x00\x01\x00\x00":
        raise ValueError(f"{relative_path}: expected a TrueType SFNT file")
    table_count = struct.unpack_from(">H", data, 4)[0]
    if len(data) < 12 + table_count * 16:
        raise ValueError(f"{relative_path}: truncated SFNT directory")
    tables = {}
    for index in range(table_count):
        raw_tag, _, offset, length = struct.unpack_from(">4sIII", data, 12 + index * 16)
        tag = raw_tag.decode("ascii")
        if tag in tables or offset + length > len(data):
            raise ValueError(f"{relative_path}: duplicate or truncated table {tag}")
        tables[tag] = data[offset:offset + length]
    for tag, minimum in (("head", 54), ("hhea", 36), ("maxp", 6)):
        if len(tables.get(tag, b"")) < minimum:
            raise ValueError(f"{relative_path}: missing or truncated {tag}")
    glyph_count = struct.unpack_from(">H", tables["maxp"], 4)[0]
    metric_count = struct.unpack_from(">H", tables["hhea"], 34)[0]
    if not 1 <= metric_count <= glyph_count:
        raise ValueError(f"{relative_path}: invalid horizontal metric count")
    hmtx = tables.get("hmtx", b"")
    if len(hmtx) < metric_count * 4 + (glyph_count - metric_count) * 2:
        raise ValueError(f"{relative_path}: truncated horizontal metrics")
    metrics = [struct.unpack_from(">Hh", hmtx, i * 4) for i in range(metric_count)]
    last_advance = metrics[-1][0]
    metrics.extend(
        (last_advance, struct.unpack_from(">h", hmtx, metric_count * 4 + i * 2)[0])
        for i in range(glyph_count - metric_count)
    )
    ascender, descender, line_gap = struct.unpack_from(">hhh", tables["hhea"], 4)
    record = {
        "role": role,
        "path": relative_path,
        "bytes": len(data),
        "sha256": sha256(data),
        "glyphCount": glyph_count,
        "unitsPerEm": struct.unpack_from(">H", tables["head"], 18)[0],
        "verticalMetrics": {
            "ascender": ascender,
            "descender": descender,
            "lineGap": line_gap,
        },
        "selectedTableHashes": {
            tag: sha256(tables[tag]) if tag in tables else None
            for tag in TABLES_TO_COMPARE
        },
    }
    return record, metrics


def audit(root):
    inspected = [inspect_font(root, role, path) for role, path in SOURCES]
    master_record, master_metrics = inspected[0]
    comparisons = []
    for record, metrics in inspected[1:]:
        same_count = len(metrics) == len(master_metrics)
        comparisons.append({
            "path": record["path"],
            "sameGlyphCount": same_count,
            "sameUnitsPerEm": record["unitsPerEm"] == master_record["unitsPerEm"],
            "sameVerticalMetrics": record["verticalMetrics"] == master_record["verticalMetrics"],
            "advanceDifferences": [
                index for index, (master, layer) in enumerate(zip(master_metrics, metrics))
                if master[0] != layer[0]
            ],
            "sideBearingDifferenceCount": sum(
                master[1] != layer[1] for master, layer in zip(master_metrics, metrics)
            ),
            "identicalSelectedTables": {
                tag: record["selectedTableHashes"][tag] is not None
                and record["selectedTableHashes"][tag] == master_record["selectedTableHashes"][tag]
                for tag in TABLES_TO_COMPARE
            },
        })
    return {
        "auditSchemaVersion": 1,
        "tool": "tools/inspect_font_layers.py",
        "master": SOURCES[0][1],
        "fonts": [record for record, _ in inspected],
        "comparisonsToMaster": comparisons,
        "limitations": [
            "Does not execute shaping or validate outlines, hinting, or checksums.",
            "Matching tables and advances do not prove visual layer registration.",
            "Side-bearing differences can reflect intentional layer geometry.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    print(json.dumps(audit(args.root.resolve()), indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
