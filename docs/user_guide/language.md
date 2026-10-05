# 🐍 Supported Language and UI

This reference describes the implementation in `common/compiler/frontend.py` and `platforms/mobile/android/dex.py`. A feature appearing in the roadmap does not make it available in source today.

## 🧩 Application shape

Import `Activity` and `TextView` without aliases from `anpyra`. Legacy `pyandroid` imports are accepted. Define exactly one class with `Activity` as its only base and exactly one `on_create(self, state)` method.

Module-level helper functions and docstrings are supported. Arbitrary imports, module assignments, decorators, extra classes, class fields, and extra Activity methods are rejected. Anpyra inserts the superclass `onCreate` call; do not write your own `super()` call.

## ✍️ Types and declarations

| Type/form | Supported initializer | Example |
| --- | --- | --- |
| `str` | String literal | `name: str = "Babar"` |
| `bool` | Boolean literal | `active: bool = True` |
| `int` | Integer literal, existing int name, simple `+`/`-`, helper call | `total: int = score + bonus` |
| TextView | Unannotated `TextView(self)` assignment | `title = TextView(self)` |

Declare each name once and initialize it. Referenced names must already be declared. `self`, `state`, `Activity`, `TextView`, and helper-function names cannot be shadowed by locals. A boolean is not accepted as an integer.

```python
from anpyra import Activity, TextView


class MainActivity(Activity):
    def on_create(self, state):
        name: str = "Babar"
        active: bool = True
        age: int = 23
        title = TextView(self)
        if active:
            title.set_text(name)
        else:
            title.set_text("Inactive")
        self.set_content_view(title)
```

The unused `age` is legal but still consumes a register.

## ➕ Integer expressions

Literals must fit **−32768 through 32767**, including signed unary literals such as `-8`. Arithmetic results use signed 32-bit Dalvik integer behavior; overflow is not Python's arbitrary-precision behavior.

```python
from anpyra import Activity, TextView


class MainActivity(Activity):
    def on_create(self, state):
        score: int = 80
        bonus: int = 5
        total: int = score + bonus
        adjusted: int = total - 10
        title = TextView(self)
        if adjusted >= 70:
            title.set_text("Passed")
        else:
            title.set_text("Try again")
        self.set_content_view(title)
```

Each operand of `+`/`-` must be an integer name or supported integer literal. `(score + bonus) - 10` has a nested binary operand and is unsupported; split it into separate annotated declarations as above. Multiplication, division, casts and string concatenation are not implemented.

## 🔀 Conditions and branches

Supported conditions are a declared boolean name or one integer comparison: `==`, `!=`, `<`, `<=`, `>`, `>=`. Comparison operands are int names/literals. Chained comparisons, `and`, `or`, `not`, string comparisons, and `if True` are unsupported.

Branches can contain supported method calls, nested `if`/`elif`/`else`, and `pass`. Declarations, reassignment and helper calls inside branches are not yet supported. The [original experiment 007 fixture](../../tests/fixtures/exp007.py) demonstrates nested branches.

## 🧮 Integer helper functions

```python
from anpyra import Activity, TextView


def calculate_score(score: int, bonus: int) -> int:
    return score + bonus


class MainActivity(Activity):
    def on_create(self, state):
        result: int = calculate_score(80, 5)
        title = TextView(self)
        if result >= 70:
            title.set_text("Passed from a compiled helper")
        else:
            title.set_text("Failed")
        self.set_content_view(title)
```

Helpers have 0–5 required positional parameters, each annotated `int`, and an `-> int` return annotation. The body contains one return expression, optionally with docstrings. Return an int parameter/name, signed literal, or simple `+`/`-` expression.

Calls must initialize an annotated `int` in `on_create`. Arguments are int names/literals. Default/keyword/variadic parameters, keyword calls, recursion, helper-to-helper calls, statements inside helpers, and object/string return values are unsupported. Duplicate parameter/function names are rejected.

## 📱 Native authoring API

| Source operation | Android target | Rules |
| --- | --- | --- |
| `class MainActivity(Activity)` | Subclass of `android.app.Activity` | One class |
| `on_create(self, state)` | `onCreate(Bundle)` | Compiler inserts super call |
| `title = TextView(self)` | TextView constructor taking Context | Unannotated local |
| `title.set_text(value)` | `TextView.setText(CharSequence)` | Declared string or literal |
| `self.set_content_view(title)` | `Activity.setContentView(View)` | Exactly once outside branches |

Multiple TextView locals can be constructed within the register budget, but only one becomes the content view. Layout containers and adding child views are not supported.

## 📏 Register budget

`on_create` reserves two incoming registers and permits **14 local/temporary registers**. Every declared local counts. Inline string values, comparison literals, helper literal arguments, and some copies/arithmetic also introduce temporary registers. Use `--dump-ir` to see synthetic names such as `$str0`.

This is a backend limitation, not a Python limit. There is currently no lifetime-based register reuse. A short source file can exhaust the budget if it creates many temporaries.

## 🚧 Common unsupported forms

The following fragment intentionally fails compilation:

```python unsupported
counter: int = 1
counter = counter + 1  # Reassignment is not implemented.
```

Other unavailable features include loops, lists/dictionaries, floats, exceptions, f-strings, arbitrary Python libraries, callbacks, additional lifecycle methods, multi-module projects and resources. Consult [roadmap](../roadmap.md) for planned semantics rather than guessing syntax.
