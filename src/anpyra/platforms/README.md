# 🌍 Native Platform Backends

`registry.py` lists native target names, families and backend availability. Mobile targets live under `mobile/`; desktop targets live under `desktop/`.

Android is the only implemented backend. iOS, Windows, macOS and Linux folders reserve future ownership and contain no build implementation. Web is outside the project's target scope.

Platform code imports reusable rules from `anpyra.common`. Keep native APIs, artifact formats and platform configuration inside the relevant target. Register a backend only after its documented build workflow works.

See [native architecture](../../../docs/developer_guide/native_platforms.md) for dispatch, dependencies and future implementation steps.
