# 🤖 Manifest, APK and Signing Backend

Relevant files: [manifest.py](../../src/anpyra/android/manifest.py), [manifest_inspect.py](../../src/anpyra/android/manifest_inspect.py), [signing.py](../../src/anpyra/android/signing.py), [verify.py](../../src/anpyra/android/verify.py), and [build.py](../../src/anpyra/build.py).

## 📄 Binary manifest

The writer emits Android resource XML chunks rather than text XML. `StringPool` places framework attribute names with their resource IDs, ordinary strings, indexes and encoded lengths into a UTF-8 string pool. UTF-16 lengths are stored alongside UTF-8 byte lengths, which matters for Unicode labels.

`BinaryXmlBuilder` writes namespace start/end, element start/end and typed attributes. Its fixed profile contains package/version metadata, min/target SDK, application label, one exported Activity and a MAIN/LAUNCHER intent filter.

| Attribute kind | Encoding |
| --- | --- |
| String | String-pool index with string type |
| Integer | Integer typed value |
| Boolean | Android boolean typed value |

`inspect_manifest` reads this UTF-8/no-style profile and extracts metadata. It validates basic chunk bounds and element balance. It is not a general resource XML implementation or complete validation against Android's package manager.

If adding a permission, icon, theme, resource or Activity, account for resource IDs, string pool entries, writer structure, reader expectations and manifest tests together.

## 📦 Unsigned packaging

`_zip_payload` creates exactly two entries in a stable order: binary `AndroidManifest.xml` and `classes.dex`. It fixes ZIP timestamps and file permission metadata and uses deflate compression. ZIP64, resources, assets and multiple DEX files are unsupported.

The filename/ZIP entry order is part of current reproducibility behavior. New artifacts need an explicit packaging contract and an updated verifier profile rather than an extra `writestr` alone.

## 🔑 Debug identity

`generate_signer_material` creates an RSA-2048 key and self-signed `Anpyra Debug` certificate. `load_or_create_signer_material` retains the PEM private key and DER certificate under the supplied directory.

The loader checks that both exist together, the key is RSA, and certificate/public-key bytes match. A partial/mismatched identity fails. Build orchestration always uses retained material; calling the low-level signer without material creates an ephemeral identity.

Private key bytes are unencrypted in this debug workflow. Ignore rules keep them out of version control; protected release key storage/import, key rotation, expiry policy and concurrent identity creation are not implemented release guarantees.

## ✍️ v2 signing flow

The implementation follows the primary [APK v2 signing specification](https://source.android.com/docs/security/features/apksigning/v2). These steps describe Anpyra's single-signer/RSA-SHA-256 profile:

1. Find the unsigned ZIP's end-of-central-directory (EOCD) record and validate offsets.
2. Split bytes before the central directory, the central directory, and the EOCD.
3. Compute chunked SHA-256 content digest, treating the EOCD central-directory offset as the signing-block start.
4. Serialize digest, certificate and empty additional-attribute records into signed data.
5. Sign that data using RSA PKCS#1 v1.5 with SHA-256 and include public-key bytes.
6. Build the v2 ID-value pair and APK signing block, including mirrored size fields and magic.
7. Insert the block before the central directory, then patch the final EOCD offset for normal ZIP readers.

The bytes used for the content digest and the bytes stored in the final EOCD differ in that central-directory offset. Applying only the final offset while computing the digest produces an invalid APK signature profile.

## ✅ Verification flow

`inspect_apk` locates and parses the block, enforces one signer and the supported algorithm, checks certificate/public-key consistency and verifies the signature. It recomputes content digest with the signing-block-start offset treatment.

It then reads exactly the expected two entries, decodes manifest metadata, and checks DEX magic/SHA-1/Adler-32. A failed check raises; a returned `ApkReport` contains successful flags.

This verifies the generated profile's integrity. It does not certify signer trust, app store acceptance, all DEX instruction constraints, device installability, or arbitrary APKs. Writer/reader share code and assumptions, so independent verification is needed before a stronger release claim.

## 🧱 Output publication

`build_apk` verifies the signed APK in a temporary staging directory, writes report/other artifacts there, and replaces the destination files after checks pass. Compilation failures preserve an earlier APK. A failure between multiple file replacements can leave an inconsistent artifact set; they are not one transaction.

Configuration validation and source/Dex generation precede signer loading. APK verification follows signing and precedes output publication. Preserve this ordering when adding stages.

## 🧪 Test and extension checklist

Current integration tests cover Unicode/version metadata, stable rebuild bytes, matching retained identity, partial/mismatched identity rejection, content tampering, and a validly signed payload with a bad DEX checksum.

Add focused tests for the exact structure you change. For broadening the profile, plan malformed input, extra entries, multiple signers, large ZIP fields and independent Android checks. Follow [release testing](testing.md) and [debugging](debugging.md) for device evidence.
