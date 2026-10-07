"""Declarative binding to the native standalone Responses API chat controller."""

from .textview import _native_only


class ChatSession:
    def __init__(
        self,
        context,
        *,
        key_input,
        message_input,
        transcript,
        status,
        send_button,
        clear_button,
        model="gpt-5.5",
    ):
        _native_only()
