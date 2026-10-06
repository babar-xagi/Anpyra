# 🧰 Repository Maintenance Scripts

## 📚 check_docs.py

Run from any directory using the script's path:

```powershell
python scripts/check_docs.py
```

The script discovers repository-owned Markdown, checks relative file links and emoji title conventions, parses Python snippets, and compiles supported documented Activity examples in memory. It reports failures with file/line information and returns a nonzero status.

It excludes local environments/caches/build outputs/reference inputs. It does not fetch external URLs, validate heading anchors, execute host snippets, install packages, or run device commands. Blocks marked `python unsupported` are syntax-checked but intentionally not compiled as apps.

Activate/install Anpyra before running it. Compiler availability is checked so supported examples cannot silently skip compilation. CI runs it alongside lint and tests. See the [testing guide](../docs/developer_guide/testing.md).

## 📦 check_release.py

```powershell
python scripts/check_release.py --tag v0.1.2
python scripts/check_release.py --tag v0.1.2 --dist dist/pypi/0.1.2
```

`check_version` reads pyproject.toml and parses the package __version__ assignment without importing framework code. The optional tag must equal vVERSION. `check_distributions` requires one wheel and one source archive, checks name/version metadata and required package/release files, and rejects duplicate/unsafe paths, tar links, common key/signing state and generated artifacts.

This read-only guard does not build, extract, upload, change versions or access credentials. `main` returns 1 with a diagnostic on failure. See [publishing](../docs/developer_guide/publishing.md) for build/upload commands and account configuration.

## 📱 check_screen_device.py

Opt-in real-device pixel matrix for Screen color/gradient/image/fit/alpha behavior. Run `python scripts/check_screen_device.py --serial DEVICE_ID` with an unlocked portrait device. It builds/installs its named test package, saves screenshots/results under build/, and leaves the test app installed. --adb, --package and --work-dir configure the target/tool/project; it does not uninstall apps or change device settings. Preserve its signing identity for future updates.

See [implementation and runtime evidence](../docs/developer_guide/screen_styling.md). The ordinary CI suite does not run this script.

## 🔤 check_text_device.py

Opt-in native typography pixel/geometry matrix. Run `python scripts/check_text_device.py --serial DEVICE_ID` on an unlocked phone; --adb, --package and --work-dir configure the test. It leaves its own package installed, saves screenshots/results and keeps its visible test view awake without changing system settings. It cannot unlock a locked phone. It measures the controlled app background to account for OEM accessibility bounds. --resume-from replays saved screenshots before fresh tail captures; use only for an unchanged candidate and inspect the recorded reuse list. See [typography internals](../docs/developer_guide/textview_styling.md); normal CI does not run it.

## 🔡 generate_demo_fonts.py

Recreates the original TTF/OTF demonstration assets from owned block outlines. Use `uv run --no-project --with fonttools scripts/generate_demo_fonts.py` to obtain the generation tool in isolation; ordinary app builds do not require FontTools. This deliberately overwrites the two example fonts. See [font asset details](../examples/text_style/assets/README.md).

## 🟦 check_button_device.py

Opt-in native Button pointer/pixel/geometry checks. Use `python scripts/check_button_device.py --serial DEVICE_ID` with an unlocked phone. --adb, --package and --work-dir select the tool/test app. The script saves screenshots/results, holds its own visible test view awake and captures press states during a continuous gesture, then releases it. It does not bind app actions or change system settings. See [Button internals](../docs/developer_guide/button_styling.md).
