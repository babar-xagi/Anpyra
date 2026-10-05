"""Shared project paths and output/signing-state separation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .config import ConfigError


class ProjectSettings(Protocol):
    """Path settings provided by a native backend configuration."""

    entry: str
    output_dir: str


@dataclass(frozen=True)
class Project:
    root: Path
    config: ProjectSettings

    def __post_init__(self):
        object.__setattr__(self, "root", Path(self.root).resolve())
        source = self.resolve_path(self.config.entry)
        output = self.resolve_path(self.config.output_dir)
        if output == self.root or source.is_relative_to(output):
            raise ConfigError(
                "output_dir must be a separate directory that does not contain the entry source"
            )
        state = self.root / ".anpyra"
        if (
            source.is_relative_to(state)
            or output.is_relative_to(state)
            or state.is_relative_to(output)
        ):
            raise ConfigError("entry and output_dir must be separate from .anpyra signing state")

    def resolve_path(self, value: str) -> Path:
        path = Path(value)
        if path.is_absolute() or path.drive or path.root:
            raise ConfigError(f"project path must be relative: {value}")
        resolved = (self.root / path).resolve()
        if not resolved.is_relative_to(self.root):
            raise ConfigError(f"project path escapes the project directory: {value}")
        return resolved

    @property
    def source_path(self) -> Path:
        return self.resolve_path(self.config.entry)

    @property
    def output_path(self) -> Path:
        return self.resolve_path(self.config.output_dir)

    @property
    def state_path(self) -> Path:
        return self.resolve_path(".anpyra")
