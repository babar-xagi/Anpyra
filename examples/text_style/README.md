# 🔤 Native Typography Example

This source-only example styles a native TextView inside Screen. It exercises local font loading, color/size, horizontal/vertical alignment, runtime dp padding, wrapping, letter/line spacing, shadow and accessibility description. Install the editable checkout; the expanded typography APIs are not in PyPI 0.1.1.

From the repository root:

```powershell
uv pip install -e .
anpyra check examples/text_style --dump-dalvik
anpyra build examples/text_style
anpyra verify examples/text_style/build/dev.anpyra.textstyle.apk
anpyra install examples/text_style/build/dev.anpyra.textstyle.apk --launch
```

The declared font size is 30 sp. The TextView fills the Screen and centers its title within its bounds. The original demonstration font maps lower-case letters to the same block outlines as upper-case letters; this appearance comes from the font, not an all-caps preset.

Files: [app.py](app.py), [anpyra.toml](anpyra.toml), [font assets](assets/README.md). Complete options and limitations: [TextView guide](../../docs/user_guide/textview.md).
