"""TextView authoring and validated native typography values."""

from __future__ import annotations

import math
from dataclasses import dataclass, fields
from pathlib import PurePosixPath
from typing import TYPE_CHECKING

from .screen import StyleError, parse_color, unit_interval

if TYPE_CHECKING:
    from ..api import Activity


def number(value, name, *, minimum=None, maximum=1_000_000):
    if (
        type(value) not in (int, float)
        or not math.isfinite(value)
        or (minimum is not None and value < minimum)
        or abs(value) > maximum
    ):
        lower = f" and >= {minimum}" if minimum is not None else ""
        raise StyleError(f"{name} must be a finite number within +/-{maximum}{lower}")
    return float(value)


@dataclass(frozen=True)
class Font:
    family: str | None = None
    path: str | None = None
    bold: bool = False
    italic: bool = False

    def __post_init__(self):
        if self.family is not None and (
            not isinstance(self.family, str) or not self.family.strip() or "\x00" in self.family
        ):
            raise StyleError("font family must be a nonempty Android family name")
        if self.family is not None and self.path is not None:
            raise StyleError("font uses either a system family or a local path")
        if self.path is not None:
            if not isinstance(self.path, str) or not self.path or "\x00" in self.path:
                raise StyleError("font path must be a project-relative .ttf or .otf file")
            path = PurePosixPath(self.path.replace("\\", "/"))
            if path.is_absolute() or ".." in path.parts or ":" in str(path):
                raise StyleError("font path must stay inside the project")
            if path.suffix.lower() not in {".ttf", ".otf"}:
                raise StyleError("local fonts must be .ttf or .otf; collections are unsupported")
            object.__setattr__(self, "path", str(path))
        if type(self.bold) is not bool or type(self.italic) is not bool:
            raise StyleError("font bold and italic must be bool")

    @property
    def native_style(self):
        return int(self.bold) | (int(self.italic) << 1)


@dataclass(frozen=True)
class Shadow:
    color: str | int
    radius: float = 0
    dx: float = 0
    dy: float = 0

    def __post_init__(self):
        parse_color(self.color)
        for name in ("radius", "dx", "dy"):
            object.__setattr__(
                self,
                name,
                number(getattr(self, name), name, minimum=0 if name == "radius" else None),
            )


ALIGNMENTS = {"left", "right", "start", "end", "center"}
VERTICAL_ALIGNMENTS = {"top", "center", "bottom"}
TEXT_DIRECTIONS = {
    "inherit",
    "first_strong",
    "any_rtl",
    "ltr",
    "rtl",
    "locale",
    "first_strong_ltr",
    "first_strong_rtl",
}
BOOLEAN_PROPERTIES = {
    "keep_screen_on",
    "single_line",
    "include_font_padding",
    "all_caps",
    "underline",
    "strikethrough",
    "selectable",
}
INTEGER_PROPERTIES = {"lines", "min_lines", "max_lines"}


def validate_text_property(name, value):
    if name in {"color", "background_color"}:
        parse_color(value)
    elif name == "size":
        value = number(value, name, minimum=0)
        if value == 0:
            raise StyleError("text size must be greater than zero (sp)")
    elif name == "opacity":
        value = unit_interval(value, name)
    elif name in {"alignment", "vertical_alignment", "text_direction"}:
        choices = {
            "alignment": ALIGNMENTS,
            "vertical_alignment": VERTICAL_ALIGNMENTS,
            "text_direction": TEXT_DIRECTIONS,
        }[name]
        if not isinstance(value, str) or value not in choices:
            raise StyleError(f"{name} must be one of {', '.join(sorted(choices))}")
    elif name == "font":
        if isinstance(value, str):
            value = Font(family=value)
        if not isinstance(value, Font):
            raise StyleError("font must be Font(...) or a system family name")
    elif name == "shadow":
        if not isinstance(value, Shadow):
            raise StyleError("shadow must be Shadow(...)")
    elif name == "padding":
        if type(value) in (int, float):
            value = (value,) * 4
        elif isinstance(value, (tuple, list)) and len(value) == 2:
            value = (value[0], value[1], value[0], value[1])
        if not isinstance(value, (tuple, list)) or len(value) != 4:
            raise StyleError(
                "padding uses one number, (vertical, horizontal), or (top, right, bottom, left)"
            )
        value = tuple(number(item, "padding", minimum=0) for item in value)
    elif name in {"width", "height"}:
        if value not in ("match_parent", "wrap_content"):
            value = number(value, name, minimum=0)
    elif name in BOOLEAN_PROPERTIES:
        if type(value) is not bool:
            raise StyleError(f"{name} must be bool")
    elif name in INTEGER_PROPERTIES:
        if type(value) is not int or not 1 <= value <= 0x7FFFFFFF:
            raise StyleError(f"{name} must be an integer between 1 and 2147483647")
    elif name == "ellipsize":
        if value not in (None, "start", "middle", "end"):
            raise StyleError("ellipsize must be None, start, middle or end; marquee is unsupported")
    elif name == "letter_spacing":
        value = number(value, name, minimum=-1, maximum=10)
    elif name == "line_spacing":
        if not isinstance(value, (list, tuple)) or len(value) != 2:
            raise StyleError("line_spacing uses (extra_dp, multiplier)")
        value = (number(value[0], name), number(value[1], name, minimum=0, maximum=100))
        if value[1] == 0:
            raise StyleError("line spacing multiplier must be greater than zero")
    elif name in {"font_features", "content_description"}:
        if not isinstance(value, str) or "\x00" in value:
            raise StyleError(f"{name} must be a string without NUL")
    else:
        raise StyleError(f"unsupported TextView style property {name!r}")
    return value


@dataclass(frozen=True)
class TextStyle:
    keep_screen_on: bool | None = None
    color: str | int | None = None
    size: float | None = None
    alignment: str | None = None
    vertical_alignment: str | None = None
    padding: float | tuple | None = None
    font: Font | str | None = None
    background_color: str | int | None = None
    opacity: float | None = None
    width: float | str | None = None
    height: float | str | None = None
    lines: int | None = None
    min_lines: int | None = None
    max_lines: int | None = None
    single_line: bool | None = None
    ellipsize: str | None = None
    letter_spacing: float | None = None
    line_spacing: tuple | None = None
    include_font_padding: bool | None = None
    all_caps: bool | None = None
    underline: bool | None = None
    strikethrough: bool | None = None
    selectable: bool | None = None
    shadow: Shadow | None = None
    text_direction: str | None = None
    font_features: str | None = None
    content_description: str | None = None

    def __post_init__(self):
        for field in fields(TextStyle):
            value = getattr(self, field.name)
            if value is not None:
                object.__setattr__(self, field.name, validate_text_property(field.name, value))
        if (
            self.min_lines is not None
            and self.max_lines is not None
            and self.min_lines > self.max_lines
        ):
            raise StyleError("min_lines cannot exceed max_lines")


def _native_only():
    raise RuntimeError("Build this app with Anpyra; Android widgets cannot run on the host.")


class FontProperties:
    """Editor-facing writable declarations; validated by the source compiler."""

    family: str | None
    path: str | None
    bold: bool
    italic: bool


class TextProperties:
    """Writable source syntax, separate from immutable TextStyle/Font values."""

    color: str | int
    keep_screen_on: bool
    size: float
    alignment: str
    vertical_alignment: str
    padding: float | tuple
    background_color: str | int
    opacity: float
    width: float | str
    height: float | str
    lines: int
    min_lines: int
    max_lines: int
    single_line: bool
    ellipsize: str | None
    letter_spacing: float
    line_spacing: tuple
    include_font_padding: bool
    all_caps: bool
    underline: bool
    strikethrough: bool
    selectable: bool
    shadow: Shadow
    text_direction: str
    font_features: str
    content_description: str

    @property
    def font(self) -> FontProperties:
        _native_only()

    @font.setter
    def font(self, value: Font | str) -> None:
        _native_only()


class TextView:
    text: str

    @property
    def style(self) -> TextProperties:
        _native_only()

    @style.setter
    def style(self, value: TextStyle) -> None:
        _native_only()

    def __init__(
        self, context: Activity, *, text: str | None = None, style: TextStyle | None = None
    ):
        _native_only()

    def set_text(self, text: str) -> None:
        _native_only()

    def get_text(self) -> str:
        _native_only()

    def is_enabled(self) -> bool:
        _native_only()

    def set_enabled(self, enabled: bool) -> None:
        _native_only()

    def set_text_color(self, color: str | int) -> None:
        _native_only()

    def set_text_size(self, size: float) -> None:
        _native_only()

    def set_alignment(self, alignment: str) -> None:
        _native_only()

    def set_vertical_alignment(self, alignment: str) -> None:
        _native_only()

    def set_padding(self, *padding: float) -> None:
        _native_only()

    def set_font(self, font: Font | str) -> None:
        _native_only()

    def set_style(self, style: TextStyle) -> None:
        _native_only()
