"""Editor-facing authoring types; the compiler maps these to Android classes."""

from __future__ import annotations

from .components.textview import TextView


class Activity:
    def set_content_view(self, view: TextView) -> None:
        raise RuntimeError("Build this app with Anpyra; Android methods cannot run on the host.")
