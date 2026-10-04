# 📦 Build Outputs and Signing

## 🗂️ Application after building

```text
myapp/
├── app.py
├── anpyra.toml
├── .gitignore
├── .anpyra/
│   ├── debug-key.pem
│   └── debug-cert.der
└── build/
    ├── dev.example.myapp.apk
    ├── unsigned.apk
    ├── classes.dex
    ├── AndroidManifest.xml
    └── build-report.json
```

This is generated application output, separate from the framework's `src/` tree.

## 📄 File reference

| File | What it contains | What to do with it |
| --- | --- | --- |
| `PACKAGE.apk` | v2-signed manifest + DEX package | Install this file |
| `unsigned.apk` | Package before its v2 block is added | Debug packaging; do not use as the installable result |
| `classes.dex` | Generated Android class/method bytecode | Inspect when debugging compiler output |
| `AndroidManifest.xml` | Binary Android XML | Inspect programmatically; edit source configuration instead |
| `build-report.json` | Build metadata, fingerprints, verification and method listings | Inspect/share after checking paths and app content |
| `.anpyra/debug-key.pem` | Unencrypted local debug private key | Keep private; retain for identity |
| `.anpyra/debug-cert.der` | Certificate corresponding to that key | Retain together with the key |

Both signing files are ignored by the generated `.gitignore`. Ignoring files prevents accidental tracking; it does not encrypt them.

## 🔎 JSON report

| Field | Meaning |
| --- | --- |
| `schema_version` | Current report format version, `1` |
| `source`, `output_dir` | Resolved host paths |
| `config` | Package, label, version and SDK metadata |
| `apk_sha256`, `apk_size` | Signed APK fingerprint and byte length |
| `certificate_sha256` | Fingerprint for identifying the retained certificate |
| `verification` | Structured APK/DEX integrity results and manifest metadata |
| `methods` | Method names, register maps, code-unit counts and assembly listings |

Register-map entries include source locals, synthetic temporaries, and incoming parameter registers. The report can contain literal application strings in listings, so review it before posting publicly.

## 🛡️ What verification means

Anpyra checks certificate/public-key agreement, the supported RSA signature, APK v2 content digest, expected package entries, manifest parsing, DEX magic, SHA-1 and Adler-32. Successful verification is evidence that these checks passed, not evidence of a phone installation or full DEX semantic validation.

The [v2 specification](https://source.android.com/docs/security/features/apksigning/v2) describes how protected APK sections are digested. Anpyra verifies its own constrained package profile.

## 🔁 Rebuilds and app updates

The first signing step generates a debug identity. Later builds reuse it. Keep the same package ID and both files when you want to update the same development app. If one identity file disappears or the pair does not match, restore the matching pair; Anpyra refuses to silently replace it.

Fixed ZIP timestamps/permissions and stable entry ordering make APK bytes reproducible for identical inputs, retained signer, and tool versions. The first build in a new identity directory generates new key/certificate material, so its APK differs from another identity's build.

## 🧱 Failed builds

Source validation and bytecode generation happen before signer creation. A compile failure does not replace prior APK output. After signing, files are staged and verified before publishing. Each file replacement is atomic, but replacement of the complete output set is not a single transaction; an interrupted filesystem update can leave mixed artifacts.

Deleting/rebuilding `build/` can regenerate output if needed. Keep source and `.anpyra/` identity separate. There is no CLI `clean` command yet, and release signing, key rotation, AABs and store publishing are planned features.
