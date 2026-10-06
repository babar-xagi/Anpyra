# 📱 Android Scope and Build Computers

Anpyra currently focuses on **Android only**. Its source tree contains the Android compiler and package components needed today. There are no placeholder desktop/iOS packages or cross-platform dispatch layer.

## 🖥️ Build computer versus Android device

The build computer runs Python and Anpyra. The Android device runs the generated APK. Using PowerShell on Windows creates an Android APK; host installation instructions for Linux/macOS also describe building Android apps.

Build dependencies are Python and its installed packages. Android Studio, Java/JDK, Kotlin, Android SDK/NDK and Gradle are unnecessary for the current pipeline. Optional adb installs an already-built APK.

## 🎯 Supported target

```powershell
anpyra targets
```

```text
android  available
```

Build/check default to Android. `--target android` is retained for command compatibility; other targets are rejected. There is no platform registry.

```powershell
anpyra check myapp
anpyra build myapp
```

Inside `myapp`, omit the path or use `.`. APK filenames follow the configured package, as explained in [first app](first_app.md).

## ✅ Current evidence

The author confirmed successful phone installation of the published 0.1.0 starter app on October 6, 2026. Source checking, APK verification, public package installation and automated tests have also passed. Exact screen output, both score branches, lifecycle behavior and independent DEX inspection need separate recorded checks.

See [progress](../progress.md) for implemented components and success evidence, and [roadmap](../roadmap.md) for the Android completion phases.
