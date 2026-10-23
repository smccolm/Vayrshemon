# Vayrshemon

A Windows desktop editor for custom typography and the long-term development of the Vayrshemon language.

**Status: M4 implemented for visual review — Windows glyph studio, version 0.5.1.** Editable outline-derived bevel, shading, edge, shadow and glow treatments target the Individual Glyphs artwork. Historical fonts now preserve their open counters; interior fills require explicit layer fonts. M4 adds reproducible flat COLR/CPAL font builds, explicit raster proof export to PNG/SVG/PDF, effect bounds and publication preflight. All 66 operations share desktop, CLI and MCP controls. Native format is 0.4.0. **Final visual acceptance remains open**; the language workbench is M5.

The editor will support custom page dimensions, English and multilingual documents, Thimfora lettering, monochrome TTFs, and editable color treatments built from those fonts. APIs, MCP automation, layout inspection, and recoverable document history are part of the foundation.

- [Delivery plan and acceptance criteria](docs/PLAN.md)
- [Standard portrait translation layout and regression test](docs/FORMATTING.md)
- [M0 results, commands, and remaining uncertainties](docs/M0.md)
- [M1 launch, API/MCP, measurements, and limitations](docs/M1.md)
- [M2 authoring, recovery, API/MCP and validation](docs/M2.md)
- [M3 typesetting, collision policies, API/MCP and validation](docs/M3.md)
- [M4 paint, color-font builds, publishing and visual review](docs/M4.md)
- [Architecture and technical decisions](docs/ARCHITECTURE.md)
- [Findings from the existing Inputs archive](docs/INPUTS.md)
- [Planning revision history](CHANGELOG.md)

`Inputs/` contains the original local reference archive and is excluded from Git. M0 catalogs all 1,506 files by hash, registers all 103 TTFs, and records the current alphabet/numeral mapping. Source code, specifications, schemas, and reproducible test definitions are versioned. Original assets remain intact; runtime logs and extracts live in ignored `.local/`.

The repository is [smccolm/Vayrshemon](https://github.com/smccolm/Vayrshemon). The existing `push_to_github.bat` stages all non-ignored changes, commits, rebases from `origin/main`, and pushes to `main`. Review the staged contents before using it; use explicit Git commands for future feature branches.

## Repeatable research

On Windows, double-click [`setup.bat`](setup.bat), then [`launch.bat`](launch.bat). With Python 3.12 (64-bit) installed, setup creates or reuses `.venv`, installs the pinned M0–M4 dependencies including Qt 6.8.3, NumPy/SciPy and independent proof validation libraries, and runs all public checks. Python 3.12.7 is the tested version. Setup keeps output visible and saves a separate log for each run in `.local/logs/`. It pauses before closing; use `setup.bat --no-pause` for automation. No Rust, Node, or compiler install is needed for this milestone.

M4 opens a blank document and loads the actual 79/80/81 fonts when the local Inputs archive is available. Apply relief to the selected font in the Paint tab. Without Inputs, it uses the system English font and can load local TTFs. Save documents as `*.vay.json`; recovery and previous-save history live in `.local/`. Existing M1–M3 files migrate on open and save to a new M4 path. Original fonts are referenced by hash and local path, never uploaded automatically. `launch.bat --m3`, `launch.bat --m2` and `python -m vayrshemon lab` retain earlier interfaces.

Setup also writes `.local/mcp-config.json` for an MCP client. It discovers the active editor/lab and connects through a current-user-only local socket; mutations require the document ID, current revision, and an idempotency key. The same interface is available as `.venv\Scripts\python -m vayrshemon call session.status`. See the [M4 guide](docs/M4.md) for headless operation and the [published studio tool schemas](data/studio-mcp-tools.json).

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
