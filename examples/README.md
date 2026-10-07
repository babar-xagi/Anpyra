# 🧩 Example Applications

Run commands from the repository root after installing Anpyra.

| Example | Demonstrates | Expected screen |
| --- | --- | --- |
| [Hello](hello/README.md) | Native Activity/TextView, simplest source/config | `Hello from Anpyra!` |
| [Score](score/README.md) | Typed helper, integer arguments/return and comparison | `Passed from an Anpyra function!` with default values |
| [Chatbot](chatbot/README.md) | Layouts/input, native API worker and history (0.1.4) | Dark chat screen with runtime key entry; live replies need API quota |
| [Counter Lab](counter/README.md) | Generic callbacks, typed state and input (0.1.5) | +/−/Reset, pause, name preview and saved-state recreation |

```powershell
anpyra check examples/hello
anpyra build examples/hello
anpyra check examples/score --dump-ir --dump-dalvik
anpyra build examples/score
```

Each project has source, configuration and a walkthrough. `build/` and `.anpyra/` appear locally after building and stay out of Git. Phone behavior is verified manually using the [device checklist](../docs/developer_guide/testing.md).

## 🎨 Screen styling

The [screen_style example](screen_style/README.md) uses color, a diagonal gradient, a packaged image, fit and opacity with foreground text. It is built/verified in CI and uses the APIs available in the published package; example files are in the repository/source distribution.
