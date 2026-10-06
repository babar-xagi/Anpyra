# 📊 Implementation Progress and Verified Results

**Updated: October 6, 2026.** Current focus: finish the Android framework. Published package: **Anpyra 0.1.0**. The simplified Android-only source layout is an unreleased cleanup of that implementation.

## ✅ Success evidence

| Milestone | Result | Evidence/limits |
| --- | --- | --- |
| Original experiments 001–008 | Author reported successful runs | Historical source fixtures 005–008 retained |
| Framework source checking | Passed | Starter app produces typed IR and native method listings without writing artifacts |
| Signed APK generation | Passed | Hello/score and fresh generated projects build and pass framework verification |
| PyPI publication | Passed, October 6 | Wheel/source archive uploaded through [Trusted Publishing](https://github.com/babar-xagi/Anpyra/actions/runs/37472908394); [release 0.1.0](https://pypi.org/project/anpyra/0.1.0/) available |
| Public-index installation | Passed | Fresh `anpyra==0.1.0` environment created and used to build/verify an Android app |
| Windows/Linux release CI | Passed | Published candidate validated on Python 3.11/3.13 |
| Author's phone installation | **Author confirmed success** | Default starter package `dev.anpyra.app`, verified APK, adb detected an authorized device; reported installation completed |
| Current Android-only cleanup | Host checks passed | 55 tests; four experiment DEX hashes/listings and both signed example APK hashes equal their pre-cleanup output |
| Full runtime acceptance | Partially recorded | Installation confirmed; exact screen text, score branches, lifecycle and independent verifier results still require records |

Phone installation is a concrete success. It is not evidence for every widget, Android version or runtime path. The author has not yet supplied a device model/API and complete screen/lifecycle checklist for this cleanup.

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

## 🎨 New Screen component (unreleased)

- Implemented components/screen.py and component imports, with declarative style.bg color/image/gradient/opacity/transparent values and one TextView foreground child.
- Support RGB/ARGB/CSS colors, seven native image fit modes, linear directions, radial/sweep and layered/group transparency; foreground text color is configurable.
- Validate project-local images, static frames, orientation/profiles/alpha; package normalized PNGs by content hash and verify their signed payload/digests.
- Extend DEX fields, constants, arrays, object returns, typed register copies and range calls; preserve legacy DEX hashes.
- 76 host tests pass. On the author's Android API 33 phone, 25 native pixel cases passed (base, RGB/ARGB/group/transparent/image alpha, eight linear directions, radial/sweep and seven fit modes). Combined image/gradient/text rendering was visually confirmed.
- Native API 24–28 and additional devices still need separate runtime coverage. General layouts/events, remote/vector images and animation playback remain outside this first component contract.

Details: [user API/options](user_guide/screen.md), [implementation/tests](developer_guide/screen_styling.md), [runnable example](../examples/screen_style/README.md).

## 🧹 What changed in the cleanup?

The active source tree now has `compiler/` and `android/`, with ordinary root API/config/build/CLI files. Common/platform registry layers and desktop/iOS placeholders were removed. DEX container writing, method generation, instruction assembly, native screen bindings and APK ZIP packaging have separate owners.

Public `from anpyra import ...` and `pyandroid` authoring imports continue to work. Internal imports under removed common/platforms packages and compiler.dex change intentionally; use android.dex for DEX internals. This cleanup has not replaced immutable PyPI 0.1.0 files; publishing it requires a new version/tag.

## 🎯 Work still needed to complete Android

1. Record model/API, visible starter text, both score branches and lifecycle behavior; independently inspect APK/DEX.
2. Improve diagnostics, malformed-input coverage, artifact interruption behavior and instruction/register limits.
3. Add deliberate reassignment/definite initialization, stronger helper bodies and register lifetime analysis.
4. Implement native layout/child widgets, then buttons/input and typed properties.
5. Implement callbacks, persistent fields/state and lifecycle/recreation contracts.
6. Add static multi-file composition, resource/assets packaging and expanded verification.
7. Add protected release identity/import and tested upgrade/distribution workflows.

These are planned capabilities. Loops, collections, general Python imports/runtime, interactive widgets, resources and release/store signing are not implemented by the directory cleanup. See the detailed [roadmap](roadmap.md) and [component guide](developer_guide/android_components.md).
