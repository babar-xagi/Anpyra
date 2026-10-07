# 🎨 Native Screen Styling Example

This project uses a source-declared color, diagonal gradient and the bundled real PNG image with contain fit and opacity. A TextView is added above the background layers.

From the repository root:

```powershell
anpyra check examples/screen_style --dump-ir --dump-dalvik
anpyra build examples/screen_style
anpyra verify examples/screen_style/build/dev.anpyra.screenstyle.apk
anpyra install examples/screen_style/build/dev.anpyra.screenstyle.apk --launch
```

Change the settings in [app.py](app.py) or replace [wallpaper.png](assets/wallpaper.png) with your project image. Image paths are relative to the project root. The build normalizes the selected image/frame to PNG and packages it as a digest-named asset.

Try `cover`, `contain`, `fill`, `center`, `inside`, `fit_start` and `fit_end`. For radial gradients use `Gradient(colors, kind="radial", radius=240)`; the radius is in device pixels. `screen.style.bg.opacity` applies to the composed background only; it does not fade the foreground text.

The Screen component is available in Anpyra 0.1.1 and later; use Anpyra 0.1.4 with these repository/source-distribution example files. See [screen styling](../../docs/user_guide/screen.md) for exact syntax/options and limits.
