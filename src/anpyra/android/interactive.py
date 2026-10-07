"""Compose typed event/state and optional ChatSession classes in one DEX."""

from ..compiler.ir import ApplyScreenBackground, BindChatSession, BindClick, LoadConst
from .backgrounds import background_fields
from .button import button_fields, button_strings
from .classes import ClassDefinition, MethodDefinition, write_classes
from .codegen import _walk_ops, generate_methods
from .dex_types import DexBuild, MethodKey, MethodListing
from .events import LISTENER, EventPlan
from .layout import layout_strings
from .screen import ACTIVITY_TYPE, screen_methods
from .textview import textview_fields, textview_strings


def build_interactive_dex(app):
    from .chat import EXCEPTION, GLOBAL_LAYOUT, OBJECT, RUNNABLE, ChatPlan

    operations = tuple(_walk_ops(app.operations))
    bindings = [op for op in operations if isinstance(op, BindChatSession)]
    if len(bindings) > 1:
        raise ValueError("chat apps require exactly one ChatSession")
    generic_clicks = any(isinstance(op, BindClick) for op in operations)
    chat = ChatPlan(app, bindings[0], external_dispatch=generic_clicks) if bindings else None
    events = (
        EventPlan(app, operations, chat.refs["on_click"] if chat and generic_clicks else None)
        if app.app_fields or app.handlers
        else None
    )
    refs = chat.refs.copy() if chat else screen_methods(app.class_descriptor, operations)
    if events:
        refs.update(events.refs)
    fields = (
        set(background_fields(operations)) | button_fields(operations) | textview_fields(operations)
    )
    if chat:
        fields.update(chat.fields.values())
    if events:
        fields.update(events.fields.values())
    strings = {op.value for op in operations if isinstance(op, LoadConst) and op.type_name == "str"}
    strings.update(
        op.image_asset
        for op in operations
        if isinstance(op, ApplyScreenBackground) and op.image_asset is not None
    )
    strings.update(button_strings(operations))
    strings.update(textview_strings(operations))
    strings.update(layout_strings(operations))
    if chat:
        strings.update(chat.literals)
    if events:
        strings.update(events.literals)
    helpers = {
        fn.name: MethodKey(app.class_descriptor, fn.name, "I", ("I",) * len(fn.parameters))
        for fn in app.functions
    }
    generated = {}

    def lifecycle(pools, which):
        if not generated:
            generated["methods"] = generate_methods(
                app,
                pools.types,
                pools.strings,
                pools.methods,
                helpers,
                refs,
                pools.fields,
                chat_scroll=chat.scroll if chat else None,
                event_plan=events,
            )
        return getattr(generated["methods"], which)

    ui_methods = [
        MethodDefinition(
            refs["app_constructor"], 0x10001, lambda p: lifecycle(p, "constructor_code"), True
        ),
        MethodDefinition(refs["app_on_create"], 4, lambda p: lifecycle(p, "lifecycle_code")),
    ]
    if chat:
        ui_methods.extend(
            (
                MethodDefinition(chat.refs["init_chat"], 1, chat.init),
                MethodDefinition(chat.refs["on_click"], 1, chat.click),
                MethodDefinition(chat.refs["on_reply"], 1, chat.reply),
            )
        )
        if chat.scroll:
            ui_methods.append(MethodDefinition(chat.refs["scroll_run"], 1, chat.scroll_run))
    if events:
        ui_methods.extend(events.definitions())
    for key in helpers.values():

        def helper(pools, key=key):
            lifecycle(pools, "constructor_code")
            return next(row[2] for row in generated["methods"].helper_codes if row[0] == key)

        ui_methods.append(MethodDefinition(key, 9, helper, True))
    interfaces = ()
    if chat or generic_clicks:
        interfaces += (LISTENER,)
    if chat and chat.scroll:
        interfaces += (GLOBAL_LAYOUT,)
    classes = [
        ClassDefinition(
            app.class_descriptor,
            ACTIVITY_TYPE,
            tuple(ui_methods),
            tuple((field, 2) for field in fields if field.owner == app.class_descriptor),
            interfaces,
        )
    ]
    if chat:
        classes.extend(
            (
                ClassDefinition(
                    chat.worker,
                    OBJECT,
                    (
                        MethodDefinition(
                            chat.refs["worker_ctor"], 0x10001, chat.worker_constructor, True
                        ),
                        MethodDefinition(chat.refs["worker_run"], 1, chat.worker_run),
                    ),
                    tuple(
                        (field, 2) for field in chat.fields.values() if field.owner == chat.worker
                    ),
                    (RUNNABLE,),
                ),
                ClassDefinition(
                    chat.delivery,
                    OBJECT,
                    (
                        MethodDefinition(
                            chat.refs["delivery_ctor"], 0x10001, chat.delivery_constructor, True
                        ),
                        MethodDefinition(chat.refs["delivery_run"], 1, chat.delivery_run),
                    ),
                    tuple(
                        (field, 1) for field in chat.fields.values() if field.owner == chat.delivery
                    ),
                    (RUNNABLE,),
                ),
            )
        )
    references = (
        *refs.values(),
        *helpers.values(),
        *(chat.refs.values() if chat else ()),
        *(events.refs.values() if events else ()),
    )
    data = write_classes(classes, references, fields, strings, (EXCEPTION,) if chat else ())
    methods = generated["methods"]
    extra = events.listings() if events else ()
    if chat:
        extra += tuple(
            MethodListing(
                f"{key.owner}->{key.name}",
                tuple(
                    ("this" if index == 0 else f"arg{index}", typ, b.registers - b.inputs + index)
                    for index, typ in enumerate((key.owner, *key.parameters))
                ),
                b.code_units,
                b.assembly_listing,
            )
            for key, b in chat.builders
        )
    return DexBuild(
        data,
        methods.register_map,
        methods.code_units,
        methods.assembly_listing,
        (*methods.listings, *extra),
    )
