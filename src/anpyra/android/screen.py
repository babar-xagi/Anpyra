"""Native Activity/TextView references and screen-rendering bytecode calls.

Android renders the generated calls on the device; this is not a host UI renderer.
"""

from ..compiler.ir import (
    CallSuperOnCreate,
    NewScreen,
    NewTextView,
    SetContentView,
    SetScreenContent,
    SetText,
    SetTextColor,
    SetTextStyle,
)
from .backgrounds import FRAME, SDK_FIELD, VIEW, background_methods
from .dalvik import (
    OP_IF_LT,
    OP_INVOKE_DIRECT,
    OP_INVOKE_SUPER,
    OP_INVOKE_VIRTUAL,
    emit_const,
    emit_invoke,
)
from .dex_types import MethodKey
from .textview import textview_methods

ACTIVITY_TYPE = "Landroid/app/Activity;"
BUNDLE_TYPE = "Landroid/os/Bundle;"
CONTEXT_TYPE = "Landroid/content/Context;"
TEXT_VIEW_TYPE = "Landroid/widget/TextView;"
CHAR_SEQUENCE_TYPE = "Ljava/lang/CharSequence;"
VIEW_TYPE = "Landroid/view/View;"


def screen_methods(class_descriptor: str, operations=()) -> dict[str, MethodKey]:
    """Declare the Android UI methods referenced by generated DEX."""
    methods = {
        "activity_constructor": MethodKey(ACTIVITY_TYPE, "<init>", "V", ()),
        "activity_on_create": MethodKey(ACTIVITY_TYPE, "onCreate", "V", (BUNDLE_TYPE,)),
        "activity_set_content_view": MethodKey(ACTIVITY_TYPE, "setContentView", "V", (VIEW_TYPE,)),
        "text_view_constructor": MethodKey(TEXT_VIEW_TYPE, "<init>", "V", (CONTEXT_TYPE,)),
        "text_view_set_text": MethodKey(TEXT_VIEW_TYPE, "setText", "V", (CHAR_SEQUENCE_TYPE,)),
        "app_constructor": MethodKey(class_descriptor, "<init>", "V", ()),
        "app_on_create": MethodKey(class_descriptor, "onCreate", "V", (BUNDLE_TYPE,)),
    }
    if any(isinstance(op, NewScreen) for op in operations):
        methods.update(background_methods())
        methods["frame_constructor"] = MethodKey(FRAME, "<init>", "V", (CONTEXT_TYPE,))
        methods["frame_content"] = MethodKey(FRAME, "addView", "V", (VIEW_TYPE,))
    if any(isinstance(op, SetTextColor) for op in operations):
        methods["text_view_color"] = MethodKey(TEXT_VIEW_TYPE, "setTextColor", "V", ("I",))
    methods.update(textview_methods(operations))
    if any(isinstance(op, (NewScreen, SetTextColor, SetTextStyle)) for op in operations):
        methods["view_force_dark"] = MethodKey(VIEW, "setForceDarkAllowed", "V", ("Z",))
    return methods


def emit_screen_operation(
    op,
    assembler,
    registers,
    this_register,
    state_register,
    type_indexes,
    method_indexes,
    methods,
    argument_base=None,
    scratch=(),
    field_indexes=None,
) -> bool:
    """Emit one lifecycle/widget operation; return False for non-screen IR."""

    def invoke(name, args, opcode=OP_INVOKE_VIRTUAL, pretty=""):
        key = methods[name]
        emit_invoke(
            assembler,
            opcode,
            method_indexes[key],
            args,
            (key.owner, *key.parameters),
            argument_base,
            pretty or f"{key.owner}->{key.name}",
        )

    def preserve_colors(register):
        if argument_base is None:
            return
        end = assembler.new_label("skip_force_dark")
        assembler.emit("sget", 0, field_indexes[SDK_FIELD], "Build.VERSION.SDK_INT", size=2)
        emit_const(assembler, 1, 29)
        assembler.emit("if_test", OP_IF_LT, 0, 1, end, "if-lt", size=2)
        emit_const(assembler, 1, 0)
        invoke("view_force_dark", (register, 1))
        assembler.label(end)

    if isinstance(op, CallSuperOnCreate):
        invoke(
            "activity_on_create",
            (this_register, state_register),
            OP_INVOKE_SUPER,
            "Activity.onCreate(Bundle)",
        )
    elif isinstance(op, NewTextView):
        register = registers[op.target]
        assembler.emit(
            "new_instance", register, type_indexes[TEXT_VIEW_TYPE], TEXT_VIEW_TYPE, size=2
        )
        invoke(
            "text_view_constructor",
            (register, this_register),
            OP_INVOKE_DIRECT,
            "TextView.<init>(Context)",
        )
        preserve_colors(register)
    elif isinstance(op, SetText):
        invoke(
            "text_view_set_text",
            (registers[op.receiver], registers[op.value_var]),
            pretty="TextView.setText(CharSequence)",
        )
    elif isinstance(op, SetContentView):
        invoke(
            "activity_set_content_view",
            (this_register, registers[op.view]),
            pretty="Activity.setContentView(View)",
        )
    elif isinstance(op, NewScreen):
        register = registers[op.target]
        assembler.emit("new_instance", register, type_indexes[FRAME], FRAME, size=2)
        invoke("frame_constructor", (register, this_register), OP_INVOKE_DIRECT)
        preserve_colors(register)
    elif isinstance(op, SetScreenContent):
        invoke("frame_content", (registers[op.receiver], registers[op.view]))
    elif isinstance(op, SetTextColor):
        value = scratch[3]
        emit_const(assembler, value, op.color)
        invoke("text_view_color", (registers[op.receiver], value))
    else:
        return False
    return True
