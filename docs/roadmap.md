# 🗺️ Anpyra Roadmap and Development Phases

**Snapshot:** October 4, 2026 · **Current package:** v0.1.0 alpha · **Direction:** Python source → typed IR → native DEX → signed APK.

**Future direction:** native mobile and desktop applications. Android is the only implemented target; iOS, Windows, macOS and Linux have reserved folders. Web is outside scope. This organization does not change the immediate priority of Android validation and features.

This roadmap records completed work, validation gaps and proposed future phases. Future phases describe intended work, not available APIs or promised release dates. Priorities can change with evidence; phases that depend on new language/runtime semantics must not be marked complete from documentation alone.

## 🧭 Status and evidence

| Marker | Meaning |
| --- | --- |
| ✅ Completed | Deliverable exists with the stated evidence |
| 🧪 Validation pending | Implementation exists but a required check is outstanding |
| 📋 Planned | Work has not been implemented |

The original experiments were reported successful on a phone by the author. The refactored framework passed host tests, example builds and wheel installation/build checks. Its **own real-device acceptance and independent binary verification are still pending**. Do not combine these into a broader device-support claim.

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

### 🌍 Native platform foundation

- [x] Common source analysis/IR, application metadata and project path code separated from target packaging.
- [x] Android SDK configuration, authoring API, DEX, manifest, APK, signing and verification owned by the Android backend.
- [x] Separate native mobile Android/iOS and desktop Windows/macOS/Linux directories.
- [x] Explicit available/planned target registry, `targets` listing and build/check target selection.
- [x] Historical imports retained through compatibility modules.
- [x] Boundary/dispatch/compatibility checks added; current suite contains 48 tests.
- [ ] Generalize the current Android-shaped source/UI/IR/register contracts for another backend.
- [ ] Implement, package and runtime-validate any additional native target.

## 🧱 Phase overview

| Phase | Focus | Status | Depends on |
| --- | --- | --- | --- |
| 0 | Experimental proof 001–008 | ✅ Author-reported device success | — |
| 1 | Unified v0.1 compiler/framework | ✅ Host baseline complete | 0 |
| 2 | Documentation and contributor organization | ✅ Repository work implemented | 1 |
| 3 | Validation, diagnostics and binary hardening | 🧪 Device/independent checks pending; further work planned | 1–2 |
| 4 | Language semantics and register model | 📋 Planned | 3 |
| 5 | Native layouts and widget surface | 📋 Planned | 3–4 |
| 6 | Events, application state and lifecycle | 📋 Planned | 4–5 |
| 7 | Modules, classes and multiple Activities | 📋 Planned | 4, lifecycle contracts |
| 8 | Assets/resources and package expansion | 📋 Planned | 5, 7 where required |
| 9 | Release identity and distribution | 📋 Planned | Validated runtime/package contracts |
| 10 | Tooling, platform coverage and ecosystem | 📋 Planned, incremental | Relevant earlier phases |
| 11 | Additional native mobile/desktop backends | 📋 Planned; folder/dispatch foundation exists | Proven shared semantics and target-specific toolchains |

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

- [ ] Run the [framework device checklist](developer_guide/testing.md) on the author's phone and record model/API/commit/fingerprints/results.
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

- [ ] Add asset selection/path validation and deterministic packaging.
- [ ] Design resource IDs/tables and image/string/icon references where needed.
- [ ] Expand manifest metadata such as permissions/theme only with tests and a clear model.
- [ ] Update APK verification to the intended expanded profile.
- [ ] Evaluate compression/alignment, larger ZIPs and multi-DEX constraints as actual needs arise.

**Dependencies:** widget/application features using these resources and a documented package contract.

**Exit criteria:** a resource-using app displays packaged content correctly, missing/unsafe paths fail, retained signing works for updates, and independent Android package inspection accepts the new artifacts.

## 9️⃣ Phase 9 — Release signing and distribution

**Outcome:** make distribution deliberate and reproducible.

- [ ] Explicit debug/release modes and signer selection/import.
- [ ] Protected release key handling, identity backups and actionable errors.
- [ ] Package/version upgrade checks and documented signing compatibility.
- [ ] Evaluate v3/key rotation and older-device support only if requirements justify them.
- [ ] Build verified source/wheel release artifacts and define versioning policy.
- [ ] Establish PyPI publication and versioned documentation when maintainers choose to publish.
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

## 🌍 Phase 11 — Additional native platforms

**Outcome:** implement genuine native mobile/desktop targets after establishing reusable application semantics. Directory creation is a foundation, not completion of this phase. No fixed target delivery order or dates are promised.

- [x] Reserve `platforms/mobile/ios/` and `platforms/desktop/{windows,macos,linux}/`; keep Android code isolated.
- [x] Add target inventory/dispatch with honest availability and early rejection for unavailable targets.
- [ ] Generalize lifecycle/widget operations and Android-specific descriptor/register assumptions in the shared front end/IR.
- [ ] Define platform capability checks, target configuration and backend/result contracts around an actual second implementation.
- [ ] Choose a first additional native platform based on real host/toolchain and UI requirements.
- [ ] Implement its native code generation, UI bindings, packaging and applicable signing/distribution workflow inside its target folder.
- [ ] Add target-specific examples, native runtime acceptance, isolated package checks and CI where feasible.
- [ ] Extend subsequent native targets independently while preserving Android behavior.

**Dependencies:** validated Android baseline; defined shared language/UI behavior; researched target-native runtime, format, host and toolchain constraints. Android's Python-only build does not prove the same dependency model for iOS or desktop.

**Exit criteria per target:** real native artifacts build, supported source behavior is documented, an example runs correctly on that platform, failures are tested and CLI status reflects proven capability. Web remains outside target scope.

Implementation details: [native platform architecture](developer_guide/native_platforms.md).

## 🎯 Next practical milestone

First complete framework acceptance and independent inspection of hello/score. Then build a **small counter app** through phases 4–6: layout, label, button, click callback and typed mutable state. This is a proposal with dependencies, not a buildable v0.1 example.

## 🤝 How to keep the roadmap useful

Choose one deliverable per issue/review where practical. Record implementation, tests, docs and runtime evidence. Mark a checkbox only after its contract is met. If scope changes, update dependencies and limits before changing APIs. Keep successful historical examples working at each step.

Further reading: [developer guide](developer_guide/README.md), [extension workflow](developer_guide/extending.md), [release checklist](developer_guide/release.md), [changelog](../CHANGELOG.md).
