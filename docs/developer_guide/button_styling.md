# 🛠️ Button Design Implementation

Button is source-only after PyPI 0.1.2. It compiles to Android's actual Button subclass; Python authoring types are not a host renderer. Callback support is intentionally a separate runtime/compiler phase.

## 🗂️ File ownership and debugging

| File | Code and responsibility | Fix here for |
| --- | --- | --- |
| [components/button.py](../../src/anpyra/components/button.py) | Button, ButtonStyle, ButtonState, Border, Icon; finite units/colors/path validation and design snapshots | Authoring signatures and invalid properties |
| [compiler/button_style.py](../../src/anpyra/compiler/button_style.py) | Declarative paths, state/background switching, typography reuse, attachment snapshot and padding reapplication | Style merge/order, missing normal fill, incorrect partial updates |
| [compiler/frontend.py](../../src/anpyra/compiler/frontend.py) | Button imports/constructor, TextView subtype acceptance, enabled branches, attachment/parent checks and callback diagnostics | Source acceptance, error lines or view parenting |
| [compiler/ir.py](../../src/anpyra/compiler/ir.py) | NewButton, SetButtonProperty, ApplyButtonDesign | Missing IR traversal/data |
| [android/button.py](../../src/anpyra/android/button.py) | Native refs/fields, state arrays/colors, drawables, corners, stroke, ripple, icon bounds and layout | Runtime states/colors, missing native methods or register clobber |
| [android/icons.py](../../src/anpyra/android/icons.py) | Aspect-ratio fitting of normalized RGBA icons | Cover/contain/fill, transparency or canvas limits |
| [android/assets.py](../../src/anpyra/android/assets.py) | Shared read_image validation and icon hash/report/prepared IR | Asset paths, EXIF/ICC, output protection or packaging |
| [android/textview.py](../../src/anpyra/android/textview.py) | Shared typography; native-gravity getter/mask updates for unspecified Button axis | Text alignment or inherited font/spacing issues |
| [android/screen.py](../../src/anpyra/android/screen.py) | Native Button construction and force-dark guard | Wrong native class/constructor or declared color changes |
| [android/codegen.py](../../src/anpyra/android/codegen.py), [dex.py](../../src/anpyra/android/dex.py) | Wide frame, new emitter delegation, fields/strings and unique native pools | Outgoing args, missing references or DEX table issues |
| [android/dalvik.py](../../src/anpyra/android/dalvik.py) | iput 22c for FrameLayout.LayoutParams.gravity | Encoded field/register operand errors |

## 🧠 Compiler and subtype contract

Button extends the authoring TextView and native android.widget.Button extends TextView. Existing text/font operations therefore keep their native TextView references. Source type validation accepts Button where TextView/View content is expected, but preserves distinct Button symbols for construction and design handling.

Text styling remains ordered IR. Button backgrounds/states/icons are immutable design values collected until attachment, then emitted before the parent add/setContentView. Design updates after attachment fail; text content and enabled methods retain their supported call semantics. Partial native gravity preserves the actual theme's missing axis, rather than guessing a center/top combination.

Parent checks reject an already attached view. Screen remains a one-child container. No Python application source is executed to parse factories/assets. ButtonStyle separates inherited TextStyle fields from design and interaction fields; TextStyle validates its own declared fields so inheritance does not misclassify Button extras.

## ⚙️ Native drawables and state handling

State resources are static fields from android.R.attr, not guessed numeric resource IDs. Disabled specifications negate state_enabled with integer subtraction. Selector priority is disabled → pressed → focused → hovered → normal.

Custom background states are GradientDrawables inside StateListDrawable. Color/gradient fill, per-corner dp radii, rounded stroke width and background alpha are set explicitly. Theme background tint is cleared for custom drawables so an OEM/theme tint cannot replace caller colors. Explicit padding is replayed after background replacement because a native drawable can change view padding.

Per-state label colors use ColorStateList([[I, [I). Unspecified entries query the widget's existing ColorStateList with the corresponding native state specification and its default color. This preserves native fallback colors without inventing an application palette. Separate persistent scratch slots retain state/color arrays while temporary state values are constructed.

RippleDrawable wraps the selector with a caller color and an opaque GradientDrawable mask. The mask's RGB is irrelevant to rendering; its alpha and radii define coverage. Normal corner geometry applies to all states. Explicit elevation clears the theme StateListAnimator to prevent it overriding declared height; ordinary themed Buttons retain their animator.

## 📐 Layout, units and registers

Source symbols retain the 14-symbol limit. Button methods use the existing widened frame: v0/v1 reserved for arrays/fields, seven scratch registers, five outgoing invocation words and final self/state. Typed move/from16/invoke-range cover high registers. Glyph/text/font operations share the established emitter and asset path.

Dp uses actual DisplayMetrics and TypedValue.applyDimension; integer geometry uses Math.round. FrameLayout.LayoutParams dimensions/margins/gravity position the actual Button. The new iput encoding uses reserved low registers for the value/object operands, avoiding four-bit register overflow even with a full source-symbol budget.

## 🖼️ Icon lifecycle

read_image shares Screen's validation, first-frame selection, orientation/profile/alpha handling and metadata stripping. fit_icon transforms to the declared aspect ratio within the existing raster limits, using contain/cover/fill. No fixed device density or application icon size is embedded in the asset pipeline.

Normalized bytes are hashed into the same constrained signed PNG asset profile. Native code opens the asset, decodes a Bitmap, closes the stream, creates BitmapDrawable(Resources, Bitmap), and assigns dp bounds, optional tint/alpha and relative compound position. Font and icon assets can coexist. No new runtime dependency beyond Pillow/cryptography is introduced.

## 🧪 Verification and remaining work

[Unit tests](../../tests/unit/test_button.py) cover the actual native subtype, theme preservation, design validation, state paths, partial gravity, parenting/diagnostics, enabled branches, unique method pools and actual iput words. [Integration tests](../../tests/integration/test_button_assets.py) verify normalized pixel geometry/alpha, signed assets, reproducibility, no-write checks, corrupt-icon protection and font/icon coexistence.

[check_button_device.py](../../scripts/check_button_device.py) is an opt-in pixel/pointer/geometry matrix for the selected phone. It installs its own package and saves screenshots/results; it holds its test view awake while visible and releases injected pointer presses in finally blocks. It does not change system settings or bind application actions. Actual results and Android-version limits belong in [progress](../progress.md).

The actual TECNO BG7 / API 33 run passed 20 cases. Pointer screenshots use a continuous held gesture after Activity input-window readiness; launch completion alone was insufficient for reliable early touches on this device. Exact press/release and disabled colors, border/radii, four gradients, icon positions/tint, layout/margins, native gravity and ripple/focus were checked. Hover and radial/sweep fills currently have host validation/emission coverage, not separately recorded device cases. These results do not establish support for every Android API/font/theme.

Remaining work includes Python click callbacks, multi-child layouts, richer interaction/state contracts, per-state icons/image backgrounds and runtime coverage across more devices/APIs. Host validation is not evidence for every native font/theme/device.
