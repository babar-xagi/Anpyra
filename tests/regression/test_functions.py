# Adapted from the user-provided Experiment 008 tests.
import tempfile
import unittest
import zipfile
from pathlib import Path

from anpyra.build import build_apk
from anpyra.common.compiler.frontend import CompileError, compile_source
from anpyra.common.compiler.ir import CallFunction, IntBinary, ReturnValue
from anpyra.platforms.mobile.android.dex import build_dex
from anpyra.platforms.mobile.android.verify import inspect_apk

SOURCE = """\
from pyandroid import Activity, TextView

def calculate_score(score: int, bonus: int) -> int:
    return score + bonus

class MainActivity(Activity):
    def on_create(self, state):
        score: int = 80
        bonus: int = 5
        final_score: int = calculate_score(score, bonus)
        title = TextView(self)
        if final_score >= 70:
            title.set_text("Passed from Python function!")
        else:
            title.set_text("Failed")
        self.set_content_view(title)
"""


class FunctionRegressionTests(unittest.TestCase):
    def test_function_ir(self):
        ir = compile_source(SOURCE).ir
        self.assertEqual(len(ir.functions), 1)
        fn = ir.functions[0]
        self.assertEqual(fn.name, "calculate_score")
        self.assertEqual(fn.parameters, (("score", "int"), ("bonus", "int")))
        self.assertEqual(fn.return_type, "int")
        self.assertTrue(any(isinstance(x, IntBinary) for x in fn.operations))
        self.assertTrue(any(isinstance(x, ReturnValue) for x in fn.operations))

    def test_call_lowers_to_ir(self):
        ir = compile_source(SOURCE).ir
        calls = [x for x in ir.operations if isinstance(x, CallFunction)]
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].target, "final_score")
        self.assertEqual(calls[0].args, ("score", "bonus"))

    def test_dalvik_has_static_call_and_result(self):
        d = build_dex(compile_source(SOURCE).ir)
        main = next(m for m in d.methods if m.name == "onCreate")
        txt = "\n".join(main.assembly)
        self.assertIn("invoke-static", txt)
        self.assertIn("move-result", txt)

    def test_helper_has_return(self):
        d = build_dex(compile_source(SOURCE).ir)
        fn = next(m for m in d.methods if m.name == "calculate_score")
        txt = "\n".join(fn.assembly)
        self.assertIn("add-int", txt)
        self.assertIn("return v", txt)

    def test_subtraction_helper(self):
        s = SOURCE.replace("return score + bonus", "return score - bonus")
        fn = next(m for m in build_dex(compile_source(s).ir).methods if m.name == "calculate_score")
        self.assertIn("sub-int", "\n".join(fn.assembly))

    def test_rejects_wrong_argument_count(self):
        s = SOURCE.replace("calculate_score(score, bonus)", "calculate_score(score)")
        with self.assertRaises(CompileError):
            compile_source(s)

    def test_rejects_untyped_function_parameter(self):
        s = SOURCE.replace("score: int, bonus: int", "score, bonus: int")
        with self.assertRaises(CompileError):
            compile_source(s)

    def test_builds_v2_apk(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            sp = td / "app.py"
            sp.write_text(SOURCE, encoding="utf-8")
            r = build_apk(sp, td / "build")
            rep = inspect_apk(r.apk_path)
            self.assertEqual(rep.package, "dev.anpyra.app")
            self.assertTrue(rep.v2_signature_ok and rep.v2_content_digest_ok and rep.dex_sha1_ok)

    def test_apk_payload(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            sp = td / "app.py"
            sp.write_text(SOURCE, encoding="utf-8")
            r = build_apk(sp, td / "build")
            with zipfile.ZipFile(r.apk_path) as z:
                self.assertEqual(set(z.namelist()), {"AndroidManifest.xml", "classes.dex"})


if __name__ == "__main__":
    unittest.main()
