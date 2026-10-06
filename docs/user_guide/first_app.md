# 🚀 Your First Application

Complete [installation](installation.md) first. Commands here run from the folder **containing** `myapp`, with Anpyra available in your environment. You can replace `anpyra` with `python -m anpyra`. A source checkout is not required to create your own app.

## 1️⃣ Create a project

```powershell
anpyra init myapp --package dev.example.myapp --label "My First App"
```

The directory must be new or empty. It receives `app.py`, `anpyra.toml`, and a `.gitignore` excluding generated output/signing state.

This example explicitly selects `dev.example.myapp`. If you used only `anpyra init myapp`, its default package is `dev.anpyra.app`, and its APK is named `dev.anpyra.app.apk`. Use the actual package from your `anpyra.toml` and the APK path printed by `build`.

## 2️⃣ Write the screen

Replace its `app.py` with:

```python
from anpyra import Activity, TextView


class MainActivity(Activity):
    def on_create(self, state):
        greeting: str = "My first native app from Python!"
        title = TextView(self)
        title.set_text(greeting)
        self.set_content_view(title)
```

The typed string is passed to a native TextView and displayed as the Activity's content. The superclass lifecycle call is automatic.

## 3️⃣ Check source

```powershell
anpyra check myapp
anpyra check myapp --dump-ir --dump-dalvik
```

`check` validates source and DEX generation in memory. It writes no artifacts or signing identity. Fix any reported errors using [troubleshooting](troubleshooting.md).

If you have already entered the project with `cd myapp`, use `anpyra check` or `anpyra check .`, including any dump flags. `anpyra check myapp` inside that folder would look for another nested `myapp` directory.

## 4️⃣ Build and verify

```powershell
anpyra build myapp
anpyra verify myapp/build/dev.example.myapp.apk
```

`build/` receives the APK, unsigned APK, manifest, DEX and JSON report. `.anpyra/` retains the debug signer created during the first signing step.

## 5️⃣ Install and open

With adb configured and the phone authorized:

```powershell
adb devices
anpyra install myapp/build/dev.example.myapp.apk --launch
```

For multiple devices, replace the placeholder serial:

```powershell
anpyra install myapp/build/dev.example.myapp.apk --serial DEVICE_ID --launch
```

Expect **My first native app from Python!** on screen. This is a manual runtime check, separate from building.

### 🗂️ Commands inside the project folder

If you created the default project and then ran `cd myapp`, these paths apply:

```powershell
anpyra check --dump-ir --dump-dalvik
anpyra build
anpyra install .\build\dev.anpyra.app.apk --launch
```

From its parent folder, the last path is `myapp/build/dev.anpyra.app.apk`. Replace the filename if you configured another package. An absolute APK path also works.

## 6️⃣ Update the app

Change the greeting, rebuild, and install again. Retain the package ID and both signing files for updates. `install` uses `adb install -r`; Android still applies its version/identity policies.

Increase `version_code` when advancing your app version. `version_name` is human-readable. See [configuration](configuration.md) for Anpyra's validation rules.

## 🧮 Explore the score project

This example requires the repository checkout; its `examples/` directory is not included in a normal PyPI installation. Run the following from the checkout root.

```powershell
anpyra check examples/score --dump-dalvik
anpyra build examples/score
anpyra install examples/score/build/dev.anpyra.score.apk --launch
```

It computes `80 + 5` through a compiled helper, then compares to `70`. Change `score` to `50`, rebuild/install, and expect the failure text. See its [walkthrough](../../examples/score/README.md).

Next: [language](language.md), [configuration](configuration.md), [CLI reference](cli.md).
