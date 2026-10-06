"""Read-only release guards for source versions and built distribution archives."""

from __future__ import annotations

import argparse
import ast
import re
import sys
import tarfile
import tomllib
import zipfile
from email.parser import BytesParser
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_PARTS = {
    ".git",
    ".venv",
    ".cache",
    ".reference",
    ".anpyra",
    ".pyandroid",
    "__pycache__",
    ".env",
    ".pypirc",
}
PRIVATE_SUFFIXES = {".apk", ".dex", ".pem", ".der", ".key", ".p12", ".pfx"}


def check_version(root: Path = ROOT, tag: str | None = None) -> tuple[str, str]:
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    name, version = project["name"], project["version"]
    tree = ast.parse((root / "src/anpyra/__init__.py").read_text(encoding="utf-8"))
    versions = [
        ast.literal_eval(node.value)
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "__version__" for target in node.targets
        )
    ]
    if versions != [version]:
        raise ValueError("pyproject.toml version and anpyra.__version__ must match")
    if tag is not None and tag != f"v{version}":
        raise ValueError(f"release tag must be v{version}, got {tag!r}")
    return name, version


def _check_paths(names: list[str]):
    if len(names) != len(set(names)):
        raise ValueError("distribution contains duplicate archive entries")
    for name in names:
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts or "\\" in name:
            raise ValueError(f"unsafe archive path: {name}")
        if PRIVATE_PARTS.intersection(path.parts) or path.suffix.lower() in PRIVATE_SUFFIXES:
            raise ValueError(f"private/generated file in distribution: {name}")


def _check_metadata(data: bytes, name: str, version: str):
    metadata = BytesParser().parsebytes(data)

    def normalize(value):
        return re.sub(r"[-_.]+", "-", value).lower()

    if normalize(metadata.get("Name", "")) != normalize(name) or metadata.get("Version") != version:
        raise ValueError("distribution name/version does not match project metadata")


def check_distributions(directory: Path, name: str, version: str):
    files = list(directory.iterdir())
    wheels = [path for path in files if path.name.endswith(".whl")]
    sources = [path for path in files if path.name.endswith(".tar.gz")]
    if len(files) != 2 or len(wheels) != 1 or len(sources) != 1:
        raise ValueError("release directory must contain exactly one wheel and one .tar.gz sdist")
    with zipfile.ZipFile(wheels[0]) as archive:
        names = archive.namelist()
        _check_paths(names)
        metadata = [name for name in names if name.endswith(".dist-info/METADATA")]
        if len(metadata) != 1 or "anpyra/py.typed" not in names:
            raise ValueError("wheel must contain one metadata record and the typing marker")
        _check_metadata(archive.read(metadata[0]), name, version)
    with tarfile.open(sources[0], "r:gz") as archive:
        members = archive.getmembers()
        names = [member.name for member in members]
        _check_paths(names)
        if any(not (member.isfile() or member.isdir()) for member in members):
            raise ValueError("source distribution must not contain links or special files")
        roots = {PurePosixPath(path).parts[0] for path in names}
        if len(roots) != 1:
            raise ValueError("source distribution must have one root directory")
        prefix = roots.pop()
        required = {"pyproject.toml", "LICENSE", "docs/pypi_readme.md", "scripts/check_release.py"}
        if not {f"{prefix}/{path}" for path in required}.issubset(names):
            raise ValueError("source distribution is missing release source/documentation files")
        record = archive.extractfile(f"{prefix}/PKG-INFO")
        if record is None:
            raise ValueError("source distribution is missing PKG-INFO")
        with record:
            _check_metadata(record.read(), name, version)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", help="require an exact vVERSION release tag")
    parser.add_argument(
        "--dist", type=Path, help="check a fresh directory containing wheel and sdist"
    )
    args = parser.parse_args(argv)
    try:
        name, version = check_version(tag=args.tag)
        if args.dist is not None:
            check_distributions(args.dist, name, version)
        print(f"Release checks OK: {name} {version}")
        return 0
    except (
        OSError,
        ValueError,
        KeyError,
        SyntaxError,
        tarfile.TarError,
        zipfile.BadZipFile,
    ) as exc:
        print(f"Release checks failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
