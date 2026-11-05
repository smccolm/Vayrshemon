# Letter duplex print proofs

The subsequent full native edition uses the user's revised **Title | Blank**, **Frontispiece | chapter opening** order. See `NATIVE_PRINT_EDITION.md`. The PDF proofs below remain unchanged historical design records.

## Proof 3: display blank and physical page order

The latest pair is in `Exports/KJV Letter proof 3/`. Use **READ - KJV Letter proof 3.pdf** in a PDF viewer: it includes a leading, display-only blank so ordinary paired view shows blank | title, then frontispiece | illuminated opening. Its layout is `/TwoPageLeft`; turn off a viewer's separate-cover option. This companion has 11 PDF pages. Its real pages are exact copies of the print master's drawing streams, with shifted bookmarks/navigation labels and unchanged printed Unta numbers.

Use **PRINT - KJV Letter proof 3.pdf** for home duplex printing. It has 10 physical faces / 5 sheets, starts with the right-hand title, and retains the frontispiece on the left and chapter opening on the right after turning the title leaf. The screen's leading blank represents the inside cover and is not an extra printed face. Print the PRINT master at 100% / Actual size, Letter, double-sided long-edge flip. If printing from the READ companion instead, print only PDF pages 2–11; its `PrintPageRange` suggests this but viewers may ignore that preference.

No blank was inserted between the title and frontispiece. This implements the user's correction to show a blank **before** the title while retaining correct binding/duplex parity. The print layout, source text, Maxima, art pixels, protected folios and earlier proofs remain unchanged. Run the builder with `--out "Exports\KJV Letter proof 3"` to generate the two copies and their manifest in a fresh directory.

## Proof 2: bound-page layout and supplied artwork

The prior proof remains in `Exports/KJV Letter proof 2/KJV - Letter duplex print proof 2.pdf`. Proof 1 remains intact. Supply both `--title-art` and `--frontispiece-art` to the generator, or use its defaults in ignored `Inputs/Print artwork/`. The private copies preserve the original Downloads bytes; no dependency on the Downloads folder is required after copying. The complete artwork is embedded losslessly at 1103 × 1426 pixels, approximately 134 DPI at the print size. The body remains vector outlines. This is placement of supplied art, not regenerated or retouched artwork.

Every body area and artwork canvas is centered **9 pt outward** from the physical paper center: x=297 pt on a left page, x=315 pt on a right page. Body inside/outside margins are 45/27 pt (5/8 and 3/8 inch). The inside margin is therefore 1/4 inch larger than the outside margin, giving the requested 1/8-inch center offset. This supersedes proof 1's 36/27 pt body margins. The outside margin is retained rather than pushing text toward the printer's unprintable edge. Headings share their body center. Folios stay safely anchored 28 pt inside the outside and bottom paper edges.

The front-matter image canvases include their supplied white borders. They are fitted without cropping/distortion; the actual dark artwork is separately checked against the 18 pt printer-safe region. Letter page dimensions, long-edge duplex, page order, 36/28 pt type, Maxima and exact Genesis 1–2 text are retained. `tests/test_kjv_print_proof.py` also verifies mirrored offsets, uncropped image placement, original embedded pixel dimensions, lossless compression and unchanged source images.

Setup's `--check` verifies geometry/font primitives without requiring private artwork or the Bible. No reinstall is required. The current generator produces proof 3; this section records proof 2's unchanged physical design.

## Proof 1: original design record

The user requested a Vayrshemon-only print proof on 2026-11-04, using US Letter paper and double-sided home printing. This is a separate publication design. It does not change the approved workbench layout or the historical translation.

The proof is **incomplete as a Bible edition**: complete Genesis 1:1–2:25, 56 of 31,102 verses. It includes a cover, frontispiece, illuminated Genesis opening, ordinary full-width pages and a chapter/verse-number restart. Visible text is Vayrshemon with Unta numerals. English PDF bookmarks, accessible page labels and the printing note are navigation metadata, not an English reading column.

## Reproduce

The original PDF remains in `Exports/KJV Letter proof 1/`; the current builder generates the proof 3 pair as described above. The output directory must be new. Old proofs are retained. The tool checks the exact Bible and ledger hashes before authoring and again afterward; it does not run a historical compiler, open Forge, alter the language pin or save the original document.

The generator is versioned source; the PDF, printing note and verse/page manifest belong in ignored Exports. It is currently a PDF proof generator, not a new editable ornament/page-master feature in the Workbench. A complete native print edition remains future work after design approval.

## Physical specification

- Letter: 612 × 792 pt, portrait, 100% / Actual size, double-sided, long-edge flip.
- One page per printed face, no booklet imposition. Odd physical pages are right-hand pages. The cover is face 1; its reverse is the frontispiece, facing the illuminated opening on face 3.
- Inner margin 36 pt / 0.5 inch; outer and top margins 27 pt / 0.375 inch. Check the actual printer's printable region using the proof.
- Body 36 pt Thimfora 79, exact 28 pt leading and 4 pt between verses. This is a print-specific size, not a change to the 50 pt workbench standard. Unchanged Maxima and spelling, no normalization, no added hyphens, no font fallback.
- Verse markers 24 pt, base-12 Unta; reset within each biblical chapter. The first verse's marker precedes the illuminated actual first glyph, not the rest of its word. A continued verse is not renumbered.
- Chapter numerals 50 pt (opening caption 42 pt). Folios 50 pt, with their actual ink 28 pt from the bottom and outside edges. Body ink ends at or above y=729 pt. Every body folio is present and checked against body/initial/chapter artwork with 4 pt clearance.
- Cover/frontispiece are unnumbered. Body starts at Unta 1 on PDF face 3. PDF UI labels remain decimal. An unnumbered blank back is added only when needed to finish a duplex sheet.
- Outline-only vector PDF: no full-page raster fallback or font substitution. Restrained indigo/brass ornament on the cover, frontispiece and opening; ordinary text pages are black on white. Printer grayscale remains usable.

## Artwork and title provenance

The Memon is the actual original Maxima M outline, centered on its ink. The opening initial is the original first character of Genesis 1:1, enlarged and separately decorated; it is not duplicated in the body. Book title `Govis`, history subtitle `TÍnvÅl`, beginning title `Pá`, and pronoun captions `ráun` / `ly` use the existing historical vocabulary. The frontispiece's three centers, common enclosure and twelvefold geometry are new book ornament, not invented alphabet characters or claimed ancient art.

## Validation

`tests/test_kjv_print_proof.py` checks exact case/text preservation, multi-page verse continuations, Unta conversion/reset, mirrored margins, unclipped folios and PDF duplex/page-label settings using explicitly synthetic structural strings. `tests/test_parallel_translation.py` remains mandatory. Setup invokes only `--check` (bundled fonts and print primitives); it never regenerates private books or proofs. Render the actual final PDF with Poppler and inspect every page, including the opening initial and chapter transition, before delivery.
