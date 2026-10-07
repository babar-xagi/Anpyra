# 🖱️ Button Events and Typed App State

This is an **unreleased source feature**. Published Anpyra 0.1.4 includes ChatSession's built-in actions but does not include these generic callbacks or State declarations. Install the current checkout with `uv pip install -e ".[dev]"` to use this guide.

## ⚡ First counter

```python
from anpyra import Activity, Button, Column, State, TextView

class MainActivity(Activity):
    def on_create(self, state):
        self.count: int = State(0, persist=True)
        page = Column(self)
        label = TextView(self, text="0")
        self.label = label
        button = Button(self, text="Add one")
        button.on_click(self.increment)
        page.add(label)
        page.add(button)
        self.set_content_view(page)
        self.refresh()

    def increment(self):
        self.count += 1
        self.refresh()

    def refresh(self):
        self.label.set_text(str(self.count))
```

Pass the method reference `self.increment`, without `()`. Android calls the compiled method on the UI thread when the native Button is clicked. `self.refresh()` is a normal supported call between these methods; its initial call updates the label after any saved count has been restored.

## 🧠 Fields and callback locals

Declare retained scalar fields in `on_create`, with an exact `int`, `str` or `bool` annotation and a literal default:

```python
self.count: int = 0
self.message: str = "Ready"
self.enabled: bool = True
```

Those fields are mutable in handlers and default to memory-only state. Store widget references with `self.label = label` after constructing the local widget. Handlers cannot capture lifecycle locals such as `label` directly: use `self.label`. Widget references cannot be rebound inside handlers.

Handler locals may be annotated or inferred, reassigned without changing type, and initialized on every path that reaches their read. Local values do not survive a later click; use Activity fields for retained values. Calling a handler from `on_create` before its required fields are initialized is rejected, including dependencies through other handlers.

## 💾 Opt-in saved-instance state

```python
self.count: int = State(0, persist=True)
self.name: str = State("", persist=True)
self.paused: bool = False
```

`persist=True` saves that scalar to Android's instance-state Bundle and restores it when Android supplies that Bundle to the recreated Activity. Count/name are restored before later initialization calls such as `self.refresh()`. The memory-only paused flag returns to its default. Widget references are recreated and never serialized.

This is Android saved-instance state, not a database or settings file. A new task without saved state starts from defaults. `self.recreate()` can demonstrate the same save/restore path without changing phone rotation/display settings. Physical rotation, process restoration and additional Android versions need separate acceptance records; recreation was tested on API 33.

Input widgets retain disabled view-state saving. To preserve selected input, explicitly copy `self.entry.get_text()` into an opted-in scalar field, then restore the widget from that field in initialization. Draft input and password fields are not automatically persisted. Keep temporary keys in memory-only state.

## ⌨️ Runtime widget operations

In an Activity handler:

```python
name: str = self.entry.get_text()
if name:
    self.preview.text = "Hello, " + name + "!"
else:
    self.preview.set_text("Enter your name")
self.submit.set_enabled(False)
```

| Operation | Behavior |
| --- | --- |
| `get_text()` | Read TextView/TextInput/Button text as an immutable string |
| `set_text(str)` or `.text = str` | Update visible text |
| `set_enabled(bool)` | Change native enabled state |
| `is_enabled()` | Read native enabled state |
| `set_text_color(literal)` | Change text color using a compile-time Anpyra color |
| `self.recreate()` | Recreate the Activity; only allowed through click callbacks |

Style declarations still belong in `on_create`. Runtime arbitrary style assignments and dynamic color parsing are outside this first contract.

## 🧮 Expressions and limits

Handlers support scalar literals/fields/locals, integer `+`/`-` and `+=`/`-=`, string concatenation/`+=`, `str(...)`, `bool(...)`, `not`, boolean `and`/`or`, matching-type equality, integer ordering, nested `if`/`elif`/`else`, early `return`, and existing typed integer helper calls. `and`/`or` require bool operands and short-circuit. Strings and integers have normal nonempty/nonzero truthiness. Boolean text uses `True`/`False`.

Handler and field integers are **signed 32-bit values**. Arithmetic wraps like Android integer bytecode: `2147483647 + 1` becomes `-2147483648`. Legacy lifecycle integer locals retain their existing signed-16-bit literal contract. This is deliberately a restricted Python subset.

Each handler has only `self`, takes no arguments, returns no value, and may have `-> None`. Up to 32 methods, 32 Activity fields and eight scalar locals per handler are supported. Complex expressions can exhaust temporary registers; split them into simpler statements. Methods must be bound or called, and recursive method graphs are rejected. Lambdas, closures, async handlers, loops, arbitrary imports, user-defined classes and custom lifecycle methods remain unsupported.

## 💬 Use alongside ChatSession

Generic handlers can coexist with ChatSession on separate buttons. ChatSession owns its Send/New chat controls; binding another handler to those buttons is rejected. Generic clicks dispatch independently, while ChatSession's existing worker, busy handling and delivery retain their own contract.

## 📱 Complete example

From the editable checkout:

```powershell
anpyra check examples/counter --dump-ir --dump-dalvik
anpyra build examples/counter
anpyra install examples/counter/build/dev.anpyra.counter.apk --launch
```

The [Counter Lab source](../../examples/counter/app.py) includes +/−/Reset, Pause/Resume, a name input/preview and Recreate screen. Its visible title keeps the screen awake for testing; remove the keep_screen_on declaration for normal sleep behavior. See [implementation ownership](../developer_guide/events.md) and [progress](../progress.md).
