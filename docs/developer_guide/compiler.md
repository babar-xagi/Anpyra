# 🧠 Compiler and DEX Internals

Relevant files: [frontend.py](../../src/anpyra/compiler/frontend.py), [ir.py](../../src/anpyra/compiler/ir.py), [dex.py](../../src/anpyra/compiler/dex.py). See the [source reference](source_reference.md) for every symbol.

## 1️⃣ Parse and validate the module

`compile_source` validates package/label and calls `_compile_source`. Python's `ast.parse` creates an AST; syntax errors become `CompileError`. Supported imports, module statements, Activity shape, helper signatures and lifecycle signature are then checked.

No app import, `eval` or `exec` is used. AST validation is a language boundary: code may be syntactically Python yet outside Anpyra's implemented semantics. When adding a feature, decide its semantics before broadening accepted nodes.

The outer error wrapper adds `source_path`; `_line(node)` adds a source line where available. Class/module-wide errors do not always have a line. Diagnostics are readable exceptions, not yet structured error codes/spans.

## 2️⃣ Build signatures, symbols and helper IR

The front end collects helper signatures before lowering bodies, so lifecycle calls can refer to helpers defined elsewhere in the module. Helpers are restricted to integer parameters/return and a single return expression. They do not call each other.

`HelperCompiler` starts with parameter symbols. Integer literals or binary destinations add synthetic symbols. Its return becomes `ReturnValue`; a binary expression also emits `IntBinary`.

`FunctionCompiler` handles `on_create`. A symbol table maps names to source types. Declarations reject duplicates and reserved-name shadowing. Initializer validation occurs before declaring its target; otherwise `n: int = n` could incorrectly read an uninitialized register.

Synthetic values use names such as `$int0` and `$str1`. They are compiler-generated and count toward the lifecycle register budget. String/boolean annotated values require literal constants; integer values support the documented names/literals/simple arithmetic/helper calls.

## 3️⃣ Lower source to operations

| Source | IR |
| --- | --- |
| `score: int = 80` | `LoadConst(score, int, 80)` |
| `total: int = score + bonus` | `IntBinary(total, score, +, bonus)` |
| `result: int = calculate_score(score, bonus)` | `CallFunction(result, calculate_score, (score, bonus))` |
| `title = TextView(self)` | `NewTextView(title)` |
| `title.set_text("Passed")` | Synthetic string `LoadConst` then `SetText` |
| `if active:` | `IfBool` with operation tuples |
| `if score >= 70:` | Literal temporary plus `IfCompare` |
| `self.set_content_view(title)` | `SetContentView(title)` |

Lifecycle IR starts with `CallSuperOnCreate`. Branches contain calls/nested branches/pass rather than declarations. The recursive content-view count must be one and an attachment must also exist in the top-level operation list, ensuring it is outside branches.

## 4️⃣ Collect and index DEX references

`build_dex` collects class/Android type descriptors, string values, method names, prototypes and references. Examples of descriptors include `Landroid/widget/TextView;`, `I` for int and `V` for void. A prototype identifies return/parameter types; a shorty compresses reference types to `L`.

Strings sort by UTF-16 code units. Types, prototypes and method IDs then sort by their required indexes. DEX indexes are not arbitrary insertion order. Changing a string or signature can affect indexes elsewhere, so encoded references must use the final maps.

DEX string data uses modified UTF-8, with a UTF-16 length. NUL is encoded differently from ordinary UTF-8; supplementary characters are encoded through surrogate code units. The binary tests cover these cases. See the primary [DEX format specification](https://source.android.com/docs/core/runtime/dex-format).

## 5️⃣ Assign register frames

Lifecycle symbols occupy low registers; the final two incoming registers hold `self` and `state`. The current implementation permits at most 14 symbols plus those two values. Allocation does not analyze lifetimes or reuse dead values.

Helper temporaries occupy low registers; parameters occupy the high registers. For `calculate_score(score, bonus)` with one result temporary, the helper frame has three registers: result `v0`, incoming score `v1`, incoming bonus `v2`.

`registers_size` is the frame size, `ins_size` the incoming words, and `outs_size` the maximum outgoing invocation words. The helper example has `(3, 2, 0)` because it makes no calls. The lifecycle frame reserves enough outgoing words for UI calls and helper arity.

## 6️⃣ Assemble instructions and branches

The assembler collects `AsmInstruction` and `Label` records. Its first pass calculates label positions; its second pass encodes instructions and computes signed displacements relative to the current instruction.

| Operation | Main emitted instruction(s) |
| --- | --- |
| Small int/bool constant | `const/4` |
| Other supported int literal | `const/16` |
| String constant | `const-string` |
| Integer arithmetic | `add-int`, `sub-int` |
| Widget construction | `new-instance`, `invoke-direct` |
| Text/content-view call | `invoke-virtual` |
| Lifecycle super call | `invoke-super` |
| Helper call | `invoke-static`, immediately `move-result` |
| Helper return | `return` |
| Lifecycle/constructor return | `return-void` |
| Conditions | Inverted `if-*`, `if-eqz`, optional `goto/16` |

Branch offsets and instruction sizes are measured in **16-bit code units**. File offsets are bytes. Mixing these units causes classic branch bugs. Targets must land at instruction boundaries. Current signed-16-bit offsets can overflow on larger methods.

Invocation uses the 35c form: up to five arguments and four-bit register references. Some comparison encodings also use four-bit registers. Increasing the allocator limit alone would not make wider registers valid; wider instruction support or register shuffling is required.

## 7️⃣ Write the DEX file

The writer lays out header and fixed ID sections, then data sections: type lists, string data, aligned code items, encoded class data and map list. Class data lists constructors/static helpers as direct methods and `onCreate` as a virtual method. Sorted method indexes are delta-encoded with ULEB128.

It fills the SHA-1 signature over bytes after the signature field, then Adler-32 over bytes after magic/checksum. Header file/data sizes and map offsets must describe the final bytes. Checksum success alone does not establish semantic validity.

## 🧪 Debugging and test boundaries

`test_dex.py` independently reads selected DEX tables/code items to validate frame layout, actual helper words, immediate result instruction, branch boundaries, map offsets and checksums. Its helper decoder is intentionally limited to the test profile, not a general DEX reader; add decoding/test coverage when adding instructions.

Use [debugging](debugging.md) to compare AST → IR → listing → bytes → Android behavior. Independent Android verification and broader malformed-input coverage remain future validation work.
