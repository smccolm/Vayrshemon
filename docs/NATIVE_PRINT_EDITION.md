# Complete native Letter Bible

## Compact edition

The user requested a second, complete edition limited to **1,000 duplex sheets / 2,000 pages**, including artwork and intentional blanks. `python -m tools.kjv_print_edition --compact` writes to a separate `Saves/KJV Bible - Compact Letter Edition v0.10-kjv.280/` folder and refuses to replace existing editions. The first 26/19 pt trial exceeded the cap at 2,048 pages and was not published.

The verified compact file contains **1,952 pages / 976 sheets**, a **3.904-inch paper stack** at the user's 0.004 inches per sheet. All 31,102 verse hashes, all page layouts and folio placements, and save/reopen identity pass. Native SHA256: `5476263866d34b96aff0be3d747542c33a17fa396f9da2c6b06700f985862c16`. It opens in the 0.15.34 Workbench in two-page black-on-white view; 17 targeted native, print-proof, parallel-formatting, storage and loading regressions pass.

The compact `letter-compact.1` profile retains 26 pt Thimfora with exact 18 pt leading, 18 pt Unta verse markers and 2 pt verse spacing. The title/frontispiece, all 66 illuminated openings, 45/27 pt inside/outside margins, mirrored 9 pt shifts and 50 pt folios at a 28 pt inset remain. Native profile metadata drives preview, PNG, SVG and PDF consistently; missing or altered compact typography is rejected, as are files exceeding 2,000 pages. Original `letter-native.1` files retain their 36/28 pt defaults without migration.

The page limit concerns the paper stack: sheets × 0.004 inches. Covers, sewing and glue are additional. Text and language are not shortened or modernized. All 31,102 frozen verse hashes must match before the compact file is saved.

## Original Letter edition

Delivered native edition: `Saves/KJV Bible - Letter Edition v0.10-kjv.280/KJV Bible - Vayrshemon Letter Edition.vay`, **3,818 pages / 31,102 verses / 66 books**, approximately 18 MB. Native SHA256: `767516a219b6e0c6e754259ac9df2e4e0f44eb2c235c48224cc21853f11c61f5`. Its folder contains the edition manifest, verification report, opening/body preview spreads and a 66-book page index. The updated Workbench successfully opened the full file and displayed live paired-page navigation.

The complete Vayrshemon-only publication derives from the supplied artwork and Letter print proof, using all 31,102 exact verse texts from the hash-pinned `0.10-kjv.280` ledger. It is a distinct edition, not a modernization or replacement of the four-column historical Bible.

The requested new order is **Title | Blank**, **Frontispiece | Genesis opening**. Each later book also starts on the right of a Workbench spread, adding a blank when needed. The title is centered. All following left/right pages use -9/+9 pt center offsets, with 45 pt inside and 27 pt outside margins. These sides follow the requested native paired arrangement. This order supersedes the previous PDF reading/printing companions; physical sheet/cover assembly must be considered when preparing the eventual bound print run.

The file opens in two-page mode with black ink on white Letter paper. Text uses the original 36 pt Thimfora master outlines at exact 28 pt leading, with 24 pt Unta verse markers. Body folio 1 begins at Genesis; folios count intervening pages, suppress ink on deliberate blanks, and use 50 pt Unta at a preferred 28 pt bottom/outside inset. Every placement is checked against the actual body and ornament ink. Chapter numerals restart verse numbering; all 66 books have illuminated openings. Genesis retains the proof's attested `Pá` heading. Other openings use the attested native word `Govis` and their canonical Unta ordinal; English book names are navigation metadata only, not body text.

## Native storage and access

`state.printEdition`, version 1 / layout `letter-native.1`, augments the existing native document. Ordinary native frames retain exact source text for search and copy. Scalar spans specify the fixed line placements; vector paths describe ornaments and the original enlarged initial. Artwork PNG bytes are embedded once and hash-verified. Text is rendered lazily from bundled original TTFs, not raster page images or an external PDF.

This publication's text and geometry are read-only to preserve its sealed historical layout. Changes require a separately generated edition. Save/save-as, page navigation, source selection/copy, search, Unta visibility/position, undo of numbering changes, PNG, SVG and PDF remain available. The original four-column work remains separate. `publication.edition.inspect` exposes provenance, verse count, section/page links and the selected page's side/folio through Python, CLI, desktop and MCP.

The frozen ledger contains parentheses/brackets absent from the Thimfora master; those exact punctuation scalars use the bundled Transliteration 7 outlines at a matching optical size. One editorial hyphen, absent from both supplied fonts, is retained as its original scalar and drawn as a small typographic rule. No language letters, case, words or punctuation are deleted or substituted in the native source. Exceptional overlong compounds may wrap at glyph boundaries without inserted hyphens; the manifest records their verse IDs. This is line layout, not lexical change.

## Build and verification

Run `.venv\Scripts\python.exe -m tools.kjv_print_edition` to create a new private edition folder. Existing output folders are refused. The default output is `Saves/KJV Bible - Letter Edition v0.10-kjv.280/`. No Forge writes, source regeneration or historical audit is invoked.

The builder verifies the frozen native and ledger hashes before and after, every exact verse hash and source span, all rendered line bounds, all folio clearances, complete 66-section/31,102-verse coverage, and save/reopen identity. Its manifest records layout version independently of language version. Runtime document validation also rejects altered source spans, unpainted source text, broken artwork hashes, invalid paths and missing references.

`tests/test_native_print_edition.py` covers native save/reopen, exact text/case, requested pairing, mirrored sides, punctuation, long compounds, numbering/undo/collision rejection and artwork-bearing exports. Run the approved parallel translation, print proof, file, book loading, storage and export regressions with it. Setup checks runtime primitives only; it never rebuilds private books or reinstalls this existing environment.
# Book-opening preference, corrected 2026-11-05

New editions use the next available page for each biblical book, whether left
or right. There is no inter-book blank inserted to enforce a side. Title | Blank
and Frontispiece | Genesis opening remain; only front matter and any final duplex
padding are intentionally blank. Binding offsets and protected folios follow the
actual page side. This supersedes the right-opening requirement described in the
original edition notes below. `--legacy-right-openings` exists only to reproduce
that older layout; existing saved editions are never automatically repaginated.

The separately versioned compact historical correction 0.10-kjv.281 uses the
grammar in `data/language/archaic-kjv-281/grammar.md`. Its complete ledger supplies
the new text, while its publication retains the approved compact type profile.
Setup verifies the package without rebuilding private books.

