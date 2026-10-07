# 🛠️ Developer Guide

This guide is for maintainers and contributors extending or fixing Anpyra. It describes the code that exists today and identifies boundaries that future work must change.

## 🧭 Reading order

| Page | Purpose |
| --- | --- |
| [Repository structure](repository_structure.md) | Understand each directory, tracked files and generated artifacts |
| [Development setup](development_setup.md) | Create an environment, run checks and work on a change |
| [Architecture](architecture.md) | Follow configuration/source through the build pipeline |
| [Android components](android_components.md) | Screen, method generation, DEX, packaging and ownership |
| [Source reference](source_reference.md) | Every source file, its classes/functions, behavior and relevant tests |
| [Compiler internals](compiler.md) | AST validation, IR, symbols, registers, instructions and DEX layout |
| [Android backend](android_backend.md) | Binary manifest, ZIP, debug identity, v2 signing and verification |
| [Debugging](debugging.md) | Symptom-to-file map and concrete bug-fixing workflow |
| [Testing and device acceptance](testing.md) | Grouped tests, their coverage, gaps and device checklist |
| [Extending Anpyra](extending.md) | Add syntax or a widget across the whole pipeline |
| [Release checklist](release.md) | Version, packaging, validation and distribution gates |
| [PyPI publishing](publishing.md) | Account setup, manual CI pipeline, version tags and release commands |

## 🎨 Screen styling

[Implementation and native pixel testing](screen_styling.md) maps the component/parser/assets/DEX changes and exact validation.

## 💬 Chatbot and interactive components

[Native chatbot implementation](chatbot.md) maps every new file, generated classes, fields, requests, response parsing and key-free device tests. This is an unreleased source feature with focused ChatSession actions; generic Python callbacks remain future work.

## 🎯 Start with the problem

For a source error, begin in `compiler/frontend.py`. For wrong DEX, compare IR with `android/dex.py`. For installation/signature issues, trace `android/` and its `build.py`. The [debugging guide](debugging.md) maps specific symptoms to methods and tests.

The public import surface remains anpyra and historical pyandroid. Source analysis is in compiler/; the Android components are in android/. android/dex.py is the canonical DEX entry point; it retains the legacy writer and dispatches chat apps to android/classes.py. The former common/platforms and internal compiler.dex paths were removed intentionally. Read [progress](../progress.md) for completed work and success evidence.

## 📋 Work planning

Use the [roadmap](../roadmap.md) to distinguish implemented capabilities from future phases. Use [CONTRIBUTING.md](../../CONTRIBUTING.md) for review conventions and the [changelog](../../CHANGELOG.md) to record user-visible changes.
