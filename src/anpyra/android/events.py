"""Native generic click dispatch, typed state, expression code and saved state."""

from ..compiler.ir import (
    BindClick,
    CallEvent,
    EventAction,
    EventAssign,
    EventExpr,
    EventIf,
    EventReturn,
    InitAppField,
    StoreAppField,
)
from .classes import MethodDefinition
from .dalvik import (
    OP_IF_EQ,
    OP_IF_GE,
    OP_IF_GT,
    OP_IF_LE,
    OP_IF_LT,
    OP_IF_NE,
    OP_INVOKE_SUPER,
    OP_INVOKE_VIRTUAL,
    emit_const,
    emit_invoke,
)
from .dex_types import FieldKey, MethodKey, MethodListing
from .method_builder import MethodBuilder
from .screen import ACTIVITY_TYPE, BUNDLE_TYPE

STRING = "Ljava/lang/String;"
TEXT = "Landroid/widget/TextView;"
VIEW = "Landroid/view/View;"
LISTENER = "Landroid/view/View$OnClickListener;"
TYPES = {
    "int": "I",
    "bool": "Z",
    "str": STRING,
    "TextView": TEXT,
    "Button": "Landroid/widget/Button;",
    "TextInput": "Landroid/widget/EditText;",
    "Screen": "Landroid/widget/FrameLayout;",
    "Column": "Landroid/widget/LinearLayout;",
    "Row": "Landroid/widget/LinearLayout;",
    "ScrollView": "Landroid/widget/ScrollView;",
}
INVERSE = {
    "==": OP_IF_NE,
    "!=": OP_IF_EQ,
    "<": OP_IF_GE,
    "<=": OP_IF_GT,
    ">": OP_IF_LE,
    ">=": OP_IF_LT,
}


def walk_values(value):
    if isinstance(value, EventExpr):
        yield value
        for argument in value.args:
            yield from walk_values(argument)
    elif isinstance(value, EventAssign):
        yield from walk_values(value.value)
    elif isinstance(value, EventAction):
        for argument in value.args:
            yield from walk_values(argument)
    elif isinstance(value, EventIf):
        yield from walk_values(value.condition)
        yield from walk_values(value.then_ops)
        yield from walk_values(value.else_ops)
    elif isinstance(value, tuple):
        for item in value:
            yield from walk_values(item)


class EventPlan:
    def __init__(self, app, operations, chat_fallback=None):
        self.app = app
        self.fields, self.refs, self.builders = {}, {}, []
        self.bindings = [op for op in operations if isinstance(op, BindClick)]
        self.schema = {field.name: field for field in app.app_fields}
        self.literals = {"True", "False"}
        self.fallback = chat_fallback
        for field in app.app_fields:
            self.fields[field.name] = FieldKey(
                app.class_descriptor, "anpyra_field_" + field.name, TYPES[field.type_name]
            )
            if field.persist:
                self.literals.add("anpyra.state." + field.name)
                self.refs["restore_" + field.name] = MethodKey(
                    app.class_descriptor, "anpyra_restore_" + field.name, "V", (BUNDLE_TYPE,)
                )
        for index, binding in enumerate(self.bindings):
            self.fields["$click" + str(index)] = FieldKey(
                app.class_descriptor, "anpyra_click_" + str(index), TYPES["Button"]
            )
        for method in app.handlers:
            self.refs["handler_" + method.name] = MethodKey(
                app.class_descriptor, "anpyra_event_" + method.name, "V", ()
            )
            self.literals.update(
                value.value
                for value in walk_values(method.operations)
                if value.kind == "constant" and value.type_name == "str"
            )
        self.literals.update(
            op.value
            for op in operations
            if isinstance(op, InitAppField) and isinstance(op.value, str)
        )
        for fn in app.functions:
            self.refs["helper_" + fn.name] = MethodKey(
                app.class_descriptor, fn.name, "I", ("I",) * len(fn.parameters)
            )

        def add(key, owner, name, returned="V", params=()):
            self.refs[key] = MethodKey(owner, name, returned, params)

        add("bind_click", VIEW, "setOnClickListener", params=(LISTENER,))
        add("set_text", TEXT, "setText", params=("Ljava/lang/CharSequence;",))
        add("get_text", TEXT, "getText", "Ljava/lang/CharSequence;")
        add("to_string", "Ljava/lang/Object;", "toString", STRING)
        add("int_string", STRING, "valueOf", STRING, ("I",))
        add("concat", STRING, "concat", STRING, (STRING,))
        add("equals", STRING, "equals", "Z", ("Ljava/lang/Object;",))
        add("empty", STRING, "isEmpty", "Z")
        add("set_enabled", VIEW, "setEnabled", params=("Z",))
        add("is_enabled", VIEW, "isEnabled", "Z")
        add("set_text_color", TEXT, "setTextColor", params=("I",))
        add("recreate", ACTIVITY_TYPE, "recreate")
        if self.bindings:
            add("dispatch", app.class_descriptor, "onClick", params=(VIEW,))
        if chat_fallback:
            self.refs["chat_fallback"] = chat_fallback
        if any(field.persist for field in app.app_fields):
            add("save_super", ACTIVITY_TYPE, "onSaveInstanceState", params=(BUNDLE_TYPE,))
            add("save", app.class_descriptor, "onSaveInstanceState", params=(BUNDLE_TYPE,))
            add("has_key", BUNDLE_TYPE, "containsKey", "Z", (STRING,))
            for typ, suffix in (("int", "Int"), ("str", "String"), ("bool", "Boolean")):
                add("save_" + typ, BUNDLE_TYPE, "put" + suffix, params=(STRING, TYPES[typ]))
                add("load_" + typ, BUNDLE_TYPE, "get" + suffix, TYPES[typ], (STRING,))

    def builder(self, pools, key, registers=16, inputs=1):
        builder = MethodBuilder(pools, self.refs, self.fields, registers, inputs)
        self.builders.append((self.refs[key], builder))
        return builder

    def dispatch(self, pools):
        b = self.builder(pools, "dispatch", 6, 2)
        for index, binding in enumerate(self.bindings):
            b.get(0, 4, "$click" + str(index))
            b.compare(OP_IF_NE, 0, 5, "next" + str(index))
            b.invoke("handler_" + binding.handler, (4,))
            b.asm.emit("return_void", size=1)
            b.label("next" + str(index))
        if self.fallback:
            b.invoke("chat_fallback", (4, 5))
        b.asm.emit("return_void", size=1)
        return b.finish()

    def restore(self, pools, field):
        b = self.builder(pools, "restore_" + field.name, 6, 2)
        b.zero(5, "done")
        b.string(0, "anpyra.state." + field.name)
        b.invoke("has_key", (5, 0), result=1)
        b.zero(1, "done")
        b.invoke("load_" + field.type_name, (5, 0), result=0)
        # Defensive saved Bundle handling never installs a null into a str field.
        if field.type_name == "str":
            b.zero(0, "done")
        b.put(0, 4, field.name)
        b.label("done")
        b.asm.emit("return_void", size=1)
        return b.finish()

    def save(self, pools):
        b = self.builder(pools, "save", 6, 2)
        method = self.refs["save_super"]
        emit_invoke(
            b.asm,
            OP_INVOKE_SUPER,
            pools.methods[method],
            (4, 5),
            (method.owner, *method.parameters),
            None,
            "Activity.onSaveInstanceState",
        )
        for field in self.app.app_fields:
            if field.persist:
                b.string(0, "anpyra.state." + field.name)
                b.get(1, 4, field.name)
                b.invoke("save_" + field.type_name, (5, 0, 1))
        b.asm.emit("return_void", size=1)
        return b.finish()

    def definitions(self):
        result = [
            MethodDefinition(
                self.refs["handler_" + handler.name],
                1,
                lambda pools, h=handler: RuntimeEmitter(self, pools, h).compile(),
            )
            for handler in self.app.handlers
        ]
        if self.bindings:
            result.append(MethodDefinition(self.refs["dispatch"], 1, self.dispatch))
        if "save" in self.refs:
            result.append(MethodDefinition(self.refs["save"], 4, self.save))
        for field in self.app.app_fields:
            if field.persist:
                result.append(
                    MethodDefinition(
                        self.refs["restore_" + field.name],
                        1,
                        lambda pools, f=field: self.restore(pools, f),
                    )
                )
        return result

    def listings(self):
        return tuple(
            MethodListing(
                f"{key.owner}->{key.name}",
                tuple(
                    ("this" if i == 0 else f"arg{i}", typ, b.registers - b.inputs + i)
                    for i, typ in enumerate((key.owner, *key.parameters))
                ),
                b.code_units,
                b.assembly_listing,
            )
            for key, b in self.builders
        )


class RuntimeEmitter:
    def __init__(self, plan, pools, handler):
        self.plan, self.handler = plan, handler
        self.b = plan.builder(pools, "handler_" + handler.name)
        self.locals = {name: index for index, (name, _) in enumerate(handler.local_types)}
        self.free = list(range(len(self.locals), 15))

    def allocate(self):
        if not self.free:
            raise ValueError(
                f"callback {self.handler.name}: expression needs too many temporary registers; split it into simpler statements"
            )
        return self.free.pop(0)

    def release(self, *registers):
        for reg in registers:
            self.free.append(reg)
        self.free.sort()

    def truth(self, argument, invert=False):
        b = self.b
        value = self.value(argument)
        result = self.allocate()
        done = b.asm.new_label("truth_done")
        b.const(result, 1 if invert else 0)
        if argument.type_name == "str":
            yes = b.asm.new_label("truth_yes")
            b.invoke("empty", (value,), result=value)
            b.zero(value, yes)
            b.jump(done)
            b.label(yes)
        else:
            b.zero(value, done)
        b.const(result, 0 if invert else 1)
        b.label(done)
        self.release(value)
        return result

    def value(self, expr):
        b = self.b
        if expr.kind in {"truth", "not"}:
            return self.truth(expr.args[0], expr.kind == "not")
        if expr.kind == "to_string":
            value = self.value(expr.args[0])
            typ = expr.args[0].type_name
            if typ == "int":
                b.invoke("int_string", (value,), static=True, result=value)
                return value
            if typ == "str":
                return value
            result = self.allocate()
            end = b.asm.new_label("bool_string")
            b.string(result, "False")
            b.zero(value, end)
            b.string(result, "True")
            b.label(end)
            self.release(value)
            return result
        if expr.kind == "bool_op":
            result = self.allocate()
            end = b.asm.new_label("bool_done")
            b.const(result, 0)
            for arg in expr.args:
                value = self.value(arg)
                if expr.value == "and":
                    b.zero(value, end)
                else:
                    next_arg = b.asm.new_label("bool_next")
                    b.zero(value, next_arg)
                    b.const(result, 1)
                    b.jump(end)
                    b.label(next_arg)
                self.release(value)
            if expr.value == "and":
                b.const(result, 1)
            b.label(end)
            return result
        if expr.kind in {"binary", "compare", "helper"}:
            args = [self.value(arg) for arg in expr.args]
            result = self.allocate()
            if expr.kind == "helper":
                b.invoke("helper_" + expr.value, tuple(args), static=True, result=result)
            elif expr.kind == "binary":
                if expr.type_name == "str":
                    b.invoke("concat", tuple(args), result=result)
                else:
                    b.asm.emit(
                        "int_binop",
                        0x90 if expr.value == "+" else 0x91,
                        result,
                        *args,
                        "add-int" if expr.value == "+" else "sub-int",
                        size=2,
                    )
            elif expr.args[0].type_name == "str":
                b.invoke("equals", tuple(args), result=result)
                if expr.value == "!=":
                    end, yes = b.asm.new_label("ne_done"), b.asm.new_label("ne_yes")
                    b.zero(result, yes)
                    b.const(result, 0)
                    b.jump(end)
                    b.label(yes)
                    b.const(result, 1)
                    b.label(end)
            else:
                end = b.asm.new_label("compare_done")
                b.const(result, 0)
                b.compare(INVERSE[expr.value], *args, end)
                b.const(result, 1)
                b.label(end)
            self.release(*args)
            return result
        result = self.allocate()
        if expr.kind == "constant":
            if expr.type_name == "str":
                b.string(result, expr.value)
            else:
                b.const(result, int(expr.value))
        elif expr.kind == "local":
            b.asm.emit(
                "move_object" if expr.type_name == "str" else "move",
                result,
                self.locals[expr.value],
                size=2,
            )
        elif expr.kind == "field":
            b.get(result, 15, expr.value)
        elif expr.kind in {"get_text", "is_enabled"}:
            b.get(result, 15, expr.value)
            b.invoke(expr.kind, (result,), result=result)
            if expr.kind == "get_text":
                b.invoke("to_string", (result,), result=result)
        else:
            raise ValueError(f"unsupported event expression {expr.kind}")
        return result

    def statements(self, operations):
        b = self.b
        for op in operations:
            if isinstance(op, EventAssign):
                result = self.value(op.value)
                if op.kind == "field":
                    b.put(result, 15, op.name)
                else:
                    b.asm.emit(
                        "move_object" if op.value.type_name == "str" else "move",
                        self.locals[op.name],
                        result,
                        size=2,
                    )
                self.release(result)
            elif isinstance(op, EventIf):
                other, end = b.asm.new_label("event_else"), b.asm.new_label("event_end")
                result = self.truth(op.condition)
                b.zero(result, other)
                self.release(result)
                self.statements(op.then_ops)
                b.jump(end)
                b.label(other)
                self.statements(op.else_ops)
                b.label(end)
            elif isinstance(op, EventReturn):
                b.asm.emit("return_void", size=1)
            elif isinstance(op, EventAction):
                if op.receiver is None:
                    b.invoke(
                        "recreate" if op.method == "recreate" else "handler_" + op.method, (15,)
                    )
                else:
                    receiver = self.allocate()
                    b.get(receiver, 15, op.receiver)
                    args = [self.value(arg) for arg in op.args]
                    b.invoke(op.method, (receiver, *args))
                    self.release(receiver, *args)

    def compile(self):
        self.statements(self.handler.operations)
        self.b.asm.emit("return_void", size=1)
        return self.b.finish()


def emit_event_lifecycle(
    op,
    asm,
    registers,
    this_register,
    state_register,
    sidx,
    midx,
    fidx,
    methods,
    argument_base,
    plan,
):
    if not isinstance(op, (StoreAppField, InitAppField, BindClick, CallEvent)):
        return False

    def invoke(key, args):
        method = methods[key]
        emit_invoke(
            asm,
            OP_INVOKE_VIRTUAL,
            midx[method],
            args,
            (method.owner, *method.parameters),
            argument_base,
            method.name,
        )

    if isinstance(op, (StoreAppField, InitAppField)):
        field = plan.fields[op.name]
        if isinstance(op, InitAppField):
            if field.type_name == STRING:
                asm.emit("const_string", 0, sidx[op.value], op.value, size=2)
            else:
                emit_const(asm, 0, int(op.value))
        else:
            asm.emit("move_object", 0, registers[op.value_var], size=2)
        asm.emit("move_object", 1, this_register, size=2)
        kind = (
            "iput_object"
            if field.type_name.startswith("L")
            else "iput_boolean"
            if field.type_name == "Z"
            else "iput"
        )
        asm.emit(kind, 0, 1, fidx[field], field.name, size=2)
        if plan.schema[op.name].persist:
            invoke("restore_" + op.name, (this_register, state_register))
    elif isinstance(op, BindClick):
        index = plan.bindings.index(op)
        field = plan.fields["$click" + str(index)]
        asm.emit("move_object", 0, registers[op.button], size=2)
        asm.emit("move_object", 1, this_register, size=2)
        asm.emit("iput_object", 0, 1, fidx[field], field.name, size=2)
        invoke("bind_click", (registers[op.button], this_register))
    else:
        invoke("handler_" + op.handler, (this_register,))
    return True
