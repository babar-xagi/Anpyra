"""Generate original block-outline fonts for tests; no third-party font data."""

from pathlib import Path

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.ttGlyphPen import TTGlyphPen

patterns = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01111", "10000", "10000", "10000", "10000", "10000", "01111"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01111", "10000", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "J": ["00111", "00010", "00010", "00010", "10010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "10101", "01010"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
}


def outline(pen, char):
    rows = patterns.get(
        char.upper(), ["11111", "10001", "10001", "10001", "10001", "10001", "11111"]
    )
    if char == " ":
        return
    for y, row in enumerate(rows):
        for x, bit in enumerate(row):
            if bit == "1":
                left, bottom = 40 + x * 100, (6 - y) * 100
                pen.moveTo((left, bottom))
                pen.lineTo((left, bottom + 90))
                pen.lineTo((left + 90, bottom + 90))
                pen.lineTo((left + 90, bottom))
                pen.closePath()


out = Path(__file__).resolve().parents[1] / "examples/text_style/assets"
out.mkdir(parents=True, exist_ok=True)
for ttf in (True, False):
    chars = [chr(i) for i in range(32, 127)]
    glyph_order = [".notdef", *[f"u{ord(c):04X}" for c in chars]]
    fb = FontBuilder(1000, isTTF=ttf)
    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap({ord(c): f"u{ord(c):04X}" for c in chars})
    glyphs = {}
    for name, char in zip(glyph_order, ["?", *chars]):
        pen = TTGlyphPen(None) if ttf else T2CharStringPen(600, None)
        outline(pen, char)
        glyphs[name] = pen.glyph() if ttf else pen.getCharString()
    if ttf:
        fb.setupGlyf(glyphs)
    else:
        fb.setupCFF(
            "AnpyraDemo-Regular",
            {"FullName": "Anpyra Demo", "FamilyName": "Anpyra Demo", "Weight": "Regular"},
            glyphs,
            {},
        )
    fb.setupHorizontalMetrics({name: (600, 40) for name in glyph_order})
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupOS2(sTypoAscender=800, sTypoDescender=-200, usWinAscent=800, usWinDescent=200)
    fb.setupNameTable(
        {
            "familyName": "Anpyra Demo",
            "styleName": "Regular",
            "uniqueFontIdentifier": "AnpyraDemo-1",
            "fullName": "Anpyra Demo Regular",
            "psName": "AnpyraDemo-Regular",
            "version": "Version 1.0",
            "copyright": "Anpyra contributors. Apache License 2.0.",
        }
    )
    fb.setupPost()
    fb.setupMaxp()
    fb.font["head"].created = fb.font["head"].modified = 2082844800
    target = out / ("AnpyraDemo.ttf" if ttf else "AnpyraDemo.otf")
    fb.save(target)
    print(target.name, target.stat().st_size)
