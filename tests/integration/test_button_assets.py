"""Raster icon normalization, Button font reuse and signed artifact behavior."""

import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from PIL import Image

from anpyra import build_project, compile_source
from anpyra.android.assets import AssetError
from anpyra.android.dex import build_dex
from anpyra.android.verify import inspect_apk
from anpyra.cli import main
from anpyra.scaffold import init_project

SOURCE = """from anpyra import Activity
from anpyra.components import Button,Icon
class MainActivity(Activity):
    def on_create(self,state):
        button = Button(self,text="Continue")
        button.style.icon = Icon("assets/icon.png",size=24,fit="contain")
        self.set_content_view(button)
"""


class ButtonAssetTests(unittest.TestCase):
    def project(self, directory):
        project = init_project(Path(directory) / "app")
        (project.root / "assets").mkdir()
        Image.new("RGBA", (80, 40), (20, 180, 80, 128)).save(project.root / "assets/icon.png")
        project.source_path.write_text(SOURCE, encoding="utf-8")
        return project

    def test_fit_modes_preserve_expected_alpha_and_source_geometry(self):
        for fit in ("contain", "cover", "fill"):
            with self.subTest(fit=fit), tempfile.TemporaryDirectory() as directory:
                project = self.project(directory)
                project.source_path.write_text(
                    SOURCE.replace('fit="contain"', 'fit="' + fit + '"'), encoding="utf-8"
                )
                result = build_project(project)
                report = json.loads(result.report_path.read_text())
                entry = report["assets"][0]
                self.assertEqual(entry["kind"], "button_icon")
                with zipfile.ZipFile(result.apk_path) as archive:
                    image = Image.open(io.BytesIO(archive.read(entry["entry"]))).convert("RGBA")
                    self.assertEqual(image.size, (80, 80))
                    center = image.getpixel((40, 40))
                    # RGBA resampling uses premultiplied alpha; integer RGB
                    # rounding may differ by one while alpha stays exact.
                    self.assertTrue(all(abs(a - b) <= 1 for a, b in zip(center[:3], (20, 180, 80))))
                    self.assertEqual(center[3], 128)
                    self.assertEqual(image.getpixel((40, 0))[3], 0 if fit == "contain" else 128)
                self.assertTrue(inspect_apk(result.apk_path).v2_signature_ok)
                previous = result.apk_path.read_bytes()
                self.assertEqual(build_project(project).apk_path.read_bytes(), previous)

    def test_check_writes_no_artifacts_or_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            project = self.project(directory)
            self.assertEqual(main(["check", str(project.root)]), 0)
            self.assertFalse(project.output_path.exists())
            self.assertFalse(project.state_path.exists())

    def test_missing_or_corrupt_icon_preserves_previous_output(self):
        with tempfile.TemporaryDirectory() as directory:
            project = self.project(directory)
            result = build_project(project)
            previous = result.apk_path.read_bytes()
            path = project.root / "assets/icon.png"
            path.unlink()
            with self.assertRaises(AssetError):
                build_project(project)
            path.write_bytes(b"bad image")
            with self.assertRaises(AssetError):
                build_project(project)
            self.assertEqual(previous, result.apk_path.read_bytes())

    def test_button_font_and_icon_assets_are_both_included(self):
        with tempfile.TemporaryDirectory() as directory:
            project = self.project(directory)
            font = Path(__file__).resolve().parents[2] / "examples/text_style/assets/AnpyraDemo.ttf"
            (project.root / "assets/font.ttf").write_bytes(font.read_bytes())
            source = SOURCE.replace("Button,Icon", "Button,Icon,Font").replace(
                "        self.set_content_view(button)",
                '        button.style.font = Font(path="assets/font.ttf")\n        self.set_content_view(button)',
            )
            project.source_path.write_text(source, encoding="utf-8")
            result = build_project(project)
            report = json.loads(result.report_path.read_text())
            self.assertEqual({entry["kind"] for entry in report["assets"]}, {"button_icon", "font"})
            self.assertEqual(len(inspect_apk(result.apk_path).entries), 4)

    def test_low_level_dex_requires_prepared_icons(self):
        with self.assertRaisesRegex(ValueError, "resolve Button icon"):
            build_dex(compile_source(SOURCE).ir)
