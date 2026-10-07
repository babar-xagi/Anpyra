"""Signed standalone chat packaging and old non-network package behavior."""

import tempfile
import unittest
from pathlib import Path

from anpyra import build_apk
from anpyra.android.manifest_inspect import inspect_manifest


class ChatBuildTests(unittest.TestCase):
    def test_chat_build_is_reproducible_and_contains_internet_permission(self):
        source = Path(__file__).resolve().parents[2] / "examples/chatbot/app.py"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = build_apk(source, root / "output", state_dir=root / "identity")
            payload = first.apk_path.read_bytes()
            self.assertEqual(
                inspect_manifest(first.manifest_path.read_bytes())["permissions"],
                ("android.permission.INTERNET",),
            )
            second = build_apk(source, root / "output", state_dir=root / "identity")
            self.assertEqual(second.apk_path.read_bytes(), payload)
            self.assertTrue(second.verification.dex_checksum_ok)
