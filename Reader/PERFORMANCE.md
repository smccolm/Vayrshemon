The measurements below describe the original 280 benchmark corpus, now preserved in `Saves/Archive/Previous editions/KJV before 281.7z`. New benchmark/fidelity runs default to the current matching four-column 281; the historical timings below are not measurements of that new edition.

# Reader 1.0 performance and fidelity — 2026-11-05

Measured on this Windows PC with the existing Workbench windows still running. The principal test is the complete **20,780-page**, 66-section, four-column Bible: `Saves/KJV Bible v0.10-kjv.280/KJV Bible.vay`. Its SHA256 remained `a70a7e00b9f915dd9126668dc2af3c0c3078632bd5b5aa72ad50789b7f437754`. No PDF is involved, and the historical edition is never rewritten.

## Startup and storage

| Operation | Measured time |
| --- | ---: |
| First opening with an entirely new Reader cache, through fully displayed pages | **26.71 s** |
| Restarting the application with that prepared book, through fully displayed pages | **607 ms** |
| Reopening the indexed book inside the running Reader | **under 300 ms** |
| Creating the application window | **343 ms** |
| Closing the full book | **13 ms** |

First use is a real one-time cost: the existing native format contains a compressed whole-document JSON payload. The Reader validates it, creates individually addressable page records and a search index, verifies the source hash, then displays the book. Progress remains visible. The fresh-cache test used an isolated Reader profile; the Windows filesystem cache was **not** flushed, so this is not a cold-machine disk benchmark. Subsequent opens avoid parsing that whole payload.

The full-Bible index is 189,153,280 bytes (180.4 MiB). Page-image, glyph and index caches have eviction budgets rather than growing with every rendered page indefinitely. During the mixed interaction run, the UI working set was 353.8 MiB and the two workers 182.1/181.5 MiB: approximately **717 MiB combined**. UI peak working set was 385.5 MiB. Worker peak working sets were 207.9/212.1 MiB; these peaks need not occur simultaneously. Python launcher overhead is additional and small. Private committed memory was 314.0 + 143.6 + 143.4 MiB. Restricting numeric-library worker threads removed roughly 1.4 GiB of unnecessary private commitment per rendering worker found in an earlier run.

## Reading actions

The release run mixes pages already in memory, disk-cached pages, and newly composed pages. It covers all three palettes, both page modes, pages 1/101/10001/20779, adjacent pages, distant jumps, revisits and final-page boundaries. Do not interpret its median as an uncached guarantee.

| Action | Median | 95th percentile | Maximum |
| --- | ---: | ---: | ---: |
| Page/spread navigation, 48 completed actions | **8 ms** | **653 ms** | **1,111 ms** |
| One/two-page switch, 6 actions | **42 ms** | **241 ms** | **241 ms** |
| Zoom to 100%/150%, sharp image ready | **377 ms** | **907 ms** | **907 ms** |
| Fit Height/Width | **3 ms** | **333 ms** | **333 ms** |
| Palette change | **164 ms** | **1,715 ms** | **1,715 ms** |
| Literal phrase search across the whole book | **2 ms** | **7 ms** | **7 ms** |
| UI paint | **1.1 ms** | **2.0 ms** | **2.8 ms** |
| Pan dispatch | **0.008 ms** | **0.048 ms** | **0.051 ms** |

Zoom visibly responds using the existing image in about 4 ms, then replaces it with the sharp render. Page navigation acknowledges/display-updates in about 3 ms; a previously unseen page may show a loading placeholder until composition completes. Pan dispatch excludes the following paint, measured separately above. The API benchmark also includes polling overhead; the table uses the app's own measured action-completion durations.

Five rapidly superseding distant jumps settled on the final target in **1.05 s**. A separate edge run measured 10% zoom at **366 ms**, 300% zoom at **517 ms**, final-page single/paired switches at **21–23 ms**, and bookmarking at **2 ms**. Tests assert that prefetching cannot evict the visible high-zoom pages from the memory cache.

**Remaining outliers are recorded, not hidden:** first-use color glyph preparation can take roughly 1.7–2.5 seconds, and the first uncached jump just after a cached reopen can wait roughly one second for the rendering libraries. Normal navigation's p95 still exceeds the 500 ms target. The run recorded three UI heartbeat stalls, maximum **185 ms**, including startup; it did not sustain a 60 Hz guarantee through every operation. Diagnostics continue to flag these thresholds automatically under Help → Performance. There are no claims that every color page or every machine will meet the median.

The 1,952-page compact print edition was also opened and timed: **3.84 s** including its first index, **166 ms** to its frontispiece/illuminated opening, **121 ms** to its last spread, and **5 ms** to revisit the cached opening. Its artwork, mirrored binding offsets, Maxima and Unta folios were visually inspected.

## Correctness and Windows integration

- All **24 pixel comparisons** passed against the unchanged Workbench renderer: pages 1, 2, 10,391 and 20,780 × three palettes × one/two-page numbering modes. This is sampled visual regression, not a claim to have inspected every page.
- Automated tests cover native page/index identity, source hashes, search, exact rendering/folio placement, compact illuminated pages, concurrent cache publication, explicit right-page jumps and visible-page cache retention. The approved `test_parallel_translation.py` regression is included.
- Final regression run: **8 tests passed**. A live 300% zoom dwell also retained both visible pages after prefetch; the section selector followed Revelation and Genesis correctly. All three pre-existing Workbench windows remained responsive. Both the original four-column and compact native SHA256 hashes were unchanged.
- Live tests cover invalid page numbers, first/last boundaries, direct right-page navigation followed by Next, rapid stale-request replacement, 10–300% zoom, fit, panning, search, bookmarks, and the MCP status tool. Logs include failures encountered during development as well as the final reports.
- `Reader/VayrshemonReader.exe` is a small named, icon-bearing launcher built from `Launcher.cs`. It was launched successfully with the complete book. Per-user `.vay` Open With/capability registration, the Memon icon/thumbnail handlers and Workbench edit verb are installed.
- **The Windows default-app chooser was not confirmed.** Windows resolved a double-click to its chooser; the user stopped computer control while this was being checked. Use Reader's launcher now, or select **Vayrshemon Reader → Always** in Windows' chooser. No protected UserChoice hash was modified.

## Reproducible evidence

Private reports are under `Reader/.local/benchmarks/`: `release-live.json` (full interactions), `lifecycle.json` (fresh profile and restart), `edge-actions.json`, and `compact.json`. `Reader/.local/verification/fidelity.json` records all 24 comparisons and the unchanged source hash; captures include `reader-white.png`, `reader-color.png` and `reader-compact.png`. Development timing logs are retained separately. Run the commands in [README.md](README.md) to reproduce them.

Future changes to loading, rendering, caching, navigation or font handling must remeasure the full book and retain outliers. Keep first-use import, immediate UI response, full sharp-page readiness and cached revisit results distinct.
