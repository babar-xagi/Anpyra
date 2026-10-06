# 🔡 Original Demonstration Fonts

`AnpyraDemo.ttf` and `AnpyraDemo.otf` are original fonts generated for this project from simple 5×7 block outlines. They contain ASCII demonstration glyphs, map lower-case letters to matching upper-case outlines and use simple box shapes for non-letter symbols. These are test/demo assets, not a complete production typeface.

They are covered by the repository's [Apache-2.0 license](../../../LICENSE). No third-party font data is included. Application code uses the TTF; the OTF also exercises CFF asset validation/loading in tests. No font-generation library is needed to build an app with these existing files.

Source outlines and generation settings live in [generate_demo_fonts.py](../../../scripts/generate_demo_fonts.py). To regenerate deliberately from the repository root, use an isolated generation dependency:

```powershell
uv run --no-project --with fonttools scripts/generate_demo_fonts.py
```

This overwrites the two demonstration fonts. FontTools is a generation tool only; it is not an Anpyra runtime/build dependency.
