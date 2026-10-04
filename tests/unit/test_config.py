import tempfile
import unittest
from pathlib import Path

from anpyra import AppConfig, ConfigError, Project, load_project
from anpyra.scaffold import init_project


class ConfigTests(unittest.TestCase):
    def test_invalid_settings(self):
        for settings in (
            {"package": "hello"},
            {"package": "dev.bad-package"},
            {"label": ""},
            {"version_code": True},
            {"version_code": 0},
            {"version_name": 5},
            {"min_sdk": 23},
            {"min_sdk": 36, "target_sdk": 35},
            {"target_sdk": "36"},
        ):
            with self.subTest(settings=settings), self.assertRaises(ConfigError):
                AppConfig(**settings)

    def test_paths_cannot_escape_or_overlap(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for settings in (
                {"entry": "../app.py"},
                {"output_dir": "../build"},
                {"output_dir": str(root / "build")},
                {"output_dir": "."},
                {"entry": "build/app.py"},
                {"output_dir": ".anpyra"},
                {"entry": ".anpyra/app.py"},
            ):
                with self.subTest(settings=settings), self.assertRaises(ConfigError):
                    Project(root, AppConfig(**settings))

    def test_scaffold_roundtrip_and_custom_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            project = init_project(
                Path(directory) / "hello",
                package="dev.example.hello",
                label='Hello "World" 🐍',
            )
            self.assertEqual(load_project(project.root).config, project.config)
            self.assertEqual(load_project(project.root / "anpyra.toml"), project)
            self.assertIn("from anpyra", project.source_path.read_text())

    def test_scaffold_preserves_existing_files(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "precious.txt"
            path.write_text("keep me")
            with self.assertRaisesRegex(ValueError, "must be empty"):
                init_project(directory)
            self.assertEqual(path.read_text(), "keep me")

    def test_unknown_settings_and_invalid_toml(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "anpyra.toml"
            for text in (
                '[app]\nlable="typo"',
                '[app]\nmin_sdk="24"',
                "[other]",
                "[app",
                "[app]\n[extra]",
            ):
                path.write_text(text)
                with self.subTest(text=text), self.assertRaises(ConfigError):
                    load_project(directory)
