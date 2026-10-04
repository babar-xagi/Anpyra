# 📝 Changelog

This file records user-visible milestones. Planned work belongs in the [roadmap](docs/roadmap.md), not as completed release notes.

## 🛠️ Unreleased

### 📚 Documentation

- Modern project README with navigation, badges, pipeline, supported feature summary and alpha limits.
- Detailed user/developer guides, file/function map, debugging and extension workflows.
- Full phase roadmap distinguishing implemented work from pending device validation and future features.
- Contribution, issue/PR templates and walkthroughs for both examples.

### 🗂️ Organization and checks

- Existing tests grouped into unit/integration/regression without changing public framework module paths.
- Historical fixtures retained; discovery markers added for grouped tests.
- Documentation link/title/Python-example checks and CI integration.
- Source-distribution inclusion of documentation, examples, tests and repository maintenance files.

## 📦 0.1.0 — October 4, 2026

- Unified the PyAndroid 001–008 work around the cumulative experiment 008 compiler.
- Added installable package, typed authoring imports, project configuration and compile/build APIs.
- Added six CLI commands, example projects, JSON build report and v2 APK verification.
- Retained per-project debug signing identity and deterministic package metadata.
- Added 41 host tests, Ruff checks and Windows/Linux CI configuration.
- Built/verified both examples and tested isolated wheel installation/new-app build.

The baseline is alpha. Original experiment device success was reported by the author; framework-specific phone acceptance and independent binary inspection remain pending. There is no full Python runtime, general Android binding surface, release identity workflow or publishing service in this version.
