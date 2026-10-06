# 🗺️ Anpyra Roadmap and Development Phases

**Snapshot:** October 6, 2026 · **Current package:** v0.1.2 alpha · **Direction:** Python source → typed IR → native DEX → signed APK.

**Current direction:** complete the Android framework first. Common/platform dispatch layers and other-target placeholders have been removed from the active source. The [progress record](progress.md) lists implemented components, publication, author-confirmed phone installation and remaining evidence.

This roadmap records completed work, validation gaps and proposed future phases. Future phases describe intended work, not available APIs or promised release dates. Priorities can change with evidence; phases that depend on new language/runtime semantics must not be marked complete from documentation alone.

## 🧭 Status and evidence

| Marker | Meaning |
| --- | --- |
| ✅ Completed | Deliverable exists with the stated evidence |
| 🧪 Validation pending | Implementation exists but a required check is outstanding |
| 📋 Planned | Work has not been implemented |

The original experiments were reported successful on a phone by the author. The refactored framework passed host tests, example builds and wheel installation/build checks. The author has now confirmed starter APK installation on a phone. Exact screen output, both score branches, lifecycle checks and independent binary verification still need recorded evidence. Do not combine these into a broader device-support claim.

## ✅ What has already been achieved?

### 🧬 Experimental foundation

| Experiment | Implemented milestone | Retained in framework |
| --- | --- | --- |
| 001 | Raw DEX structure, strings/tables/checksums | DEX writer |
| 002 | Constructors and Android lifecycle methods | Method/code-item generation |
| 003 | TextView construction and visible UI calls | Authoring API, lowering and Dalvik calls |
| 004C | Binary manifest, installable APK, v2 signing | Android backend and package orchestration |
| 005 | Real source parsing, AST checks, IR | Static compiler front end |
| 006 | `str`/`int`/`bool`, symbols, types, branches | Typed locals and boolean control flow |
| 007 | Integer expressions/comparisons, nested conditions | Arithmetic and branch lowering |
| 008 | Typed helper parameters/calls/returns | Separate static DEX methods |

### 📦 Framework baseline

- [x] Installable `anpyra` package, Python 3.11+ metadata and console command.
- [x] Public Activity/TextView authoring types and compile/build APIs.
- [x] Validated project configuration and relative-path handling.
- [x] `init`, `check`, `build`, `verify`, `doctor`, optional adb `install`.
- [x] Typed source/compiler/backend modules organized by responsibility.
- [x] Persistent debug identity; partial/mismatched identity rejection.
- [x] Deterministic ZIP metadata and same-input/same-identity rebuild checks.
- [x] Staged artifact verification and preservation of earlier APK on compile failure.
- [x] JSON report with metadata, fingerprints, verification and listings.
- [x] `pyandroid` import compatibility and original source fixtures 005–008.
- [x] Hello and score projects, both built and locally verified.
- [x] Baseline suite of 41 tests and clean Ruff checks.
- [x] Wheel creation plus isolated wheel-install/new-project build smoke check.
- [x] CI configuration for Windows/Linux with Python 3.11/3.13.
- [x] v0.1 code pushed to the repository's main branch.

### 📚 Documentation and repository organization

- [x] Modern README with restrained emojis, badges, pipeline and clear alpha limits.
- [x] Separate user/developer guides and documentation indexes.
- [x] Installation/concepts/first-app/language/config/CLI/API/signing/troubleshooting/migration pages.
- [x] File-by-file source map, internals, debugging, test and extension guides.
- [x] Tests organized into unit/integration/regression plus historical fixtures.
- [x] Contribution, issue and PR templates, example/source/test navigation pages.
- [x] Local docs checks for links, emoji titles and Python/app snippets.
- [x] Source-distribution inclusion rules for project guidance and examples.

### 🧹 Android-only organization

- [x] Remove common/platform registry layers and desktop/iOS placeholders from active source.
- [x] Put AST/IR in compiler/ and native Android components in android/.
- [x] Separate DEX file writing, Dalvik assembly, method generation, screen bindings and APK ZIP packaging.
- [x] Preserve public application/experiment authoring imports while consolidating internal DEX access into android/dex.py.
- [x] Verify 55 tests and exact pre-cleanup DEX/APK output preservation.
- [x] Record published 0.1.0 wheel/source success and author-confirmed phone installation.
- [x] Verify the 0.1.1 PyPI upload, fresh installation and pip/uv upgrades from 0.1.0; original files remain immutable.

## 🧱 Phase overview

| Phase | Focus | Status | Depends on |
| --- | --- | --- | --- |
| 0 | Experimental proof 001–008 | ✅ Author-reported device success | — |
| 1 | Unified v0.1 compiler/framework | ✅ Host baseline complete | 0 |
| 2 | Documentation and contributor organization | ✅ Repository work implemented | 1 |
| 3 | Validation, diagnostics and binary hardening | 🧪 Phone installation reported; full runtime/independent checks pending | 1–2 |
| 4 | Language semantics and register model | 📋 Planned | 3 |
| 5 | Native layouts and widget surface | 📋 Planned | 3–4 |
| 6 | Events, application state and lifecycle | 📋 Planned | 4–5 |
| 7 | Modules, classes and multiple Activities | 📋 Planned | 4, lifecycle contracts |
| 8 | Assets/resources and package expansion | 📋 Planned | 5, 7 where required |
| 9 | Release identity and distribution | 📋 Planned | Validated runtime/package contracts |
| 10 | Tooling, platform coverage and ecosystem | 📋 Planned, incremental | Relevant earlier phases |

Phases are a dependency-oriented plan, not a fixed schedule. Small independent tooling improvements can happen earlier. General-purpose Python compatibility is not promised by completing this list.

## 0️⃣ Phase 0 — Experimental proof

**Outcome:** establish that a Python-written native toolchain can generate Android code and a signed package. The author supplied successful experiment archives. Their cumulative source/backend work was audited and retained through experiment 008.

**Exit evidence:** original experiment results supplied by the author. Historical source-app fixtures are preserved; original private signing material is not distributed.

## 1️⃣ Phase 1 — Unified framework foundation

**Outcome:** turn repeated experiments into one reusable package, build API and application workflow.

**Completed deliverables:** package/CLI/config, source/IR/DEX/Android modules, examples, retained debug identity, verified outputs and reports, compatibility imports, tests, wheel and CI configuration.

**Exit evidence:** 41 baseline tests, lint/format checks, both examples built/verified, and a wheel installed in isolation then used for a fresh project. Framework-specific phone validation belongs to phase 3.

## 2️⃣ Phase 2 — Documentation and contributor readiness

**Outcome:** make the repository understandable to users, the author, and future contributors.

**Deliverables:** professional landing page, user/developer navigation, supported syntax examples, every source file's responsibilities, bug-to-file map, testing/release practices, grouped tests, example walkthroughs and document checks.

**Acceptance:** local documentation links resolve, Python snippets parse, supported app snippets compile, test discovery retains the 41 original checks plus new native-architecture checks, and existing examples/public module paths continue to work. Guides describe current code rather than fictional APIs.

## 3️⃣ Phase 3 — Validation and binary hardening

**Outcome:** strengthen confidence in the existing compiler before expanding it.

- [x] Obtain author confirmation of starter APK installation on a phone (October 6, 2026).
- [ ] Run the full [framework device checklist](developer_guide/testing.md) on the author's phone and record model/API/commit/fingerprints/results.
- [ ] Verify generated APK/DEX using an independent implementation or Android tools; record discrepancies and fixes.
- [ ] Add structured diagnostics where they help: error code, source location and actionable explanation.
- [ ] Extend malformed-input/boundary tests for DEX, manifest, ZIP and signer parsing.
- [ ] Examine register limits, index ranges, branch overflow and deterministic outputs across supported environments.
- [ ] Define failure behavior for interrupted multi-artifact publication and identity creation.
- [ ] Confirm actual CI matrix outcomes; record known platform limitations.

**Dependencies:** current examples/tests and documented binary contracts.

**Exit criteria:** hello and both score branches pass recorded device checks, independent inspection results are available, identified binary defects have regression tests, and diagnostics preserve useful failure information. Host checks alone cannot complete this phase.

## 4️⃣ Phase 4 — Language semantics and register allocation

**Outcome:** support practical calculations and control flow without unclear behavior.

- [ ] Specify signed integer behavior, evaluation order, type stability and initialization rules.
- [ ] Add reassignment with definite-initialization/data-flow checks.
- [ ] Support wider constants and nested arithmetic expressions deliberately.
- [ ] Add helper local statements and conditional returns.
- [ ] Add helper-to-helper calls with signatures and call graph validation.
- [ ] Implement register lifetime analysis/reuse and necessary wider instruction formats or shuffling.
- [ ] Decide which loops, additional scalar types, and conversions are useful next; do not silently accept them early.

**Touched areas:** front end, IR, register/assembler/backend model, language docs and compiler/binary/device tests.

**Exit criteria:** multiple calculations and branch updates produce correct runtime results; uninitialized/mismatched values fail clearly; helper call frames and new instruction forms are validated in bytes and on Android. Existing fixtures continue to compile.

## 5️⃣ Phase 5 — Native layouts and widgets

**Source milestone delivered:** Screen container/background color, packaged raster image/fit/alpha and linear/radial/sweep gradients, with one TextView child. 25 API 33 native pixel cases passed. General multiple-child layouts, buttons/input and events remain planned; see [Screen guide](user_guide/screen.md).

**Outcome:** display a useful screen with more than one standalone text view.

- [ ] Design layout/child-view authoring APIs and Android method mappings.
- [ ] Add a vertical layout and multiple child text widgets as a first complete use case.
- [ ] Add Button and input-widget construction/configuration after layout contracts exist.
- [ ] Specify text/value conversion and widget property types.
- [ ] Keep API stubs, validation, IR and code generation in agreement.

**Dependencies:** stable native calls and enough register capacity for practical screens.

**Exit criteria:** a documented multi-widget layout builds, verifies and renders correctly on a recorded device; invalid parent/child/property types fail. Events are phase 6, not implied by a Button constructor.

## 6️⃣ Phase 6 — Events, mutable state and lifecycle

**Outcome:** make a small interactive app.

- [ ] Generate listener/interface bindings and callback dispatch.
- [ ] Provide safe mutable app state/fields instead of lifecycle locals for long-lived values.
- [ ] Implement a button click updating a counter and its visible text.
- [ ] Specify lifecycle/recreation/state persistence behavior.
- [ ] Add lifecycle hooks only when their source and bytecode contracts are implemented.
- [ ] Define object lifetime/reference behavior and errors for invalid callbacks.

**Dependencies:** phase 4 semantics and phase 5 UI.

**Exit criteria:** a counter/input example reacts correctly, retains state according to the documented lifecycle contract, and passes a repeated click/recreation device test without verifier/runtime errors.

## 7️⃣ Phase 7 — Modules, classes and application composition

**Outcome:** organize larger apps without executing host imports.

- [ ] Static module discovery and supported imports between compiled modules.
- [ ] Name resolution, symbol ownership and linking.
- [ ] User-defined class/field/method model where required by state/UI.
- [ ] Multiple generated classes/Activities and manifest launch/entry rules.
- [ ] Useful missing-module, duplicate-symbol and signature diagnostics.
- [ ] Extend project configuration/scaffold for the supported layout.

**Exit criteria:** a multi-file app compiles with correct method ownership; a multi-Activity example launches/navigates as documented; errors are deterministic. Document unsupported Python module semantics explicitly.

## 8️⃣ Phase 8 — Assets, resources and packaging model

**Outcome:** package application content beyond the original two-entry profile.

- [x] Add project-local Screen image selection, validation/conversion and deterministic digest-named PNG asset packaging.
- [ ] Expand asset types and resource tables deliberately beyond the Screen PNG profile.
- [ ] Design resource IDs/tables and image/string/icon references where needed.
- [ ] Expand manifest metadata such as permissions/theme only with tests and a clear model.
- [x] Update verification for signed digest-named screen PNGs; broader resource/package profiles remain future work.
- [ ] Evaluate compression/alignment, larger ZIPs and multi-DEX constraints as actual needs arise.

**Dependencies:** widget/application features using these resources and a documented package contract.

**Exit criteria:** a resource-using app displays packaged content correctly, missing/unsafe paths fail, retained signing works for updates, and independent Android package inspection accepts the new artifacts.

## 9️⃣ Phase 9 — Release signing and distribution

**Outcome:** make distribution deliberate and reproducible.

**Package-publishing foundation exists:** manual tagged TestPyPI/PyPI workflow, reused CI, archive/version/description guards, starter/Screen wheel smoke tests and [account/command guide](developer_guide/publishing.md). Production Trusted Publishing published 0.1.0 and 0.1.1 on October 6, 2026. Fresh 0.1.1 installation and pip/uv upgrades from 0.1.0 passed, including retained app identity/config/output and new Screen builds. TestPyPI rehearsal and versioned hosted documentation remain pending. This does not complete Android release-signing or store-distribution work.

- [ ] Explicit debug/release modes and signer selection/import.
- [ ] Protected release key handling, identity backups and actionable errors.
- [ ] Package/version upgrade checks and documented signing compatibility.
- [ ] Evaluate v3/key rotation and older-device support only if requirements justify them.
- [ ] Build verified source/wheel release artifacts and define versioning policy.
- [x] Publish the framework wheel/source archive to PyPI and verify a fresh index installation.
- [ ] Establish versioned hosted documentation.
- [ ] Evaluate AAB/store delivery separately; define support before advertising it.

**Exit criteria:** isolated package installation succeeds, release identity is preserved/protected, upgrade paths are tested, and platform/distribution claims have recorded evidence. Local APK v2 debug signing alone does not establish store readiness.

## 🔟 Phase 10 — Tooling and ecosystem

**Outcome:** reduce friction while keeping compiler behavior inspectable.

- [ ] Incremental rebuild/cache model tied to source/config/signing inputs.
- [ ] Better inspection tools and structured build/diagnostic output.
- [ ] Editor integrations or a language service based on supported semantics.
- [ ] More device/platform CI, reproducibility checks and performance measurements.
- [ ] Stable extension points after native API patterns are proven.
- [ ] Versioned learning examples and contributor onboarding improvements.

**Exit criteria:** each tool solves a measured task, preserves the build contract and has appropriate checks. These items can be delivered independently; no plugin system or IDE integration exists yet.

## 🎯 Next practical milestone

The starter APK has been installed successfully according to the author. Next record its visible text/lifecycle and both score branches, plus independent inspection of hello/score. Then build a **small counter app** through phases 4–6: layout, label, button, click callback and typed mutable state. This is a proposal with dependencies, not a buildable v0.1 example.

## 🤝 How to keep the roadmap useful

Choose one deliverable per issue/review where practical. Record implementation, tests, docs and runtime evidence. Mark a checkbox only after its contract is met. If scope changes, update dependencies and limits before changing APIs. Keep successful historical examples working at each step.

Further reading: [developer guide](developer_guide/README.md), [extension workflow](developer_guide/extending.md), [release checklist](developer_guide/release.md), [changelog](../CHANGELOG.md).

## 🔤 Typography implementation in 0.1.2

- [x] Separate TextView authoring and native style implementation, preserving public imports.
- [x] Implement title text, colors/size, gravity, padding/dimensions, fonts, spacing, overflow, decorations/shadows, selection and accessibility declarations.
- [x] Validate/package standalone TTF/OTF fonts and reject malformed signed assets.
- [x] Add focused tests, runnable example and user/developer file ownership guides.
- [x] Verify the 0.1.2 PyPI publication, fresh installation and separate pip/uv upgrades from 0.1.1, including typography/local-font APK builds.
- [ ] Extend rich text, arbitrary font weights/axes, automatic size and broader Android runtime coverage.
