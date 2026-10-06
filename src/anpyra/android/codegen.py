"""Compile checked IR into lifecycle, constructor and helper method code."""

from __future__ import annotations

from dataclasses import dataclass

from ..compiler.ir import (
    AppIR,
    ApplyScreenBackground,
    CallFunction,
    IfBool,
    IfCompare,
    IntBinary,
    LoadConst,
    NewScreen,
    ReturnValue,
    SetTextColor,
)
from .backgrounds import emit_background
from .dalvik import (
    OP_ADD_INT,
    OP_IF_EQ,
    OP_IF_GE,
    OP_IF_GT,
    OP_IF_LE,
    OP_IF_LT,
    OP_IF_NE,
    OP_INVOKE_DIRECT,
    OP_INVOKE_STATIC,
    OP_RETURN_VOID,
    OP_SUB_INT,
    Assembler,
    emit_const,
    emit_invoke,
    encode_invoke_35c,
    make_code_item,
)
from .dex_types import MethodListing
from .screen import emit_screen_operation


@dataclass(frozen=True)
class GeneratedMethods:
    constructor_code: bytes
    lifecycle_code: bytes
    helper_codes: tuple
    register_map: tuple[tuple[str, str, int], ...]
    code_units: int
    assembly_listing: tuple[str, ...]
    listings: tuple[MethodListing, ...]


def _walk_ops(ops):
    for op in ops:
        yield op
        if isinstance(op, (IfBool, IfCompare)):
            yield from _walk_ops(op.then_ops)
            yield from _walk_ops(op.else_ops)


def generate_methods(
    app: AppIR, tidx, sidx, midx, helper_keys, screen_refs, field_indexes=None
) -> GeneratedMethods:
    act_ctor = screen_refs["activity_constructor"]
    # Main register map.
    symbols = list(app.symbol_types)
    if len(symbols) + 2 > 16:
        raise ValueError("Anpyra v0.1 on_create supports at most 14 locals")
    wide = any(isinstance(op, (NewScreen, SetTextColor)) for op in _walk_ops(app.operations))
    offset = 2 if wide else 0
    reg_of = {n: i + offset for i, (n, _) in enumerate(symbols)}
    scratch = tuple(range(offset + len(symbols), offset + len(symbols) + 7)) if wide else ()
    argument_base = offset + len(symbols) + 7 if wide else None
    this_reg = argument_base + 5 if wide else len(symbols)
    state_reg = this_reg + 1
    main_regs = state_reg + 1
    main_asm = Assembler()
    inverse = {
        "==": (OP_IF_NE, "if-ne"),
        "!=": (OP_IF_EQ, "if-eq"),
        "<": (OP_IF_GE, "if-ge"),
        "<=": (OP_IF_GT, "if-gt"),
        ">": (OP_IF_LE, "if-le"),
        ">=": (OP_IF_LT, "if-lt"),
    }

    def emit_main(ops):
        for op in ops:
            if isinstance(op, ApplyScreenBackground):
                emit_background(
                    op,
                    main_asm,
                    reg_of,
                    this_reg,
                    tidx,
                    sidx,
                    midx,
                    field_indexes or {},
                    screen_refs,
                    scratch,
                    argument_base,
                )
                continue
            if emit_screen_operation(
                op,
                main_asm,
                reg_of,
                this_reg,
                state_reg,
                tidx,
                midx,
                screen_refs,
                argument_base,
                scratch,
                field_indexes,
            ):
                continue
            elif isinstance(op, LoadConst):
                r = reg_of[op.target]
                if op.type_name == "str":
                    main_asm.emit("const_string", r, sidx[op.value], op.value, size=2)
                elif op.type_name == "bool":
                    emit_const(main_asm, r, 1 if op.value else 0)
                elif op.type_name == "int":
                    emit_const(main_asm, r, op.value)
            elif isinstance(op, IntBinary):
                main_asm.emit(
                    "int_binop",
                    OP_ADD_INT if op.operator == "+" else OP_SUB_INT,
                    reg_of[op.target],
                    reg_of[op.left_var],
                    reg_of[op.right_var],
                    "add-int" if op.operator == "+" else "sub-int",
                    size=2,
                )
            elif isinstance(op, CallFunction):
                key = helper_keys[op.function_name]
                regs = tuple(reg_of[x] for x in op.args)
                emit_invoke(
                    main_asm,
                    OP_INVOKE_STATIC,
                    midx[key],
                    regs,
                    key.parameters,
                    argument_base,
                    f"{op.function_name}(" + ",".join("I" for _ in regs) + ")I",
                )
                main_asm.emit("move_result", reg_of[op.target], size=1)
            elif isinstance(op, IfBool):
                el = main_asm.new_label("if_else")
                end = main_asm.new_label("if_end")
                main_asm.emit(
                    "if_eqz",
                    reg_of[op.condition_var],
                    el if op.else_ops else end,
                    size=2,
                )
                emit_main(op.then_ops)
                if op.else_ops:
                    main_asm.emit("goto16", end, size=2)
                    main_asm.label(el)
                    emit_main(op.else_ops)
                main_asm.label(end)
            elif isinstance(op, IfCompare):
                el = main_asm.new_label("cmp_else")
                end = main_asm.new_label("cmp_end")
                opc, mn = inverse[op.operator]
                main_asm.emit(
                    "if_test",
                    opc,
                    reg_of[op.left_var],
                    reg_of[op.right_var],
                    el if op.else_ops else end,
                    mn,
                    size=2,
                )
                emit_main(op.then_ops)
                if op.else_ops:
                    main_asm.emit("goto16", end, size=2)
                    main_asm.label(el)
                    emit_main(op.else_ops)
                main_asm.label(end)

    emit_main(app.operations)
    main_asm.emit("return_void", size=1)
    main_words, main_listing = main_asm.assemble()
    main_outs = max(
        [2] + [len(op.args) for op in _walk_ops(app.operations) if isinstance(op, CallFunction)]
    )
    if wide:
        main_outs = max(main_outs, 5)
    main_code = make_code_item(
        registers_size=main_regs, ins_size=2, outs_size=main_outs, insns=main_words
    )

    # Constructor.
    ctor_words = encode_invoke_35c(OP_INVOKE_DIRECT, midx[act_ctor], [0]) + [OP_RETURN_VOID]
    ctor_code = make_code_item(registers_size=1, ins_size=1, outs_size=1, insns=ctor_words)

    # Helper methods: params occupy high registers in static method frame.
    helper_codes = []
    method_listings = []
    for fn in app.functions:
        param_names = [n for n, _ in fn.parameters]
        locals_ = [(n, t) for n, t in fn.symbol_types if n not in param_names]
        if len(locals_) + len(param_names) > 16:
            raise ValueError(f"{fn.name} has too many registers for Anpyra v0.1")
        freg = {n: i for i, (n, _) in enumerate(locals_)}
        base = len(locals_)
        for i, n in enumerate(param_names):
            freg[n] = base + i
        fasm = Assembler()
        for op in fn.operations:
            if isinstance(op, LoadConst):
                r = freg[op.target]
                fasm.emit("const4", r, op.value, size=1) if -8 <= op.value <= 7 else fasm.emit(
                    "const16", r, op.value, size=2
                )
            elif isinstance(op, IntBinary):
                fasm.emit(
                    "int_binop",
                    OP_ADD_INT if op.operator == "+" else OP_SUB_INT,
                    freg[op.target],
                    freg[op.left_var],
                    freg[op.right_var],
                    "add-int" if op.operator == "+" else "sub-int",
                    size=2,
                )
            elif isinstance(op, ReturnValue):
                fasm.emit("return", freg[op.value_var], size=1)
            else:
                raise ValueError(f"unsupported helper IR {op!r}")
        fwords, flisting = fasm.assemble()
        fcode = make_code_item(
            registers_size=len(locals_) + len(param_names),
            ins_size=len(param_names),
            outs_size=0,
            insns=fwords,
        )
        regs = tuple(
            [(n, t, freg[n]) for n, t in locals_]
            + [(f"p{i}:{n}", t, freg[n]) for i, (n, t) in enumerate(fn.parameters)]
        )
        helper_codes.append((helper_keys[fn.name], fn, fcode, flisting, regs, len(fwords)))
        method_listings.append(MethodListing(fn.name, regs, len(fwords), flisting))

    main_map = tuple(
        [(n, t, reg_of[n]) for n, t in symbols]
        + [("p0:self", "MainActivity", this_reg), ("p1:state", "Bundle", state_reg)]
    )
    method_listings.append(MethodListing("onCreate", main_map, len(main_words), main_listing))
    return GeneratedMethods(
        ctor_code,
        main_code,
        tuple(helper_codes),
        main_map,
        len(main_words),
        main_listing,
        tuple(method_listings),
    )
