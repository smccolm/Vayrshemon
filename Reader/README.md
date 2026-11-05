# Vayrshemon Reader 1.0

Run `E:\Vayrshemon\Reader\launch.bat` or `VayrshemonReader.exe`. For `.vay` double-click opening, choose **Vayrshemon Reader → Always** if Windows displays its application chooser. The Reader runs in a separate process alongside the Workbench. It never edits or saves the book. **Edit in Vayrshemon Workbench** remains available in Explorer; Reader also has **File → Open in Workbench**.

Open, zoom, Fit Height, Fit Width, drag to pan, switch one/two pages, and use the page field or arrow buttons. A direct jump to an even page keeps that number displayed and shows its containing spread; Next advances to the next left page. The book selector jumps between major sections. Find searches literal phrases in the stored text; results are capped at 200. Ctrl+G focuses the page field, Ctrl+F opens Find, Ctrl+B lists bookmarks, Ctrl+W closes the book, and F11 toggles fullscreen. Ctrl+mouse wheel zooms. Maxima, all three aligned color-font layers, the Roman treatment, Unta folios, and fixed print-edition art use the original rendering engine. Fixed print editions remain black on white.

The Reader remembers reading position, view, palette, zoom and bookmarks separately from the source. A newly opened document starts with its saved mode; later opens restore Reader preferences. There is no editing, Forge, recovery history or PDF conversion.

## Installation

The existing installation is reused. `Reader\setup.bat` checks the shared runtime, builds the small Memon-icon launcher using Windows' .NET Framework compiler, and installs the per-user Reader association. The project `setup.bat` also includes the Reader for a future installation, using the bundled fonts. The application lives in Reader, but uses the parent project's runtime, fonts and exact typesetter; this folder alone is not a portable distribution.

The association preserves Memon icons, saved-page thumbnails, and the Workbench editing command. It respects protected Windows default-app choices. To restore previous registry values, run `.venv\Scripts\python.exe -m Reader.register --uninstall` from the project directory.

## Speed and storage

The existing native format stores a whole compressed document. Its first Reader opening validates it and builds a disposable, searchable page index, with visible progress. Subsequent openings use that index. Only visible/connected pages are composed; adjacent pages are prefetched. Cached images scale immediately while a sharp render completes in a worker. The UI, two rendering processes, and the Workbench are independent.

Generated cache budgets: 512 MiB page images, 256 MiB glyph tiles, 2 GiB book indexes. Active or oversized individual indexes can exceed the index eviction target. The UI keeps up to 256 MiB of decoded images, retaining the visible pages when evicting prefetched images. Indexes are about 180 MiB for the full four-column Bible, not a 13 GiB PDF. Changed files get a fresh index; source SHA256 is verified during the first import. Fonts/engine changes invalidate paint caches. `.local` is ignored by Git and is disposable while Reader is closed; preferences and association rollback records also live there, so retain those if clearing caches manually.

**Help → Performance** reports medians, p95, maxima and slow operations. All actions, page preparation, image decoding, worker timing, paint timing and UI stalls are logged under `Reader\.local\logs`; each performance log rotates at 20 MiB. Cold import and uncached first-use color rendering are measured separately from cached results. See [PERFORMANCE.md](PERFORMANCE.md) for this machine's full-Bible results and limitations.

## Automation and regression checks

The current-user-only local API exposes status, open/close, page navigation, view, palette, zoom, fit, pan, search, bookmarks, capture and performance. It is separate from the Workbench endpoint. Use `.venv\Scripts\python.exe -m Reader.control reader.status` from the project directory. Other operations take a JSON parameter object; status includes action/completion IDs so clients can wait for a fully rendered view. No API writes a `.vay` file.

`Reader\mcp.py` exposes the same controls over MCP stdio. Use the absolute `.venv\Scripts\python.exe` as command and absolute `Reader\mcp.py` as argument. Setup adds `vayrshemonReader` to `.local\mcp-config.json`. An optional `--descriptor` selects a particular Reader window; otherwise it controls the most recently launched one. The app must be running.

Run from the project root:

```powershell
.venv\Scripts\python.exe -m unittest tests.test_reader tests.test_parallel_translation
.venv\Scripts\python.exe -m Reader.benchmark
.venv\Scripts\python.exe -m Reader.benchmark_lifecycle
.venv\Scripts\python.exe -m Reader.verify_fidelity
```

The live benchmark navigates the full 20,780-page Bible across all palettes and view modes, tests zoom/panning/search/boundaries/rapid jumps, and records memory. The lifecycle benchmark creates a separate cold profile, opens that same full book, closes it, and restarts to distinguish first-use and cached startup. Fidelity checks compare selected beginning/middle/end pages pixel-for-pixel with the unchanged Workbench renderer. Reports and captures stay private in `Reader\.local`. Modern `.vay` and legacy `.vay.json` documents in formats 0.5/0.6 and compressed native 0.7 are supported; very old lab formats need a Workbench resave first.
