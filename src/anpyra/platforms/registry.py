"""Explicit native target inventory; planned targets cannot build artifacts."""

from dataclasses import dataclass
from importlib import import_module
from types import ModuleType


class UnsupportedTargetError(ValueError):
    """A requested native target has no implemented backend."""


@dataclass(frozen=True)
class TargetInfo:
    name: str
    family: str
    backend_module: str | None = None

    @property
    def implemented(self) -> bool:
        return self.backend_module is not None


_TARGETS = (
    TargetInfo("android", "mobile", "anpyra.platforms.mobile.android.backend"),
    TargetInfo("ios", "mobile"),
    TargetInfo("windows", "desktop"),
    TargetInfo("macos", "desktop"),
    TargetInfo("linux", "desktop"),
)


def list_targets() -> tuple[TargetInfo, ...]:
    return _TARGETS


def get_target(name: str) -> TargetInfo:
    for target in _TARGETS:
        if target.name == name:
            return target
    names = ", ".join(target.name for target in _TARGETS)
    raise UnsupportedTargetError(f"unknown native target {name!r}; native targets: {names}")


def get_backend(name: str) -> ModuleType:
    target = get_target(name)
    if target.backend_module is None:
        raise UnsupportedTargetError(
            f"{name} is planned but not implemented; only android can build apps today"
        )
    return import_module(target.backend_module)
