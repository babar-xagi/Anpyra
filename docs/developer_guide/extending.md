# 🧩 Extending Anpyra

The native pipeline remains the design direction. New features must be implemented across every stage they affect rather than accepted syntactically before code generation exists.

## 🧭 Feature workflow

1. Describe a concrete app/source behavior and choose its roadmap phase.
2. Specify types, evaluation order, errors, side effects and runtime behavior.
3. Design a minimal accepted source form and rejected alternatives.
4. Add/extend IR only where the existing operations cannot express that behavior.
5. Implement validation/lowering, register/instruction/reference generation, and package changes as needed.
6. Add tests for valid output and failures at the relevant layers.
7. Validate Android behavior when the feature changes runtime execution.
8. Document the accepted form/limits and update status only after its acceptance criteria pass.

## 🐍 Adding a language feature

Suppose a proposal adds multiplication. Decide integer overflow behavior and operand forms first. The likely touch points are `FunctionCompiler.compile_int_value_into`, `HelperCompiler.compile_return_expr`, `IntBinary`, instruction handling in `android/dalvik.py` and helper/lifecycle emitters in `android/codegen.py`.

Both helper and lifecycle paths must implement it consistently, or explicitly document different support. Add a test of actual encoded instructions and a source rejection case, then add a working user example. Merely accepting `ast.Mult` would otherwise promise behavior without valid bytecode.

For reassignment, the design is more involved: initialization/state changes, branch data flow, type stability and register reuse must be specified. Current `declare` is intentionally single-assignment by name; relaxing it alone is not a complete implementation.

## 📱 Adding a widget or method

| Stage | Needed change |
| --- | --- |
| Authoring API | Typed host stub in `api.py` and deliberate public export |
| Imports | Front-end whitelist and compatibility decision |
| Validation | Constructor/receiver/argument types and accepted source form |
| IR | Explicit operation or consistent generalized call representation |
| Backend references | Native descriptor/method declarations in screen.py; pool/index collection in dex.py |
| Instructions | Screen calls in screen.py, scalar/control flow and registers in codegen.py, binary formats in dalvik.py |
| Tests | Source lowering, actual bytes and device behavior |
| Docs | Current feature reference, example, source map and roadmap status |

A Button callback also needs listener/interface class generation, event dispatch and mutable application state. It cannot be implemented by adding `Button` to `api.py` alone. Layouts require child view operations and correct Android signatures.

## 📦 Adding assets/resources/modules

The current APK verifier expects exactly two entries. New assets need packaging rules and an updated accepted profile. Android resources may require a resource table and manifest references; they are separate from ZIP asset files.

Multiple Python modules need module discovery, supported import/name-resolution semantics and linking. Continue static compilation; do not execute host imports as a shortcut. More Activities/classes also affect class definitions, method ownership, manifest generation and tests.

## 🔑 Adding release signing

Design explicit key selection/loading, protected storage, error behavior and upgrade identity checks. Separate debug and release workflows. Do not infer a release identity from a random debug directory. Key rotation/v3/AAB/store work requires additional binary and distribution contracts.

## 🏗️ Refactoring large internals

The Android-only cleanup already separates DEX writing, method generation, Dalvik assembly, native screen bindings, encoding and packaging. Follow the [component ownership guide](android_components.md); edit the canonical implementation rather than adding a parallel emitter.

Keep refactoring and new semantics reviewable. File extraction must preserve table order, registers and APK bytes unless a behavior change is deliberate and tested. Public application imports remain compatible; the former common/platform internal paths were removed intentionally. Historical DEX hashes and same-identity APK comparisons protect this cleanup.

## ✅ Definition of done

A feature is ready when its semantics are specified, source acceptance matches implementation, necessary bytecode/package stages work, invalid forms fail usefully, relevant tests pass, runtime evidence exists where needed, and examples/docs state actual limits. See [roadmap](../roadmap.md) and [release checklist](release.md).
