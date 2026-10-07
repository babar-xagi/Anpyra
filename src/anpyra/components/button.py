"""Native Button authoring and validated geometry, states and icon declarations."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field, fields
from typing import TYPE_CHECKING

from .screen import Background, Image, StyleError, parse_color, unit_interval
from .textview import (
    TextProperties,
    TextStyle,
    TextView,
    _native_only,
    number,
    validate_text_property,
)

if TYPE_CHECKING:
    from ..api import Activity


def corners(value):
    values = (value,) * 4 if type(value) in (int, float) else value
    if not isinstance(values, (list, tuple)) or len(values) != 4:
        raise StyleError(
            "corner_radius uses dp or (top_left, top_right, bottom_right, bottom_left)"
        )
    return tuple(number(item, "corner radius", minimum=0) for item in values)


def button_background(value):
    if not isinstance(value, Background) or value.image is not None:
        raise StyleError(
            "Button backgrounds use Background(color=...) or gradient=...; images use Icon"
        )
    if value.color is not None and value.gradient is not None:
        raise StyleError("Button backgrounds choose a color or gradient, not both")
    return value


@dataclass(frozen=True)
class Border:
    color: str | int
    width: float = 1

    def __post_init__(self):
        parse_color(self.color)
        object.__setattr__(self, "width", number(self.width, "border width", minimum=0))


@dataclass(frozen=True)
class Icon:
    path: str
    size: float | tuple = 24
    position: str = "start"
    fit: str = "contain"
    tint: str | int | None = None
    opacity: float = 1

    def __post_init__(self):
        image = Image(self.path)
        object.__setattr__(self, "path", image.path)
        sizes = (self.size, self.size) if type(self.size) in (int, float) else self.size
        if not isinstance(sizes, (tuple, list)) or len(sizes) != 2:
            raise StyleError("icon size uses positive dp or (width_dp, height_dp)")
        sizes = tuple(number(item, "icon size", minimum=0) for item in sizes)
        if min(sizes) == 0:
            raise StyleError("icon dimensions must be greater than zero")
        if self.position not in ("start", "end", "top", "bottom"):
            raise StyleError("icon position is start, end, top or bottom")
        if self.fit not in ("contain", "cover", "fill"):
            raise StyleError("icon fit is contain, cover or fill")
        if self.tint is not None:
            parse_color(self.tint)
        object.__setattr__(self, "size", sizes)
        object.__setattr__(self, "opacity", unit_interval(self.opacity, "icon opacity"))


@dataclass(frozen=True)
class ButtonState:
    color: str | int | None = None
    bg: Background | None = None
    border: Border | None = None

    def __post_init__(self):
        if self.color is not None:
            parse_color(self.color)
        if self.bg is not None:
            button_background(self.bg)
        if self.border is not None and not isinstance(self.border, Border):
            raise StyleError("state border must be Border(...)")


@dataclass(frozen=True)
class ButtonDesign:
    bg: Background = field(default_factory=Background)
    border: Border | None = None
    corner_radius: tuple | None = None
    ripple_color: str | int | None = None
    pressed: ButtonState | None = None
    disabled: ButtonState | None = None
    focused: ButtonState | None = None
    hovered: ButtonState | None = None
    icon: Icon | None = None
    placement: str | None = None
    margin: tuple | None = None
    layout_size: tuple | None = None

    @property
    def custom_background(self):
        return (
            self.bg.color is not None
            or self.bg.gradient is not None
            or self.bg.transparent
            or self.border is not None
            or self.corner_radius is not None
            or self.ripple_color is not None
            or any(
                state is not None and (state.bg is not None or state.border is not None)
                for state in self.states
            )
        )

    @property
    def states(self):
        return self.disabled, self.pressed, self.focused, self.hovered

    def validate(self):
        button_background(self.bg)
        if (
            self.custom_background
            and self.bg.color is None
            and self.bg.gradient is None
            and not self.bg.transparent
        ):
            raise StyleError(
                "declare button.style.bg.color or gradient for custom corners, borders, states or ripple"
            )


@dataclass(frozen=True)
class ButtonStyle(TextStyle):
    bg: Background | None = None
    border: Border | None = None
    corner_radius: float | tuple | None = None
    ripple_color: str | int | None = None
    pressed: ButtonState | None = None
    disabled: ButtonState | None = None
    focused: ButtonState | None = None
    hovered: ButtonState | None = None
    icon: Icon | None = None
    icon_gap: float | None = None
    enabled: bool | None = None
    clickable: bool | None = None
    focusable: bool | None = None
    elevation: float | None = None
    min_width: float | None = None
    min_height: float | None = None
    placement: str | None = None
    margin: float | tuple | None = None

    def __post_init__(self):
        super().__post_init__()
        for descriptor in fields(ButtonStyle):
            if descriptor.name in TextStyle.__dataclass_fields__:
                continue
            value = getattr(self, descriptor.name)
            if value is not None:
                object.__setattr__(
                    self, descriptor.name, validate_button_property(descriptor.name, value)
                )
        if self.selectable:
            raise StyleError(
                "Button text selection is unsupported; use TextView for selectable text"
            )


def validate_button_property(name, value):
    if name == "bg":
        return button_background(value)
    if name == "border":
        if value is not None and not isinstance(value, Border):
            raise StyleError("border must be Border(...) or None")
    elif name == "corner_radius":
        value = corners(value)
    elif name == "ripple_color":
        if value is not None:
            parse_color(value)
    elif name in {"pressed", "disabled", "focused", "hovered"}:
        if value is not None and not isinstance(value, ButtonState):
            raise StyleError(f"{name} must be ButtonState(...) or None")
    elif name == "icon":
        if value is not None and not isinstance(value, Icon):
            raise StyleError("icon must be Icon(...) or None")
    elif name in {"icon_gap", "elevation", "min_width", "min_height"}:
        value = number(value, name, minimum=0)
    elif name in {"enabled", "clickable", "focusable"}:
        if type(value) is not bool:
            raise StyleError(f"{name} must be bool")
    elif name == "placement":
        if value not in (
            "top_start",
            "top_center",
            "top_end",
            "center_start",
            "center",
            "center_end",
            "bottom_start",
            "bottom_center",
            "bottom_end",
        ):
            raise StyleError("placement must be a supported FrameLayout position")
    elif name == "margin":
        value = validate_text_property("padding", value)
    else:
        raise StyleError(f"unsupported Button style property {name!r}")
    return value


class BorderProperties:
    color: str | int
    width: float


class ButtonBackgroundProperties:
    color: str | int | None
    gradient: object
    opacity: float
    transparent: bool


class StateProperties:
    color: str | int | None
    bg: ButtonBackgroundProperties
    border: BorderProperties


class ButtonProperties(TextProperties):
    bg: ButtonBackgroundProperties
    border: BorderProperties
    corner_radius: float | tuple
    ripple_color: str | int | None
    pressed: StateProperties
    disabled: StateProperties
    focused: StateProperties
    hovered: StateProperties
    icon: Icon | None
    icon_gap: float
    enabled: bool
    clickable: bool
    focusable: bool
    elevation: float
    min_width: float
    min_height: float
    placement: str
    margin: float | tuple


class Button(TextView):
    @property
    def style(self) -> ButtonProperties:
        _native_only()

    @style.setter
    def style(self, value: ButtonStyle | TextStyle) -> None:
        _native_only()

    def __init__(
        self,
        context: Activity,
        *,
        text: str | None = None,
        style: ButtonStyle | TextStyle | None = None,
    ):
        _native_only()

    def set_enabled(self, enabled: bool) -> None:
        _native_only()

    def on_click(self, handler: Callable[[], None]) -> None:
        """Bind a no-argument Activity method; compiled to a native listener."""
        _native_only()

    def set_style(self, style: ButtonStyle | TextStyle) -> None:
        _native_only()
