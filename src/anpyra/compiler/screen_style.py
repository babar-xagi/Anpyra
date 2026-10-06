"""Parse declarative component values without executing application source."""

import ast
from dataclasses import replace

from ..components.screen import Background, Gradient, Image, StyleError

CONSTRUCTORS = {"Background": Background, "Gradient": Gradient, "Image": Image}


def style_value(node, constants=None):
    if isinstance(node, ast.Name) and constants is not None and node.id in constants:
        return constants[node.id]
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in CONSTRUCTORS
    ):
        if any(keyword.arg is None for keyword in node.keywords):
            raise StyleError("style constructors do not accept ** expansion")
        keys = [keyword.arg for keyword in node.keywords]
        if len(keys) != len(set(keys)):
            raise StyleError("duplicate style keyword")
        try:
            return CONSTRUCTORS[node.func.id](
                *[style_value(value, constants) for value in node.args],
                **{item.arg: style_value(item.value, constants) for item in node.keywords},
            )
        except TypeError as exc:
            raise StyleError(str(exc)) from exc
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError) as exc:
        raise StyleError(
            "style values must be literals or initialized constant string/bool locals"
        ) from exc


def background_assignment(background: Background, attribute: str, value) -> Background:
    if attribute == "image" and isinstance(value, str):
        value = Image(value)
    if attribute == "gradient" and isinstance(value, (list, tuple)):
        value = Gradient(value)
    if attribute in {"fit", "image_opacity", "frame"}:
        if background.image is None:
            raise StyleError("set the background image before its image options")
        field = {"fit": "fit", "image_opacity": "opacity", "frame": "frame"}[attribute]
        return replace(background, image=replace(background.image, **{field: value}))
    if attribute not in {"color", "image", "gradient", "opacity", "transparent"}:
        raise StyleError(f"unsupported background property {attribute!r}")
    return replace(background, **{attribute: value})
