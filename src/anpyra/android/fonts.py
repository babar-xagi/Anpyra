"""Bounded validation of standalone SFNT fonts before native asset loading."""

import io
import struct

from PIL import ImageFont


def validate_font(payload: bytes, extension: str) -> None:
    if not 12 <= len(payload) <= 16 * 1024 * 1024:
        raise ValueError("font must be between 12 bytes and 16 MiB")
    expected = b"OTTO" if extension == ".otf" else b"\x00\x01\x00\x00"
    if payload[:4] != expected:
        raise ValueError("font extension must match standalone TrueType/OpenType content")
    count = struct.unpack_from(">H", payload, 4)[0]
    end = 12 + count * 16
    if not 1 <= count <= 4096 or end > len(payload):
        raise ValueError("font table directory is invalid")
    tables = set()
    for index in range(count):
        tag, _, offset, length = struct.unpack_from(">4sIII", payload, 12 + index * 16)
        if tag in tables or offset < end or offset + length > len(payload):
            raise ValueError("font contains duplicate or out-of-bounds tables")
        tables.add(tag)
    if not {b"head", b"cmap", b"name", b"hhea", b"hmtx", b"maxp"}.issubset(tables):
        raise ValueError("font is missing required SFNT tables")
    if not ({b"glyf", b"loca"}.issubset(tables) or {b"CFF ", b"CFF2"} & tables):
        raise ValueError("font contains no supported outlines")
    try:
        font = ImageFont.truetype(io.BytesIO(payload), size=24)
        font.getmask("Anpyra")
    except (OSError, ValueError) as exc:
        raise ValueError(f"cannot decode font: {exc}") from exc
