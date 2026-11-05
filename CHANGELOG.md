## 2026-11-05 — definitive historical 281 and later dramatic 0.12

- Compact 281 is sealed and definitive; a complete matching four-column edition preserves exact verse targets and approved geometry, Maxima and paint. Narrow-frame clitic/tag boundaries wrap without changing text or type size.
- Both complete plays move from 0.11 to 0.12: twenty source-linked additive/continuation revisions, six inherited grammatical dictionary entries, no new lexical roots; deliberate repetitions stay. Dictionary, wiki, Forge and the current-language pin advance together.
- Earlier editions and complete Forge ancestry are compressed and verified before redundant unpacked files are removed. Setup verifies the current package without rebuilding private books.

# Planning revision history

## Reader 1.0.0 — Independent native book reader

- Added `Reader/`: a separate read-only app with its own Memon launcher, .vay handler, search, bookmarks, one/two-page navigation, zoom and API/MCP controls. Workbench editing remains separate and can run concurrently.
- Indexed the full 20,780-page Bible for random access; isolated rendering, exact persistent glyph tiles, bounded image/index caches, prefetching and continuous action/stall timings avoid full-book composition. No PDF conversion or source document rewrite.
- Tested full-Bible cold/restart/navigation/zoom/palette/search/memory and 24 pixel-identical comparisons with the unchanged Workbench renderer. See `Reader/PERFORMANCE.md` for measured limits, first-use costs, and Windows' remaining default-app choice. Root and Reader setup build/register the launcher without reinstalling this working environment.

## 0.15.34 — Compact complete Bible

- Added a separate `letter-compact.1` layout with 26 pt original Thimfora, 18 pt leading, 18 pt Unta verse markers and 2 pt verse spacing. The earlier 36/28 pt edition keeps its original rendering defaults.
- Compact native files record their typography and enforce a maximum of 2,000 pages / 1,000 duplex sheets. Complete verse identity, artwork, book openings, mirrored binding margins, Maxima and protected folios remain intact.
- Updated setup runtime checks and native save/reopen/export coverage; no new dependencies or reinstall.

## 0.15.33 — Native bound print editions

- Added a versioned fixed print layout with searchable/copyable native text, embedded original artwork, lazy vector text rendering and safe Unta folios. Text/geometry are sealed; navigation, saving, numbering changes and exports remain available.
- Added a complete frozen-KJV Letter builder using the requested Title/Blank and Frontispiece/Opening spreads, mirrored binding offsets and illuminated openings for all 66 books. Exact verse hashes, all page/folio bounds and save/reopen identity are checked.
- Added publication inspection to API/MCP and setup runtime verification. Existing approved workbench formatting and frozen historical translations are unchanged.

## Letter design proof 3 — blank/title reading spread and physical print master

The reading companion now begins with a display-only blank: blank | title, then frontispiece | illuminated opening. Its `/TwoPageLeft` layout pairs from the first PDF page. A separately named PRINT PDF retains the title as physical recto 1, frontispiece as verso 2 and opening as recto 3, with the existing mirrored binding offsets and Unta folios. Adding the display blank directly to a duplex print job would reverse those physical sides, so the READ PDF suggests skipping page 1 when printing, and the printing note directs the user to the unambiguous PRINT master. Every real page's drawing stream and dimensions are identical between the two files; labels and bookmarks account for the display blank. Supplied artwork, all 56 frozen verse strings and prior proofs are unchanged. Setup retains the same runtime and no reinstall is required.

## Letter duplex design proof 2 — binding gutter and supplied artwork

Replaced the title and frontispiece with the user's supplied PNGs, copied unchanged into ignored Inputs/Print artwork. The entire images are embedded losslessly at their original resolution without cropping or distortion. Both artwork and body areas are centered exactly 9 pt outward from the physical sheet center: left pages leftward, right pages rightward. Body margins now reserve 45 pt inside / 27 pt outside (5/8 / 3/8 inch); the illuminated heading follows its body center. Unta folios retain the protected 28 pt outside/bottom inset. Text size, leading, Maxima and all 56 excerpt verses are unchanged; the slightly narrower measure is repaginated. Proof 1 and the frozen Bible/ledger remain unchanged. Setup retains its private-file-free runtime check; no new dependencies.

## Letter duplex design proof 1 — frozen KJV 0.10-kjv.280

Added a separate, reproducible PDF proof builder for US Letter home duplex printing. The design excerpt contains Genesis 1–2 (56 verses), a Memon cover, an original geometric frontispiece and an illuminated opening. Full-width 36 pt Thimfora / 28 pt leading, 24 pt Unta verse markers and 50 pt Unta folios use exact bundled outlines. Mirrored 36/27 pt binding/outside margins, a reserved footer and outline-bound checks protect the numbers. Continuations retain at least two verse lines on each side of a page break. The PDF starts on a right-hand page, requests actual size and long-edge duplex, and distinguishes cover/frontispiece from body folios.

This is an incomplete design proof, not a newly translated or modernized Bible or a replacement for the approved four-column layout. The source Bible and ledger are SHA256-pinned and never written. Setup checks the print runtime without opening/rebuilding private books; no dependency or application reinstall is required. See `docs/PRINT_PROOF.md`.

## 0.15.32 — opening the complete Bible

Large books now use the pinned native Draft 2020-12 schema validator, retaining reference-validator errors and all semantic, checksum, font and size checks. Opening adopts its freshly parsed state, keeps one independent editing snapshot, and reuses that snapshot for recovery. The Open dialog reuses its validated preflight only when the file hash still matches. Paragraph-alignment inspection walks each spread once; dictionary sense and corpus-link validation use indexes. Exact font files are checked once per distinct font instead of once per frame. Loading stages are visible and logged; command-line opening shows the editor before loading, and the local open/preflight API allows a large book to finish without the old three-minute timeout. Setup installs and checks the added validator in the existing environment.

The frozen v280 Bible was opened in the real editor with all 20,780 pages, checked at both ends, and returned to its opening spread. Its SHA256 remains `a70a7e00b9f915dd9126668dc2af3c0c3078632bd5b5aa72ad50789b7f437754`. The measured opening took 207.8 seconds before the final distinct-font optimization; final-spread navigation took 2.0 seconds and return navigation 1.1 seconds. This fixes repeated work, not the remaining cost of loading a very large native document. No translation, formatting, Maxima, numbering, saved mode or renderer changes were made.

## KJV 0.10-kjv.280 — native vocabulary correction

**Latest verified complete historical correction: 0.10-kjv.280.** `Saves/KJV Bible v0.10-kjv.280/KJV Bible.vay` contains **31,102/31,102 verses, all 66 sections, 20,780 pages**. SHA256 `a70a7e00b9f915dd9126668dc2af3c0c3078632bd5b5aa72ad50789b7f437754`; Forge head `da33601402a3abd548a0af36924599af837753740469d6b5c90dfdbbc687fa71`. Corrected 547 existing lexical forms and 7,329 verse texts, including 38 marriage/oath errors and eight related married/wedding cases; added 9 semantic entries. Dictionary, eight grammar sections, seven wiki articles and 31,102 current Forge verse fixtures updated. All four columns, exact source text, save/reopen identity, 41,560 folio placements and selected monochrome/color proofs verified. Approved geometry, 50/22 pt type, 38 pt leading, Maxima and paint retained. Long numeric products have explicit factor-boundary line opportunities without character changes. Original 278, the intermediate 279 language checkpoint and modern 0.10 pin are unchanged. Use 280 for the completed corrected Bible. This is an authorized historical correction, not modernization; it remains permanently excluded from consolidation. See `docs/research/kjv-native-vocabulary-280.json`. Structural validation and translator self-review are not independent literary certification.

Setup now verifies package 280; no dependencies or reinstall were needed. Seven language regressions and both approved parallel-format tests passed. Saved books remain ignored by Git.


Earlier working checkpoint (superseded): combined v54 remains the verified combined save (8,766 verses / 6,346 pages). Native61 is sealed and verified through 1 Kings 19: 691 Kings verses / 494 pages; 9,457 Bible verses. Four tests passed in 11.148 s; proofs493/494 viewed. Head61 3d72c5d6f27b1665e442a5eb655782ee6009ad83f81293d07f6cb7f8487d0050. Working62 completes authored/compiled/audited 1 Kings20–22,125 new verses:816 Kings /9,582 Bible,21,520 remain. Its preflight and publication are running. Twenty-two lexical additions,9 grammar sections,2 wiki articles. Working63 reviews all203 earlier human-one candidates and corrects47 verses in new copies (14 Genesis,7 Numbers,10 first Samuel,16 second Samuel); preflight workers running. Sealed earlier editions and frozen Jonah unchanged. Setup verifies through61; no reinstall. Whole Bible remains incomplete; next canonical section is2Kings1.

## 0.15.31 — whole-corpus Forge capacity

A growing reviewed Bible exceeded the5,000-page-example ceiling. Forge now accepts up to40,000 page examples in a snapshot bounded at256MiB; the separate2,000 wiki-article bound, record IDs, rule references and per-record checks remain. The40,000-example project was committed, exported and restored with exact older/current snapshots. Overflow, duplicate IDs, missing references and the snapshot byte guard were tested:5 targeted tests passed in23.960s, including the approved parallel-format regression. Existing historical hashes and document rendering are unchanged. No dependencies or reinstall were needed.


## Historical continuation through Ruth;1Samuel underway

The sealed0.10-kjv.41 register contains complete Genesis, Exodus, Leviticus, Numbers, Deuteronomy, Joshua, Judges and Ruth plus frozen Jonah: **7261/31102 authored verses;23841 remain**. v39 corrected only the explicit counted plural in Judges12:14; v40 completed Judges, and v41 added all85 Ruth verses. Complete Judges has482 native pages and Ruth68, with save/reopen, four-column text, approved geometry and Unta placement checks passed. The combined v40 file through Judges subsequently completed:5086 pages,7176 verses, saved/reopened/verified. Later1Samuel checkpoints are summarized above. Whole Bible remains incomplete. Historical editions are never modernized. Setup verifies sealed registers through v41 without reinstalling this installation.


Earlier v35 checkpoint: the combined incomplete Bible was `Saves/KJV Bible v0.10-kjv.35/KJV Bible - WORK IN PROGRESS.vay`: 6558/31102 verses,4604 pages, complete through Joshua plus frozen Jonah. Saved/reopened with all four columns and9208 folio placements verified. Forge head`d164e1c2dba3607029331d19adaf7cf47c6420cff469b56cf8b6d1a38ceeefa6`. v36 adds sealed Judges1–5 (145verses/104pages; total6703); v37 Judges6–9 remains a draft checkpoint. The entire Bible goal is still active and incomplete.

## Historical KJV 0.10-kjv.31–32 — incomplete Bible

Complete Deuteronomy is saved in the combined v31 checkpoint: 5900 verses / 4120 pages; exact columns, save/reopen and 8240 folio placements checked. Viewed Deuteronomy 32:39–41 and final chapter proofs. v31 adds 123 verses, 16 entries, nine grammar sections and two wiki articles; eight targeted tests pass. v32 adds Joshua 1–6, 125 verses and seven entries; its 104-page section and nine targeted tests pass. Whole Bible remains incomplete. No reinstall.

## Historical KJV 0.10-kjv.26 — incomplete Bible

Deuteronomy 1–6: 219 verses, 40 entries, nine grammar sections, three wiki articles; nineteen documented earlier sense corrections. Combined 5160 verses / 3550 pages saved and reopened identically, all four columns and 7100 folios checked. 34 targeted tests; viewed Deuteronomy 6:3–5.

## Historical KJV 0.10-kjv.25 — incomplete Bible

Numbers 31–36: 228 verses, 94 entries, eight grammar sections, two wiki articles. Saved 4941 verses / 3388 pages. 363 numeric clauses, two fractional schedules, 33 targeted tests, exact columns/folios/save-reopen passed. No reinstall.

## Historical KJV 0.10-kjv.24 — incomplete Bible

Numbers 26–30: 175 verses, 39 entries, eight grammar sections, two wiki articles. Saved 4713 verses / 3258 pages. 313 numeric clauses, five fractional schedules, 32 targeted tests, exact columns/folios/save-reopen passed. No reinstall.

## Historical KJV 0.10-kjv.23 — incomplete Bible

Numbers 17–25: 245 verses, 58 entries, nine grammar sections, two wiki articles. Saved 4538 verses / 3148 pages. 243 numeric clauses, three fractions, 31 targeted tests, exact columns/folios/save-reopen passed. No reinstall.

## Historical KJV 0.10-kjv.22 — incomplete Bible

Numbers 11–16: 220 verses, 61 entries, nine grammar sections, two wiki articles. Combined checkpoint 4293 verses / 2974 pages. 214 numeric clauses, seven fractions, 30 targeted tests, exact columns, folios and save/reopen passed. No reinstall.

## Historical KJV 0.10-kjv.21 — incomplete Bible

Numbers 5–10: 232 verses, 11 lexical entries, eight grammar sections, two wiki articles. Combined saved checkpoint 4073 verses / 2824 pages. Four columns, save/reopen, folios, 172 numeric clauses and 30 targeted regressions pass. Setup verifies v21; no reinstall.

## Historical KJV continuation 0.10-kjv.20 — incomplete Bible

Added Numbers 1–4: 188 verses, 39 lexical entries, eight grammar sections, two wiki articles. Saved one 2,676-page checkpoint with 3,841 verses. Earlier targets intact. Four-column/save/reopen/folio checks, 67 numeric clauses and 29 targeted regressions passed. Source census discrepancy preserved. Setup verifies v20; no reinstall.

## Historical KJV continuation 0.10-kjv.19 — incomplete Bible

Completed Leviticus with 259 new verses, 34 lexical entries, eight grammar sections and two wiki articles. Saved one 2,558-page checkpoint with 3,653 verses; earlier text intact. Four-column, save/reopen, folio, 158 numeric clause and 34 targeted regression checks passed. Setup verifies v19; no reinstall.

## Historical KJV continuation 0.10-kjv.18 — incomplete Bible

Added Leviticus 16–20: 144 verses, 25 lexical entries, eight grammar sections and two wiki articles; corrected two prior Ephah measure senses. Saved one 2,372-page checkpoint with 3,394 verses. Four columns, save/reopen, folios and 101 numeric clauses verified; 33 targeted tests passed. Setup verifies v18; no reinstall.

## Historical KJV continuation 0.10-kjv.17 — incomplete Bible

Added Leviticus 11–15: 204 verses, 55 lexical entries, eight grammar sections and two wiki articles. Saved one 2,258-page Bible checkpoint with 3,250 verses. Four columns, save/reopen, folios and 88 numeric clauses verified; 33 targeted tests passed. Setup verifies v17; no reinstall.

## Historical KJV continuation 0.10-kjv.16 — incomplete Bible

Added Leviticus 1–10: 252 verses, 23 lexical entries, eight grammar sections and two wiki articles. Saved one 2,114-page Bible checkpoint with 3,046 verses. Four columns, save/reopen, folios and 35 numeric clauses verified; 32 targeted tests passed. Setup verifies v16; no reinstall.

## Historical KJV continuation 0.10-kjv.15 — incomplete Bible

Completed Exodus by adding chapters 32–40: 307 verses, 18 lexical entries, eight grammar sections and two wiki articles. Saved one 1,920-page Bible checkpoint with 2,794 verses. Four columns, save/reopen, folios and 276 numeric clauses verified; 31 targeted tests passed. Setup verifies v15; no reinstall.

## Historical KJV continuation 0.10-kjv.14 — incomplete Bible

Added Exodus 25–31, 243 verses, 100 lexical entries, eight grammar sections and two wiki articles. Saved one 1,714-page file with 2,487 verses, preserving Genesis and frozen Jonah. Verified quantities, four columns, save/reopen and folios; 30 targeted tests passed. Setup verifies v14; no full reinstall.

## Historical KJV continuation 0.10-kjv.13 — incomplete Bible

Added Exodus 19–24, 169 verses, 25 lexical senses, eight grammar sections and two wiki articles. Saved one 1,556-page file with 2,244 verses, preserving Genesis and frozen Jonah. Developed one-voice singular-we, name-bearing messenger relations and difficult-law distinctions. All columns, save/reopen and folios verified. Setup verifies v13; no reinstall.

## Historical KJV continuation 0.10-kjv.12 — incomplete Bible

Added Exodus 13–18, 159 verses, 43 entries, eight grammar sections and two wiki articles. Saved one 1,442-page file with 2,075 verses, retaining all Genesis and frozen Jonah. Developed commemorative/choral plural-I, communal singular-we and paired human speakers; checked rations, chronology, all columns and folios. Setup verifies v12; no reinstall. Exodus 19–24 drafts continue in v13.

## Historical KJV continuation 0.10-kjv.11 — incomplete Bible

Added Exodus 7–12, 182 verses, 41 dictionary entries, eight grammar sections and two wiki articles. Saved one 1,318-page file with 1,916 verses, preserving all Genesis and frozen Jonah. Verified four columns, folios and save/reopen; continued Exodus 13 onward in v12. Setup verifies v11; no reinstall.

## 0.15.30 — compressed native books

Large books save in a bounded, checksummed 0.7 envelope while retaining their exact editable 0.6 state. Added streamed hashing/writing, compressed recovery and export snapshots, exact prior-file backups and bounded Explorer header reads. A separate 1,178-page Bible copy shrank from 125 MB to 11 MB with exact state/history and identical checked rasters. Old files and the original checkpoint remain unchanged. Setup is updated; no application reinstall was run.

## Historical KJV continuation 0.10-kjv.10 — incomplete Bible

Added Exodus 1–6, 153 verses, 62 lexical entries, eight grammar sections and two wiki articles. Saved one 1,178-page working file with 1,734 verses and unchanged Jonah. Distinguished quoted divine self-naming and human commission; corrected four working Genesis worship senses and clarified possessive gloss labels. Preserved formatting and Maxima. Setup verifies v10; no reinstall was run. Exodus 7–9 authoring continues in v11.

## Historical KJV continuation 0.10-kjv.9 — incomplete Bible

Completed Genesis through 50:26, adding 174 verses, 80 lexical entries, eight grammar sections and two wiki articles. Saved one 1,060-page working file with 1,581 verses and unchanged Jonah. Preserved formatting and Maxima; setup verifies v9. No reinstall was run. Exodus authoring continues.

## Historical KJV continuation 0.10-kjv.8 — incomplete Bible

Added Genesis 39–44, 209 verses, 27 lexical entries, eight grammar sections and two wiki articles. Saved one 940-page file with 1,407 verses and unchanged Jonah. Developed office-self, kin-self and shared-liability distinctions; preserved formatting and Maxima. Setup verifies v8; no reinstall was run.

## Historical KJV continuation 0.10-kjv.7 — incomplete Bible

Added Genesis 33–38, 189 verses, 113 lexical entries, eight grammar sections and two wiki articles. Saved one 800-page combined checkpoint with 1,198 translated verses and unchanged frozen Jonah. Expanded the bounded Forge page-demo library to 5,000 with history roundtrip coverage. Approved formatting and Maxima remain; setup verifies v7. The whole-Bible task continues.

## Historical KJV continuation 0.10-kjv.6 — incomplete Bible

Added Genesis 27–32, 233 verses, 65 dictionary entries, eight grammar sections and two wiki articles. Saved a 682-page combined checkpoint containing 1,009 translated verses with unchanged frozen Jonah. Developed human plural-I for Jacob's two bands while preserving personal identity claims and separate negotiating parties. Approved formatting and Maxima remain; setup verifies v6. The entire-Bible task continues.

## Historical KJV continuation 0.10-kjv.5 — incomplete Bible

Added Genesis 21–26, 214 verses, 97 dictionary entries, eight grammar sections and two wiki articles. Saved one 520-page checkpoint with 776 total translated verses including unchanged frozen Jonah. Developed plural-I self-oath, quoted personal I, singular-we household and polity voices. Preserved approved formatting, Maxima and paint; setup verifies the new package. The entire-Bible task continues.


## Working KJV covenant continuation · 0.10-kjv.4

- Author Genesis 16–20 with source-bound discourse notes, 36 entries, 8 grammar sections, 132 exact compiler cases and 52 Forge reading fixtures. Preserve every parent lexical record.
- Save one 376-page working Bible containing 562 / 31,102 verses. Preserve frozen Jonah, prior editions, all four columns, Maxima and approved formatting. The whole-Bible goal remains incomplete and continues in the next historical working version.
- Keep setup verification current; no reinstall.

## Working KJV identity continuation · 0.10-kjv.3

- Develop internally plural I and singular we, with provenance, ordinary-human contrasts and exact source preservation. Add 75 lexical entries, 7 grammar sections and 116 fixtures.
- Author Genesis 12–15 and revise 33 earlier working verses. Save one 280-page working Bible: 430 / 31,102 verses; 30,672 remain untranslated. Frozen Jonah and previous editions are unchanged.
- Verify the four columns, layout, folios, save/reopen and safe measured-spread reuse. Continue whole-Bible authoring; this checkpoint is not completion.
These entries distinguish specification revisions from evidence-tool and future application releases.

## Whole-Bible scope correction and historical continuation — 2026-10-25

- Correct the deliverable to one complete Bible `.vay`, with 66 biblical books as major sections. Individual section deliveries do not complete the request. Identity-based coverage checks reject duplicates, changed source strings and unauthored placeholders; completion requires every source verse.
- Author Genesis 1–11, all 299 verses, with analyses, back-readings and interpretation notes. Keep frozen Jonah's 48 verses unchanged. Current coverage is 347 of 31,102; **30,755 verses remain untranslated**. The 0.10-kjv.2 document is explicitly a working excerpt.
- Add 189 lexical entries (135 proper-name identities/senses and 54 common entries), eight continuation grammar sections, two Forge wiki articles and 56 verse fixtures. Distinguish retrospective regret from Jonah's withdrawal of intended calamity; preserve source quantities, unresolved pronouns, ancient cosmography and deliberately cumbersome calques. No inflectional, Maxima, font or paint changes.
- Verify 75 numerical clauses and ten genealogy age sums separately. Use analytical possessives where long compounds exceed the approved column width. Setup verifies the explicitly selected working historical register while retaining the original frozen default. No reinstall or dependency change.

## Historical KJV register 0.10-kjv.1 — 2026-10-25

- Start the explicitly requested whole-KJV, book-by-book project with an exact 66-book / 31,102-verse source index. Jonah is the first complete authored book: 48 verses, with source-order analyses, construction glosses, literal back-readings and verse-specific editorial notes. The other 65 books remain pending.
- Branch from consolidated 0.10 without changing the modern pointer or existing plays. Add 45 semantic entries (including compounds, retained historical forms, sense distinctions and six name adaptations), eight historical grammar sections, three Forge wiki articles and 48 verse fixtures. Preserve awkward calques and explicit participant tracking without random word substitution.
- Pin a separate historical compiler, retaining target encoding and morphology while making historical possessive gloss labels readable. Preserve the approved four-column type, Maxima, paint, geometry, paragraph alignment and default Unta numbering.
- Add overwrite refusal, frozen-edition hashes, anti-consolidation guards and explicit future-work instructions. Setup verifies the historical package and runs its regressions; no reinstall or new dependency.

## M14 Fit Height after Close 0.15.29 — 2026-10-25

- Apply the clean initial Fit Height and centering step after File → Close and File → New, including API/MCP calls with a desktop attached. Check for an untouched document rather than a zero session revision. Preserve saved-file zoom on Open.
- Keep the new page clean, without an extra revision, Undo step or save prompt. Retain single-page mode, black-on-white defaults, panel preferences and approved typography. Update setup guidance without reinstalling.

## M14 close document 0.15.28 — 2026-10-25

- Add File → Close (Ctrl+W), returning to a clean Untitled page while keeping the application and Forge session open. Reuse the saved/opened-state comparison for the Save/Discard/Cancel prompt, including unsaved new documents and Undo back to the saved state.
- Keep the document open if Save As is cancelled or saving fails. Close unchanged files without a prompt; retain the saved file and clear the closed document's Undo history. Expose guarded `document.close` through API/CLI/MCP.
- Update setup guidance and contracts without adding dependencies or reinstalling. Preserve page formatting, Maxima, fonts and exports.

## M14 reading defaults 0.15.27 — 2026-10-25

- Start blank documents in Monochrome: black on white, including File → New. Retain Fit Height, single-page mode, the clean workspace defaults and saved panel preferences.
- Preserve the saved color mode when opening existing documents. Set the default before the initial saved-state checkpoint, without creating an edit or save prompt. Update setup guidance and the existing startup/reopen regression.
- Default new documents to Unta numbering at 50 pt with a preferred 28 pt edge inset once they contain at least two pages, in either reading mode. Adding/removing pages and Undo naturally follow the saved minimum-page rule. View → Page numbering can turn off the rule or numbering entirely; prior saved settings and older editions remain unchanged. Preserve body formatting and collision-safe placement, including export validation.

## Language consolidation 0.10 — 2026-10-25

- Consolidate both complete Shakespeare ledgers into a pinned, self-contained starting package for the next translation. Canonical semantic keys replace reconstruction from an old snapshot and competing TSV declarations; retain explicit historical forms and original editions.
- Review 57 homograph groups and 12 competing declarations. Correct generic versus numeric one, double case, obstructive versus physical bar, living mortality versus already dead, numeral names from the Unta chart and ordinal distinctions. Revise 28 current forms including dependent compounds; preserve deliberate polysemy, rhetorical recurrence and register.
- Add an expressive utterance enclitic, ’hā (`excl.`), in response to the missing Thimfora exclamation glyph. Migrate 221 target occurrences across 176 units while preserving English, command/wish/spell force and Maxima; reject borrowed `!` in the current editorial compiler.
- Add ten consolidated reference records, three current wiki articles, one morphology record, 64 positive/negative compiler cases and 53 Forge review fixtures. Keep one unresolved literary reading and ten unrelated homophone groups explicitly documented. This is the current authored working baseline, not a gated stable release.
- Produce separate complete 0.10 books with the approved four-column typography and paragraph alignment; reflow longer forms onto extra pages. Bundle the reusable package in the repository while keeping personal editions and full Forge ancestry under ignored Saves. Update setup to verify package hashes, without reinstalling or adding dependencies.

## M14 expanded dictionaries 0.15.26 — 2026-10-25

- Raise the language dictionary bound from 2,000 to 10,000 entries in both editable data and immutable revision references; permit 20,000 shared language objects. Other collection limits remain unchanged. Regenerate current native/API/MCP contracts and retain the document format and typography.
- Add a 2,655-headword language/Forge roundtrip regression and an upper-bound rejection check. Update setup without adding dependencies or reinstalling.
- Author the separate Midsummer 0.9 language continuation from All's Well 0.8. The private edition, full source ledger, dictionary, wiki and combined book remain under ignored Saves; the repository records only the edition's counts and validation evidence.

## M14 Unta page numbering 0.15.25 — 2026-10-25

- Add View → Page numbering with saved, undoable master visibility, separate single/left/right visibility and corner choices, numeral size and preferred edge inset. Older documents remain unnumbered until enabled.
- Convert physical page indexes to exact base-12 Unta glyphs from the original three-font family. Preserve body formatting, Maxima, frames, margins and paragraph alignment; use the current color/monochrome treatment.
- Keep complete numeral effects clear of text regions and visible overhangs, searching only the chosen margin. Withhold unsafe folios and report the page; refuse overlapping exports while allowing the document to be saved.
- Share placement across preview, thumbnails and PNG/SVG/PDF; freeze the page mode in export jobs. Add three API/MCP controls and regenerate contracts. Update setup without reinstalling or adding dependencies.
- Pass 26 focused tests and verify safe default folio placement on all 674 actual play pages. Review the approved example in color and both monochrome palettes, the independently rendered facing PDF, and the native Windows dialog; preserve the original save.

## M14 faster full-color export 0.15.24 — 2026-10-24

- Reuse exact glyph paths, effect bounds and layer metadata across pages with bounded, identity-keyed caches. Avoid repeated font-file reads and outline construction while preserving the three-font registration, Roman treatment, Maxima and identical pixels.
- Check and draw color PDF pages in one composition pass when first-page preflight establishes the existing whole-book raster policy. Preserve full preflight for initially undecorated books, lossless output at the requested DPI, late-error cleanup and page progress.
- Expose geometry cache counters through `performance.inspect`; keep the lighting tile cache limit unchanged. Update setup without dependencies or reinstalling.
- Verify cache mutation isolation, bounded retention, recipe changes, mixed decorated/plain PDFs, the six PDF modes and approved parallel typography.
- Complete the same 674-page color play at 292 DPI in 631.4 seconds, plus 50.1 seconds snapshot loading (11m 21s total, versus 38m 9s previously). Independently verify identical compressed images, drawing streams, resources and page boxes on all 674 pages, with unchanged numbering and paired view; review opening, middle and final spreads.

## M14 faster full-book PDF and progress bar 0.15.23 — 2026-10-24

- Check and draw monochrome PDF pages in one composition pass. Reuse collision results for unchanged solver geometry and precompute cluster bounds without changing tolerances, pair order, repair decisions or drawing.
- Show a progress bar, physical page count, elapsed time and Cancel in the reading status bar. Keep preparation visible, report finalization/verification and reserve 100% for successfully published output. Expose structured progress through the existing API/MCP.
- Retain exact page dimensions, approved formatting, Maxima and lossless color rendering. Keep partial files private, close temporary PDF handles after errors, and release evicted worker frame objects between pages.
- Update setup without reinstalling or adding dependencies. Validate single-pass composition, late errors, cancellation, all six PDF view/color combinations and approved parallel typography.
- Complete the real 674-page white-on-black export in 236.3 seconds (276.3 including snapshot loading); confirm every page has identical compressed artwork, resources and dimensions to the preceding export, plus independent rendered spread review.

## M14 large PDF finalization 0.15.22 — 2026-10-24

- Preserve compressed PDF drawing streams while correcting fractional page origins. Surround the existing artwork with the same graphics-state/translation operators instead of parsing and retaining every glyph outline.
- Retain exact page sizes, numbered pages, facing/single opening view, approved formatting and Maxima. Verify pixel equality against the previous transform and enforce that metadata adjustment never decodes compressed artwork.
- Recover the completed 674-page white-on-black export without repeating page rendering; finalization takes 2.7 seconds with the corrected path. Update setup without reinstalling.

## M14 PDF export progress 0.15.21 — 2026-10-24

- Report each physical page during PDF checking and writing, then identify final numbering/view metadata and output verification. A whole book no longer reports misleading page 1 of 1 progress.
- Keep the current export stage and elapsed time visible in the reading status bar with all panels collapsed. Remove the running indicator after completion; preserve the existing completion/error message and cancellation controls.
- Preserve the rendering pipeline, formatting, Maxima and atomic publication. Update setup; no new dependencies or reinstall.

## M14 complete native books 0.15.20 — 2026-10-24

- Allow a complete play in one `.vay`: M14 limits are 2,048 pages, 4,096 frames, two million text scalars, 120 MiB state and 128 MiB file. Retain native 0.6 structure and older-file compatibility; earlier milestone limits stay frozen.
- Load large-book frame editors on demand and retain a bounded working set. Page selection advances the guard clock without serializing the whole document or adding Undo entries. Edits still use the existing alignment, Undo, save and recovery writer.
- Extend offline backup/recovery, API responses and the bounded native Explorer reader for complete books. Update setup without reinstalling Python or dependencies.
- Add ordered-volume assembly with source hashes and exact page/typesetting comparison; never reflow text or alter source volumes. Verify complete-play navigation and rendered pages against their original volumes.

## M14 page navigation 0.15.19 — 2026-10-24

- Add a compact bottom navigator in this order: zoom, one/two-page icons, previous, Page [number] of total, next. Enter accepts every physical page including the last; invalid input leaves the view unchanged.
- Single-page arrows move one page; paired arrows move to the next/previous pair's left page. Direct right-page entry retains that exact number and displays its containing pair. Boundaries follow the visible pair, including an unpaired last page.
- Retain manual zoom or automatic Fit Height/Fit Width during navigation and mode changes. Refit only the preview; preserve document content, formatting, Maxima, dirty state and Undo history. Selection advances the existing API revision guard so stale text edits cannot land in a newly selected frame.
- Publish `view.page` through API/CLI/MCP and page/count/boundary/fit information through `view.inspect`. Update setup.bat; no dependency or file-format changes. Verify the actual play without writing its files, plus navigation and approved formatting regressions.

## M14 Python bootstrap and desktop shortcut 0.15.18 — 2026-10-24

- Setup locates usable Python 3.12 x64 and installs the official per-user runtime only when absent. Verify a pinned SHA-256 and publisher signature before execution; preserve existing environments, PATH, associations and Python installations.
- Create a Vayrshemon desktop shortcut to launch.bat with the centered Memon icon, and provide a standalone shortcut script. Preserve unrelated shortcuts.
- Check bootstrap branches with mocked downloads/installers and inspect the actual shortcut; do not run a reinstall on this installation.

## M14 bundled application fonts 0.15.17 — 2026-10-24

- Bundle byte-identical Thimfora 79/80/81 and Transliteration 7 fonts, with hashes, sizes and provenance, as tracked application assets. Inputs, Saves and Exports remain ignored.
- Load the bundled family at startup and resolve missing document paths only to the same font identity. Preserve Maxima, metrics, three-layer alignment and approved rendering; valid existing paths remain in use.
- Setup verifies the fonts without installing them into Windows. Source releases include and require all four files. Validation uses the existing environment; no reinstall or environment replacement is performed.

## M14 PDF reading export 0.15.16 — 2026-10-24

- Add File → Export → PDF with timestamp names in Exports. Export all physical pages in one background snapshot, numbered separately from 1 and opening in single-page or facing-page view to match the Workbench. Paired view starts with pages 1–2; no cover page or visible footer is added.
- Preserve fractional page dimensions and top-left content origins despite Qt's integer PDF page boxes. Keep monochrome outlines, use lossless color images for bevel/glow, and retain approved formatting and Maxima.
- Add `pdf_view` to the existing PDF API/MCP controls; retain cancellation and changed-target overwrite guards and publish only after metadata succeeds. Pin pypdf in setup requirements and add six-mode export/visual checks.

## M14 default export folder 0.15.15 — 2026-10-24

- The PNG button and File → Export → PNG / SVG default to the project's `Exports` folder (`E:\Vayrshemon\Exports` here). Preserve timestamp-only single-page names and matching `_Left` / `_Right` spread names; another destination can still be chosen.
- Create the folder during setup and when opening an export dialog. Ignore generated exports in Git, retain the approved formatting and Maxima, and verify PNG/SVG workers and parallel-translation regressions.

## M14 single-page blank startup 0.15.14 — 2026-10-24

- Blank startup and File → New select one-page mode even when the previous session remembered two-page mode. The selected icon now agrees with the blank page; startup still uses Fit Height.
- Saved `.vay` documents restore their own saved one/two-page view, including when launched directly. Restoring a view does not rewrite workspace preferences or document state. Sidebar and panel preferences remain intact.
- Update setup.bat and verify remembered two-page restart, saved spread opening, File → New, clean document history and approved formatting regressions.

## M14 paired SVG export 0.15.13 — 2026-10-24

- File → Export → SVG now exports both visible pages in two-page mode as `DateTimestamp_Left.svg` and `DateTimestamp_Right.svg`, using one timestamp and document snapshot. Single-page mode exports one `DateTimestamp.svg`; an unpaired final page produces only `_Left`.
- Share PNG's filename, overwrite and background-job handling with SVG. Check both destinations before publishing, preserve files changed during rendering, and cancel both outputs together. Keep PNG in the bottom bar and SVG in the File menu; the Publish panel uses the same visible-page behavior.
- Retain the last progress message during a transient Windows progress-file lock; log the retry condition without failing status polling or weakening output validation.
- Preserve monochrome vector outlines, color bevel/glow at the selected DPI, exact glyphs/Maxima, formatting and page dimensions. Publish paired SVG through the existing `jobs.export` API/MCP controls and update setup.bat without new dependencies.

## M14 compact proof exports 0.15.12 — 2026-10-24

- Remove SVG proof from the current Workbench bottom bar; keep PNG in the bottom bar and both formats under File → Export. Earlier milestone windows retain their export buttons.
- Suggest timestamp-only SVG filenames matching PNG: `DateTimestamp.svg` in one-page view and `DateTimestamp_Left.svg` or `DateTimestamp_Right.svg` for the selected page in two-page view. SVG still exports one physical page; PNG's paired export is unchanged.
- Preserve approved typography, Maxima, page geometry and paint. Update setup.bat; no new dependencies or file-format changes.

## M14 centered ruler labels 0.15.11 — 2026-10-24

- Center horizontal ruler numbers over their tick marks so facing-page labels no longer run together at the gutter. At very small zooms, omit a crowded end label while retaining its tick and the next page's zero.
- Preserve document geometry, typography, Maxima and paint. Update setup.bat; no new dependencies or file-format changes.

## M14 in-place transliteration 0.15.10 — 2026-10-24

- Remove the Reading copy label, mode dropdown and creation button from the current Workbench ribbon. Add Language → Update transliteration for the existing Thimfora/Transliteration 7 pair, including when the facing gloss/English page is selected in either view mode.
- Refresh exact source slots, paragraph breaks and Maxima without recasing or translating. Retain Roman formatting and existing automatic paragraph alignment; text and spacing undo together. English/gloss text, page geometry and paint stay intact. An already matching column is a no-op.
- Explain replacement of direct Roman edits before applying it; a review guard rejects intervening source/target changes. Publish inspection/update through API/CLI/MCP and keep the frozen M12/M13 conversion interfaces available. Update setup.bat; no new dependency or file-format change.

## M14 quiet desktop launch 0.15.9 — 2026-10-24

- Start the editor without a persistent command window. `launch.bat` hands off to a windowless launcher and returns immediately; all editor arguments remain supported.
- Capture Python output, native output and early startup tracebacks in a separate timestamped `.local/logs/launch-*.log` for each launch. Show an error dialog with the log location on failure; retain structured session diagnostics and the explicit console CLI.
- Update setup.bat to verify the windowless interpreter and exercise the actual batch launch, argument forwarding, output capture and failure reporting. Preserve the approved first-run view and document rendering.

## M14 approved first-run workspace 0.15.8 — 2026-10-24

- Match the approved clean startup view on a fresh installation: maximized Language Workbench, blank Untitled page fitted to height, Select tool, Color / relief, transliteration reading mode and single-page view.
- Fit after the window lays out, using the same calculation as Fit Height. Initialize the new page without an undo step or unsaved-change prompt; opening an existing file retains its saved zoom.
- Default the controls panel to collapsed and unpinned; keep source, diagnostics and guides hidden. Existing workspace preferences and saved document appearances take precedence. Update setup.bat and verify a fresh workspace without local preferences.

## M14 requirements folder 0.15.7 — 2026-10-24

- Group all 15 milestone dependency files under `requirements/`. Update setup.bat, CI, dependency auditing, evidence references and installation instructions; package versions are unchanged.
- Include the folder in release bundles while retaining verification and installation of older bundles with requirements at the root.

## M14 maximized startup 0.15.6 — 2026-10-24

- Open the editor maximized from launch.bat and when opening a document from Explorer. Keep the title bar, menus and normal window controls available. Update setup.bat.

## M14 minimal filename title 0.15.5 — 2026-10-24

- Show only the filename without the native or legacy extension in the title bar, or Untitled before the first save. Remove the app name and title decorations; unsaved state remains in the status bar and close prompt. Keep setup.bat current.

## M14 default Saves folder 0.15.4 — 2026-10-24

- Start Save for new documents, Save As and Open in the project's `Saves` folder (`E:\Vayrshemon\Saves` in this installation). Save As preserves the current filename and converts legacy suffixes to `.vay`; ordinary Save updates an existing file in place.
- Create the folder during setup and when a file dialog needs it. Exclude saved documents from Git; keep existing documents in their current locations. No formatting or rendering changes.

## M14 filename title bar 0.15.3 — 2026-10-24

- Show the actual filename, including its extension, in the title bar. New documents display Untitled; unsaved changes retain the asterisk. Opening another file and Save As update the displayed name.
- Keep internal document titles and Forge identifiers in document metadata, without displaying them as filenames. Update setup.bat; document contents, formatting and rendering are unchanged.

## M14 taskbar identity 0.15.2 — 2026-10-24

- Set a stable Windows AppUserModelID before Qt creates its application/windows, so the taskbar identifies Vayrshemon independently of its Python launcher.
- Use the existing centered color Memon icon as the application-wide icon, retaining the title-bar icon and saved-mode document icons. Both launch.bat and Explorer document opening use this startup path.
- Record startup identity in diagnostics and update setup.bat; no new dependencies or document/rendering changes.

## M14 workspace visibility 0.15.1 — 2026-10-24

- Remember source editor, diagnostics panels and page guides across launches, independently of documents. Fresh workspaces start with these hidden; existing sidebar preferences remain in force.
- Add individual checkable View menu controls. Closing the source editor, Page focus, Edit with diagnostics and API/MCP workspace changes all update the same preferences without changing document formatting or zoom during restoration.
- Update setup.bat; no new dependencies, native-format or API-version changes.

## M14 native files and Explorer previews 0.15.0 — 2026-10-24

- Default Save As to `.vay`, retaining legacy `.vay.json`/`.vaylab.json` imports. Native wrapper 0.6 preserves the editable state and embeds an atomic, validated preview of the saved page or spread.
- Add centered Memon icons for Color / relief, white-on-black and black-on-white Monochrome, with saved-state thumbnails through an isolated native Windows provider. File associations stay per-user; the approved system COM component is installed in Program Files.
- Preserve approved geometry, paragraph alignment, 50/22 pt sizes, 38 pt leading, Maxima and paint. Both pages in all three modes matched M13 proof pixels exactly.
- Add saved-preview inspection and shell status; publish 153 API/CLI/MCP controls. Preserve recovery, verified font backups, export workers and timestamped paired PNG output.
- Update setup.bat, C++/SDK bootstrap, reversible registration, logs, source releases and compatibility tests. Correct the legacy multicolor test to use Color mode, and preserve a reopened sidebar's requested width when its preview reaches minimum size.

## M13 selectable monochrome paper 0.14.5 — 2026-10-24

- Add explicit “Monochrome: white on black” and “Monochrome: black on white” choices to the existing rendering dropdown. Keep the compact ribbon and Color / relief option.
- Persist the paper preference with the document, support Undo/Redo and use the captured choice in PNG/SVG/PDF proofs. Changing it leaves source colors, text, Maxima, fonts, paragraph alignment and geometry untouched.
- Expose optional `view.configure.monochromePaper` (`black`, `white`, or legacy `auto`) through API/CLI/MCP, with synchronized discovery and file contracts. Existing documents retain their appearance until an explicit choice; native format 0.5.0 and 151 controls remain.
- Update setup.bat and regression coverage; no new dependencies.

## M13 true monochrome 0.14.4 — 2026-10-24

- Render every column with white ink on dark paper or black ink on light paper in Monochrome, including colored source text and colored backgrounds. Transparent backgrounds resolve against white paper in this mode. Use neutral antialiasing without colored ClearType fringes.
- Share this presentation across the preview and PNG, outline SVG and PDF proofs, including legacy native-layout documents. Preserve saved colors, font identities, Maxima, glyph positions and the Color / relief treatment.
- Update setup.bat; no new dependencies, API controls or native-format changes.

## M13 automatic paragraph alignment 0.14.3 — 2026-10-24

- Reflow corresponding paragraph starts when text changes in a complete four-column spread. Typing, paste, IME and API edits include the spacing adjustment in the same Undo step. Saves and exports see the committed alignment immediately.
- Preserve text and prior spacing when counts differ or the result would overset; show a nonmodal status and resume on a later fitting edit. Keep all approved fonts, leading, geometry and paint.
- Reuse native shaping and placement for lightweight line measurements without touching painted glyphs or populating the paint cache. Most keystrokes retain their existing wrapping and spacing.
- Add a small × to the source editor header. Closing and reopening the pane do not change the document. Update setup.bat; dependencies, native format, API version and 151-operation count remain unchanged.

## M13 paragraph alignment 0.14.2 — 2026-10-24

- Align the first baseline of each corresponding paragraph across all four columns. Change only paragraph-before spacing; retain text, Maxima, font sizes, exact leading, page geometry and bevel/glow.
- Add Edit → Align paragraph starts across columns and `page.paragraphs.align` through API/CLI/MCP. The operation is undoable, repeatable and rolls back on overset or mismatched paragraph counts. New Forge gloss copies align automatically.
- Update setup.bat; no new dependency. API 0.14.1 exposes 151 operations; native documents and paint engine are unchanged.

## M13 facing PNG export 0.14.1 — 2026-10-24

- Make the PNG button follow the visible one/two-page arrangement. Two-page mode exports `DateTimestamp_Left.png` and `DateTimestamp_Right.png` from one immutable snapshot; single-page mode suggests `DateTimestamp.png` with no document-title prefix.
- Use one chooser and shared timestamp for the pair. Render both pages in one cancellable background job, show both destinations and check both replacement hashes before publishing. An unpaired final page produces only `_Left`; it does not invent a blank right page.
- Extend the existing `jobs.export` API/MCP operation with `page_ids` and matching optional replacement hashes. Keep the 150-operation surface, font treatment, native format and API version unchanged. Update setup and add real button/worker regressions.

## M13 construction gloss 0.14.0 — 2026-10-24

- Fill the reserved third column in a separate facing-page copy with a source-order construction gloss, using compact grammatical labels and the approved 22 pt / 38 pt Roman treatment.
- Add a Forge Gloss workspace with editable, versioned dictionary labels and word-level sense, grammar, context and adaptation details. Retain invalid/stale edits, reject unbound analyses and protect historical versions.
- Preserve the other three columns pixel for pixel, including all Maxima. Store linked source/gloss paragraphs, detect stale text after edits and retain complete diagnostics. Stop on overset instead of reducing approved type sizes.
- Demonstrate experimental language 0.7.0 on the unchanged four-paragraph Tempest example and editorial coda. Preserve all prior history, dictionaries, grammar and variation rules.
- Publish 150 CLI/API/MCP operations and update setup, requirement chain, CI and release validation. Native documents, Forge envelope and paint engine retain their existing versions; no new dependency is required.

## M12 Fit Width alignment 0.13.3 — 2026-10-24

- Fit Width centers the visible page or pair horizontally and aligns its top immediately below the ruler. Repeated clicks return to the top after panning; Fit Height and Center page retain their existing behavior.
- Preserve document formatting and update setup.bat; no dependency changes.

## M12 facing pages and approved reading standard 0.13.2 — 2026-10-24

- Freeze the user-approved left-page reference: 50 pt Thimfora, 22 pt transliteration 7, matching 38 pt baselines, enlarged page and retained paint. New Roman copies/Forge runs use the approved size and leading; the older English baseline remains independently protected.
- Add icon-only one/two-page controls beside a 190 px zoom slider. Persist view mode outside document state. Paint, hit-test, center, pan and fit the selected physical page or facing pair; handle arbitrary page sizes and an unpaired final page.
- Add a saved facing-page demo with a blank left frame and English in transliteration 7 on the far right. Preserve the approved left page pixel for pixel. Cover the custom font's missing hyphen with an explicit, identically styled Times New Roman punctuation run.
- Add `view.pages` to API/MCP (145 operations), retaining API 0.13.0 and native 0.5.0 compatibility. Update setup.bat; no new dependencies.
- Recognize the original Roman p/j sidebearings at the approved size as reviewable ink overhangs using exact font/glyph metrics; retain strict rejection of actual overset and the raw layout diagnostics.

## M12 Roman relief and compact controls 0.13.1 — 2026-10-23

- Reconstruct the Roman style from the matching Translation 1/2 PSD layers: blue overlay, gradient inner/outer glows, smooth inner bevel and satin shading. New Transliteration 7 readings use this separately versioned binding; existing books adopt it explicitly in Paint. Keep the approved three-font treatment and source glyphs intact.
- Consolidate navigation, reading and file actions into one row on wide windows; wrap file actions on smaller windows. Remove the repeated Workbench/preview headings and move application/version information to Help → About.
- Advance the paint engine to 1.2.0, with profile hashes in inspection/export evidence and additive native/API binding contracts. Retain API 0.13.0 and native document 0.5.0; styled documents require this reader. Update setup.bat without new runtime dependencies.

## M12 toolbar refinement — 2026-10-23

- Place Reading copy controls immediately after Fit Width in the navigation row, removing the extra row above the page. Document formatting and rendering are unchanged.

## M12 parallel reading and continuity 0.13.0 — 2026-10-23

- Add the Reading workspace with the user-selected original transliteration 7 Roman forms, literal Times New Roman slots and retained English. Copy exact source characters and Maxima/Minima; do not normalize or guess Unicode respellings.
- Create separate editable reading copies and version-pinned test pages. Preserve approved geometry, sizes, leading and Thimfora 79/81/80 paint; change only the requested right-column font. Retain the original Roman p sidebearing diagnostic for review.
- Propose optional literary subject continuity in separate coherent tests, requiring an explicit adjacent antecedent, matching participant identity and contextual conditions. Retain the fuller reading, exact M11 Tempest text, dictionary and prior cases.
- Demonstrate experimental language 0.6.0, edited versioned wiki, parallel readings, continuity comparisons and the actual timestamped PNG export. Add four API/MCP controls (144 total), Forge envelope 1.4.0, variation definitions 1.2.0, lab engine 1.3.0 and hashed reading evidence verified at release.
- Update setup.bat, pinned requirements, dependency auditing, CI and release checks. No new dependencies; native documents and the paint engine remain unchanged.

## M11 Maxima and topic variation 0.12.0 — 2026-10-23

- Restore sentence-initial Maxima through explicit orthographic letter pairs, including pairs that do not follow Unicode casing. Add an Orthography workspace with a glyph preview, exact guarded apply, pair inventory, policy editor and frozen audits.
- Preserve earlier cases and text; create reviewed bound cases with unchanged scalar offsets. Test all 47 pairs and prevent a wrapped line from creating a new capital.
- Add optional subject-first orders for an established, noncontrast literary topic. Retain prior orders and case constraints; expose available and blocked alternatives. Count watched prefixes by mapped letter identity so capitals cannot conceal repetition.
- Demonstrate experimental language 0.5.0 with eight sentence-initial Maxima, an edited versioned wiki, 256 language cases and the approved two-column Shakespeare page. Preserve dictionary records, English, typography and the actual three-font paint.
- Add seven API/MCP controls (140 total), Forge envelope 1.3.0, variation definition 1.1.0 and lab engine 1.2.0. Pin and verify spelling evidence in page runs and named releases. Correct the new revision's inherited attested label on M10's explicitly proposed discourse rule; preserve historical records.
- Update setup.bat, the pinned requirement chain, CI and contracts without adding dependencies. Native books and the paint engine are unchanged.

## M10 variation in context 0.11.0 — 2026-10-23

- Add optional, context-conditioned surface alternatives while preserving all complete forms, roots, case and event nominalizers. Explicit context gates apply to word and annotated clause tests.
- Add the Variation workspace: guarded definitions, forms inspector, repetition audits, frozen evidence and before/after comparisons using identical watch definitions. Counts are advisory, not naturalness scores.
- Retain old language suites; demonstrate experimental language 0.4.0 with coherent Shakespeare text and a versioned discourse wiki. Preserve the approved two-column presentation and three-font paint.
- Publish six API/MCP operations (133 total), Forge envelope 1.2.0 with monotonic upgrades, and context-aware lab engine 1.1.0. Native books remain 0.5.0.
- Pin variation evidence in page tests and verify it for named releases. Keep setup.bat, requirement chain, CI and bounded validation tests current without new dependencies.

## M9 language integration and releases 0.10.0 — 2026-10-23

- Replace Fit Page with Fit Height and Fit Width. Center single-page views after open, resize, zoom and panel changes, keeping ordinary Hand panning and document geometry independent.
- Merge frozen branch heads through a common ancestor, stable record IDs and field-level conflicts. Record both parents and explicit resolutions; preserve drafts and reject stale plans.
- Pin immutable named language releases to dictionary/wiki snapshots and verified suite/Workbench evidence. Retain unresolved meaning and parsing gaps on experimental releases.
- Add Merges and Releases tabs and six API/MCP operations (127 total). Upgrade Forge projects to 1.1.0 only when merges/releases are used; retain 1.0.0 reads and native document 0.5.0.
- Fix the enlarged-page PNG button: choose supported DPI, retain timestamp names, add missing suffixes, confirm replacement, and refuse to overwrite a destination changed during rendering.
- Update setup.bat, requirement chain, CI, contracts and regressions without new dependencies. Demonstrate a merged Shakespeare release on the unchanged approved presentation.

## M8 executable Language Forge tests 0.9.0 — 2026-10-23

- Add bounded, declarative inventory, inflection, token-analysis and clause rules with independent positive/negative expectations, explicit review/unsupported results and grammar coverage.
- Author rules, cases and bilingual pages in the Forge; preserve historical read-only views and retain invalid or stale edits for recovery.
- Compare one pinned suite against two language versions; persist hashed results through six new API/MCP operations (121 total).
- Demonstrate a proposed literary adaptation of Shakespeare's Tempest with cited roots, back-translations, versioned wiki notes and unchanged approved two-column typography, paint and margins. Preserve soft verse breaks and timestamped proof filenames.
- Bind printed script to exact frozen clause inputs; reject mismatches. Restore history in immutable timestamp order rather than SQLite insertion order.
- Keep setup.bat, pinned requirement chain, CI, contracts and regressions current; no new dependency or native document format.

## M7 Language Forge 0.8.0 — 2026-10-23

- Add a full Forge tab with independent transactional projects, branches, hashed versions, autosaved dictionary/wiki drafts, historical views, typed diffs and verified portable history bundles.
- Expose 115 API/MCP operations with project identity/generation guards and document-independent language mutations; retain all earlier interface modes.
- Create a private source-derived proposal with 751 dictionary records, 12 wiki pages, a subsequent wiki/dictionary revision, separate letter-frequency profiles and a novel bilingual test.
- Generate separate test books from the approved presentation; record language/test/template/render identities, overflow, missing glyphs, collisions and explicit linguistic review limits. Preserve original pixel/geometry regression and timestamped proof dialogs.
- Update setup.bat, dependency chain, CI, contracts and tests; no new external package or native document format.

## M6.1 controls and approved baseline 0.7.1 — 2026-10-23

- Add a permanently reachable collapse/expand rail, pin control, temporary opening and scoped keyboard shortcuts. Persist visibility, pin, width and selected tab outside documents; retain zoom, text, geometry, rendering and undo state.
- Add `ui.sidebar` / `ui.sidebar.inspect` through desktop, CLI and MCP (98 operations), with guarded mutations, retry safety and visible preference failures. Keep discovery compatible with running M6 0.7.0 sessions.
- Record the user's explicit approval of the larger two-column page as a hash-pinned visual baseline with private source, PNG and font-complete backup. Verify exact protected state, geometry and RGBA pixels; retain the original translation fixture too.
- Update setup.bat, setup messages, contracts, tests and documentation. No new dependency, native format, language-data or paint-engine change.

## M6 reliability and navigation 0.7.0 / native format 0.5.0 unchanged — 2026-10-23

- Add explicit Select/Hand tools, fitted-page panning, center/fit controls, scoped keyboard navigation and API/MCP inspection. Panning and tool switches preserve selection, revision, dirty state and undo.
- Reuse unchanged story shaping, scope composition to the current page/connected flows, bound caches, cull offscreen paint and stop hidden-inspector refresh work. Record 100-page/100k-scalar and large decorative-page performance; the 50 ms edit target remains open.
- Export proofs in isolated cancellable workers with immutable snapshots, stale-revision reporting, full logs and exclusive destination publication. Preserve timestamped save suggestions.
- Add verified saved-document/font bundles, visible backup failures, standard-library recovery/inspection and documented interchange.
- Add versioned Windows source installation, atomic activation/rollback, offline wheelhouse setup and dependency/license inventory. Keep setup.bat and CI current; no new dependency or native migration.

## M5 language workbench 0.6.0 / native format 0.5.0 — 2026-10-23

- Add content-addressed language revisions, stable lexical/sense IDs, branching/adoption/diffs and portable hash-checked packages; retain old documents and spellings during migration.
- Import 733 records from both historical translation charts and the language-terms document, with exact source hashes, unresolved rows and competing tense readings. Add orthography/input/transliteration, grammar/morphology and interlinear data contracts.
- Link corpus analyses and dictionary entries to explicit bilingual page ranges; report stale text and older revision pins. Add literal concordances, surface frequencies and exact rational base-12/Unta formatting/parsing.
- Add six desktop panels, typed record editing, searchable printable dictionary/grammar/corpus publishing, and 19 shared API/MCP operations (85 total).
- Suggest local date/time filenames for PNG, SVG proof and Publish exports. Keep the standard black two-column page and its three-font rendering unchanged.
- Update setup.bat, CI, requirements chain, published contracts and tests; no new runtime dependency.

## M4 reference lighting 0.5.3 / paint engine 1.1.0 — 2026-10-23

- Calibrate separate bevels, three-stop interior shading, fine black edge and cyan glow against Individual Glyphs. Record four complete PSD layer styles and the two gradient variants across all 106 mapped PSDs. Preserve the actual 79/81/80 fonts and shared origins.
- Compute bevel distance from the combined fill boundary (no internal overlap seams), retain crisp relief, and expose interior bevel, highlight/shadow strength, normal smoothing, gradient colors, glow range and spread through desktop/API/MCP.
- Screen-blend all page glows before text ink, so neighboring glyphs and English are not washed out and white paper is not darkened by cyan halos.
- Add an opt-in lighting profile. Older recipes keep their previous rendering; new documents and Restore use the new profile. Existing API/native/recipe format versions stay compatible.
- Save the standard two-column demo on black with pale contrasting English; add `verify_m4 --black` and separate ink/halo reference diagnostics. Update setup.bat; no new runtime dependency.

## M4 three-font correction 0.5.2 / paint engine 1.0.2 — 2026-10-23

- Correct the color demo to use the actual 79 outline, 81 interior and 80 glow fonts. The user rejected the previous single-font rendering and counter-only patch as the requested construction.
- Reuse master positions, baselines and scale across layers; preserve additive interior subpaths. Use 80 only for translucent outer glow and 79 for the edge/shadow, with the shadow above the interior.
- Add registered source-layer glyph proofs and per-glyph alignment diagnostics through the existing API/MCP. Validate layer character mappings and test unequal side bearings, overlapping interior paths, and glow-only geometry.
- Preserve the archival fixture; make a separately documented two-column color copy with the evidenced clitic encoding adaptation and current three-font typeface. The proof generator no longer silently substitutes single-font relief.
- Update setup.bat and project standards. No additional runtime dependency; final visual acceptance remains open.

## M4 counter correction 0.5.1 / paint engine 1.0.1 — 2026-10-23

- Correct the solid blue centers in the user's circled glyphs: derived paint follows original ink and preserves every counter instead of filling all closed contours. Explicit three-layer shading remains available.
- Preserve source text, original font identities and page geometry. Existing API 0.5.0, native 0.4.0 and recipe 1.0.0 contracts remain compatible; record the renderer implementation version separately in provenance and proof diagnostics.
- Add synthetic TTF counter checks at two DPIs on white, black and transparent backgrounds, plus regressions for the actual circled historical glyphs. Update setup.bat to run these with the standard parallel-translation suite; no dependency changes.

## M4 studio 0.5.0 / native format 0.4.0 / specification 0.6.0 — 2026-10-22

- Add versioned, editable outline-derived blue bevels, violet interior shading, dark edges, shadow and glow, informed by the original artwork and archived Photoshop settings.
- Bind verified 79/80/81 layers or explicitly derived historical outlines without changing source text/font identities; integrate actual finite paint extents before collision solving.
- Add atomic PNG/SVG/PDF publication, multipage physical sizes, explicit raster fallback/DPI and preflight that accurately declares non-searchable proofs.
- Build reproducible COLR v0/CPAL flat-color fallback fonts with original mono outlines, mappings, palettes, compiler/source/output hashes and independent FreeType validation.
- Add nine API/MCP controls, Paint/Publish desktop tabs and page-focus mode, M1–M3 migration, private reference coverage/proof tooling and M4 regression tests.
- Update setup.bat, pinned requirements and CI. Preserve the standard two-column page, its original fonts and its known overhang diagnostic.
- Keep VISUAL-01 pending user review: shader differences, historical contours and unresolved punctuation mappings remain explicit. No visual baseline is silently approved.

## M4 visual-quality target clarified — 2026-10-22

- Adopt `Inputs/Versions Best/Individual Glyphs` as the user's finished-glyph visual target; explicitly record that M3 rendering is below expectations.
- Add VISUAL-01 as required M4 work: reference-matched contours, blue bevels/highlights, recessed shading, fine edges and glow, with matched-scale comparisons and full-page proof on the standard portrait translation layout.
- Distinguish layout approval from visual acceptance; require reviewed glyph/page appearance and report export-format limitations without silently lowering the target.

## Parallel translation standard 1.0.0 — 2026-10-22

- Record the approved portrait page with two full-height independent columns, Vayrshemon left and English translation right, without title, column headings, or footer.
- Add a versioned formatting definition, persistent project guidance, and a hash-bound local fixture using the actual paired passages and original font runs.
- Add public and local acceptance tests for independent editing, undo, paragraph alignment, save/reopen and PNG export through the existing API. Standard unittest discovery and setup.bat include them without new dependencies.
- Retain the known natural script ink overhang in diagnostics; paragraph alignment is explicit spacing, not automatic semantic linking.

## M3 workbench 0.4.0 / native format 0.3.0 / specification 0.5.0 — 2026-10-22

- Add derived typesetting, baseline grids, leading distribution and Unicode break tailoring with versioned language profiles.
- Add equal-width finite frame flow, keep rules and widow/orphan minima without moving or duplicating source text.
- Inspect advance/ink/reserved-effect bounds and protected joins; repair vertical clearance within explicit frame, expansion and iteration constraints.
- Add isolated kerning comparisons, explicit optical pair rules, dense specimens and before/after baseline diagnostics.
- Preserve Arabic joins across equal-format ranges, use grapheme counts for line columns, canonicalize fallback run order, and prevent duplicate run IDs after replacement.
- Add twelve controls to the shared API/MCP interface (57 total), desktop workbench tabs, M3 schemas, M1/M2 migration and recovery/geometry regressions.
- Update setup.bat and CI for M3; keep the same pinned runtime and preserve the older editor/lab entry points.
- Record real source-font MCP, UI/headless, collision, export and forced-exit recovery evidence. Effects, color-font compilation and searchable publishing remain M4.

## M2 editor 0.3.0 / native format 0.2.0 / specification 0.4.0 — 2026-10-22

- Add multi-page Windows authoring with independent frames, asymmetric margins, rulers, pan/zoom and explicit overflow.
- Add complete transaction undo/redo, find/replace, semantic clipboard, named styles, paragraph alignment/spacing/tabs, tracking, word spacing and baseline controls.
- Add validated atomic native files, previous-save history, interruption recovery with locks/checksums/durability reporting, M1 migration and exact font relocation.
- Expose 45 shared operations through desktop, CLI and MCP; publish separate versioned contracts and preserve the M0/M1 interfaces.
- Add registered recipe/palette selection, physical PNG export and portable outline SVG proof with baked clipping.
- Keep setup.bat current, make launch.bat open M2, and retain the M1 laboratory command.
- Add regression and real source-font MCP/UI/headless/recovery evidence. Keep automatic frame flow/collision repair, color-font compilation and language-workbench features in later milestones.

## M1 laboratory 0.2.0 / specification 0.3.0 — 2026-10-22

- Implement the native Windows font/input lab, headless renderer, and current-user local API/MCP bridge.
- Adopt Qt 6.8.3 for shared layout, native editing/IME/accessibility, and positioned glyph rendering; replace the provisional unimplemented Tauri/Skia adapter.
- Load exact font files privately, preserve same-family distinctions, and register all three source color layers on master origins.
- Add glyph/source/feature/fallback inspection, layer controls, overlays, reference art, custom physical page sizes, and bounded PNG tiles.
- Add revision/idempotency/document-target checks, atomic lab saves, external-change detection, and correlated component logs.
- Correct Qt's emoji-fallback source-index issue through native range queries, and preserve mixed colors, paragraph leading, Unicode, and feature undo through save/reopen.
- Update setup.bat, add launch.bat and generated MCP configuration, publish API/file/tool schemas, and add native regression and measurement evidence.
- Record manual OS IME, external UIA client, and physical monitor-DPI checks as remaining validation; M2/M3/M4 authoring, collision, and font-compilation work stays scoped separately.

## M0 Windows setup — 2026-10-22

- Add `setup.bat` to create or reuse an isolated Python 3.12 environment, install pinned dependencies, and run dependency, contract, and test checks.
- Keep setup output visible, save per-run console and structured check logs, and return a failure exit code for automation.
- Exercise the setup entry point in Windows CI; retain the direct Python checks on Linux.

## Specification 0.2.0 / M0 tools and data 0.1.0 — 2026-10-22

- Complete the M0 evidence-and-contracts milestone: hash all 1,506 assets and register all 103 TTFs.
- Transcribe the 47-letter maxima/minima pairs and 12 Unta digits, bind them to exact font hashes, and explicitly preserve unresolved slots and transliterations.
- Add strict legacy byte/scalar preservation and DOCX evidence extraction with retained font/run information.
- Add initial JSON Schemas, capability matrix, requirements traceability, decision records, and public/local fixture definitions.
- Add structured CLI logs, source-write protection, public synthetic tests, and Windows/Linux CI.
- Keep original Inputs and local logs/extracts out of Git.

## 0.1.0 — 2026-10-22

- Confirm Windows desktop, local files, APIs, and MCP controls as the initial direction.
- Define the editor, font/color pipeline, layout diagnostics, document history, and subsequent language workbench milestones.
- Record legacy encoding, font identity, and three-layer lettering findings from the Inputs archive.
- Add a repeatable comparison of the three source fonts and an evidence snapshot.
- Exclude the original `Inputs/` archive from Git.

## Repository foundation — 2026-10-22

- Initialize `main` and connect it to `smccolm/Vayrshemon`.
- Commit the existing GitHub push helper.


KJV progress (2026-10-26): v31 combined checkpoint saved/reopened, 5900/31102 verses on 4120 pages. All Deuteronomy is included; 25202 verses remain. v32 preserves Joshua 1–6 as a sealed language/native section (6025 total authored); v33 Joshua 7–12 is in native preflight (6203 authored). v34 drafts Joshua 13–18. Whole Bible remains incomplete.
# 2026-11-05 — Historical compact Bible correction 281

- Complete 31,102-verse compact Bible in a new versioned save: 1,912 pages / 956
  duplex sheets, down from 1,952 / 976. Book openings use either side, without
  inter-book blank pages. Title/blank, frontispiece/opening, compact typography,
  mirrored binding margins, Maxima and protected Unta folios remain.
- 10,900 verse texts revised through documented construct phrases, relational
  clitics, dependent pronouns, dependent-clause endings and additive continuation.
  Verse-initial independent “and” drops from 11,096 to 707. Six overt grammatical
  forms and a zero continuation construction; no new lexical roots.
- Dictionary, grammar wiki, all 31,102 Forge fixtures and per-verse change ledger
  belong to historical branch `kjv-historical-flow-281`. Existing editions and
  the modern 0.11 pin remain unchanged. No full Forge ancestry copy is created.
- Setup verifies 281 without regenerating private books. Contrast tests,
  approved parallel-translation regression, full page/folio collision checks,
  exact verse reconstruction and save/reopen checks pass.
