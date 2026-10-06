# 🎨 Screen Styling Implementation and Validation

This source feature adds native background styling and packaged raster images without Java/Gradle/SDK compilation. It is unreleased; published 0.1.0 remains unchanged. Public syntax is documented in the [screen guide](../user_guide/screen.md).

## 🗂️ Ownership

| File | Implemented work |
| --- | --- |
| [components/screen.py](../../src/anpyra/components/screen.py) | Screen authoring type; Background/Image/Gradient value validation; arbitrary color and opacity normalization |
| [compiler/screen_style.py](../../src/anpyra/compiler/screen_style.py) | Literal/constructor parsing and immutable background replacements, without executing app source |
| [compiler/frontend.py](../../src/anpyra/compiler/frontend.py) | Component imports, screen symbols/style state, ownership/attachment checks and text color lowering |
| [compiler/ir.py](../../src/anpyra/compiler/ir.py) | NewScreen, SetScreenContent, ApplyScreenBackground, SetTextColor |
| [android/assets.py](../../src/anpyra/android/assets.py) | Project-relative image resolution, frame/EXIF/ICC/alpha handling, metadata removal, deterministic PNG and asset report |
| [android/backgrounds.py](../../src/anpyra/android/backgrounds.py) | Native drawable/image references, enum fields, layered background hierarchy and emission |
| [android/screen.py](../../src/anpyra/android/screen.py) | FrameLayout construction/content, native text color and gated Force Dark behavior |
| [android/codegen.py](../../src/anpyra/android/codegen.py) | Rendering scratch registers and argument bank; primitive/native operation coordination |
| [android/dalvik.py](../../src/anpyra/android/dalvik.py) | Const32, arrays, static fields, object results, register copies and invoke-range |
| [android/dex.py](../../src/anpyra/android/dex.py), [dex_types.py](../../src/anpyra/android/dex_types.py) | External FieldKey references, field ID pool/header/map, derived references and asset strings |
| [android/packaging.py](../../src/anpyra/android/packaging.py), [verify.py](../../src/anpyra/android/verify.py) | Optional constrained digest-named PNG entries and signed content/PNG validation |

## 🧠 Source and IR rules

Screen styles are declarative. The front end retains immutable style state for each Screen and emits ApplyScreenBackground immediately before attachment. Style assignments after attachment, conditional style assignment, unsupported factories/keywords/properties and reparenting fail clearly. Source must import the authoring types it uses.

Image/Gradient/Background factories accept literals; initialized constant string/bool locals can be used. Ordinary app lists/floats/runtime mutation remain outside the existing language subset. Lists and float values inside style declarations are specifically parsed component data.

No fallback color/image is substituted. Hex/integer colors normalize to ARGB; opacity bounds, gradient directions/types/radius/center and fit/frame options are validated. Native identifiers/constants are Android API contracts, not fixed application style values.

## 📺 Native hierarchy

Screen creates a FrameLayout. Its foreground TextView is separate from a background FrameLayout inserted behind it. That background owns a LayerDrawable for base color plus gradient, and an ImageView above those drawable layers.

Background opacity uses the background FrameLayout's native float alpha, applying to the **composed group** while preserving foreground opacity. Image opacity uses ImageView.setImageAlpha, multiplying its intrinsic PNG alpha. A global LayerDrawable.setAlpha on individual child drawables would not produce equivalent group compositing; the separate background view avoids that error.

ImageView ScaleType fields implement cover/contain/fill/center/inside/start/end. FrameLayout.LayoutParams uses match-parent dimensions, and insertion index zero preserves layer order. AssetManager opens the packaged PNG, BitmapFactory decodes it, ImageView retains the bitmap and the input stream is closed.

GradientDrawable uses an orientation enum plus an int[] of declared colors. Linear uses native orientation; radial/sweep use native gradient type and center, with a float32 pixel radius for radial. Stops are evenly spaced; custom positions are not implemented.

Force Dark is disabled on styled view subtrees on API 29+ using a Build.VERSION.SDK_INT branch. Older supported APIs skip that call. This preserves explicit colors without changing device/system settings.

Primary API references: [GradientDrawable](https://developer.android.com/reference/android/graphics/drawable/GradientDrawable), [ImageView scale types](https://developer.android.com/reference/android/widget/ImageView.ScaleType), [Dalvik formats](https://source.android.com/docs/core/runtime/dalvik-bytecode).

## ⚙️ Register and DEX changes

Legacy apps retain their original frames and bytes. Styled apps reserve two low registers for array construction, place up to 14 source symbols in registers 2–15, then allocate seven rendering scratch registers, five invocation argument slots, and the final self/state incoming registers. This fits the supported byte-register forms while retaining four-bit registers for source comparisons/new-array.

When an invocation uses high registers, typed object/primitive move-from16 instructions copy arguments to the reserved contiguous bank and invoke-range is used. Object results immediately follow their invokes. Float style arguments use IEEE float32 bits in constant words. Full ARGB values use const32 where needed; short/small constants remain compact when encodable.

Field IDs refer to external orientation/scale enums and SDK_INT, not generated application fields. DEX collection includes field owner/type/name references and writes the field section/header/map only when needed. Method/type/prototype pools remain sorted.

## 📦 Asset contract

prepare_assets receives the project root separately from the entry source. It validates containment after resolving symlinks, checks existence/decoding/dimensions/frame, applies EXIF orientation, converts ICC profiles to sRGB where present, preserves alpha and strips metadata before encoding PNG.

The entry is assets/anpyra/SHA256.png; the DEX string passed to AssetManager omits the assets/ prefix. PNG payloads are deduplicated by digest and archived in stable order. Build reports list original relative path/frame, packaged entry, digest and dimensions.

Check performs this work in memory before DEX generation; it writes no artifacts/keys. Build validates images before signing-state creation. Missing/corrupt assets fail early and preserve previous artifacts. The verifier rejects duplicate/unknown entries, mismatched asset hashes and invalid PNG structure/dimensions. It still does not claim arbitrary APK semantic/runtime verification.

## 🧪 Automated and real-device evidence

Host tests cover color formats/invalid values, opacity, fit/path/frame/gradient rules, source lowering/errors/ownership, native fields and wide invocation words, RGBA packaging/signature, static GIF frames, common raster formats, metadata/profile behavior, no-write check and failure preservation. Legacy experiment DEX hashes remain unchanged.

On Android API 33, **25 native pixel cases passed**: base reference, arbitrary RGB, group opacity, transparency, eight linear directions, radial/sweep, seven fit modes, image opacity, layered group opacity, arbitrary ARGB alpha and intrinsic PNG alpha. Combined gradient/image/foreground text was also visually confirmed. Coverage is recorded for that device/API; API 24–28 and additional devices still need separate runtime evidence.

Reproduce the core matrix with an authorized device:

```powershell
python scripts/check_screen_device.py --serial DEVICE_ID
```

The optional script builds/installs its named test package and saves screenshots/results under build/screen-device-checks. Keep the phone unlocked and the demo open; it leaves the test app installed. Use --package and --work-dir to avoid another test identity/project. Preserve the generated signing state for updates. The script is opt-in and is not run in normal CI.

Limits: one content TextView, static styles/images, bounded raster dimensions, no remote image fetching, no animation playback or general layout/callback system. These constraints are explicit rather than silently ignored.
