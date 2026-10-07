"""Editor-facing native EditText; input stays on the Android device."""

from .textview import TextView, _native_only


class TextInput(TextView):
    def __init__(self, context, *, hint="", password=False, hint_color=None):
        _native_only()
