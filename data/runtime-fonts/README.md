# Application fonts

These four original fonts are bundled with the application at the owner's explicit request on 2026-10-24. They are byte-for-byte copies, with provenance, sizes and SHA-256 identities in `manifest.json` and the existing `data/fonts.json` catalog.

| File | Approved role |
|---|---|
| `Thimfora_79.ttf` | Master script outlines and shaping |
| `Thimfora_80_Infill.ttf` | Glow layer |
| `Thimfora_81_Fragments.ttf` | Interior layer |
| `transliteration 7.ttf` | Intended Roman forms, including Maxima/Minima counterparts |

The renderer retains the master glyph origins and existing three-font paint recipe. No glyph, mapping, metric, font name or font file has been regenerated. Runtime Qt registration remains private to the application; setup does not install these fonts into Windows.

Startup and identity-based font lookup prefer these assets. Existing documents retain working font paths; a missing path can resolve to the exact bundled hash. Explicitly supplied replacement paths and changed font bytes still fail normal validation. Other archival and user fonts remain external.

Run `.venv\Scripts\python -m tools.verify_runtime_fonts` to check the bundle. `setup.bat` runs this check, and versioned source release bundles include these assets. `Inputs/`, `Saves/` and `Exports/` remain ignored.
