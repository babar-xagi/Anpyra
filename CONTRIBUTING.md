# 🤝 Contributing to Anpyra

Anpyra is an alpha native compiler framework. Contributions should make one concrete behavior clearer, more reliable, or more useful without claiming unsupported Python/Android features.

## 🧭 Find your starting point

- Users: begin with the [user guide](docs/user_guide/README.md).
- Maintainers: read [development setup](docs/developer_guide/development_setup.md) and [source reference](docs/developer_guide/source_reference.md).
- Feature proposals: check [roadmap phases](docs/roadmap.md).
- Bug reports: use [troubleshooting](docs/user_guide/troubleshooting.md) and [debugging](docs/developer_guide/debugging.md).

## 🐛 Report a bug

Provide expected/actual behavior, exact command, minimal app source/config, host versions and complete error. For Android issues, include device/API and install/launch results. A redacted IR/Dalvik excerpt or report helps; private signing keys and unrelated device logs do not belong in an issue.

The [bug report template](.github/ISSUE_TEMPLATE/bug_report.md) provides those fields. State whether the source is documented as supported; an unsupported feature request is a different discussion from broken existing behavior.

## 🧩 Propose a feature

Describe the concrete app you want to build, minimal syntax/API, expected Android behavior, roadmap phase and acceptance criteria. Explain compiler/IR/backend/package impact using the [extension guide](docs/developer_guide/extending.md). Avoid making the front end accept a feature before code generation exists.

## 🏗️ Prepare a change

1. Create a descriptive branch and establish passing baseline checks.
2. Reproduce the problem with a focused test or concrete documented example.
3. Make the smallest coherent change across necessary stages.
4. Put unit/integration/historical regression checks in their matching groups.
5. Update user/developer guides if behavior, paths or limits change.
6. Run relevant checks and describe their results honestly.

```powershell
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
ruff check src tests examples scripts
ruff format --check src tests examples scripts
python scripts/check_docs.py
git diff --check
```

For runtime or binary-format changes, follow [device/release validation](docs/developer_guide/testing.md). A docs-only change needs link/example checks; relocating tests also needs complete discovery and example smoke checks.

## 🧹 Repository conventions

Use `src/` for runtime code, `examples/` for complete application projects, `tests/` for evidence, `docs/user_guide/` for user tasks and `docs/developer_guide/` for internals. Keep documentation in simple English with meaningful emoji headings and relative file links.

Do not commit generated APKs/DEX, local environments, caches, or debug/release keys. Preserve experiment fixtures as historical inputs. Maintain public import compatibility deliberately and record any breaking behavior in the changelog.

## 📝 Review description

Use the [PR template](.github/pull_request_template.md). Explain the original problem, resulting behavior, affected stages, validation, compatibility and remaining limitations. Distinguish tests you ran from CI/device checks still pending. Keep roadmap completion tied to actual evidence.

The repository uses [Apache-2.0](LICENSE); preserve relevant notices when modifying existing code.
