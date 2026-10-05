"""Shared application identity and version validation."""

from __future__ import annotations

import re
from dataclasses import dataclass


class ConfigError(ValueError):
    """The project configuration cannot be used to build an app."""


@dataclass(frozen=True)
class ApplicationMetadata:
    package: str = "dev.anpyra.app"
    label: str = "Anpyra"
    version_code: int = 1
    version_name: str = "0.1.0"

    def __post_init__(self):
        for name in ("package", "label", "version_name"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip() or "\x00" in value:
                raise ConfigError(f"{name} must be a nonempty string without NUL characters")
        if not re.fullmatch(r"[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+", self.package):
            raise ConfigError(
                "package must have at least two lowercase segments, e.g. dev.example.hello"
            )
        if type(self.version_code) is not int or not 1 <= self.version_code <= 0x7FFFFFFF:
            raise ConfigError("version_code must be a positive signed 32-bit integer")
