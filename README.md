# Vayrshemon

A Windows desktop editor for custom typography and the long-term development of the Vayrshemon language.

**Status: M1 implemented — native Windows font and input laboratory, version 0.2.0.** M0 evidence/schema tooling remains 0.1.0; specification revision is 0.3.0. The lab has editable mixed-language text, custom page sizes, registered color layers, glyph inspection, local persistence, and live APIs/MCP. Full multi-page editing, recovery, collision repair, and portable color-font compilation remain later milestones.

The editor will support custom page dimensions, English and multilingual documents, Thimfora lettering, monochrome TTFs, and editable color treatments built from those fonts. APIs, MCP automation, layout inspection, and recoverable document history are part of the foundation.

- [Delivery plan and acceptance criteria](docs/PLAN.md)
- [M0 results, commands, and remaining uncertainties](docs/M0.md)
- [M1 launch, API/MCP, measurements, and limitations](docs/M1.md)
- [Architecture and technical decisions](docs/ARCHITECTURE.md)
- [Findings from the existing Inputs archive](docs/INPUTS.md)
- [Planning revision history](CHANGELOG.md)

`Inputs/` contains the original local reference archive and is excluded from Git. M0 catalogs all 1,506 files by hash, registers all 103 TTFs, and records the current alphabet/numeral mapping. Source code, specifications, schemas, and reproducible test definitions are versioned. Original assets remain intact; runtime logs and extracts live in ignored `.local/`.

The repository is [smccolm/Vayrshemon](https://github.com/smccolm/Vayrshemon). The existing `push_to_github.bat` stages all non-ignored changes, commits, rebases from `origin/main`, and pushes to `main`. Review the staged contents before using it; use explicit Git commands for future feature branches.

## Repeatable research

On Windows, double-click [`setup.bat`](setup.bat), then [`launch.bat`](launch.bat). With Python 3.12 (64-bit) installed, setup creates or reuses `.venv`, installs the pinned M0/M1 dependencies including Qt 6.8.3, and runs all public checks. Python 3.12.7 is the tested version. Setup keeps output visible and saves a separate log for each run in `.local/logs/`. It pauses before closing; use `setup.bat --no-pause` for automation. No Rust, Node, or compiler install is needed for this milestone.

The lab opens the actual 79/80/81 fonts when the local Inputs archive is available. Source files remain untouched. Without Inputs, it starts with the system English font and can load local TTFs. Save lab documents as `*.vaylab.json`; the first default destination is `.local/`. Original fonts are referenced by hash and local path, never embedded or uploaded automatically.

Setup also writes `.local/mcp-config.json` for an MCP client. It connects to the running lab through a current-user-only local socket; mutations require the document ID, current revision, and an idempotency key. The same interface is available as `.venv\Scripts\python -m vayrshemon call session.status`. See the [M1 guide](docs/M1.md) for headless operation and the [published tool schemas](data/mcp-tools.json).

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
