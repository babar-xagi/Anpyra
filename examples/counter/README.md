# 🔢 Counter Lab

This example uses Anpyra 0.1.5 generic button callbacks, mutable typed state and runtime input. Install with `uv pip install "anpyra==0.1.5"` or `python -m pip install "anpyra==0.1.5"`. Example files are in the repository/source archive.

```powershell
anpyra check examples/counter --dump-dalvik
anpyra build examples/counter
anpyra install examples/counter/build/dev.anpyra.counter.apk --launch
```

Press +/− to change the count, Reset to zero it, and Pause/Resume to change native enabled state. Enter a name and press Show name. Recreate screen restores opted-in count/name while the memory-only paused flag resets. A new task without saved state starts from defaults.

The title keeps its visible window awake for testing; system settings are unchanged. [User guide](../../docs/user_guide/events.md) explains the API and [developer guide](../../docs/developer_guide/events.md) maps every implementation file.
