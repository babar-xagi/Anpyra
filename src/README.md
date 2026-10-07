# 🧱 Source Navigation

Anpyra now has a direct Android-only layout. Public API/configuration/build/CLI files live at the package root. Python source analysis lives in compiler/; native artifact components live in android/.

| Area | Responsibility |
| --- | --- |
| anpyra/api.py | Activity/TextView authoring stubs |
| anpyra/config.py | AppConfig, Project, TOML and safe paths |
| anpyra/scaffold.py | New Android project templates |
| anpyra/cli.py, build.py | User commands and build orchestration |
| anpyra/compiler/frontend.py, ir.py | Python AST validation and typed operation records |
| anpyra/components/layout.py, textinput.py, chat.py | Unreleased layout/input/controller authoring |
| anpyra/compiler/interactive.py | Layout/input/binding source contracts |
| anpyra/android/layout.py, chat.py | Native layout/input and standalone chat behavior |
| anpyra/android/screen.py | Native Android screen/lifecycle method calls |
| anpyra/android/codegen.py, dalvik.py | Method frames/control flow and instruction assembly |
| anpyra/android/dex.py, dex_types.py, encoding.py | DEX container, records and binary primitives |
| anpyra/android/classes.py, method_builder.py | Multi-class controller metadata and callback/worker code |
| anpyra/android/manifest.py, manifest_inspect.py | Binary XML writing/reading |
| anpyra/android/packaging.py, signing.py, verify.py | APK ZIP, retained identity/signature and integrity |
| pyandroid/__init__.py | Historical authoring class exports |

There are no common/platform registry or future-target packages. See [component ownership](../docs/developer_guide/android_components.md), [every source file](../docs/developer_guide/source_reference.md), and [progress](../docs/progress.md). Keep app projects, caches and signing state outside src/.
