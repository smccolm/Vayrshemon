# Inputs archive: findings for the editor

Reviewed 2026-10-22. This is an engineering evidence summary, not a declaration that every historical language decision is canonical. All source paths below are relative to the ignored `Inputs/` directory. Original files were left unchanged.

## 1. Scope and limitations

The archive contains **1,506 files, 9,498,822,127 bytes** (approximately 9.5 GB), including **103 TTF fonts**. It contains fonts and FontLab sources, design masters, raster exports, keyboard artwork, kerning material, language charts, and Word documents. No application source code was found.

Review covered the file inventory, font table/name metadata and specimens, readable document contents, raster images, Illustrator PDF previews, and embedded Photoshop previews. There are 31 substantive DOCX documents plus three Word lock files, three legacy DOC files, six plain-text files, and one XPS document. Native FontLab and InDesign project internals were not fully decoded; a preview is not a complete inspection of every editable design layer. Exact duplicates were grouped rather than treated as independent revisions.

The previous review's extracted documents and contact sheets are local research artifacts outside the repository. M0 now includes a reproducible [catalog](../data/assets.json) with hashes for all 1,506 files and explicit relationship certainty. Same-stem relationships are candidates, not proof of derivation. A separate archive backup has not been configured.

## 2. Legacy text is font-dependent

The Thimfora and transliteration fonts reuse Latin/extended character positions. Plain text extracted without the correct font can look like unrelated Latin characters. That is not sufficient evidence of corruption.

Implications:

- Import the original character codes together with the source font identity and run boundaries.
- Define mappings per font/orthography revision; do not assume all Thimfora versions encode the same inventory.
- Preserve unresolved positions and conflicting interpretations. Generic Unicode normalization and case conversion can destroy legacy distinctions.
- Build semantic copy/search/transliteration from verified mappings rather than exposing the legacy slot values as if they were the language's spelling.

Primary mapping references include `Origins_2_Thimfora_2.jpg`, `Thimfora 79 - Full Set - 1.docx`, `Thimfora 79 - Full Set - 2.docx`, `Versions Best/Instructions - Venik.docx`, the older Thatus instructions, and `Transliteration 7 - Decimal.jpg`.

The reviewed alphabet chart presents **47 letters** with maxima/minima forms. The numeric material presents **12 Unta digits**. These are the initial inventory to transcribe and verify, not grounds to assume every older font or chart is equivalent.

## 3. The existing color lettering is a three-font composition

Source: `font files/How to Make High Quality Color Text with Photoshop.txt` and the matching artwork.

| Paint order | Source font | Role described in the archived workflow |
| --- | --- | --- |
| Top | `font files/Thimfora_79.ttf` | Master outline: light blue ridge, fine black edge, subtle shadow |
| Middle | `font files/Thimfora_81_Fragments.ttf` | Interior dark-blue ridge, darkening toward its base |
| Bottom | `font files/Thimfora_80_Infill.ttf` | Outer glow; the filename reflects an earlier intended role |

The original process duplicates a master text layer, changes layer fonts, creates paths, and applies Photoshop effects. It also describes a special boolean treatment for the interior subpaths. The editor must investigate contour fill rules and preserve the intended shape rather than blindly reproducing that raster workflow.

The [repeatable audit](research/font-layer-audit.json), produced by [inspect_font_layers.py](../tools/inspect_font_layers.py), checks the actual three source files:

- Each has 123 glyphs and 1,000 units per em.
- `cmap`, `GDEF`, `GPOS`, and legacy `kern` table bytes match across all three.
- Horizontal advances match for every glyph. Basic ascender, descender, and line-gap values also match.
- Interior-layer side bearings differ from the master. Its complete `hmtx`/`hhea` tables therefore differ despite shared advances and basic vertical metrics.

This supports a master-shaped, shared-origin composition. It does **not** prove every contour is correctly registered or that hinting/effects agree at all sizes. M1 must overlay actual glyphs and compare them against the reference art. Do not “repair” the side bearings merely to make the tables equal.

The ordinary TTF outlines are the source material. A portable color font and an editable editor paint recipe are new derived artifacts that still need to be built and verified.

## 4. Font identity and history

Font generations include named early revisions, numbered Thimfora revisions through 79, then the 80/81 layers, and multiple transliteration versions. Sources include `.vfb` and `.bak` as well as exported `.ttf` files.

`Versions Rough/Thimfora Barim Aug 10 2011.ttf` and `Versions Rough/Thimfora Venik July 16 2011.ttf` both report the internal family name **Thimfora Venik**. Filename, family name, glyph inventory, and semantic encoding are distinct facts. Load fonts by file content identity and face index, not family name alone.

The selected 79/80/81 fonts contain both GPOS and legacy kerning data. Preserve the engine's shaping result and test feature behavior; adding another kerning pass could apply spacing twice.

## 5. Language material and useful fixtures

| Sources | What they contribute | Editor/workbench use |
| --- | --- | --- |
| `Origins_2_Thimfora_2.jpg` and full-set DOCX files | Letter forms, names, transliteration and slot references | Verified input map, alphabet specimen, case/form mapping |
| `Origins_3_Unta_2.jpg`, `Unta - Base 12.jpg` | Numerals and base-12 place-value conventions | Exact numeric model and formatting fixtures |
| `Origins_6_Pronoun_Chart.jpg` | Pronoun distinctions and multiple grammatical roles | Structured paradigms with source provenance |
| `Origins_7_Table_of_Correlatives.jpg` | Correlative categories, populated and unfilled cells | Preserve unknown data; table and grammar-model examples |
| `Origins_8_Aspect.jpg`, `Origins_5_Hadthem_Verb_Tense.bmp` | Tense/aspect material | Separate grammatical features rather than infer from typography |
| `Inventory of Clitics.jpg` | Clitic categories and grammatical markings | Mark placement, analysis links, and dense-layout fixtures |
| `Versions Best/Translation Chart.docx`, `Versions Best/Translation Chart 1.docx` | Evolving bilingual lexical material | Lexicon import with version/ambiguity tracking |
| `Versions Best/Polished Examples.docx` | English, script, transliteration and gloss examples | First realistic mixed-language editing and publishing fixtures |
| `Kerning/`, rough kerning sequences and test texts | Pair spacing and dense specimens | Glyph-position and collision regression corpus |
| `New_Keyboard_5.png`, `Versions Best/Small/` | Custom keyboard layouts and states | Input palette and physical-key mapping design |

There are discrepancies between revisions. For example, the reviewed Hadthem DOCX has a future-suffix inconsistency relative to its script row and XPS/exported counterpart. Record that conflict when transcribing the rule; do not silently choose a reading and rewrite the source. Older numeral names and transliterations also vary.

Green knotwork, blue relief lettering, dark backgrounds, and keyboard artwork can inform the editor's preview/style library. They should remain source references until a specific asset or reproducible style is selected for use.

## 6. Import priorities

1. Verify the current alphabet/numeral mapping and the three-font glyph registration.
2. Preserve one representative mixed-language DOCX as a source fixture and import it with font runs intact.
3. Turn the existing pair sequences into measurable spacing fixtures.
4. Transcribe the first lexical/grammar records with explicit source links and unresolved fields.
5. Expand to historical font revisions and native design formats only after the current pipeline is reliable.

Keep all original Inputs ignored. Track source hashes, mappings, recipes, inspection tools, and deliberately selected regression definitions. Avoid treating modification dates, filename numbers, or duplicate copies as sufficient evidence that a linguistic decision supersedes another.
