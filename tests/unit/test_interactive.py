"""Source contracts and independent DEX inspection for the native chat controller."""

import hashlib
import struct
import unittest
import zlib
from pathlib import Path

from anpyra import CompileError, compile_source
from anpyra.android.dex import build_dex
from anpyra.android.manifest import build_manifest
from anpyra.android.manifest_inspect import inspect_manifest
from anpyra.compiler.ir import AddLayoutChild, BindChatSession, NewTextInput
from tests.unit.test_dex import read_uleb, u32

ROOT = Path(__file__).resolve().parents[2]
CHAT = (ROOT / "examples/chatbot/app.py").read_text(encoding="utf-8")


def source(*lines):
    return (
        "from anpyra import Activity, TextView, Screen, Column, Row, ScrollView, TextInput, ChatSession, Button\n"
        "class MainActivity(Activity):\n    def on_create(self,state):\n"
        + "".join("        " + line + "\n" for line in lines)
    )


def records(data):
    """Read class definitions, field deltas and code items without using writer metadata."""
    strings = []
    for index in range(u32(data, 56)):
        _, offset = read_uleb(data, u32(data, u32(data, 60) + 4 * index))
        strings.append(data[offset : data.index(0, offset)].decode("utf-8", errors="surrogatepass"))
    types = [strings[u32(data, u32(data, 68) + 4 * index)] for index in range(u32(data, 64))]
    method_ids = u32(data, 92)
    classes = {}
    for index in range(u32(data, 96)):
        cls, flags, parent, interfaces, _, _, offset, _ = struct.unpack_from(
            "<8I", data, u32(data, 100) + 32 * index
        )
        interface_types = ()
        if interfaces:
            interface_types = tuple(
                types[struct.unpack_from("<H", data, interfaces + 4 + 2 * j)[0]]
                for j in range(u32(data, interfaces))
            )
        counts = []
        for _ in range(4):
            count, offset = read_uleb(data, offset)
            counts.append(count)
        for count in counts[:2]:
            field_index = 0
            for _ in range(count):
                delta, offset = read_uleb(data, offset)
                _, offset = read_uleb(data, offset)
                field_index += delta
                assert field_index < u32(data, 80)
        methods = {}
        for count in counts[2:]:
            method_index = 0
            for _ in range(count):
                delta, offset = read_uleb(data, offset)
                access, offset = read_uleb(data, offset)
                code, offset = read_uleb(data, offset)
                method_index += delta
                name = strings[u32(data, method_ids + 8 * method_index + 4)]
                methods[name] = (access, code)
        classes[types[cls]] = (interface_types, counts, methods)
    return classes


class InteractiveTests(unittest.TestCase):
    def test_example_and_custom_layout_values_lower(self):
        compiled = compile_source(CHAT)
        binding = next(op for op in compiled.ir.operations if isinstance(op, BindChatSession))
        self.assertEqual(binding.model, "gpt-5.5")
        password = next(
            op for op in compiled.ir.operations if isinstance(op, NewTextInput) and op.password
        )
        self.assertEqual(password.hint_color, 0xFF94A3B8)
        row = next(
            op for op in compiled.ir.operations if isinstance(op, AddLayoutChild) and op.weight == 2
        )
        self.assertEqual((row.width, row.height, row.margin), (0, 52, (0, 8, 0, 0)))

    def test_single_input_can_be_content_without_a_screen(self):
        data = build_dex(
            compile_source(
                source('entry = TextInput(self, hint="Name")', "self.set_content_view(entry)")
            ).ir
        )
        self.assertIn(b"Landroid/widget/EditText;", data.data)
        self.assertIn(b"setSaveEnabled", data.data)
        self.assertEqual(u32(data.data, 96), 1)

    def test_layout_cycles_and_reparenting_fail(self):
        for lines in (
            (
                "a = Column(self)",
                "b = Row(self)",
                "a.add(b)",
                "b.add(a)",
                "self.set_content_view(a)",
            ),
            (
                "a = Column(self)",
                "b = Row(self)",
                "t = TextView(self)",
                "a.add(t)",
                "b.add(t)",
                "self.set_content_view(a)",
            ),
            ("a = Column(self)", "a.add(a)", "self.set_content_view(a)"),
            ("a = ScrollView(self)", "a.set_content(a)", "self.set_content_view(a)"),
            ("a = Column(self)", "b = Row(self)", "a.add(b)", "self.set_content_view(b)"),
        ):
            with self.subTest(lines=lines), self.assertRaises(CompileError):
                compile_source(source(*lines))

    def test_invalid_layout_and_input_values_fail_with_diagnostics(self):
        for expression in (
            "a.add(t, weight=-1)",
            "a.add(t, width=True)",
            "a.add(t, margin=(1,2,3))",
            "a.add(t, unknown=1)",
        ):
            with self.subTest(expression=expression), self.assertRaises(CompileError):
                compile_source(
                    source(
                        "a = Column(self)",
                        "t = TextView(self)",
                        expression,
                        "self.set_content_view(a)",
                    )
                )
        for expression in (
            "TextInput(self, password=1)",
            "TextInput(self, hint=5)",
            'TextInput(self, hint_color="invalid")',
            'Column(self, color="red")',
        ):
            with self.subTest(expression=expression), self.assertRaises(CompileError):
                compile_source(source(f"a = {expression}", "self.set_content_view(a)"))

    def test_chat_binding_requires_masked_distinct_views_and_one_controller(self):
        for original, replacement in (
            ("password=True", "password=False"),
            ("message_input=message_input", "message_input=key_input"),
            ("send_button=send_button", "send_button=transcript"),
            ('model="gpt-5.5"', 'model=""'),
            (
                "        screen.set_content(page)",
                "        another = ChatSession(self)\n        screen.set_content(page)",
            ),
        ):
            with self.subTest(replacement=replacement), self.assertRaises(CompileError):
                compile_source(CHAT.replace(original, replacement))

    def test_imports_are_required_and_host_execution_is_explicit(self):
        with self.assertRaisesRegex(CompileError, "import TextInput"):
            compile_source(
                source("e = TextInput(self)", "self.set_content_view(e)").replace(", TextInput", "")
            )
        from anpyra import TextInput

        with self.assertRaises(RuntimeError):
            TextInput(None)

    def test_three_classes_have_listener_runnable_fields_and_real_exception_handlers(self):
        app = compile_source(CHAT).ir
        data = build_dex(app).data
        self.assertEqual(data, build_dex(app).data)
        self.assertEqual(data[12:32], hashlib.sha1(data[32:]).digest())
        self.assertEqual(u32(data, 8), zlib.adler32(data[12:]) & 0xFFFFFFFF)
        classes = records(data)
        self.assertEqual(len(classes), 3)
        self.assertIn("Landroid/view/View$OnClickListener;", classes[app.class_descriptor][0])
        self.assertIn(
            "Landroid/view/ViewTreeObserver$OnGlobalLayoutListener;",
            classes[app.class_descriptor][0],
        )
        worker = classes[app.class_descriptor[:-1] + "$ChatWorker;"]
        self.assertEqual(worker[0], ("Ljava/lang/Runnable;",))
        self.assertEqual(worker[1][:2], [0, 4])
        for owner, name in (
            (app.class_descriptor, "chatReply"),
            (app.class_descriptor[:-1] + "$ChatWorker;", "run"),
        ):
            code = classes[owner][2][name][1]
            self.assertEqual(code % 4, 0)
            registers, inputs, outs, tries, debug, size = struct.unpack_from("<HHHHII", data, code)
            self.assertEqual(tries, 1)
            try_offset = code + 16 + size * 2 + (2 if size % 2 else 0)
            start, count, handler_offset = struct.unpack_from("<IHH", data, try_offset)
            self.assertLess(start, size)
            self.assertLessEqual(start + count, size)
            self.assertEqual(handler_offset, 1)
            handlers = try_offset + 8
            self.assertEqual(data[handlers : handlers + 2], b"\x01\x01")
            _, offset = read_uleb(data, handlers + 2)
            handler, _ = read_uleb(data, offset)
            self.assertLess(handler, size)
            self.assertEqual(data[code + 16 + handler * 2], 0x0D)

    def test_internet_permission_is_opt_in_and_example_has_no_embedded_key(self):
        self.assertEqual(
            inspect_manifest(build_manifest("dev.test.app", "MainActivity", "App"))["permissions"],
            (),
        )
        self.assertEqual(
            inspect_manifest(build_manifest("dev.test.app", "MainActivity", "App", internet=True))[
                "permissions"
            ],
            ("android.permission.INTERNET",),
        )
        data = build_dex(compile_source(CHAT).ir).data
        self.assertIn(b"https://api.openai.com/v1/responses", data)
        self.assertIn(b"reasoning.encrypted_content", data)
        self.assertNotIn(b"sk-proj-", data)
