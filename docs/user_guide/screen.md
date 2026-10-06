# 🎨 Screen Backgrounds, Images and Gradients

Screen styling is available in **Anpyra 0.1.1**. Install directly with `uv pip install "anpyra==0.1.2"` or `python -m pip install "anpyra==0.1.2"` in your environment. Existing 0.1.0 users should follow the [upgrade instructions](installation.md). Pillow is installed automatically.

## 🧩 Create a screen

```python
from anpyra import Activity, TextView
from anpyra.components import Screen, Gradient


class MainActivity(Activity):
    def on_create(self, state):
        screen = Screen(self)
        screen.style.bg.color = "#123456"
        screen.style.bg.gradient = Gradient(["#0f766e", "#2563eb"], direction="left_right")
        screen.style.bg.opacity = 0.8
        title = TextView(self)
        title.set_text("Styled from Python")
        title.set_text_color("white")
        screen.set_content(title)
        self.set_content_view(screen)
```

Declare styles and optional content before attaching the screen, outside conditions. A Screen can also display only its background without a TextView. `screen.bg` is a shorter alias for `screen.style.bg`.

Style values are literals or initialized constant string/bool locals. The compiler validates declarations without executing app source. They are not live bindings or event-driven property changes.

## 🌈 Color formats

| Input | Meaning |
| --- | --- |
| `"#RGB"`, `"#RRGGBB"` | Opaque RGB |
| `"#ARGB"`, `"#AARRGGBB"` | Android hex ordering: alpha first |
| `"rgba(12,34,56,0.5)"` | RGB channels 0–255; alpha 0–1 |
| `"rgb(12,34,56)"`, CSS named colors | Parsed through Pillow's color parser |
| `0x80123456` | 32-bit ARGB integer; signed equivalents also accepted |
| `"transparent"` | Zero alpha |

Colors are taken from app declarations, with no substituted palette or fallback color. Invalid values fail clearly. For example, integer `0x00ffffff` is transparent white; use `0xffffffff` or `"#ffffff"` for opaque white.

## 🖼️ Background images

Import Image and add these declarations before screen attachment:

```python
from anpyra.components import Image

screen.style.bg.image = Image("assets/photo.jpg", fit="cover", opacity=0.7)
```

Copy your image into the project. Paths are relative to its root, including when `entry` is inside a source subfolder. URLs, absolute paths, parent traversal and symlinks escaping the project are rejected.

The build decodes raster formats supported by the installed Pillow build, selects a static frame, applies EXIF orientation, converts embedded ICC profiles to sRGB where present, preserves alpha, strips metadata and writes a deterministic PNG. Common PNG/JPEG/WebP/GIF/BMP/TIFF/ICO and supported AVIF inputs work through this conversion. Vector/document formats need conversion to a raster file first.

Animated images are **static frames**, not playback. Select one with `Image("assets/animation.gif", frame=1)`. Invalid/missing frames, broken images or unavailable decoders fail at check/build. Images must be at most 4096 pixels per side and 16 million total pixels; resize larger images first.

### 📐 Fit modes

| Fit | Native behavior |
| --- | --- |
| `cover` | Fill the background area while preserving aspect ratio; crop overflow |
| `contain` | Preserve aspect ratio and fit fully, centered; background shows in gaps |
| `fill` | Stretch to the full area; aspect ratio may change |
| `center` | Center without scaling to fit; oversized content is clipped |
| `inside` | Center and shrink when necessary; smaller images are not enlarged |
| `fit_start` | Contain scaling aligned to the start |
| `fit_end` | Contain scaling aligned to the end |

`stretch` aliases fill; `fit`/`fit_center` alias contain; `center_crop` aliases cover. Native image density/geometry rules apply. You can also set `screen.bg.fit`, `screen.bg.image_opacity`, `screen.bg.frame`, or nested `screen.bg.image.fit` / `.opacity` / `.frame` after declaring the image.

## 🌅 Gradient options

Import Gradient and configure one of three native types:

```python
from anpyra.components import Gradient

screen.bg.gradient = Gradient(["red", "orange", "blue"], direction="top_bottom")
screen.bg.gradient = Gradient(["white", "#000000"], kind="radial", radius=240, center=(0.3, 0.4))
screen.bg.gradient = Gradient(["red", "blue"], kind="sweep", center=(0.5, 0.5))
```

These are alternative declarations; the last declaration replaces the earlier gradient. Use 2–256 equally spaced colors, including alpha colors. Custom stop positions are not implemented.

Linear directions: top_bottom, bottom_top, left_right, right_left, tl_br, tr_bl, bl_tr, br_tl. Radial requires a positive finite float32 radius in **pixels**. Radial/sweep centers are width/height fractions 0–1. A list/tuple assigned to `screen.bg.gradient` creates a default top-to-bottom linear gradient.

## 🫧 Opacity and composition

Background ordering is **color → gradient → image → foreground content**. An opaque image hides underlying layers; image opacity or intrinsic PNG alpha reveals them. An opaque gradient covers its base color.

`screen.bg.opacity` is 0–1 and fades the composed background as a group; foreground text stays opaque. `Image(..., opacity=...)` separately controls image alpha (quantized to Android's 0–255 image-alpha range). `screen.bg.transparent = True` hides the whole background; False restores its configured opacity. None clears color/image/gradient values.

Transparency reveals the Activity's existing window background. It does not make the Activity/system bars translucent or reveal other apps. Screen styles cover the Activity **content area**, with system bars/action bar managed by Android. On API 29+ the component disables Force Dark for its styled view subtree so explicitly declared colors are preserved.

## 📦 Whole background value

```python
from anpyra.components import Background, Gradient

screen.bg = Background(color="#102030", gradient=Gradient(["#80445566", "#00112233"]), opacity=0.6)
```

A Screen accepts one TextView content child in this first component version. General layouts/multiple children, callbacks, repeat tiling, remote images and runtime style reassignment are not implemented. Source locals/temporaries still have a 14-symbol budget; rendering scratch/argument registers are separate.

## ✅ Verified behavior

Native Android API 33 pixel checks passed for arbitrary RGB/ARGB, transparent/group opacity, all eight linear directions, radial/sweep, all seven fit modes, image opacity and intrinsic PNG alpha. Combined gradient/image/text rendering was also visually checked. This is evidence for that tested device/API; other API/device coverage remains to be recorded.

Start with the [runnable example](../../examples/screen_style/README.md). Component internals are explained in [screen styling implementation](../developer_guide/screen_styling.md).
