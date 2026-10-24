# Vayrshemon editor: delivery plan

Revision **0.17.0**, 2026-10-24. Status: M0–M14 implemented, including [M6.1 panel controls and approved visual baseline](M6.1.md), [M7 Language Forge](M7.md), [M8 executable tests](M8.md), [M9 merges and releases](M9.md), [M10 contextual variation](M10.md), [M11 Maxima and topic orders](M11.md), [M12 parallel reading and continuity](M12.md), [M13 abbreviated construction gloss](M13.md), and [M14 native files and Explorer previews](M14.md). The approved facing spread has script, Roman reading, construction gloss and English, with the accepted page geometry, Maxima and font treatments preserved. Its approved reference is protected separately from broader M4 glyph-inventory coverage. M6 records a remaining large-document edit-latency gap against the provisional 50 ms target. External OS IME, Windows UIA client, and physical multi-monitor checks remain explicitly listed in [M1](M1.md).

## 1. Product commitment

Build a Windows desktop editor that can become the authoring environment for an entire constructed language. The first useful release must let us write, revise, inspect, save, and export real documents using the existing script. Subsequent releases will add the structured lexicon, grammar, corpus, and publishing capabilities needed to develop the language over years.

Confirmed requirements: local files; custom page widths and heights; monochrome TTFs and color fonts derived from them; English-only, Vayrshemon-only, and mixed-language pages; extensive control over spacing and collisions; versioning; programmatic control through APIs and MCP; accessible troubleshooting output.

The approved default bilingual format and recurring acceptance case is [the portrait parallel translation page](FORMATTING.md): exactly two full-height independent columns, Vayrshemon left and English translation right, without title, column headings, or footer. Use it for future bilingual demos and milestone regression testing alongside the existing stress cases.

Working spelling is **Vayrshemon**, matching the repository and archive. Language, script, and font names will be separate metadata, so display names can change without changing persistent IDs.

Architecture proposals below are engineering choices to validate, not additional user decisions required before work can proceed. Technical details and source references are in [ARCHITECTURE.md](ARCHITECTURE.md); archive evidence is in [INPUTS.md](INPUTS.md).

## 2. Requirements and proof of completion

| ID | Requirement | Acceptance evidence |
| --- | --- | --- |
| PAGE-01 | Independently configurable width and height, including mixed sizes within one document; mm, inches, and points | Enter fractional dimensions, save/reopen, and verify physical export size independently of zoom and display scaling |
| PAGE-02 | Page margins, bleed, guides, backgrounds, text frames, and overflow behavior | Overlong text flows, overflows, or clips according to an explicit policy; no silent loss |
| TEXT-01 | English, Vayrshemon, and mixed-language text at span level | One paragraph contains both; selection, search, clipboard, and undo preserve language and orthography metadata |
| TEXT-02 | Reliable editing | Keyboard, pointer selection, navigation, IME composition, dead keys, paste, deletion, undo/redo, and accessibility operate on meaningful text boundaries |
| FONT-01 | Load local monochrome TTFs without installing them globally | Two files with the same internal family name remain distinguishable; missing or changed files produce an explicit diagnostic |
| FONT-02 | Editable color treatments from the original TTF layers | Edit one logical text run; every color layer stays registered and follows the same layout |
| FONT-03 | Build portable color fonts | A reproducible build produces a validated COLR/CPAL font and a compatibility report; unsupported effects are identified |
| VISUAL-01 | Meet the user's finished-glyph visual standard | Compare against `Inputs/Versions Best/Individual Glyphs`; verify contours, blue bevel/highlight detail, recessed shading, fine edges and glow at reading and detail sizes, in the editor and exports |
| LAYOUT-01 | Detailed paragraph and line controls | Explicit font size, tracking, word spacing, kerning, baseline shift, line-height modes, paragraph spacing, alignment, and break policies |
| LAYOUT-02 | Explainable collision handling | Inspect offending geometry; choose warn, allow, or constrained repair; intentional overlaps remain possible |
| DATA-01 | Durable, portable documents | Save/reopen semantic equality; recovery after interrupted writes; migrations preserve a prior readable copy |
| VERSION-01 | Reconstruct a historical result | Resolve document revision, exact font hashes, mapping and recipe revisions, and engine versions; replay the same fixture |
| AUTO-01 | APIs and MCP for meaningful operations | Create, edit, inspect, render, diagnose, save, and export through the same command contracts used by the UI |
| DEBUG-01 | Troubleshooting visibility | Correlated UI, core, renderer, importer, build, and MCP logs plus a reproducible problem bundle |
| EXPORT-01 | Useful publishing outputs | PNG, SVG, and PDF have checked dimensions and visual comparisons; text extraction and effect limitations are reported |
| LANG-01 | Grow into a language workbench | Stable links from document spans to orthography, lexemes, senses, analyses, examples, and source evidence |

“Arbitrary page dimensions” means free numeric dimensions rather than a preset list. Storage precision, rendering memory, export formats, and printers have finite limits. The engine must validate dimensions, tile large surfaces, and explain format-specific limits; it must never silently resize or crop a page. An unbounded scrolling draft surface can be a later view of the same content.

## 3. Decisions that protect future revisions

1. **Meaning survives appearance changes.** Preserve original legacy codes and their exact mapping profile during import. Introduce stable script-symbol identities and a versioned orthography model before interpreting those codes as language data.
2. **One layout authority.** UI, print/export, CLI, and MCP consume the same shaped runs and layout results. Browser CSS text measurement will not decide pagination.
3. **Editable text survives visual effects.** Color recipes reference the same logical text and positioned glyphs. The editor retains source text when an export must flatten an effect.
4. **Every user action has an inspectable command.** Commands have revision checks, undo semantics, structured results, and trace IDs. Agent tools use these contracts.
5. **Old work remains recoverable.** Changing a font, recipe, schema, or engine creates an explicit new revision and a comparison, rather than invisibly rewriting history.
6. **Language rules remain revisable.** Attested, proposed, deprecated, disputed, and unknown data are distinct. Blanks remain unresolved unless an explicitly authorized proposed version makes a documented extrapolation. The user authorized that first extrapolated branch for M7.

## 4. Delivery sequence

Milestones are gated by working evidence, not calendar guesses. Each ends in a runnable checkpoint, recorded limitations, a regression set, and a versioned change log. Revisit scope after the font/input spike gives us actual performance and compatibility data.

### M0 — Evidence and contracts

**Complete:** 1,506 assets hashed; 103 fonts registered; the 47 letter pairs, 12 digits and remaining cmap slots are mapped or explicitly unresolved; schemas, capability/requirement/decision records, fixtures and public validation tests are implemented. See [M0 results and commands](M0.md). Complete Word import, historical mappings, rendering and the live MCP bridge remain later work.

Deliver:

- Asset catalog with relative paths, hashes, source relationships, and review status; keep original assets in ignored `Inputs/`.
- Font registry starting with Thimfora 79, 80, 81, transliteration 7, and the older naming-collision examples.
- Character mapping workbook/data for the 47-letter maxima/minima inventory, 12 Unta digits, and punctuation. Each entry has source evidence and confidence.
- Requirements IDs, initial document/command schemas, capability matrix, and architecture decision log.
- A small fixture selection: alphabet and digits, mixed-language examples, kerning sequences, line-spacing stress cases, and color references.

**Exit gate:** every initial symbol is either mapped with evidence or explicitly unresolved; all selected assets are identified by hash; legacy import never guesses away an unmapped character. Public CI has synthetic or redistributable fixtures; local tests resolve the ignored archive by hash.

### M1 — Font, rendering, and input laboratory

**Implemented:** Qt 6.8.3 native text/input adapter, one-page lab window, shared headless geometry and rendering, private hash-bound fonts, registered three-layer colors, editable multilingual text, accessibility inspection, revision-checked API/MCP, atomic lab saves, and measurements. See [M1 results and limitations](M1.md). This replaces the provisional Tauri/Skia laboratory route; that route was not tested or declared to have failed. M1 remains a laboratory, not the full M2 authoring release.

Deliver:

- A minimal Windows window plus headless runner that loads the actual TTFs, shapes text, and displays arbitrary-size page surfaces.
- Side-by-side monochrome, registered three-layer color, and reference-image views. Layer toggles, origin markers, baseline and ink-bound overlays.
- Editable text with caret hit-testing, selection, horizontal/vertical navigation, clipboard, undo, IME composition, and accessibility inspection.
- Shape inspector: source units, clusters, glyph IDs, advances, offsets, selected font, active features, and fallback reason.
- Structured logs from all running components and an initial MCP inspect/render/edit route.
- Measurements for rendering transport, redraw latency, memory, DPI changes, and save/reopen of a minimal document.

**Exit gate:** actual source fonts render and remain aligned; mixed English/script typing and IME work; UI and headless geometry agree; selection follows visible glyph clusters; the accessibility tree exposes meaningful text. If the proposed shell/input bridge fails this gate, change the adapter before committing to the UI framework. Record screenshots and metrics from the successful route.

### M2 — First usable editor

**Implemented:** native multi-page authoring with independent frames, complete transaction undo, semantic clipboard, styles and paragraph controls, atomic saves/history, forced-exit recovery, M1 migration, missing-font resolution, 45 API/MCP operations, PNG and outline SVG proof. The real source-font acceptance runner composes through live MCP and verifies text/geometry across UI, save/reopen, headless rendering and recovery. See [M2 usage, evidence and limits](M2.md). Automatic text flow between frames is deferred to the later layout work; M2 retains overflow explicitly.

Deliver:

- New/open/save/save-as, recent files, recovery, undo/redo, find/replace, and basic styles.
- Custom page sizes, per-page overrides, margins, text frames, zoom, pan, rulers, and explicit overflow indicators.
- English-only, script-only, and mixed-language documents with correct clipboard representations.
- Local font loading, monochrome text, registered flat-color layers, and editable palette/recipe selection.
- Line and paragraph spacing, alignment, tabs, tracking, kerning controls, and baseline adjustment.
- Native document format with schema validation, history, atomic save, migration hooks, and missing-asset handling.
- CLI/MCP parity for all these operations; PNG export and initial vector export proof.

**Exit gate:** compose a real mixed-language page, change its dimensions, edit both languages, switch monochrome/color, close/reopen, recover an interrupted session, and reproduce the page through MCP. Geometry and text must round-trip. This milestone is a usable editing tool even while richer visual effects remain in development.

### M3 — Typesetting and collision workbench

**Implemented:** derived native shaping, explicit language break profiles, baseline grids, equal-width finite frame flow, paragraph keeps and widow/orphan minima, conservative bounds with protected joins, bounded vertical repair, explicit optical pairs, dense specimens and 57 shared operations. Save/reopen, subprocess recovery and UI/headless proof retain source and geometry. See [M3 scope, evidence and limits](M3.md); automatic page creation, variable-width flow, exact contour collision and dictionary hyphenation remain future extensions.

Deliver:

- Exact, minimum, and proportional line-height modes; leading distribution; baseline grids; paragraph before/after spacing; keep-with-next and widow/orphan control.
- Unicode-aware line breaking with versioned language tailoring; explicit discretionary breaks and a future hyphenation interface.
- Separate advance, ink, stroke, and effect bounds; horizontal and vertical collision reports.
- Warn/allow/repair policies with minimum clearance, maximum expansion, fixed-page constraints, and visible explanations.
- Controlled optical adjustments stored separately from font kerning. Bounded solver iterations, deterministic tie-breaking, and unresolved-constraint output.
- Kerning/pair explorer, dense alphabet specimens, baseline comparisons, and before/after layout differences.

**Exit gate:** no automatic change to text or font size; no separation of intentional connected glyphs or marks; constrained repairs either meet their documented clearance or return a stable explanation. Reflow terminates and remains reproducible.

### M4 — Color-font studio and publishing

Implementation: application 0.5.3, API 0.5.0, native format 0.4.0. The 2026-10-23 correction requires the actual registered 79/81/80 fonts; single-font approximations do not satisfy the visual target. See [M4](M4.md) for paint controls, explicit COLR v0 fallback, PDF/SVG/PNG proof exports, independent validation and remaining review. The visual gate below is still active; implementation and passing tests do not imply approval.

**Visual quality is an outstanding requirement.** The user identified `Inputs/Versions Best/Individual Glyphs` as the quality reference on 2026-10-22. Its 128 JPEG references cover maxima, minima, Unta and punctuation. The current M3 monochrome outlines and registered flat colors do **not** satisfy this target. Approval of the portrait translation layout establishes page structure, not approval of the current glyph appearance.

Start M4 with **reference-quality glyph rendering (VISUAL-01)**, before treating color-font compilation as complete:

1. Bind the reference images to the existing asset hashes and verified glyph identities. Record unresolved or historical font correspondences rather than guessing a mapping. Inspect the full set; the initial visual review sampled `Maxima_1_Jiam.jpg`, `Minima_1_Jiam.jpg`, `Unta_0_Pholim.jpg` and `Punctuation_3_Period.jpg`.
2. Build a reproducible, editable treatment that reproduces the reference contours and proportions, luminous blue bevels and highlights, dark blue/violet recessed channels, fine dark edges, and controlled soft outer glow. Record any shape mismatch in the underlying TTF separately from a paint/effect mismatch.
3. Compare reference and rendered glyphs side by side and with aligned overlays at matched scale on the reference black background. Check reading size, enlarged detail, zoom/DPI changes, and light/transparent output separately. Preserve negative spaces, narrow joins and punctuation detail; avoid clipped glow, jagged contours and halos between registered layers.
4. Apply the actual three-font treatment to the [standard portrait translation page](FORMATTING.md), preserving its two independent columns and attested paired passages. Keep archival imports intact; use an explicitly documented review copy when adopting the 79/81/80 typeface and its encoding, then measure paragraph alignment again. Use this full-page proof to check readability, effect clearance, line collisions and export fidelity; isolated attractive glyphs alone do not pass.
5. Establish reviewed visual baselines and comparison tolerances, with an explicit record of remaining differences. Completion requires the user's visual acceptance of representative glyphs and the standard page, plus coverage checks across the reference set. Passing geometry tests or successfully building a color font does not establish visual acceptance.

Deliver:

- Versioned paint recipes for fills, gradients, strokes, shadows, glow, and bevel-style treatments, with accurate effect extents.
- Rebuildable color font pipeline: source TTF hashes, glyph mapping, palettes, recipes, compiler versions, output hashes, and validation reports.
- COLR/CPAL output for supported treatments; explicit alternatives for effects outside that format. Preserve a monochrome fallback.
- Page PNG, SVG, and PDF export; deliberate raster fallback at specified resolution; multi-page print proof and color/background checks.
- Export preflight for page dimensions, missing fonts, overset text, unsupported effects, font embedding, and text-extraction behavior.

**Exit gate:** satisfy VISUAL-01 against the Individual Glyphs references, compare exported pages against the editor, check physical size, validate the generated font in an independent renderer, and test copying/searching exported text. If a target font format cannot reproduce a treatment, report that limitation and provide an explicit supported export path; do not silently reduce the visual target to flat fills. Decorative output must never be presented as semantically faithful searchable text when it is only an image or outline.

### M5 — Language workbench

Implemented in application 0.6.0 / API 0.6.0 / native format 0.5.0. See [M5](M5.md) for workflows, evidence and limits. The local seed retains 733 lexical records from competing sources, two corpus pairs, seven tense forms and explicit uncertainty. This is structured language authoring, not approval of historical readings as canonical rules.

Delivered vertical increments:

1. Orthography registry, symbol inventory, input layouts, transliteration profiles, and reversible mappings where possible.
2. Lexicon with stable entry and sense IDs, pronunciations/IPA, parts of speech, definitions, examples, variants, etymologies, status, and citations.
3. Morphology and grammar data: roots, affixes/clitics, paradigms, inflection, derivation, tense/aspect, pronouns, and construction examples.
4. Interlinear glossing, aligned translations, corpus search, concordances, frequency analysis, and links between dictionary entries and document occurrences.
5. Exact base-12 number representation and Unta formatting, including rational values and versioned reading conventions.
6. Grammar-book and dictionary publishing from the same structured data, plus portable data export and later audio links.

**Exit gate for each increment:** real examples from the archive can be represented without erasing uncertainty or competing revisions. A language revision identifies the rules and lexicon used by a document; adopting a new revision is inspectable and reversible. Changes to language data do not silently rewrite quotations or historical documents.

### M6 — Long-term reliability and release discipline

Implemented in 0.7.0: Select/Hand navigation, page/flow-component layout, bounded shaping reuse, cancellable isolated proof workers, verified font-complete backups, standard-library recovery, versioned source installs/rollback, dependency inventory and 96 API/MCP operations. [M6 evidence and limits](M6.md) distinguish automated verification from remaining physical accessibility checks and performance targets. No new native format or dependency is introduced.

Harden throughout development; complete before relying on the app as the only authoring tool:

- Large-document editing, paginated and unusually large-page performance, incremental reflow, bounded caches, and cancellable background jobs.
- Windows installer/update/rollback path; independent document backups and a recovery exercise on a clean installation.
- Accessibility, keyboard-only workflows, migration compatibility, and an audited dependency/license inventory.
- Exported interchange documentation and an offline command-line recovery/inspection utility.

Browser support, real-time collaboration, plugins, advanced vertical typography, and GPU-specific optimizations are later decisions. Their extension points should remain possible without delaying the first reliable Windows editor.

## 5. Validation strategy

| Suite | Examples | Required observation |
| --- | --- | --- |
| Source fonts | All selected glyphs, missing glyph, duplicated family names, GPOS/kern interaction | Font hash, mapping, glyph IDs, positions, and explicit substitution policy |
| Editing | Combining marks, ligatures, surrogate pairs, mixed direction, IME, undo grouping | Correct semantic ranges, caret affinity, retained composition and metadata |
| Layout | Tall/wide/tiny pages, dense lines, overhangs, negative spacing, long unbreakable content | Stable overflow and collision diagnostics; bounded memory and solver work |
| Color | Three-layer text, gradients, alpha, glow, DPI and zoom changes | Same origins and advances; no clipped effects or raster seams |
| Visual fidelity | Individual Glyphs reference set and the standard portrait translation page | Matched-scale reference comparisons, reviewed bevel/shading/glow detail, readable page text, and explicit user visual acceptance; current M3 rendering remains below target |
| Persistence | Crash during write, truncated journal, missing font, external edit, old schema | Recoverable last durable revision and a clear conflict/migration report |
| Automation | Stale revision, retried mutation, cancellation, concurrent manual edit | No double-application or lost edits; structured errors and trace IDs |
| Publishing | Physical units, backgrounds, raster effects, copy/search, large dimensions | Visual proof plus semantic and format-limit reports |
| Language | Ambiguous transliteration, conflicting grammar sources, renamed symbols | Preserved provenance and stable links; unresolved meaning remains visible |

Use Unicode conformance data for the pinned segmentation/bidi versions; shaping fixtures for glyph positions; property/fuzz tests for parsers, history, transforms, and bounded layout; image comparisons for visual changes. A changed golden image requires an explanation, not automatic acceptance. Compare geometry separately from raster pixels so antialiasing differences do not conceal layout regressions.

Provisional performance budgets, to measure and ratify in M1 on a recorded reference machine: p95 key-to-visible feedback below 50 ms for the active page; a 16.7 ms interactive frame budget for ordinary pan/selection; no whole-document reflow for a local edit unless pagination dependencies require it. Benchmark a 100,000-character, 100-page synthetic document and a large decorative page. Record hardware, cold/warm state, font and effect complexity; publish memory and large-page limits after measurement rather than promising unlimited capacity.

## 6. Versioning and the revision loop

| Item | Versioning policy |
| --- | --- |
| Code, plans, schemas, migration scripts, test definitions | Git commits with focused changes; milestone tags and release notes; dependency/toolchain locks |
| Original Inputs | Keep untouched and ignored; maintain relative-path/hash manifests and a separately configured backup |
| Derived fonts and recipes | New artifact revision, source hashes, tool versions, generation recipe, comparison report; retain earlier artifacts |
| Documents | Stable IDs, monotonic revisions, durable journal, checkpoints, named revisions, semantic diffs, and recovery |
| Language data | Stable entity IDs and explicit revisions; provenance and migration records; historic documents pin their language revision |
| Debug sessions | Correlated logs and replay bundle outside source control by default; intentional, minimized regression cases go into Git |

Git is source history; it is not the sole backup of the language archive or live documents. M0/M2 will define the backup location and retention with the user before enabling storage outside the project. Do not automatically upload the ignored archive or debug bundles.

For each requested revision: capture a reproducing document or operation sequence; identify affected requirements; implement the smallest coherent change; run relevant checks; inspect visual/semantic differences; record compatibility effects; commit a named checkpoint. Update this plan when the direction changes. Keep incomplete investigations and unresolved decisions visible.

## 7. Immediate implementation queue

M13 now supplies version-pinned, abbreviated word glosses for exhaustively annotated test pages and keeps all three existing columns unchanged. Next gloss work: author-reviewed internal morpheme segmentation, ambiguity displays, implicit-participant notation, and integration of gloss proof manifests into named-release evidence. Keep full explanations in Forge while preserving the compact four-column reading surface. Do not guess analyses for unannotated prose or turn the source's singular `we` into an accepted collective rule without language-author review.

1. Complete the remaining physical OS/IME/accessibility checks listed in M1 on the user's chosen input setup; retain the passing native event and provider regressions.
2. Preserve the approved enlarged-page baseline introduced by M6.1. Continue broader Individual Glyphs inventory checks separately; no automatic replacement of approved state, geometry or pixels.
3. Reduce full-state snapshot/validation/undo cost and long-paragraph shaping. M6's 100-page/100,000-scalar case limits reshaping to the changed story and meets the measured pan budget, but p95 edit-through-page-paint is 247 ms, above the provisional 50 ms target.
4. Keep setup.bat, published API/MCP schemas, regression tests, and milestone evidence updated with every dependency or behavior change.
5. Expand the M5 language data through cited revisions: verify historical font mappings and IPA, adjudicate competing tense readings, and develop real paradigms and corpus segmentation. Do not infer these from glyph appearance.
6. M7 is implemented: top-level Forge workspace, independent project history and branches, version-bound dictionary/wiki, source-derived proposal and Run in Workbench. M8 provides a bounded finite compiler and frozen-case comparisons; M9 provides explicit merges and immutable releases. M10 adds optional context-conditioned forms and advisory repetition inspection. M11 restores mapped sentence-initial Maxima, previews exact spelling changes, adds optional established-topic clause orders and makes prefix counts aware of paired letter identities. M12 adds exact original-font Roman readings, preserving all symbol slots and case, and a separate optional subject-continuity proposal checked against explicit adjacent antecedents. Prior spellings, complete forms, orders and tests remain available. Next, broaden coherent samples across dialogue, narrative and ceremonial registers; document proper names, abbreviations, quotations, information structure and discourse continuity. Develop collocations, polysemy and productive derivation through separate cited proposals before introducing frequency preferences. Human linguistic acceptance, a broader grammar and richer criss-cross merge-base handling remain open. Keep software, language, presentation, document and test-run identities separate. Mechanical rule assertions do not certify literary meaning, naturalness or general prose grammar.

The first demo should answer a concrete question: **can we type and revise real English and Vayrshemon on a custom-sized page, with editable color lettering, and inspect exactly why every glyph and line is where it is?**
