# 🧱 Source Navigation

`anpyra/` is the installable framework. `pyandroid/` is the compatibility import package for historical application source.

| Area | Purpose |
| --- | --- |
| Top-level Anpyra files | Public API, configuration, scaffold, CLI and build orchestration |
| `anpyra/compiler/` | Source AST, typed IR, register/instruction assembly and DEX |
| `anpyra/android/` | Binary manifest, APK v2 signing and verification |
| `pyandroid/__init__.py` | Re-export Activity/TextView for old imports |

For each file's classes/functions, implemented behavior, limits and tests, read the [source reference](../docs/developer_guide/source_reference.md). For data flow, read [architecture](../docs/developer_guide/architecture.md). Do not put application projects or generated artifacts inside the framework package.
