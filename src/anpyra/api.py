"""Public authoring API, currently supplied by the Android backend."""

from .platforms.mobile.android.api import Activity, TextView

__all__ = ["Activity", "TextView"]
