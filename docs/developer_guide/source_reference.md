# 🔎 Source File Reference

Use this map to locate the code responsible for a feature or failure. Paths link to actual files; named functions are current implementation entry points, not stable external APIs.

## 🚪 Package entry and authoring API

| File | Implemented responsibility | Where to look when fixing |
| --- | --- | --- |
| [anpyra/__init__.py](../../src/anpyra/__init__.py) | Public exports and `__version__ = "0.1.0"` | Import failures, public API/version consistency |
| [anpyra/__main__.py](../../src/anpyra/__main__.py) | Runs CLI `main()` and uses its result as process status | `python -m anpyra` behavior |
| [api.py](../../src/anpyra/api.py) | Editor-facing `Activity`, `TextView`; methods raise a host RuntimeError | Authoring type signatures and host-execution message |
| [pyandroid/__init__.py](../../src/pyandroid/__init__.py) | Re-exports the same Activity/TextView objects | Legacy import compatibility |
| [py.typed](../../src/anpyra/py.typed) | Marker indicating typing information ships with package | Missing marker/package-data configuration |
| [compiler/__init__.py](../../src/anpyra/compiler/__init__.py) | Compiler package marker/docstring | Package imports only; no engine logic |
| [android/__init__.py](../../src/anpyra/android/__init__.py) | Android backend package marker/docstring | Package imports only; no Android logic |

The authoring methods are `Activity.set_content_view`, `TextView.__init__` and `TextView.set_text`. Their Android behavior is emitted by the compiler, not implemented by those host bodies. Test: `tests/unit/test_compiler.py` checks legacy identity and the host error.

## ⚙️ config.py

File: [config.py](../../src/anpyra/config.py). Tests: [test_config.py](../../tests/unit/test_config.py).

| Symbol | What it implements |
| --- | --- |
| `ConfigError` | User-facing invalid configuration exception |
| `AppConfig` | Frozen package/label/version/SDK/entry/output metadata with defaults |
| `AppConfig.__post_init__` | Nonempty strings/no NUL, package pattern, exact integer types/range, min SDK and target relationship |
| `Project` | Root + configuration object, with normalized absolute root |
| `Project.__post_init__` | Reject source/output/signing overlap and output equal to project root |
| `Project.resolve_path` | Reject absolute/drive/root paths and resolved paths outside project |
| `source_path`, `output_path`, `state_path` | Entry, configured output, `.anpyra` directory |
| `load_project` | Read TOML, require one `[app]` table, reject unknown keys, create Project |

Defaults are documented in the user guide. This module does not compile source or accept arbitrary new TOML keys. Add a configuration feature here, propagate it through scaffold/build, and update tests and reference tables.

## 🏗️ scaffold.py

File: [scaffold.py](../../src/anpyra/scaffold.py). Tests: configuration scaffold tests and CLI integration tests.

`STARTER_SOURCE` is the generated hello application. `init_project` validates metadata through `AppConfig`/`Project`, refuses nonempty destinations, and writes source, TOML and ignore rules. Its JSON-based string quoting uses `ensure_ascii=False` to keep supplementary Unicode characters valid in TOML.

If generated projects fail but hand-written projects work, inspect this template and quoting first. Its writes are individual writes, not a full filesystem transaction. Adding resources or multiple starter files needs a deliberate scaffold design.

## ⌨️ cli.py

File: [cli.py](../../src/anpyra/cli.py). Tests: [test_cli.py](../../tests/integration/test_cli.py).

`main(argv)` creates the parser and dispatches all six commands. `_dump` prints IR and per-method assembly when requested. The `check` branch runs compile + DEX in memory; `build` uses project orchestration; `verify` prints an `ApkReport` or JSON; `doctor` reports host versions and adb availability.

`install` verifies before invoking subprocesses. It constructs argument lists for adb, optional `-s`, `install -r`, and `am start -W -n`; it does not execute a shell command assembled from user text. `main` catches command exceptions, writes stderr and returns `1`; keyboard interruption returns `130`. Argument errors are handled by argparse before dispatch.

Inspect this file for a wrong flag, missing command, incorrect printed path or adb argument. Compiler semantics should stay in the compiler rather than become CLI-specific rules.

## 📦 build.py

File: [build.py](../../src/anpyra/build.py). Tests: [test_build.py](../../tests/integration/test_build.py), CLI and helper regression builds.

| Symbol | What it implements |
| --- | --- |
| `BuildResult` | Artifact paths, CompileResult, DexBuild, ApkReport, signed APK size |
| `_zip_payload` | In-memory ZIP containing manifest/DEX, fixed timestamp, compression and file permissions |
| `build_apk` | Metadata validation → compile → manifest/DEX → ZIP → retained signer → sign → staged verify → output/report |
| `build_project` | Accept Project/path, resolve source/output/state and forward config to `build_apk` |

`build_apk` rejects output containing source and overlap with signing state. It writes a report with metadata, APK/certificate fingerprints, verification and listings. Artifact publication occurs after verification; each `.replace()` is atomic but the multi-file set is not.

Look here for wrong output names, report fields, ordering of stages, signer directory, reproducibility or failure-preservation problems. It currently supports exactly one DEX and manifest; resources/assets or new artifacts require packaging and verifier changes too.

## 🧠 compiler/frontend.py

File: [frontend.py](../../src/anpyra/compiler/frontend.py). Tests: [test_compiler.py](../../tests/unit/test_compiler.py), historical fixtures and [test_functions.py](../../tests/regression/test_functions.py).

| Symbol/group | What it implements |
| --- | --- |
| `CompileError`, `CompileResult` | Readable compiler errors; source/AST/IR return record |
| `_line`, `_is_name`, `_is_docstring`, `_int_literal` | Source diagnostics and AST recognition, including signed integer literals |
| `_require_imports` | Supported authoring imports without aliases; reject unsupported module statements/imports |
| `_find_activity_class`, `_find_on_create` | One Activity class/lifecycle method; reject extra class body/decorators/invalid signatures |
| `_annotation_name`, `_constant_type` | Supported annotations and distinct literal types (`bool` before `int`) |
| `COMPARE_OPS` | AST comparison classes mapped to source comparison names |
| `FunctionSignature`, `_collect_function_signatures` | Required typed parameters, return type, name/duplicate/arity validation |
| `HelperCompiler` | Validate and lower a helper's single return expression |
| `FunctionCompiler` | Validate/lower lifecycle locals, widgets, calls and branches |
| `_count_content_view` | Recursive attachment count |
| `_compile_source` | Parse/validate module; build helpers and lifecycle IR; enforce attachment and register budget |
| `compile_source` | Validate package/label and attach source path to CompileError |
| `compile_file` | Read UTF-8 Path and delegate to source compilation |

`HelperCompiler.synthetic` creates temporary symbol names; `require_int` and `int_operand` enforce operand types; `compile_return_expr` creates literal/binary/return operations; `compile` enforces one return body.

`FunctionCompiler.declare` rejects duplicates and reserved-name shadowing. `require` checks names/types. `synthetic` creates temporary constants. `int_operand`, `compile_int_value_into` and `compile_call_into` implement int values/helper calls. `compile_ann_assign` validates the initializer before declaring the target, preventing `n: int = n` from using an uninitialized register.

`compile_assignment` recognizes only unannotated TextView construction. `compile_expr` recognizes text/content-view calls. `compile_condition` builds boolean/comparison branches; `compile_branch` allows method calls/nested conditions/pass; `compile_statement` dispatches lifecycle syntax. Branch declarations and general expressions are not currently implemented.

Read this file first for accepted/rejected syntax, undefined names, incorrect inferred types, wrong diagnostics or missing IR operations. Its narrow helper/lifecycle models are intentional v0.1 limits.

## 🧱 compiler/ir.py

File: [ir.py](../../src/anpyra/compiler/ir.py). Tests: compiler/helper tests inspect emitted records.

| Record | Meaning |
| --- | --- |
| `CallSuperOnCreate` | Invoke Android superclass lifecycle method |
| `LoadConst` | Initialize a typed string/int/bool symbol |
| `IntBinary` | Destination and two int operands with `+`/`-` |
| `CallFunction` | Helper name, named arguments and result destination |
| `ReturnValue` | Helper's returned int symbol |
| `NewTextView` | Allocate/initialize a widget |
| `SetText` | Receiver widget and string symbol |
| `SetContentView` | Attach named view to Activity |
| `IfBool`, `IfCompare` | Condition plus immutable then/else operation tuples |
| `FunctionIR` | Helper parameters/return type/body/symbols; `pretty()` listing |
| `AppIR` | App metadata/helpers/lifecycle/symbols; descriptor/Activity properties and recursive pretty output |

`IROp` is the union of supported operation records. New IR must also be handled by traversals and backend emitters. A dataclass alone does not implement code generation.

## ⚙️ compiler/dex.py

File: [dex.py](../../src/anpyra/compiler/dex.py). Tests: [test_dex.py](../../tests/unit/test_dex.py), helper regression and builds.

| Symbol/group | What it implements |
| --- | --- |
| `DEX_MAGIC`, header/map/access/opcode constants | DEX 035 metadata and supported instruction identifiers |
| `align`, `uleb128` | File alignment and unsigned variable-length integer encoding |
| `utf16_code_units`, `mutf8_encode`, `dex_string_sort_key` | DEX string representation and UTF-16 ordering, including NUL/supplementary characters |
| `encode_21c`, `encode_invoke_35c`, `make_code_item` | Selected binary instruction/code-item formats; invoke count/register limits |
| `ProtoKey`, `MethodKey` | Hashable method signature/reference identities |
| `AsmInstruction`, `Label` | Assembler items and symbolic destinations |
| `MethodListing`, `DexBuild` | Emitted bytes plus registers/code sizes/assembly for inspection |
| `Assembler.new_label/label/emit/assemble` | Collect instructions, resolve labels, encode words and build listing |
| `_shorty` | Compact return/parameter signature string |
| `_walk_ops` | Recursive IR traversal through branches |
| `build_dex` | Pool collection, index sorting, register maps, methods, DEX sections and integrity fields |

Inside `build_dex`, `emit_main` handles lifecycle operations, `inverse` selects the inverted comparison branch, and `add_code` places aligned code items. Helper parameters are assigned above helper temporaries. Constructor/static helpers go in direct methods; `onCreate` is a virtual method. Method references and class data use sorted indexes and delta encodings.

The writer then emits header, string/type/proto/method/class sections, type lists, string data, code items, class data and map list; SHA-1 is filled before Adler-32. The current lifecycle frame is limited to 16 registers including two incoming values. Branch displacements use signed 16-bit code-unit offsets.

Fix this file for malformed bytes, wrong registers, branch destinations, table indexes, incoming parameter layout, opcode encoding or string ordering. The [compiler guide](compiler.md) explains the stages and invariants.

## 📄 android/manifest.py

File: [manifest.py](../../src/anpyra/android/manifest.py). Tests: build metadata/Unicode roundtrip and every verified APK build.

`_chunk_header` and `_enc_len8` encode XML/string-pool structures. `StringPool` collects resource-backed attribute names and ordinary strings, writes UTF-8 pools with UTF-16 lengths, and emits the resource map. `Attr` represents namespace/name/type/value.

`BinaryXmlBuilder` stores metadata and constructs the manifest. `idx` resolves pool indexes; `_node_header`, namespace methods and element methods encode chunks; `_typed_value` encodes strings, ints and booleans. `build` emits manifest → uses-sdk → application → exported Activity → MAIN/LAUNCHER intent filter. `build_manifest` is the wrapper used by builds.

Inspect for bad manifest attributes, labels/Unicode, SDK/version values, namespace/resource IDs or chunk lengths. Permissions, icons, resource references and multiple Activities are not implemented.

## 🔍 android/manifest_inspect.py

File: [manifest_inspect.py](../../src/anpyra/android/manifest_inspect.py).

`AxmlError` identifies parsing failures. `_read_len8` decodes pool lengths; `_parse_string_pool` reads the expected UTF-8/no-style pool; `inspect_manifest` reads chunk bounds, attributes and balanced elements, then returns package, versions, SDKs, label, Activity and exported metadata.

It is a reader for the generated profile rather than a general Android XML parser. If writer and reader agree on the same incorrect format, self-verification can miss a bug; independent Android inspection is a release objective. Add focused malformed-input/roundtrip tests when changing it.

## 🔑 android/signing.py

File: [signing.py](../../src/anpyra/android/signing.py). Tests: build/identity/reproducibility/tamper workflows.

| Symbol/group | What it implements |
| --- | --- |
| `V2SigningError` | Signing/ZIP/identity validation error |
| `ZipSections`, `V2SignerMaterial`, `V2SignResult` | ZIP slices, key/cert data, signed result/offsets |
| `_u32`, `_u64`, `lp32`, `seq32` | Little-endian and length-prefixed binary fields |
| `find_eocd`, `split_zip_sections` | Locate ZIP tail, reject unsupported multi-disk/inconsistent offsets |
| `patch_eocd_central_directory_offset` | Set the offset for digesting or final signed ZIP; no ZIP64 support |
| `compute_chunked_content_digest` | APK v2 SHA-256 chunk digest over protected sections |
| `generate_signer_material` | RSA-2048 key and self-signed Anpyra Debug certificate |
| `load_or_create_signer_material` | Persist/reuse pair; reject partial, non-RSA or mismatched material |
| `build_v2_value` | Digest/certificate/attribute/signature/public-key length-prefixed signer data |
| `build_apk_signing_block` | v2 ID-value pair, leading/trailing sizes and APK block magic |
| `sign_apk_v2` | Digest unsigned ZIP, create block, insert before central directory, patch final EOCD |

The algorithm is RSA PKCS#1 v1.5 with SHA-256. The low-level signer can generate ephemeral material if none is passed; build orchestration always supplies the retained project signer. There is no release key import/encryption/rotation workflow in v0.1.

## ✅ android/verify.py

File: [verify.py](../../src/anpyra/android/verify.py). Tests: signature/content corruption and bad DEX checksum in [test_build.py](../../tests/integration/test_build.py).

`ApkV2VerifyError` represents profile/integrity failures; `ApkReport` carries parsed metadata and successful checks. `_u32`, `_u64`, `_take_lp32`, `_iter_lp32_sequence` read bounded binary fields. `_locate_signing_block` validates ZIP/block relationships and finds the v2 pair. `_parse_v2_signer` enforces one signer/algorithm/certificate, checks public-key agreement and verifies its signature.

`inspect_apk(Path)` recomputes the protected content digest with the required EOCD adjustment, reads exactly two ZIP entries, decodes the manifest, and checks DEX magic/SHA-1/Adler-32. Successful flags are true because a failed check raises. It does not perform Android runtime verification, trust-chain validation, arbitrary signer/package auditing or device installation.

## 🧪 Tests, examples and repository tooling

| File/group | Implemented check or purpose |
| --- | --- |
| [test_compiler.py](../../tests/unit/test_compiler.py) | Historical app acceptance, rejection diagnostics, initialization, reserved names, literal range, register budget and host stubs |
| [test_config.py](../../tests/unit/test_config.py) | Invalid metadata/types/paths, scaffold protection, TOML roundtrip and Unicode |
| [test_dex.py](../../tests/unit/test_dex.py) | Independent byte-level header/map/helper/invoke/branch/MUTF-8 checks |
| [test_build.py](../../tests/integration/test_build.py) | Metadata, rebuild bytes, failure preservation, identity safeguards, tamper/checksum rejection |
| [test_cli.py](../../tests/integration/test_cli.py) | Init/check/build/verify workflow, no-write check, errors and mocked adb argument lists |
| [test_functions.py](../../tests/regression/test_functions.py) | Adapted experiment 008 helper IR, instructions, invalid signatures/calls and APK payload |
| [fixtures/exp005.py](../../tests/fixtures/exp005.py) | Earliest source-app shape |
| [fixtures/exp006.py](../../tests/fixtures/exp006.py) | Typed locals and boolean branching |
| [fixtures/exp007.py](../../tests/fixtures/exp007.py) | Arithmetic/comparisons and nested branches |
| [fixtures/exp008.py](../../tests/fixtures/exp008.py) | Helper method and call |
| Test package `__init__.py` files | Discovery/import markers; no runtime framework code |
| [hello/app.py](../../examples/hello/app.py), [hello/anpyra.toml](../../examples/hello/anpyra.toml) | Native greeting and complete app metadata |
| [score/app.py](../../examples/score/app.py), [score/anpyra.toml](../../examples/score/anpyra.toml) | Typed helper, comparison and native result text |
| [pyproject.toml](../../pyproject.toml) | Package/version/dependencies/console entry/source discovery/typing/Ruff |
| [MANIFEST.in](../../MANIFEST.in) | Source distribution inclusion rules |
| [tests.yml](../../.github/workflows/tests.yml) | OS/Python matrix, lint/docs/tests/examples/wheel checks |
| [check_docs.py](../../scripts/check_docs.py) | Owned Markdown links/headings and syntax/buildability of documented Python app examples |
| Root README/contribution/changelog and docs indexes | Navigation, maintenance workflow and status; no executable framework implementation |

Read [testing](testing.md), [debugging](debugging.md), and [release](release.md) before changing binary-format behavior.
