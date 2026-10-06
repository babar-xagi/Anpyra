# 🟦 Native Button Design Example

This example creates an actual Android Button inside Screen. It demonstrates typography, dp size/placement/padding, a rounded border, pressed/disabled backgrounds, native ripple, an end icon and elevation. Anpyra 0.1.3 includes Button. The example source/icon are in the repository/source distribution; ordinary wheel users can create a project using the same API.

From the repository root:

```powershell
uv pip install -e .
anpyra check examples/button_style --dump-dalvik
anpyra build examples/button_style
anpyra verify examples/button_style/build/dev.anpyra.buttonstyle.apk
anpyra install examples/button_style/build/dev.anpyra.buttonstyle.apk --launch
```

The button is centered with a 260×64 dp box. Press feedback is native. No Python click action is bound in this design example; callback compilation is future work. To inspect disabled design, set `button.style.enabled = False` before screen attachment.

Files: [app.py](app.py), [anpyra.toml](anpyra.toml), [icon](assets/README.md). Full [user guide](../../docs/user_guide/button.md) and [implementation map](../../docs/developer_guide/button_styling.md).
