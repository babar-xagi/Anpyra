# 🛠️ TextView Styling Implementation

Expanded typography ships in Anpyra 0.1.2. The original PyPI 0.1.1 files remain immutable. Application imports remain compatible, while TextView's canonical class now lives in its component file.

## 🗂️ Ownership and bug-fix map

| File | Implementation | Debug here for |
| --- | --- | --- |
| [components/textview.py](../../src/anpyra/components/textview.py) | TextView authoring methods; writable TextProperties/FontProperties editor interfaces; immutable Font, Shadow and TextStyle; value validation | Missing signatures, invalid option acceptance, unit/format constraints |
| [api.py](../../src/anpyra/api.py) | Activity and compatible TextView import | Root/legacy API compatibility |
| [compiler/frontend.py](../../src/anpyra/compiler/frontend.py) | Component imports, constructor keywords, text assignment/setters, style property chains, branch restrictions and constant locals | A valid source declaration fails or wrong line/source is reported |
| [compiler/screen_style.py](../../src/anpyra/compiler/screen_style.py) | Literal factory parsing shared with Screen; no app execution | Constructor keywords/literals/constant parsing |
| [compiler/text_style.py](../../src/anpyra/compiler/text_style.py) | Ordered SetTextStyle IR, combined font/gravity/dimensions and min/max line constraints | Related properties overwrite each other or line updates conflict |
| [compiler/ir.py](../../src/anpyra/compiler/ir.py) | SetTextStyle(receiver, property, value, font_asset) | Missing traversal/debug representation |
| [android/textview.py](../../src/anpyra/android/textview.py) | Native refs/strings/fields; font, gravity, paint, layout and unit-conversion emission | Device rendering, wrong native method signature or registers |
| [android/fonts.py](../../src/anpyra/android/fonts.py) | Font size/header/table bounds and Pillow outline decoding | Invalid or valid SFNT accepted/rejected incorrectly |
| [android/assets.py](../../src/anpyra/android/assets.py) | Project path containment, digest-named font assets, prepared IR and reports | Missing font, project root resolution or repeated asset handling |
| [android/dex.py](../../src/anpyra/android/dex.py) | Additional typography strings/enum fields, unique method pool | Duplicate references or missing native descriptor/string |
| [android/codegen.py](../../src/anpyra/android/codegen.py) | Wider frame for SetTextStyle and delegation to its emitter | Outgoing arguments, scratch clobber or frame limits |
| [android/packaging.py](../../src/anpyra/android/packaging.py), [verify.py](../../src/anpyra/android/verify.py) | Restricted PNG/TTF/OTF entry names; independent digest and format validation | Signed malformed assets accepted or valid payload rejected |

## 🧠 Source contract

TextView constructors accept one Activity context plus optional `text=`/`style=`. The front end supports `.text`, `.style.PROPERTY`, `.style.font.PROPERTY` and documented setter methods. Factories must be explicitly imported; unknown keywords/properties fail. Initialized literal integer locals can feed styles without widening the general Python subset to floats.

Typography declarations execute outside branches. Legacy `set_text` and `set_text_color` calls retain their branch behavior. Font/gravity/dimension properties need compile-time related-state tracking, so accepting branch-dependent updates without a merge model would be incorrect. Style setters are emitted in source order; complete declarations validate final line limits before intermediate setters.

TextStyle is a value declaration. TextProperties and FontProperties describe writable authoring syntax for editors; their host methods are not a renderer and raise RuntimeError. TextView is one actual class, re-exported by api.py, package root and pyandroid.

## ⚙️ Native emission and registers

`textview_methods` declares only references needed by operations. DEX method IDs are deduplicated before sorting: Screen background alpha and TextView alpha reference the same native method, as do component and legacy foreground-color paths.

Styled lifecycle frames reserve v0/v1 for existing array/SDK guards, source symbols from v2, seven scratch registers, five contiguous outgoing argument slots, and incoming self/state last. With 14 source symbols the frame reaches 30 registers. Typed move/from16 packing and invoke/range already exist; no new assembler opcode is required for typography. SetPadding and SetShadowLayer consume five argument words including the receiver. Every invoke result is captured immediately.

Dp conversion obtains Context Resources and actual DisplayMetrics, then calls `TypedValue.applyDimension(COMPLEX_UNIT_DIP, value, metrics)`. Integer padding/layout sizes additionally call `Math.round(float)`. Text size uses native `TextView.setTextSize(float)`, whose unit is sp. Letter spacing is em; line-spacing extra and shadow dimensions use runtime dp conversion. Metrics occupy a dedicated scratch register so sequential conversion does not overwrite previous argument values.

Dimensions allocate FrameLayout.LayoutParams and call View.setLayoutParams. Unspecified peer dimensions become wrap_content once sizing is declared. Gravity combines horizontal and vertical values, then resets View text alignment to TEXT_ALIGNMENT_GRAVITY. Absolute left/right and paragraph/layout-relative start/end follow Android behavior; do not replace them with fixed pixel offsets.

Paint decoration reads current flags and applies `or-int` for adding or `and-int` with a complemented mask for removing underline/strike bits. Other flags survive. Ellipsis uses a native TruncateAt enum field or null to clear. API 29 force-dark guards already protect declared colors; native typography setters otherwise fit the minimum API 24 contract.

## 🔡 Font lifecycle and asset contract

Font family strings go to Typeface.create(String, style); an unspecified family/path obtains the current TextView typeface, then applies a style request. Custom files use AssetManager plus Typeface.createFromAsset, followed by a normal/bold/italic/bold-italic request. A family/path switch clears the previous source while preserving declared style flags. Device family fallback and synthesized variants are native Android behavior, not guaranteed additional font files.

Standalone font validation caps data at 16 MiB, checks extension/magic, bounded unique SFNT table records, required metric/name/map tables and supported outlines, then asks Pillow/FreeType to decode/rasterize. It is a format-profile check, not independent proof of compatibility with every Android font parser. Collections and web font containers fail explicitly.

Font bytes remain unchanged and are packaged under `assets/anpyra/<sha256>.ttf` or `.otf`. IR stores the AssetManager path without `assets/`. Preparation happens before debug keys are loaded. `check` resolves/validates assets in memory without output or keys. Report records add source/kind/entry/hash/size. Packaging and verification dispatch by the constrained extension; a valid APK signature cannot hide a bad font payload or mismatched digest.

## 🧪 Automated and device checks

The [unit tests](../../tests/unit/test_textview.py) cover actual public import identity, dimensions/options/errors, constructor/text syntax, all native property refs, combined updates, source diagnostics, branch restrictions, complete line changes, method-ID uniqueness and a wide frame with padding/shadow/ellipsis.

The [integration tests](../../tests/integration/test_text_fonts.py) build real TTF/OTF APKs, assert byte-preserved packaged fonts and reproducibility, protect prior outputs on missing/corrupt fonts, check no-write validation, reject bad table bounds and independently re-sign malformed font payloads to test verifier rejection.

The complete host suite has 95 passing tests. The actual TECNO BG7 / API 33 run recorded 30 passing cases, including 15 gravity combinations, unit conversions, font formats/styles, decorations, transformations, opacity, direction and native selection focus. Combined overflow/shadow rendering and the long-press Copy/Share toolbar were visually confirmed. Clipboard copying/sharing and every OpenType feature were not independently exercised.

Run the opt-in [device script](../../scripts/check_text_device.py) with an unlocked phone:

```powershell
python scripts/check_text_device.py --serial DEVICE_ID
```

It installs its own test package, captures pixels/geometry and limited accessibility nodes for that app, and saves results/screenshots under its work directory. Its test view uses `keep_screen_on=True` while visible, plus a wake key before launch; it cannot unlock a locked phone or change system timeout settings. Normal CI does not run device commands. Preserve the test signing identity across reruns. `--resume-from CASE` can re-measure saved screenshots before resuming fresh captures; use this only for an unchanged test candidate, and retain the recorded reused-screenshot list. See [progress](../progress.md) for actual results and gaps.

Android intentionally hides click/long-click accessibility actions for selectable non-editable TextViews. The script therefore checks focusability and an actual long-press/focus response rather than those hidden flags. The Copy/Share popup is visible in the recorded screenshot. Native platform behavior is documented in [Android 13 TextView source](https://android.googlesource.com/platform/frameworks/base/+/refs/heads/android13-release/core/java/android/widget/TextView.java).

Remaining work includes rich spans, numeric/variable weights, font fallback configuration, auto-size, callbacks, general layouts, and runtime validation on more Android APIs/devices. No feature should be considered implemented only because it appears in an authoring annotation.
