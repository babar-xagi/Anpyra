# 🧩 Example Applications

Run commands from the repository root after installing Anpyra.

| Example | Demonstrates | Expected screen |
| --- | --- | --- |
| [Hello](hello/README.md) | Native Activity/TextView, simplest source/config | `Hello from Anpyra!` |
| [Score](score/README.md) | Typed helper, integer arguments/return and comparison | `Passed from an Anpyra function!` with default values |

```powershell
anpyra check examples/hello
anpyra build examples/hello
anpyra check examples/score --dump-ir --dump-dalvik
anpyra build examples/score
```

Each project has source, configuration and a walkthrough. `build/` and `.anpyra/` appear locally after building and stay out of Git. Phone behavior is verified manually using the [device checklist](../docs/developer_guide/testing.md).
