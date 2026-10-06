"""Native TextView typography, density conversion and font bytecode emission."""

import struct

from ..compiler.ir import SetTextStyle
from ..components.screen import parse_color
from .backgrounds import ASSETS, CONTEXT, FRAME_PARAMS, LAYOUT_PARAMS, STRING, VIEW
from .dalvik import OP_INVOKE_DIRECT, OP_INVOKE_STATIC, OP_INVOKE_VIRTUAL, emit_const, emit_invoke
from .dex_types import FieldKey, MethodKey

TEXT = "Landroid/widget/TextView;"
TYPEFACE = "Landroid/graphics/Typeface;"
RESOURCES = "Landroid/content/res/Resources;"
METRICS = "Landroid/util/DisplayMetrics;"
TRUNCATE = "Landroid/text/TextUtils$TruncateAt;"
CHAR_SEQUENCE = "Ljava/lang/CharSequence;"
GRAVITY_HORIZONTAL = {"left": 3, "right": 5, "start": 0x800003, "end": 0x800005, "center": 1}
GRAVITY_VERTICAL = {"top": 48, "center": 16, "bottom": 80}
DIRECTIONS = {
    "inherit": 0,
    "first_strong": 1,
    "any_rtl": 2,
    "ltr": 3,
    "rtl": 4,
    "locale": 5,
    "first_strong_ltr": 6,
    "first_strong_rtl": 7,
}

SIMPLE = {
    "keep_screen_on": ("text_keep_screen_on", VIEW, "setKeepScreenOn", "Z"),
    "color": ("text_view_color", TEXT, "setTextColor", "I"),
    "background_color": ("text_background_color", VIEW, "setBackgroundColor", "I"),
    "size": ("text_size", TEXT, "setTextSize", "F"),
    "opacity": ("text_opacity", VIEW, "setAlpha", "F"),
    "lines": ("text_lines", TEXT, "setLines", "I"),
    "min_lines": ("text_min_lines", TEXT, "setMinLines", "I"),
    "max_lines": ("text_max_lines", TEXT, "setMaxLines", "I"),
    "single_line": ("text_single_line", TEXT, "setSingleLine", "Z"),
    "letter_spacing": ("text_letter_spacing", TEXT, "setLetterSpacing", "F"),
    "include_font_padding": ("text_include_padding", TEXT, "setIncludeFontPadding", "Z"),
    "all_caps": ("text_all_caps", TEXT, "setAllCaps", "Z"),
    "selectable": ("text_selectable", TEXT, "setTextIsSelectable", "Z"),
    "text_direction": ("text_direction", VIEW, "setTextDirection", "I"),
    "font_features": ("text_features", TEXT, "setFontFeatureSettings", STRING),
    "content_description": ("text_description", VIEW, "setContentDescription", CHAR_SEQUENCE),
}


def textview_methods(operations):
    result = {}

    def add(key, owner, name, returned="V", parameters=()):
        result[key] = MethodKey(owner, name, returned, parameters)

    for op in operations:
        if not isinstance(op, SetTextStyle):
            continue
        name = op.property
        if name in SIMPLE:
            key, owner, native, parameter = SIMPLE[name]
            add(key, owner, native, parameters=(parameter,))
        elif name == "gravity":
            add("text_gravity", TEXT, "setGravity", parameters=("I",))
            add("text_alignment", VIEW, "setTextAlignment", parameters=("I",))
        elif name == "font":
            add("text_typeface", TEXT, "setTypeface", parameters=(TYPEFACE,))
            add("text_get_typeface", TEXT, "getTypeface", TYPEFACE)
            add("typeface_style", TYPEFACE, "create", TYPEFACE, (TYPEFACE, "I"))
            if op.value.family is not None:
                add("typeface_family", TYPEFACE, "create", TYPEFACE, (STRING, "I"))
            if op.value.path is not None:
                add("context_assets", CONTEXT, "getAssets", ASSETS)
                add("typeface_asset", TYPEFACE, "createFromAsset", TYPEFACE, (ASSETS, STRING))
        elif name == "ellipsize":
            add("text_ellipsize", TEXT, "setEllipsize", parameters=(TRUNCATE,))
        elif name in {"underline", "strikethrough"}:
            add("text_get_flags", TEXT, "getPaintFlags", "I")
            add("text_flags", TEXT, "setPaintFlags", parameters=("I",))
        elif name == "padding":
            add("text_padding", VIEW, "setPadding", parameters=("I", "I", "I", "I"))
        elif name == "dimensions":
            add("layout_constructor", FRAME_PARAMS, "<init>", parameters=("I", "I"))
            add("text_layout", VIEW, "setLayoutParams", parameters=(LAYOUT_PARAMS,))
        elif name == "line_spacing":
            add("text_line_spacing", TEXT, "setLineSpacing", parameters=("F", "F"))
        elif name == "shadow":
            add("text_shadow", TEXT, "setShadowLayer", parameters=("F", "F", "F", "I"))
        if name in {"padding", "dimensions", "line_spacing", "shadow"}:
            add("text_resources", CONTEXT, "getResources", RESOURCES)
            add("text_metrics", RESOURCES, "getDisplayMetrics", METRICS)
            add(
                "text_dimension",
                "Landroid/util/TypedValue;",
                "applyDimension",
                "F",
                ("I", "F", METRICS),
            )
            add("text_round", "Ljava/lang/Math;", "round", "I", ("F",))
    return result


def textview_fields(operations):
    return {
        FieldKey(TRUNCATE, op.value.upper(), TRUNCATE)
        for op in operations
        if isinstance(op, SetTextStyle) and op.property == "ellipsize" and op.value is not None
    }


def textview_strings(operations):
    strings = set()
    for op in operations:
        if not isinstance(op, SetTextStyle):
            continue
        if op.property in {"font_features", "content_description"}:
            strings.add(op.value)
        elif op.property == "font":
            if op.value.family is not None:
                strings.add(op.value.family)
            if op.value.path is not None:
                if op.font_asset is None:
                    raise ValueError("resolve local font assets before building DEX")
                strings.add(op.font_asset)
    return strings


def emit_text_style(
    op,
    assembler,
    registers,
    this_register,
    type_indexes,
    string_indexes,
    method_indexes,
    field_indexes,
    methods,
    scratch,
    argument_base,
):
    if not isinstance(op, SetTextStyle):
        return False
    receiver = registers[op.receiver]
    a, b, c, d, unit, temporary, metrics = scratch
    name, value = op.property, op.value

    def invoke(key, args, opcode=OP_INVOKE_VIRTUAL):
        method = methods[key]
        types = (
            method.parameters if opcode == OP_INVOKE_STATIC else (method.owner, *method.parameters)
        )
        emit_invoke(
            assembler,
            opcode,
            method_indexes[method],
            args,
            types,
            argument_base,
            f"{method.owner}->{method.name}",
        )

    def floating(register, number):
        emit_const(assembler, register, struct.unpack("<I", struct.pack("<f", number))[0])

    def string(register, literal):
        assembler.emit("const_string", register, string_indexes[literal], literal, size=2)

    def pixels(number, destination, *, rounded=False):
        emit_const(assembler, unit, 1)  # Android COMPLEX_UNIT_DIP
        floating(temporary, number)
        invoke("text_dimension", (unit, temporary, metrics), OP_INVOKE_STATIC)
        assembler.emit("move_result", destination, size=1)
        if rounded:
            invoke("text_round", (destination,), OP_INVOKE_STATIC)
            assembler.emit("move_result", destination, size=1)

    if name in {"padding", "dimensions", "line_spacing", "shadow"}:
        invoke("text_resources", (this_register,))
        assembler.emit("move_result_object", temporary, size=1)
        invoke("text_metrics", (temporary,))
        assembler.emit("move_result_object", metrics, size=1)
    if name in SIMPLE:
        key, _, _, parameter = SIMPLE[name]
        if name in {"color", "background_color"}:
            emit_const(assembler, a, parse_color(value))
        elif parameter == "F":
            floating(a, value)
        elif parameter in {STRING, CHAR_SEQUENCE}:
            string(a, value)
        else:
            emit_const(assembler, a, DIRECTIONS[value] if name == "text_direction" else int(value))
        invoke(key, (receiver, a))
    elif name == "gravity":
        emit_const(assembler, a, GRAVITY_HORIZONTAL[value[0]] | GRAVITY_VERTICAL[value[1]])
        invoke("text_gravity", (receiver, a))
        emit_const(assembler, a, 1)  # TEXT_ALIGNMENT_GRAVITY
        invoke("text_alignment", (receiver, a))
    elif name == "font":
        emit_const(assembler, d, value.native_style)
        if value.path is not None:
            invoke("context_assets", (this_register,))
            assembler.emit("move_result_object", b, size=1)
            string(c, op.font_asset)
            invoke("typeface_asset", (b, c), OP_INVOKE_STATIC)
            assembler.emit("move_result_object", a, size=1)
        elif value.family is not None:
            string(b, value.family)
            invoke("typeface_family", (b, d), OP_INVOKE_STATIC)
            assembler.emit("move_result_object", a, size=1)
        else:
            invoke("text_get_typeface", (receiver,))
            assembler.emit("move_result_object", a, size=1)
        if value.family is None:
            invoke("typeface_style", (a, d), OP_INVOKE_STATIC)
            assembler.emit("move_result_object", a, size=1)
        invoke("text_typeface", (receiver, a))
    elif name == "ellipsize":
        if value is None:
            emit_const(assembler, a, 0)
        else:
            field = FieldKey(TRUNCATE, value.upper(), TRUNCATE)
            assembler.emit("sget_object", a, field_indexes[field], field.name, size=2)
        invoke("text_ellipsize", (receiver, a))
    elif name in {"underline", "strikethrough"}:
        bit = 8 if name == "underline" else 16
        invoke("text_get_flags", (receiver,))
        assembler.emit("move_result", a, size=1)
        emit_const(assembler, b, bit if value else ~bit)
        assembler.emit(
            "int_binop", 0x96 if value else 0x95, a, a, b, "or-int" if value else "and-int", size=2
        )
        invoke("text_flags", (receiver, a))
    elif name == "padding":
        top, right, bottom, left = value
        for register, number in zip((a, b, c, d), (left, top, right, bottom)):
            pixels(number, register, rounded=True)
        invoke("text_padding", (receiver, a, b, c, d))
    elif name == "dimensions":
        for register, dimension in zip((b, c), value):
            if isinstance(dimension, str):
                emit_const(assembler, register, -1 if dimension == "match_parent" else -2)
            else:
                pixels(dimension, register, rounded=True)
        assembler.emit("new_instance", a, type_indexes[FRAME_PARAMS], FRAME_PARAMS, size=2)
        invoke("layout_constructor", (a, b, c), OP_INVOKE_DIRECT)
        invoke("text_layout", (receiver, a))
    elif name == "line_spacing":
        pixels(value[0], a)
        floating(b, value[1])
        invoke("text_line_spacing", (receiver, a, b))
    elif name == "shadow":
        for register, number in zip((a, b, c), (value.radius, value.dx, value.dy)):
            pixels(number, register)
        emit_const(assembler, d, parse_color(value.color))
        invoke("text_shadow", (receiver, a, b, c, d))
    else:
        raise ValueError(f"unsupported native TextView property {name}")
    return True
