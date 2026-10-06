# 🐛 Debugging and Bug Fixing

Use evidence at each stage to locate a failure rather than modifying several stages at once.

## 🧭 Symptom-to-file map

| Symptom | Start in | Key functions/tests |
| --- | --- | --- |
| `python -m anpyra` or public imports fail | `__main__.py`, `__init__.py`, package configuration | Installed-path and wheel checks |
| CLI flag/output/exit wrong | `cli.py` | `main`, `_dump`; CLI integration tests |
| Project metadata/path rejected incorrectly | `config.py` | AppConfig/Project validation and load_project; config tests |
| New scaffold TOML/source broken | `scaffold.py` | `init_project`, `STARTER_SOURCE`; Unicode/scaffold roundtrip |
| Supported syntax rejected | `compiler/frontend.py` | AST predicate/statement method; compiler/regression tests |
| Undefined/type error missed | `compiler/frontend.py` | `declare`, `require`, initializer lowering |
| Correct source creates incorrect IR | Front end and `compiler/ir.py` | `compile_*` lowering and pretty output |
| Wrong registers/helper parameters | `android/codegen.py` | register maps and helper frames; binary DEX tests |
| Wrong branch destination | `android/codegen.py`, `android/dalvik.py` | `Assembler.assemble`, `emit_main`, code-unit widths |
| Missing `move-result`/wrong return | `android/codegen.py` | helper call/result/return emitters |
| DEX table/checksum/Unicode malformed | `android/dex.py`, `android/encoding.py` | sorting, MUTF-8, file layout, header integrity |
| Android package metadata wrong | `android/manifest.py`, reader | pools, attributes, SDK/version/Activity profile |
| Stored certificate/key rejected | `android/signing.py` | `load_or_create_signer_material` |
| v2 content digest mismatch | `android/signing.py`, `verify.py` | section offsets, EOCD adjustment, chunk digest |
| Previous APK lost after failure | `build.py` | staging/publication ordering; failure-preservation test |
| Wrong native view/context/text receiver | `android/screen.py`, `android/codegen.py` | Native method binding and register map |
| Wrong image/crop/gradient/opacity | android/backgrounds.py, components/screen.py, android/assets.py | Style values, native calls, fit and asset mapping |
| Wrong unsigned ZIP entries | `android/packaging.py` | Deterministic manifest/DEX plus validated PNG assets |
| APK installs but app crashes | Front end/backend + device logs | Find runtime instruction/type failure and reproduce minimally |
| Documentation link/example broken | `scripts/check_docs.py`, guide page | Run docs checks; compare language reference to compiler |

All module details are in the [source reference](source_reference.md).

## 1️⃣ Reproduce the smallest failure

Record the command and environment. Start from hello or score, then remove unrelated source until the problem remains. A minimal source/config avoids confusing a register-budget problem with a control-flow problem.

```powershell
anpyra doctor
anpyra check examples/score --dump-ir --dump-dalvik
```

Use a new temporary application directory for experiments. Do not overwrite a user's retained identity.

## 2️⃣ Compare source and IR

Ask whether names/types match the source and whether operations/branches appear in the correct order. If IR is wrong, fix lowering first. A missing `LoadConst` or incorrect function argument cannot be repaired reliably in byte encoding.

For a traceback hidden by CLI error handling, use a host script:

```python
from pathlib import Path

from anpyra import compile_file

compiled = compile_file(Path("examples/score/app.py"))
print(compiled.ir.pretty())
```

For a build-stage error, call `build_project` directly. It exposes the exception chain rather than converting it into CLI status `1`.

## 3️⃣ Compare IR, listing and bytes

Inspect register maps and assembly, then check actual encoded words. Listings are created by the same assembler as bytes and can share its error. `tests/unit/test_dex.py` independently inspects selected binary structures.

For branch bugs, calculate instruction start positions in code units, relative offsets, signed range and destination boundaries. For helper bugs, verify `registers_size`, `ins_size`, high parameter registers, static access flags and immediate `move-result`.

## 4️⃣ Narrow APK/manifest/signing failures

Build to a separate directory and verify the original artifact. Inspect `build-report.json` fingerprints/metadata. Check manifest/ZIP bytes before changing cryptography. Reusing a mismatched key pair, applying the wrong EOCD offset for digesting, or copying an incomplete artifact all have different fixes.

Never "fix" a signing failure by disabling verification. Never silently regenerate a user's identity to hide a loading failure.

## 5️⃣ Collect device evidence

Record phone model, API level, app package, certificate fingerprint and install result. Use adb to reproduce and capture relevant runtime logs:

```powershell
adb devices
anpyra install examples/score/build/dev.anpyra.score.apk --serial DEVICE_ID --launch
adb -s DEVICE_ID logcat -d > device-log.txt
```

Review logs before sharing; they may include unrelated device/application data. USB authorization/setup follows the [official adb guide](https://developer.android.com/tools/adb). Independent Android DEX/APK inspection can expose writer/reader agreement bugs that self-checks miss.

## 6️⃣ Add a regression and fix

Put the test at the lowest level that proves the failure. Use unit checks for lowering/bytes, integration checks for cross-stage output, and historical regression only for an experimental contract. Run the focused test, make the fix, then run the normal full checks if runtime/structure changed.

Update documentation if a behavior or limit changes. Explain expected/actual behavior, the root cause, validation and remaining limits in the review. See [testing](testing.md) and [contribution workflow](../../CONTRIBUTING.md).
