"""Font asset boundaries, native font references and signed APK verification."""

import io
import json
import struct
import tempfile
import unittest
import zipfile
from pathlib import Path

from anpyra import build_project, compile_source
from anpyra.android.assets import AssetError
from anpyra.android.dex import build_dex
from anpyra.android.fonts import validate_font
from anpyra.android.packaging import build_unsigned_apk
from anpyra.android.signing import sign_apk_v2
from anpyra.android.verify import ApkV2VerifyError, inspect_apk
from anpyra.cli import main
from anpyra.scaffold import init_project

ASSETS = Path(__file__).resolve().parents[2] / "examples/text_style/assets"
SOURCE = """from anpyra import Activity,TextView,Font
class MainActivity(Activity):
    def on_create(self,state):
        title = TextView(self, text="Title")
        title.style.font = Font(path="assets/demo.ttf", bold=True)
        self.set_content_view(title)
"""


class TextFontTests(unittest.TestCase):
    def project(self, directory, extension="ttf"):
        project = init_project(Path(directory) / "app")
        (project.root / "assets").mkdir()
        (project.root / f"assets/demo.{extension}").write_bytes(
            (ASSETS / f"AnpyraDemo.{extension}").read_bytes()
        )
        project.source_path.write_text(
            SOURCE.replace("demo.ttf", "demo." + extension), encoding="utf-8"
        )
        return project

    def test_ttf_and_otf_are_packaged_without_modifying_font_bytes(self):
        for extension in ("ttf", "otf"):
            with self.subTest(extension=extension), tempfile.TemporaryDirectory() as directory:
                project = self.project(directory, extension)
                result = build_project(project)
                report = json.loads(result.report_path.read_text())
                entry = report["assets"][0]["entry"]
                self.assertEqual(report["assets"][0]["kind"], "font")
                with zipfile.ZipFile(result.apk_path) as archive:
                    self.assertEqual(
                        archive.read(entry), (ASSETS / f"AnpyraDemo.{extension}").read_bytes()
                    )
                self.assertTrue(inspect_apk(result.apk_path).v2_signature_ok)
                first = result.apk_path.read_bytes()
                self.assertEqual(build_project(project).apk_path.read_bytes(), first)

    def test_font_check_creates_no_build_outputs_or_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            project = self.project(directory)
            self.assertEqual(main(["check", str(project.root)]), 0)
            self.assertFalse(project.state_path.exists())
            self.assertFalse(project.output_path.exists())

    def test_missing_and_invalid_fonts_preserve_previous_apk(self):
        with tempfile.TemporaryDirectory() as directory:
            project = self.project(directory)
            result = build_project(project)
            previous = result.apk_path.read_bytes()
            path = project.root / "assets/demo.ttf"
            path.unlink()
            with self.assertRaises(AssetError):
                build_project(project)
            path.write_bytes(b"not a font")
            with self.assertRaises(AssetError):
                build_project(project)
            self.assertEqual(previous, result.apk_path.read_bytes())

    def test_sfnt_directory_and_content_must_be_valid(self):
        payload = (ASSETS / "AnpyraDemo.ttf").read_bytes()
        for wrong in (b"", b"ttcf" + payload[4:], payload[:30], b"OTTO" + payload[4:]):
            with self.assertRaises(ValueError):
                validate_font(wrong, ".ttf")
        broken = bytearray(payload)
        struct.pack_into(">I", broken, 20, len(payload) + 100)
        with self.assertRaisesRegex(ValueError, "out-of-bounds"):
            validate_font(bytes(broken), ".ttf")

    def test_low_level_dex_requires_resolved_font_assets(self):
        with self.assertRaisesRegex(ValueError, "resolve local font"):
            build_dex(compile_source(SOURCE).ir)

    def test_valid_signature_cannot_hide_invalid_font_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            project = self.project(directory)
            result = build_project(project)
            buffer = io.BytesIO()
            with (
                zipfile.ZipFile(result.apk_path) as original,
                zipfile.ZipFile(buffer, "w") as altered,
            ):
                for name in original.namelist():
                    payload = original.read(name)
                    if name.endswith(".ttf"):
                        payload = b"invalid font"
                        import hashlib

                        name = "assets/anpyra/" + hashlib.sha256(payload).hexdigest() + ".ttf"
                    altered.writestr(name, payload)
            tampered = project.root / "bad-font.apk"
            tampered.write_bytes(sign_apk_v2(buffer.getvalue()).apk)
            with self.assertRaisesRegex(ApkV2VerifyError, "asset payload"):
                inspect_apk(tampered)

    def test_packager_rejects_misnamed_fonts_and_invalid_payloads(self):
        with self.assertRaises(ValueError):
            build_unsigned_apk(b"manifest", b"dex", {"assets/font.ttf": b"data"})
        with self.assertRaises(ValueError):
            build_unsigned_apk(b"manifest", b"dex", {"assets/anpyra/" + "0" * 64 + ".ttf": b"data"})
