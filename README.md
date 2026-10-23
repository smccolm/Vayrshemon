# Vayrshemon

A Windows desktop editor for custom typography and the long-term development of the Vayrshemon language.

**Status: M5 implemented — Windows language workbench, version 0.6.0.** Versioned orthographies, 733 locally imported lexical records, grammar/morphology, interlinear corpus links, exact base-12/Unta values and printable books now accompany the editor. Historical alternatives and uncertain readings remain explicit. All 85 operations share desktop, CLI and MCP controls; native format is 0.5.0. The existing Individual Glyphs treatment keeps the actual Thimfora 79 outline, 81 interior and 80 glow at shared master origins. **Final M4 visual acceptance remains open.**

The editor will support custom page dimensions, English and multilingual documents, Thimfora lettering, monochrome TTFs, and editable color treatments built from those fonts. APIs, MCP automation, layout inspection, and recoverable document history are part of the foundation.

The current reference treatment includes separate bevels, per-glyph interior gradients measured from the original PSDs, and cyan Screen glow. `python -m tools.verify_m4 --black` builds the standard portrait translation review with pale English on black paper. See [M4 lighting validation](docs/research/m4-lighting-validation.json) for the comparisons and 112-test setup run.

- [Delivery plan and acceptance criteria](docs/PLAN.md)
- [Standard portrait translation layout and regression test](docs/FORMATTING.md)
- [M0 results, commands, and remaining uncertainties](docs/M0.md)
- [M1 launch, API/MCP, measurements, and limitations](docs/M1.md)
- [M2 authoring, recovery, API/MCP and validation](docs/M2.md)
- [M3 typesetting, collision policies, API/MCP and validation](docs/M3.md)
- [M4 paint, color-font builds, publishing and visual review](docs/M4.md)
- [M5 language revisions, lexicon, corpus, exact numbers and publishing](docs/M5.md)
- [Architecture and technical decisions](docs/ARCHITECTURE.md)
- [Findings from the existing Inputs archive](docs/INPUTS.md)
- [Planning revision history](CHANGELOG.md)

`Inputs/` contains the original local reference archive and is excluded from Git. M0 catalogs all 1,506 files by hash, registers all 103 TTFs, and records the current alphabet/numeral mapping. Source code, specifications, schemas, and reproducible test definitions are versioned. Original assets remain intact; runtime logs and extracts live in ignored `.local/`.

The repository is [smccolm/Vayrshemon](https://github.com/smccolm/Vayrshemon). The existing `push_to_github.bat` stages all non-ignored changes, commits, rebases from `origin/main`, and pushes to `main`. Review the staged contents before using it; use explicit Git commands for future feature branches.

## Repeatable research

On Windows, double-click [`setup.bat`](setup.bat), then [`launch.bat`](launch.bat). With Python 3.12 (64-bit) installed, setup creates or reuses `.venv`, installs the pinned M0–M5 dependencies including Qt 6.8.3, NumPy/SciPy and independent proof validation libraries, and runs all public checks. M5 adds no new external dependency. Python 3.12.7 is the tested version. Setup keeps output visible and saves a separate log for each run in `.local/logs/`. It pauses before closing; use `setup.bat --no-pause` for automation. No Rust, Node, or compiler install is needed for this milestone.

M5 opens a blank document and loads the actual 79/80/81 fonts when the local Inputs archive is available. Apply relief in Paint; import the verified local language archive in Language. Without Inputs, use system/local fonts and create or import language records. Save documents as `*.vay.json`; recovery and previous-save history live in `.local/`. M1–M4 files migrate and save to a new M5 path. Original fonts remain hash/path references. `launch.bat --m4`, `--m3`, `--m2` and `python -m vayrshemon lab` retain earlier interfaces. PNG and SVG proof save dialogs suggest date-and-time filenames.

Setup also writes `.local/mcp-config.json` for an MCP client. It discovers the active editor/lab and connects through a current-user-only local socket; mutations require the document ID, current revision, and an idempotency key. The same interface is available as `.venv\Scripts\python -m vayrshemon call session.status`. See the [M5 guide](docs/M5.md) for headless operation and the [published language tool schemas](data/language-mcp-tools.json).

After setup, run tools directly through the project environment. The public checks work without Inputs:

```powershell
.venv\Scripts\python -m tools.m0 check
.venv\Scripts\python -m unittest discover -s tests -v
```

See the [M0 guide](docs/M0.md) for installation, catalog regeneration, source verification, and legacy decoding.

Run this read-only comparison from the repository root:

```powershell
.venv\Scripts\python tools/inspect_font_layers.py --root .
```

It compares the three source TTFs used by the archived color-lettering instructions. The checked-in [audit](docs/research/font-layer-audit.json) records their hashes and metrics; it does not contain the fonts themselves.
