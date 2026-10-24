# Standard parallel translation page

**Approved left page, 2026-10-24:** use **50 pt Thimfora** in its left column and **22 pt transliteration 7** in its right column, both on **38 pt baselines**, with 24 pt paragraph-after spacing and measured paired paragraph starts. Keep the exact enlarged page, margins, Maxima, black paper and independent script/Roman bevel and glow. This supersedes the 28 pt trial and the earlier 18 pt Roman setting for new transliteration readings. The [left-page reference](../data/formatting/approved-left-page-20261024.json) records immutable state, font, geometry and pixel hashes; the older English baseline remains intact.

In facing view, the right page uses the same page/frame geometry. **M13 fills its formerly reserved left column with the abbreviated construction gloss**, in source order, and retains natural English in the far-right column. Both use transliteration 7 at **22 pt / 38 pt** with the Roman relief profile. The source facing template keeps its blank column; the gloss is created in a separate copy. English words, punctuation and paragraph boundaries remain exact. Explicit unsupported or repurposed punctuation slots use Times New Roman with the same Roman relief. Paragraphs align where space permits; longer gloss paragraphs may start later, with measured delays recorded, rather than changing the protected columns. See [M13](M13.md).

The bottom action bar has a 190 px zoom slider followed by icon-only one-page and two-page controls. Tooltips and accessible names identify the controls. One-page mode shows the selected page; two-page mode shows consecutive pairs (1–2, 3–4, …), including an unpaired final page. The view preference persists separately from document state. Fit Width fits the visible pair, centers it horizontally and aligns its top below the ruler; Fit Height fits its tallest page. Click either page's frame to edit it. PNG/SVG export still targets the selected physical page; PDF includes all pages.

**Current approved demo, 2026-10-23:** the user explicitly approved the enlarged page's font size, dimensions, margins and font quality. Use the [M6.1 visual baseline](M6.1.md#approved-reference) for new workbench demonstrations and appearance-preservation checks. Its page is 865.498700 × 1120.057141 pt, with proportionally enlarged frames/margins and preserved 50 pt script / 18 pt English. The original standard below remains an additional regression fixture. Historical notes about pending page approval below describe the earlier milestones; they do not revoke this later acceptance.

**Requested M12 reading variant:** Thimfora remains on the left; the user-selected original transliteration 7 font displays identical symbol slots and Maxima/Minima on the right. Literal Times New Roman slots remain an optional view. Only the right-column font changes; page/frame geometry, sizes, leading, pale text, black paper and the approved three-font treatment remain. Paragraph starts are measured anew. This variant does not replace the approved English baseline or its hashes. See [M12](M12.md) for exact text preservation and the recorded 0.046875 pt Roman `p` sidebearing overhang.

**Subsequent reading refinements:** the Roman column now has its independent archived bevel/glow treatment. The user's larger-text request adds a separate legibility specimen at **28 pt Roman / 36 pt leading**, retaining **50 pt Thimfora / 38 pt leading**, exact page/frame geometry and paint. Its longer, four-paragraph literary text uses about 86% / 92% of the two frame heights after paragraph-start alignment. This editable specimen does not alter the frozen English baseline or the baseline-sized Forge runner. See the [legibility evidence](research/m12-reading-legibility.json) for provenance and remaining ink-overhang diagnostics.

Approved by the user on 2026-10-22. Standard `format.parallel-translation`, revision **1.0.0**, is the default bilingual formatting and a required regression scenario for future editor milestones. Its machine-readable definition is [parallel-translation.json](../data/formatting/parallel-translation.json).

The page contains **exactly two independent, editable text columns**: Vayrshemon on the left and the corresponding English translation on the right. Use the page height for those columns. There is no title frame, column-heading frame, or footer. Do not link the Vayrshemon story into the English column as a continuation.

**This approval covers layout, not final rendering quality.** The user explicitly identified the current glyph appearance as below expectations. `Inputs/Versions Best/Individual Glyphs` is the visual target for the [M4 VISUAL-01 requirement](PLAN.md#m4--color-font-studio-and-publishing). Future color/effect work must meet that reference quality on this same two-column page; the present monochrome specimen is a structural regression baseline only.

| Measurement | Points |
| --- | ---: |
| Portrait page width × height | 612 × 792 |
| Top / bottom margins | 42 / 48 |
| Left / right margins | 48 / 48 |
| Left column x / y | 48 / 42 |
| Right column x / y | 324 / 42 |
| Each column width × height | 240 × 702 |
| Gutter | 36 |

Corresponding paragraphs begin on matching baselines. Each language wraps independently; a longer passage in one language must not cause source text to be duplicated, discarded, or reassigned to the other language. Page dimensions remain editable; this standard does not remove arbitrary page sizing or prescribe the layout of English-only or Vayrshemon-only documents.

## Reference specimen

Use the two paired examples in `Inputs/Versions Best/Polished Examples.docx`: source paragraphs 0 and 17 with English paragraphs 4 and 21 (zero-based). These are the “I am many. We are one.” and blue-jewel passages. The source hash and original `test seven` / `transliteration 5` font hashes are pinned in the definition. Preserve the source's exceptional transliteration-font run as well as the script runs. Do not reinterpret this older text using the Thimfora 79 mapping, fabricate additional language, or repeat passages just to fill space.

The accepted specimen uses 31 pt script with exact 38 pt leading and 18 pt English with exact 30 pt leading, 24 pt paragraph-after spacing, and additional before-spacing to align paired paragraph starts. It uses monochrome outlines (blue script and dark English), no baseline grid, and collision warnings. These are reference typography values for these fonts; new fonts and longer passages may need explicit adjustments while retaining the two-column arrangement.

The approved editable document remains local at `.local/demos/portrait-translation-20261022/Vayrshemon-English-portrait.vay.json`. Originals and generated documents/proofs remain ignored. The public definition contains provenance and layout, not the source passages or fonts.

For Individual Glyphs color review, the user's 2026-10-23 correction requires the actual Thimfora 79/81/80 family. Use the separate [layered review definition](../data/formatting/parallel-translation-layered.json), built by `tools.layered_translation_fixture`. It retains these page/frame dimensions and paired passages, explicitly adapts the old clitic slot using the archived layered example, and records conversion provenance. Its 50 pt master font has different outlines and metrics, so line wrapping and paired spacing are measured anew. This color copy does not replace the unchanged archival fixture or imply visual approval.

For the requested bevel/glow review, use black paper (`#FF000000`, ARGB) and pale English (`#E4E9F0FF`, RGBA). The current reference recipe is `individual-glyphs-1`. This presentation makes the translucent glow visible while retaining the same two editable columns and attested passages. `python -m tools.verify_m4 --black` creates this saved native demo and black PNG/SVG/PDF proofs, with a separate white-paper comparison.

## Repeatable acceptance test

Run `.venv\Scripts\python -m unittest discover -s tests -p test_parallel_translation.py -v`. Normal full-suite discovery, including setup.bat, also runs this test; there are no new dependencies.

The public case uses clearly synthetic text and a generated font, so CI can verify portrait dimensions, two full-height independent columns, paired paragraph baselines, independent edits and undo, and semantic/geometry preservation across save/reopen and PNG export without Inputs. The local case reconstructs the actual source pairs with hash-checked original fonts and records its saved document, PNG, layout diagnostics, and source provenance in a fresh `.local/test-parallel-translation/` directory. It skips only when required local files are absent; mismatched source hashes fail.

For authoring, typography, font, persistence, and export changes, run the public case; run the real source case whenever Inputs is available and visually inspect its proof when rendering changes. Use this scenario in future live demos as well as the existing stress fixtures.

## Current limits to retain in reports

M3 stores paragraph-start alignment as explicit paragraph spacing. It is not yet an automatic semantic source/translation pairing feature; editing either column can require realignment. The test fixture performs that alignment through existing APIs, not through a new application command.

The approved Windows specimen has a small natural left ink overhang: the original script glyph at source UTF-16 offset 80 extends about 0.70 pt beyond its frame. The glyph remains visible and all text fits vertically, but M3 reports `FRAME_OVERFLOW`. Retain and inspect this diagnostic; do not claim a zero-overflow baseline, silently clip the glyph, or rewrite the source to hide it. System English font metrics can vary across platforms, so alignment is measured rather than copied from a platform-specific pixel golden.
