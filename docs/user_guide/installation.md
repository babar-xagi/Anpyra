# 🧰 Installation

Anpyra's current Android pipeline builds apps using **Python and its Python dependencies**. **uv is recommended** for installing and managing the environment; pip is also supported.

## ✅ Requirements

| Item | Purpose |
| --- | --- |
| Python 3.11+ | Run the compiler and build pipeline; examples below use Python 3.12 |
| **uv, recommended**, or pip | Create the environment and install Anpyra |
| Git or a source checkout | Obtain this source-based alpha |
| `cryptography>=46.0.0` | Keys, certificates and APK signatures; installed automatically with Anpyra |
| Android API 24+ device, for running/testing | Run the generated APK; not needed to build on your computer |
| Platform-tools, optional | Supply `adb` for device installation |

## 🐍 Python-based Android builds

**No Java/JDK, Kotlin, Android SDK build kit, Android NDK, or Android Studio is required to build an APK.** Gradle, D8, R8, AAPT2 and apksigner are also unnecessary for this pipeline. Anpyra's Python code generates DEX, binary XML and the APK, then signs it using `cryptography`.

The `min_sdk` and `target_sdk` settings are Android compatibility metadata written into the manifest. They do not require installing an SDK. The minimum API level follows [Android's v2 signing support](https://source.android.com/docs/security/features/apksigning/v2). Optional adb comes from Android platform-tools; it is used to install/run an already-built APK.

These requirements describe the **implemented Android backend**. Future native iOS/desktop backends have not established their toolchain requirements. See [native targets](platforms.md).

## ⚡ Recommended: install with uv

Follow [uv's official installation instructions](https://docs.astral.sh/uv/getting-started/installation/) if uv is not installed. You can use its standalone installer without installing Java or another Android toolchain.

### 🪟 Windows PowerShell

Install uv once with the official installer:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Open a new terminal if uv is not yet on PATH, then check `uv --version`. Obtain the checkout and install Anpyra:

```powershell
git clone https://github.com/babar-xagi/Anpyra.git
cd Anpyra
uv venv --python 3.12
uv pip install -e .
.\.venv\Scripts\python.exe -m anpyra --version
.\.venv\Scripts\python.exe -m anpyra doctor
.\.venv\Scripts\python.exe -m anpyra build examples/hello
```

If you already have the checkout, begin with `uv venv` in its root. If `.venv` already exists, keep it and run `uv pip install -e .` instead of recreating it.

These commands use the environment directly and require no activation script. uv can [obtain a missing Python version](https://docs.astral.sh/uv/guides/install-python/). The first setup needs network access to obtain missing Python/packages.

For shorter `anpyra` commands, optionally activate the environment:

```powershell
.\.venv\Scripts\Activate.ps1
anpyra doctor
anpyra check examples/hello
```

If activation is blocked, continue using `.\.venv\Scripts\python.exe -m anpyra COMMAND`. No system execution-policy change is needed for that workflow.

### 🐧 Linux and 🍎 macOS

Install uv once:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Open a new terminal if needed, then:

```bash
git clone https://github.com/babar-xagi/Anpyra.git
cd Anpyra
uv venv --python 3.12
uv pip install -e .
.venv/bin/python -m anpyra doctor
.venv/bin/python -m anpyra build examples/hello
```

Optionally activate with `source .venv/bin/activate` to use `anpyra` directly. The same existing-environment guidance applies.

uv discovers the project's `.venv` for its pip interface; see [uv environments](https://docs.astral.sh/uv/pip/environments/). An editable install (`-e .`) imports Anpyra from `src/`, so keep the checkout available. Local source edits become visible without reinstalling each file. This workflow uses `uv venv` / `uv pip`; it does not require `uv sync` or a project lockfile.

The baseline was exercised locally on Windows. Linux is configured in CI. macOS uses the Python workflow but is not currently a CI target. These are build-host instructions; the generated application still targets Android.

## 📦 Alternative: install with pip

Use this route if you prefer standard Python environment/package commands. Install Python 3.11+ first. Both routes install the same Anpyra package and dependencies; choose one for your environment.

uv-created environments do not require pip itself. If switching such an environment to the pip route, first run its Python with `-m ensurepip --upgrade`, or continue using `uv pip`.

### 🪟 Windows PowerShell

From the repository root:

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m anpyra doctor
.\.venv\Scripts\python.exe -m anpyra build examples/hello
```

If `.venv` already exists, skip environment creation. Activation is optional, as in the uv workflow.

### 🐧 Linux and 🍎 macOS

From the repository root:

```bash
python3 --version
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m anpyra doctor
.venv/bin/python -m anpyra build examples/hello
```

## 🛠️ Contributor dependencies

From the checkout, install the development extra for Ruff and run the checks. On Windows:

```powershell
uv pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts/check_docs.py
.\.venv\Scripts\ruff.exe check src tests examples scripts
```

With pip, replace the first line with `.\.venv\Scripts\python.exe -m pip install -e ".[dev]"`. On Linux/macOS use `.venv/bin/python` and `.venv/bin/ruff`. See [development setup](../developer_guide/development_setup.md) for the full workflow.

## 📦 Install a local wheel

Build a wheel from the checkout with uv:

```powershell
uv build --wheel --out-dir dist
```

Or use pip:

```powershell
.\.venv\Scripts\python.exe -m pip wheel --no-deps . --wheel-dir dist
```

In a separate directory containing a fresh virtual environment, install the wheel using its actual absolute path. For example, if the checkout is `D:\Anpyra`:

```powershell
uv venv --python 3.12
uv pip install "D:\Anpyra\dist\anpyra-0.1.0-py3-none-any.whl"
```

The pip alternative is `python -m pip install PATH_TO_WHEEL` inside the activated fresh environment. Use a fresh environment to avoid an existing editable install of the same version being considered satisfied. Dependencies must exist or be obtainable by your package manager.

Anpyra was not published to PyPI by this work. `pip install anpyra` or `uv pip install anpyra` is not the documented installation route.

Maintainers can use the prepared [TestPyPI/PyPI publishing workflow](../developer_guide/publishing.md). Once a release is confirmed on PyPI, normal package-name installation becomes available for that version.

## 📱 Optional adb

Get platform-tools from the [official Android page](https://developer.android.com/tools/releases/platform-tools), extract them, and add their directory to your shell's `PATH`. Confirm with `adb version` and `adb devices`.

For USB use, enable Developer options and USB debugging, connect the phone, and accept its computer-authorization prompt. A ready device appears as `device` in `adb devices`. See the [official adb guide](https://developer.android.com/tools/adb).

Compilation works without adb. You can also transfer the APK and install using the device's package installer, subject to its settings.

## 🩺 Confirm setup

With the environment activated:

```powershell
anpyra doctor
anpyra check examples/hello
anpyra build examples/hello
anpyra verify examples/hello/build/dev.anpyra.hello.apk
```

Without activation, use your environment's Python with `-m anpyra` before each command. `doctor` reports host versions and adb availability; it does not connect to a phone or certify runtime compatibility.

Next: [core concepts](concepts.md) or [first application](first_app.md).
