"""Event source contracts and behavior executed from the emitted DEX bytes."""

import unittest
from pathlib import Path

from anpyra import CompileError, compile_source
from anpyra.android.dex import build_dex
from anpyra.compiler.ir import BindClick, InitAppField, StoreAppField
from tests.dex_runtime import DexRuntime, Instance, Widget

ROOT = Path(__file__).resolve().parents[2]
COUNTER = (ROOT / "examples/counter/app.py").read_text(encoding="utf-8")


def source(initial, handler):
    return (
        "from anpyra import Activity, TextView, TextInput, Button, State\n"
        "class MainActivity(Activity):\n    def on_create(self,state):\n"
        + "".join("        " + line + "\n" for line in initial)
        + "    def click(self):\n"
        + "".join("        " + line + "\n" for line in handler)
    )


BASE = [
    "self.n: int = 0",
    "label = TextView(self)",
    "self.label = label",
    "button = Button(self)",
    "button.on_click(self.click)",
    "self.set_content_view(label)",
]


def runtime(text):
    app = compile_source(text).ir
    vm, instance, widgets = DexRuntime(build_dex(app).data), Instance(), {}
    for op in app.operations:
        if isinstance(op, InitAppField):
            instance.fields["anpyra_field_" + op.name] = op.value
        elif isinstance(op, StoreAppField):
            widget = widgets.setdefault(op.value_var, Widget())
            instance.fields["anpyra_field_" + op.name] = widget
    index = 0
    for op in app.operations:
        if isinstance(op, BindClick):
            instance.fields["anpyra_click_" + str(index)] = widgets.setdefault(op.button, Widget())
            index += 1
    return vm, instance, widgets


class EventTests(unittest.TestCase):
    def test_counter_clicks_and_negative_values_dispatch_to_distinct_methods(self):
        vm, obj, views = runtime(COUNTER)
        for _ in range(3):
            vm.call("onClick", obj, views["plus"])
        self.assertEqual(views["number"].text, "3")
        for _ in range(5):
            vm.call("onClick", obj, views["minus"])
        self.assertEqual(views["number"].text, "-2")
        vm.call("onClick", obj, views["reset"])
        self.assertEqual(views["number"].text, "0")
        vm.call("onClick", obj, Widget())  # Unregistered views do not invoke another handler.
        self.assertEqual(views["number"].text, "0")

    def test_bool_not_formatting_and_disabled_controls(self):
        vm, obj, views = runtime(COUNTER)
        vm.call("onClick", obj, views["pause"])
        self.assertEqual(views["status"].text, "Paused: True")
        self.assertFalse(views["plus"].enabled)
        self.assertEqual(views["pause"].text, "Resume")
        vm.call("onClick", obj, views["plus"])
        self.assertEqual(views["number"].text, "0")
        vm.call("onClick", obj, views["pause"])
        self.assertTrue(views["plus"].enabled)
        self.assertEqual(views["status"].text, "Paused: False")

    def test_input_reading_unicode_and_empty_branch(self):
        vm, obj, views = runtime(COUNTER)
        views["entry"].text = "Babar 🐍"
        vm.call("onClick", obj, views["show"])
        self.assertEqual(views["preview"].text, "Hello, Babar 🐍!")
        self.assertEqual(views["entry"].reads, 1)
        views["entry"].text = ""
        vm.call("onClick", obj, views["show"])
        self.assertEqual(views["preview"].text, "Your name preview appears here")

    def test_saved_instance_state_is_opt_in_and_recreation_calls_native_activity(self):
        vm, obj, views = runtime(COUNTER)
        vm.call("onClick", obj, views["plus"])
        views["entry"].text = "Babar"
        vm.call("onClick", obj, views["show"])
        vm.call("onClick", obj, views["pause"])
        saved = {}
        vm.call("onSaveInstanceState", obj, saved)
        self.assertEqual(saved, {"anpyra.state.count": 1, "anpyra.state.name": "Babar"})
        _, cold, _ = runtime(COUNTER)
        vm.call("anpyra_restore_count", cold, saved)
        vm.call("anpyra_restore_name", cold, saved)
        self.assertEqual(cold.fields["anpyra_field_count"], 1)
        self.assertEqual(cold.fields["anpyra_field_name"], "Babar")
        self.assertFalse(cold.fields["anpyra_field_paused"])
        vm.call("onClick", obj, views["recreate"])
        self.assertTrue(obj.recreated)

    def test_persisted_bool_and_null_string_defense(self):
        text = source(
            BASE[:1]
            + [
                "self.flag: bool = State(True,persist=True)",
                'self.text: str = State("default",persist=True)',
            ]
            + BASE[1:],
            ["self.flag = not self.flag"],
        )
        vm, obj, _ = runtime(text)
        vm.call("anpyra_event_click", obj)
        saved = {}
        vm.call("onSaveInstanceState", obj, saved)
        self.assertEqual(saved["anpyra.state.flag"], 0)
        vm.call("anpyra_restore_text", obj, {"anpyra.state.text": None})
        self.assertEqual(obj.fields["anpyra_field_text"], "default")
        vm.call("anpyra_restore_flag", obj, {})
        self.assertEqual(obj.fields["anpyra_field_flag"], 0)

    def test_signed_32_bit_arithmetic_wraps_and_formats(self):
        for initial, operation, expected in (
            (2147483647, "+", "-2147483648"),
            (-2147483648, "-", "2147483647"),
        ):
            with self.subTest(initial=initial):
                text = source(
                    [f"self.n: int = {initial}", *BASE[1:]],
                    [f"self.n {operation}= 1", "self.label.text = str(self.n)"],
                )
                vm, obj, views = runtime(text)
                vm.call("anpyra_event_click", obj)
                self.assertEqual(views["label"].text, expected)

    def test_comparisons_bool_short_circuit_and_runtime_getters(self):
        text = source(
            BASE[:1] + ["entry = TextInput(self)", "self.entry = entry"] + BASE[1:],
            [
                "a: bool = False and bool(self.entry.get_text())",
                "b: bool = True or bool(self.entry.get_text())",
                "if a == False and b and self.label.is_enabled():",
                '    self.label.set_text("passed")',
            ],
        )
        vm, obj, views = runtime(text)
        vm.call("anpyra_event_click", obj)
        self.assertEqual(views["label"].text, "passed")
        self.assertEqual(views["entry"].reads, 0)

    def test_string_equality_null_literal_and_local_reassignment(self):
        text = source(
            BASE,
            [
                'value: str = "A\\x00🐍"',
                'value += "!"',
                'if value != "other":',
                "    self.label.text = value",
            ],
        )
        vm, obj, views = runtime(text)
        vm.call("anpyra_event_click", obj)
        self.assertEqual(views["label"].text, "A\x00🐍!")

    def test_helper_calls_and_local_data_flow(self):
        text = (
            "from anpyra import Activity, TextView, Button, State\ndef twice(n:int)->int:\n    return n+n\n"
            + source(
                BASE,
                [
                    "if self.n == 0:",
                    "    value: int = twice(5)",
                    "else:",
                    "    value: int = 1",
                    "self.n = value",
                    "self.label.text = str(value)",
                ],
            ).split("\n", 1)[1]
        )
        vm, obj, views = runtime(text)
        vm.call("anpyra_event_click", obj)
        self.assertEqual(views["label"].text, "10")
        vm.call("anpyra_event_click", obj)
        self.assertEqual(views["label"].text, "1")

    def test_invalid_state_types_and_defaults_are_rejected(self):
        for declaration in (
            "self.n: int = True",
            "self.n: int = 2147483648",
            "self.n: str = 3",
            "self.n: int = State(0,persist=1)",
            "self.n: int = State(0,unknown=True)",
            "self.n: int = self.missing",
        ):
            with self.subTest(declaration=declaration), self.assertRaises(CompileError):
                compile_source(source([declaration, *BASE[1:]], ["pass"]))

    def test_handler_shape_binding_and_recursion_are_rejected(self):
        valid = source(BASE, ["self.n += 1"])
        for original, replacement in (
            ("def click(self):", "def click(self, extra):"),
            ("button.on_click(self.click)", "button.on_click(self.click())"),
            ("self.n += 1", "self.click()"),
            ("self.n += 1", "return 1"),
        ):
            with self.subTest(replacement=replacement), self.assertRaises(CompileError):
                compile_source(valid.replace(original, replacement))
        with self.assertRaisesRegex(CompileError, "one click handler"):
            compile_source(
                valid.replace(
                    "button.on_click(self.click)",
                    "button.on_click(self.click)\n        button.on_click(self.click)",
                )
            )

    def test_captured_locals_and_undefined_fields_are_rejected(self):
        for body in (
            ['label.set_text("bad")'],
            ["self.missing = 1"],
            ['self.n = "bad"'],
            ["self.label = self.n"],
            ["self.label.set_text(self.n)"],
            ['self.label.style.color = "red"'],
        ):
            with self.subTest(body=body), self.assertRaisesRegex(CompileError, "app.py:"):
                compile_source(source(BASE, body))

    def test_branch_definite_initialization_and_type_stability(self):
        for body in (
            ["if self.n == 0:", "    value: int = 1", "self.n = value"],
            ["value: int = 1", 'value = "bad"'],
            ["if self.n == 0:", "    value: int = 1", "else:", '    value: str = "bad"'],
        ):
            with self.subTest(body=body), self.assertRaises(CompileError):
                compile_source(source(BASE, body))
        compile_source(
            source(
                BASE,
                ["if self.n == 0:", "    return", "else:", "    value: int = 2", "self.n = value"],
            )
        )

    def test_early_calls_validate_transitive_field_initialization(self):
        with self.assertRaisesRegex(CompileError, "before initialization"):
            compile_source(source(["self.click()", *BASE], ["self.n += 1"]))
        with self.assertRaisesRegex(CompileError, "recreate must only"):
            compile_source(source([*BASE, "self.click()"], ["self.recreate()"]))

    def test_references_cannot_be_rebound_and_imports_are_explicit(self):
        with self.assertRaises(CompileError):
            compile_source(source([*BASE, "self.label = label"], ["pass"]))
        with self.assertRaisesRegex(CompileError, "import State"):
            compile_source(
                source(BASE, ["pass"])
                .replace("self.n: int = 0", "self.n: int = State(0)")
                .replace(", State", "")
            )
        with self.assertRaises(CompileError):
            compile_source(
                source(BASE, ["pass"]).replace(
                    "def click(self):", "@staticmethod\n    def click(self):"
                )
            )

    def test_callback_limit_and_unused_methods_have_diagnostics(self):
        with self.assertRaisesRegex(CompileError, "8 scalar locals"):
            compile_source(source(BASE, [f"n{i}: int = {i}" for i in range(9)]))
        with self.assertRaisesRegex(CompileError, "bound or called"):
            compile_source(source(BASE, ["pass"]) + "    def unused(self):\n        pass\n")

    def test_chat_and_generic_callbacks_compose_without_reference_collisions(self):
        chat = (ROOT / "examples/chatbot/app.py").read_text(encoding="utf-8")
        mixed = chat.replace(
            "        screen.set_content(page)",
            '        self.extra: int = 0\n        extra = Button(self, text="Extra")\n        extra.on_click(self.click)\n        page.add(extra)\n        screen.set_content(page)',
        )
        mixed += "\n    def click(self):\n        self.extra += 1\n"
        dex = build_dex(compile_source(mixed).ir)
        self.assertIn(b"anpyraChatClick", dex.data)
        self.assertIn(b"anpyra_event_click", dex.data)
        with self.assertRaisesRegex(CompileError, "owns its send/clear"):
            compile_source(
                mixed.replace("extra.on_click(self.click)", "send_button.on_click(self.click)")
            )
