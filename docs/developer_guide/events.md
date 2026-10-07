# 🖱️ Event and State Implementation Map

Generic Python callbacks and typed Activity state are an unreleased source addition. They compile into native Activity fields/methods and a View.OnClickListener; no Python interpreter runs inside the APK.

## 🗂️ New files

| File | Responsibility | Fix here when |
| --- | --- | --- |
| [components/state.py](../../src/anpyra/components/state.py) | Editor-facing typed State(default, persist=False) initializer | State authoring signature is wrong |
| [compiler/events.py](../../src/anpyra/compiler/events.py) | Field/alias declarations, callback binding, typed expressions/statements, definite initialization, method reachability and cycle checks | Accepted syntax/types or diagnostics are wrong |
| [android/events.py](../../src/anpyra/android/events.py) | EventPlan, instance fields, click dispatch, RuntimeEmitter, native getters/setters and Bundle save/restore | Clicking, expression behavior or saved-state values are wrong |
| [android/interactive.py](../../src/anpyra/android/interactive.py) | Compose lifecycle/helpers/event methods and optional ChatSession worker/delivery classes | Features collide or native references are omitted |
| [counter/app.py](../../examples/counter/app.py) | Full styled example, counter/input controls and opted-in state | Example UX or displayed values are wrong |
| [check_events_device.py](../../scripts/check_events_device.py) | Native clicks, typed values, input, integer boundaries and recreation checks | Phone automation/acceptance needs changes |
| [test_events.py](../../tests/unit/test_events.py) | Source rejection and generated-byte behavior contracts | An event/state regression needs coverage |
| [dex_runtime.py](../../tests/dex_runtime.py) | Independent decoding/execution of the emitted event instruction subset, with controlled native calls | Byte-level behavior tests need another instruction |

The test executor is Python test infrastructure only. It is excluded from the installable wheel and is never embedded in an APK. It does not perform ART's verifier/type checking; real-device results are a separate requirement.

## 🔧 Existing changes

`compiler/ir.py` adds AppField/InitAppField/StoreAppField, BindClick/CallEvent, typed EventExpr, assignment/action/if/return nodes and EventHandler metadata. AppIR retains empty defaults for fields/handlers so historical callers and output remain compatible. `frontend.py` collects named methods, delegates lifecycle additions and carries field/handler metadata. Existing styling and helper compilation stay in their canonical modules.

`components/button.py` adds on_click; TextView and other native View authoring types expose runtime text/enabled primitives; Activity adds recreate. Root/component exports include State. `codegen.py` delegates field initialization/binding/handler calls using its reserved low registers and invocation bank. `dex.py` dispatches event/state apps to the shared interactive writer. `chat.py` retains the chat controller and delegates container composition; its click method gains a separate native name only when generic dispatch also exists.

## 🧠 Source contract and data flow

Scalar fields have exact int/str/bool types, initialized literal defaults and an explicit persistence flag. Widget fields alias initialized lifecycle views. All fields have a single lifecycle declaration. Callback locals have stable scalar types; branch merging retains only values initialized on every continuing path. Handler-to-handler calls form an acyclic reachable graph. Initial calls check transitive required fields against the fields initialized at that source location.

Handlers cannot access captured lifecycle locals, replace widget references, change field/local types or run arbitrary host Python. Source errors preserve filename/line context. Runtime text/color/enabled actions use native method contracts. Boolean string formatting preserves Python capitalization; integer math uses Android signed-32-bit wraparound and strings use native immutable concatenation.

## ⚙️ Generated code

MainActivity owns private `anpyra_field_*` fields and private retained click-button references. Public generated `anpyra_event_*` methods implement the named Python handlers. A single native onClick(View) compares button identity and invokes the matching method. RuntimeEmitter allocates typed locals below scratch registers; self is v15, keeping field operands inside the four-bit instruction limit. All caller arguments fit the generated invocation frames.

Opted-in scalar fields add native restore methods and a protected onSaveInstanceState(Bundle) override. The override calls the Activity superclass, then writes typed `anpyra.state.*` entries. Each field's lifecycle initializer writes its default and restores it only when a non-null Bundle contains its key. Null restored strings retain the default. Widget references and memory-only fields are never saved by this mechanism.

Generic handlers and ChatSession share the native listener through explicit dispatch. Generic buttons are checked first; unmatched clicks reach ChatSession's renamed internal method. The shared writer collects references from **both** plans, including their distinct EditText/TextView getText signatures, rather than losing one through dictionary-key replacement. ChatSession's send/clear controls cannot be rebound.

## 🧪 Verification and debugging

```powershell
python -m unittest tests.unit.test_events -v
python scripts/check_events_device.py --serial DEVICE_ID
python scripts/check_chat_device.py --serial DEVICE_ID --mixed --work-dir build/chat-mixed-checks
```

The event script builds its own package and records model/API/results/screenshots under build/. It verifies saved-state recreation by calling the test Activity's recreate method, without changing system rotation/display settings. The mixed script uses a separate package/signing identity and controlled responses, with no real API key. Leave the phone unlocked and avoid manual taps during the automation.

Compare source IR, class-qualified callback/restore/save listings, emitted bytes and actual phone UI when investigating a bug. Preserve identities for test APK updates. Source checking/checksums alone do not establish device acceptance. The original experiment DEX hashes and the pre-change chatbot DEX were preserved during this implementation.
