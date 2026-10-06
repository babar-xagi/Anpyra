"""Screen authoring API and validated, source-configurable background values."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import PurePosixPath

from PIL import ImageColor


class StyleError(ValueError):
    """A declared screen style is invalid."""


def unit_interval(value, name: str) -> float:
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
        raise StyleError(f"{name} must be a finite number between 0 and 1")
    return float(value)


def alpha_byte(opacity: float) -> int:
    return math.floor(unit_interval(opacity, "opacity") * 255 + 0.5)


def parse_color(value: str | int) -> int:
    """Return unsigned Android ARGB; hex alpha is first, rgba() alpha is last."""
    if type(value) is int:
        if -0x80000000 <= value <= 0xFFFFFFFF:
            return value & 0xFFFFFFFF
        raise StyleError("integer colors must fit 32-bit ARGB")
    if not isinstance(value, str) or not value.strip():
        raise StyleError("color must be a color string or 32-bit ARGB integer")
    color = value.strip().lower()
    if color == "transparent":
        return 0
    if color.startswith("#"):
        digits = color[1:]
        if len(digits) not in (3, 4, 6, 8) or not re.fullmatch(r"[0-9a-f]+", digits):
            raise StyleError("hex colors use #RGB, #ARGB, #RRGGBB or #AARRGGBB")
        if len(digits) in (3, 4):
            digits = "".join(char * 2 for char in digits)
        if len(digits) == 6:
            digits = "ff" + digits
        return int(digits, 16)
    rgba = re.fullmatch(r"rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([0-9.]+)\s*\)", color)
    if rgba:
        red, green, blue = (int(rgba[index]) for index in (1, 2, 3))
        if max(red, green, blue) > 255:
            raise StyleError("rgba color channels must be between 0 and 255")
        try:
            alpha = alpha_byte(float(rgba[4]))
        except ValueError as exc:
            raise StyleError("rgba alpha must be between 0 and 1") from exc
    else:
        try:
            red, green, blue, alpha = ImageColor.getcolor(color, "RGBA")
        except (ValueError, TypeError) as exc:
            raise StyleError(f"invalid color: {value!r}") from exc
    return (alpha << 24) | (red << 16) | (green << 8) | blue


FIT_MODES = {"cover", "contain", "fill", "center", "inside", "fit_start", "fit_end"}
FIT_ALIASES = {"stretch": "fill", "fit": "contain", "fit_center": "contain", "center_crop": "cover"}
DIRECTIONS = {
    "top_bottom",
    "bottom_top",
    "left_right",
    "right_left",
    "tl_br",
    "tr_bl",
    "bl_tr",
    "br_tl",
}


@dataclass(frozen=True)
class Image:
    path: str
    fit: str = "cover"
    opacity: float = 1.0
    frame: int = 0

    def __post_init__(self):
        if not isinstance(self.path, str) or not self.path or "\x00" in self.path:
            raise StyleError("image path must be a nonempty project-relative path")
        path = self.path.replace("\\", "/")
        parts = PurePosixPath(path)
        if parts.is_absolute() or ".." in parts.parts or ":" in path:
            raise StyleError(
                "image path must stay inside the project; URLs/absolute paths are unsupported"
            )
        if not isinstance(self.fit, str):
            raise StyleError("image fit must be a supported mode")
        fit = FIT_ALIASES.get(self.fit.lower(), self.fit.lower())
        if fit not in FIT_MODES:
            raise StyleError(
                f"unsupported image fit {self.fit!r}; choose {', '.join(sorted(FIT_MODES))}"
            )
        if type(self.frame) is not int or self.frame < 0:
            raise StyleError("image frame must be a nonnegative integer")
        object.__setattr__(self, "path", path)
        object.__setattr__(self, "fit", fit)
        object.__setattr__(self, "opacity", unit_interval(self.opacity, "image opacity"))


@dataclass(frozen=True)
class Gradient:
    colors: tuple[str | int, ...]
    direction: str = "top_bottom"
    kind: str = "linear"
    radius: float | None = None
    center: tuple[float, float] = (0.5, 0.5)

    def __post_init__(self):
        if not isinstance(self.colors, (list, tuple)) or not 2 <= len(self.colors) <= 256:
            raise StyleError("gradient needs 2–256 color stops")
        for color in self.colors:
            parse_color(color)
        if not isinstance(self.direction, str) or self.direction not in DIRECTIONS:
            raise StyleError(f"unsupported gradient direction {self.direction!r}")
        if not isinstance(self.kind, str) or self.kind not in {"linear", "radial", "sweep"}:
            raise StyleError("gradient kind must be linear, radial or sweep")
        if self.kind == "radial":
            if (
                type(self.radius) not in (int, float)
                or not math.isfinite(self.radius)
                or not 0 < self.radius <= 3.4028235e38
            ):
                raise StyleError(
                    "radial gradient requires a positive finite float32 radius in pixels"
                )
        elif self.radius is not None:
            raise StyleError("gradient radius applies only to radial gradients")
        if not isinstance(self.center, (tuple, list)) or len(self.center) != 2:
            raise StyleError("gradient center must contain two fractions")
        center = tuple(unit_interval(value, "gradient center") for value in self.center)
        if self.kind == "linear" and center != (0.5, 0.5):
            raise StyleError("custom gradient center applies to radial/sweep gradients")
        object.__setattr__(self, "colors", tuple(self.colors))
        object.__setattr__(self, "center", center)


@dataclass(frozen=True)
class Background:
    color: str | int | None = None
    image: Image | None = None
    gradient: Gradient | None = None
    opacity: float = 1.0
    transparent: bool = False

    def __post_init__(self):
        if self.color is not None:
            parse_color(self.color)
        if self.image is not None and not isinstance(self.image, Image):
            raise StyleError("background image must be Image(...) or None")
        if self.gradient is not None and not isinstance(self.gradient, Gradient):
            raise StyleError("background gradient must be Gradient(...) or None")
        if type(self.transparent) is not bool:
            raise StyleError("background transparent must be bool")
        object.__setattr__(self, "opacity", unit_interval(self.opacity, "background opacity"))

    @property
    def effective_opacity(self) -> float:
        return 0.0 if self.transparent else self.opacity


class BackgroundProperties:
    color: str | int | None
    image: Image | str | None
    gradient: Gradient | tuple | list | None
    opacity: float
    transparent: bool
    fit: str
    image_opacity: float
    frame: int


class ScreenStyle:
    bg: BackgroundProperties | Background


class Screen:
    style: ScreenStyle
    bg: BackgroundProperties | Background

    def __init__(self, context) -> None:
        raise RuntimeError("Build this app with Anpyra; Screen runs on Android.")

    def set_content(self, view) -> None:
        raise RuntimeError("Build this app with Anpyra; Screen runs on Android.")
