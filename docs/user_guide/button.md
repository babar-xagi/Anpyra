# 🟦 Button Design and Native States

Button is an **unreleased source component** after PyPI 0.1.2. Install an editable checkout (`uv pip install -e .`) to try it. It compiles to `android.widget.Button`, inherits TextView typography and supports native press feedback. Published 0.1.2 does not contain this component yet.

## ✨ Create a styled button

```python
from anpyra import Activity
from anpyra.components import Button, Border


class MainActivity(Activity):
    def on_create(self, state):
        button = Button(self, text="Continue")
        button.style.color = "white"
        button.style.size = 18
        button.style.all_caps = False
        button.style.bg.color = "#2563eb"
        button.style.corner_radius = 16
        button.style.border = Border("#93c5fd", width=2)
        button.style.padding = (12, 20)
        button.style.width = 260
        button.style.height = 64
        button.style.placement = "center"
        button.style.pressed.bg.color = "#1e40af"
        button.style.ripple_color = "#50ffffff"
        self.set_content_view(button)
```

Button can be the Activity content directly or the single child of `Screen.set_content(button)`. Configure design before attachment. A child cannot be attached to two parents. Existing TextView imports and APIs remain compatible.

## 🔤 Text, sizing and geometry

Button inherits [TextView styling](textview.md): content, colors, sp size, system/local fonts, bold/italic, dp padding/dimensions, letter/line spacing, wrapping/ellipsis, decorations, text shadow, opacity, direction, accessibility and keep-screen-on behavior. Use `.text`, `text=`, `set_text` or initialized string locals.

`alignment` and `vertical_alignment` control text **inside** the button. Changing one axis preserves the native theme's other axis until you declare it. `placement` controls the **button itself** in its FrameLayout parent.

| Property | Value | Behavior |
| --- | --- | --- |
| `placement` | `top_start`, `top_center`, `top_end`, `center_start`, `center`, `center_end`, `bottom_start`, `bottom_center`, `bottom_end` | Native FrameLayout gravity; start/end follow layout direction |
| `margin` | dp, `(vertical, horizontal)`, `(top, right, bottom, left)` | Native nonnegative margins outside the button |
| `min_width`, `min_height` | Nonnegative dp | Native text-view minimum dimensions |
| `elevation` | Nonnegative dp | Native surface elevation; explicit elevation clears the theme state animator so it does not override your value |
| `enabled`, `clickable`, `focusable` | Boolean | Native interaction flags |
| `icon_gap` | Nonnegative dp | Space between compound icon and text |

Padding/margins and sizes use the device's actual density at runtime. Declaring placement or margins creates native FrameLayout layout parameters; undeclared width/height become `wrap_content`. Explicit dimensions are kept. Native elevation shadows depend on Android lighting, drawable outline and parent clipping; `shadow=Shadow(...)` affects the text rather than the surface.

Without custom background declarations, Android's themed background/feedback remains in place. Theme defaults such as all-caps, minimum sizes and padding can vary; declare the values you need.

## 🎨 Backgrounds, borders and corners

```python
button.style.bg.color = "#123456"
button.style.corner_radius = (16, 4, 12, 0)
button.style.border = Border("white", width=2)
button.style.bg.opacity = 0.8
```

Corner tuples are top-left, top-right, bottom-right, bottom-left, in dp. A single number applies to all corners. `radius` is an alias for `corner_radius`. Border widths use dp and are rounded to pixels; zero disables the stroke.

An outline button uses `bg.color="transparent"` plus a border. `bg.opacity` applies to the whole background drawable, including its border. `bg.transparent=True` makes that drawable fully transparent; inherited `style.opacity` applies to the entire button, including text and icons.

Custom corners, borders, state backgrounds and ripple require an explicit normal fill: `bg.color`, `bg.gradient` or `bg.transparent`. Anpyra does not guess a theme/application color. Set `border=Border(...)` or `border.color` before setting `border.width`.

```python
button.style.bg.gradient = Gradient(
    ["#2563eb", "#7c3aed"], direction="left_right"
)
```

Import `Gradient` first. Existing linear directions and radial/sweep gradient options are supported; radial radius retains the [Screen gradient](screen.md) pixel-unit contract. Color and gradient are alternative fills: assigning a non-None color clears the gradient, and assigning a non-None gradient clears the color. A complete `Background` containing both fails explicitly. `background_color` is an alias for `bg.color` on Button. Background images are not implemented; use a compound Icon for a raster image.

## 👆 Pressed, disabled, focused and hovered design

```python
button.style.pressed.bg.color = "#1e40af"
button.style.pressed.color = "#ffff00"
button.style.disabled.bg.color = "#334155"
button.style.disabled.color = "#94a3b8"
button.style.focused.border = Border("#fbbf24", width=3)
button.style.hovered.bg.color = "#3b82f6"
```

Each state accepts label `color`, `bg` properties and `border`. Native selector priority is disabled, pressed, focused, hovered, then normal. Undeclared state label colors are queried from the button's existing ColorStateList. State backgrounds without a fill inherit the normal fill; their declared opacity/transparent settings still apply. Undeclared state borders inherit the normal border.

You can use value declarations:

```python
button.style.disabled = ButtonState(
    color="#94a3b8", bg=Background(color="#334155")
)
button.style.enabled = False
```

Import `ButtonState` and `Background`. Style declarations are static and outside branches. `set_enabled(True/False)` or `set_enabled(initialized_bool_local)` also works inside supported branches. Disabled native Buttons reject presses. Focus normally comes from keyboard/navigation and hover from pointer devices; these are separate from touch press.

## 💧 Native ripple

```python
button.style.ripple_color = "#50ffffff"
```

An explicit ripple wraps your custom state background with Android RippleDrawable and an opaque mask matching your corner geometry. Alpha in the color controls the overlay. Set `ripple_color=None` to omit it before attachment. A custom fill has no added ripple unless declared; explicit pressed backgrounds still provide press feedback.

Native callbacks/actions are a separate future phase. Button press states, selection of its drawables and ripple work now; binding a Python `on_click` handler is not implemented and fails with a compiler diagnostic. Button text selection is deliberately unsupported because it conflicts with button interaction; use TextView for selectable text.

## 🖼️ Icons

```python
button.style.icon = Icon(
    "assets/arrow.png",
    size=(24, 24),
    position="end",
    fit="contain",
    tint="white",
    opacity=1,
)
button.style.icon_gap = 12
```

Import `Icon`. Size is positive dp or a `(width_dp, height_dp)` pair. Positions are `start`, `end`, `top`, `bottom`. Start/end use native relative compound drawables and follow layout direction. `contain` preserves the whole image with transparent letterboxing; `cover` crops to the requested aspect; `fill` stretches. Tint is optional; no tint preserves source colors. Icon opacity multiplies intrinsic image alpha.

Raster paths are local to the project root. Image limits, EXIF/ICC normalization, metadata stripping and format constraints are shared with Screen. Animated raster files use their first frame; SVG/remote images and animated icons are not supported. Normalized PNG pixels preserve alpha; resampling can round RGB values by one due to premultiplied-alpha interpolation. Native drawable bounds implement the final dp size without depending on the bitmap's density metadata. Assets are included only when referenced, signed and digest-verified. Missing/corrupt icons fail before new signing state/output is created.

## 🧩 Complete style declaration

```python
button.style = ButtonStyle(
    color="white",
    size=18,
    all_caps=False,
    bg=Background(color="#2563eb"),
    corner_radius=16,
    border=Border("#93c5fd", width=2),
    pressed=ButtonState(bg=Background(color="#1e40af")),
    ripple_color="#50ffffff",
    width=260,
    height=64,
    placement="center",
)
```

Import each factory. `Button(self, text="Continue", style=ButtonStyle(...))` and `set_style(...)` use the same path. A TextStyle value is also accepted for shared typography. Unspecified fields preserve previous declarations/native defaults. Unsupported options fail rather than silently drawing a substitute.

See the [runnable example](../../examples/button_style/README.md), [implementation map](../developer_guide/button_styling.md) and [progress evidence](../progress.md). Multi-child layouts, image backgrounds, per-state icons, arbitrary callback/lifecycle methods and store-release signing remain future work. Native APIs are described by the official [Button](https://developer.android.com/reference/android/widget/Button), [GradientDrawable](https://developer.android.com/reference/android/graphics/drawable/GradientDrawable), [StateListDrawable](https://developer.android.com/reference/android/graphics/drawable/StateListDrawable) and [RippleDrawable](https://developer.android.com/reference/android/graphics/drawable/RippleDrawable) references.
