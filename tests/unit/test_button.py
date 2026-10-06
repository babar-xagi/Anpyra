"""Button model validation, subtype contracts and real DEX encodings."""

import struct
import unittest

from anpyra import Button, CompileError, compile_source
from anpyra.android.dalvik import Assembler
from anpyra.android.dex import build_dex
from anpyra.compiler.ir import ApplyButtonDesign, IfBool, NewButton, SetButtonProperty, SetTextStyle
from anpyra.components import (
    Background,
    Border,
    ButtonStyle,
    Gradient,
    Icon,
    StyleError,
    TextView,
)


def source(*lines):
    return (
        "from anpyra import Activity\nfrom anpyra.components import Button,ButtonStyle,ButtonState,Border,Icon,Background,Gradient,Font,TextStyle,Screen\nclass MainActivity(Activity):\n    def on_create(self,state):\n        button = Button(self,text='Continue')\n"
        + "".join("        " + line + "\n" for line in lines)
        + "        self.set_content_view(button)\n"
    )


class ButtonTests(unittest.TestCase):
    def test_canonical_native_subtype_and_minimal_source(self):
        self.assertTrue(issubclass(Button, TextView))
        self.assertEqual(Button.__module__, "anpyra.components.button")
        compiled = compile_source(source())
        self.assertTrue(any(isinstance(op, NewButton) for op in compiled.ir.operations))
        listing = "\n".join(build_dex(compiled.ir).assembly_listing)
        self.assertIn("Landroid/widget/Button;", listing)
        self.assertIn("Button.<init>", listing)
        self.assertNotIn("setBackground", listing)

    def test_shape_and_icon_values_validate_without_fallback_colors(self):
        style = ButtonStyle(
            bg=Background(color="transparent"),
            border=Border("#80123456", width=2.5),
            corner_radius=(1, 2, 3, 4),
            icon=Icon("assets\\photo.jpg", size=(24, 16)),
        )
        self.assertEqual(style.corner_radius, (1.0, 2.0, 3.0, 4.0))
        self.assertEqual(style.icon.path, "assets/photo.jpg")
        for keyword in (
            {"corner_radius": (-1, 2, 3, 4)},
            {"border": "red"},
            {"enabled": 1},
            {"elevation": -1},
            {"placement": "anywhere"},
            {"selectable": True},
        ):
            with self.assertRaises(StyleError):
                ButtonStyle(**keyword)
        for keyword in (
            {"path": "../private.png"},
            {"path": "image.png", "size": 0},
            {"path": "image.png", "fit": "tile"},
            {"path": "image.png", "position": "left"},
            {"path": "image.png", "opacity": 2},
        ):
            with self.assertRaises(StyleError):
                Icon(**keyword)

    def test_custom_geometry_requires_explicit_fill(self):
        for line in (
            "button.style.corner_radius = 12",
            'button.style.border = Border("red")',
            'button.style.ripple_color = "blue"',
        ):
            with self.assertRaisesRegex(CompileError, "declare button.style.bg"):
                compile_source(source(line))
        build_dex(
            compile_source(
                source(
                    'button.style.bg.color = "transparent"', 'button.style.border = Border("red")'
                )
            ).ir
        )

    def test_color_and_gradient_switches_are_explicit_alternatives(self):
        compiled = compile_source(
            source(
                'button.style.bg.color = "red"',
                'button.style.bg.gradient = Gradient(["blue","green"])',
            )
        )
        design = next(
            op.design for op in compiled.ir.operations if isinstance(op, ApplyButtonDesign)
        )
        self.assertIsNone(design.bg.color)
        self.assertEqual(design.bg.gradient.colors, ("blue", "green"))
        with self.assertRaises(StyleError):
            ButtonStyle(bg=Background(color="red", gradient=Gradient(["blue", "green"])))

    def test_nested_state_border_and_scalar_aliases_compile(self):
        compiled = compile_source(
            source(
                'button.style.background_color = "#123456"',
                "button.style.radius = 10",
                'button.style.border.color = "white"',
                "button.style.border.width = 3",
                'button.style.pressed.bg.color = "red"',
                'button.style.disabled.color = "gray"',
                'button.style.focused.border = Border("blue",width=4)',
            )
        )
        design = next(
            op.design for op in compiled.ir.operations if isinstance(op, ApplyButtonDesign)
        )
        self.assertEqual(design.corner_radius, (10.0,) * 4)
        self.assertEqual(design.border.width, 3)
        self.assertEqual(design.pressed.bg.color, "red")
        self.assertEqual(design.disabled.color, "gray")
        listing = "\n".join(build_dex(compiled.ir).assembly_listing)
        for native in (
            "state_enabled",
            "state_pressed",
            "state_focused",
            "ColorStateList;-><init>",
            "StateListDrawable;->addState",
        ):
            self.assertIn(native, listing)

    def test_button_gravity_preserves_the_native_unspecified_axis(self):
        compiled = compile_source(source('button.style.alignment = "left"'))
        operation = next(
            op
            for op in compiled.ir.operations
            if isinstance(op, SetTextStyle) and op.property == "gravity"
        )
        self.assertEqual(operation.value, ("left", None))
        self.assertIn("getGravity", "\n".join(build_dex(compiled.ir).assembly_listing))

    def test_button_can_be_screen_content_and_not_reparented(self):
        app = source("screen = Screen(self)", "screen.set_content(button)").replace(
            "self.set_content_view(button)", "self.set_content_view(screen)"
        )
        self.assertTrue(build_dex(compile_source(app).ir).data)
        # Explicitly construct a root-then-other-parent order with one Activity attachment.
        app = source(
            "self.set_content_view(button)", "screen = Screen(self)", "screen.set_content(button)"
        ).rsplit("        self.set_content_view(button)\n", 1)[0]
        with self.assertRaisesRegex(CompileError, "two parents"):
            compile_source(app)

    def test_dynamic_enabled_branches_use_typed_boolean_registers(self):
        compiled = compile_source(
            source(
                "ready: bool = False",
                "if ready:",
                "    button.set_enabled(True)",
                "else:",
                "    button.set_enabled(ready)",
            )
        )
        self.assertIn("setEnabled", "\n".join(build_dex(compiled.ir).assembly_listing))
        branch = next(op for op in compiled.ir.operations if isinstance(op, IfBool))
        self.assertIsInstance(branch.else_ops[0], SetButtonProperty)
        self.assertEqual(branch.else_ops[0].value_var, "ready")
        self.assertTrue(branch.then_ops[0].value)

    def test_style_and_callbacks_errors_have_source_context(self):
        for line in (
            "button.style.missing = 1",
            "button.style.border.width = 2",
            'button.style.bg.image = "photo.png"',
            'button.on_click("handler")',
        ):
            with self.subTest(line=line), self.assertRaisesRegex(CompileError, "bad.py: line"):
                compile_source(source(line), source_path="bad.py")
        with self.assertRaisesRegex(CompileError, "before attachment"):
            compile_source(
                source("self.set_content_view(button)", 'button.style.bg.color = "red"').rsplit(
                    "        self.set_content_view(button)\n", 1
                )[0]
            )

    def test_complete_declaration_keeps_text_and_drawable_paths_separate(self):
        app = source(
            'button.style = ButtonStyle(color="white",size=20,font=Font(family="serif",bold=True),bg=Background(color="red"),corner_radius=(1,2,3,4),border=Border("blue",width=2),ripple_color="#50ffffff",placement="center",margin=(4,8),min_width=0,min_height=0,elevation=2)'
        )
        dex = build_dex(compile_source(app).ir)
        for native in (
            "setTypeface",
            "setCornerRadii",
            "setStroke",
            "RippleDrawable;-><init>",
            "setMargins",
            "iput",
            "setStateListAnimator",
            "setMinWidth",
        ):
            self.assertIn(native, "\n".join(dex.assembly_listing))
        count, offset = struct.unpack_from("<II", dex.data, 88)
        entries = [dex.data[offset + i * 8 : offset + (i + 1) * 8] for i in range(count)]
        self.assertEqual(count, len(set(entries)))

    def test_iput_actual_words_and_register_bounds(self):
        asm = Assembler()
        asm.emit("iput", 0, 1, 9, "gravity", size=2)
        self.assertEqual(asm.assemble()[0], [0x1059, 9])
        asm = Assembler()
        asm.emit("iput", 16, 1, 9, "gravity", size=2)
        with self.assertRaises(ValueError):
            asm.assemble()


if __name__ == "__main__":
    unittest.main()
