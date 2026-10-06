# Adapted from the user-provided PyAndroid experiments for Anpyra.
from __future__ import annotations

import struct
from dataclasses import dataclass

NO_INDEX = 0xFFFFFFFF

RES_STRING_POOL_TYPE = 0x0001
RES_XML_TYPE = 0x0003
RES_XML_START_NAMESPACE_TYPE = 0x0100
RES_XML_END_NAMESPACE_TYPE = 0x0101
RES_XML_START_ELEMENT_TYPE = 0x0102
RES_XML_END_ELEMENT_TYPE = 0x0103
RES_XML_RESOURCE_MAP_TYPE = 0x0180

UTF8_FLAG = 0x00000100

TYPE_STRING = 0x03
TYPE_INT_DEC = 0x10
TYPE_INT_BOOLEAN = 0x12

ANDROID_NS = "http://schemas.android.com/apk/res/android"

# Framework resource IDs for manifest attributes used by Anpyra.
ANDROID_ATTR_LABEL = 0x01010001
ANDROID_ATTR_NAME = 0x01010003
ANDROID_ATTR_EXPORTED = 0x01010010
ANDROID_ATTR_VERSION_CODE = 0x0101021B
ANDROID_ATTR_VERSION_NAME = 0x0101021C
ANDROID_ATTR_MIN_SDK_VERSION = 0x0101020C
ANDROID_ATTR_TARGET_SDK_VERSION = 0x01010270


def _chunk_header(chunk_type: int, header_size: int, size: int) -> bytes:
    return struct.pack("<HHI", chunk_type, header_size, size)


def _enc_len8(n: int) -> bytes:
    if n <= 0x7F:
        return bytes([n])
    if n <= 0x7FFF:
        return bytes([(n >> 8) | 0x80, n & 0xFF])
    raise ValueError("string too long for Anpyra")


class StringPool:
    def __init__(self, resource_names: list[tuple[str, int]], strings: list[str]):
        # Resource-mapped attribute names must occupy the first N slots,
        # because the resource-map is indexed by string-pool index.
        ordered = []
        resource_ids = []
        seen = set()

        for text, resid in resource_names:
            if text in seen:
                continue
            seen.add(text)
            ordered.append(text)
            resource_ids.append(resid)

        for text in strings:
            if text not in seen:
                seen.add(text)
                ordered.append(text)

        self.strings = ordered
        self.index = {s: i for i, s in enumerate(ordered)}
        self.resource_ids = resource_ids

    def build(self) -> bytes:
        offsets = []
        blob = bytearray()

        for s in self.strings:
            offsets.append(len(blob))
            raw = s.encode("utf-8")
            utf16_len = len(s.encode("utf-16-le")) // 2
            blob += _enc_len8(utf16_len)
            blob += _enc_len8(len(raw))
            blob += raw
            blob.append(0)

        while len(blob) % 4:
            blob.append(0)

        header_size = 28
        strings_start = header_size + 4 * len(self.strings)
        size = strings_start + len(blob)

        out = bytearray()
        out += _chunk_header(RES_STRING_POOL_TYPE, header_size, size)
        out += struct.pack(
            "<IIIII",
            len(self.strings),  # stringCount
            0,  # styleCount
            UTF8_FLAG,
            strings_start,
            0,  # stylesStart
        )
        out += b"".join(struct.pack("<I", x) for x in offsets)
        out += blob
        return bytes(out)

    def build_resource_map(self) -> bytes:
        body = b"".join(struct.pack("<I", x) for x in self.resource_ids)
        return _chunk_header(RES_XML_RESOURCE_MAP_TYPE, 8, 8 + len(body)) + body


@dataclass(frozen=True)
class Attr:
    namespace: str | None
    name: str
    kind: str
    value: str | int | bool


class BinaryXmlBuilder:
    def __init__(
        self,
        package: str,
        activity: str,
        label: str,
        *,
        version_code: int = 1,
        version_name: str = "0.1.0",
        min_sdk: int = 24,
        target_sdk: int = 36,
    ):
        self.package = package
        self.activity = activity
        self.label = label
        self.version_code = version_code
        self.version_name = version_name
        self.min_sdk = min_sdk
        self.target_sdk = target_sdk

        resource_names = [
            ("label", ANDROID_ATTR_LABEL),
            ("name", ANDROID_ATTR_NAME),
            ("exported", ANDROID_ATTR_EXPORTED),
            ("minSdkVersion", ANDROID_ATTR_MIN_SDK_VERSION),
            ("targetSdkVersion", ANDROID_ATTR_TARGET_SDK_VERSION),
            ("versionCode", ANDROID_ATTR_VERSION_CODE),
            ("versionName", ANDROID_ATTR_VERSION_NAME),
        ]

        strings = [
            "android",
            ANDROID_NS,
            "manifest",
            "package",
            "uses-sdk",
            "application",
            "activity",
            "intent-filter",
            "action",
            "category",
            self.package,
            self.activity,
            self.label,
            self.version_name,
            "android.intent.action.MAIN",
            "android.intent.category.LAUNCHER",
        ]

        self.pool = StringPool(resource_names, strings)
        self.line = 1

    def idx(self, s: str) -> int:
        return self.pool.index[s]

    def _node_header(self, typ: int, size: int) -> bytes:
        return _chunk_header(typ, 16, size) + struct.pack("<II", self.line, NO_INDEX)

    def namespace_start(self) -> bytes:
        size = 24
        return self._node_header(RES_XML_START_NAMESPACE_TYPE, size) + struct.pack(
            "<II", self.idx("android"), self.idx(ANDROID_NS)
        )

    def namespace_end(self) -> bytes:
        size = 24
        return self._node_header(RES_XML_END_NAMESPACE_TYPE, size) + struct.pack(
            "<II", self.idx("android"), self.idx(ANDROID_NS)
        )

    def _typed_value(self, attr: Attr) -> tuple[int, int, int]:
        if attr.kind == "string":
            si = self.idx(str(attr.value))
            return si, TYPE_STRING, si
        if attr.kind == "int":
            return NO_INDEX, TYPE_INT_DEC, int(attr.value)
        if attr.kind == "bool":
            return NO_INDEX, TYPE_INT_BOOLEAN, 0xFFFFFFFF if bool(attr.value) else 0
        raise ValueError(f"unknown attr kind: {attr.kind}")

    def start_element(self, name: str, attrs: list[Attr] | None = None) -> bytes:
        attrs = attrs or []
        size = 16 + 20 + 20 * len(attrs)

        out = bytearray(self._node_header(RES_XML_START_ELEMENT_TYPE, size))
        out += struct.pack(
            "<IIHHHHHH",
            NO_INDEX,  # namespace
            self.idx(name),
            20,  # attributeStart (relative to attrExt)
            20,  # attributeSize
            len(attrs),
            0,
            0,
            0,  # idIndex, classIndex, styleIndex
        )

        for attr in attrs:
            ns_idx = self.idx(attr.namespace) if attr.namespace else NO_INDEX
            raw_idx, data_type, data = self._typed_value(attr)
            out += struct.pack(
                "<IIIHBBI",
                ns_idx,
                self.idx(attr.name),
                raw_idx,
                8,  # Res_value.size
                0,  # res0
                data_type,
                data,
            )

        return bytes(out)

    def end_element(self, name: str) -> bytes:
        size = 24
        return self._node_header(RES_XML_END_ELEMENT_TYPE, size) + struct.pack(
            "<II", NO_INDEX, self.idx(name)
        )

    def build(self) -> bytes:
        chunks = bytearray()
        chunks += self.pool.build()
        chunks += self.pool.build_resource_map()
        chunks += self.namespace_start()

        chunks += self.start_element(
            "manifest",
            [
                Attr(None, "package", "string", self.package),
                Attr(ANDROID_NS, "versionCode", "int", self.version_code),
                Attr(ANDROID_NS, "versionName", "string", self.version_name),
            ],
        )

        chunks += self.start_element(
            "uses-sdk",
            [
                Attr(ANDROID_NS, "minSdkVersion", "int", self.min_sdk),
                Attr(ANDROID_NS, "targetSdkVersion", "int", self.target_sdk),
            ],
        )
        chunks += self.end_element("uses-sdk")

        chunks += self.start_element(
            "application",
            [
                Attr(ANDROID_NS, "label", "string", self.label),
            ],
        )

        chunks += self.start_element(
            "activity",
            [
                Attr(ANDROID_NS, "name", "string", self.activity),
                Attr(ANDROID_NS, "exported", "bool", True),
            ],
        )

        chunks += self.start_element("intent-filter")

        chunks += self.start_element(
            "action",
            [
                Attr(ANDROID_NS, "name", "string", "android.intent.action.MAIN"),
            ],
        )
        chunks += self.end_element("action")

        chunks += self.start_element(
            "category",
            [
                Attr(ANDROID_NS, "name", "string", "android.intent.category.LAUNCHER"),
            ],
        )
        chunks += self.end_element("category")

        chunks += self.end_element("intent-filter")
        chunks += self.end_element("activity")
        chunks += self.end_element("application")
        chunks += self.end_element("manifest")
        chunks += self.namespace_end()

        total = 8 + len(chunks)
        return _chunk_header(RES_XML_TYPE, 8, total) + bytes(chunks)


def build_manifest(
    package: str,
    activity: str,
    label: str,
    *,
    version_code: int = 1,
    version_name: str = "0.1.0",
    min_sdk: int = 24,
    target_sdk: int = 36,
) -> bytes:
    return BinaryXmlBuilder(
        package,
        activity,
        label,
        version_code=version_code,
        version_name=version_name,
        min_sdk=min_sdk,
        target_sdk=target_sdk,
    ).build()
