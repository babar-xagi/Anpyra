"""Native LinearLayout, ScrollView and EditText emission for interactive apps."""

import struct

from ..compiler.ir import AddLayoutChild, NewLayout, NewTextInput, SetScrollContent
from .backgrounds import CONTEXT, LAYOUT_PARAMS, VIEW
from .dalvik import OP_INVOKE_DIRECT, OP_INVOKE_STATIC, OP_INVOKE_VIRTUAL, emit_const, emit_invoke
from .dex_types import MethodKey
from .textview import METRICS, RESOURCES

LINEAR = "Landroid/widget/LinearLayout;"
PARAMS = "Landroid/widget/LinearLayout$LayoutParams;"
SCROLL = "Landroid/widget/ScrollView;"
EDIT = "Landroid/widget/EditText;"
FRAME_PARAMS = "Landroid/widget/FrameLayout$LayoutParams;"


def layout_methods(operations):
    result = {}

    def add(key, owner, name, returned="V", parameters=()):
        result[key] = MethodKey(owner, name, returned, parameters)

    for op in operations:
        if isinstance(op, NewLayout):
            if op.kind == "ScrollView":
                add("scroll_constructor", SCROLL, "<init>", parameters=(CONTEXT,))
                add("scroll_fill", SCROLL, "setFillViewport", parameters=("Z",))
            else:
                add("linear_constructor", LINEAR, "<init>", parameters=(CONTEXT,))
                add("linear_orientation", LINEAR, "setOrientation", parameters=("I",))
        elif isinstance(op, NewTextInput):
            add("edit_constructor", EDIT, "<init>", parameters=(CONTEXT,))
            add("edit_hint", EDIT, "setHint", parameters=("Ljava/lang/CharSequence;",))
            add("edit_type", EDIT, "setInputType", parameters=("I",))
            add("edit_single", EDIT, "setSingleLine", parameters=("Z",))
            add("edit_save", VIEW, "setSaveEnabled", parameters=("Z",))
            if op.hint_color is not None:
                add("edit_hint_color", EDIT, "setHintTextColor", parameters=("I",))
        elif isinstance(op, AddLayoutChild):
            add("linear_params", PARAMS, "<init>", parameters=("I", "I", "F"))
            add("linear_add", LINEAR, "addView", parameters=(VIEW, LAYOUT_PARAMS))
            add(
                "linear_margin",
                "Landroid/view/ViewGroup$MarginLayoutParams;",
                "setMargins",
                parameters=("I",) * 4,
            )
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
        elif isinstance(op, SetScrollContent):
            add("scroll_params", FRAME_PARAMS, "<init>", parameters=("I", "I"))
            add("scroll_add", SCROLL, "addView", parameters=(VIEW, LAYOUT_PARAMS))
    return result


def layout_strings(operations):
    return {op.hint for op in operations if isinstance(op, NewTextInput)}


def emit_layout(
    op, asm, registers, this_register, tidx, sidx, midx, methods, scratch, argument_base
):
    if not isinstance(op, (NewLayout, NewTextInput, AddLayoutChild, SetScrollContent)):
        return False
    a, b, c, d, unit, temp, metrics = scratch

    def invoke(key, args, opcode=OP_INVOKE_VIRTUAL):
        method = methods[key]
        types = (
            method.parameters if opcode == OP_INVOKE_STATIC else (method.owner, *method.parameters)
        )
        emit_invoke(
            asm, opcode, midx[method], args, types, argument_base, f"{method.owner}->{method.name}"
        )

    def floating(register, value):
        emit_const(asm, register, struct.unpack("<I", struct.pack("<f", value))[0])

    def dimension(value, register):
        if isinstance(value, str):
            emit_const(asm, register, -1 if value == "match_parent" else -2)
            return
        emit_const(asm, unit, 1)
        floating(temp, value)
        invoke("text_dimension", (unit, temp, metrics), OP_INVOKE_STATIC)
        asm.emit("move_result", register, size=1)
        invoke("text_round", (register,), OP_INVOKE_STATIC)
        asm.emit("move_result", register, size=1)

    if isinstance(op, NewLayout):
        target = registers[op.target]
        descriptor = SCROLL if op.kind == "ScrollView" else LINEAR
        asm.emit("new_instance", target, tidx[descriptor], descriptor, size=2)
        invoke(
            "scroll_constructor" if op.kind == "ScrollView" else "linear_constructor",
            (target, this_register),
            OP_INVOKE_DIRECT,
        )
        emit_const(asm, a, 1 if op.kind in {"Column", "ScrollView"} else 0)
        invoke("scroll_fill" if op.kind == "ScrollView" else "linear_orientation", (target, a))
    elif isinstance(op, NewTextInput):
        target = registers[op.target]
        asm.emit("new_instance", target, tidx[EDIT], EDIT, size=2)
        invoke("edit_constructor", (target, this_register), OP_INVOKE_DIRECT)
        asm.emit("const_string", a, sidx[op.hint], op.hint, size=2)
        invoke("edit_hint", (target, a))
        if op.password:
            emit_const(asm, a, 1)
            invoke("edit_single", (target, a))
        # setSingleLine installs a transformation: setInputType must follow it
        # to restore Android's password transformation for a masked input.
        emit_const(asm, a, 0x81 if op.password else 0x20001)
        invoke("edit_type", (target, a))
        # Input belongs to this Activity lifetime; never restore credentials in saved state.
        emit_const(asm, a, 0)
        invoke("edit_save", (target, a))
        if op.hint_color is not None:
            emit_const(asm, a, op.hint_color)
            invoke("edit_hint_color", (target, a))
    elif isinstance(op, SetScrollContent):
        emit_const(asm, a, -1)
        emit_const(asm, b, -2)
        asm.emit("new_instance", c, tidx[FRAME_PARAMS], FRAME_PARAMS, size=2)
        invoke("scroll_params", (c, a, b), OP_INVOKE_DIRECT)
        invoke("scroll_add", (registers[op.receiver], registers[op.view], c))
    else:
        invoke("text_resources", (this_register,))
        asm.emit("move_result_object", temp, size=1)
        invoke("text_metrics", (temp,))
        asm.emit("move_result_object", metrics, size=1)
        dimension(op.width, a)
        dimension(op.height, b)
        floating(c, op.weight)
        asm.emit("new_instance", d, tidx[PARAMS], PARAMS, size=2)
        invoke("linear_params", (d, a, b, c), OP_INVOKE_DIRECT)
        if any(op.margin):
            asm.emit("move_object", 1, d, size=2)
            top, right, bottom, left = op.margin
            for value, register in zip((left, top, right, bottom), (a, b, c, d)):
                dimension(value, register)
            invoke("linear_margin", (1, a, b, c, d))
            asm.emit("move_object", d, 1, size=2)
        invoke("linear_add", (registers[op.receiver], registers[op.view], d))
    return True
