# 🧰 Development Setup

## 🏗️ Prepare your checkout

From a clean checkout with Python 3.11+:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m anpyra doctor
```

On Linux/macOS use `source .venv/bin/activate`. Windows activation is optional: invoke `.\.venv\Scripts\python.exe` and `.\.venv\Scripts\ruff.exe` directly. The development extra adds Ruff; tests use standard-library `unittest`.

## 🧪 Establish a baseline

```powershell
python -m unittest discover -s tests -v
ruff check src tests examples scripts
ruff format --check src tests examples scripts
python scripts/check_docs.py
anpyra check examples/hello
anpyra check examples/score
```

Tests are grouped by responsibility but the root discovery command still runs all 41 baseline tests. Package markers make the groups discoverable on supported Python versions. Run from the repository root.

## 🌿 Work on a change

Use a descriptive branch such as `codex/fix-branch-offset`. Identify the smallest relevant test and reproduction before modifying a binary format. Keep the public source module imports intact unless an intentional API change is required.

```powershell
git switch -c codex/fix-branch-offset
python -m unittest tests.unit.test_dex -v
```

The [debugging guide](debugging.md) maps symptoms to code; the [extension guide](extending.md) explains feature work across stages.

## 🧭 Local commands

| Goal | Command |
| --- | --- |
| Compiler diagnostics | `anpyra check examples/score --dump-ir --dump-dalvik` |
| Framework tests | `python -m unittest discover -s tests -v` |
| Compiler/config/DEX tests | `python -m unittest discover -s tests/unit -v` |
| Build/CLI tests | `python -m unittest discover -s tests/integration -v` |
| Historical helper regression | `python -m unittest tests.regression.test_functions -v` |
| Format edited files | `ruff format src tests examples scripts` |
| Lint | `ruff check src tests examples scripts` |
| Documentation checks | `python scripts/check_docs.py` |
| Build wheel | `python -m pip wheel --no-deps . --wheel-dir dist` |

Do not format or rewrite historical fixtures to "improve" their semantics. Their declarations are compiler inputs, including deliberately unused locals; Ruff permits `F841` in fixtures.

## 🔎 Before review

Review `git diff --check`, `git diff` and `git status --short`. Check that generated APKs, certificates/private keys, environments and caches are absent from the change. Update relevant guides when behavior changes. The [pull request template](../../.github/pull_request_template.md) captures problem, change, validation and limits.

Use [release checks](release.md) for a distributable build. Publishing a release is a separate action from building a local wheel.
