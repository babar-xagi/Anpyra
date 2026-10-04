# Adapted from the user-provided PyAndroid experiments for Anpyra.
from __future__ import annotations

import hashlib
import struct
import zlib
from dataclasses import dataclass

from .ir import (
    AppIR,
    CallFunction,
    CallSuperOnCreate,
    IfBool,
    IfCompare,
    IntBinary,
    LoadConst,
    NewTextView,
    ReturnValue,
    SetContentView,
    SetText,
)

DEX_MAGIC = b"dex\n035\x00"
HEADER_SIZE = 0x70
ENDIAN_CONSTANT = 0x12345678
NO_INDEX = 0xFFFFFFFF
ACC_PUBLIC = 0x0001
ACC_PROTECTED = 0x0004
ACC_STATIC = 0x0008
ACC_FINAL = 0x0010
ACC_CONSTRUCTOR = 0x10000
TYPE_HEADER_ITEM = 0x0000
TYPE_STRING_ID_ITEM = 0x0001
TYPE_TYPE_ID_ITEM = 0x0002
TYPE_PROTO_ID_ITEM = 0x0003
TYPE_METHOD_ID_ITEM = 0x0005
TYPE_CLASS_DEF_ITEM = 0x0006
TYPE_MAP_LIST = 0x1000
TYPE_TYPE_LIST = 0x1001
TYPE_CLASS_DATA_ITEM = 0x2000
TYPE_CODE_ITEM = 0x2001
TYPE_STRING_DATA_ITEM = 0x2002
OP_MOVE_RESULT = 0x0A
OP_RETURN_VOID = 0x0E
OP_RETURN = 0x0F
OP_CONST_4 = 0x12
OP_CONST_16 = 0x13
OP_CONST_STRING = 0x1A
OP_NEW_INSTANCE = 0x22
OP_GOTO_16 = 0x29
OP_IF_EQ = 0x32
OP_IF_NE = 0x33
OP_IF_LT = 0x34
OP_IF_GE = 0x35
OP_IF_GT = 0x36
OP_IF_LE = 0x37
OP_IF_EQZ = 0x38
OP_INVOKE_VIRTUAL = 0x6E
OP_INVOKE_SUPER = 0x6F
OP_INVOKE_DIRECT = 0x70
OP_INVOKE_STATIC = 0x71
OP_ADD_INT = 0x90
OP_SUB_INT = 0x91


def align(v, b=4):
    return (v + b - 1) & ~(b - 1)


def uleb128(v):
    out = bytearray()
    while True:
        x = v & 0x7F
        v >>= 7
        if v:
            out.append(x | 0x80)
        else:
            out.append(x)
            return bytes(out)


def utf16_code_units(s):
    r = s.encode("utf-16-le", errors="surrogatepass")
    return [int.from_bytes(r[i : i + 2], "little") for i in range(0, len(r), 2)]


def mutf8_encode(s):
    out = bytearray()
    for u in utf16_code_units(s):
        if u == 0:
            out += b"\xc0\x80"
        elif u <= 0x7F:
            out.append(u)
        elif u <= 0x7FF:
            out.extend((0xC0 | (u >> 6), 0x80 | (u & 0x3F)))
        else:
            out.extend((0xE0 | (u >> 12), 0x80 | ((u >> 6) & 0x3F), 0x80 | (u & 0x3F)))
    return bytes(out)


def dex_string_sort_key(s):
    return tuple(utf16_code_units(s))


def encode_21c(op, r, idx):
    return [op | (r << 8), idx]


def encode_invoke_35c(op, mid, regs):
    if len(regs) > 5 or any(not 0 <= r <= 15 for r in regs):
        raise ValueError("invoke-35c register/count limit")
    p = list(regs) + [0] * (5 - len(regs))
    c, d, e, f, g = p
    return [op | (g << 8) | (len(regs) << 12), mid, c | (d << 4) | (e << 8) | (f << 12)]


def make_code_item(*, registers_size, ins_size, outs_size, insns):
    return struct.pack(
        "<HHHHII", registers_size, ins_size, outs_size, 0, 0, len(insns)
    ) + struct.pack("<" + "H" * len(insns), *insns)


@dataclass(frozen=True)
class ProtoKey:
    return_type: str
    parameters: tuple[str, ...]


@dataclass(frozen=True)
class MethodKey:
    owner: str
    name: str
    return_type: str
    parameters: tuple[str, ...]


@dataclass(frozen=True)
class AsmInstruction:
    kind: str
    args: tuple
    size: int


@dataclass(frozen=True)
class Label:
    name: str


@dataclass(frozen=True)
class MethodListing:
    name: str
    registers: tuple[tuple[str, str, int], ...]
    code_units: int
    assembly: tuple[str, ...]


@dataclass(frozen=True)
class DexBuild:
    data: bytes
    register_map: tuple[tuple[str, str, int], ...]
    code_units: int
    assembly_listing: tuple[str, ...]
    methods: tuple[MethodListing, ...]


class Assembler:
    def __init__(self):
        self.items = []
        self.label_counter = 0

    def new_label(self, prefix):
        n = f"{prefix}_{self.label_counter}"
        self.label_counter += 1
        return n

    def label(self, n):
        self.items.append(Label(n))

    def emit(self, k, *args, size):
        self.items.append(AsmInstruction(k, tuple(args), size))

    def assemble(self):
        labels = {}
        pc = 0
        for i in self.items:
            if isinstance(i, Label):
                labels[i.name] = pc
            else:
                pc += i.size
        words = []
        listing = []
        pc = 0

        def s16(x):
            if not -32768 <= x <= 32767:
                raise ValueError("branch offset signed16 overflow")
            return x & 0xFFFF

        for i in self.items:
            if isinstance(i, Label):
                listing.append(f"{pc:04x}: <{i.name}>")
                continue
            k = i.kind
            a = i.args
            if k == "const4":
                r, v = a
                enc = [OP_CONST_4 | (r << 8) | ((v & 0xF) << 12)]
                text = f"const/4 v{r}, #{v}"
            elif k == "const16":
                r, v = a
                enc = [OP_CONST_16 | (r << 8), v & 0xFFFF]
                text = f"const/16 v{r}, #{v}"
            elif k == "const_string":
                r, idx, lit = a
                enc = encode_21c(OP_CONST_STRING, r, idx)
                text = f"const-string v{r}, {lit!r}"
            elif k == "new_instance":
                r, idx, desc = a
                enc = encode_21c(OP_NEW_INSTANCE, r, idx)
                text = f"new-instance v{r}, {desc}"
            elif k == "invoke":
                op, mid, regs, pretty = a
                enc = encode_invoke_35c(op, mid, list(regs))
                mn = {
                    OP_INVOKE_DIRECT: "invoke-direct",
                    OP_INVOKE_SUPER: "invoke-super",
                    OP_INVOKE_VIRTUAL: "invoke-virtual",
                    OP_INVOKE_STATIC: "invoke-static",
                }[op]
                text = f"{mn} {{{', '.join('v' + str(r) for r in regs)}}}, {pretty}"
            elif k == "move_result":
                (r,) = a
                enc = [OP_MOVE_RESULT | (r << 8)]
                text = f"move-result v{r}"
            elif k == "return":
                (r,) = a
                enc = [OP_RETURN | (r << 8)]
                text = f"return v{r}"
            elif k == "int_binop":
                op, destination, left, right, mn = a
                enc = [op | (destination << 8), left | (right << 8)]
                text = f"{mn} v{destination}, v{left}, v{right}"
            elif k == "if_test":
                op, left, right, t, mn = a
                off = labels[t] - pc
                enc = [op | (left << 8) | (right << 12), s16(off)]
                text = f"{mn} v{left}, v{right}, {t}  # offset {off:+d}"
            elif k == "if_eqz":
                r, t = a
                off = labels[t] - pc
                enc = [OP_IF_EQZ | (r << 8), s16(off)]
                text = f"if-eqz v{r}, {t}  # offset {off:+d}"
            elif k == "goto16":
                (t,) = a
                off = labels[t] - pc
                enc = [OP_GOTO_16, s16(off)]
                text = f"goto/16 {t}  # offset {off:+d}"
            elif k == "return_void":
                enc = [OP_RETURN_VOID]
                text = "return-void"
            else:
                raise ValueError(f"unknown asm {k}")
            if len(enc) != i.size:
                raise AssertionError(f"{k} size mismatch")
            listing.append(f"{pc:04x}: {text}")
            words.extend(enc)
            pc += i.size
        return words, tuple(listing)


def _shorty(p):
    def one(d):
        return "L" if d.startswith(("L", "[")) else d[0]

    return one(p.return_type) + "".join(one(x) for x in p.parameters)


def _walk_ops(ops):
    for op in ops:
        yield op
        if isinstance(op, (IfBool, IfCompare)):
            yield from _walk_ops(op.then_ops)
            yield from _walk_ops(op.else_ops)


def build_dex(app: AppIR) -> DexBuild:
    cls = app.class_descriptor
    activity = "Landroid/app/Activity;"
    bundle = "Landroid/os/Bundle;"
    context = "Landroid/content/Context;"
    text_view = "Landroid/widget/TextView;"
    charseq = "Ljava/lang/CharSequence;"
    view = "Landroid/view/View;"
    void = "V"
    int_t = "I"
    protos = [
        ProtoKey(void, ()),
        ProtoKey(void, (bundle,)),
        ProtoKey(void, (context,)),
        ProtoKey(void, (charseq,)),
        ProtoKey(void, (view,)),
    ]
    act_ctor = MethodKey(activity, "<init>", void, ())
    act_on = MethodKey(activity, "onCreate", void, (bundle,))
    act_set = MethodKey(activity, "setContentView", void, (view,))
    tv_ctor = MethodKey(text_view, "<init>", void, (context,))
    tv_set = MethodKey(text_view, "setText", void, (charseq,))
    our_ctor = MethodKey(cls, "<init>", void, ())
    our_on = MethodKey(cls, "onCreate", void, (bundle,))
    helper_keys = {}
    for fn in app.functions:
        params = tuple(int_t for _ in fn.parameters)
        p = ProtoKey(int_t, params)
        protos.append(p)
        helper_keys[fn.name] = MethodKey(cls, fn.name, int_t, params)
    methods = [
        act_ctor,
        act_on,
        act_set,
        tv_ctor,
        tv_set,
        our_ctor,
        our_on,
        *helper_keys.values(),
    ]
    strings_from_main = {
        op.value
        for op in _walk_ops(app.operations)
        if isinstance(op, LoadConst) and op.type_name == "str"
    }
    strings_set = {
        cls,
        activity,
        bundle,
        context,
        text_view,
        charseq,
        view,
        void,
        int_t,
        "<init>",
        "onCreate",
        "setText",
        "setContentView",
        *helper_keys.keys(),
        *strings_from_main,
    }
    for p in protos:
        strings_set.add(_shorty(p))
    strings = sorted(strings_set, key=dex_string_sort_key)
    sidx = {s: i for i, s in enumerate(strings)}
    types = sorted(
        {cls, activity, bundle, context, text_view, charseq, view, void, int_t},
        key=lambda s: sidx[s],
    )
    tidx = {s: i for i, s in enumerate(types)}
    protos = sorted(
        set(protos),
        key=lambda p: (tidx[p.return_type], tuple(tidx[x] for x in p.parameters)),
    )
    pidx = {p: i for i, p in enumerate(protos)}
    methods = sorted(
        methods,
        key=lambda m: (
            tidx[m.owner],
            sidx[m.name],
            pidx[ProtoKey(m.return_type, m.parameters)],
        ),
    )
    midx = {m: i for i, m in enumerate(methods)}

    # Main register map.
    symbols = list(app.symbol_types)
    if len(symbols) + 2 > 16:
        raise ValueError("Anpyra v0.1 on_create supports at most 14 locals")
    reg_of = {n: i for i, (n, _) in enumerate(symbols)}
    this_reg = len(symbols)
    state_reg = len(symbols) + 1
    main_regs = len(symbols) + 2
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
            if isinstance(op, CallSuperOnCreate):
                main_asm.emit(
                    "invoke",
                    OP_INVOKE_SUPER,
                    midx[act_on],
                    (this_reg, state_reg),
                    "Activity.onCreate(Bundle)",
                    size=3,
                )
            elif isinstance(op, LoadConst):
                r = reg_of[op.target]
                if op.type_name == "str":
                    main_asm.emit("const_string", r, sidx[op.value], op.value, size=2)
                elif op.type_name == "bool":
                    main_asm.emit("const4", r, 1 if op.value else 0, size=1)
                elif op.type_name == "int":
                    main_asm.emit(
                        "const4", r, op.value, size=1
                    ) if -8 <= op.value <= 7 else main_asm.emit("const16", r, op.value, size=2)
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
                main_asm.emit(
                    "invoke",
                    OP_INVOKE_STATIC,
                    midx[key],
                    regs,
                    f"{op.function_name}(" + ",".join("I" for _ in regs) + ")I",
                    size=3,
                )
                main_asm.emit("move_result", reg_of[op.target], size=1)
            elif isinstance(op, NewTextView):
                r = reg_of[op.target]
                main_asm.emit("new_instance", r, tidx[text_view], text_view, size=2)
                main_asm.emit(
                    "invoke",
                    OP_INVOKE_DIRECT,
                    midx[tv_ctor],
                    (r, this_reg),
                    "TextView.<init>(Context)",
                    size=3,
                )
            elif isinstance(op, SetText):
                main_asm.emit(
                    "invoke",
                    OP_INVOKE_VIRTUAL,
                    midx[tv_set],
                    (reg_of[op.receiver], reg_of[op.value_var]),
                    "TextView.setText(CharSequence)",
                    size=3,
                )
            elif isinstance(op, SetContentView):
                main_asm.emit(
                    "invoke",
                    OP_INVOKE_VIRTUAL,
                    midx[act_set],
                    (this_reg, reg_of[op.view]),
                    "Activity.setContentView(View)",
                    size=3,
                )
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

    # Fixed sections.
    string_ids_off = HEADER_SIZE
    string_ids_size = len(strings)
    type_ids_off = string_ids_off + string_ids_size * 4
    type_ids_size = len(types)
    proto_ids_off = type_ids_off + type_ids_size * 4
    proto_ids_size = len(protos)
    method_ids_off = proto_ids_off + proto_ids_size * 12
    method_ids_size = len(methods)
    class_defs_off = method_ids_off + method_ids_size * 8
    data_off = align(class_defs_off + 32, 4)
    param_lists = sorted(
        {p.parameters for p in protos if p.parameters},
        key=lambda ps: tuple(tidx[x] for x in ps),
    )
    tl = bytearray()
    po = {}
    cur = data_off
    for ps in param_lists:
        cur = align(cur, 4)
        while data_off + len(tl) < cur:
            tl.append(0)
        po[ps] = cur
        item = bytearray(struct.pack("<I", len(ps)))
        for d in ps:
            item += struct.pack("<H", tidx[d])
        while len(item) % 4:
            item.append(0)
        tl += item
        cur += len(item)
    sd_start = data_off + len(tl)
    sd = bytearray()
    sdo = []
    for s in strings:
        sdo.append(sd_start + len(sd))
        sd += uleb128(len(utf16_code_units(s))) + mutf8_encode(s) + b"\0"
    cur = align(sd_start + len(sd), 4)
    code_offsets = {}
    code_blobs = []

    def add_code(key, blob):
        nonlocal cur
        cur = align(cur, 4)
        code_offsets[key] = cur
        code_blobs.append((cur, blob))
        cur += len(blob)

    add_code(our_ctor, ctor_code)
    for key, fn, blob, *_ in helper_codes:
        add_code(key, blob)
    add_code(our_on, main_code)
    class_data_off = cur

    # class_data: direct methods constructor + static helpers, sorted by method index.
    direct = [(midx[our_ctor], ACC_PUBLIC | ACC_CONSTRUCTOR, code_offsets[our_ctor])]
    for key, fn, *_ in helper_codes:
        direct.append((midx[key], ACC_PUBLIC | ACC_STATIC, code_offsets[key]))
    direct.sort()
    virtual = [(midx[our_on], ACC_PROTECTED, code_offsets[our_on])]
    cd = bytearray()
    cd += uleb128(0) + uleb128(0) + uleb128(len(direct)) + uleb128(1)
    prev = 0
    for idx, flags, off in direct:
        cd += uleb128(idx - prev) + uleb128(flags) + uleb128(off)
        prev = idx
    prev = 0
    for idx, flags, off in virtual:
        cd += uleb128(idx - prev) + uleb128(flags) + uleb128(off)
        prev = idx
    map_off = align(class_data_off + len(cd), 4)

    string_ids = b"".join(struct.pack("<I", x) for x in sdo)
    type_ids = b"".join(struct.pack("<I", sidx[d]) for d in types)
    proto_ids = bytearray()
    for p in protos:
        proto_ids += struct.pack(
            "<III", sidx[_shorty(p)], tidx[p.return_type], po.get(p.parameters, 0)
        )
    method_ids = bytearray()
    for m in methods:
        method_ids += struct.pack(
            "<HHI",
            tidx[m.owner],
            pidx[ProtoKey(m.return_type, m.parameters)],
            sidx[m.name],
        )
    class_def = struct.pack(
        "<IIIIIIII",
        tidx[cls],
        ACC_PUBLIC | ACC_FINAL,
        tidx[activity],
        0,
        NO_INDEX,
        0,
        class_data_off,
        0,
    )
    data = bytearray(tl) + sd
    # lay code blobs at their absolute offsets
    for off, blob in code_blobs:
        data += b"\0" * (off - (data_off + len(data)))
        data += blob
    if data_off + len(data) != class_data_off:
        raise AssertionError("class_data offset mismatch")
    data += cd
    data += b"\0" * (map_off - (data_off + len(data)))
    code_count = 2 + len(helper_codes)
    first_code = min(code_offsets.values())
    map_entries = [
        (TYPE_HEADER_ITEM, 1, 0),
        (TYPE_STRING_ID_ITEM, string_ids_size, string_ids_off),
        (TYPE_TYPE_ID_ITEM, type_ids_size, type_ids_off),
        (TYPE_PROTO_ID_ITEM, proto_ids_size, proto_ids_off),
        (TYPE_METHOD_ID_ITEM, method_ids_size, method_ids_off),
        (TYPE_CLASS_DEF_ITEM, 1, class_defs_off),
        (TYPE_TYPE_LIST, len(param_lists), min(po.values())),
        (TYPE_STRING_DATA_ITEM, string_ids_size, sd_start),
        (TYPE_CODE_ITEM, code_count, first_code),
        (TYPE_CLASS_DATA_ITEM, 1, class_data_off),
        (TYPE_MAP_LIST, 1, map_off),
    ]
    mb = bytearray(struct.pack("<I", len(map_entries)))
    for typ, size, off in map_entries:
        mb += struct.pack("<HHII", typ, 0, size, off)
    data += mb
    data_size = len(data)
    file_size = data_off + data_size
    header = struct.pack(
        "<8sI20s20I",
        DEX_MAGIC,
        0,
        b"\0" * 20,
        file_size,
        HEADER_SIZE,
        ENDIAN_CONSTANT,
        0,
        0,
        map_off,
        string_ids_size,
        string_ids_off,
        type_ids_size,
        type_ids_off,
        proto_ids_size,
        proto_ids_off,
        0,
        0,
        method_ids_size,
        method_ids_off,
        1,
        class_defs_off,
        data_size,
        data_off,
    )
    out = bytearray(header) + string_ids + type_ids + proto_ids + method_ids + class_def
    out += b"\0" * (data_off - len(out))
    out += data
    out[12:32] = hashlib.sha1(out[32:]).digest()
    out[8:12] = struct.pack("<I", zlib.adler32(out[12:]) & 0xFFFFFFFF)
    main_map = tuple(
        [(n, t, reg_of[n]) for n, t in symbols]
        + [("p0:self", "MainActivity", this_reg), ("p1:state", "Bundle", state_reg)]
    )
    method_listings.append(MethodListing("onCreate", main_map, len(main_words), main_listing))
    return DexBuild(bytes(out), main_map, len(main_words), main_listing, tuple(method_listings))
