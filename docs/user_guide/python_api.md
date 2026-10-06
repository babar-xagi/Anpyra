# 🧰 Python API for Host Tools

These examples are **host scripts**, separate from the restricted Android app source. Host scripts can use normal Python libraries to call Anpyra. Their imports should not be copied into `app.py` unless the language reference permits them.

## 🔤 Component imports

TextView now has one canonical implementation in `anpyra.components.textview`, re-exported through `anpyra` and `pyandroid` for compatibility. Version 0.1.2 adds Font, Shadow and TextStyle plus declarative typography; see the [TextView guide](textview.md). These expanded properties are included in the 0.1.2 wheel.

## 📦 Build a configured application

```python
from anpyra import build_project

result = build_project("examples/hello")
print(result.apk_path)
print(result.apk_size)
print(result.verification.v2_signature_ok)
```

`build_project()` accepts a project directory, configuration file, or `Project` object. It defaults to the current directory.

Its optional keyword `target="android"` is retained for compatibility. Other values raise ValueError before loading/writing a project; Android is the only target and there is no registry. `build_apk`, `BuildResult`, `AppConfig`, `Activity` and `TextView` remain Android interfaces.

## ⚙️ Inspect or adjust project configuration

```python
from dataclasses import replace

from anpyra import Project, build_project, load_project

project = load_project("examples/hello")
config = replace(project.config, label="Custom Hello", version_code=2)
result = build_project(Project(project.root, config))
```

Configuration objects are immutable. The replacement above affects that API build; it does not edit `anpyra.toml` on disk. `Project` exposes `root`, `config`, `source_path`, `output_path` and `state_path`.

## 📄 Build one source file

```python
from anpyra import build_apk

result = build_apk(
    "examples/hello/app.py",
    "build/api-hello",
    package="dev.example.apihello",
    label="API Hello",
    version_code=1,
    version_name="0.1.0",
    min_sdk=24,
    target_sdk=36,
    state_dir="build/api-hello-identity",
)
```

`build_apk()` does not require TOML. Without `state_dir`, it uses `.anpyra/` next to the source. Output must not contain the source or overlap the signing directory. Unlike project-managed paths, direct API paths can be absolute; callers select their own destinations.

## 🧠 Compile without packaging

```python
from pathlib import Path

from anpyra import compile_file, compile_source

compiled = compile_file(Path("examples/score/app.py"))
print(compiled.ir.pretty())

text = Path("examples/hello/app.py").read_text(encoding="utf-8")
compiled = compile_source(text, source_path=Path("hello_preview.py"))
print(compiled.ir.qualified_activity)
```

Both return `CompileResult(source_path, ast_tree, ir)` and accept `package`/`label` keyword arguments. `compile_file()` currently expects a `Path`; build functions also accept strings. Compilation alone does not write artifacts or create an identity.

## 📋 BuildResult fields

| Field | Type/purpose |
| --- | --- |
| `apk_path`, `unsigned_apk_path`, `manifest_path`, `dex_path`, `report_path` | `Path` values for written output |
| `compile_result` | Source AST and typed app IR |
| `dex_build` | DEX bytes, registers and method listings |
| `verification` | `ApkReport` for the verified staged APK |
| `apk_size` | Length of the signed APK |

## 🚦 Handle errors

```python
from anpyra import CompileError, ConfigError, build_project

try:
    result = build_project("myapp")
except (CompileError, ConfigError) as error:
    print(f"Fix the project: {error}")
```

Filesystem, cryptography, backend and subprocess errors can use other exception types; do not assume those two classes cover every failure. The CLI catches command errors and returns `1`; direct calls expose tracebacks useful to maintainers.

## 🔒 Public and internal interfaces

The package root exports authoring types, configuration records, compile/build functions and user-facing errors. Compiler and Android component modules are implementation details in the alpha series. The cleanup removes common/platforms and compiler.dex internal paths; DEX code lives in android.dex. For example, `anpyra.android.verify.inspect_apk(Path(...))` is currently available internally, but there is no package-root verification function or API stability promise for that module.
