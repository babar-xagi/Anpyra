"""Compatibility import path; implementation lives in anpyra.common.compiler.ir."""

from importlib import import_module as _import_module

_implementation = _import_module("anpyra.common.compiler.ir")
__all__ = [name for name in dir(_implementation) if not name.startswith("_")]


def __getattr__(name):
    return getattr(_implementation, name)


def __dir__():
    return sorted(set(globals()) | set(dir(_implementation)))
