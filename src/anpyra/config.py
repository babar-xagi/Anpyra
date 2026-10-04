"""Validated application metadata and project-relative paths."""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, fields
from pathlib import Path


class ConfigError(ValueError):
    """The project configuration cannot be used to build an app."""


@dataclass(frozen=True)
class AppConfig:
    package: str = "dev.anpyra.app"
    label: str = "Anpyra"
    version_code: int = 1
    version_name: str = "0.1.0"
    min_sdk: int = 24
    target_sdk: int = 36
    entry: str = "app.py"
    output_dir: str = "build"

    def __post_init__(self):
        for name in ("package", "label", "version_name", "entry", "output_dir"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip() or "\x00" in value:
                raise ConfigError(f"{name} must be a nonempty string without NUL characters")
        if not re.fullmatch(r"[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+", self.package):
            raise ConfigError(
                "package must have at least two lowercase segments, e.g. dev.example.hello"
            )
        for name in ("version_code", "min_sdk", "target_sdk"):
            value = getattr(self, name)
            if type(value) is not int or not 1 <= value <= 0x7FFFFFFF:
                raise ConfigError(f"{name} must be a positive signed 32-bit integer")
        if self.min_sdk < 24:
            raise ConfigError("min_sdk must be at least 24: Anpyra uses APK v2 signing")
        if self.target_sdk < self.min_sdk:
            raise ConfigError("target_sdk must be greater than or equal to min_sdk")


@dataclass(frozen=True)
class Project:
    root: Path
    config: AppConfig

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


def load_project(path: str | Path = ".") -> Project:
    path = Path(path).resolve()
    config_path = path / "anpyra.toml" if path.is_dir() else path
    try:
        data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ConfigError(f"cannot read {config_path}: {exc}") from exc
    if set(data) != {"app"} or not isinstance(data["app"], dict):
        raise ConfigError("anpyra.toml must contain one [app] table")
    unknown = set(data["app"]) - {field.name for field in fields(AppConfig)}
    if unknown:
        raise ConfigError(f"unknown app settings: {', '.join(sorted(unknown))}")
    return Project(config_path.parent, AppConfig(**data["app"]))
