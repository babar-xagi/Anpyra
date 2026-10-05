import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from anpyra.cli import main
from anpyra.scaffold import init_project


class CliTests(unittest.TestCase):
    def call(self, args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(args)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_targets_reports_available_and_planned_backends(self):
        code, output, error = self.call(["targets"])
        self.assertEqual((code, error), (0, ""))
        self.assertIn("android  mobile  available", output)
        self.assertIn("windows  desktop planned (not implemented)", output)
        self.assertNotIn("web", output)

    def test_planned_target_rejected_for_build_and_check(self):
        with tempfile.TemporaryDirectory() as directory:
            for command in ("build", "check"):
                code, _, error = self.call([command, directory, "--target", "ios"])
                self.assertEqual(code, 1)
                self.assertIn("planned but not implemented", error)
                self.assertEqual(list(Path(directory).iterdir()), [])

    def test_check_writes_no_artifacts_or_signing_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            project = init_project(directory)
            code, output, error = self.call(["check", directory, "--dump-dalvik"])
            self.assertEqual((code, error), (0, ""))
            self.assertIn("TextView.setText", output)
            self.assertFalse(project.output_path.exists())
            self.assertFalse(project.state_path.exists())

    def test_init_build_verify_workflow(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "hello"
            self.assertEqual(
                self.call(["init", str(project), "--package", "dev.example.hello"])[0],
                0,
            )
            self.assertEqual(self.call(["build", str(project)])[0], 0)
            code, output, error = self.call(
                ["verify", str(project / "build/dev.example.hello.apk"), "--json"]
            )
            self.assertEqual((code, error), (0, ""))
            self.assertTrue(json.loads(output)["v2_content_digest_ok"])

    def test_errors_return_nonzero(self):
        with tempfile.TemporaryDirectory() as directory:
            code, output, error = self.call(["build", directory])
            self.assertEqual(code, 1)
            self.assertIn("cannot read", error)
            code, output, error = self.call(["verify", str(Path(directory) / "missing.apk")])
            self.assertEqual(code, 1)

    def test_optional_device_command_uses_argument_lists(self):
        with tempfile.TemporaryDirectory() as directory:
            project = init_project(directory)
            self.assertEqual(self.call(["build", directory])[0], 0)
            with (
                patch("anpyra.cli.shutil.which", return_value="adb"),
                patch("anpyra.cli.subprocess.run") as run,
            ):
                code, _, _ = self.call(
                    [
                        "install",
                        str(project.output_path / "dev.anpyra.app.apk"),
                        "--serial",
                        "test device",
                        "--launch",
                    ]
                )
                self.assertEqual(code, 0)
                self.assertEqual(
                    run.call_args_list[0].args[0][:4],
                    ["adb", "-s", "test device", "install"],
                )
                self.assertEqual(
                    run.call_args_list[1].args[0][-1],
                    "dev.anpyra.app/dev.anpyra.app.MainActivity",
                )

    def test_missing_adb_is_explained(self):
        with tempfile.TemporaryDirectory() as directory:
            project = init_project(directory)
            self.assertEqual(self.call(["build", directory])[0], 0)
            with patch("anpyra.cli.shutil.which", return_value=None):
                code, _, error = self.call(
                    ["install", str(project.output_path / "dev.anpyra.app.apk")]
                )
                self.assertEqual(code, 1)
                self.assertIn("platform-tools", error)
