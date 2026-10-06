# 🔎 Source File Reference

All framework paths below link to their canonical implementation. The current source checkout is Android-only. Public app APIs remain compatible; removed common/platform internal imports intentionally change in 0.1.1.

## 🚪 Public package and project files

| File | Functions/records and implementation | Fix here when |
| --- | --- | --- |
| [__init__.py](../../src/anpyra/__init__.py) | Public Activity/TextView, AppConfig/Project/errors, compile/build exports and version | Public imports/version inconsistent |
| [__main__.py](../../src/anpyra/__main__.py) | Run CLI main and exit with returned status | python -m anpyra differs from console command |
| [api.py](../../src/anpyra/api.py) | Activity.set_content_view; compatible TextView re-export; explicit host RuntimeErrors | Editor signatures or host execution error incorrect |
| [config.py](../../src/anpyra/config.py) | ConfigError; frozen AppConfig; Project; load_project | Metadata, SDKs, TOML or paths incorrect |
| [scaffold.py](../../src/anpyra/scaffold.py) | STARTER_SOURCE and init_project | New source/config/ignore template wrong |
| [cli.py](../../src/anpyra/cli.py) | main parser/dispatch and _dump IR/method listing | Flags, output, path or adb arguments wrong |
| [build.py](../../src/anpyra/build.py) | BuildResult; build_apk; build_project; historical _zip_payload alias | Stage ordering, output/report or failure preservation wrong |
| [py.typed](../../src/anpyra/py.typed) | Installed typing marker | Package omits typing data |
| [pyandroid exports](../../src/pyandroid/__init__.py) | Same Activity/TextView objects | Experiment imports break |

AppConfig validates nonempty strings/NUL, lowercase application ID, exact positive integer versions/SDKs, min SDK ≥24 and target ≥min. Project normalizes its root and resolve_path rejects absolute/escaping paths; source, output and signing state cannot overlap. Its properties expose source_path/output_path/state_path. load_project requires one [app] TOML table and rejects unknown keys.

init_project refuses nonempty destinations, validates metadata/paths and writes source/TOML/ignore files with Unicode-safe string quoting. It does not create signing state. build_apk compiles before loading a signer, packages/signs, verifies staged artifacts, then replaces output and writes metadata/fingerprint/listing records. Individual file replacements are atomic; the full artifact set is not a transaction.

CLI check writes nothing. build/check accept only Android and load project config. targets prints the supported Android target. verify reads an existing APK. install verifies then invokes adb argument lists (optional serial, install -r and launch); shell interpolation is not used. Errors return 1, parser errors 2, interruptions 130.

## 🧠 Python front end

File: [frontend.py](../../src/anpyra/compiler/frontend.py). Tests: compiler/unit, function regressions and historical fixtures.

| Symbol/group | Implemented responsibility |
| --- | --- |
| CompileError, CompileResult | Source diagnostics and source-path/AST/IR result |
| _line, _is_name, _is_docstring, _int_literal | AST recognition, line messages and signed literals |
| _require_imports, _find_activity_class, _find_on_create | Restricted module imports, one Activity and lifecycle signature |
| _annotation_name, _constant_type, COMPARE_OPS | Supported scalar types, distinct bool/int and comparison names |
| FunctionSignature, _collect_function_signatures | Typed helper signature, name/duplicate/arity validation |
| HelperCompiler | Lower one helper return expression using parameter/temp symbols |
| FunctionCompiler | Validate/lower lifecycle locals, arithmetic, helpers, widgets and branches |
| _count_content_view | Recursively count UI attachments |
| _compile_source | Parse/validate module, build helpers/lifecycle, require unconditional attachment and register budget |
| compile_source, compile_file | Validate metadata; attach source path to errors; read UTF-8 source |

HelperCompiler.synthetic/require_int/int_operand/compile_return_expr/compile implement helper temporary/type/expression rules. FunctionCompiler.declare/require/synthetic manage names/types; int_operand/compile_int_value_into/compile_call_into lower calculations/calls; compile_ann_assign validates before declaring to avoid self-initialization. compile_assignment recognizes TextView construction, compile_expr UI methods, compile_condition boolean/int comparison, compile_branch restricted nested statements and compile_statement dispatch.

Source is never executed or imported. Source acceptance alone does not implement a native method; IR and Android emitters must support it.

## 🧱 Intermediate representation

File: [ir.py](../../src/anpyra/compiler/ir.py).

CallSuperOnCreate models the automatic lifecycle call. LoadConst, IntBinary, CallFunction and ReturnValue model typed values/calculations/helper results. NewTextView, SetText and SetContentView model native UI work. IfBool/IfCompare carry immutable then/else tuples. IROp is their union. FunctionIR carries helper parameters/body/symbols; AppIR carries metadata/helpers/lifecycle/symbols. Their pretty output and Activity/class-descriptor properties support inspection/code generation.

New records need front-end lowering, traversals, emitter handling and tests; a dataclass alone does not generate executable behavior.

## 📺 Screen bindings and method code

New source components are documented in [Screen styling internals](screen_styling.md): [components/screen.py](../../src/anpyra/components/screen.py) owns Screen/value objects and color/opacity validation; [compiler/screen_style.py](../../src/anpyra/compiler/screen_style.py) parses declarative values; [android/backgrounds.py](../../src/anpyra/android/backgrounds.py) emits native layers/gradient/image operations; [android/assets.py](../../src/anpyra/android/assets.py) validates, normalizes and maps local image assets.

Typography is traced in [TextView internals](textview_styling.md): [components/textview.py](../../src/anpyra/components/textview.py) owns the authoring class and Font/Shadow/TextStyle values; [compiler/text_style.py](../../src/anpyra/compiler/text_style.py) merges ordered related properties; [android/textview.py](../../src/anpyra/android/textview.py) emits native typography/density/font calls; [android/fonts.py](../../src/anpyra/android/fonts.py) validates standalone fonts.

IR now includes NewScreen, SetScreenContent, ApplyScreenBackground, SetTextColor and SetTextStyle. Styled methods have reserved low array registers, rendering scratch and a high invocation bank. FieldKey/external field ID pools support native enum/SDK references. New Dalvik forms cover full constants, arrays, static fields, object results, move-from16 and invoke-range. Legacy method frames/DEX bytes remain unchanged.

| File | Symbols and responsibility |
| --- | --- |
| [screen.py](../../src/anpyra/android/screen.py) | Android Activity/Bundle/Context/TextView/CharSequence/View descriptor constants; screen_methods declares native/generated method references; emit_screen_operation emits super lifecycle, view construction, text and content attachment |
| [codegen.py](../../src/anpyra/android/codegen.py) | GeneratedMethods record; _walk_ops recursive branch traversal; generate_methods creates constructor, onCreate and static helper code/listings/registers |

Screen operations emit into the assembler using assigned registers and final type/method indexes. Android renders the resulting native calls; there is no host drawing or layout engine here.

generate_methods assigns lifecycle locals to low registers and self/state to the final two registers, enforcing 14 locals/temporaries. Helpers place temporaries below incoming parameter registers. It emits scalar constants/arithmetic/calls/results, delegates UI operations to screen.py, and resolves nested conditional branches through the assembler. The inverted comparison opcode skips the then branch when the source condition fails. Outgoing frame size covers UI calls and helper arity. Constructor code invokes the native Activity constructor.

## ⚙️ Dalvik and binary primitives

| File | Symbols and responsibility |
| --- | --- |
| [dalvik.py](../../src/anpyra/android/dalvik.py) | OP_* supported opcodes; encode_21c and encode_invoke_35c; make_code_item; AsmInstruction/Label; Assembler.new_label/label/emit/assemble |
| [encoding.py](../../src/anpyra/android/encoding.py) | align; uleb128; utf16_code_units; mutf8_encode; dex_string_sort_key |
| [dex_types.py](../../src/anpyra/android/dex_types.py) | ProtoKey(return_type, parameters), MethodKey(owner/name/signature), MethodListing(name/registers/code_units/assembly), DexBuild(bytes/main listing/methods) |

Assembler first measures instruction/label positions, then encodes words and listings. Branch displacements are signed 16-bit **code units**, not byte offsets. Invocation format 35c permits at most five four-bit register references. make_code_item serializes frame sizes and words. Modified UTF-8 encodes NUL specially and supplementary characters through UTF-16 surrogate units; string sorting uses those same units.

## 📦 DEX file writing

File: [dex.py](../../src/anpyra/android/dex.py).

DEX_MAGIC/header/access/map constants describe DEX 035. _shorty compresses signatures. build_dex collects screen/helper references and literal strings, derives referenced types/prototypes, sorts IDs, then calls generate_methods with final indexes. It places aligned type lists, string data, method code, class data and the map list; direct methods are constructor/static helpers, while onCreate is virtual. Class data method IDs use deltas/ULEB128. Header fields describe final sizes/offsets. SHA-1 is written before Adler-32.

Fix container offsets/indexes/class metadata here; fix instruction words in dalvik.py, register/IR lowering in codegen.py, UI references in screen.py and strings in encoding.py. Former compiler.dex imports should be updated to android.dex.

## 📄 Manifest, packaging and signing

| File | Symbols and responsibility |
| --- | --- |
| [manifest.py](../../src/anpyra/android/manifest.py) | _chunk_header/_enc_len8; StringPool; Attr; BinaryXmlBuilder; build_manifest |
| [manifest_inspect.py](../../src/anpyra/android/manifest_inspect.py) | AxmlError; _read_len8/_parse_string_pool; inspect_manifest |
| [packaging.py](../../src/anpyra/android/packaging.py) | build_unsigned_apk: manifest/DEX plus optional validated PNG assets, fixed timestamp, compression/permissions |
| [signing.py](../../src/anpyra/android/signing.py) | V2SigningError; ZipSections/V2SignerMaterial/V2SignResult; ZIP slicing, retained identity, digest and APK signing |
| [verify.py](../../src/anpyra/android/verify.py) | ApkV2VerifyError/ApkReport; bounded signer parsing and inspect_apk |

BinaryXmlBuilder creates namespace/string/resource-map chunks and typed attributes, then manifest/uses-sdk/application/exported Activity/MAIN-LAUNCHER elements. StringPool uses UTF-16 lengths in UTF-8 pool data. The inspector checks chunk/attribute bounds and returns identity/version/SDK/UI metadata for the generated profile.

Signing helpers _u32/_u64/lp32/seq32 build binary fields. find_eocd/split_zip_sections/patch_eocd_central_directory_offset manage ZIP sections. compute_chunked_content_digest protects ZIP regions with the v2 EOCD adjustment. generate_signer_material creates RSA-2048/self-signed debug material; load_or_create_signer_material retains the pair and rejects partial/non-RSA/mismatched identities. build_v2_value/build_apk_signing_block/sign_apk_v2 build and insert the signed block. No release-key import/encryption/rotation workflow exists yet.

Verification's _take_lp32/_iter_lp32_sequence/_locate_signing_block/_parse_v2_signer enforce the generated single-signer profile, signature/public-key agreement and protected content digest. inspect_apk checks manifest/DEX, optional PNG asset digests/structure, and DEX magic/SHA-1/Adler-32. Failed checks raise; successful report flags do not represent runtime validation or trust-chain/device certification.

## 🧪 Tests and repository files

| File/group | Responsibility |
| --- | --- |
| [test_compiler.py](../../tests/unit/test_compiler.py), [test_config.py](../../tests/unit/test_config.py) | Source acceptance/rejection, initialization/types/register limits and configuration/scaffold/path behavior |
| [test_dex.py](../../tests/unit/test_dex.py) | Independent byte reading for tables/frames/results/branches/strings/checksums |
| [test_architecture.py](../../tests/unit/test_architecture.py) | No placeholder layers, canonical component ownership, Android-only early rejection and public/experiment object identity |
| [test_build.py](../../tests/integration/test_build.py), [test_cli.py](../../tests/integration/test_cli.py) | Artifact/signing/rebuild/failure workflows, commands and mocked adb |
| [test_functions.py](../../tests/regression/test_functions.py) | Experiment 008 helper IR/instructions/validation/APK |
| [test_android_output.py](../../tests/regression/test_android_output.py) | Exact experiment 005–008 DEX hashes captured before cleanup |
| tests/fixtures/exp005.py–exp008.py | Original immutable source inputs |
| [test_release.py](../../tests/unit/test_release.py) | Version/tag/stale archive/metadata/private path/link rejection |
| [check_docs.py](../../scripts/check_docs.py) | Owned Markdown links/emoji titles/Python syntax/Activity compilation |
| [check_release.py](../../scripts/check_release.py) | Static version/tag and built archive checks; no upload/credential access |
| [tests.yml](../../.github/workflows/tests.yml), [publish.yml](../../.github/workflows/publish.yml) | Host CI and manual tagged Trusted Publishing |
| [pyproject.toml](../../pyproject.toml), [MANIFEST.in](../../MANIFEST.in) | Packaging/dependencies/CLI/typing/lint metadata and source inclusions |
| [PyPI README](../pypi_readme.md), [progress](../progress.md), [roadmap](../roadmap.md) | Package presentation, success evidence and Android work planning |
| examples/hello and examples/score | Complete source/TOML walkthroughs; no package runtime code |
| Package/test __init__.py files | Import/discovery markers |

Use [components](android_components.md), [debugging](debugging.md), [testing](testing.md) and [publishing](publishing.md) when making changes.
