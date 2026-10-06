"""Write DEX pools, sections, class metadata and integrity fields."""

from __future__ import annotations

import hashlib
import struct
import zlib

from ..compiler.ir import AppIR, ApplyScreenBackground, LoadConst
from .backgrounds import background_fields
from .codegen import _walk_ops, generate_methods
from .dex_types import DexBuild, MethodKey, ProtoKey
from .encoding import align, dex_string_sort_key, mutf8_encode, uleb128, utf16_code_units
from .screen import ACTIVITY_TYPE, screen_methods
from .textview import textview_fields, textview_strings

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
TYPE_FIELD_ID_ITEM = 0x0004
TYPE_METHOD_ID_ITEM = 0x0005
TYPE_CLASS_DEF_ITEM = 0x0006
TYPE_MAP_LIST = 0x1000
TYPE_TYPE_LIST = 0x1001
TYPE_CLASS_DATA_ITEM = 0x2000
TYPE_CODE_ITEM = 0x2001
TYPE_STRING_DATA_ITEM = 0x2002


def _shorty(p):
    def one(d):
        return "L" if d.startswith(("L", "[")) else d[0]

    return one(p.return_type) + "".join(one(x) for x in p.parameters)


def build_dex(app: AppIR) -> DexBuild:
    cls = app.class_descriptor
    activity, void, int_t = ACTIVITY_TYPE, "V", "I"
    operations = tuple(_walk_ops(app.operations))
    screen_refs = screen_methods(cls, operations)
    fields = tuple(set(background_fields(operations)) | textview_fields(operations))
    protos = [ProtoKey(method.return_type, method.parameters) for method in screen_refs.values()]
    our_ctor = screen_refs["app_constructor"]
    our_on = screen_refs["app_on_create"]
    helper_keys = {}
    for fn in app.functions:
        params = tuple(int_t for _ in fn.parameters)
        p = ProtoKey(int_t, params)
        protos.append(p)
        helper_keys[fn.name] = MethodKey(cls, fn.name, int_t, params)
    methods = list({*screen_refs.values(), *helper_keys.values()})
    strings_from_main = {
        op.value
        for op in _walk_ops(app.operations)
        if isinstance(op, LoadConst) and op.type_name == "str"
    }
    strings_from_main.update(
        op.image_asset
        for op in operations
        if isinstance(op, ApplyScreenBackground) and op.image_asset is not None
    )
    strings_from_main.update(textview_strings(operations))
    type_descriptors = {cls, activity, void, int_t}
    for method in methods:
        type_descriptors.update((method.owner, method.return_type, *method.parameters))
    for field in fields:
        type_descriptors.update((field.owner, field.type_name))
    strings_set = {
        *type_descriptors,
        *(method.name for method in methods),
        *(field.name for field in fields),
        *strings_from_main,
    }
    for p in protos:
        strings_set.add(_shorty(p))
    strings = sorted(strings_set, key=dex_string_sort_key)
    sidx = {s: i for i, s in enumerate(strings)}
    types = sorted(
        type_descriptors,
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
    fields = sorted(
        fields, key=lambda field: (tidx[field.owner], sidx[field.name], tidx[field.type_name])
    )
    fidx = {field: index for index, field in enumerate(fields)}

    generated = generate_methods(app, tidx, sidx, midx, helper_keys, screen_refs, fidx)
    ctor_code, main_code = generated.constructor_code, generated.lifecycle_code
    helper_codes = generated.helper_codes
    # Fixed sections.
    string_ids_off = HEADER_SIZE
    string_ids_size = len(strings)
    type_ids_off = string_ids_off + string_ids_size * 4
    type_ids_size = len(types)
    proto_ids_off = type_ids_off + type_ids_size * 4
    proto_ids_size = len(protos)
    field_ids_size = len(fields)
    field_ids_off = proto_ids_off + proto_ids_size * 12 if fields else 0
    method_ids_off = proto_ids_off + proto_ids_size * 12 + field_ids_size * 8
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
    field_ids = b"".join(
        struct.pack("<HHI", tidx[field.owner], tidx[field.type_name], sidx[field.name])
        for field in fields
    )
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
    if fields:
        map_entries.insert(4, (TYPE_FIELD_ID_ITEM, field_ids_size, field_ids_off))
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
        field_ids_size,
        field_ids_off,
        method_ids_size,
        method_ids_off,
        1,
        class_defs_off,
        data_size,
        data_off,
    )
    out = bytearray(header) + string_ids + type_ids + proto_ids + field_ids + method_ids + class_def
    out += b"\0" * (data_off - len(out))
    out += data
    out[12:32] = hashlib.sha1(out[32:]).digest()
    out[8:12] = struct.pack("<I", zlib.adler32(out[12:]) & 0xFFFFFFFF)
    return DexBuild(
        bytes(out),
        generated.register_map,
        generated.code_units,
        generated.assembly_listing,
        generated.listings,
    )
