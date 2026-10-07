"""Typed scalar initializers with explicit opt-in Android saved-instance state."""

from typing import TypeVar

from .textview import _native_only

T = TypeVar("T", int, str, bool)


def State(default: T, *, persist: bool = False) -> T:
    """Declare a scalar Activity field; persistence is off unless requested."""
    _native_only()
