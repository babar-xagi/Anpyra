# 📱 Android Backend

This is the working native Android implementation. It consumes the shared compiler IR and produces a signed APK.

| File | Responsibility |
| --- | --- |
| `api.py` | Activity/TextView authoring stubs |
| `config.py` | Android AppConfig, SDK validation and TOML loading |
| `backend.py` | Target-dispatch entry points for check/build/loading |
| `build.py` | Compile → manifest/DEX → ZIP → signing → staged verify → artifacts |
| `dex.py` | Dalvik assembly, registers, DEX sections and checksums |
| `manifest.py` | Binary AndroidManifest.xml writer |
| `manifest_inspect.py` | Reader for generated binary manifest profile |
| `signing.py` | Retained debug identity and APK v2 signing |
| `verify.py` | Signature/content/DEX/manifest inspection |
| `__init__.py` | Package marker |

The common layer contains Python analysis and IR. Historical `anpyra.compiler` and `anpyra.android` paths forward here where appropriate; edit these canonical files for Android fixes.

Read the [Android backend guide](../../../../../docs/developer_guide/android_backend.md) and [source reference](../../../../../docs/developer_guide/source_reference.md) for functions, formats and debugging details.
