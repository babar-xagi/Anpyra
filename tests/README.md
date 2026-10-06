# 🧪 Test Navigation

Run all tests from the repository root:

```powershell
python -m unittest discover -s tests -v
```

## 🗂️ Groups

| Directory | Files | What it protects |
| --- | --- | --- |
| `unit/` | `test_compiler.py`, `test_config.py`, `test_dex.py`, `test_platforms.py`, `test_release.py` | Source/config/DEX behavior, native boundaries and release guards |
| `integration/` | `test_build.py`, `test_cli.py` | Build output, signing identity, tamper checks and command workflow |
| `regression/` | `test_functions.py` | Preserved experiment 008 helper and APK contracts |
| `fixtures/` | `exp005.py`–`exp008.py` | Historical source inputs, not executed apps/test runners |

`__init__.py` files allow grouped discovery/imports. The suite contains 54 tests, including native boundaries, import compatibility, target dispatch and release guards. Fixtures resolve from `tests/fixtures/`, independently of which group owns a test.

Run a focused module with `python -m unittest tests.unit.test_dex -v`. See the [testing guide](../docs/developer_guide/testing.md) for coverage, gaps, distribution checks and manual device acceptance. Keep generated keys/artifacts in temporary directories, not fixtures.
