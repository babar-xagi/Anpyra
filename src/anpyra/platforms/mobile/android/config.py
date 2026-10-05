"""Android project configuration, including SDK levels."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, fields
from pathlib import Path

from ....common.config import ApplicationMetadata, ConfigError
from ....common.project import Project


@dataclass(frozen=True)
class AppConfig(ApplicationMetadata):
    min_sdk: int = 24
    target_sdk: int = 36
    entry: str = "app.py"
    output_dir: str = "build"

    def __post_init__(self):
        super().__post_init__()
        for name in ("entry", "output_dir"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip() or "\x00" in value:
                raise ConfigError(f"{name} must be a nonempty string without NUL characters")
        for name in ("min_sdk", "target_sdk"):
            value = getattr(self, name)
            if type(value) is not int or not 1 <= value <= 0x7FFFFFFF:
                raise ConfigError(f"{name} must be a positive signed 32-bit integer")
        if self.min_sdk < 24:
            raise ConfigError("min_sdk must be at least 24: Anpyra uses APK v2 signing")
        if self.target_sdk < self.min_sdk:
            raise ConfigError("target_sdk must be greater than or equal to min_sdk")


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
