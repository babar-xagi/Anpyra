# 💬 Native Chatbot Implementation and File Map

The chatbot is an unreleased source addition. It preserves the Python → AST → IR → DEX → APK architecture. It adds a small native interaction path rather than embedding CPython or the Python OpenAI SDK.

## 🗂️ New files and ownership

| File | Implementation | Fix here when |
| --- | --- | --- |
| [components/layout.py](../../src/anpyra/components/layout.py) | Editor-facing Column/Row/ScrollView declarations | Layout authoring signatures are wrong |
| [components/textinput.py](../../src/anpyra/components/textinput.py) | TextView-derived TextInput with hint/password/hint color | Input authoring signature is wrong |
| [components/chat.py](../../src/anpyra/components/chat.py) | ChatSession's six-view/model contract | Public binding signature is wrong |
| [compiler/interactive.py](../../src/anpyra/compiler/interactive.py) | Constructor/layout lowering, dimensions, weight, margin, binding types and masked-key check | Source is accepted/rejected incorrectly |
| [android/layout.py](../../src/anpyra/android/layout.py) | LinearLayout orientation/children/weighted parameters, dp conversion, ScrollView and EditText calls | Geometry, hint, input type or keyboard behavior is wrong |
| [android/chat.py](../../src/anpyra/android/chat.py) | ChatPlan, field/method pools, click dispatch, worker, JSON, history, delivery and scroll behavior | Sending, response parsing, state or UI recovery is wrong |
| [android/classes.py](../../src/anpyra/android/classes.py) | Multi-class DEX tables, interfaces, instance/static field metadata and method code offsets | ART rejects class metadata, fields or interfaces |
| [android/method_builder.py](../../src/anpyra/android/method_builder.py) | Typed invocation/field helpers and code items with exception tables | Worker/callback registers, invoke forms or catch offsets are wrong |
| [examples/chatbot/app.py](../../examples/chatbot/app.py) | Complete styled app using existing Screen/TextView/Button plus layouts and input | App layout, colors, copy or spacing need changes |
| [examples/chatbot/anpyra.toml](../../examples/chatbot/anpyra.toml) | Example identity, min SDK 24, target SDK 36 and output path | Example identity/build metadata need changes |
| [scripts/check_chat_device.py](../../scripts/check_chat_device.py) | Key-free controlled device acceptance | Device automation or fixture protocol is wrong |
| [unit tests](../../tests/unit/test_interactive.py) | Source contracts and independently read class/field/catch metadata | Compiler/DEX regression needs coverage |
| [build tests](../../tests/integration/test_chat_build.py) | Signed chat build, manifest permission and reproducibility | Package integration regresses |

Authoring classes intentionally raise on host execution. They describe compiled syntax; runtime implementations are generated native Android methods.

## 🔧 Existing files changed

| File | Change |
| --- | --- |
| `compiler/ir.py` | NewLayout, AddLayoutChild, NewTextInput, SetScrollContent and BindChatSession |
| `compiler/frontend.py` | New imports/types, generic View children, parent/cycle tracking, source budgets and constructor/method dispatch |
| `android/codegen.py` | Wider layout/input frame, scalar-first assignment and scoped controller field/listener binding |
| `android/dalvik.py` | Instance get/put forms, check-cast, move-exception and interface invocation support |
| `android/dex.py` | Canonical entry point; legacy writer remains for ordinary apps, chat apps dispatch to the multi-class writer |
| `android/screen.py` | Register native layout/input references alongside existing UI references |
| `android/manifest.py` | Conditional INTERNET permission; ordinary manifest bytes stay unchanged |
| `android/manifest_inspect.py` | Return declared permissions for verification/tests |
| `build.py` | Enable INTERNET only when the app contains a ChatSession binding |
| Package/component `__init__.py` | Export the new authoring types |

## ⚙️ Generated classes and runtime flow

The example generates three classes inside its DEX:

1. **MainActivity** implements View.OnClickListener and, when a transcript ScrollView exists, ViewTreeObserver.OnGlobalLayoutListener. Fields retain the six widget references, history JSONArray, busy flag and optional scrolling container/flag.
2. **MainActivity$ChatWorker** implements Runnable. It captures Activity, key, pending message and serialized history, runs on Thread, performs the HTTP request and parses response items.
3. **MainActivity$ChatDelivery** implements Runnable. It posts the result back using Activity.runOnUiThread, ignores destroyed/finishing Activities and calls chatReply.

`onClick` validates trimmed key/message. New chat resets successful history. Send marks busy and disables both buttons and both inputs before starting the worker. The busy flag prevents duplicate concurrent sends. Delivery restores controls after successful or failed requests. Successful replies commit a copied history array and clear message input; failures leave the message available for retry. A pending-scroll flag waits for global layout after text append, then scrolls to the newly measured bottom. ScrollView children receive match-parent width and wrap-content height.

Generated callback/worker listings are included in check/build output with class-qualified names. The original lifecycle listings and legacy byte regression fixtures remain intact.

## 🌐 Request and parser contract

The production endpoint is fixed to OpenAI HTTPS. The key becomes the Authorization header in memory. No logging, file persistence, preferences or Python SDK is involved. The key EditText's saved state is disabled; autofill exclusion is guarded for API 26+. The worker uses native URL/HttpURLConnection, streams and org.json with bounded connect/read timeouts.

Request fields are `model`, complete `input`, `store=false`, `reasoning.effort=none`, `include=[reasoning.encrypted_content]`, and `max_output_tokens=1500`. This profile is intended for GPT-5.5-compatible models. Output parsing checks completed status, walks every item's content, renders output_text/refusal, and retains every successful output item for the next request. Failure paths show controlled messages instead of raw provider errors that might contain credential details.

The current history is Activity-local and unbounded by turn count. Context overflow remains a provider error. Streaming, retries, cancellation, long-lived storage, generic user classes/callbacks and multi-Activity composition are future work.

## 🧱 DEX details

The multi-class writer owns sorted/deduplicated strings, types, prototypes, fields, methods and class definitions. Parameter/interface type lists are shared; interface lists are sorted by type index. Class data keeps separate delta sequences for static/instance fields and direct/virtual methods. Code items are four-byte aligned. The map is ordered by section offset; SHA-1 precedes Adler-32.

Generated controller methods use at most 16 registers, keeping instance field operands inside their four-bit limits. Wider lifecycle object registers use the existing range-invocation bank. MethodBuilder emits a single typed Exception handler with correct code-unit ranges, odd-insn padding and handler-list-relative offsets. It supplies method assembly for inspection. The host verifier still checks checksums/signature rather than proving ART type correctness; real device checks cover runtime acceptance.

## 🧪 Run verification

```powershell
python -m unittest tests.unit.test_interactive tests.integration.test_chat_build -v
python scripts/check_chat_device.py --serial DEVICE_ID
```

The device script builds a separate `dev.anpyra.chatchecks` app, starts a loopback fixture server, uses adb reverse and records only synthetic request bodies. The **test-only** APK uses a patched localhost HTTP endpoint and target SDK 27; the real example retains OpenAI HTTPS and target SDK 36. All overrides are scoped to the fixture build. No real API key, paid API request or phone settings change is needed. The reverse mapping and host server are cleaned up; its test app remains installed.

The fixture checks missing fields, request locking, full-output history, long text, refusal, malformed JSON, incomplete responses, quota recovery and reset. It validates native controller behavior; it does not establish a successful AI conversation. Keep the phone unlocked and leave its test app foreground. Input values are redacted from diagnostic UI state.
