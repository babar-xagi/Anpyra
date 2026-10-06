# 🔄 Experiment Migration and FAQ

## 🧭 Move a source app from experiments 005–008

1. Install Anpyra and create a new project with `anpyra init migrated --package dev.example.migrated`.
2. Copy the experiment's `app.py` into that directory, preserving your original separately.
3. Configure package, label and versions in `anpyra.toml`.
4. Run `anpyra check migrated --dump-ir --dump-dalvik`.
5. Build, verify, and install the new APK on a phone.

`from pyandroid import Activity, TextView` remains accepted. New source should prefer `from anpyra import Activity, TextView`. The original experiment 005–008 applications are preserved as [regression fixtures](../../tests/fixtures/exp005.py).

## 🔑 Keep an existing installed identity

To update an existing experimental app, retain its exact package ID and copy the original matching `.pyandroid/debug-key.pem` and `.pyandroid/debug-cert.der` into the new project's `.anpyra/` directory. Do this before the first build creates a new pair.

Copy both files together and keep them private. Older experiment variants may not have retained a reusable signer; a random replacement cannot reproduce the previous identity. Use a new package for a separate app if the identity is unavailable. Uninstalling an old app is a deliberate action that can remove its data.

The framework does not import archived private keys automatically. Its wheel contains no experimental keys or generated APKs.

## 🏗️ What happened to experiments 001–004C?

They proved the low-level pieces: DEX container, constructors/lifecycle, native UI calls, binary manifest, APK packaging and v2 signing. These are retained through the cumulative experiment 008 backend rather than maintained as eight parallel engines. See [experiment lineage](../developer_guide/architecture.md).

## ❓ FAQ

| Question | Answer |
| --- | --- |
| Does the APK contain CPython? | No; supported source is translated into Android bytecode. |
| Can I use any pip library in app source? | No; arbitrary imports and a Python runtime are not provided. Host build tools can use ordinary Python. |
| Is this a Kivy/BeeWare wrapper? | No; the repository writes DEX, binary manifest and signing structures itself. |
| Why do Python UI types raise errors on a PC? | They are authoring/editor stubs for compiled Android calls, not desktop widgets. |
| Can I add buttons or layouts? | Planned. Adding a stub alone does not generate Android code. |
| Is target SDK the minimum phone version? | No; `min_sdk` is the minimum declared API. `target_sdk` describes the targeted platform behavior. |
| Do I need adb to build? | No; it is optional for the install command. |
| Is PyPI/store publishing ready? | The framework can be installed directly from PyPI; 0.1.3 includes native Button design, Screen styling, typography/local fonts and Android-only modules. Android release identity/app-store delivery remains planned. |
| Has framework APK installation succeeded? | The author confirmed starter APK installation on a phone. Full screen/lifecycle/score and independent checks remain to be recorded; this is not device certification. |
| Where is future work listed? | The [phased roadmap](../roadmap.md), with deliverables and acceptance criteria. |

Next: [developer guide](../developer_guide/README.md) if you want to extend the framework.
