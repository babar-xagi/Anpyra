"""Public build entry points and native target dispatch."""

from __future__ import annotations

from pathlib import Path

from .common.project import Project
from .platforms.mobile.android.build import BuildResult, _zip_payload, build_apk
from .platforms.registry import get_backend

__all__ = ["BuildResult", "build_apk", "build_project", "_zip_payload"]


def build_project(project: str | Path | Project = ".", *, target: str = "android") -> BuildResult:
    """Build using an implemented native backend; Android remains the default."""
    return get_backend(target).build_project(project)
