# 🧪 Testing and Device Acceptance

## 🗂️ Test layers

| Layer | Files | Purpose |
| --- | --- | --- |
| Unit | `tests/unit/test_compiler.py` | Types, syntax/rejection, historical source compatibility, initialization and register limits |
| Unit | `tests/unit/test_screen.py` | Component values, source diagnostics, native fields and wide instruction words |
| Unit | `tests/unit/test_config.py` | Settings, relative paths, invalid config, scaffolding and Unicode |
| Unit | `tests/unit/test_architecture.py` | Android-only package ownership, screen descriptors, early target rejection and historical imports |
| Unit | `tests/unit/test_release.py` | Release version/tag consistency, stale artifacts, metadata/private-path/link rejection |
| Unit | `tests/unit/test_dex.py` | Selected emitted bytes, frame layout, branch destinations, checksums and MUTF-8 |
| Integration | `tests/integration/test_build.py` | Build/manifest/signing/report/reproducibility/failure preservation |
| Integration | `tests/integration/test_screen_assets.py` | Real image assets/signatures, alpha/frames/formats, metadata and error preservation |
| Integration | `tests/integration/test_cli.py` | Command workflow and mocked device command construction |
| Regression | `tests/regression/test_android_output.py` | Exact experiment 005–008 DEX hashes from the pre-cleanup implementation |
| Regression | `tests/regression/test_functions.py` | Adapted experiment 008 typed-helper contracts |
| Fixtures | `tests/fixtures/exp005.py` through `exp008.py` | Historical source inputs; not test runners |

The current suite contains **138 tests**. Interactive/chat coverage is in `tests/unit/test_interactive.py` and `tests/integration/test_chat_build.py`. CLI coverage includes Unicode output through Windows-style legacy-encoded pipes. One exact-output regression checks all four experiment DEX hashes captured before Android component cleanup. Package `__init__.py` files allow recursive unittest discovery. Some retained regression tests build APKs, so the groups describe intent rather than strict isolation rules.

## ⌨️ Run checks

```powershell
python -m unittest discover -s tests -v
python -m unittest tests.unit.test_dex -v
python -m unittest tests.integration.test_build -v
python -m unittest tests.regression.test_functions -v
ruff check src tests examples scripts
ruff format --check src tests examples scripts
python scripts/check_docs.py
```

`check_docs.py` validates repository-owned local Markdown file links, emoji title conventions, Python snippet syntax and compilable documented Activity examples. It does not verify external URLs, anchors, network instructions or device behavior. Snippets marked `python unsupported` are syntax-checked but excluded from app compilation.

## 🏗️ Build and distribution smoke checks

```powershell
anpyra build examples/hello
anpyra build examples/score
anpyra verify examples/score/build/dev.anpyra.score.apk
python -m pip wheel --no-deps . --wheel-dir dist
```

Install the wheel into a fresh environment, change outside the source checkout, and run `python -m anpyra --version`, `init`, `build`, and `verify` on a temporary project. Otherwise an editable install can hide a missing wheel file. Confirm the wheel contains package code, license and `py.typed`, and no private keys/generated APKs.

## 🔄 CI responsibilities

[tests.yml](../../.github/workflows/tests.yml) runs on Ubuntu and Windows with Python 3.11 and 3.13. It installs the development extra, lints/formats, checks docs, runs the suite, builds examples, verifies score and builds a wheel. CI is a configured workflow; confirm actual run results before claiming all matrix jobs passed.

There is currently no emulator/device job, coverage threshold, type-checking gate or external APK verifier. macOS is not a CI target.

## 📱 Manual framework acceptance

The author reported the original experiments working on a phone. The author confirmed installation of the published starter APK on October 6, 2026. The remaining runtime acceptance checks still need records; the current source cleanup has host output-preservation evidence. Complete this checklist for a candidate release:

- [ ] Record OS/Python/Anpyra/cryptography versions and commit ID.
- [ ] Record device model, Android version/API and connection method.
- [ ] Build/verify hello; record APK/certificate fingerprints.
- [ ] Install/launch hello and confirm its exact greeting.
- [ ] Build/install score with `80 + 5`; confirm the passing text.
- [ ] Change score to `50`, rebuild with the same package/key pair, install as an update, and confirm failure text.
- [ ] Restore the score example after the test.
- [ ] Confirm app restart/lifecycle behavior and collect any crashes.
- [ ] Record independent APK/DEX inspection results if available.
- [ ] Document tested devices and any unresolved failures; do not generalize to untested platforms.

Attach evidence in a review or release record. Update the [roadmap](../roadmap.md) only when the criterion is actually completed.

## 🎯 Add meaningful tests

Test observable contracts or actual binary data. For a branch change, assert destinations land on instruction starts. For identity changes, assert the retained certificate remains stable and invalid material is preserved/rejected. For unsupported syntax, assert a useful error instead of merely mirroring the implementation.

Use temporary directories for builds and never commit generated signing material. Keep historical fixtures stable and add a new minimal fixture/test for new semantics. Do not invent arbitrary test-count targets; close a specific coverage gap.

## 🖱️ Generic event/state coverage

`tests/unit/test_events.py` validates source contracts and runs generated callback/save/restore bytes through the independent test-only `tests/dex_runtime.py`. Native acceptance uses `scripts/check_events_device.py`; mixed ChatSession/controller acceptance uses `scripts/check_chat_device.py --mixed --work-dir build/chat-mixed-checks`. See the [implementation guide](events.md).
