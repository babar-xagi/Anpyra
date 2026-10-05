"""The anpyra command and python -m anpyra share this entry point."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import asdict
from importlib.metadata import version
from pathlib import Path

from . import __version__
from .build import build_project
from .platforms.mobile.android.verify import inspect_apk
from .platforms.registry import get_backend, list_targets
from .scaffold import init_project


def _dump(dex, ir, args):
    if args.dump_ir:
        print(ir.pretty())
    if args.dump_dalvik:
        for method in dex.methods:
            print(f"\n{method.name} ({method.code_units} code units)")
            print("\n".join("  " + line for line in method.assembly))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="anpyra", description="Native Python app toolchain; Android builds available today."
    )
    parser.add_argument("--version", action="version", version=f"Anpyra {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init", help="create an application project")
    init.add_argument("directory", type=Path)
    init.add_argument("--package", default="dev.anpyra.app")
    init.add_argument("--label", default="Anpyra")
    for name, help_text in (
        ("build", "build and verify a signed APK"),
        ("check", "validate source and DEX generation without writing artifacts"),
    ):
        command = commands.add_parser(name, help=help_text)
        command.add_argument("project", type=Path, nargs="?", default=Path("."))
        command.add_argument("--dump-ir", action="store_true")
        command.add_argument("--dump-dalvik", action="store_true")
        command.add_argument("--target", default="android", help="native target (default: android)")
    commands.add_parser("targets", help="list implemented and planned native targets")
    verify = commands.add_parser(
        "verify",
        help="verify an Anpyra APK's signature, content digest and DEX checksums",
    )
    verify.add_argument("apk", type=Path)
    verify.add_argument("--json", action="store_true")
    commands.add_parser("doctor", help="show host prerequisites and optional adb availability")
    install = commands.add_parser("install", help="verify and install an APK using optional adb")
    install.add_argument("apk", type=Path)
    install.add_argument("--serial", help="select the adb device")
    install.add_argument("--launch", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            project = init_project(args.directory, package=args.package, label=args.label)
            print(f"Created {project.root}")
            print(f'anpyra build "{project.root}"')
        elif args.command in {"build", "check"}:
            backend = get_backend(args.target)
            project = backend.load_project(args.project)
            if args.command == "build":
                result = build_project(project, target=args.target)
                print(f"Built {result.apk_path} ({result.apk_size} bytes)")
                print("Verified APK v2 signature, content digest, DEX SHA-1 and Adler-32.")
                print(f"Build report: {result.report_path}")
                _dump(result.dex_build, result.compile_result.ir, args)
            else:
                compiled, dex = backend.check_project(project)
                print(f"Valid: {project.source_path}; {len(dex.methods)} method listings")
                _dump(dex, compiled.ir, args)
        elif args.command == "targets":
            for target in list_targets():
                status = "available" if target.implemented else "planned (not implemented)"
                print(f"{target.name:8} {target.family:7} {status}")
        elif args.command == "verify":
            report = inspect_apk(args.apk)
            if args.json:
                print(json.dumps(asdict(report), indent=2))
            else:
                print(f"Verified {args.apk}: {report.package} / {report.activity}")
        elif args.command == "doctor":
            print(f"Anpyra: {__version__}")
            print(f"Python: {sys.version.split()[0]} ({sys.executable})")
            print(f"cryptography: {version('cryptography')}")
            print("Build prerequisites: OK")
            print(f"adb (optional for install): {shutil.which('adb') or 'not found'}")
        elif args.command == "install":
            report = inspect_apk(args.apk)
            adb = shutil.which("adb")
            if adb is None:
                raise ValueError(
                    "adb was not found on PATH; install Android platform-tools to use this command"
                )
            command = [adb] + (["-s", args.serial] if args.serial else [])
            subprocess.run(command + ["install", "-r", str(args.apk.resolve())], check=True)
            if args.launch:
                subprocess.run(
                    command
                    + [
                        "shell",
                        "am",
                        "start",
                        "-W",
                        "-n",
                        f"{report.package}/{report.activity}",
                    ],
                    check=True,
                )
        return 0
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"anpyra: {exc}", file=sys.stderr)
        return 1
