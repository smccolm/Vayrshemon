# Planning revision history

These entries distinguish specification revisions from evidence-tool and future application releases.

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
