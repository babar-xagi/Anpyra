"""Image asset decoding, APK packaging and style builds without host source execution."""

import hashlib
import io
import tempfile
import unittest
import zipfile
from pathlib import Path

from PIL import Image as PillowImage
from PIL import ImageCms, PngImagePlugin

from anpyra import build_project, compile_source
from anpyra.android.assets import AssetError, prepare_assets, validate_png
from anpyra.android.dex import build_dex
from anpyra.android.packaging import build_unsigned_apk
from anpyra.android.signing import load_or_create_signer_material, sign_apk_v2
from anpyra.android.verify import ApkV2VerifyError, inspect_apk
from anpyra.scaffold import init_project
from tests.integration import test_cli

SOURCE = """from anpyra import Activity
from anpyra.components import Screen, Image
class MainActivity(Activity):
    def on_create(self, state):
        screen = Screen(self)
        screen.bg.color = "#f0a"
        screen.bg.image = Image("assets/photo.png", fit="contain", opacity=0.5)
        self.set_content_view(screen)
"""


class ScreenAssetTests(unittest.TestCase):
    def test_profile_conversion_preserves_alpha_and_strips_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            project = self.project(directory)
            profile = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
            text = PngImagePlugin.PngInfo()
            text.add_text("private-note", "do not package metadata")
            PillowImage.new("RGBA", (31, 17), (12, 34, 56, 128)).save(
                project.root / "assets/photo.png", icc_profile=profile, pnginfo=text
            )
            assets = prepare_assets(compile_source(SOURCE).ir, project.root)
            with PillowImage.open(io.BytesIO(next(iter(assets.entries.values())))) as image:
                self.assertEqual(image.getpixel((2, 2)), (12, 34, 56, 128))
                self.assertNotIn("icc_profile", image.info)
                self.assertNotIn("private-note", image.info)

    def test_common_raster_formats_normalize_to_png(self):
        for format_, extension in (
            ("JPEG", "jpg"),
            ("WEBP", "webp"),
            ("BMP", "bmp"),
            ("TIFF", "tiff"),
            ("ICO", "ico"),
        ):
            with self.subTest(format=format_), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                PillowImage.new("RGB", (32, 32), (20, 100, 180)).save(
                    root / f"photo.{extension}", format=format_
                )
                source = SOURCE.replace("assets/photo.png", f"photo.{extension}")
                assets = prepare_assets(compile_source(source).ir, root)
                with PillowImage.open(io.BytesIO(next(iter(assets.entries.values())))) as image:
                    self.assertEqual(image.format, "PNG")
                    self.assertEqual(image.size, (32, 32))

    def test_malformed_png_is_rejected_even_with_valid_header(self):
        with self.assertRaises(AssetError):
            validate_png(b"\x89PNG\r\n\x1a\n" + b"not valid PNG chunks")

    def project(self, directory, source=SOURCE):
        project = init_project(directory)
        project.source_path.write_text(source, encoding="utf-8")
        (project.root / "assets").mkdir()
        PillowImage.new("RGBA", (31, 17), (12, 34, 56, 128)).save(project.root / "assets/photo.png")
        return project

    def test_real_rgba_pixels_are_packaged_and_signed(self):
        with tempfile.TemporaryDirectory() as directory:
            project = self.project(directory)
            result = build_project(project)
            with zipfile.ZipFile(result.apk_path) as archive:
                assets = [name for name in archive.namelist() if name.startswith("assets/")]
                self.assertEqual(len(assets), 1)
                payload = archive.read(assets[0])
                self.assertIn(hashlib.sha256(payload).hexdigest(), assets[0])
                with PillowImage.open(io.BytesIO(payload)) as image:
                    self.assertEqual(image.getpixel((4, 4)), (12, 34, 56, 128))
            self.assertTrue(inspect_apk(result.apk_path).v2_signature_ok)
            self.assertEqual(
                result.apk_path.read_bytes(), build_project(project).apk_path.read_bytes()
            )

    def test_check_validates_images_without_artifacts_or_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            project = self.project(directory)
            code, _, error = test_cli.CliTests().call(["check", directory])
            self.assertEqual((code, error), (0, ""))
            self.assertFalse(project.output_path.exists())
            self.assertFalse(project.state_path.exists())
            (project.root / "assets/photo.png").unlink()
            code, _, error = test_cli.CliTests().call(["check", directory])
            self.assertEqual(code, 1)
            self.assertIn("does not exist", error)

    def test_bad_images_fail_before_signing_and_preserve_previous_output(self):
        with tempfile.TemporaryDirectory() as directory:
            project = self.project(directory)
            result = build_project(project)
            previous = result.apk_path.read_bytes()
            (project.root / "assets/photo.png").write_bytes(b"not-an-image")
            with self.assertRaises(AssetError):
                build_project(project)
            self.assertEqual(previous, result.apk_path.read_bytes())

    def test_gif_frame_selection_is_static_and_preserves_selected_color(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = PillowImage.new("RGB", (20, 10), "red")
            second = PillowImage.new("RGB", (20, 10), "blue")
            first.save(root / "frames.gif", save_all=True, append_images=[second], duration=100)
            source = SOURCE.replace("assets/photo.png", "frames.gif").replace(
                "opacity=0.5", "opacity=0.5, frame=1"
            )
            assets = prepare_assets(compile_source(source).ir, root)
            with PillowImage.open(io.BytesIO(next(iter(assets.entries.values())))) as image:
                self.assertEqual(image.getpixel((5, 5)), (0, 0, 255, 255))

    def test_low_level_dex_rejects_unresolved_image(self):
        with self.assertRaisesRegex(ValueError, "resolve screen image"):
            build_dex(compile_source(SOURCE).ir)

    def test_packaging_rejects_misnamed_images(self):
        with self.assertRaisesRegex(ValueError, "invalid screen asset"):
            build_unsigned_apk(b"xml", b"dex", {"assets/../private.png": b"bytes"})

    def test_valid_signature_does_not_hide_bad_asset_digest(self):
        with tempfile.TemporaryDirectory() as directory:
            project = self.project(directory)
            result = build_project(project)
            with zipfile.ZipFile(result.apk_path) as archive:
                records = {name: archive.read(name) for name in archive.namelist()}
            asset = next(name for name in records if name.startswith("assets/"))
            records[asset] = records[asset] + b"changed"
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, "w") as archive:
                for name, data in records.items():
                    archive.writestr(name, data)
            signer = load_or_create_signer_material(project.state_path)
            result.apk_path.write_bytes(sign_apk_v2(buffer.getvalue(), signer).apk)
            with self.assertRaisesRegex(ApkV2VerifyError, "image digest"):
                inspect_apk(result.apk_path)
