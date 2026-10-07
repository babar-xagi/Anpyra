# 🔢 Counter Lab

Unreleased source example for generic button callbacks, mutable typed state and runtime input. Install the editable checkout with `uv pip install -e ".[dev]"`; published 0.1.4 does not include these new APIs.

```powershell
anpyra check examples/counter --dump-dalvik
anpyra build examples/counter
anpyra install examples/counter/build/dev.anpyra.counter.apk --launch
```

Press +/− to change the count, Reset to zero it, and Pause/Resume to change native enabled state. Enter a name and press Show name. Recreate screen restores opted-in count/name while the memory-only paused flag resets. A new task without saved state starts from defaults.

The title keeps its visible window awake for testing; system settings are unchanged. [User guide](../../docs/user_guide/events.md) explains the API and [developer guide](../../docs/developer_guide/events.md) maps every implementation file.
