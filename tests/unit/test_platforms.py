"""Native dispatch, shared-layer boundaries and historical import contracts."""

import ast
import importlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

from anpyra import AppConfig, build_project
from anpyra.common.config import ApplicationMetadata
from anpyra.platforms.registry import UnsupportedTargetError, get_backend, list_targets


class PlatformTests(unittest.TestCase):
    def test_only_android_is_available_and_web_is_excluded(self):
        targets = list_targets()
        self.assertEqual([target.name for target in targets if target.implemented], ["android"])
        self.assertEqual(
            {target.name: target.family for target in targets},
            {
                "android": "mobile",
                "ios": "mobile",
                "windows": "desktop",
                "macos": "desktop",
                "linux": "desktop",
            },
        )
        self.assertEqual(get_backend("android").__name__, "anpyra.platforms.mobile.android.backend")
        with self.assertRaisesRegex(UnsupportedTargetError, "unknown native target"):
            get_backend("web")

    def test_planned_builds_fail_before_project_reads_or_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for target in ("ios", "windows", "macos", "linux"):
                with self.subTest(target=target):
                    with self.assertRaisesRegex(
                        UnsupportedTargetError, "planned but not implemented"
                    ):
                        build_project(root / "no-project", target=target)
                    self.assertEqual(list(root.iterdir()), [])

    def test_common_modules_do_not_import_platform_or_public_facades(self):
        common = importlib.import_module("anpyra.common")
        root = Path(common.__file__).parent
        for path in root.rglob("*.py"):
            relative = path.relative_to(root).with_suffix("")
            package = ".".join(("anpyra", "common", *relative.parts[:-1]))
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                names = []
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    name = "." * node.level + (node.module or "")
                    names = [importlib.util.resolve_name(name, package)]
                for name in names:
                    if name.startswith("anpyra"):
                        self.assertTrue(name.startswith("anpyra.common"), f"{path}: {name}")

    def test_shared_metadata_has_no_sdk_settings(self):
        shared = ApplicationMetadata("dev.example.hello", "Hello", 3, "1.2")
        android = AppConfig("dev.example.hello", "Hello", 3, "1.2", 24, 35)
        self.assertIsInstance(android, ApplicationMetadata)
        for field in ("package", "label", "version_code", "version_name"):
            self.assertEqual(getattr(shared, field), getattr(android, field))
        self.assertFalse(hasattr(shared, "min_sdk"))
        self.assertEqual((android.min_sdk, android.target_sdk), (24, 35))

    def test_historical_modules_forward_the_same_implementation_objects(self):
        mappings = {
            "compiler.frontend": ("common.compiler.frontend", "CompileError", "compile_source"),
            "compiler.ir": ("common.compiler.ir", "AppIR", "LoadConst"),
            "compiler.dex": ("platforms.mobile.android.dex", "build_dex", "DexBuild"),
            "android.manifest": ("platforms.mobile.android.manifest", "build_manifest"),
            "android.manifest_inspect": (
                "platforms.mobile.android.manifest_inspect",
                "inspect_manifest",
            ),
            "android.signing": (
                "platforms.mobile.android.signing",
                "sign_apk_v2",
                "V2SigningError",
            ),
            "android.verify": ("platforms.mobile.android.verify", "inspect_apk", "ApkReport"),
            "api": ("platforms.mobile.android.api", "Activity", "TextView"),
            "config": ("platforms.mobile.android.config", "AppConfig", "load_project"),
            "build": ("platforms.mobile.android.build", "BuildResult", "build_apk", "_zip_payload"),
        }
        for old, (new, *names) in mappings.items():
            old_module = importlib.import_module(f"anpyra.{old}")
            new_module = importlib.import_module(f"anpyra.{new}")
            for name in names:
                with self.subTest(module=old, symbol=name):
                    self.assertIs(getattr(old_module, name), getattr(new_module, name))
