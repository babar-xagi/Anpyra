"""DEX alignment, unsigned integers and modified UTF-8 encoding."""


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
