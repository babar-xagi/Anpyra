"""Small native multi-child layouts and scrolling containers."""

from .textview import _native_only


class Column:
    def set_enabled(self, enabled: bool) -> None:
        _native_only()

    def is_enabled(self) -> bool:
        _native_only()

    def __init__(self, context):
        _native_only()

    def add(self, view, *, width="match_parent", height="wrap_content", weight=0, margin=0):
        _native_only()

    def set_padding(self, *padding):
        _native_only()

    def set_background_color(self, color):
        _native_only()


class Row(Column):
    pass


class ScrollView:
    def set_enabled(self, enabled: bool) -> None:
        _native_only()

    def is_enabled(self) -> bool:
        _native_only()

    def __init__(self, context):
        _native_only()

    def set_content(self, view):
        _native_only()
