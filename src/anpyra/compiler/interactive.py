"""Restricted multi-child layout and standalone chat-controller bindings."""

import ast

from ..components.screen import StyleError, parse_color
from ..components.textview import number, validate_text_property
from .ir import AddLayoutChild, BindChatSession, NewLayout, NewTextInput
from .screen_style import style_value


def constructor(fc, node):
    call = node.value
    if (
        not isinstance(call, ast.Call)
        or not isinstance(call.func, ast.Name)
        or call.func.id not in {"Column", "Row", "ScrollView", "TextInput", "ChatSession"}
    ):
        return None
    target, kind = node.targets[0].id, call.func.id
    if len(call.args) != 1 or not isinstance(call.args[0], ast.Name) or call.args[0].id != "self":
        raise StyleError(f"construct {kind}(self, ...)")
    names = [item.arg for item in call.keywords]
    if None in names or len(names) != len(set(names)):
        raise StyleError("use distinct explicit keyword arguments")
    if kind in {"Column", "Row", "ScrollView"}:
        if names:
            raise StyleError(f"{kind} constructor takes only context")
        fc.declare(target, kind, node)
        return (NewLayout(target, kind),)
    if kind == "TextInput":
        if any(name not in {"hint", "password", "hint_color"} for name in names):
            raise StyleError("TextInput accepts hint=, password= and hint_color=")
        values = {item.arg: style_value(item.value, fc.constants) for item in call.keywords}
        if (
            not isinstance(values.get("hint", ""), str)
            or type(values.get("password", False)) is not bool
        ):
            raise StyleError("hint is str and password is bool")
        fc.declare(target, kind, node)
        fc.text_inputs[target] = values.get("password", False)
        color = values.get("hint_color")
        return (
            NewTextInput(
                target,
                values.get("hint", ""),
                values.get("password", False),
                None if color is None else parse_color(color),
            ),
        )
    required = {
        "key_input": "TextInput",
        "message_input": "TextInput",
        "transcript": "TextView",
        "status": "TextView",
        "send_button": "Button",
        "clear_button": "Button",
    }
    values = {}
    for item in call.keywords:
        if item.arg == "model":
            values["model"] = style_value(item.value, fc.constants)
        elif item.arg in required and isinstance(item.value, ast.Name):
            fc.require(item.value.id, required[item.arg], node)
            values[item.arg] = item.value.id
        else:
            raise StyleError(f"invalid ChatSession binding keyword {item.arg!r}")
    if not required.keys() <= values.keys() or fc.chat_bound:
        raise StyleError("bind one ChatSession with all six views")
    if len(set(values[name] for name in required)) != len(required):
        raise StyleError("ChatSession views must be distinct")
    if not fc.text_inputs.get(values["key_input"]):
        raise StyleError("ChatSession key_input must be TextInput(password=True)")
    model = values.get("model", "gpt-5.5")
    if not isinstance(model, str) or not model.strip() or "\x00" in model:
        raise StyleError("ChatSession model must be a nonempty string")
    fc.declare(target, kind, node)
    fc.chat_bound = True
    return (BindChatSession(target, **{name: values[name] for name in required}, model=model),)


def method(fc, node, receiver, attr, call):
    if not isinstance(receiver, ast.Name):
        return None
    kind = fc.symbols.get(receiver.id)
    if attr == "add" and kind in {"Column", "Row"}:
        if fc.branch_depth or len(call.args) != 1 or not isinstance(call.args[0], ast.Name):
            raise StyleError("layout.add(view, ...) belongs outside branches")
        child = call.args[0].id
        fc.require(child, "View", node)
        if fc.symbols[child] == "Screen":
            raise StyleError("Screen is the Activity root; add a layout or widget as content")
        if child == receiver.id or child in fc.attached:
            raise StyleError("a view cannot be its own parent or have two parents")
        keys = [item.arg for item in call.keywords]
        if (
            None in keys
            or len(keys) != len(set(keys))
            or any(key not in {"width", "height", "weight", "margin"} for key in keys)
        ):
            raise StyleError("layout.add accepts width, height, weight and margin")
        values = {item.arg: style_value(item.value, fc.constants) for item in call.keywords}
        width = validate_text_property("width", values.get("width", "match_parent"))
        height = validate_text_property("height", values.get("height", "wrap_content"))
        weight = number(values.get("weight", 0), "layout weight", minimum=0, maximum=1000)
        margin = validate_text_property("padding", values.get("margin", 0))
        fc.attach(child, receiver.id, node)
        prefix = fc.button_styler.apply(child) if fc.symbols[child] == "Button" else ()
        return (*prefix, AddLayoutChild(receiver.id, child, width, height, weight, margin))
    if attr == "set_background_color" and kind in {"Column", "Row"}:
        if len(call.args) != 1 or call.keywords:
            raise StyleError("set_background_color accepts one color")
        return fc.text_styler.assign(
            receiver.id, "background_color", style_value(call.args[0], fc.constants)
        )
    return None
