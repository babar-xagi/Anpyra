"""Public compatibility, typography diagnostics and actual emitted DEX records."""

import math
import struct
import unittest

import anpyra
import pyandroid
from anpyra import CompileError, compile_source
from anpyra.android.dex import build_dex
from anpyra.compiler.ir import SetTextStyle
from anpyra.components import Font, Shadow, StyleError, TextStyle, TextView
from anpyra.components.textview import validate_text_property


def source(*lines):
    return (
        "from anpyra import Activity,TextView,Font,Shadow,TextStyle,Screen\nclass MainActivity(Activity):\n    def on_create(self,state):\n        title = TextView(self)\n"
        + "".join("        " + line + "\n" for line in lines)
        + "        self.set_content_view(title)\n"
    )


class TextViewTests(unittest.TestCase):
    def test_historical_imports_share_the_component(self):
        self.assertIs(anpyra.TextView, TextView)
        self.assertIs(pyandroid.TextView, TextView)
        self.assertEqual(TextView.__module__, "anpyra.components.textview")

    def test_units_and_padding_forms_are_validated(self):
        self.assertEqual(TextStyle(padding=12).padding, (12.0,) * 4)
        self.assertEqual(TextStyle(padding=(4, 9)).padding, (4.0, 9.0, 4.0, 9.0))
        self.assertEqual(TextStyle(padding=(1, 2, 3, 4)).padding, (1.0, 2.0, 3.0, 4.0))
        self.assertEqual(TextStyle(size=18.5, opacity=0.3).size, 18.5)
        for size in (0, -1, True, math.nan, math.inf, 1_000_001):
            with self.subTest(size=size), self.assertRaises(StyleError):
                TextStyle(size=size)

    def test_invalid_native_options_are_rejected(self):
        for name, value in (
            ("color", "bad-color"),
            ("alignment", []),
            ("opacity", 2),
            ("padding", (-1, 2)),
            ("font", 3),
            ("max_lines", 0),
            ("lines", True),
            ("single_line", "yes"),
            ("ellipsize", "marquee"),
            ("width", "auto"),
            ("letter_spacing", -2),
            ("line_spacing", (0, 0)),
            ("unknown", 1),
        ):
            with self.subTest(name=name), self.assertRaises(StyleError):
                validate_text_property(name, value)

    def test_fonts_and_shadow_validate_source_values(self):
        self.assertEqual(Font(bold=True, italic=True).native_style, 3)
        self.assertEqual(TextStyle(font="serif").font, Font(family="serif"))
        self.assertEqual(Font(path="assets\\demo.ttf").path, "assets/demo.ttf")
        self.assertEqual(Shadow("red", dx=-2).dx, -2)
        for kwargs in (
            {"path": "../a.ttf"},
            {"path": "C:/a.ttf"},
            {"path": "a.woff"},
            {"family": "serif", "path": "a.ttf"},
            {"bold": 1},
        ):
            with self.assertRaises(StyleError):
                Font(**kwargs)

    def test_constructor_text_property_and_style_setters_compile(self):
        app = source(
            'title.text = "A title"',
            "title.set_text_size(24)",
            "title.set_padding(4, 8)",
            'title.set_font(Font(family="serif", italic=True))',
            'title.set_style(TextStyle(color="rebeccapurple", underline=True))',
        )
        compiled = compile_source(app)
        listing = "\n".join(build_dex(compiled.ir).assembly_listing)
        for method in (
            "setTextSize",
            "setPadding",
            "setTypeface",
            "setTextColor",
            "getPaintFlags",
            "setPaintFlags",
        ):
            self.assertIn(method, listing)
        app = app.replace(
            "title = TextView(self)",
            'title = TextView(self, text="Initial", style=TextStyle(size=14))',
        )
        self.assertIn("Initial", str(compile_source(app).ir.operations))

    def test_every_component_property_reaches_a_native_method(self):
        values = dict(
            keep_screen_on=True,
            color="red",
            size=24.0,
            alignment="right",
            vertical_alignment="bottom",
            padding=6,
            font=Font(family="serif", bold=True),
            background_color="#102030",
            opacity=0.7,
            width=140,
            height=80,
            lines=2,
            min_lines=1,
            max_lines=3,
            single_line=False,
            ellipsize="end",
            letter_spacing=0.2,
            line_spacing=(4, 1.2),
            include_font_padding=False,
            all_caps=True,
            underline=True,
            strikethrough=True,
            selectable=True,
            shadow=Shadow("blue", radius=1),
            text_direction="rtl",
            font_features="'kern' 0",
            content_description="Title",
        )
        app = source("title.style = " + repr(TextStyle(**values)))
        compiled = compile_source(app)
        listing = "\n".join(build_dex(compiled.ir).assembly_listing)
        for native in (
            "setKeepScreenOn",
            "setTextSize",
            "setGravity",
            "setPadding",
            "setTypeface",
            "setBackgroundColor",
            "setAlpha",
            "setLayoutParams",
            "setLines",
            "setMinLines",
            "setMaxLines",
            "setSingleLine",
            "setEllipsize",
            "setLetterSpacing",
            "setLineSpacing",
            "setIncludeFontPadding",
            "setAllCaps",
            "setPaintFlags",
            "setTextIsSelectable",
            "setShadowLayer",
            "setTextDirection",
            "setFontFeatureSettings",
            "setContentDescription",
        ):
            self.assertIn(native, listing)

    def test_font_and_alignment_updates_preserve_related_values(self):
        compiled = compile_source(
            source(
                'title.style.font = Font(family="serif", bold=True)',
                "title.style.font.italic = True",
                'title.style.alignment = "right"',
                'title.style.vertical_alignment = "bottom"',
            )
        )
        styles = [op for op in compiled.ir.operations if isinstance(op, SetTextStyle)]
        self.assertEqual(styles[1].value, Font(family="serif", bold=True, italic=True))
        self.assertEqual(styles[-1].value, ("right", "bottom"))

    def test_source_errors_have_path_and_line(self):
        for line in (
            "title.style.size = -1",
            "title.style.padding = (1, 2, 3)",
            "title.style.font.weight = 300",
            "title.style.no_such_style = 5",
            "title = TextView(self, missing=True)",
        ):
            with (
                self.subTest(line=line),
                self.assertRaisesRegex(CompileError, r"example.py: line 5:"),
            ):
                compile_source(source(line), source_path="example.py")

    def test_style_branches_and_unimported_factories_fail(self):
        app = source("enabled: bool = True", "if enabled:", '    title.set_font("serif")')
        with self.assertRaisesRegex(CompileError, "outside branches"):
            compile_source(app)
        app = source('title.style.font = Font(family="serif")').replace(
            ",Font,Shadow,TextStyle,Screen", ""
        )
        with self.assertRaisesRegex(CompileError, "import Font"):
            compile_source(app)

    def test_line_limit_conflicts_and_complete_updates(self):
        with self.assertRaisesRegex(CompileError, "min_lines"):
            compile_source(source("title.style.lines = 2", "title.style.min_lines = 3"))
        # Both limits can move together without an invalid intermediate state.
        compiled = compile_source(
            source(
                "title.style = TextStyle(min_lines=1,max_lines=2)",
                "title.style = TextStyle(min_lines=4,max_lines=5)",
            )
        )
        self.assertTrue(build_dex(compiled.ir).data)

    def test_combined_screen_and_text_references_have_unique_method_ids(self):
        app = source(
            "screen = Screen(self)",
            'screen.bg.color = "blue"',
            "title.style.opacity = .5",
            'title.style.color = "red"',
            'title.set_text_color("white")',
            "screen.set_content(title)",
        ).replace("self.set_content_view(title)", "self.set_content_view(screen)")
        data = build_dex(compile_source(app).ir).data
        count, offset = struct.unpack_from("<II", data, 88)
        ids = [data[offset + 8 * i : offset + 8 * (i + 1)] for i in range(count)]
        self.assertEqual(len(ids), len(set(ids)))

    def test_wide_frame_encodes_padding_and_shadow_with_five_arguments(self):
        app = source(
            *[f"value{i}: int = {i}" for i in range(10)],
            "title.style.padding = (1,2,3,4)",
            'title.style.shadow = Shadow("#123456",radius=2,dx=-1,dy=3)',
            'title.style.ellipsize = "end"',
        )
        dex = build_dex(compile_source(app).ir)
        self.assertGreater(len(dex.register_map), 12)
        listing = "\n".join(dex.assembly_listing)
        self.assertIn("invoke-virtual/range", listing)
        self.assertIn("Math;->round", listing)
        self.assertIn("setShadowLayer", listing)
        self.assertIn("sget-object", listing)


if __name__ == "__main__":
    unittest.main()
