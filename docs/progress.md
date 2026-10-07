# 📊 Implementation Progress and Verified Results

**Updated: October 7, 2026.** Current focus: finish the Android framework. Release version: **Anpyra 0.1.5**. This version includes Android-only components, Screen styling, TextView typography, native Button design, layouts/input and scoped ChatSession. The original 0.1.0/0.1.1 releases remain immutable.

## 🖱️ Generic events/state (0.1.5) — October 7, 2026

- Implement named `button.on_click(self.handler)`, typed mutable Activity scalar fields and retained widget references.
- Compile integer/string/boolean expressions, reassignment, branches, runtime text/enabled operations and acyclic handler calls. Branch locals must be definitely initialized; lifecycle calls validate transitive field initialization.
- Implement explicit `State(..., persist=True)` Bundle save/restore. Memory-only fields reset on recreation; widget references are recreated. New tasks start from defaults when no saved Bundle is supplied.
- Pass **138 host tests**, including 17 event/source/emitted-byte tests. The independent test executor reads actual DEX instructions and controlled native calls; it is not an ART verifier or an APK runtime.
- Record **11 native event cases** on TECNO BG7 / API 33: initial state, repeated clicks, reset/decrement, disabled/boolean state, input/string preview, opted-in int/string/bool restoration, memory-only reset, new-task reset and signed-int32 boundaries.
- Preserve the exact pre-change ChatSession DEX and historical experiment DEX hashes. Generic/chat composition passed 15 controlled native cases, including independent callback dispatch before/after chat requests and scoped busy controls.
- Publish 0.1.5 through Trusted Publishing and verify public fresh installation/upgrades. Earlier PyPI files remain immutable.

Evidence: ignored `build/event-device-checks/report.json` and screenshot. Physical rotation, broader lifecycle hooks and other Android versions still need separate checks. [Usage](user_guide/events.md) and [file ownership](developer_guide/events.md) explain supported behavior and limits.

## 💬 Standalone chatbot (0.1.4) — October 6, 2026

The current source adds Column, Row, ScrollView, TextInput and ChatSession alongside the released Screen/TextView/Button components. It generates a native Android click listener, worker thread, HTTPS/JSON request, UI delivery and in-memory history. No Python server or embedded Python/OpenAI SDK is needed.

| Check | Result and scope |
| --- | --- |
| Host regression suite | **121 tests passed**, including nine new layout/chat/source/DEX/build tests and a Windows Unicode-output regression; historical DEX output preserved |
| Source/docs quality | Ruff lint/format passed; 58 Markdown files and 11 documented Activity examples checked |
| Isolated local wheel | New modules present, no key/APK/DEX/cache payloads; separate wheel-only environment built and verified the chatbot |
| Production app | 8,882-byte signed `dev.anpyra.chatbot` APK built, verified, installed and launched on TECNO BG7, Android API 33 |
| Controlled native acceptance | **13 checks passed**, seven synthetic requests; missing key/message, masked password, scrollable long text, busy guard, worker/delivery, full-output history, quota/malformed/incomplete recovery, refusal and New chat reset |
| Visual review | Password dots and scrolling to the measured reply bottom confirmed; native call order/child sizing corrected after initial screenshot review |
| Live OpenAI access | Supplied temporary key returned HTTP 429, `credit_balance_exhausted`, `insufficient_quota`; **no successful live AI answer verified** |
| Publication | **PyPI 0.1.4 published and public-index checks passed**; earlier releases remain immutable |

Device automation initially sent Back while OEM keyboard visibility was stale; the test now keeps the keyboard open and uses the resized app's button bounds. Acceptance evidence is under ignored `build/chat-device-checks/` (`report.json`, synthetic requests, screenshot). Controlled responses validate native controller behavior separately from provider/model behavior.

Read the [user guide](user_guide/chatbot.md) for installation/usage and [developer file map](developer_guide/chatbot.md) for every added file, implemented code and bug-fixing ownership. Generic Python callbacks, durable state, streaming, cancellation and additional Android-version coverage remain future work.

## ✅ Released foundation evidence

| Milestone | Result | Evidence/limits |
| --- | --- | --- |
| Original experiments 001–008 | Author reported successful runs | Historical source fixtures 005–008 retained |
| Framework source checking | Passed | Starter app produces typed IR and native method listings without writing artifacts |
| Signed APK generation | Passed | Hello/score and fresh generated projects build and pass framework verification |
| PyPI publication | Passed, October 6 | [0.1.3 Trusted Publishing run](https://github.com/babar-xagi/Anpyra/actions/runs/37539219407) succeeded; [PyPI 0.1.3](https://pypi.org/project/anpyra/0.1.3/) wheel/source hashes match checked CI artifacts |
| Public-index installation | Passed | Fresh `anpyra==0.1.3` installation built/verified starter and Button/state/ripple/icon APKs; Button rebuild was byte-identical |
| Package upgrades | Passed | Separate pip/uv environments upgraded 0.1.2 → 0.1.3; starter APK bytes, project configuration and signing identity preserved; new Button/icon builds verified and reproducible |
| Windows/Linux release CI | Passed | Published candidate validated on Python 3.11/3.13 |
| Author's phone installation | **Author confirmed success** | Default starter package `dev.anpyra.app`, verified APK, adb detected an authorized device; reported installation completed |
| Current Android-only cleanup | Host checks passed | 55 tests; four experiment DEX hashes/listings and both signed example APK hashes equal their pre-cleanup output |
| Full runtime acceptance | Partially recorded | Installation confirmed; exact screen text, score branches, lifecycle and independent verifier results still require records |

Phone installation and the API 33 Screen checks below are concrete successes. Device-model records and the broader lifecycle/score checklist remain incomplete; these results do not establish coverage of every widget or Android version.

## 🧱 What is implemented?

### 🐍 Source compiler

- Static Python parsing; app source is never imported/executed on the build computer.
- One Activity class and `on_create` lifecycle method.
- Initialized `str`, `int`, `bool` locals, symbol/type checks and useful source errors.
- Signed 16-bit integer literals and simple `+`/`-` calculations.
- Boolean branches, integer comparisons and nested conditions.
- Top-level typed integer helpers, up to five parameters, static method calls and returned results.
- Rejection of unsupported imports, declarations, source forms and invalid initialization.

Files: [frontend](../src/anpyra/compiler/frontend.py), [IR](../src/anpyra/compiler/ir.py).

### 📺 Native screen

- Activity superclass lifecycle call.
- TextView allocation and initialization with Activity context.
- Literal/typed string passed to Android `setText`.
- One unconditional content-view attachment.

Files: [authoring API](../src/anpyra/api.py), [screen bindings](../src/anpyra/android/screen.py), [method generation](../src/anpyra/android/codegen.py). Android renders these generated native calls; no host preview exists.

### ⚙️ Dalvik and DEX

- Low-register lifecycle frame and high-register incoming helper parameters.
- Constant, allocation, invocation/result, arithmetic, return and condition instructions.
- Symbolic label resolution and signed branch displacement checks.
- DEX 035 string/type/prototype/method/class tables, code/class data and map.
- UTF-16 ordering, modified UTF-8 strings, alignment/ULEB128, SHA-1 and Adler-32.

Files: [Dalvik](../src/anpyra/android/dalvik.py), [encoding](../src/anpyra/android/encoding.py), [DEX records](../src/anpyra/android/dex_types.py), [DEX writer](../src/anpyra/android/dex.py).

### 📦 Android package and signing

- Binary manifest with identity, versions, SDKs and exported launcher Activity.
- Deterministic unsigned ZIP containing manifest and classes.dex.
- Retained RSA debug identity; incomplete/mismatched pairs rejected.
- APK Signature Scheme v2 with SHA-256 content digest/signature.
- Staged verification before artifact replacement.
- Signed/unsigned APK, DEX, manifest and JSON build report.

Files: [manifest](../src/anpyra/android/manifest.py), [packaging](../src/anpyra/android/packaging.py), [signing](../src/anpyra/android/signing.py), [verification](../src/anpyra/android/verify.py), [build orchestration](../src/anpyra/build.py).

### 🧰 Project and release tooling

- Validated TOML, safe project paths, starter scaffold and stable public authoring/build APIs.
- CLI init/check/build/verify/doctor/targets and optional adb install/launch.
- Grouped tests, original fixtures, byte-level checks and output preservation checks.
- uv-recommended installation with pip alternatives and separate user/developer guides.
- Manual release pipeline, version/tag/archive/description checks, isolated wheel smoke and Trusted Publishing.
- Version 0.1.1 published from commit `3ef07e9b6fa625d6d1c90b4abbf539ef77283df7`, tag `v0.1.1`; [GitHub release](https://github.com/babar-xagi/Anpyra/releases/tag/v0.1.1) provides notes and install/upgrade commands.

### 🔐 Published 0.1.1 archive fingerprints

| File | SHA-256 |
| --- | --- |
| `anpyra-0.1.1-py3-none-any.whl` | `676fa4d927920cd8e4a1fae227a414ce6e33cb91adafe70be6c3bbc20e24db4d` |
| `anpyra-0.1.1.tar.gz` | `051d100d3bec01ed76950500a373d19f79402071e4f10da4c1645abdded112ac` |

## 🎨 Screen component (0.1.1)

- Implemented components/screen.py and component imports, with declarative style.bg color/image/gradient/opacity/transparent values and one TextView foreground child.
- Support RGB/ARGB/CSS colors, seven native image fit modes, linear directions, radial/sweep and layered/group transparency; foreground text color is configurable.
- Validate project-local images, static frames, orientation/profiles/alpha; package normalized PNGs by content hash and verify their signed payload/digests.
- Extend DEX fields, constants, arrays, object returns, typed register copies and range calls; preserve legacy DEX hashes.
- 76 host tests pass. On the author's Android API 33 phone, 25 native pixel cases passed (base, RGB/ARGB/group/transparent/image alpha, eight linear directions, radial/sweep and seven fit modes). Combined image/gradient/text rendering was visually confirmed.
- Native API 24–28 and additional devices still need separate runtime coverage. General layouts/events, remote/vector images and animation playback remain outside this first component contract.

Details: [user API/options](user_guide/screen.md), [implementation/tests](developer_guide/screen_styling.md), [runnable example](../examples/screen_style/README.md).

## 🧹 What changed in the cleanup?

The active source tree now has `compiler/` and `android/`, with ordinary root API/config/build/CLI files. Common/platform registry layers and desktop/iOS placeholders were removed. DEX container writing, method generation, instruction assembly, native screen bindings and APK ZIP packaging have separate owners.

Public `from anpyra import ...` and `pyandroid` authoring imports continue to work. Internal imports under removed common/platforms packages and compiler.dex change intentionally; use android.dex for DEX internals. This cleanup ships under version/tag 0.1.1/v0.1.1 and does not replace immutable PyPI 0.1.0 files.

## 🎯 Work still needed to complete Android

1. Record model/API, visible starter text, both score branches and lifecycle behavior; independently inspect APK/DEX.
2. Improve diagnostics, malformed-input coverage, artifact interruption behavior and instruction/register limits.
3. Add deliberate reassignment/definite initialization, stronger helper bodies and register lifetime analysis.
4. Implement native layout/child widgets, then buttons/input and typed properties.
5. Implement callbacks, persistent fields/state and lifecycle/recreation contracts.
6. Add static multi-file composition, resource/assets packaging and expanded verification.
7. Add protected release identity/import and tested upgrade/distribution workflows.

These are planned capabilities. Loops, collections, general Python imports/runtime, interactive widgets, resources and release/store signing are not implemented by the directory cleanup. See the detailed [roadmap](roadmap.md) and [component guide](developer_guide/android_components.md).

## 🔤 Expanded TextView component (0.1.2)

- Move the real TextView authoring class to components/textview.py; root/api/pyandroid imports re-export the same class.
- Implement text content/constructor keywords plus foreground/background color, sp size, dp padding/dimensions, horizontal/vertical gravity, opacity, system/local fonts, bold/italic, wrapping/line limits/ellipsis, spacing, decoration, selection, shadows, direction, OpenType features and accessibility description.
- Add ordered style IR, combined property state, runtime density conversion and unique native method references; keep legacy experiment DEX unchanged.
- Validate and package byte-preserved standalone TTF/OTF fonts under signed content hashes; invalid fonts fail before keys/output changes.
- Add original demo fonts, runnable typography example, detailed user/developer references, 19 new host tests and opt-in device checks.
- All 95 host tests, docs/lint/workflow checks and local wheel/source checks passed. An isolated wheel installation built/verified the font example. Legacy experiment DEX hashes remain unchanged.
- On TECNO BG7 / Android API 33, 30 recorded cases passed: size/letter spacing, 15 gravity combinations, dp padding/dimensions, TTF/OTF, bold/italic, decoration add/remove, uppercase, opacity, line spacing, RTL and selection focus; remaining native options passed combined launch and visible ellipsis/shadow checks. Native Copy/Share toolbar was visually confirmed after long-press; clipboard copying/sharing was not performed.
- The device runner accounted for the OEM's clipped accessibility bounds by measuring its controlled app background. Previously captured screenshots for unchanged cases were replayed during final tail checks; device results distinguish reused captures. API 24–28 and other devices/fonts still need separate runtime coverage.
- Expanded typography ships under version/tag 0.1.2/v0.1.2; it does not replace immutable PyPI 0.1.1 files.

## 📦 Verified 0.1.2 publication

Published October 6, 2026 from commit `21b8ed8aefd11c0c267734b87c4e81f84c6548fd`, tag `v0.1.2`. [Publishing run](https://github.com/babar-xagi/Anpyra/actions/runs/37528963281) and [GitHub release](https://github.com/babar-xagi/Anpyra/releases/tag/v0.1.2) provide the checked files and notes. The public index installed the new APIs directly; no checkout was used by the isolated package environments.

| File | SHA-256 |
| --- | --- |
| `anpyra-0.1.2-py3-none-any.whl` | `9b4c0d00f53210835b83dea3841c00eaa8c745b980eb429f07655e49922538a9` |
| `anpyra-0.1.2.tar.gz` | `b324a27c5d9b4064c1e0f7a5175c0c3aa6d9f129f5a40d405493e364d1745de9` |

## 🟦 Native Button component (0.1.3)

- Implement actual android.widget.Button construction with shared TextView typography and a separate components/button.py API.
- Implement caller-configured fills/gradients, border/corners, opacity, state label/background/border colors, native ripple, dimensions/placement/margins, elevation and compound raster icons with fit/tint/alpha.
- Preserve native unspecified gravity and caller padding, validate single-parent attachment, support bool enabled calls/branches, and reject unimplemented callbacks explicitly.
- Share safe image decoding/normalization/signing with Screen; new icon assets are referenced by content hash, while legacy DEX output remains unchanged.
- All 111 host tests, docs/lint/workflow and local wheel/source checks pass. An isolated wheel installation builds/verifies the centered icon example; legacy DEX regressions remain byte-identical.
- On TECNO BG7 / Android API 33, 20 recorded Button cases passed: dimensions/density, real held press/release label/background colors, disabled presses, borders/corner radii, four gradient directions, four icon positions/tint, margins, explicit padding/native gravity, masked ripple, keyboard focus and native Button accessibility class. Screenshots/results are recorded by the opt-in device script.
- Hover, radial/sweep fills, every font/theme and API 24–28 still need separate runtime coverage. Native press feedback works; Python click callback compilation remains a future phase.
- Button ships under 0.1.3/v0.1.3; original PyPI 0.1.2 remains immutable. Multi-child layouts, Python callback binding, image backgrounds and additional Android runtime coverage remain planned.

## 📦 Verified 0.1.3 publication

Published October 6, 2026 from commit `1b064f99d75518394f5ead12df7c5aaf1d50aaf2`, tag `v0.1.3`. [Publishing run](https://github.com/babar-xagi/Anpyra/actions/runs/37539219407) and [GitHub release](https://github.com/babar-xagi/Anpyra/releases/tag/v0.1.3) provide the exact checked files. Fresh public installation and pip/uv upgrades from 0.1.2 passed, including signed Button/icon builds and retained existing project identity/output.

| File | SHA-256 |
| --- | --- |
| `anpyra-0.1.3-py3-none-any.whl` | `bc131961c0ce9ccb031f09abd5314a1822d39e94d18d16bf1355ba042dfa0158` |
| `anpyra-0.1.3.tar.gz` | `95bac7c3416bdb7560cbcf1bd917339560383326b540598d63e0c9845db5a591` |

## 📦 Verified 0.1.4 publication

Published October 6, 2026 from commit `80bc3b4`, tag `v0.1.4`. [Publishing run](https://github.com/babar-xagi/Anpyra/actions/runs/37573611590) passed the four Windows/Linux Python 3.11/3.13 jobs, archive/version/README guards and installed-wheel starter/Screen/typography/Button/chatbot builds. [GitHub release](https://github.com/babar-xagi/Anpyra/releases/tag/v0.1.4) contains the same exact archives as [PyPI 0.1.4](https://pypi.org/project/anpyra/0.1.4/).

Fresh public installation and separate pip/uv 0.1.3 → 0.1.4 upgrades passed. Existing configuration, source, signing certificate and starter APK hashes remained unchanged. All three 0.1.4 environments built/verified a three-class chatbot APK and a byte-identical rebuild. The initial pip query briefly listed only older versions immediately after upload; a subsequent public-index retry succeeded. These are installation/build checks; they do not establish a successful live AI answer.

| File | SHA-256 |
| --- | --- |
| `anpyra-0.1.4-py3-none-any.whl` | `e85bda713d5e5ccda55a8592359a86d0ab05e5c5d593bf3d4eebeee07ba15ffa` |
| `anpyra-0.1.4.tar.gz` | `7fa253211dfb3f21078fb656a7c6e39b961de2d547c32d33571fd24dec3f08a1` |

## 📦 Verified 0.1.5 publication

Published October 7, 2026 from commit `c9974a6`, tag `v0.1.5`. [Publishing run](https://github.com/babar-xagi/Anpyra/actions/runs/37586622006) passed Windows/Linux Python 3.11/3.13 validation, archive/version/description guards and installed-wheel builds including Counter Lab. [GitHub release](https://github.com/babar-xagi/Anpyra/releases/tag/v0.1.5) holds the exact files on [PyPI 0.1.5](https://pypi.org/project/anpyra/0.1.5/).

Fresh public installation and separate pip/uv 0.1.4 → 0.1.5 upgrades passed. Source, configuration, signing certificate and starter APK hashes stayed unchanged. All three 0.1.5 environments built/verified Counter Lab and ChatSession, with byte-identical rebuilds. These are package/build checks; native event acceptance is recorded above.

| File | SHA-256 |
| --- | --- |
| `anpyra-0.1.5-py3-none-any.whl` | `8da8b0e04b5cf14a1a324e415e62be81c9ace532ba9ea2c3e2f492e9ec19cf5b` |
| `anpyra-0.1.5.tar.gz` | `a281ae68aa56b4f73c626e1afdf6f62c731c8b10aed7210e2bad25f83d0caa7d` |
