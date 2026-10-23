# Vayrshemon interchange and offline recovery

| Artifact | Retains | Does not provide |
| --- | --- | --- |
| Native `*.vay.json`, format 0.5.0 | Stable page/frame/run IDs; exact Unicode/legacy source slots; UTF-16 ranges; style/font hashes; paint; typesetting; language revision graph; corpus links | Font bytes (ordinary native files use exact hash/path references) |
| `*.vaybackup`, format 1.0.0 | Exact native bytes, declared font bytes, sizes/hashes and provenance manifest | Whole Inputs archive, external audio files, installed system fonts or dependency runtime |
| Language JSON package, format 1.0.0 | Selected language dataset, original citations/uncertainty, typed records and hash manifest | Full native page layout and old retained revision graph |
| Offline `text --out` JSON | Exact blocks/runs and their legacy/Unicode metadata, separated by page/frame | Guessed decoding, normalization, reconstruction of decorative effects |
| PNG | Pixel proof and resolution metadata | Editable or searchable semantic text |
| SVG | Outline proof or explicitly declared raster image at chosen DPI | Guaranteed semantic text; bevel/glow stay rasterized |
| PDF | Physical page dimensions and outline/raster appearance | Searchable/copyable text, semantic tagging or full font embedding |
| Dictionary/grammar/corpus HTML | Escaped printable records and source citations | A native editable document or embedded private fonts |

Micro-point integer strings express stored page/frame dimensions. Layout reports use logical pixels at 96 DPI; API geometry configuration uses points unless its schema specifies another unit. Page dimensions are independent of raster export limits.

Native editing ranges use **UTF-16 code units** and reject surrogate/grapheme splits. Corpus token offsets use **Unicode scalar indices**. Do not interchange these units. Legacy font slots retain original codepoints, font identities and mapping/provenance records. A glyph shape is not a reliable transliteration or language identification.

Use `tools/recovery.py` with `python -S` when the editor cannot start. `inspect` validates basic structure and reports versions, counts, font references and hash; it does not claim full semantic validity. `text` creates a new JSON file without rewriting its source. `verify` checks all backup members. `restore` requires a new directory, preserves the original exact file and only relocates font paths in a separate recovered copy. The editor then performs its full validation. Recovery never invents missing glyphs, normalizes spelling or silently substitutes source fonts.

M1–M4 imports retain the existing migration policy: read originals and save a new format/path. M5 and M6 share native 0.5.0 and language package 1.0.0. Release rollback changes application selection, not documents. Keep native files and verified backups as authoritative sources; exported visual proofs are not document backups.
