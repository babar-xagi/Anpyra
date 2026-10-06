"""Collect Button design declarations while reusing ordered text styling."""

from dataclasses import fields, replace

from ..components.button import (
    Border,
    ButtonDesign,
    ButtonState,
    ButtonStyle,
    validate_button_property,
)
from ..components.screen import Background, Gradient, StyleError
from ..components.textview import TextStyle
from .ir import ApplyButtonDesign, SetButtonProperty

STATES = {"pressed", "disabled", "focused", "hovered"}
IMMEDIATE = {
    "enabled",
    "clickable",
    "focusable",
    "elevation",
    "min_width",
    "min_height",
    "icon_gap",
}


class ButtonStyler:
    def __init__(self, text_styler):
        self.text = text_styler
        self.designs = {}

    def design(self, receiver):
        return self.designs.get(receiver, ButtonDesign())

    def begin(self, receiver):
        # None means preserve that part of the actual native Button gravity.
        self.text.values[receiver] = {"alignment": None, "vertical_alignment": None}

    def background(self, background, name, value):
        if name not in {"color", "gradient", "opacity", "transparent"}:
            raise StyleError(
                "Button background properties are color, gradient, opacity and transparent"
            )
        if name == "gradient" and isinstance(value, (list, tuple)):
            value = Gradient(value)
        updates = {name: value}
        if name == "color" and value is not None:
            updates["gradient"] = None
        if name == "gradient" and value is not None:
            updates["color"] = None
        result = replace(background or Background(), **updates)
        return validate_button_property("bg", result)

    def border(self, border, name, value):
        if name == "color":
            return replace(border, color=value) if border is not None else Border(value)
        if name == "width" and border is not None:
            return replace(border, width=value)
        raise StyleError("set Border(...) or border.color before border.width")

    def assign(self, receiver, chain, value):
        if chain == ["style"]:
            return self.whole(receiver, value)
        if not chain or chain[0] != "style":
            raise StyleError("use button.style.PROPERTY")
        parts = chain[1:]
        design = self.design(receiver)
        if parts == ["background_color"]:
            parts = ["bg", "color"]
        if parts == ["radius"]:
            parts = ["corner_radius"]
        if len(parts) == 1:
            name = parts[0]
            if name in TextStyle.__dataclass_fields__:
                if name == "selectable" and value:
                    raise StyleError("Button text selection is unsupported; use TextView")
                return self.text.assign(receiver, name, value)
            value = validate_button_property(name, value)
            if name in IMMEDIATE:
                return (SetButtonProperty(receiver, name, value),)
            design = replace(design, **{name: value})
        elif parts[:1] == ["font"] and len(parts) == 2:
            return self.text.font_property(receiver, parts[1], value)
        elif parts[:1] == ["bg"] and len(parts) == 2:
            design = replace(design, bg=self.background(design.bg, parts[1], value))
        elif parts[:1] == ["border"] and len(parts) == 2:
            design = replace(design, border=self.border(design.border, parts[1], value))
        elif parts and parts[0] in STATES:
            name = parts[0]
            state = getattr(design, name) or ButtonState()
            if len(parts) == 2 and parts[1] in {"color", "bg", "border"}:
                state = replace(state, **{parts[1]: value})
            elif len(parts) == 3 and parts[1] == "bg":
                state = replace(state, bg=self.background(state.bg, parts[2], value))
            elif len(parts) == 3 and parts[1] == "border":
                state = replace(state, border=self.border(state.border, parts[2], value))
            else:
                raise StyleError("button states support color, bg properties and border")
            design = replace(design, **{name: state})
        else:
            raise StyleError("unsupported Button property path")
        self.designs[receiver] = design
        return ()

    def whole(self, receiver, style):
        if not isinstance(style, TextStyle):
            raise StyleError("Button style must be ButtonStyle(...) or TextStyle(...)")
        if style.selectable:
            raise StyleError("Button text selection is unsupported; use TextView")
        # Preserve atomic min/max validation in the shared text declaration path.
        values = {
            item.name: getattr(style, item.name)
            for item in fields(TextStyle)
            if item.name != "background_color"
        }
        ops = list(self.text.whole(receiver, TextStyle(**values)))
        if style.background_color is not None:
            self.assign(receiver, ["style", "bg", "color"], style.background_color)
        if isinstance(style, ButtonStyle):
            for descriptor in fields(ButtonStyle):
                if descriptor.name not in TextStyle.__dataclass_fields__:
                    value = getattr(style, descriptor.name)
                    if value is not None:
                        ops.extend(self.assign(receiver, ["style", descriptor.name], value))
        return tuple(ops)

    def apply(self, receiver):
        design = self.design(receiver)
        design.validate()
        values = self.text.values.get(receiver, {})
        if design.placement is not None or design.margin is not None:
            design = replace(
                design,
                layout_size=(
                    values.get("width", "wrap_content"),
                    values.get("height", "wrap_content"),
                ),
            )
        operations = [ApplyButtonDesign(receiver, design)]
        # A replacement background may change native padding; explicit source
        # padding wins over the drawable/theme's internal padding afterward.
        if design.custom_background and "padding" in values:
            operations.extend(self.text.assign(receiver, "padding", values["padding"]))
        return tuple(operations)
