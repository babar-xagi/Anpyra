# ⌨️ Command Reference

Run `anpyra --help` or `anpyra COMMAND --help`. Every command also works as `python -m anpyra COMMAND` with the installed environment's Python.

## 🧭 Global options

```powershell
anpyra --version
anpyra --help
```

`--version` prints `Anpyra 0.1.1`. A subcommand is required for normal work.

## 🏗️ init

```text
anpyra init DIRECTORY [--package ID] [--label TEXT]
```

Creates `app.py`, `anpyra.toml` and `.gitignore`. Defaults are package `dev.anpyra.app` and label `Anpyra`. It refuses a nonempty directory to preserve existing files.

```powershell
anpyra init myapp --package dev.example.myapp --label "My App"
```

## 🔍 check

```text
anpyra check [PROJECT] [--target android] [--dump-ir] [--dump-dalvik]
```

Loads configuration, compiles source and generates DEX in memory. It creates no artifacts or signing files. `PROJECT` defaults to `.` and accepts a directory or config path.

Inside your app directory use `anpyra check` or `anpyra check .`. From the parent directory use `anpyra check myapp`. Paths are relative to your current shell directory.

```powershell
anpyra check examples/score --dump-ir --dump-dalvik
```

## 📦 build

```text
anpyra build [PROJECT] [--target android] [--dump-ir] [--dump-dalvik]
```

Compiles and packages the app, loads/creates its debug identity, signs, verifies staged output, then publishes local artifacts. Prints the APK path/size and report path.

Metadata and output paths come from configuration; there are no `--package`, `--output-dir`, release, or clean options on this subcommand.

```powershell
anpyra build examples/hello
anpyra build myapp/anpyra.toml --dump-ir
```

Build/check default to Android. `--target android` selects it explicitly. Only Android is accepted; other target names produce an argument-parser error before project reads/writes. `--dump-dalvik` describes Android bytecode.

## 🌍 targets

```powershell
anpyra targets
```

Prints `android  available`. There are no additional target packages or dispatch registry. See [Android scope](android.md) for the host/target distinction.

## ✅ verify

```text
anpyra verify APK [--json]
```

Checks the framework's single-signer APK v2 profile, protected content, DEX magic, SHA-1 and Adler-32. It expects manifest and DEX plus optional validated digest-named screen PNG assets in the current source feature. It is not a general verifier for arbitrary APKs with assets, resources or multiple signers.

```powershell
anpyra verify examples/hello/build/dev.anpyra.hello.apk
anpyra verify examples/hello/build/dev.anpyra.hello.apk --json
```

JSON includes package, Activity, label, SDKs, exported flag, integrity flags, certificate subject, signing-block size and central-directory offset. Failure returns an error rather than a successful report containing false flags.

## 🩺 doctor

```powershell
anpyra doctor
```

Reports Anpyra/Python/cryptography/Pillow versions, Python executable, and optional adb path. It does not perform network checks, device discovery, or runtime validation. Missing adb does not prevent builds.

## 📱 install

```text
anpyra install APK [--serial DEVICE_ID] [--launch]
```

Verifies the APK first, then invokes optional adb with `install -r`. `--serial` selects a device. `--launch` runs the manifest's Activity using `am start -W -n`. It does not rebuild source automatically.

```powershell
anpyra install myapp/build/dev.example.myapp.apk --serial DEVICE_ID --launch
```

## 🚦 Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Successful command; help/version also exit successfully |
| `1` | Configuration, compile, build, verification or subprocess failure handled by the CLI |
| `2` | Argument-parser usage error, such as an unknown flag |
| `130` | Keyboard interruption during command execution |

The CLI writes handled errors to stderr as `anpyra: ...`. For a Python traceback, reproduce via the [Python API](python_api.md) or follow the [developer debugging guide](../developer_guide/debugging.md).
