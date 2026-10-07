"""General DEX class/field/interface writer for interactive native controllers.

Legacy applications retain their existing byte-preserving DEX writer.
"""

import hashlib
import struct
import zlib
from dataclasses import dataclass

from .dex import _shorty
from .dex_types import MethodKey, ProtoKey
from .encoding import align, dex_string_sort_key, mutf8_encode, uleb128, utf16_code_units


@dataclass
class MethodDefinition:
    key: MethodKey
    flags: int
    factory: object
    direct: bool = False


@dataclass
class ClassDefinition:
    descriptor: str
    superclass: str
    methods: tuple
    fields: tuple = ()
    interfaces: tuple = ()
    flags: int = 0x11


@dataclass
class Pools:
    types: dict
    strings: dict
    methods: dict
    fields: dict


def write_classes(classes, references, field_references=(), literal_strings=(), extra_types=()):
    methods = set(references)
    fields = set(field_references)
    types = {"V", *extra_types}
    for cls in classes:
        types.update((cls.descriptor, cls.superclass, *cls.interfaces))
        methods.update(method.key for method in cls.methods)
        fields.update(field for field, flags in cls.fields)
    protos = {ProtoKey(method.return_type, method.parameters) for method in methods}
    for method in methods:
        types.update((method.owner, method.return_type, *method.parameters))
    for field in fields:
        types.update((field.owner, field.type_name))
    strings = sorted(
        {
            *types,
            *literal_strings,
            *(method.name for method in methods),
            *(field.name for field in fields),
            *(_shorty(proto) for proto in protos),
        },
        key=dex_string_sort_key,
    )
    sidx = {value: index for index, value in enumerate(strings)}
    types = sorted(types, key=sidx.__getitem__)
    tidx = {value: index for index, value in enumerate(types)}
    protos = sorted(
        protos,
        key=lambda proto: (
            tidx[proto.return_type],
            tuple(tidx[value] for value in proto.parameters),
        ),
    )
    pidx = {value: index for index, value in enumerate(protos)}
    methods = sorted(
        methods,
        key=lambda method: (
            tidx[method.owner],
            sidx[method.name],
            pidx[ProtoKey(method.return_type, method.parameters)],
        ),
    )
    midx = {value: index for index, value in enumerate(methods)}
    fields = sorted(
        fields, key=lambda field: (tidx[field.owner], sidx[field.name], tidx[field.type_name])
    )
    fidx = {value: index for index, value in enumerate(fields)}
    classes = sorted(classes, key=lambda cls: tidx[cls.descriptor])
    pools = Pools(tidx, sidx, midx, fidx)
    string_off = 0x70
    type_off = string_off + len(strings) * 4
    proto_off = type_off + len(types) * 4
    field_off = proto_off + len(protos) * 12
    method_off = field_off + len(fields) * 8
    class_off = method_off + len(methods) * 8
    data_off = align(class_off + len(classes) * 32, 4)
    data = bytearray()
    lists = {
        tuple(tidx[value] for value in proto.parameters) for proto in protos if proto.parameters
    }
    lists.update(
        tuple(sorted(tidx[value] for value in cls.interfaces)) for cls in classes if cls.interfaces
    )
    list_offsets = {}
    for values in sorted(lists):
        data += b"\0" * (align(data_off + len(data), 4) - (data_off + len(data)))
        list_offsets[values] = data_off + len(data)
        data += struct.pack("<I", len(values)) + b"".join(
            struct.pack("<H", value) for value in values
        )
        data += b"\0" * (align(data_off + len(data), 4) - (data_off + len(data)))
    string_data_off = data_off + len(data)
    string_offsets = []
    for value in strings:
        string_offsets.append(data_off + len(data))
        data += uleb128(len(utf16_code_units(value))) + mutf8_encode(value) + b"\0"
    data += b"\0" * (align(data_off + len(data), 4) - (data_off + len(data)))
    first_code = data_off + len(data)
    code_offsets = {}
    for cls in classes:
        for method in sorted(cls.methods, key=lambda definition: midx[definition.key]):
            data += b"\0" * (align(data_off + len(data), 4) - (data_off + len(data)))
            code_offsets[method.key] = data_off + len(data)
            data += method.factory(pools)
    class_data_offsets = {}
    first_class_data = data_off + len(data)
    for cls in classes:
        class_data_offsets[cls.descriptor] = data_off + len(data)
        static = sorted(
            ((field, flags) for field, flags in cls.fields if flags & 8),
            key=lambda item: fidx[item[0]],
        )
        instance = sorted(
            ((field, flags) for field, flags in cls.fields if not flags & 8),
            key=lambda item: fidx[item[0]],
        )
        direct = sorted(
            (method for method in cls.methods if method.direct),
            key=lambda definition: midx[definition.key],
        )
        virtual = sorted(
            (method for method in cls.methods if not method.direct),
            key=lambda definition: midx[definition.key],
        )
        for count in (len(static), len(instance), len(direct), len(virtual)):
            data += uleb128(count)
        for definitions in (static, instance):
            previous = 0
            for field, flags in definitions:
                index = fidx[field]
                data += uleb128(index - previous) + uleb128(flags)
                previous = index
        for definitions in (direct, virtual):
            previous = 0
            for method in definitions:
                index = midx[method.key]
                data += (
                    uleb128(index - previous)
                    + uleb128(method.flags)
                    + uleb128(code_offsets[method.key])
                )
                previous = index
    data += b"\0" * (align(data_off + len(data), 4) - (data_off + len(data)))
    map_off = data_off + len(data)
    entries = [
        (0, 1, 0),
        (1, len(strings), string_off),
        (2, len(types), type_off),
        (3, len(protos), proto_off),
        (5, len(methods), method_off),
        (6, len(classes), class_off),
        (0x2002, len(strings), string_data_off),
        (0x2001, len(code_offsets), first_code),
        (0x2000, len(classes), first_class_data),
        (0x1000, 1, map_off),
    ]
    if fields:
        entries.append((4, len(fields), field_off))
    if lists:
        entries.append((0x1001, len(lists), min(list_offsets.values())))
    data += struct.pack("<I", len(entries))
    for kind, count, offset in sorted(entries, key=lambda entry: entry[2]):
        data += struct.pack("<HHII", kind, 0, count, offset)
    fixed = b"".join(struct.pack("<I", offset) for offset in string_offsets)
    fixed += b"".join(struct.pack("<I", sidx[value]) for value in types)
    fixed += b"".join(
        struct.pack(
            "<III",
            sidx[_shorty(proto)],
            tidx[proto.return_type],
            list_offsets.get(tuple(tidx[value] for value in proto.parameters), 0),
        )
        for proto in protos
    )
    fixed += b"".join(
        struct.pack("<HHI", tidx[field.owner], tidx[field.type_name], sidx[field.name])
        for field in fields
    )
    fixed += b"".join(
        struct.pack(
            "<HHI",
            tidx[method.owner],
            pidx[ProtoKey(method.return_type, method.parameters)],
            sidx[method.name],
        )
        for method in methods
    )
    fixed += b"".join(
        struct.pack(
            "<IIIIIIII",
            tidx[cls.descriptor],
            cls.flags,
            tidx[cls.superclass],
            list_offsets.get(tuple(sorted(tidx[value] for value in cls.interfaces)), 0),
            0xFFFFFFFF,
            0,
            class_data_offsets[cls.descriptor],
            0,
        )
        for cls in classes
    )
    header = struct.pack(
        "<8sI20s20I",
        b"dex\n035\0",
        0,
        b"\0" * 20,
        data_off + len(data),
        0x70,
        0x12345678,
        0,
        0,
        map_off,
        len(strings),
        string_off,
        len(types),
        type_off,
        len(protos),
        proto_off,
        len(fields),
        field_off if fields else 0,
        len(methods),
        method_off,
        len(classes),
        class_off,
        len(data),
        data_off,
    )
    result = bytearray(header) + fixed
    result += b"\0" * (data_off - len(result)) + data
    result[12:32] = hashlib.sha1(result[32:]).digest()
    result[8:12] = struct.pack("<I", zlib.adler32(result[12:]) & 0xFFFFFFFF)
    return bytes(result)
