"""Android entry points used by native target dispatch."""

from ....common.compiler.frontend import CompileResult, compile_file
from ....common.project import Project
from .build import build_project
from .config import load_project
from .dex import DexBuild, build_dex

__all__ = ["build_project", "check_project", "load_project"]


def check_project(project: Project) -> tuple[CompileResult, DexBuild]:
    """Check source and Android code generation without writing build artifacts."""
    compiled = compile_file(
        project.source_path, package=project.config.package, label=project.config.label
    )
    return compiled, build_dex(compiled.ir)
