"""Release guards reject mismatched identities and private/stale package contents."""

import io
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.check_release import ROOT, check_distributions, check_version


class ReleaseTests(unittest.TestCase):
    def make_distributions(self, root, *, wheel_version="0.1.0", extra=None):
        metadata = f"Name: anpyra\nVersion: {wheel_version}\n"
        with zipfile.ZipFile(root / "anpyra-0.1.0-py3-none-any.whl", "w") as archive:
            archive.writestr("anpyra-0.1.0.dist-info/METADATA", metadata)
            archive.writestr("anpyra/py.typed", "")
            if extra:
                archive.writestr(extra, "should not ship")
        prefix = "anpyra-0.1.0/"
        with tarfile.open(root / "anpyra-0.1.0.tar.gz", "w:gz") as archive:
            for name in (
                "pyproject.toml",
                "LICENSE",
                "docs/pypi_readme.md",
                "scripts/check_release.py",
                "PKG-INFO",
            ):
                data = b"Name: anpyra\nVersion: 0.1.0\n" if name == "PKG-INFO" else b"placeholder"
                info = tarfile.TarInfo(prefix + name)
                info.size = len(data)
                archive.addfile(info, io.BytesIO(data))

    def test_source_versions_and_tag_must_match(self):
        name, version = check_version()
        self.assertEqual(check_version(tag=f"v{version}"), (name, version))
        with self.assertRaisesRegex(ValueError, "release tag must"):
            check_version(tag="v999.0.0")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src/anpyra").mkdir(parents=True)
            (root / "pyproject.toml").write_bytes((ROOT / "pyproject.toml").read_bytes())
            (root / "src/anpyra/__init__.py").write_text('__version__ = "999.0.0"')
            with self.assertRaisesRegex(ValueError, "must match"):
                check_version(root)

    def test_complete_matching_archives_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_distributions(root)
            check_distributions(root, "anpyra", "0.1.0")

    def test_stale_artifact_directory_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_distributions(root)
            (root / "old-release.whl").write_bytes(b"old wheel")
            with self.assertRaisesRegex(ValueError, "exactly one wheel"):
                check_distributions(root, "anpyra", "0.1.0")

    def test_wrong_wheel_metadata_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_distributions(root, wheel_version="0.2.0")
            with self.assertRaisesRegex(ValueError, "name/version"):
                check_distributions(root, "anpyra", "0.1.0")

    def test_private_generated_and_unsafe_wheel_paths_are_rejected(self):
        for name in ("anpyra/.anpyra/debug-key.pem", "anpyra/app.apk", ".pypirc", "../escape.py"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self.make_distributions(root, extra=name)
                with self.assertRaises(ValueError):
                    check_distributions(root, "anpyra", "0.1.0")

    def test_source_links_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_distributions(root)
            with tarfile.open(root / "anpyra-0.1.0.tar.gz", "w:gz") as archive:
                info = tarfile.TarInfo("anpyra-0.1.0/key")
                info.type = tarfile.SYMTYPE
                info.linkname = "../../private.pem"
                archive.addfile(info)
            with self.assertRaisesRegex(ValueError, "links or special files"):
                check_distributions(root, "anpyra", "0.1.0")
