import hashlib
import json
import struct
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from anpyra import CompileError, Project, build_apk, build_project
from anpyra.build import _zip_payload
from anpyra.platforms.mobile.android.manifest_inspect import inspect_manifest
from anpyra.platforms.mobile.android.signing import (
    V2SigningError,
    load_or_create_signer_material,
    sign_apk_v2,
)
from anpyra.platforms.mobile.android.verify import ApkV2VerifyError, inspect_apk
from anpyra.scaffold import init_project


class BuildTests(unittest.TestCase):
    def test_project_metadata_and_reproducible_rebuild(self):
        with tempfile.TemporaryDirectory() as directory:
            project = init_project(Path(directory) / "hello")
            project = Project(
                project.root,
                replace(
                    project.config,
                    version_code=7,
                    version_name="2.4",
                    label="Snake 🐍",
                    target_sdk=35,
                ),
            )
            first = build_project(project)
            first_bytes = first.apk_path.read_bytes()
            cert = (project.state_path / "debug-cert.der").read_bytes()
            info = inspect_manifest(first.manifest_path.read_bytes())
            self.assertEqual(
                (
                    info["versionCode"],
                    info["versionName"],
                    info["label"],
                    info["targetSdkVersion"],
                ),
                (7, "2.4", "Snake 🐍", 35),
            )
            self.assertTrue(first.verification.dex_checksum_ok)
            second = build_project(project)
            self.assertEqual(first_bytes, second.apk_path.read_bytes())
            self.assertEqual(cert, (project.state_path / "debug-cert.der").read_bytes())
            report = json.loads(second.report_path.read_text())
            self.assertEqual(report["apk_sha256"], hashlib.sha256(first_bytes).hexdigest())
            self.assertEqual(report["config"]["version_code"], 7)

    def test_failure_preserves_previous_apk(self):
        with tempfile.TemporaryDirectory() as directory:
            project = init_project(directory)
            result = build_project(project)
            previous = result.apk_path.read_bytes()
            project.source_path.write_text("print('unsupported')")
            with self.assertRaises(CompileError):
                build_project(project)
            self.assertEqual(previous, result.apk_path.read_bytes())

    def test_no_signing_identity_created_for_bad_source(self):
        with tempfile.TemporaryDirectory() as directory:
            project = init_project(directory)
            project.source_path.write_text("raise RuntimeError('never execute')")
            with self.assertRaises(CompileError):
                build_project(project)
            self.assertFalse(project.state_path.exists())
            self.assertFalse(project.output_path.exists())

    def test_incomplete_identity_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory)
            key = state / "debug-key.pem"
            key.write_text("must not replace")
            with self.assertRaisesRegex(V2SigningError, "incomplete"):
                load_or_create_signer_material(state)
            self.assertEqual(key.read_text(), "must not replace")
            self.assertFalse((state / "debug-cert.der").exists())

    def test_mismatched_identity_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            load_or_create_signer_material(root / "one")
            load_or_create_signer_material(root / "two")
            (root / "one/debug-cert.der").write_bytes((root / "two/debug-cert.der").read_bytes())
            with self.assertRaisesRegex(V2SigningError, "does not match"):
                load_or_create_signer_material(root / "one")

    def test_tampered_apk_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            result = build_project(init_project(directory))
            data = bytearray(result.apk_path.read_bytes())
            data[40] ^= 1
            result.apk_path.write_bytes(data)
            with self.assertRaisesRegex(ApkV2VerifyError, "content digest mismatch"):
                inspect_apk(result.apk_path)

    def test_valid_signature_cannot_hide_bad_dex_checksum(self):
        with tempfile.TemporaryDirectory() as directory:
            project = init_project(directory)
            result = build_project(project)
            data = bytearray(result.dex_path.read_bytes())
            struct.pack_into("<I", data, 8, 0)
            payload = _zip_payload(result.manifest_path.read_bytes(), bytes(data))
            material = load_or_create_signer_material(project.state_path)
            result.apk_path.write_bytes(sign_apk_v2(payload, material).apk)
            with self.assertRaisesRegex(ApkV2VerifyError, "DEX integrity"):
                inspect_apk(result.apk_path)

    def test_build_does_not_overwrite_source(self):
        with tempfile.TemporaryDirectory() as directory:
            project = init_project(directory)
            with self.assertRaisesRegex(ValueError, "cannot contain the source"):
                build_apk(project.source_path, project.root)
