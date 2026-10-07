"""Typed Activity fields and restricted Python click-handler source lowering."""

import ast

from ..components.screen import StyleError, parse_color
from .ir import (
    AppField,
    BindChatSession,
    BindClick,
    CallEvent,
    EventAction,
    EventAssign,
    EventExpr,
    EventHandler,
    EventIf,
    EventReturn,
    InitAppField,
    StoreAppField,
)

SCALARS = {"int", "str", "bool"}
TEXT_VIEWS = {"TextView", "Button", "TextInput"}
VIEWS = TEXT_VIEWS | {"Screen", "Column", "Row", "ScrollView"}
LIFECYCLE = {"on_start", "on_resume", "on_pause", "on_stop", "on_destroy", "on_save_instance_state"}


def fail(message):
    raise StyleError(message)


def field_name(node):
    if (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "self"
    ):
        return node.attr
    return None


def literal(node):
    try:
        value = ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError):
        fail("state defaults must be int/str/bool literals")
    typ = (
        "bool"
        if type(value) is bool
        else "int"
        if type(value) is int
        else "str"
        if isinstance(value, str)
        else None
    )
    if typ is None or (typ == "int" and not -0x80000000 <= value <= 0x7FFFFFFF):
        fail("state values use str, bool or signed 32-bit int")
    return typ, value


def collect_methods(cls):
    result = {}
    for node in cls.body:
        if not isinstance(node, ast.FunctionDef) or node.name == "on_create":
            continue
        args = node.args.posonlyargs + node.args.args
        if (
            node.name in result
            or node.name in LIFECYCLE | {"recreate", "set_content_view"}
            or node.name.startswith("__")
        ):
            fail(f"line {node.lineno}: duplicate/reserved callback method {node.name!r}")
        if (
            len(args) != 1
            or args[0].arg != "self"
            or node.args.vararg
            or node.args.kwarg
            or node.args.kwonlyargs
            or node.args.defaults
            or node.decorator_list
            or getattr(node, "type_params", [])
            or args[0].annotation
            or (
                node.returns is not None
                and not (isinstance(node.returns, ast.Constant) and node.returns.value is None)
            )
        ):
            fail(f"line {node.lineno}: handlers use def {node.name}(self), optionally -> None")
        result[node.name] = node
    if len(result) > 32:
        fail("at most 32 Activity callback methods are supported")
    return result


def lifecycle(fc, node):
    """Return new lifecycle operations, or None to retain legacy lowering."""
    if isinstance(node, ast.AnnAssign) and (name := field_name(node.target)) is not None:
        if (
            fc.branch_depth
            or node.value is None
            or not isinstance(node.annotation, ast.Name)
            or node.annotation.id not in SCALARS
        ):
            fail("declare initialized self fields with int/str/bool annotations outside branches")
        value, persist = node.value, False
        if (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id == "State"
        ):
            if (
                len(value.args) != 1
                or len(value.keywords) > 1
                or any(k.arg != "persist" for k in value.keywords)
            ):
                fail("use State(default, persist=True/False)")
            if value.keywords:
                flag = value.keywords[0].value
                if not isinstance(flag, ast.Constant) or type(flag.value) is not bool:
                    fail("State persist must be a literal bool")
                persist = flag.value
            value = value.args[0]
        typ, initial = literal(value)
        if typ != node.annotation.id:
            fail(f"self.{name} requires {node.annotation.id}, got {typ}")
        declare_field(fc, name, typ, persist)
        return (InitAppField(name, initial),)
    if (
        isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and (name := field_name(node.targets[0])) is not None
    ):
        if (
            fc.branch_depth
            or not isinstance(node.value, ast.Name)
            or fc.symbols.get(node.value.id) not in VIEWS
        ):
            fail(
                "initialize scalar self fields with annotations; widget fields alias a declared view outside branches"
            )
        declare_field(fc, name, fc.symbols[node.value.id], False)
        fc.widget_origins[name] = node.value.id
        return (StoreAppField(name, node.value.id),)
    if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
        return None
    call = node.value
    if not isinstance(call.func, ast.Attribute):
        return None
    receiver = call.func.value
    if call.func.attr == "on_click":
        button = (
            receiver.id
            if isinstance(receiver, ast.Name)
            else fc.widget_origins.get(field_name(receiver))
        )
        if button is None:
            fail("bind on_click on a declared Button or its self reference")
        fc.require(button, "Button", node)
        handler = field_name(call.args[0]) if len(call.args) == 1 else None
        if fc.branch_depth or call.keywords or handler not in fc.event_methods:
            fail(
                "bind button.on_click(self.handler) outside branches; do not call the handler here"
            )
        if button in fc.click_bound:
            fail("each button has one click handler")
        fc.click_bound.add(button)
        return (BindClick(button, handler),)
    if (
        isinstance(receiver, ast.Name)
        and receiver.id == "self"
        and call.func.attr in fc.event_methods
    ):
        if call.args or call.keywords:
            fail("Activity handlers take no arguments")
        fc.event_calls.append((call.func.attr, frozenset(fc.app_fields), node.lineno))
        return (CallEvent(call.func.attr),)
    return None


def declare_field(fc, name, typ, persist):
    if (
        name in fc.app_fields
        or name in fc.event_methods
        or name in {"on_create", "state", "self", "recreate", "set_content_view"}
        or name.startswith("__")
    ):
        fail(f"duplicate/reserved Activity field {name!r}")
    if len(fc.app_fields) >= 32:
        fail("at most 32 Activity fields are supported")
    fc.app_fields[name] = AppField(name, typ, persist)


class HandlerCompiler:
    def __init__(self, fc):
        self.fc = fc
        self.locals = {}
        self.required = set()
        self.calls = set()
        self.recreates = False

    def field(self, name):
        if name not in self.fc.app_fields:
            fail(f"undefined Activity field self.{name}; initialize it in on_create")
        self.required.add(name)
        return self.fc.app_fields[name].type_name

    def expression(self, node, env, depth=0):
        if depth > 16:
            fail("callback expression is too deeply nested")

        def expr(child):
            return self.expression(child, env, depth + 1)

        if isinstance(node, ast.Constant) or (
            isinstance(node, ast.UnaryOp)
            and isinstance(node.op, (ast.USub, ast.UAdd))
            and isinstance(node.operand, ast.Constant)
        ):
            typ, value = literal(node)
            return EventExpr("constant", typ, value)
        if isinstance(node, ast.Name):
            if node.id not in env:
                fail(
                    f"local {node.id!r} is not definitely initialized; lifecycle locals must be retained on self"
                )
            return EventExpr("local", env[node.id], node.id)
        if (name := field_name(node)) is not None:
            typ = self.field(name)
            if typ not in SCALARS:
                fail("widget references can only be used as method receivers")
            return EventExpr("field", typ, name)
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub)):
            left, right = expr(node.left), expr(node.right)
            operator = "+" if isinstance(node.op, ast.Add) else "-"
            if left.type_name != right.type_name or left.type_name not in (
                {"int", "str"} if operator == "+" else {"int"}
            ):
                fail("+ supports two ints or two strings; - supports two ints")
            return EventExpr("binary", left.type_name, operator, (left, right))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.Not, ast.USub, ast.UAdd)):
            value = expr(node.operand)
            if isinstance(node.op, ast.Not):
                return EventExpr("not", "bool", args=(value,))
            if value.type_name != "int":
                fail("unary + / - requires int")
            return (
                value
                if isinstance(node.op, ast.UAdd)
                else EventExpr("binary", "int", "-", (EventExpr("constant", "int", 0), value))
            )
        if isinstance(node, ast.BoolOp):
            values = tuple(expr(x) for x in node.values)
            if any(x.type_name != "bool" for x in values):
                fail("and/or operands must be bool in this subset")
            return EventExpr(
                "bool_op", "bool", "and" if isinstance(node.op, ast.And) else "or", values
            )
        if isinstance(node, ast.Compare) and len(node.ops) == 1:
            left, right = expr(node.left), expr(node.comparators[0])
            operators = {
                ast.Eq: "==",
                ast.NotEq: "!=",
                ast.Lt: "<",
                ast.LtE: "<=",
                ast.Gt: ">",
                ast.GtE: ">=",
            }
            operator = operators.get(type(node.ops[0]))
            if (
                operator is None
                or left.type_name != right.type_name
                or (left.type_name != "int" and operator not in {"==", "!="})
            ):
                fail("compare matching types; ordering requires int")
            return EventExpr("compare", "bool", operator, (left, right))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in {"str", "bool"} and len(node.args) == 1 and not node.keywords:
                value = expr(node.args[0])
                return EventExpr(
                    "to_string" if node.func.id == "str" else "truth", node.func.id, args=(value,)
                )
            if node.func.id in self.fc.functions:
                signature = self.fc.functions[node.func.id]
                args = tuple(expr(arg) for arg in node.args)
                if (
                    node.keywords
                    or len(args) != len(signature.parameters)
                    or any(arg.type_name != "int" for arg in args)
                ):
                    fail(
                        "integer helpers require their declared number of positional int arguments"
                    )
                return EventExpr("helper", "int", node.func.id, args)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            receiver = field_name(node.func.value)
            if (
                receiver is not None
                and node.func.attr in {"get_text", "is_enabled"}
                and not node.args
                and not node.keywords
            ):
                typ = self.field(receiver)
                if (node.func.attr == "get_text" and typ not in TEXT_VIEWS) or (
                    node.func.attr == "is_enabled" and typ not in VIEWS
                ):
                    fail(f"{node.func.attr} is unsupported for {typ}")
                return EventExpr(
                    "get_text" if node.func.attr == "get_text" else "is_enabled",
                    "str" if node.func.attr == "get_text" else "bool",
                    receiver,
                )
        fail(
            "unsupported callback expression; use typed fields/locals, +/-, comparisons, str/bool or native getters"
        )

    def assign(self, target, value, env, annotation=None):
        if (name := field_name(target)) is not None:
            typ = self.field(name)
            if annotation is not None or typ not in SCALARS:
                fail("declare fields in on_create; widget references cannot be rebound in handlers")
            if value.type_name != typ:
                fail(f"self.{name} requires {typ}, got {value.type_name}")
            return EventAssign("field", name, value)
        if not isinstance(target, ast.Name):
            fail("callback assignment requires a scalar local or declared self field")
        name = target.id
        if name in {
            "self",
            "state",
            "str",
            "int",
            "bool",
            *self.fc.imported,
            *self.fc.functions,
            *self.fc.event_methods,
        }:
            fail(f"local {name!r} shadows a reserved name")
        if annotation is not None:
            if (
                name in env
                or not isinstance(annotation, ast.Name)
                or annotation.id not in SCALARS
                or annotation.id != value.type_name
            ):
                fail(
                    "annotated callback locals must be newly initialized with their matching scalar type"
                )
        if (name in self.locals and self.locals[name] != value.type_name) or (
            name in env and env[name] != value.type_name
        ):
            fail(f"callback local {name!r} cannot change type")
        self.locals[name] = value.type_name
        env[name] = value.type_name
        if len(self.locals) > 8:
            fail(
                "callbacks support at most 8 scalar locals; use Activity fields for retained state"
            )
        return EventAssign("local", name, value)

    def action(self, call, env):
        if (
            not isinstance(call, ast.Call)
            or not isinstance(call.func, ast.Attribute)
            or call.keywords
        ):
            fail("callback statements use declared Activity/widget methods")
        receiver, method = call.func.value, call.func.attr
        if isinstance(receiver, ast.Name) and receiver.id == "self":
            if call.args:
                fail("Activity event methods take no arguments")
            if method in self.fc.event_methods:
                self.calls.add(method)
                return EventAction(None, method)
            if method == "recreate":
                self.recreates = True
                return EventAction(None, "recreate")
            fail("unknown Activity callback method")
        name = field_name(receiver)
        typ = self.field(name)
        if method == "set_text_color" and typ in TEXT_VIEWS and len(call.args) == 1:
            try:
                color = parse_color(ast.literal_eval(call.args[0]))
            except (ValueError, TypeError):
                fail("runtime set_text_color currently requires a literal Anpyra color")
            return EventAction(name, method, (EventExpr("constant", "int", color),))
        values = tuple(self.expression(x, env) for x in call.args)
        if (
            method == "set_text"
            and typ in TEXT_VIEWS
            and len(values) == 1
            and values[0].type_name == "str"
        ):
            return EventAction(name, method, values)
        if (
            method == "set_enabled"
            and typ in VIEWS
            and len(values) == 1
            and values[0].type_name == "bool"
        ):
            return EventAction(name, method, values)
        fail("runtime widgets support set_text(str), set_enabled(bool) and literal set_text_color")

    def statements(self, nodes, env):
        ops, terminated = [], False
        for node in nodes:
            try:
                if terminated:
                    fail("unreachable statement after return")
                if isinstance(node, ast.Pass) or (
                    isinstance(node, ast.Expr)
                    and isinstance(node.value, ast.Constant)
                    and isinstance(node.value.value, str)
                ):
                    continue
                if isinstance(node, ast.Assign) and len(node.targets) == 1:
                    target = node.targets[0]
                    if (
                        isinstance(target, ast.Attribute)
                        and target.attr == "text"
                        and field_name(target.value) is not None
                    ):
                        call = ast.Call(
                            func=ast.Attribute(value=target.value, attr="set_text"),
                            args=[node.value],
                            keywords=[],
                        )
                        ops.append(self.action(call, env))
                    else:
                        ops.append(self.assign(target, self.expression(node.value, env), env))
                elif isinstance(node, ast.AnnAssign) and node.value is not None:
                    ops.append(
                        self.assign(
                            node.target, self.expression(node.value, env), env, node.annotation
                        )
                    )
                elif isinstance(node, ast.AugAssign) and isinstance(node.op, (ast.Add, ast.Sub)):
                    binary = ast.BinOp(left=node.target, op=node.op, right=node.value)
                    ops.append(self.assign(node.target, self.expression(binary, env), env))
                elif isinstance(node, ast.Expr):
                    ops.append(self.action(node.value, env))
                elif isinstance(node, ast.Return) and (
                    node.value is None
                    or (isinstance(node.value, ast.Constant) and node.value.value is None)
                ):
                    ops.append(EventReturn())
                    terminated = True
                elif isinstance(node, ast.If):
                    condition = self.expression(node.test, env)
                    then_ops, then_env, then_return = self.statements(node.body, dict(env))
                    else_ops, else_env, else_return = self.statements(node.orelse, dict(env))
                    live = [
                        branch
                        for branch, ended in ((then_env, then_return), (else_env, else_return))
                        if not ended
                    ]
                    if live:
                        common = set.intersection(*(set(branch) for branch in live))
                        env = {name: live[0][name] for name in common}
                    terminated = then_return and else_return
                    ops.append(EventIf(condition, then_ops, else_ops))
                else:
                    fail(f"unsupported callback statement {type(node).__name__}")
            except StyleError as exc:
                raise StyleError(f"line {node.lineno}: {exc}") from exc
        return tuple(ops), env, terminated


def finalize(fc, operations):
    handlers, compilers = [], {}
    for name, node in fc.event_methods.items():
        compiler = HandlerCompiler(fc)
        ops, _, _ = compiler.statements(node.body, {})
        compilers[name] = compiler
        handlers.append(EventHandler(name, ops, tuple(compiler.locals.items())))
    requirements, recreates = {}, {}

    def visit(name, stack=()):
        if name in stack:
            fail("recursive callback call graph: " + " -> ".join((*stack, name)))
        if name in requirements:
            return requirements[name]
        compiler = compilers[name]
        required = set(compiler.required)
        has_recreate = compiler.recreates
        for called in compiler.calls:
            required.update(visit(called, (*stack, name)))
            has_recreate |= recreates[called]
        requirements[name], recreates[name] = required, has_recreate
        return required

    for name in compilers:
        visit(name)
    roots = {op.handler for op in operations if isinstance(op, BindClick)} | {
        name for name, _, _ in fc.event_calls
    }
    reachable = set()

    def reach(name):
        if name not in reachable:
            reachable.add(name)
            for called in compilers[name].calls:
                reach(called)

    for name in roots:
        reach(name)
    if set(compilers) - reachable:
        fail(
            "Activity methods must be bound or called: "
            + ", ".join(sorted(set(compilers) - reachable))
        )
    for name, initialized, line in fc.event_calls:
        missing = requirements[name] - initialized
        if missing:
            fail(
                f"line {line}: {name} uses Activity fields before initialization: {', '.join(sorted(missing))}"
            )
        if recreates[name]:
            fail(f"line {line}: recreate must only run from a click callback")
    chat = next((op for op in operations if isinstance(op, BindChatSession)), None)
    if chat and fc.click_bound.intersection({chat.send_button, chat.clear_button}):
        fail("ChatSession owns its send/clear buttons; bind generic handlers to separate buttons")
    return tuple(fc.app_fields.values()), tuple(handlers)
