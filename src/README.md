# 🧱 Source Navigation

`anpyra/` is the installable framework. `pyandroid/` is the compatibility import package for historical application source.

| Area | Purpose |
| --- | --- |
| Top-level Anpyra files | Public imports, scaffold, CLI and native build dispatch |
| `anpyra/common/` | Source AST, IR, identity/version validation and project paths |
| `anpyra/platforms/registry.py` | Available/planned native target inventory |
| `anpyra/platforms/mobile/android/` | Authoring/config, DEX, binary manifest, APK/signing/verification |
| `anpyra/platforms/mobile/ios/` | Reserved future iOS backend |
| `anpyra/platforms/desktop/{windows,macos,linux}/` | Reserved future desktop backends |
| `anpyra/compiler/`, `anpyra/android/` | Historical import forwarding only |
| `pyandroid/__init__.py` | Re-export Activity/TextView for old imports |

For each file's classes/functions, implemented behavior, limits and tests, read the [source reference](../docs/developer_guide/source_reference.md). For data flow, read [architecture](../docs/developer_guide/architecture.md). Do not put application projects or generated artifacts inside the framework package.

Only Android is implemented. Common compiler/IR code still describes the current Activity/TextView model; future native backends require semantic work as explained in [native architecture](../docs/developer_guide/native_platforms.md). Web is outside target scope.
