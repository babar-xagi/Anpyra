# 📱 Android Implementation

Each component has one canonical implementation here. Build orchestration is in ../build.py; Python analysis/IR are in ../compiler/.

| File | What it implements |
| --- | --- |
| screen.py | Activity/TextView native descriptors and screen-operation bytecode emission |
| codegen.py | Constructor/lifecycle/helpers, registers, math, calls and branches |
| dalvik.py | Opcodes, instruction/code-item formats, symbolic labels and assembler |
| dex_types.py | Prototype/method keys and DEX/listing records |
| encoding.py | Alignment, ULEB128, modified UTF-8 and string ordering |
| dex.py | Reference pools/indexes, DEX file sections, class metadata/checksums |
| manifest.py | Binary manifest writer |
| manifest_inspect.py | Generated manifest reader |
| packaging.py | Deterministic unsigned APK ZIP |
| signing.py | RSA debug identity and APK v2 signature block |
| verify.py | APK signature/content, manifest and DEX inspection |
| __init__.py | Package marker; no dispatch registry |

Read the [component guide](../../../docs/developer_guide/android_components.md) and [source reference](../../../docs/developer_guide/source_reference.md). Android itself renders views; screen.py generates its native calls.
