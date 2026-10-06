"""Lower declarative TextView properties into ordered native styling IR."""

from dataclasses import fields, replace

from ..components.screen import StyleError
from ..components.textview import Font, TextStyle, validate_text_property
from .ir import SetTextStyle


class TextStyler:
    def __init__(self):
        self.values = {}

    def assign(self, receiver, name, value, *, check_limits=True):
        value = validate_text_property(name, value)
        current = self.values.setdefault(receiver, {})
        candidate = {**current, name: value}
        if name == "lines":
            candidate.update(min_lines=value, max_lines=value)
        if check_limits and candidate.get("min_lines", 1) > candidate.get("max_lines", 0x7FFFFFFF):
            raise StyleError("min_lines cannot exceed max_lines")
        current.update(candidate)
        if name in {"alignment", "vertical_alignment"}:
            return (
                SetTextStyle(
                    receiver,
                    "gravity",
                    (current.get("alignment", "start"), current.get("vertical_alignment", "top")),
                ),
            )
        if name in {"width", "height"}:
            return (
                SetTextStyle(
                    receiver,
                    "dimensions",
                    (current.get("width", "wrap_content"), current.get("height", "wrap_content")),
                ),
            )
        return (SetTextStyle(receiver, name, value),)

    def font_property(self, receiver, name, value):
        if name not in {"family", "path", "bold", "italic"}:
            raise StyleError("font properties are family, path, bold and italic")
        font = self.values.get(receiver, {}).get("font", Font())
        # Switching the font source explicitly replaces the previous source.
        updates = {name: value}
        if name == "family":
            updates["path"] = None
        elif name == "path":
            updates["family"] = None
        return self.assign(receiver, "font", replace(font, **updates))

    def whole(self, receiver, style):
        if not isinstance(style, TextStyle):
            raise StyleError("TextView style must be TextStyle(...)")
        specified = {
            field.name: getattr(style, field.name)
            for field in fields(style)
            if getattr(style, field.name) is not None
        }
        candidate = {**self.values.get(receiver, {}), **specified}
        if "lines" in specified:
            candidate.update(
                min_lines=specified.get("min_lines", specified["lines"]),
                max_lines=specified.get("max_lines", specified["lines"]),
            )
        if candidate.get("min_lines", 1) > candidate.get("max_lines", 0x7FFFFFFF):
            raise StyleError("min_lines cannot exceed max_lines")
        # Validate the final pair before ordered setters; avoid transient conflicts
        # when a complete declaration changes both limits together.
        current = self.values.setdefault(receiver, {})
        current.pop("min_lines", None)
        current.pop("max_lines", None)
        ops = []
        for field in fields(style):
            value = getattr(style, field.name)
            if value is not None:
                ops.extend(self.assign(receiver, field.name, value, check_limits=False))
        current.update(candidate)
        return tuple(ops)
