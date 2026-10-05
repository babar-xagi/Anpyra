# Adapted from the user-provided PyAndroid experiments for Anpyra.
from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

from .ir import (
    AppIR,
    CallFunction,
    CallSuperOnCreate,
    FunctionIR,
    IfBool,
    IfCompare,
    IntBinary,
    LoadConst,
    NewTextView,
    ReturnValue,
    SetContentView,
    SetText,
)


class CompileError(ValueError):
    pass


@dataclass(frozen=True)
class CompileResult:
    source_path: Path
    ast_tree: ast.Module
    ir: AppIR


def _line(node: ast.AST) -> str:
    n = getattr(node, "lineno", None)
    return f"line {n}: " if n is not None else ""


def _is_name(node: ast.AST, name: str) -> bool:
    return isinstance(node, ast.Name) and node.id == name


def _require_imports(tree: ast.Module) -> None:
    imported = set()
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            if node.level or node.module not in {"anpyra", "pyandroid"}:
                raise CompileError(
                    f"{_line(node)}only imports from anpyra or pyandroid are supported"
                )
            for alias in node.names:
                if alias.asname or alias.name not in {"Activity", "TextView"}:
                    raise CompileError(f"{_line(node)}import Activity and TextView without aliases")
                imported.add(alias.name)
        elif not isinstance(node, (ast.FunctionDef, ast.ClassDef)) and not _is_docstring(node):
            raise CompileError(f"{_line(node)}unsupported module statement: {type(node).__name__}")
    if {"Activity", "TextView"} - imported:
        raise CompileError(
            "app source must import Activity and TextView from anpyra (or pyandroid)"
        )


def _is_docstring(node):
    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    )


def _int_literal(node):
    if isinstance(node, ast.Constant) and type(node.value) is int:
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        if isinstance(node.operand, ast.Constant) and type(node.operand.value) is int:
            return -node.operand.value if isinstance(node.op, ast.USub) else node.operand.value
    return None


def _find_activity_class(tree: ast.Module) -> ast.ClassDef:
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
    if (
        len(classes) != 1
        or len(classes[0].bases) != 1
        or not _is_name(classes[0].bases[0], "Activity")
    ):
        raise CompileError("Anpyra v0.1 requires exactly one class extending Activity")
    cls = classes[0]
    if cls.decorator_list or cls.keywords or getattr(cls, "type_params", []):
        raise CompileError(
            f"{_line(cls)}Activity decorators, class keywords and type parameters are unsupported"
        )
    for node in cls.body:
        if not _is_docstring(node) and not (
            isinstance(node, ast.FunctionDef) and node.name == "on_create"
        ):
            raise CompileError(f"{_line(node)}Activity body supports only on_create and docstrings")
    return cls


def _find_on_create(cls: ast.ClassDef) -> ast.FunctionDef:
    methods = [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "on_create"]
    if len(methods) != 1:
        raise CompileError(f"{cls.name} must define exactly one on_create(self, state)")
    fn = methods[0]
    args = fn.args.posonlyargs + fn.args.args
    if (
        len(args) != 2
        or args[0].arg != "self"
        or args[1].arg != "state"
        or fn.args.vararg
        or fn.args.kwarg
        or fn.args.kwonlyargs
        or fn.args.defaults
    ):
        raise CompileError(f"{_line(fn)}expected: def on_create(self, state):")
    if fn.decorator_list or getattr(fn, "type_params", []):
        raise CompileError(f"{_line(fn)}on_create decorators and type parameters are unsupported")
    return fn


def _annotation_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name) and node.id in {"str", "int", "bool"}:
        return node.id
    raise CompileError(f"{_line(node)}supported annotations are str, int, and bool")


def _constant_type(value):
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, str):
        return "str"
    return None


COMPARE_OPS = {
    ast.Eq: "==",
    ast.NotEq: "!=",
    ast.Lt: "<",
    ast.LtE: "<=",
    ast.Gt: ">",
    ast.GtE: ">=",
}


@dataclass(frozen=True)
class FunctionSignature:
    name: str
    parameters: tuple[tuple[str, str], ...]
    return_type: str


def _collect_function_signatures(tree: ast.Module) -> dict[str, FunctionSignature]:
    out = {}
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        if node.decorator_list or getattr(node, "type_params", []):
            raise CompileError(f"{_line(node)}decorators are not supported in Anpyra v0.1")
        if node.name in {"Activity", "TextView"}:
            raise CompileError(f"{_line(node)}function name {node.name!r} shadows the Android API")
        if node.name in out:
            raise CompileError(f"{_line(node)}duplicate function {node.name!r}")
        args = node.args.posonlyargs + node.args.args
        if len({arg.arg for arg in args}) != len(args):
            raise CompileError(f"{_line(node)}duplicate function parameter")
        if node.args.vararg or node.args.kwarg or node.args.kwonlyargs or node.args.defaults:
            raise CompileError(
                f"{_line(node)}functions use simple required positional parameters only"
            )
        if len(args) > 5:
            raise CompileError(f"{_line(node)}functions currently support at most 5 parameters")
        params = []
        for arg in args:
            if arg.annotation is None or _annotation_name(arg.annotation) != "int":
                raise CompileError(f"{_line(arg)}function parameters must be annotated int")
            params.append((arg.arg, "int"))
        if node.returns is None or _annotation_name(node.returns) != "int":
            raise CompileError(f"{_line(node)}top-level functions must declare -> int")
        out[node.name] = FunctionSignature(node.name, tuple(params), "int")
    return out


class HelperCompiler:
    def __init__(self, sig: FunctionSignature):
        self.sig = sig
        self.symbols = {name: typ for name, typ in sig.parameters}
        self.synthetic_counter = 0

    def synthetic(self, typ, value=None):
        name = f"${typ}{self.synthetic_counter}"
        self.synthetic_counter += 1
        self.symbols[name] = typ
        return name

    def require_int(self, name, node):
        if self.symbols.get(name) != "int":
            raise CompileError(f"{_line(node)}{name!r} must be int")

    def int_operand(self, node):
        if isinstance(node, ast.Name):
            self.require_int(node.id, node)
            return node.id, ()
        value = _int_literal(node)
        if value is not None:
            if not -32768 <= value <= 32767:
                raise CompileError(f"{_line(node)}int literal must fit signed 16-bit")
            name = self.synthetic("int")
            return name, (LoadConst(name, "int", value),)
        raise CompileError(f"{_line(node)}function return expressions expect int names/literals")

    def compile_return_expr(self, node):
        if isinstance(node, ast.Name):
            self.require_int(node.id, node)
            return (ReturnValue(node.id),)
        value = _int_literal(node)
        if value is not None:
            if not -32768 <= value <= 32767:
                raise CompileError(f"{_line(node)}int literal must fit signed 16-bit")
            name = self.synthetic("int")
            return (LoadConst(name, "int", value), ReturnValue(name))
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub)):
            left, lops = self.int_operand(node.left)
            right, rops = self.int_operand(node.right)
            target = self.synthetic("int")
            op = "+" if isinstance(node.op, ast.Add) else "-"
            return (
                *lops,
                *rops,
                IntBinary(target, left, op, right),
                ReturnValue(target),
            )
        raise CompileError(
            f"{_line(node)}function return supports int name/literal or + / - expression"
        )

    def compile(self, node: ast.FunctionDef) -> FunctionIR:
        body = [
            x
            for x in node.body
            if not (
                isinstance(x, ast.Expr)
                and isinstance(x.value, ast.Constant)
                and isinstance(x.value.value, str)
            )
        ]
        if len(body) != 1 or not isinstance(body[0], ast.Return) or body[0].value is None:
            raise CompileError(
                f"{_line(node)}Anpyra v0.1 function body must contain exactly one return expression"
            )
        ops = self.compile_return_expr(body[0].value)
        return FunctionIR(
            node.name,
            self.sig.parameters,
            "int",
            tuple(ops),
            tuple(self.symbols.items()),
        )


class FunctionCompiler:
    def __init__(self, functions: dict[str, FunctionSignature]):
        self.functions = functions
        self.symbols: dict[str, str] = {}
        self.synthetic_counter = 0

    def declare(self, name, typ, node):
        if name in {"self", "state", "Activity", "TextView"} or name in self.functions:
            raise CompileError(f"{_line(node)}variable {name!r} shadows a reserved name")
        if name in self.symbols:
            raise CompileError(f"{_line(node)}variable {name!r} is already declared")
        self.symbols[name] = typ

    def require(self, name, expected, node):
        actual = self.symbols.get(name)
        if actual is None:
            raise CompileError(f"{_line(node)}undefined variable {name!r}")
        if actual != expected:
            raise CompileError(f"{_line(node)}{name!r} has type {actual}, expected {expected}")

    def synthetic(self, typ, value):
        name = f"${typ}{self.synthetic_counter}"
        self.synthetic_counter += 1
        self.symbols[name] = typ
        return name, LoadConst(name, typ, value)

    def int_operand(self, node):
        if isinstance(node, ast.Name):
            self.require(node.id, "int", node)
            return node.id, ()
        value = _int_literal(node)
        if value is not None:
            if not -32768 <= value <= 32767:
                raise CompileError(f"{_line(node)}int literal must fit signed 16-bit")
            name, load = self.synthetic("int", value)
            return name, (load,)
        raise CompileError(f"{_line(node)}expected int variable or literal")

    def compile_call_into(self, target, node: ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in self.functions:
            raise CompileError(f"{_line(node)}unknown compiled function call")
        sig = self.functions[node.func.id]
        if node.keywords or len(node.args) != len(sig.parameters):
            raise CompileError(
                f"{_line(node)}{sig.name} expects {len(sig.parameters)} positional arguments"
            )
        arg_names = []
        ops = []
        for arg, (_, expected) in zip(node.args, sig.parameters):
            if expected != "int":
                raise CompileError("internal function signature error")
            name, pre = self.int_operand(arg)
            ops.extend(pre)
            arg_names.append(name)
        return (*ops, CallFunction(target, sig.name, tuple(arg_names)))

    def compile_int_value_into(self, target, node):
        if isinstance(node, ast.Call):
            return self.compile_call_into(target, node)
        value = _int_literal(node)
        if value is not None:
            if not -32768 <= value <= 32767:
                raise CompileError(f"{_line(node)}int literal must fit signed 16-bit")
            return (LoadConst(target, "int", value),)
        if isinstance(node, ast.Name):
            self.require(node.id, "int", node)
            zero, load = self.synthetic("int", 0)
            return (load, IntBinary(target, node.id, "+", zero))
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub)):
            left, lops = self.int_operand(node.left)
            right, rops = self.int_operand(node.right)
            return (
                *lops,
                *rops,
                IntBinary(target, left, "+" if isinstance(node.op, ast.Add) else "-", right),
            )
        raise CompileError(
            f"{_line(node)}int value supports literals, names, +, -, or compiled function calls"
        )

    def compile_ann_assign(self, node):
        if not isinstance(node.target, ast.Name) or node.value is None:
            raise CompileError(f"{_line(node)}simple initialized annotated locals required")
        name = node.target.id
        typ = _annotation_name(node.annotation)
        if typ == "int":
            operations = self.compile_int_value_into(name, node.value)
            self.declare(name, typ, node)
            return operations
        if not isinstance(node.value, ast.Constant):
            raise CompileError(f"{_line(node)}{typ} currently requires literal constant")
        actual = _constant_type(node.value.value)
        if actual != typ:
            raise CompileError(f"{_line(node)}cannot assign {actual} to {name}: {typ}")
        self.declare(name, typ, node)
        return (LoadConst(name, typ, node.value.value),)

    def compile_assignment(self, node):
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            raise CompileError(f"{_line(node)}simple assignments only")
        target = node.targets[0].id
        call = node.value
        if not (
            isinstance(call, ast.Call)
            and _is_name(call.func, "TextView")
            and len(call.args) == 1
            and _is_name(call.args[0], "self")
            and not call.keywords
        ):
            raise CompileError(f"{_line(node)}supported untyped assignment: name = TextView(self)")
        self.declare(target, "TextView", node)
        return (NewTextView(target),)

    def compile_expr(self, node):
        call = node.value
        if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Attribute):
            raise CompileError(f"{_line(node)}unsupported expression")
        receiver = call.func.value
        attr = call.func.attr
        if (
            attr == "set_text"
            and isinstance(receiver, ast.Name)
            and len(call.args) == 1
            and not call.keywords
        ):
            self.require(receiver.id, "TextView", node)
            arg = call.args[0]
            if isinstance(arg, ast.Name):
                self.require(arg.id, "str", node)
                return (SetText(receiver.id, arg.id),)
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                temp, load = self.synthetic("str", arg.value)
                return (load, SetText(receiver.id, temp))
            raise CompileError(f"{_line(node)}set_text accepts str variable or literal")
        if (
            attr == "set_content_view"
            and _is_name(receiver, "self")
            and len(call.args) == 1
            and isinstance(call.args[0], ast.Name)
            and not call.keywords
        ):
            self.require(call.args[0].id, "TextView", node)
            return (SetContentView(call.args[0].id),)
        raise CompileError(f"{_line(node)}unsupported method call")

    def compile_condition(self, node, body, orelse):
        if isinstance(node, ast.Name):
            self.require(node.id, "bool", node)
            return (
                IfBool(
                    node.id,
                    tuple(self.compile_branch(body)),
                    tuple(self.compile_branch(orelse)),
                ),
            )
        if isinstance(node, ast.Compare):
            if (
                len(node.ops) != 1
                or len(node.comparators) != 1
                or type(node.ops[0]) not in COMPARE_OPS
            ):
                raise CompileError(f"{_line(node)}single supported comparison required")
            left, lops = self.int_operand(node.left)
            right, rops = self.int_operand(node.comparators[0])
            return (
                *lops,
                *rops,
                IfCompare(
                    left,
                    COMPARE_OPS[type(node.ops[0])],
                    right,
                    tuple(self.compile_branch(body)),
                    tuple(self.compile_branch(orelse)),
                ),
            )
        raise CompileError(f"{_line(node)}if condition must be bool or int comparison")

    def compile_branch(self, stmts):
        ops = []
        for s in stmts:
            if isinstance(s, ast.Pass):
                continue
            if isinstance(s, ast.Expr):
                ops.extend(self.compile_expr(s))
                continue
            if isinstance(s, ast.If):
                ops.extend(self.compile_condition(s.test, s.body, s.orelse))
                continue
            raise CompileError(f"{_line(s)}branches support method calls and nested if/elif")
        return ops

    def compile_statement(self, node):
        if isinstance(node, ast.AnnAssign):
            return self.compile_ann_assign(node)
        if isinstance(node, ast.Assign):
            return self.compile_assignment(node)
        if isinstance(node, ast.Expr):
            if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                return ()
            return self.compile_expr(node)
        if isinstance(node, ast.If):
            return self.compile_condition(node.test, node.body, node.orelse)
        raise CompileError(f"{_line(node)}unsupported statement: {type(node).__name__}")


def _count_content_view(ops):
    total = 0
    for op in ops:
        if isinstance(op, SetContentView):
            total += 1
        elif isinstance(op, (IfBool, IfCompare)):
            total += _count_content_view(op.then_ops) + _count_content_view(op.else_ops)
    return total


def _compile_source(source: str, *, source_path: Path, package: str, label: str) -> CompileResult:
    try:
        tree = ast.parse(source, filename=str(source_path))
    except SyntaxError as exc:
        raise CompileError(f"Python syntax error: {exc}") from exc
    _require_imports(tree)
    signatures = _collect_function_signatures(tree)
    class_node = _find_activity_class(tree)
    if class_node.name in signatures:
        raise CompileError(f"{_line(class_node)}Activity name shadows a compiled function")
    on_create = _find_on_create(class_node)

    helper_irs = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            helper_irs.append(HelperCompiler(signatures[node.name]).compile(node))

    fc = FunctionCompiler(signatures)
    operations = [CallSuperOnCreate()]
    for node in on_create.body:
        operations.extend(fc.compile_statement(node))
    if _count_content_view(operations) != 1 or not any(
        isinstance(op, SetContentView) for op in operations
    ):
        raise CompileError(
            "on_create must call self.set_content_view(view) exactly once, outside branches"
        )
    if "TextView" not in fc.symbols.values():
        raise CompileError("on_create must create at least one TextView")
    if len(fc.symbols) > 14:
        raise CompileError(
            "on_create exceeds 14 registers for locals and temporary values in Anpyra v0.1"
        )
    ir = AppIR(
        package,
        class_node.name,
        label,
        tuple(helper_irs),
        tuple(operations),
        tuple(fc.symbols.items()),
    )
    return CompileResult(source_path, tree, ir)


def compile_source(
    source: str,
    *,
    source_path: Path = Path("app.py"),
    package: str = "dev.anpyra.app",
    label: str = "Anpyra",
) -> CompileResult:
    from ..config import ApplicationMetadata

    ApplicationMetadata(package=package, label=label)
    try:
        return _compile_source(source, source_path=Path(source_path), package=package, label=label)
    except CompileError as exc:
        raise CompileError(f"{source_path}: {exc}") from exc


def compile_file(
    path: Path, *, package: str = "dev.anpyra.app", label: str = "Anpyra"
) -> CompileResult:
    return compile_source(
        path.read_text(encoding="utf-8"), source_path=path, package=package, label=label
    )
