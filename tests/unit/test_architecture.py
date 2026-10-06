"""Android-only package boundaries and retained public import contracts."""

import ast
import tempfile
import unittest
from pathlib import Path

import anpyra
import pyandroid
from anpyra import build_project
from anpyra.android import codegen, dex, packaging
from anpyra.build import _zip_payload
from anpyra.compiler.frontend import compile_file


class ArchitectureTests(unittest.TestCase):
    def test_source_has_no_common_or_platform_placeholder_packages(self):
        root = Path(anpyra.__file__).parent
        self.assertFalse((root / "common").exists())
        self.assertFalse((root / "platforms").exists())
        self.assertFalse((root / "compiler/dex.py").exists())
        self.assertTrue((root / "android/screen.py").is_file())

    def test_public_and_experiment_imports_keep_the_same_objects(self):
        self.assertIs(pyandroid.Activity, anpyra.Activity)
        self.assertIs(pyandroid.TextView, anpyra.TextView)
        self.assertIs(anpyra.compile_file, compile_file)

    def test_other_targets_fail_before_reading_or_writing_a_project(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(ValueError, "Android only"):
                build_project(root / "missing", target="other")
            self.assertEqual(list(root.iterdir()), [])

    def test_packaging_has_one_canonical_implementation(self):
        self.assertIs(_zip_payload, packaging.build_unsigned_apk)

    def test_native_ui_descriptors_are_owned_by_screen_component(self):
        for module in (codegen, dex):
            tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
            descriptors = [
                node.value
                for node in ast.walk(tree)
                if isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and node.value.startswith("Landroid/")
            ]
            self.assertEqual(descriptors, [], module.__name__)
