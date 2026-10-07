# Adapted from the user-provided PyAndroid experiments for Anpyra.
from __future__ import annotations

import struct

from .manifest import (
    RES_STRING_POOL_TYPE,
    RES_XML_END_ELEMENT_TYPE,
    RES_XML_END_NAMESPACE_TYPE,
    RES_XML_RESOURCE_MAP_TYPE,
    RES_XML_START_ELEMENT_TYPE,
    RES_XML_START_NAMESPACE_TYPE,
    RES_XML_TYPE,
    TYPE_INT_BOOLEAN,
    TYPE_INT_DEC,
    TYPE_STRING,
)


class AxmlError(ValueError):
    pass


def _read_len8(data: bytes, p: int) -> tuple[int, int]:
    b = data[p]
    p += 1
    if b & 0x80:
        return ((b & 0x7F) << 8) | data[p], p + 1
    return b, p


def _parse_string_pool(data: bytes, off: int):
    typ, header_size, size = struct.unpack_from("<HHI", data, off)
    if typ != RES_STRING_POOL_TYPE or header_size != 28:
        raise AxmlError("invalid string pool")
    count, style_count, flags, strings_start, styles_start = struct.unpack_from(
        "<IIIII", data, off + 8
    )
    if style_count != 0 or styles_start != 0:
        raise AxmlError("styles are not expected")
    utf8 = bool(flags & 0x100)
    if not utf8:
        raise AxmlError("Anpyra expects UTF-8 string pool")

    offsets = [struct.unpack_from("<I", data, off + header_size + 4 * i)[0] for i in range(count)]
    strings = []
    base = off + strings_start
    for rel in offsets:
        p = base + rel
        _, p = _read_len8(data, p)
        byte_len, p = _read_len8(data, p)
        raw = data[p : p + byte_len]
        strings.append(raw.decode("utf-8"))
    return tuple(strings), off + size


def inspect_manifest(data: bytes) -> dict:
    if len(data) < 8:
        raise AxmlError("manifest too small")
    typ, header_size, total_size = struct.unpack_from("<HHI", data, 0)
    if typ != RES_XML_TYPE or header_size != 8 or total_size != len(data):
        raise AxmlError("invalid XML root chunk")

    off = 8
    strings, off = _parse_string_pool(data, off)

    typ, header_size, size = struct.unpack_from("<HHI", data, off)
    if typ != RES_XML_RESOURCE_MAP_TYPE or header_size != 8:
        raise AxmlError("resource map missing")
    resource_ids = tuple(
        struct.unpack_from("<I", data, p)[0] for p in range(off + 8, off + size, 4)
    )
    off += size

    stack = []
    starts = []
    attrs_by_element = {}

    while off < len(data):
        typ, header_size, size = struct.unpack_from("<HHI", data, off)
        if size < header_size or off + size > len(data):
            raise AxmlError("invalid XML chunk bounds")

        if typ in (RES_XML_START_NAMESPACE_TYPE, RES_XML_END_NAMESPACE_TYPE):
            off += size
            continue

        if typ == RES_XML_START_ELEMENT_TYPE:
            (
                ns_idx,
                name_idx,
                attr_start,
                attr_size,
                attr_count,
                id_idx,
                class_idx,
                style_idx,
            ) = struct.unpack_from("<IIHHHHHH", data, off + 16)
            name = strings[name_idx]
            attrs = {}
            p = off + 16 + attr_start
            for _ in range(attr_count):
                ans, aname, raw, value_size, res0, data_type, value = struct.unpack_from(
                    "<IIIHBBI", data, p
                )
                p += attr_size
                key = strings[aname]
                if data_type == TYPE_STRING:
                    val = strings[value]
                elif data_type == TYPE_INT_DEC:
                    val = value
                elif data_type == TYPE_INT_BOOLEAN:
                    val = bool(value)
                else:
                    val = value
                attrs[key] = val
            stack.append(name)
            starts.append(name)
            attrs_by_element.setdefault(name, []).append(attrs)

        elif typ == RES_XML_END_ELEMENT_TYPE:
            ns_idx, name_idx = struct.unpack_from("<II", data, off + 16)
            name = strings[name_idx]
            if not stack or stack[-1] != name:
                raise AxmlError(f"unbalanced end tag: {name}")
            stack.pop()

        off += size

    if stack:
        raise AxmlError(f"unclosed elements: {stack}")

    required_order = [
        "manifest",
        "uses-sdk",
        "application",
        "activity",
        "intent-filter",
        "action",
        "category",
    ]
    for x in required_order:
        if x not in starts:
            raise AxmlError(f"missing element: {x}")

    manifest_attrs = attrs_by_element["manifest"][0]
    uses_attrs = attrs_by_element["uses-sdk"][0]
    app_attrs = attrs_by_element["application"][0]
    activity_attrs = attrs_by_element["activity"][0]
    action_attrs = attrs_by_element["action"][0]
    category_attrs = attrs_by_element["category"][0]

    return {
        "strings": strings,
        "resource_ids": resource_ids,
        "package": manifest_attrs["package"],
        "versionCode": manifest_attrs["versionCode"],
        "versionName": manifest_attrs["versionName"],
        "minSdkVersion": uses_attrs["minSdkVersion"],
        "targetSdkVersion": uses_attrs["targetSdkVersion"],
        "label": app_attrs["label"],
        "activity": activity_attrs["name"],
        "exported": activity_attrs["exported"],
        "action": action_attrs["name"],
        "category": category_attrs["name"],
        "permissions": tuple(
            item.get("name") for item in attrs_by_element.get("uses-permission", [])
        ),
    }
