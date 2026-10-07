"""Small typed assembler helper for generated listener and worker methods."""

import struct

from .dalvik import (
    OP_INVOKE_DIRECT,
    OP_INVOKE_STATIC,
    OP_INVOKE_VIRTUAL,
    Assembler,
    Label,
    emit_const,
    emit_invoke,
    make_code_item,
)
from .encoding import uleb128


class MethodBuilder:
    def __init__(self, pools, refs, fields, registers=16, inputs=1):
        self.pools, self.refs, self.fields = pools, refs, fields
        self.registers, self.inputs = registers, inputs
        self.asm = Assembler()

    def const(self, register, value):
        emit_const(self.asm, register, value)

    def string(self, register, value):
        self.asm.emit("const_string", register, self.pools.strings[value], value, size=2)

    def invoke(self, name, args, *, static=False, direct=False, result=None):
        method = self.refs[name]
        opcode = OP_INVOKE_STATIC if static else OP_INVOKE_DIRECT if direct else OP_INVOKE_VIRTUAL
        types = method.parameters if static else (method.owner, *method.parameters)
        emit_invoke(
            self.asm,
            opcode,
            self.pools.methods[method],
            args,
            types,
            None,
            f"{method.owner}->{method.name}",
        )
        if result is not None:
            self.asm.emit(
                "move_result_object"
                if method.return_type.startswith(("L", "["))
                else "move_result",
                result,
                size=1,
            )

    def create(self, register, descriptor, constructor, args=()):
        self.asm.emit("new_instance", register, self.pools.types[descriptor], descriptor, size=2)
        self.invoke(constructor, (register, *args), direct=True)

    def get(self, register, owner, name):
        field = self.fields[name]
        kind = (
            "iget_object"
            if field.type_name.startswith(("L", "["))
            else "iget_boolean"
            if field.type_name == "Z"
            else "iget"
        )
        self.asm.emit(kind, register, owner, self.pools.fields[field], field.name, size=2)

    def put(self, register, owner, name):
        field = self.fields[name]
        kind = (
            "iput_object"
            if field.type_name.startswith(("L", "["))
            else "iput_boolean"
            if field.type_name == "Z"
            else "iput"
        )
        self.asm.emit(kind, register, owner, self.pools.fields[field], field.name, size=2)

    def label(self, name):
        self.asm.label(name)

    def zero(self, register, target):
        self.asm.emit("if_eqz", register, target, size=2)

    def compare(self, opcode, left, right, target, name="if-test"):
        self.asm.emit("if_test", opcode, left, right, target, name, size=2)

    def jump(self, target):
        self.asm.emit("goto16", target, size=2)

    def finish(self, catch=None):
        words, listing = self.asm.assemble()
        self.code_units = len(words)
        self.assembly_listing = tuple(listing)
        if catch is None:
            return make_code_item(
                registers_size=self.registers, ins_size=self.inputs, outs_size=5, insns=words
            )
        offsets = {}
        pc = 0
        for item in self.asm.items:
            if isinstance(item, Label):
                offsets[item.name] = pc
            else:
                pc += item.size
        start, end, handler, descriptor = catch
        handlers = (
            uleb128(1) + b"\x01" + uleb128(self.pools.types[descriptor]) + uleb128(offsets[handler])
        )
        blob = struct.pack(
            "<HHHHII", self.registers, self.inputs, 5, 1, 0, len(words)
        ) + struct.pack("<" + "H" * len(words), *words)
        if len(words) % 2:
            blob += b"\0\0"
        blob += struct.pack("<IHH", offsets[start], offsets[end] - offsets[start], 1)
        return blob + handlers
