"""Byte-for-byte preservation of historical DEX output during component cleanup."""

import hashlib
import unittest
from pathlib import Path

from anpyra.android.dex import build_dex
from anpyra.compiler.frontend import compile_file

# Captured from the working 0.1.0 implementation before Android-only extraction.
EXPECTED = {
    "exp005.py": "71edca0753c48dd07afc3e4cd3807579a1b84afcebf3d9e78d82aed1d426495f",
    "exp006.py": "dd2cc77941dff115425b428e84fd5f8faa9dcf5842333ccab9f64c556123b007",
    "exp007.py": "74f90914958070d2b9bb736b48208cc60b121a2e1e8fcdc8ec93db61e115dedb",
    "exp008.py": "33aaf2ca9424e83570bac38825422c4572d3d5fb38bc19b2888fb3f5e5fa6359",
}


class AndroidOutputTests(unittest.TestCase):
    def test_experiment_dex_bytes_match_the_pre_cleanup_baseline(self):
        fixtures = Path(__file__).parents[1] / "fixtures"
        for name, expected in EXPECTED.items():
            with self.subTest(experiment=name):
                result = build_dex(compile_file(fixtures / name).ir)
                self.assertEqual(hashlib.sha256(result.data).hexdigest(), expected)
