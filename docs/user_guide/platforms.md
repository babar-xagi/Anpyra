# 🌍 Native Targets and Build Hosts

Anpyra builds Android apps today. Native iOS, Windows, macOS and Linux applications are future goals. The repository has separate folders for those backends, but they cannot build apps yet. Web is outside the target scope.

## 🖥️ Host versus target

The **host** is the computer running Python and Anpyra. The **target** is the platform running your generated app. For example, using PowerShell on Windows to build an APK means Windows host → Android target. It does not create a Windows `.exe`.

The [installation guide](installation.md) describes host setup and its validation limits. Host instructions for macOS or Linux do not imply native macOS/Linux application output.

## 📋 Check target availability

```powershell
anpyra targets
```

```text
android  mobile  available
ios      mobile  planned (not implemented)
windows  desktop planned (not implemented)
macos    desktop planned (not implemented)
linux    desktop planned (not implemented)
```

Only an `available` target can build applications. Planned entries describe future direction.

## 📱 Select Android

```powershell
anpyra check examples/hello --target android
anpyra build examples/hello --target android
```

You can omit `--target android`; it is the default. Existing Android projects and commands continue to work. `anpyra init` creates an Android project. `verify` and `install` work with Android APKs.

Selecting `--target windows` or `--target ios` gives a not-implemented error before building or creating signing files. Changing the target flag cannot convert the current Activity/TextView source into a desktop or iOS application.

See the [roadmap](../roadmap.md) for future phases and the [native architecture guide](../developer_guide/native_platforms.md) for code ownership.
