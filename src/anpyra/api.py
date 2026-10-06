"""Editor-facing authoring types; the compiler maps these to Android classes."""

from __future__ import annotations


class Activity:
    def set_content_view(self, view: TextView) -> None:
        raise RuntimeError("Build this app with Anpyra; Android methods cannot run on the host.")


class TextView:
    def __init__(self, context: Activity) -> None:
        raise RuntimeError("Build this app with Anpyra; Android widgets cannot run on the host.")

    def set_text(self, text: str) -> None:
        raise RuntimeError("Build this app with Anpyra; Android widgets cannot run on the host.")
