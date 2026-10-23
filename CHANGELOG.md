# Planning revision history

These entries distinguish specification revisions from evidence-tool and future application releases.

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
