# 🧪 Test Navigation

Run all tests from the repository root:

```powershell
python -m unittest discover -s tests -v
```

## 🗂️ Groups

| Directory | Files | What it protects |
| --- | --- | --- |
| `unit/` | `test_compiler.py`, `test_config.py`, `test_dex.py`, `test_architecture.py`, `test_release.py`, `test_screen.py`, `test_textview.py`, `test_button.py` | Source/config/DEX behavior, native boundaries and release guards |
| `integration/` | `test_build.py`, `test_cli.py`, `test_screen_assets.py`, `test_text_fonts.py`, `test_button_assets.py` | Build output, signing identity, tamper checks and command workflow |
| `regression/` | `test_functions.py`, `test_android_output.py` | Preserved experiment 008 helper and APK contracts |
| `fixtures/` | `exp005.py`–`exp008.py` | Historical source inputs, not executed apps/test runners |

`__init__.py` files allow grouped discovery/imports. The suite contains 138 tests, including Android component ownership, import compatibility, early unsupported-target rejection, release guards and exact experiment DEX output. Fixtures resolve from `tests/fixtures/`, independently of which group owns a test. New `unit/test_interactive.py` and `integration/test_chat_build.py` cover layouts/inputs/bindings, independently read multi-class/exception metadata, conditional INTERNET permission and signed chat reproducibility. CLI checks protect Unicode dumps in legacy-encoded Windows pipes.

Run a focused module with `python -m unittest tests.unit.test_dex -v`. See the [testing guide](../docs/developer_guide/testing.md) for coverage, gaps, distribution checks and manual device acceptance. Keep generated keys/artifacts in temporary directories, not fixtures.

## 🎨 Screen coverage

unit/test_screen.py checks declared colors/opacity/gradient/image options, compiler diagnostics/ownership, field references and wide instruction words. integration/test_screen_assets.py covers actual RGBA/frames/common formats/profiles/metadata, packaging/signatures, no-write check and corrupt-image/output protection. The separate opt-in device matrix is described in the [styling internals](../docs/developer_guide/screen_styling.md).

## 🔤 Typography coverage

unit/test_textview.py protects native text property validation, diagnostics, imports, related font/gravity/dimension state, line limits and unique DEX references. integration/test_text_fonts.py covers original standalone TTF/OTF assets, no-write validation, reproducibility, bad-font protection and signed malformed font rejection. Device evidence is recorded separately.

## 🟦 Button coverage

unit/test_button.py protects the native subtype, validation, states/gravity, parenting, enabled branches, method IDs and actual iput words. integration/test_button_assets.py checks contain/cover/fill alpha geometry, no-write validation, output preservation, signature checks and shared font/icon packaging. All existing regression checks continue to pass. Device cases are separate from normal CI.

## 🖱️ Generic event/state coverage

`tests/unit/test_events.py` validates source contracts and runs generated callback/save/restore bytes through the independent test-only `tests/dex_runtime.py`. Native acceptance uses `scripts/check_events_device.py`; mixed ChatSession/controller acceptance uses `scripts/check_chat_device.py --mixed --work-dir build/chat-mixed-checks`. See the [implementation guide](../docs/developer_guide/events.md).
