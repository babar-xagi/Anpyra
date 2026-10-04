"""Check repository-owned Markdown and compile documented app examples in memory."""

from __future__ import annotations

import ast
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {
    ".git",
    ".venv",
    ".cache",
    ".ruff_cache",
    ".reference",
    ".anpyra",
    ".pyandroid",
    "build",
    "dist",
    "__pycache__",
}
LINK = re.compile(r"\]\(([^\n)]+)\)")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")


def markdown_files() -> list[Path]:
    paths = list(ROOT.glob("*.md"))
    for name in ("docs", "examples", "tests", "src", "scripts", ".github"):
        paths.extend((ROOT / name).rglob("*.md"))
    return sorted(
        path for path in paths if not any(part in EXCLUDED for part in path.relative_to(ROOT).parts)
    )


def main() -> int:
    try:
        from anpyra import compile_source
    except ImportError as exc:
        print(f"Install Anpyra in this environment before checking docs: {exc}", file=sys.stderr)
        return 1

    failures = []
    snippets = 0
    apps = 0
    paths = markdown_files()

    def fail(path: Path, line: int, message: str):
        failures.append(f"{path.relative_to(ROOT).as_posix()}:{line}: {message}")

    def check_snippet(path: Path, line: int, info: str, body: list[str]):
        nonlocal snippets, apps
        if not info.split() or info.split()[0] not in {"python", "py"}:
            return
        snippets += 1
        source = "\n".join(body)
        try:
            tree = ast.parse(source, filename=f"{path}:{line}")
        except SyntaxError as exc:
            fail(path, line + (exc.lineno or 1), f"Python snippet syntax error: {exc.msg}")
            return
        if "unsupported" in info.split():
            return
        is_app = any(
            isinstance(node, ast.ClassDef)
            and any(isinstance(base, ast.Name) and base.id == "Activity" for base in node.bases)
            for node in tree.body
        )
        if is_app:
            try:
                compiled = compile_source(source, source_path=path)
                # Include backend generation: a valid IR alone does not prove encodability.
                from anpyra.compiler.dex import build_dex

                build_dex(compiled.ir)
                apps += 1
            except Exception as exc:
                fail(path, line, f"documented Activity example does not compile: {exc}")

    for path in paths:
        lines = path.read_text(encoding="utf-8").splitlines()
        titles = [(index, text) for index, text in enumerate(lines, 1) if text.startswith("# ")]
        if not titles:
            fail(path, 1, "missing Markdown title")
        elif not any(unicodedata.category(char) == "So" for char in titles[0][1]):
            fail(path, titles[0][0], "title should include a meaningful emoji")

        fence = None
        info = ""
        body = []
        start = 0
        for line_number, line in enumerate(lines, 1):
            marker = FENCE.match(line)
            if fence is not None:
                if (
                    marker
                    and marker.group(1)[0] == fence[0]
                    and len(marker.group(1)) >= len(fence)
                    and not marker.group(2).strip()
                ):
                    check_snippet(path, start, info, body)
                    fence = None
                else:
                    body.append(line)
                continue
            if marker:
                fence, info, start, body = marker.group(1), marker.group(2).strip(), line_number, []
                continue
            for match in LINK.finditer(line):
                target = match.group(1).strip()
                if target.startswith("<"):
                    target = target[1 : target.index(">")]
                else:
                    target = target.split(' "', 1)[0]
                url = urlsplit(target)
                if url.scheme or url.netloc or not url.path:
                    continue
                resolved = (path.parent / unquote(url.path)).resolve()
                if not resolved.is_relative_to(ROOT):
                    fail(path, line_number, f"local link escapes repository: {target}")
                elif not resolved.exists():
                    fail(path, line_number, f"missing local link target: {target}")
        if fence is not None:
            fail(path, start, "unclosed code fence")

    if failures:
        for message in failures:
            print(message, file=sys.stderr)
        print(f"Documentation checks failed: {len(failures)} issue(s).", file=sys.stderr)
        return 1
    print(
        f"Docs OK: {len(paths)} Markdown files, {snippets} Python snippets, {apps} compiled Activity examples."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
