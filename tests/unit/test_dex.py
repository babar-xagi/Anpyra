"""Inspect emitted DEX bytes independently of the assembler's text listing."""

import hashlib
import struct
import unittest
import zlib
from pathlib import Path

from anpyra import compile_source
from anpyra.android.dex import build_dex, mutf8_encode


def u32(data, offset):
    return struct.unpack_from("<I", data, offset)[0]


def read_uleb(data, offset):
    value, shift = 0, 0
    while True:
        byte = data[offset]
        offset += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, offset
        shift += 7


def read_methods(data):
    string_count, string_offset = struct.unpack_from("<II", data, 56)
    strings = []
    for index in range(string_count):
        offset = u32(data, string_offset + 4 * index)
        _, offset = read_uleb(data, offset)
        strings.append(data[offset : data.index(0, offset)].decode("utf-8"))
    _, method_offset = struct.unpack_from("<II", data, 88)
    class_offset = u32(data, 100)
    offset = u32(data, class_offset + 24)
    counts = []
    for _ in range(4):
        value, offset = read_uleb(data, offset)
        counts.append(value)
    assert counts[:2] == [0, 0]
    methods = {}
    for count in counts[2:]:
        index = 0
        for _ in range(count):
            diff, offset = read_uleb(data, offset)
            flags, offset = read_uleb(data, offset)
            code_offset, offset = read_uleb(data, offset)
            index += diff
            name = strings[u32(data, method_offset + 8 * index + 4)]
            registers, inputs, outputs, tries, debug, size = struct.unpack_from(
                "<HHHHII", data, code_offset
            )
            words = struct.unpack_from("<" + "H" * size, data, code_offset + 16)
            methods[name] = (registers, inputs, outputs, words, flags)
    return methods


class DexTests(unittest.TestCase):
    def setUp(self):
        source = (Path(__file__).parents[1] / "fixtures/exp008.py").read_text(encoding="utf-8")
        self.dex = build_dex(compile_source(source).ir).data

    def test_header_integrity_and_map_boundaries(self):
        data = self.dex
        self.assertEqual(u32(data, 32), len(data))
        self.assertEqual(data[12:32], hashlib.sha1(data[32:]).digest())
        self.assertEqual(u32(data, 8), zlib.adler32(data[12:]) & 0xFFFFFFFF)
        map_offset = u32(data, 52)
        map_count = u32(data, map_offset)
        offsets = []
        for index in range(map_count):
            kind, unused, count, offset = struct.unpack_from(
                "<HHII", data, map_offset + 4 + 12 * index
            )
            self.assertGreater(count, 0)
            self.assertLess(offset, len(data))
            offsets.append(offset)
            if kind == 0x2001:
                self.assertEqual(offset % 4, 0)
                self.assertEqual(count, 3)
        self.assertEqual(offsets, sorted(offsets))

    def test_helper_parameters_use_incoming_registers(self):
        registers, inputs, outputs, words, flags = read_methods(self.dex)["calculate_score"]
        self.assertEqual((registers, inputs, outputs), (3, 2, 0))
        self.assertTrue(flags & 0x8)  # static method
        self.assertEqual(words, (0x0090, 0x0201, 0x000F))  # add-int v0,v1,v2; return v0

    def test_invoke_result_and_branch_targets_in_actual_code(self):
        registers, inputs, outputs, words, _ = read_methods(self.dex)["onCreate"]
        self.assertEqual(inputs, 2)
        self.assertGreaterEqual(outputs, 2)
        widths = {
            0x0A: 1,
            0x0E: 1,
            0x12: 1,
            0x13: 2,
            0x1A: 2,
            0x22: 2,
            0x29: 2,
            0x32: 2,
            0x33: 2,
            0x34: 2,
            0x35: 2,
            0x36: 2,
            0x37: 2,
            0x38: 2,
            0x6E: 3,
            0x6F: 3,
            0x70: 3,
            0x71: 3,
            0x90: 2,
            0x91: 2,
        }
        pc, starts, targets, static_calls = 0, [], [], 0
        while pc < len(words):
            starts.append(pc)
            opcode = words[pc] & 0xFF
            if opcode == 0x71:
                static_calls += 1
                self.assertEqual(words[pc + 3] & 0xFF, 0x0A)
            if opcode == 0x29 or 0x32 <= opcode <= 0x38:
                delta = struct.unpack("<h", struct.pack("<H", words[pc + 1]))[0]
                targets.append(pc + delta)
            pc += widths[opcode]
        self.assertEqual(pc, len(words))
        self.assertEqual(static_calls, 1)
        self.assertTrue(targets)
        self.assertTrue(all(target in starts for target in targets))

    def test_modified_utf8_encodes_null_and_supplementary_characters(self):
        self.assertEqual(mutf8_encode("A\x00🐍"), b"A\xc0\x80\xed\xa0\xbd\xed\xb0\x8d")
