# 🧰 Installation

Anpyra's current Android pipeline builds apps using **Python and its Python dependencies**. **uv is recommended** for installing and managing the environment; pip is also supported.

## ✅ Requirements

| Item | Purpose |
| --- | --- |
| Python 3.11+ | Run the compiler and build pipeline; examples below use Python 3.12 |
| **uv, recommended**, or pip | Create the environment and install Anpyra |
| Git/source checkout, optional | Needed for development and repository examples; not for PyPI installation |
| `Pillow>=11.3.0` | Screen color/image parsing, conversion and validation; installed automatically |
| `cryptography>=46.0.0` | Keys, certificates and APK signatures; installed automatically with Anpyra |
| Android API 24+ device, for running/testing | Run the generated APK; not needed to build on your computer |
| Platform-tools, optional | Supply `adb` for device installation |

## 🐍 Python-based Android builds

**No Java/JDK, Kotlin, Android SDK build kit, Android NDK, or Android Studio is required to build an APK.** Gradle, D8, R8, AAPT2 and apksigner are also unnecessary for this pipeline. Anpyra's Python code generates DEX, binary XML and the APK, then signs it using `cryptography`.

The `min_sdk` and `target_sdk` settings are Android compatibility metadata written into the manifest. They do not require installing an SDK. The minimum API level follows [Android's v2 signing support](https://source.android.com/docs/security/features/apksigning/v2). Optional adb comes from Android platform-tools; it is used to install/run an already-built APK.

Anpyra **0.1.3 includes Screen styling and expanded TextView typography, including local fonts, plus native Button design**. Install directly from PyPI; no Git checkout is needed to use these APIs. These requirements describe the Android-only build pipeline. See [Android scope](android.md) for build computers versus the device that runs the APK.

## 📦 Install from PyPI

Install Anpyra **0.1.3** from [the official project page](https://pypi.org/project/anpyra/0.1.3/) with uv (recommended) or pip. Python dependencies are installed automatically. These commands download the package directly from PyPI.

### ⚡ uv (recommended)

Install uv using [its official instructions](https://docs.astral.sh/uv/getting-started/installation/). On Windows, open PowerShell in a directory for your environment:

```powershell
uv venv --python 3.12
uv pip install "anpyra==0.1.3"
.\.venv\Scripts\python.exe -m anpyra --version
.\.venv\Scripts\python.exe -m anpyra doctor
.\.venv\Scripts\python.exe -m anpyra init myapp
.\.venv\Scripts\python.exe -m anpyra build myapp
```

The version command should print `Anpyra 0.1.3`. On Linux/macOS use `.venv/bin/python -m anpyra` for the final commands. For the latest available version instead of an exact pin, use `uv pip install anpyra` in a fresh environment.

### 🐍 pip alternative

On Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install "anpyra==0.1.3"
.\.venv\Scripts\python.exe -m anpyra --version
.\.venv\Scripts\python.exe -m anpyra doctor
```

On Linux/macOS create the environment with `python3 -m venv .venv` and use `.venv/bin/python -m pip install anpyra`. Keep an existing environment instead of recreating it. Activation is optional. A normal package installation does not include the repository's `examples/` folder; use `anpyra init` to create your own app, or follow the source checkout instructions below.

## 🔄 Upgrade from an earlier version to 0.1.3

Upgrade in **the same Python environment where Anpyra is already installed**. Keep your app directory, `anpyra.toml`, assets and `.anpyra/` signing identity. Updating the compiler package does not update or install an Android APK; rebuild your app after upgrading. Your app's `version_name` is independent of the Anpyra package version.

### ⚡ Existing uv environment

From the directory containing your existing `.venv`:

```powershell
uv pip install --python .\.venv\Scripts\python.exe --upgrade "anpyra==0.1.3"
.\.venv\Scripts\python.exe -m anpyra --version
.\.venv\Scripts\python.exe -m anpyra doctor
```

On Linux/macOS replace `.\.venv\Scripts\python.exe` with `.venv/bin/python`. In an activated environment you can shorten the upgrade command to `uv pip install --upgrade "anpyra==0.1.3"`.

### 🐍 Existing pip installation

If you originally used `python -m pip install anpyra`, use that same Python:

```powershell
python -m pip install --upgrade "anpyra==0.1.3"
python -m anpyra --version
python -m anpyra doctor
```

For a Windows `.venv`, replace `python` in all three commands with `.\.venv\Scripts\python.exe`. On Linux/macOS use the Python from your existing environment, for example `.venv/bin/python`. A uv-created environment may not contain pip; use the uv command above or install pip with its Python's `-m ensurepip --upgrade` first.

### 🆕 Upgrade to the latest available release

Use one command in your existing environment:

```powershell
# uv: in the activated environment or beside its .venv
uv pip install --upgrade anpyra
# pip: use the Python that already has Anpyra installed
python -m pip install --upgrade anpyra
```

An exact pin (`anpyra==0.1.3`) selects this release; the unpinned `--upgrade anpyra` selects the latest compatible release. See the official [uv package commands](https://docs.astral.sh/uv/pip/packages/) and [pip upgrade guide](https://pip.pypa.io/en/stable/user_guide/#only-if-needed-recursive-upgrade).

### 🧭 Verify and rebuild your existing app

With the correct environment activated, from **inside your app directory**:

```powershell
anpyra --version
anpyra doctor
anpyra check
anpyra build
anpyra verify .\build\dev.anpyra.app.apk
# Optional: connected Android device with USB debugging
anpyra install .\build\dev.anpyra.app.apk --launch
```

The APK filename comes from `[app].package` in `anpyra.toml`; replace `dev.anpyra.app.apk` if you changed the package. Use your environment's Python with `-m anpyra` instead of `anpyra` if activation is unavailable. Keep `.anpyra/` so rebuilds retain the signing identity needed to update an installed app.

If the version still shows an earlier release such as `0.1.2`, compare `python -c "import sys; print(sys.executable)"` and `python -m anpyra --version` with the intended environment. On Windows, `Get-Command anpyra -All` shows which CLI executable PowerShell selects. Upgrade the interpreter that owns that installation rather than creating another environment accidentally.

Immediately after publication, a cached package-index response can report that the new version is unavailable. Retry with fresh metadata in the intended environment:

```powershell
uv pip install --no-cache --refresh "anpyra==0.1.3"
# Or pip:
python -m pip install --no-cache-dir --upgrade "anpyra==0.1.3"
```

## 🛠️ Editable source installation with uv

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
uv pip install "D:\Anpyra\dist\anpyra-0.1.3-py3-none-any.whl"
```

The pip alternative is `python -m pip install PATH_TO_WHEEL` inside the activated fresh environment. Use a fresh environment to avoid an existing editable install of the same version being considered satisfied. Dependencies must exist or be obtainable by your package manager.

Direct PyPI installation is the normal user workflow. Maintainers can follow the [publishing workflow](../developer_guide/publishing.md) for subsequent releases. Uploading the same version again cannot replace its existing files.

## 📱 Optional adb

Get platform-tools from the [official Android page](https://developer.android.com/tools/releases/platform-tools), extract them, and add their directory to your shell's `PATH`. Confirm with `adb version` and `adb devices`.

For USB use, enable Developer options and USB debugging, connect the phone, and accept its computer-authorization prompt. A ready device appears as `device` in `adb devices`. See the [official adb guide](https://developer.android.com/tools/adb).

Compilation works without adb. You can also transfer the APK and install using the device's package installer, subject to its settings.

## 🩺 Confirm setup

With the environment activated, from the parent directory of the `myapp` project created above:

```powershell
anpyra doctor
anpyra check myapp
anpyra build myapp
anpyra verify myapp/build/dev.anpyra.app.apk
```

If you have not created an app yet, run `anpyra init myapp` first. Without activation, use your environment's Python with `-m anpyra` before each command. `doctor` reports host versions and adb availability; it does not connect to a phone or certify runtime compatibility.

Next: [core concepts](concepts.md) or [first application](first_app.md).
