# 🧰 Installation

## ✅ Requirements

| Item | Purpose |
| --- | --- |
| Python 3.11+ | Run Anpyra and parse TOML configuration |
| pip and virtual environment | Install framework and dependency |
| Git or a source checkout | Obtain this source-based alpha |
| `cryptography>=46.0.0` | Keys, certificates and APK signatures; installed by pip |
| Android API 24+ device | Minimum declared SDK for v2-only APK signing |
| Platform-tools, optional | `adb` device installation |

Building does not require Android SDK build tools, Gradle, Java, Kotlin, or Android Studio. The minimum SDK follows [Android's v2 signing support](https://source.android.com/docs/security/features/apksigning/v2).

## 🪟 Windows PowerShell

If you already have the checkout, begin at the environment commands in its root.

```powershell
git clone https://github.com/babar-xagi/Anpyra.git
cd Anpyra
python --version
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m anpyra --version
python -m anpyra doctor
```

An editable install (`-e .`) imports the framework from `src/`. Keep the checkout available; local edits become visible without reinstalling each file.

If activation is blocked, use the environment directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m anpyra doctor
.\.venv\Scripts\python.exe -m anpyra build examples/hello
```

This requires no system execution-policy change.

## 🐧 Linux and 🍎 macOS

```bash
git clone https://github.com/babar-xagi/Anpyra.git
cd Anpyra
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m anpyra doctor
python -m anpyra build examples/hello
```

The baseline was exercised locally on Windows. Linux is configured in CI. macOS uses the Python workflow but is not currently a CI target; report platform-specific failures with environment details.

## 📦 Install a local wheel

Create a wheel from the checkout:

```powershell
python -m pip wheel --no-deps . --wheel-dir dist
```

In a fresh virtual environment, install the resulting file:

```powershell
python -m pip install dist/anpyra-0.1.0-py3-none-any.whl
```

Use the actual wheel's path if you are outside the checkout. An existing editable install of the same version may be considered satisfied; use a fresh environment or explicitly reinstall. Dependencies must exist or be obtainable by pip.

Anpyra was not published to PyPI by this work. `pip install anpyra` is not the documented installation route.

## 📱 Optional adb

Get platform-tools from the [official Android page](https://developer.android.com/tools/releases/platform-tools), extract them, and add their directory to your shell's `PATH`. Confirm with `adb version` and `adb devices`.

For USB use, enable Developer options and USB debugging, connect the phone, and accept its computer-authorization prompt. A ready device appears as `device` in `adb devices`. See the [official adb guide](https://developer.android.com/tools/adb).

Compilation works without adb. You can also transfer the APK and install using the device's package installer, subject to its settings.

## 🩺 Confirm setup

```powershell
anpyra doctor
anpyra check examples/hello
anpyra build examples/hello
anpyra verify examples/hello/build/dev.anpyra.hello.apk
```

`doctor` reports host versions and adb availability. It does not connect to a phone or certify runtime compatibility.

Next: [core concepts](concepts.md) or [first application](first_app.md).
