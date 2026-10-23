# Planning revision history

These entries distinguish specification revisions from evidence-tool and future application releases.

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
