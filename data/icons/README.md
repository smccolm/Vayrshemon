# Centered Memon document icons

M14's user-approved icon source is `Inputs/Versions Best/Individual Glyphs/Maxima_28_Memon.jpg`. These app assets reproduce that one capital from the actual Thimfora 79 outline, 81 interior and 80 glow paths, using the accepted relief recipe. All layers retain one shared origin/em. The ink bounds of the complete glyph determine its placement, preserving the descending curl while centering it inside the square.

`memon-paths.json` stores only this glyph's geometry and the relevant recipe/gradient, with source font/reference hashes. No complete font or original reference image is included. The original archive remains ignored. `memon-color` shows relief on black; `memon-mono-black` is white on black; `memon-mono-white` is black on white.

Rebuild the PNG/ICO assets without private fonts:

```powershell
.venv\Scripts\python -m tools.memon_icons
```

Each ICO contains 16, 20, 24, 32, 40, 48, 64, 96, 128 and 256 px images. The standalone PNG is 256 px. This is an app-identity asset, not a new font treatment or a replacement for an approved page baseline.
