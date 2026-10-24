# Vayrshemon

A Windows desktop editor for custom typography and the long-term development of the Vayrshemon language.

**Status: M14 implemented — .vay documents, version 0.15.9.** Save a single `.vay` file with a centered Memon icon reflecting its saved color mode and an embedded thumbnail of its saved page or facing spread. Old `.vay.json` and `.vaylab.json` documents remain readable. The approved four-column reading, automatic paragraph alignment, 50 pt Thimfora, 22 pt Roman, 38 pt leading, Maxima and bevel/glow are preserved. PNG still exports the visible pair as `DateTimestamp_Left.png` and `DateTimestamp_Right.png`, or the selected single page as `DateTimestamp.png`. There are 153 API/CLI/MCP controls; the native wrapper is 0.6.0, with unchanged editable state.

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
- [M6 navigation, reliability, installation and recovery](docs/M6.md)
- [M6.1 collapsible controls and approved visual baseline](docs/M6.1.md)
- [M13 construction gloss and four-column reading](docs/M13.md)
- [M14 .vay files, Memon icons and saved-page thumbnails](docs/M14.md)
- [M12 parallel Roman reading and discourse continuity](docs/M12.md)
- [M11 Maxima spelling and optional topic orders](docs/M11.md)
- [M10 contextual variation and repetition review](docs/M10.md)
- [M9 merges, releases, centered pages and PNG export](docs/M9.md)
- [M8 language tests, coverage and Shakespeare demonstration](docs/M8.md)
- [M7 Language Forge, source-derived proposal and versioned tests](docs/M7.md)
- [Interchange and exact source recovery](docs/INTERCHANGE.md)
- [Architecture and technical decisions](docs/ARCHITECTURE.md)
- [Findings from the existing Inputs archive](docs/INPUTS.md)
- [Planning revision history](CHANGELOG.md)

`Inputs/` contains the original local reference archive and is excluded from Git. M0 catalogs all 1,506 files by hash, registers all 103 TTFs, and records the current alphabet/numeral mapping. Source code, specifications, schemas, and reproducible test definitions are versioned. Original assets remain intact; runtime logs and extracts live in ignored `.local/`.

The repository is [smccolm/Vayrshemon](https://github.com/smccolm/Vayrshemon). The existing `push_to_github.bat` stages all non-ignored changes, commits, rebases from `origin/main`, and pushes to `main`. Review the staged contents before using it; use explicit Git commands for future feature branches.

## Repeatable research

On Windows, double-click [`setup.bat`](setup.bat), then [`launch.bat`](launch.bat). With Python 3.12 (64-bit) installed, setup creates or reuses `.venv`, installs the pinned M0–M14 Python dependencies, audits notices, and runs all public checks. M14 also builds the native Explorer component with MSVC C++ and the Windows SDK; setup installs the Microsoft build tools through winget if absent. Windows administrator approval installs that component under `C:\Program Files\VayrshemonShell`; file associations remain per-user. An unchanged component needs no further elevation. Python 3.12.7 and Qt 6.8.3 are tested. Logs remain in `.local/logs/`; use `setup.bat --no-pause` for automation. No Rust or Node installation is needed. All milestone dependency files live in [requirements/](requirements/); setup installs `requirements/requirements-m14.txt`.

Normal launches close the command window immediately. Troubleshooting output is saved in `.local/logs/launch-*.log`; a failure dialog points to its log. To deliberately keep a visible console, run `.venv\Scripts\python.exe -u -m vayrshemon editor` from a terminal.

M14 opens maximized with a blank document and the reading layout remembered from your previous session; new workspaces match the approved first-run view: controls collapsed and unpinned, source editor/diagnostics/guides hidden, Select active, Fit Height, Color / relief and single-page mode selected. Toggle each under View. File → Recent documents reopens your save. M14 loads the actual 79/80/81 fonts when Inputs is available. Apply relief in Paint; import the verified language archive in Language. Select clicks a frame to edit; Hand drags the page. The left edge arrow expands/collapses controls; Pin keeps them open. Ctrl+Alt+B toggles the panel and Ctrl+Alt+P toggles pinning. Without Inputs, use system/local fonts and create or import language records. Save documents as `*.vay`. Save for a new document, Save As and Open start in `Saves/` (`E:\Vayrshemon\Saves` here); ordinary Save updates an existing file in place. Setup creates `Saves/`, which is excluded from Git. Recovery, history and verified font-complete backups live in `.local/`. Save As suggests the new extension for old files. M1–M4 imports require a new path; M5–M13 files preserve their editable state and gain the new wrapper when saved. Older app releases cannot read the new wrapper; retain the original or its backup for rollback. `launch.bat --m13`, `--m12`, `--m11`, `--m10`, `--m9`, `--m8`, `--m7`, `--m6`, `--m5`, `--m4`, `--m3`, `--m2` and `python -m vayrshemon lab` retain earlier interfaces. PNG and SVG proof dialogs suggest date/time filenames and export in cancellable background jobs.

Setup also writes `.local/mcp-config.json` for an MCP client. It discovers the active editor/lab and connects through a current-user-only local socket; mutations require the document ID, current revision, and an idempotency key. The same interface is available as `.venv\Scripts\python -m vayrshemon call session.status`. See the [M6 guide](docs/M6.md) for headless operation and the [published tool schemas](data/file-mcp-tools.json).

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
