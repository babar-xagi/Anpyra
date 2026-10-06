import unittest
from pathlib import Path

from anpyra import CompileError, compile_source
from anpyra.android.dex import build_dex
from anpyra.compiler.ir import LoadConst
from anpyra.scaffold import STARTER_SOURCE


class CompilerTests(unittest.TestCase):
    def test_experiment_sources_remain_compatible(self):
        for fixture in (Path(__file__).parents[1] / "fixtures").glob("exp*.py"):
            with self.subTest(fixture=fixture.name):
                result = compile_source(fixture.read_text(encoding="utf-8"))
                self.assertTrue(build_dex(result.ir).data.startswith(b"dex\n035\x00"))

    def test_unsupported_constructs_have_filename_and_line(self):
        samples = [
            STARTER_SOURCE + "\nprint('must not execute')\n",
            STARTER_SOURCE.replace("from anpyra", "from other"),
            STARTER_SOURCE.replace("Activity, TextView", "Activity as Base, TextView"),
            STARTER_SOURCE.replace("class MainActivity", "@decorator\nclass MainActivity"),
            STARTER_SOURCE.replace("    def on_create", "    @decorator\n    def on_create"),
            STARTER_SOURCE.replace(
                "        title =",
                "        for n in range(5):\n            pass\n        title =",
            ),
            STARTER_SOURCE + "\nclass Other:\n    pass\n",
            STARTER_SOURCE.replace("    def on_create", "    field = 1\n    def on_create"),
        ]
        for source in samples:
            with self.subTest(source=source):
                with self.assertRaisesRegex(CompileError, r"sample.py: (line \d+:|Anpyra)"):
                    compile_source(source, source_path=Path("sample.py"))

    def test_self_reference_is_not_initialized(self):
        source = STARTER_SOURCE.replace("        title =", "        n: int = n\n        title =")
        with self.assertRaisesRegex(CompileError, "undefined variable 'n'"):
            compile_source(source)

    def test_reserved_names_cannot_be_shadowed(self):
        for name in ("self", "state", "Activity", "TextView"):
            source = STARTER_SOURCE.replace(
                "        title =", f"        {name}: int = 1\n        title ="
            )
            with (
                self.subTest(name=name),
                self.assertRaisesRegex(CompileError, "reserved name"),
            ):
                compile_source(source)

    def test_duplicate_variable_is_rejected(self):
        source = STARTER_SOURCE.replace(
            "        title =", "        n: int = 1\n        n: int = 2\n        title ="
        )
        with self.assertRaisesRegex(CompileError, "already declared"):
            compile_source(source)

    def test_negative_literals_and_boundaries(self):
        for value in (-32768, -8, -1, 0, 32767):
            source = STARTER_SOURCE.replace(
                "        title =", f"        n: int = {value}\n        title ="
            )
            ir = compile_source(source).ir
            constant = next(
                op for op in ir.operations if isinstance(op, LoadConst) and op.target == "n"
            )
            self.assertEqual(constant.value, value)
            build_dex(ir)
        for value in (-32769, 32768):
            with self.assertRaisesRegex(CompileError, "signed 16-bit"):
                compile_source(
                    STARTER_SOURCE.replace(
                        "        title =", f"        n: int = {value}\n        title ="
                    )
                )

    def test_bool_cannot_be_used_as_int(self):
        source = STARTER_SOURCE.replace("        title =", "        n: int = True\n        title =")
        with self.assertRaises(CompileError):
            compile_source(source)

    def test_branch_only_content_view_is_rejected(self):
        source = STARTER_SOURCE.replace(
            "        title =", "        flag: bool = True\n        title ="
        )
        source = source.replace(
            "        self.set_content_view(title)",
            "        if flag:\n            self.set_content_view(title)",
        )
        with self.assertRaisesRegex(CompileError, "outside branches"):
            compile_source(source)

    def test_register_limit_is_a_compile_error(self):
        locals = "".join(f"        n{i}: int = 1\n" for i in range(14))
        with self.assertRaisesRegex(CompileError, "14 registers"):
            compile_source(STARTER_SOURCE.replace("        title =", locals + "        title ="))

    def test_host_authoring_types_fail_clearly(self):
        from anpyra import Activity, TextView
        from pyandroid import Activity as LegacyActivity

        self.assertIs(Activity, LegacyActivity)
        with self.assertRaisesRegex(RuntimeError, "Build this app with Anpyra"):
            TextView(Activity())
