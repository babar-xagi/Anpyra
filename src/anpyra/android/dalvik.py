"""Dalvik opcodes, instruction encoding and label-based assembly."""

import struct
from dataclasses import dataclass

OP_MOVE_RESULT = 0x0A
OP_MOVE_RESULT_OBJECT = 0x0C
OP_MOVE_FROM16 = 0x02
OP_MOVE_OBJECT_FROM16 = 0x08
OP_RETURN_VOID = 0x0E
OP_RETURN = 0x0F
OP_CONST_4 = 0x12
OP_CONST_16 = 0x13
OP_CONST = 0x14
OP_CONST_STRING = 0x1A
OP_NEW_INSTANCE = 0x22
OP_NEW_ARRAY = 0x23
OP_APUT = 0x4B
OP_APUT_OBJECT = 0x4D
OP_SGET_OBJECT = 0x62
OP_SGET = 0x60
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


def encode_21c(op, r, idx):
    return [op | (r << 8), idx]


def encode_invoke_35c(op, mid, regs):
    if len(regs) > 5 or any(not 0 <= r <= 15 for r in regs):
        raise ValueError("invoke-35c register/count limit")
    p = list(regs) + [0] * (5 - len(regs))
    c, d, e, f, g = p
    return [op | (g << 8) | (len(regs) << 12), mid, c | (d << 4) | (e << 8) | (f << 12)]


def emit_const(assembler, register, value):
    if not -0x80000000 <= value <= 0xFFFFFFFF or not 0 <= register <= 255:
        raise ValueError("constant/register does not fit supported DEX formats")
    signed = value if value < 0x80000000 else value - 0x100000000
    if register <= 15 and -8 <= signed <= 7:
        assembler.emit("const4", register, signed, size=1)
    elif -32768 <= signed <= 32767:
        assembler.emit("const16", register, signed, size=2)
    else:
        assembler.emit("const32", register, signed, size=3)


def emit_invoke(assembler, opcode, method_index, registers, types, argument_base=None, pretty=""):
    if len(registers) != len(types) or len(registers) > 5:
        raise ValueError("invalid invocation word/type count")
    if all(0 <= register <= 15 for register in registers):
        assembler.emit("invoke", opcode, method_index, tuple(registers), pretty, size=3)
        return
    if argument_base is None:
        raise ValueError("wide invocation requires a reserved argument bank")
    for offset, (register, typ) in enumerate(zip(registers, types)):
        destination = argument_base + offset
        assembler.emit(
            "move_object" if typ.startswith(("L", "[")) else "move", destination, register, size=2
        )
    assembler.emit(
        "invoke_range", opcode + 6, method_index, argument_base, len(registers), pretty, size=3
    )


def make_code_item(*, registers_size, ins_size, outs_size, insns):
    return struct.pack(
        "<HHHHII", registers_size, ins_size, outs_size, 0, 0, len(insns)
    ) + struct.pack("<" + "H" * len(insns), *insns)


@dataclass(frozen=True)
class AsmInstruction:
    kind: str
    args: tuple
    size: int


@dataclass(frozen=True)
class Label:
    name: str


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
            elif k == "const32":
                r, value = a
                enc = [OP_CONST | (r << 8), value & 0xFFFF, (value >> 16) & 0xFFFF]
                text = f"const v{r}, #{value}"
            elif k in {"move", "move_object"}:
                destination, source = a
                opcode = OP_MOVE_OBJECT_FROM16 if k == "move_object" else OP_MOVE_FROM16
                enc = [opcode | (destination << 8), source]
                text = f"{'move-object' if k == 'move_object' else 'move'}/from16 v{destination}, v{source}"
            elif k == "new_array":
                destination, count, type_index, desc = a
                if max(destination, count) > 15:
                    raise ValueError("new-array uses four-bit registers")
                enc = [OP_NEW_ARRAY | (destination << 8) | (count << 12), type_index]
                text = f"new-array v{destination}, v{count}, {desc}"
            elif k in {"aput", "aput_object"}:
                value, array, index = a
                enc = [
                    (OP_APUT_OBJECT if k == "aput_object" else OP_APUT) | (value << 8),
                    array | (index << 8),
                ]
                text = f"{'aput-object' if k == 'aput_object' else 'aput'} v{value}, v{array}, v{index}"
            elif k in {"sget_object", "sget"}:
                register, field_index, pretty = a
                enc = encode_21c(
                    OP_SGET_OBJECT if k == "sget_object" else OP_SGET, register, field_index
                )
                text = f"{'sget-object' if k == 'sget_object' else 'sget'} v{register}, {pretty}"
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
            elif k == "invoke_range":
                opcode, method_index, base, count, pretty = a
                enc = [opcode | (count << 8), method_index, base]
                mnemonic = {0x74: "virtual", 0x75: "super", 0x76: "direct", 0x77: "static"}[opcode]
                text = f"invoke-{mnemonic}/range {{v{base} .. v{base + count - 1}}}, {pretty}"
            elif k == "move_result":
                (r,) = a
                enc = [OP_MOVE_RESULT | (r << 8)]
                text = f"move-result v{r}"
            elif k == "move_result_object":
                (r,) = a
                enc = [OP_MOVE_RESULT_OBJECT | (r << 8)]
                text = f"move-result-object v{r}"
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
