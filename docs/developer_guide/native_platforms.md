# 🌍 Native Platform Architecture

Anpyra currently builds **Android apps only**. The source layout reserves separate native mobile and desktop backends for future work. Web is outside this project's target scope.

## 🧭 Target status

| Family | Target | Directory under `src/anpyra/platforms/` | Status |
| --- | --- | --- | --- |
| Mobile | Android | `mobile/android/` | Implemented: Python subset → DEX → APK |
| Mobile | iOS | `mobile/ios/` | Reserved; no compiler, UI bindings or packaging |
| Desktop | Windows | `desktop/windows/` | Reserved; no executable generation or UI bindings |
| Desktop | macOS | `desktop/macos/` | Reserved; no executable generation or UI bindings |
| Desktop | Linux | `desktop/linux/` | Reserved; no executable generation or UI bindings |

Building an Android APK on a Windows computer describes the **host**. It does not mean Anpyra can build Windows applications. The target is the platform that runs the generated application.

## 🧱 Shared code

The [common package](../../src/anpyra/common/README.md) owns reusable source analysis, IR records, application identity/version validation and project path rules. It does not import target backends, DEX writers, manifest writers, cryptography or adb. Platform backends depend on this layer.

The current compiler still recognizes `Activity`, `on_create` and `TextView`. Its IR retains Android lifecycle/widget operations and descriptor helpers; its register budget reflects the existing Android emitter. Moving these files creates a dependency boundary, **not a finished platform-independent UI language**. Future platform work must generalize these contracts with tests and preserve existing Android source behavior.

SDK levels belong to Android's `AppConfig`. The common `ApplicationMetadata` contains only package/application ID, label and version fields. `Project` accepts path settings supplied by a backend; the current TOML loader remains Android-specific.

## 📱 Android-owned code

[Android's package](../../src/anpyra/platforms/mobile/android/README.md) owns authoring stubs, SDK settings, DEX emission, binary XML, APK ZIP packaging, signing identity and verification. `backend.py` provides `load_project`, `check_project` and `build_project` for dispatch. Android native references and package formats should stay here.

Public `Activity`, `TextView`, `AppConfig`, `BuildResult` and `build_apk` currently expose Android behavior. Their existing names and defaults are retained; they should not be advertised as cross-platform widgets or generic artifact records.

## 🔀 Target dispatch

[registry.py](../../src/anpyra/platforms/registry.py) is the single target inventory. `TargetInfo` records name, family and optional backend module. A target is available only when its backend module is registered. `get_backend` rejects planned targets before any project files or signing identities are created.

```powershell
anpyra targets
anpyra check examples/hello --target android
anpyra build examples/hello --target android
```

`build` and `check` default to Android. Selecting `--target ios` or `--target windows` returns a clear not-implemented error. `web` is an unknown target. `init` still creates Android projects; `verify`, `install` and Dalvik dumps remain Android operations.

```python
from anpyra import build_project

result = build_project("examples/hello", target="android")
print(result.apk_path)
```

The dispatcher returns the current Android `BuildResult`. A generic result contract and backend protocol should be designed when a second real backend exists, based on its actual artifacts and capabilities.

## 🔗 Historical imports

Existing imports under `anpyra.compiler` and `anpyra.android` forward to canonical implementations. The wrappers contain no second compiler or signer. Named imports resolve the same classes/functions, including exception types. New internal code should import `anpyra.common` or the appropriate `anpyra.platforms` module.

Edit the canonical implementation when fixing a bug. Forwarding wrappers are import compatibility surfaces; monkeypatch a canonical implementation module when testing its internal calls.

## 🛠️ Adding a future backend

1. Establish the target's source/UI semantics, native artifact format, build host constraints and toolchain/signing requirements. Android's Python-only pipeline does not establish other targets' requirements.
2. Generalize shared source/IR operations where needed, with Android regressions and clearly unsupported combinations.
3. Implement native code generation, UI bindings, project configuration and packaging inside the target directory. Keep target settings out of common metadata.
4. Define real backend entry points and an appropriate result contract. Add positive build tests plus target-specific runtime acceptance.
5. Register the backend only after it can perform its documented workflow. Update scaffolding, CLI capabilities, examples and user documentation together.

The roadmap tracks this as [phase 11](../roadmap.md). Android validation and feature development remain the immediate priorities.

## 🧪 Boundary checks

[test_platforms.py](../../tests/unit/test_platforms.py) checks shared imports, current target availability, common metadata, historical object identity and rejection before writes. CLI integration tests cover target listing and unsupported selections. Binary/build tests continue to exercise the canonical Android backend.
