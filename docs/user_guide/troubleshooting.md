# 🩺 Troubleshooting

Start with `python -m anpyra doctor`, then `anpyra check YOUR_PROJECT`. Keep the command, source and complete error message when reporting a problem.

## 🧰 Environment problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `anpyra` command not found | Environment inactive or install missing | Use its Python explicitly, then `python -m pip install -e .` |
| `No module named anpyra` | Different Python/environment | Compare `python -c "import sys; print(sys.executable)"` with the environment you installed into |
| `No module named cryptography` | Dependencies missing | Reinstall in the active environment with `python -m pip install -e .` |
| `tomllib` import failure | Python below 3.11 | Create a new environment with Python 3.11+ |
| PowerShell blocks activation | Shell execution policy | Use `.\.venv\Scripts\python.exe -m anpyra ...` without activation |
| `adb` not found | Optional tool absent from PATH | Install/configure official platform-tools or use device-side APK installation |

## ⚙️ Project configuration problems

- **Cannot read configuration:** pass the app directory or its `anpyra.toml`. Inside the app directory use `anpyra check` / `anpyra check .`. Passing `myapp` after `cd myapp` looks for a nested `myapp/myapp`. The framework root is not itself an app project.
- **Unknown app settings:** fix typos and use only [documented fields](configuration.md).
- **Invalid package:** use lowercase dot-separated segments such as `dev.example.hello`.
- **Project path escapes:** keep entry and output paths relative and inside the app root.
- **Output contains source:** choose a separate `build` directory; do not put source under that output directory.
- **Directory must be empty:** `init` protects existing files. Choose a new directory rather than deleting your work.

## 🗂️ APK not found when installing

Use the exact APK path printed by `anpyra build`. Its filename follows `[app] package` in `anpyra.toml`, not the project directory name. `anpyra init myapp` defaults to `dev.anpyra.app`; examples selecting `--package dev.example.myapp` produce a different filename.

For the default package:

| Current folder | Check command | Install command |
| --- | --- | --- |
| Parent of `myapp` | `anpyra check myapp` | `anpyra install myapp/build/dev.anpyra.app.apk --launch` |
| Inside `myapp` | `anpyra check` | `anpyra install build/dev.anpyra.app.apk --launch` |

Use `Get-ChildItem .\build\*.apk` inside the project to see its outputs, or pass an absolute path. A file-not-found error occurs before adb runs; changing USB/device settings does not resolve a wrong local path.

## 🐍 Compiler problems

| Error/behavior | Meaning | Typical correction |
| --- | --- | --- |
| Undefined variable | A name is used before declaration | Initialize it before use |
| Already declared | The same local is declared twice | Use separate names; reassignment is not implemented |
| Expected `str` | A UI text call received another type | Pass a declared string or literal |
| Signed 16-bit literal error | Constant outside the supported range | Keep literals within range; wider constants are planned |
| Exceeds 14 registers | Locals plus synthetic values exceed backend budget | Reduce declarations/inline values and inspect `--dump-ir` |
| Content view exactly once/outside branches | UI attachment occurs conditionally or repeatedly | Move one attachment after the branch |
| Unsupported statement/method/import | Valid Python outside Anpyra's subset | Use the [language reference](language.md) |
| Running source raises a host RuntimeError | Android API stubs were executed on the host | Build and install the APK instead |

## 🔑 Signing and artifact problems

**Incomplete identity:** restore both `.anpyra/debug-key.pem` and `.anpyra/debug-cert.der` from the same backup. Do not replace one file with an unrelated identity. Starting a fresh identity changes app-signing identity and may prevent an update.

**Certificate/key mismatch:** the pair belongs to different signers. Restore the matching pair before building.

**Content digest or DEX integrity failure:** verify the original build output, rebuild from source, and compare the report fingerprint. A copied, modified, partially transferred or corrupted APK can fail. Do not edit signed APK entries manually.

**Unexpected APK entries:** `verify` is restricted to Anpyra's two-entry profile. An APK created by another tool may be valid Android output while outside this verifier's scope.

## 📱 Device problems

Run `adb devices`. `unauthorized` requires accepting the phone's computer prompt; `offline` requires investigating the connection/device state. With multiple devices, use `--serial DEVICE_ID`. Follow the [official adb guide](https://developer.android.com/tools/adb) for connection setup.

If Android rejects an update, compare package ID, retained certificate fingerprint, and app version. Preserve the old identity or use a new package for a separate development app. Uninstalling an existing app can erase its app data; only do so intentionally.

If the APK installs but crashes or shows incorrect content, collect a focused log using `adb logcat`, describe expected/actual behavior, and provide the minimal source. Host checksum verification cannot diagnose every runtime bug. Use the [developer debugging workflow](../developer_guide/debugging.md).

## 🐛 Useful bug report

Include OS, Python version, `anpyra --version`, `doctor` output, exact command, minimal source/configuration, error, and device model/API if relevant. Include an IR/Dalvik excerpt or redacted report when useful. Do not attach private signing keys. See [contribution guidance](../../CONTRIBUTING.md).
