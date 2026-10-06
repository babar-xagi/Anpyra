"""Native Button drawables, state colors, geometry, ripple and icon emission."""

import struct
from dataclasses import replace

from ..compiler.ir import ApplyButtonDesign, NewButton, SetButtonProperty
from ..components.screen import alpha_byte, parse_color
from .backgrounds import (
    ASSETS,
    BITMAP,
    CONTEXT,
    DRAWABLE,
    FRAME_PARAMS,
    GRADIENT,
    LAYOUT_PARAMS,
    ORIENTATION,
    ORIENTATIONS,
    SDK_FIELD,
    STREAM,
    STRING,
    VIEW,
)
from .dalvik import (
    OP_INVOKE_DIRECT,
    OP_INVOKE_STATIC,
    OP_INVOKE_VIRTUAL,
    OP_SUB_INT,
    emit_const,
    emit_invoke,
)
from .dex_types import FieldKey, MethodKey
from .textview import METRICS, RESOURCES, TEXT

BUTTON = "Landroid/widget/Button;"
STATES = "Landroid/graphics/drawable/StateListDrawable;"
RIPPLE = "Landroid/graphics/drawable/RippleDrawable;"
COLORS = "Landroid/content/res/ColorStateList;"
BITMAP_DRAWABLE = "Landroid/graphics/drawable/BitmapDrawable;"
ATTR = "Landroid/R$attr;"
STATE_NAMES = ("disabled", "pressed", "focused", "hovered")
PLACEMENTS = {
    "top_start": 0x800033,
    "top_center": 49,
    "top_end": 0x800035,
    "center_start": 0x800013,
    "center": 17,
    "center_end": 0x800015,
    "bottom_start": 0x800053,
    "bottom_center": 81,
    "bottom_end": 0x800055,
}
GRAVITY_FIELD = FieldKey(FRAME_PARAMS, "gravity", "I")
STATE_FIELDS = {
    name: FieldKey(ATTR, "state_enabled" if name == "disabled" else "state_" + name, "I")
    for name in STATE_NAMES
}
PROPERTIES = {
    "enabled": ("button_enabled", VIEW, "setEnabled", "Z"),
    "clickable": ("button_clickable", VIEW, "setClickable", "Z"),
    "focusable": ("button_focusable", VIEW, "setFocusable", "Z"),
    "elevation": ("button_elevation", VIEW, "setElevation", "F"),
    "min_width": ("button_min_width", TEXT, "setMinWidth", "I"),
    "min_height": ("button_min_height", TEXT, "setMinHeight", "I"),
    "icon_gap": ("button_icon_gap", TEXT, "setCompoundDrawablePadding", "I"),
}


def effective_background(design, state):
    if state is None or state.bg is None:
        return design.bg
    background = state.bg
    if background.color is None and background.gradient is None and not background.transparent:
        return replace(background, color=design.bg.color, gradient=design.bg.gradient)
    return background


def button_methods(operations):
    refs = {}

    def add(key, owner, name, returns="V", params=()):
        refs[key] = MethodKey(owner, name, returns, params)

    def dimensions():
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

    for op in operations:
        if isinstance(op, NewButton):
            add("button_constructor", BUTTON, "<init>", params=(CONTEXT,))
        elif isinstance(op, SetButtonProperty):
            key, owner, native, parameter = PROPERTIES[op.property]
            add(key, owner, native, params=(parameter,))
            if op.property in {"elevation", "min_width", "min_height", "icon_gap"}:
                dimensions()
            if op.property == "elevation":
                add(
                    "button_animator",
                    VIEW,
                    "setStateListAnimator",
                    params=("Landroid/animation/StateListAnimator;",),
                )
        elif isinstance(op, ApplyButtonDesign):
            design = op.design
            if design.layout_size is not None:
                dimensions()
                add("layout_constructor", FRAME_PARAMS, "<init>", params=("I", "I"))
                add("text_layout", VIEW, "setLayoutParams", params=(LAYOUT_PARAMS,))
                add(
                    "button_margins",
                    "Landroid/view/ViewGroup$MarginLayoutParams;",
                    "setMargins",
                    params=("I", "I", "I", "I"),
                )
            if any(state is not None and state.color is not None for state in design.states):
                add("button_get_colors", TEXT, "getTextColors", COLORS)
                add("button_default_color", COLORS, "getDefaultColor", "I")
                add("button_state_color", COLORS, "getColorForState", "I", ("[I", "I"))
                add("button_colors_constructor", COLORS, "<init>", params=("[[I", "[I"))
                add("button_text_colors", TEXT, "setTextColor", params=(COLORS,))
            if design.custom_background:
                dimensions()
                add("button_shape", GRADIENT, "<init>")
                add("button_fill", GRADIENT, "setColor", params=("I",))
                add("button_stroke", GRADIENT, "setStroke", params=("I", "I"))
                add("button_radius", GRADIENT, "setCornerRadius", params=("F",))
                add("button_radii", GRADIENT, "setCornerRadii", params=("[F",))
                add("button_gradient_colors", GRADIENT, "setColors", params=("[I",))
                add("button_orientation", GRADIENT, "setOrientation", params=(ORIENTATION,))
                add("gradient_type", GRADIENT, "setGradientType", params=("I",))
                add("gradient_center", GRADIENT, "setGradientCenter", params=("F", "F"))
                add("gradient_radius", GRADIENT, "setGradientRadius", params=("F",))
                add("drawable_alpha", DRAWABLE, "setAlpha", params=("I",))
                add("button_states", STATES, "<init>")
                add("button_add_state", STATES, "addState", params=("[I", DRAWABLE))
                add("view_background", VIEW, "setBackground", params=(DRAWABLE,))
                add("button_background_tint", VIEW, "setBackgroundTintList", params=(COLORS,))
                if design.ripple_color is not None:
                    add("button_color_list", COLORS, "valueOf", COLORS, ("I",))
                    add("button_ripple", RIPPLE, "<init>", params=(COLORS, DRAWABLE, DRAWABLE))
            if design.icon is not None:
                dimensions()
                add("context_assets", CONTEXT, "getAssets", ASSETS)
                add("asset_open", ASSETS, "open", STREAM, (STRING,))
                add(
                    "bitmap_decode",
                    "Landroid/graphics/BitmapFactory;",
                    "decodeStream",
                    BITMAP,
                    (STREAM,),
                )
                add("stream_close", STREAM, "close")
                add("button_bitmap_drawable", BITMAP_DRAWABLE, "<init>", params=(RESOURCES, BITMAP))
                add("button_icon_bounds", DRAWABLE, "setBounds", params=("I", "I", "I", "I"))
                add("drawable_alpha", DRAWABLE, "setAlpha", params=("I",))
                add("button_icon_tint", DRAWABLE, "setTint", params=("I",))
                add("button_icon", TEXT, "setCompoundDrawablesRelative", params=(DRAWABLE,) * 4)
    return refs


def button_fields(operations):
    fields = set()
    for op in operations:
        if isinstance(op, NewButton):
            fields.add(SDK_FIELD)
        elif isinstance(op, ApplyButtonDesign):
            design = op.design
            if design.placement is not None:
                fields.add(GRAVITY_FIELD)
            if any(state is not None and state.color is not None for state in design.states):
                fields.update(STATE_FIELDS.values())
            if design.custom_background:
                for name, state in zip(STATE_NAMES, design.states):
                    if state is not None and (state.bg is not None or state.border is not None):
                        fields.add(STATE_FIELDS[name])
                for state in (*design.states, None):
                    gradient = effective_background(design, state).gradient
                    if gradient is not None:
                        fields.add(
                            FieldKey(ORIENTATION, ORIENTATIONS[gradient.direction], ORIENTATION)
                        )
    return fields


def button_strings(operations):
    strings = set()
    for op in operations:
        if isinstance(op, ApplyButtonDesign) and op.design.icon is not None:
            if op.icon_asset is None:
                raise ValueError("resolve Button icon assets before building DEX")
            strings.add(op.icon_asset)
    return strings


def emit_button(
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
    if not isinstance(op, (ApplyButtonDesign, SetButtonProperty)):
        return False
    receiver = registers[op.receiver]
    a, b, c, value, index, metrics, container = scratch

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

    def create(register, descriptor, key):
        assembler.emit("new_instance", register, type_indexes[descriptor], descriptor, size=2)
        invoke(key, (register,), OP_INVOKE_DIRECT)

    def floating(register, number):
        emit_const(assembler, register, struct.unpack("<I", struct.pack("<f", number))[0])

    def dimensions():
        invoke("text_resources", (this_register,))
        assembler.emit("move_result_object", index, size=1)
        invoke("text_metrics", (index,))
        assembler.emit("move_result_object", metrics, size=1)

    def pixels(number, register, *, rounded=False):
        emit_const(assembler, value, 1)
        floating(index, number)
        invoke("text_dimension", (value, index, metrics), OP_INVOKE_STATIC)
        assembler.emit("move_result", register, size=1)
        if rounded:
            invoke("text_round", (register,), OP_INVOKE_STATIC)
            assembler.emit("move_result", register, size=1)

    def array(descriptor, count, register):
        emit_const(assembler, 1, count)
        assembler.emit("new_array", 0, 1, type_indexes[descriptor], descriptor, size=2)
        if register != 0:
            assembler.emit("move_object", register, 0, size=2)

    def state_array(name):
        array("[I", 0 if name is None else 1, 0)
        if name is not None:
            field = STATE_FIELDS[name]
            assembler.emit("sget", 1, field_indexes[field], field.name, size=2)
            emit_const(assembler, value, 0)
            if name == "disabled":
                assembler.emit("int_binop", OP_SUB_INT, 1, value, 1, "sub-int", size=2)
            assembler.emit("aput", 1, 0, value, size=2)

    if isinstance(op, SetButtonProperty):
        key, _, _, parameter = PROPERTIES[op.property]
        if op.value_var is not None:
            invoke(key, (receiver, registers[op.value_var]))
        elif parameter == "Z":
            emit_const(assembler, value, int(op.value))
            invoke(key, (receiver, value))
        else:
            dimensions()
            if op.property == "elevation":
                emit_const(assembler, value, 0)
                invoke("button_animator", (receiver, value))
            pixels(op.value, b, rounded=parameter == "I")
            invoke(key, (receiver, b))
        return True

    design = op.design
    # Build a text ColorStateList while retaining native colors for unspecified states.
    if any(state is not None and state.color is not None for state in design.states):
        invoke("button_get_colors", (receiver,))
        assembler.emit("move_result_object", a, size=1)
        invoke("button_default_color", (a,))
        assembler.emit("move_result", b, size=1)
        array("[[I", 5, c)
        array("[I", 5, value)
        # Colors use the fourth scratch slot. State-array construction uses a
        # different zero register so it cannot overwrite that persistent array.
        color_array = value
        for position, (name, state) in enumerate(zip((*STATE_NAMES, None), (*design.states, None))):
            array("[I", 0 if name is None else 1, 0)
            if name is not None:
                field = STATE_FIELDS[name]
                assembler.emit("sget", 1, field_indexes[field], field.name, size=2)
                emit_const(assembler, metrics, 0)
                if name == "disabled":
                    assembler.emit("int_binop", OP_SUB_INT, 1, metrics, 1, "sub-int", size=2)
                assembler.emit("aput", 1, 0, metrics, size=2)
            emit_const(assembler, index, position)
            assembler.emit("aput_object", 0, c, index, size=2)
            if state is not None and state.color is not None:
                emit_const(assembler, metrics, parse_color(state.color))
            else:
                invoke("button_state_color", (a, 0, b))
                assembler.emit("move_result", metrics, size=1)
            assembler.emit("aput", metrics, color_array, index, size=2)
        assembler.emit("new_instance", container, type_indexes[COLORS], COLORS, size=2)
        invoke("button_colors_constructor", (container, c, color_array), OP_INVOKE_DIRECT)
        invoke("button_text_colors", (receiver, container))

    if design.custom_background or design.icon is not None or design.layout_size is not None:
        dimensions()

    def shape(background, border, *, mask=False):
        create(a, GRADIENT, "button_shape")
        gradient = background.gradient
        if mask:
            emit_const(assembler, value, 0xFFFFFFFF)  # Opaque coverage; mask RGB is not visible.
            invoke("button_fill", (a, value))
        elif gradient is not None:
            array("[I", len(gradient.colors), b)
            for position, color in enumerate(gradient.colors):
                emit_const(assembler, value, parse_color(color))
                emit_const(assembler, index, position)
                assembler.emit("aput", value, b, index, size=2)
            invoke("button_gradient_colors", (a, b))
            field = FieldKey(ORIENTATION, ORIENTATIONS[gradient.direction], ORIENTATION)
            assembler.emit("sget_object", b, field_indexes[field], field.name, size=2)
            invoke("button_orientation", (a, b))
            emit_const(assembler, value, {"linear": 0, "radial": 1, "sweep": 2}[gradient.kind])
            invoke("gradient_type", (a, value))
            if gradient.kind != "linear":
                floating(value, gradient.center[0])
                floating(index, gradient.center[1])
                invoke("gradient_center", (a, value, index))
            if gradient.kind == "radial":
                floating(value, gradient.radius)
                invoke("gradient_radius", (a, value))
        elif background.color is not None:
            emit_const(assembler, value, parse_color(background.color))
            invoke("button_fill", (a, value))
        radii = design.corner_radius
        if radii is not None:
            if len(set(radii)) == 1:
                pixels(radii[0], b)
                invoke("button_radius", (a, b))
            else:
                array("[F", 8, b)
                for position, radius in enumerate(radii):
                    pixels(radius, c)
                    for axis in (0, 1):
                        emit_const(assembler, value, 2 * position + axis)
                        assembler.emit("aput", c, b, value, size=2)
                invoke("button_radii", (a, b))
        if border is not None and not mask:
            pixels(border.width, b, rounded=True)
            emit_const(assembler, c, parse_color(border.color))
            invoke("button_stroke", (a, b, c))
        if not mask:
            emit_const(assembler, value, alpha_byte(background.effective_opacity))
            invoke("drawable_alpha", (a, value))

    if design.custom_background:
        create(container, STATES, "button_states")
        for name, state in zip(STATE_NAMES, design.states):
            if state is not None and (state.bg is not None or state.border is not None):
                shape(
                    effective_background(design, state),
                    state.border if state.border is not None else design.border,
                )
                state_array(name)
                invoke("button_add_state", (container, 0, a))
        shape(design.bg, design.border)
        state_array(None)
        invoke("button_add_state", (container, 0, a))
        if design.ripple_color is not None:
            shape(design.bg, None, mask=True)
            emit_const(assembler, value, parse_color(design.ripple_color))
            invoke("button_color_list", (value,), OP_INVOKE_STATIC)
            assembler.emit("move_result_object", b, size=1)
            assembler.emit("new_instance", c, type_indexes[RIPPLE], RIPPLE, size=2)
            invoke("button_ripple", (c, b, container, a), OP_INVOKE_DIRECT)
            assembler.emit("move_object", container, c, size=2)
        emit_const(assembler, value, 0)
        invoke("button_background_tint", (receiver, value))
        invoke("view_background", (receiver, container))

    if design.icon is not None:
        icon = design.icon
        invoke("context_assets", (this_register,))
        assembler.emit("move_result_object", b, size=1)
        assembler.emit("const_string", value, string_indexes[op.icon_asset], op.icon_asset, size=2)
        invoke("asset_open", (b, value))
        assembler.emit("move_result_object", b, size=1)
        invoke("bitmap_decode", (b,), OP_INVOKE_STATIC)
        assembler.emit("move_result_object", a, size=1)
        invoke("stream_close", (b,))
        invoke("text_resources", (this_register,))
        assembler.emit("move_result_object", c, size=1)
        assembler.emit("new_instance", b, type_indexes[BITMAP_DRAWABLE], BITMAP_DRAWABLE, size=2)
        invoke("button_bitmap_drawable", (b, c, a), OP_INVOKE_DIRECT)
        pixels(icon.size[0], c, rounded=True)
        pixels(icon.size[1], a, rounded=True)
        emit_const(assembler, index, 0)
        invoke("button_icon_bounds", (b, index, index, c, a))
        emit_const(assembler, value, alpha_byte(icon.opacity))
        invoke("drawable_alpha", (b, value))
        if icon.tint is not None:
            emit_const(assembler, value, parse_color(icon.tint))
            invoke("button_icon_tint", (b, value))
        emit_const(assembler, value, 0)
        args = [value] * 4
        args[("start", "top", "end", "bottom").index(icon.position)] = b
        invoke("button_icon", (receiver, *args))
    if design.layout_size is not None:
        for register, dimension in zip((b, c), design.layout_size):
            if isinstance(dimension, str):
                emit_const(assembler, register, -1 if dimension == "match_parent" else -2)
            else:
                pixels(dimension, register, rounded=True)
        assembler.emit("new_instance", a, type_indexes[FRAME_PARAMS], FRAME_PARAMS, size=2)
        invoke("layout_constructor", (a, b, c), OP_INVOKE_DIRECT)
        if design.placement is not None:
            emit_const(assembler, 0, PLACEMENTS[design.placement])
            assembler.emit("move_object", 1, a, size=2)
            assembler.emit(
                "iput",
                0,
                1,
                field_indexes[GRAVITY_FIELD],
                "FrameLayout.LayoutParams.gravity",
                size=2,
            )
        if design.margin is not None:
            top, right, bottom, left = design.margin
            # Preserve params in the container slot while converting four dp values.
            assembler.emit("move_object", container, a, size=2)
            for register, number in zip((a, b, c, 0), (left, top, right, bottom)):
                pixels(number, register, rounded=True)
            invoke("button_margins", (container, a, b, c, 0))
            assembler.emit("move_object", a, container, size=2)
        invoke("text_layout", (receiver, a))
    return True
