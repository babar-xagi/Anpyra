"""Style validation, source lowering, native references and wider DEX instructions."""

import math
import struct
import unittest

from anpyra import CompileError, compile_source
from anpyra.android.dalvik import OP_INVOKE_VIRTUAL, Assembler, emit_const, emit_invoke
from anpyra.android.dex import build_dex
from anpyra.compiler.ir import ApplyScreenBackground
from anpyra.components import Background, Gradient, Image, StyleError
from anpyra.components.screen import alpha_byte, parse_color

SOURCE = """from anpyra import Activity, TextView
from anpyra.components import Screen, Image, Gradient, Background
class MainActivity(Activity):
    def on_create(self, state):
        screen = Screen(self)
        screen.style.bg.color = "#123456"
        screen.style.bg.gradient = Gradient(["red", "#800000ff"], direction="left_right")
        screen.style.bg.opacity = 0.6
        title = TextView(self)
        title.set_text("Styled screen")
        title.set_text_color("white")
        screen.set_content(title)
        self.set_content_view(screen)
"""


class ScreenTests(unittest.TestCase):
    def test_arbitrary_hex_and_integer_colors_preserve_argb(self):
        for value, expected in (
            ("#135", 0xFF113355),
            ("#8135", 0x88113355),
            ("#123456", 0xFF123456),
            ("#80123456", 0x80123456),
            (-1, 0xFFFFFFFF),
            (0x12345678, 0x12345678),
            ("transparent", 0),
            ("rgba(12, 34, 56, 0.5)", 0x800C2238),
        ):
            with self.subTest(value=value):
                self.assertEqual(parse_color(value), expected)

    def test_css_names_and_rgb_expressions(self):
        self.assertEqual(parse_color("ReBeccaPurple"), 0xFF663399)
        self.assertEqual(parse_color("rgb(20,30,40)"), 0xFF141E28)

    def test_invalid_colors_fail_instead_of_falling_back(self):
        for color in (True, "#12", "#z12345", "no-such-color", 0x100000000, "rgba(256,0,0,0.5)"):
            with self.subTest(color=color), self.assertRaises(StyleError):
                parse_color(color)

    def test_opacity_bounds_and_quantization(self):
        self.assertEqual([alpha_byte(value) for value in (0, 0.5, 1)], [0, 128, 255])
        self.assertEqual(Background(opacity=0.4, transparent=True).effective_opacity, 0)
        for value in (True, -0.1, 1.1, math.nan, math.inf):
            with self.assertRaises(StyleError):
                Background(opacity=value)

    def test_image_modes_paths_and_frames(self):
        self.assertEqual(Image("assets\\photo.jpg", fit="stretch").fit, "fill")
        self.assertEqual(Image("assets/a.png").path, "assets/a.png")
        for kwargs in (
            {"path": "../private.png"},
            {"path": "https://example.com/a.png"},
            {"path": "a.png", "fit": "bogus"},
            {"path": "a.png", "frame": True},
        ):
            with self.assertRaises(StyleError):
                Image(**kwargs)

    def test_gradient_configuration(self):
        self.assertEqual(
            Gradient(["#000", "#fff"], kind="radial", radius=100).colors, ("#000", "#fff")
        )
        for kwargs in (
            {"colors": ["red"]},
            {"colors": ["red", "blue"], "kind": "radial"},
            {"colors": ["red", "blue"], "direction": "bogus"},
            {"colors": ["red", "blue"], "center": (2, 0)},
        ):
            with self.assertRaises(StyleError):
                Gradient(**kwargs)

    def test_source_style_values_are_compiled_and_native_fields_registered(self):
        compiled = compile_source(SOURCE)
        style = next(op for op in compiled.ir.operations if isinstance(op, ApplyScreenBackground))
        self.assertEqual(style.background.color, "#123456")
        self.assertEqual(style.background.opacity, 0.6)
        dex = build_dex(compiled.ir)
        self.assertGreater(struct.unpack_from("<I", dex.data, 80)[0], 0)
        listing = "\n".join(dex.assembly_listing)
        self.assertIn("sget-object", listing)
        self.assertIn("invoke-super/range", listing)
        self.assertIn("setAlpha", listing)
        self.assertIn("setTextColor", listing)

    def test_screen_only_app_and_background_object_work(self):
        source = """from anpyra import Activity
from anpyra.components import Screen, Background
class MainActivity(Activity):
    def on_create(self, state):
        screen = Screen(self)
        screen.bg = Background(color="cyan", opacity=0.25)
        self.set_content_view(screen)
"""
        self.assertTrue(build_dex(compile_source(source).ir).data.startswith(b"dex\n035"))

    def test_invalid_source_style_and_missing_import_are_diagnostics(self):
        for source in (
            SOURCE.replace('"#123456"', '"not-a-color"'),
            SOURCE.replace("0.6", "2.5"),
            SOURCE.replace("screen.style.bg.opacity", "screen.style.bg.typo"),
            SOURCE.replace("Screen, Image, Gradient, Background", "Screen, Image, Background"),
        ):
            with self.assertRaisesRegex(CompileError, "app.py:"):
                compile_source(source)

    def test_style_changes_after_attachment_and_reparenting_are_rejected(self):
        with self.assertRaisesRegex(CompileError, "before attaching"):
            compile_source(SOURCE + "        screen.bg.opacity = 0.2\n")
        with self.assertRaisesRegex(CompileError, "already-parented"):
            compile_source(
                SOURCE.replace("self.set_content_view(screen)", "self.set_content_view(title)")
            )

    def test_constant_32_and_wide_invocation_actual_words(self):
        assembler = Assembler()
        emit_const(assembler, 20, 0x80123456)
        emit_invoke(
            assembler, OP_INVOKE_VIRTUAL, 7, (30, 20), ("Landroid/view/View;", "I"), 40, "test"
        )
        words, _ = assembler.assemble()
        self.assertEqual(words[:3], [0x14 | (20 << 8), 0x3456, 0x8012])
        self.assertEqual(words[3:7], [0x08 | (40 << 8), 30, 0x02 | (41 << 8), 20])
        self.assertEqual(words[-3:], [0x74 | (2 << 8), 7, 40])
