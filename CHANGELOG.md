# 📝 Changelog

This file records user-visible milestones. Planned work belongs in the [roadmap](docs/roadmap.md), not as completed release notes.

## 📦 0.1.4 — October 6, 2026

- Add Column/Row/ScrollView, styled TextInput and a scoped ChatSession controller with runtime key entry.
- Generate native listeners, fields, worker/delivery classes, HTTPS/JSON requests, complete response history and request locking.
- Add conditional INTERNET permission, password/state handling, correctly sized scrolling content and source parent/cycle diagnostics.
- Add independent multi-class/exception metadata tests, reproducible signed chat builds, controlled phone checks and detailed user/developer guides.
- Keep Unicode source/debug output usable in legacy-encoded Windows pipes, with a regression test for the CI failure.
- Controlled native chat acceptance passed; a live AI reply remains unverified because the test key returned exhausted quota.

## 📦 0.1.3 — October 6, 2026

### 📦 Publication and upgrades

- Publish wheel/source through [Trusted Publishing](https://github.com/babar-xagi/Anpyra/actions/runs/37539219407); public archive hashes match checked CI artifacts.
- Verify fresh public installation and pip/uv upgrades from 0.1.2, preserving existing configuration, signing identity and starter APK bytes.
- Build/verify the new Button/state/ripple/icon example from each public package environment and confirm reproducible output.

### 🟦 Native Button design

- Add canonical Button/ButtonStyle/ButtonState/Border/Icon authoring and native android.widget.Button construction.
- Reuse typography and local fonts; add explicit colors/gradients, dp border/radii, state backgrounds/text, ripple, placement/margins, elevation and raster icons.
- Preserve native unspecified text gravity, explicit padding after background replacement, old imports and legacy DEX output.
- Add enabled-state branches, parent/asset checks, 16 focused host tests, original icon example and opt-in device checks.
- Pass 111 host tests, local package checks and 20 recorded native Button cases on Android API 33, including press/release, disabled state, shapes, gradients, icons, ripple and focus.
- Button callbacks/actions remain a separate future phase; previous published versions remain immutable.

## 📦 0.1.2 — October 6, 2026

### 📦 Publication and upgrades

- Publish the wheel/source through [Trusted Publishing](https://github.com/babar-xagi/Anpyra/actions/runs/37528963281); public file hashes match checked CI artifacts.
- Verify fresh PyPI installation and pip/uv upgrades from 0.1.1, retaining app config, signing identity and starter APK bytes.
- Build/verify typography/local-font APKs from each public installation and confirm reproducible rebuilds.

### 🔤 Native TextView typography

- Extract the canonical TextView class into components/textview.py with compatible public imports.
- Add ordered text styles, native dp/sp conversion, configurable fonts/size/colors/gravity/padding/dimensions/spacing/overflow/decorations/shadows and accessibility.
- Package validated standalone local TTF/OTF fonts with signed content hashes; preserve existing legacy DEX output.
- Add runnable typography example, original demonstration fonts, detailed ownership/user docs, 19 host tests and opt-in device rendering checks.
- Pass 95 host tests and 30 recorded typography device cases on Android API 33; visually confirm native selection toolbar and combined overflow/shadow rendering. Additional Android versions remain unverified.

## 📦 0.1.1 — October 6, 2026

### 🎨 Native Screen styling

- Add components/screen.py with Screen, Background, Image and Gradient; compile declarative bg properties and native text color.
- Support arbitrary declared ARGB/CSS colors, group transparency, seven image fits, static frame selection and linear/radial/sweep gradients.
- Normalize local image assets with EXIF/ICC/alpha handling and metadata stripping; sign and validate digest-named PNG entries.
- Extend DEX for native enum/static fields, arrays, full constants, object results and safe wide invocations; preserve legacy DEX output.
- Add runnable source example, option/implementation docs, opt-in device test script and 76 host tests.
- Verify 25 real-device pixel cases on Android API 33 plus combined image/gradient/text rendering.
- Include the Screen APIs in the 0.1.1 wheel; Pillow installs automatically as a dependency.

### 🧹 Android-only component cleanup

- Remove common/platform registry packages and future desktop/iOS placeholders.
- Use canonical compiler/ and android/ modules with root API/config/build/CLI files.
- Separate native screen bindings, method generation, Dalvik assembly, DEX records/encoding, file writing and APK packaging.
- Keep public app/legacy authoring imports; remove internal forwarding modules so Android DEX has one canonical file.
- Preserve exact experiment DEX output and signed example APK bytes; current suite has 55 checks.
- Add detailed component/source ownership and implementation progress; author confirmed successful starter APK phone installation.
- Release the Android-only layout in 0.1.1; immutable 0.1.0 package files and tag are retained.

### 🔄 Installation and upgrades

- Publish wheel/source through [Trusted Publishing](https://github.com/babar-xagi/Anpyra/actions/runs/37511994040); verify public archive hashes against CI artifacts and a fresh PyPI installation.
- Verify separate pip/uv upgrades from 0.1.0, preserving app config, signing identity and starter APK bytes; build/verify the new Screen image/gradient example after each upgrade.
- Document direct pip/uv installation, exact 0.1.1 and latest-release upgrades, interpreter selection and rebuilding existing apps.
- Keep existing app configuration and debug signing state during package upgrades; app versions remain independent of the compiler version.

## 📦 0.1.0 — October 6, 2026 (PyPI release; foundation built October 4)

### 📦 Python package publishing

- Manual tagged TestPyPI/PyPI workflow with reusable CI, version guards, archive/README checks and isolated wheel build smoke test.
- Separate least-privilege publishing job using Trusted Publishing and checked build artifacts.
- Package classifiers/project links and a dedicated PyPI-compatible README.
- Read-only release validator, focused rejection tests and complete account/tag/command guide.
- Production trusted publisher configured; release 0.1.0 published and verified on October 6, 2026.

### 🌍 Native platform organization

- Shared source analysis/IR, identity metadata and project paths moved to `common/`.
- Android authoring/config, DEX, manifest, APK packaging/signing/verification moved to `platforms/mobile/android/`.
- Reserved native iOS and Windows/macOS/Linux backend packages; no additional target implemented.
- Native registry, `targets` command and `build`/`check --target`; Android remains the default and planned targets fail before writes.
- Historical imports preserved through forwarding modules; seven additional boundary/dispatch/compatibility checks.
- Updated ownership guides, source reference and future native backend phase. Web is outside target scope.

### 📚 Documentation

- Recommend uv for installation, retain pip alternatives and document activation-free setup and wheel workflows.
- Clarify that Android builds use Python dependencies without Java/JDK, Kotlin, Android SDK/NDK or Android Studio; adb remains optional.
- Document emoji prefixes for every new commit subject.

- Modern project README with navigation, badges, pipeline, supported feature summary and alpha limits.
- Detailed user/developer guides, file/function map, debugging and extension workflows.
- Full phase roadmap distinguishing implemented work from pending device validation and future features.
- Contribution, issue/PR templates and walkthroughs for both examples.

### 🗂️ Organization and checks

- Existing tests grouped into unit/integration/regression without changing public framework module paths.
- Historical fixtures retained; discovery markers added for grouped tests.
- Documentation link/title/Python-example checks and CI integration.
- Source-distribution inclusion of documentation, examples, tests and repository maintenance files.

### 🧱 Framework foundation
- Published wheel and source archive through GitHub Trusted Publishing; verified public PyPI installation and a fresh Android build.
- Unified the PyAndroid 001–008 work around the cumulative experiment 008 compiler.
- Added installable package, typed authoring imports, project configuration and compile/build APIs.
- Added six CLI commands, example projects, JSON build report and v2 APK verification.
- Retained per-project debug signing identity and deterministic package metadata.
- Added 41 host tests, Ruff checks and Windows/Linux CI configuration.
- Built/verified both examples and tested isolated wheel installation/new-app build.

The baseline is alpha. Original experiment device success was reported by the author; framework-specific phone acceptance and independent binary inspection remain pending. There is no full Python runtime, general Android binding surface, release identity workflow or publishing service in this version.
