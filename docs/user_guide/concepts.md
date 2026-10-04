# 🧠 Core Concepts

## 🐍 Source and the Python subset

You write an `app.py` that looks like ordinary Python. Anpyra reads its syntax tree and translates supported statements. It neither starts a Python interpreter inside the APK nor executes app statements during the host build.

Valid Python and supported Anpyra syntax are separate checks. A list is valid Python, but list operations are unsupported in v0.1. See the [language reference](language.md).

## 📱 Activity and TextView

An Activity is the Android screen entry point. Your class extends `Activity` and defines `on_create(self, state)`. Anpyra emits Android's `onCreate(Bundle)` lifecycle method and its superclass call automatically.

`TextView(self)` creates a native text widget; `set_text(...)` supplies its text. `self.set_content_view(...)` makes the widget the screen content. Exactly one content-view call must appear outside branches in v0.1.

`state` names the incoming lifecycle state. Reading or manipulating it is not currently supported by the authoring language.

## 🧱 AST, types and IR

| Term | Meaning | Example |
| --- | --- | --- |
| AST | Tree describing source syntax | Assignment and `if` nodes |
| Semantic validation | Check names, types and supported operations | `set_text` requires a string |
| Symbol table | Known names and their types | `score: int`, `title: TextView` |
| IR | Internal operation records | Load a value, compare integers, create a widget |
| Lowering | Translate syntax into simpler operations | Helper call → call operation with arguments |

You need no IR knowledge to build. `anpyra check myapp --dump-ir` helps when learning or reporting bugs.

## ⚙️ Dalvik, registers and DEX

Dalvik instructions operate on registers: numbered slots holding method values. The current allocator gives each local and temporary a register. Temporary values also count toward the register budget.

`classes.dex` contains class definitions, methods, instructions and integrity data. Android ART executes that bytecode. Anpyra currently writes DEX version 035.

```text
Python helper call
    ↓
invoke-static: call the generated static method
move-result: copy its integer result into a register
```

Inspect an example with `anpyra check examples/score --dump-dalvik`.

## 📦 Manifest and APK

The manifest describes package ID, display label, version, SDK levels and launch Activity. Anpyra writes binary Android XML; the output manifest is not a text file to edit.

The APK packages that manifest and `classes.dex`. Anpyra adds a v2 signing block to the ZIP-based application package.

## 🔑 Identity and verification

`.anpyra/` retains a debug private key and certificate. Keep the pair together to retain the identity across rebuilds. Missing one file or a mismatched pair causes an error.

Verification checks the signature, protected content and DEX integrity. It detects corruption but does not run the app or prove Android will accept every emitted instruction. Device testing supplies that evidence.

Next: [first app](first_app.md) or [build outputs](build_outputs.md).
