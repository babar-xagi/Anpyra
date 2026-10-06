# 🔤 TextView Styling and Typography

The expanded TextView component is an **unreleased source feature** after 0.1.1. Use an editable checkout installation (`uv pip install -e .`) to try it. PyPI 0.1.1 includes the original TextView and Screen APIs, but does not include these new typography properties.

TextView is the native Android text widget. Its public implementation lives in `components/textview.py`. Existing `from anpyra import TextView` and `from pyandroid import TextView` imports stay compatible; component imports are also available.

## ✨ A styled title

```python
from anpyra import Activity
from anpyra.components import TextView, Font, Shadow


class MainActivity(Activity):
    def on_create(self, state):
        title = TextView(self, text="Welcome to Anpyra")
        title.style.color = "#663399"
        title.style.size = 28
        title.style.font = Font(family="sans-serif", bold=True)
        title.style.alignment = "center"
        title.style.vertical_alignment = "center"
        title.style.padding = (16, 24)
        title.style.width = "match_parent"
        title.style.height = "match_parent"
        title.style.shadow = Shadow("#40000000", radius=1, dx=0, dy=2)
        self.set_content_view(title)
```

A title, heading, caption or paragraph is a TextView with the text and styles you choose. There are no hidden heading presets. The Activity/action-bar title is the separate application `label` in `anpyra.toml`.

## 📝 Text content and compatible methods

These forms set the text:

```python
title = TextView(self, text="Initial title")
title.set_text("Updated title")
title.text = "Another title"
```

Text accepts a string literal or an initialized `str` local. Existing conditional `set_text` calls continue to work. Plain text and newlines are supported; HTML, spans, links and inline rich-text styles are not compiled.

For common styling, methods are available:

```python
title.set_text_color("rebeccapurple")
title.set_text_size(24)
title.set_alignment("center")
title.set_vertical_alignment("bottom")
title.set_padding(12)
title.set_font(Font(family="serif", italic=True))
title.set_style(TextStyle(color="white", size=22))
```

Import `Font`, `Shadow` and `TextStyle` before using their constructors. `set_padding` uses the same one/two/four-value order as `style.padding` below. Additional options use declarative `title.style.PROPERTY` assignments.

## 🎛️ Complete property reference

Only explicitly declared properties emit setters. Otherwise Android's existing widget/theme defaults remain in effect. Properties use literal values or initialized constant `str`, `bool` and literal-initialized `int` locals. Styling is declared outside branches; calls execute in source order.

| Property | Accepted value | Meaning |
| --- | --- | --- |
| `color` | Color string or 32-bit ARGB integer | Text foreground; same [color formats](screen.md) as Screen |
| `size` | Positive finite number | Font size in **sp**, honoring Android font scaling |
| `alignment` | `left`, `right`, `start`, `end`, `center` | Horizontal gravity inside the view; start/end follow layout direction |
| `vertical_alignment` | `top`, `center`, `bottom` | Vertical gravity inside the view |
| `padding` | Number, two values or four values | Interior spacing in **dp** |
| `font` | `Font(...)` or family string | System family/local font, bold and italic |
| `background_color` | Color | Background of this TextView; foreground color is independent |
| `opacity` | Number from 0 to 1 | Alpha for the entire TextView, including background and text |
| `width`, `height` | Nonnegative dp, `match_parent`, `wrap_content` | Native layout dimensions |
| `lines` | Positive integer | Set both minimum and maximum line counts |
| `min_lines`, `max_lines` | Positive integer | Native measurement line limits; minimum cannot exceed maximum |
| `single_line` | Boolean | Android single-line transformation/measurement |
| `ellipsize` | `start`, `middle`, `end`, or `None` | Truncate overflow; `None` clears a previous ellipsis setting |
| `letter_spacing` | Finite number, -1 to 10 | Extra character spacing in **em** |
| `line_spacing` | `(extra_dp, multiplier)` | Extra spacing plus positive line-height multiplier |
| `include_font_padding` | Boolean | Include Android's extra font ascent/descent padding |
| `all_caps` | Boolean | Android locale-aware uppercase display transformation |
| `underline`, `strikethrough` | Boolean | Change only the corresponding paint flag; preserve other flags |
| `selectable` | Boolean | Allow native text selection/copy interaction |
| `keep_screen_on` | Boolean | Keep the display awake while this view is visible; no system timeout setting change |
| `shadow` | `Shadow(color, radius=0, dx=0, dy=0)` | Text shadow, with dp radius and offsets; radius 0 clears shadow |
| `text_direction` | `inherit`, `first_strong`, `any_rtl`, `ltr`, `rtl`, `locale`, `first_strong_ltr`, `first_strong_rtl` | Native text direction heuristic; distinct from layout direction |
| `font_features` | String, such as `"'kern' 0"` | Native OpenType feature settings; effect depends on the selected font |
| `content_description` | String | Accessibility description for this widget |

Size, dimension, padding and shadow numbers are bounded to +/-1,000,000; size/dimensions/padding/radius must also satisfy their positive/nonnegative rules. This bounds native float conversion; it is not a recommended UI size. Line counts fit positive signed 32-bit integers. Line-spacing multiplier is greater than 0 and at most 100.

## 📐 Padding, dimensions and alignment

```python
title.style.padding = 12                 # all four sides
title.style.padding = (8, 20)            # vertical, horizontal
title.style.padding = (4, 8, 12, 16)     # top, right, bottom, left
title.style.width = "match_parent"
title.style.height = "wrap_content"
title.style.alignment = "end"
```

Android converts dp at runtime using the device's actual display density, rounding pixel dimensions with `Math.round`. Declaring either dimension creates native FrameLayout layout parameters; an undeclared other dimension defaults to `wrap_content`. Declare both if you need a particular result.

Alignment acts inside the TextView's bounds. A `wrap_content` view tightly fits its text, so center/right alignment may appear unchanged. Use a wider view (`match_parent` or a numeric width) to see horizontal alignment. Vertical alignment similarly needs extra height. Layout margins, child placement and multi-child layouts are separate future components.

Text direction controls bidirectional text interpretation. It does **not** change the view's layout direction: Android start/end gravity follows the device/view layout direction, which may differ from the declared text direction.

## 🔡 Fonts

System fonts:

```python
title.style.font = Font(family="serif", bold=True, italic=True)
title.style.font.family = "monospace"
title.style.font.bold = False
```

Family names are passed to Android. Available families and fallback behavior depend on the device; an unknown family may fall back. `Font()` preserves the current face and requests normal style. Bold/italic are Android style requests; Android may synthesize a face if the font has no matching variant.

Local font:

```python
title.style.font = Font(path="assets/MyFont.ttf")
title.style.font.italic = True
```

Paths are relative to the project root, even when `entry` is in a subdirectory. Fonts must be standalone `.ttf` (TrueType SFNT) or `.otf` (OpenType CFF), at most 16 MiB. Anpyra validates the table directory and decodes the font with Pillow, then preserves its bytes in a digest-named signed APK asset. Missing, invalid or escaping files fail before signing state/output creation. These formats are parsed on the host and by Android; verify your actual font on the Android versions you support.

Setting `font.family` switches away from a local path; setting `font.path` switches away from a system family. Bold/italic retain their current declared values. Font collections (`.ttc`), WOFF/WOFF2, arbitrary numeric weights, variation axes, remote/downloadable fonts and font fallback configuration are not implemented.

The [runnable typography example](../../examples/text_style/README.md) includes original demonstration TTF/OTF fonts. They use simple block outlines for testing; your app can supply its own font.

## 📄 Wrapping, lines and overflow

```python
title.style.width = 220
title.style.height = "wrap_content"
title.style.max_lines = 2
title.style.ellipsize = "end"
```

Text normally wraps to available width. Use `single_line=True` for one line and a finite width to exercise ellipsis. Android supports start/middle ellipsis for single-line text; multi-line overflow should use end ellipsis. Line limits affect measurement and are most useful with `wrap_content` height; an explicitly fixed/full-height view still follows native Android behavior.

`single_line` and `all_caps` change native transformation methods; when both are needed, set `single_line` first and `all_caps` afterward. Source order also controls later line-limit overrides. Setting `lines` resets both min/max; later individual declarations replace their respective limits.

## 🧩 A complete style value

```python
title.style = TextStyle(
    color="#123456",
    size=20,
    font=Font(family="sans-serif", bold=True),
    padding=(8, 16),
    width="match_parent",
    max_lines=2,
    ellipsize="end",
)
```

`TextStyle` is an immutable declaration containing optional properties. Fields left as `None` emit no setter; use direct `title.style.ellipsize = None` to clear ellipsis. Applying a complete style changes specified fields and preserves unspecified fields. `TextView(self, text="Title", style=TextStyle(...))` and `set_style(...)` use the same compiler path.

## 🧪 Scope and verification

This component styles one plain-text native view; it does not add a full Python runtime or a general layout system. Screen still supports one TextView foreground child. Host authoring methods raise `RuntimeError`; build the APK to see the result.

The new automated tests cover validation, imports, ordered properties, line-limit conflicts, wide calls, method-pool uniqueness, TTF/OTF packaging, reproducibility, bad-font protection and signed-payload rejection. Device results and remaining coverage gaps are recorded in [progress](../progress.md) and [developer internals](../developer_guide/textview_styling.md).

Native behavior is based on the official [TextView](https://developer.android.com/reference/android/widget/TextView), [Typeface](https://developer.android.com/reference/android/graphics/Typeface) and [dimension conversion](https://developer.android.com/reference/android/util/TypedValue#applyDimension(int,%20float,%20android.util.DisplayMetrics)) references.
