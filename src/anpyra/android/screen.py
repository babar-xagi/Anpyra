"""Native Activity/TextView references and screen-rendering bytecode calls.

Android renders the generated calls on the device; this is not a host UI renderer.
"""

from ..compiler.ir import CallSuperOnCreate, NewTextView, SetContentView, SetText
from .dalvik import OP_INVOKE_DIRECT, OP_INVOKE_SUPER, OP_INVOKE_VIRTUAL
from .dex_types import MethodKey

ACTIVITY_TYPE = "Landroid/app/Activity;"
BUNDLE_TYPE = "Landroid/os/Bundle;"
CONTEXT_TYPE = "Landroid/content/Context;"
TEXT_VIEW_TYPE = "Landroid/widget/TextView;"
CHAR_SEQUENCE_TYPE = "Ljava/lang/CharSequence;"
VIEW_TYPE = "Landroid/view/View;"


def screen_methods(class_descriptor: str) -> dict[str, MethodKey]:
    """Declare the Android UI methods referenced by generated DEX."""
    return {
        "activity_constructor": MethodKey(ACTIVITY_TYPE, "<init>", "V", ()),
        "activity_on_create": MethodKey(ACTIVITY_TYPE, "onCreate", "V", (BUNDLE_TYPE,)),
        "activity_set_content_view": MethodKey(ACTIVITY_TYPE, "setContentView", "V", (VIEW_TYPE,)),
        "text_view_constructor": MethodKey(TEXT_VIEW_TYPE, "<init>", "V", (CONTEXT_TYPE,)),
        "text_view_set_text": MethodKey(TEXT_VIEW_TYPE, "setText", "V", (CHAR_SEQUENCE_TYPE,)),
        "app_constructor": MethodKey(class_descriptor, "<init>", "V", ()),
        "app_on_create": MethodKey(class_descriptor, "onCreate", "V", (BUNDLE_TYPE,)),
    }


def emit_screen_operation(
    op, assembler, registers, this_register, state_register, type_indexes, method_indexes, methods
) -> bool:
    """Emit one lifecycle/widget operation; return False for non-screen IR."""
    if isinstance(op, CallSuperOnCreate):
        assembler.emit(
            "invoke",
            OP_INVOKE_SUPER,
            method_indexes[methods["activity_on_create"]],
            (this_register, state_register),
            "Activity.onCreate(Bundle)",
            size=3,
        )
    elif isinstance(op, NewTextView):
        register = registers[op.target]
        assembler.emit(
            "new_instance", register, type_indexes[TEXT_VIEW_TYPE], TEXT_VIEW_TYPE, size=2
        )
        assembler.emit(
            "invoke",
            OP_INVOKE_DIRECT,
            method_indexes[methods["text_view_constructor"]],
            (register, this_register),
            "TextView.<init>(Context)",
            size=3,
        )
    elif isinstance(op, SetText):
        assembler.emit(
            "invoke",
            OP_INVOKE_VIRTUAL,
            method_indexes[methods["text_view_set_text"]],
            (registers[op.receiver], registers[op.value_var]),
            "TextView.setText(CharSequence)",
            size=3,
        )
    elif isinstance(op, SetContentView):
        assembler.emit(
            "invoke",
            OP_INVOKE_VIRTUAL,
            method_indexes[methods["activity_set_content_view"]],
            (this_register, registers[op.view]),
            "Activity.setContentView(View)",
            size=3,
        )
    else:
        return False
    return True
