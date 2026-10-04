# 🧮 Score Example

## 📄 Files

- [app.py](app.py): `calculate_score(score: int, bonus: int) -> int`, typed locals, helper call and conditional text.
- [anpyra.toml](anpyra.toml): package `dev.anpyra.score` and project metadata/paths.

## 🚀 Build and inspect

```powershell
anpyra check examples/score --dump-ir --dump-dalvik
anpyra build examples/score
anpyra verify examples/score/build/dev.anpyra.score.apk
anpyra install examples/score/build/dev.anpyra.score.apk --launch
```

## 🔍 Expected flow

1. Load `score = 80` and `bonus = 5` into lifecycle registers.
2. Invoke the generated static helper and immediately read its returned int.
3. Compare `final_score = 85` against `70`.
4. Set **Passed from an Anpyra function!** and attach the TextView.

The helper is a separate DEX method with incoming parameter registers, an `add-int` instruction and an int return. It is not interpreted Python.

## 🔁 Exercise the alternate branch

Change `score` to `50`, rebuild and install using the retained identity. Expect **Failed** because the helper returns `55`. Restore the original `80` when finishing the test so the repository example keeps its documented default.

See [language reference](../../docs/user_guide/language.md) for helper restrictions and [compiler internals](../../docs/developer_guide/compiler.md) for bytecode details.
