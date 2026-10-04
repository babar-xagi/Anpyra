"""Create a small project that can be compiled immediately."""

import json
from pathlib import Path

from .config import AppConfig, Project

STARTER_SOURCE = """from anpyra import Activity, TextView


class MainActivity(Activity):
    def on_create(self, state):
        title = TextView(self)
        title.set_text("Hello from Anpyra!")
        self.set_content_view(title)
"""


def init_project(
    path: str | Path, *, package: str = "dev.anpyra.app", label: str = "Anpyra"
) -> Project:
    config = AppConfig(package=package, label=label)
    project = Project(Path(path), config)
    if project.root.exists() and any(project.root.iterdir()):
        raise ValueError(f"project directory must be empty: {project.root}")
    project.root.mkdir(parents=True, exist_ok=True)
    project.source_path.write_text(STARTER_SOURCE, encoding="utf-8")
    settings = (
        f"[app]\npackage = {json.dumps(package, ensure_ascii=False)}\nlabel = {json.dumps(label, ensure_ascii=False)}\n"
        'entry = "app.py"\nversion_code = 1\nversion_name = "0.1.0"\n'
        'min_sdk = 24\ntarget_sdk = 36\noutput_dir = "build"\n'
    )
    (project.root / "anpyra.toml").write_text(settings, encoding="utf-8")
    (project.root / ".gitignore").write_text("build/\n.anpyra/\n__pycache__/\n", encoding="utf-8")
    return project
