# 👋 Hello Example

## 📄 Files

- [app.py](app.py): one Activity that creates a TextView, sets a string literal and attaches it.
- [anpyra.toml](anpyra.toml): package `dev.anpyra.hello`, label, versions, SDKs, entry and output path.

## 🚀 Run from the repository root

```powershell
anpyra check examples/hello
anpyra build examples/hello
anpyra verify examples/hello/build/dev.anpyra.hello.apk
anpyra install examples/hello/build/dev.anpyra.hello.apk --launch
```

The final command needs adb and an authorized device. Expect **Hello from Anpyra!** after launch.

## 🧠 What happens

The compiler inserts the superclass lifecycle call, lowers widget/text/attachment operations to IR, emits native calls and DEX, generates the manifest, packages and signs the APK, then verifies it. The app source is never executed on the host.

Change the greeting, rebuild and reinstall to try an update. Retain the package/signing identity. This example is the first device smoke check and remains small enough to isolate build/lifecycle problems.

Continue with [first app](../../docs/user_guide/first_app.md) or [score](../score/README.md).
