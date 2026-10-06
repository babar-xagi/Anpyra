# 👤 User Guide

This guide is for people building small Android apps. You do not need to understand the DEX file format to begin.

## 🧭 Reading order

| Step | Page | What you learn |
| --- | --- | --- |
| 1 | [Installation](installation.md) | Environments, source/wheel install, platform-specific commands |
| 2 | [Core concepts](concepts.md) | Source, Activity, AST, IR, DEX, APK, signing and runtime |
| 3 | [First application](first_app.md) | Create, edit, check, build, verify, install and update |
| 4 | [Language reference](language.md) | Supported features, working examples and limits |
| 5 | [Configuration](configuration.md) | All settings, defaults, validation and paths |
| 6 | [Command reference](cli.md) | CLI syntax, options, output and exit behavior |
| 7 | [Build outputs](build_outputs.md) | Generated files, identity and verification |
| 8 | [Python API](python_api.md) | Use Anpyra from your own host tools |
| 9 | [Troubleshooting](troubleshooting.md) | Setup, compiler, build and installation problems |
| 10 | [Migration and FAQ](migration.md) | Move experiment apps and understand scope |
| 11 | [Android scope](android.md) | Android-only focus, build computers and device evidence |

## 🎯 Buildable examples

The included [hello](../../examples/hello/README.md) and [score](../../examples/score/README.md) projects demonstrate one native Activity, TextView content, typed values, branches, arithmetic, and simple helpers.

Check the [language reference](language.md) when writing source and the [roadmap](../roadmap.md) for future layouts, events, modules, and release workflows.

## 🔎 Report a problem

Follow [troubleshooting](troubleshooting.md), then provide the smallest failing source, your Python/Anpyra versions, exact command, and error. Maintainers can use the [debugging guide](../developer_guide/debugging.md).
