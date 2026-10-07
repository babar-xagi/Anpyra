# 💬 Standalone Android Chatbot

This **unreleased source feature** builds a native phone app from Anpyra components. The published 0.1.3 wheel does not contain the new layout, input or ChatSession APIs yet. Use the current editable checkout.

## 🛠️ Install and build

From the repository root in PowerShell:

```powershell
uv venv --python 3.12
uv pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m anpyra check examples/chatbot --dump-ir --dump-dalvik
.\.venv\Scripts\python.exe -m anpyra build examples/chatbot
.\.venv\Scripts\python.exe -m anpyra install examples/chatbot/build/dev.anpyra.chatbot.apk --launch
```

Skip `uv venv` if the environment already exists. The pip alternative is `python -m pip install -e ".[dev]"` in your activated environment. Android builds require Python and Anpyra's dependencies; no Java/JDK, Kotlin, Android SDK/NDK build kit, Gradle or Android Studio. Installation needs optional adb and an authorized Android API 24+ device. The recorded component device checks use API 33.

You do not install the Python `openai` package into the APK. Android executes generated native HTTPS/JSON calls. Ordinary Python library imports and the pasted console `while True` chatbot are outside the compiler's supported subset.

## 📱 Use the app

1. Enter your temporary OpenAI API key in the masked field.
2. Enter a message and press **Send message**.
3. Wait for the response; request controls are disabled while a request runs.
4. Ask a follow-up. The app sends successful conversation turns with the next request.
5. Press **New chat** to clear conversation history. The key stays in the current screen.

The key is entered at runtime and is absent from source, APK constants, reports and Git. Input state saving is disabled; the chat key is excluded from autofill on API 26+. The app writes no key or conversation files. Closing/recreating the Activity resets key and history. This includes rotation or Android recreating the screen. Key validity and expiry are controlled by the API account; the app does not create its own 30-minute expiry.

The demo keeps its own visible window awake for phone testing. This is `title.style.keep_screen_on = True`; remove that declaration for normal automatic screen sleep. System display settings are unchanged.

## 🧩 Layout and input concepts

`Screen` supplies the background. `Column` stacks children vertically; `Row` places them horizontally. `ScrollView` accepts one widget or layout and scrolls content taller than the viewport. A native `TextInput` accepts keyboard input and reuses TextView styling.

```python
from anpyra import Activity, Column, Row, TextInput, TextView, Button

class MainActivity(Activity):
    def on_create(self, state):
        page = Column(self)
        page.set_padding(16)
        heading = TextView(self, text="Your message")
        page.add(heading)
        entry = TextInput(self, hint="Write here", hint_color="#64748b")
        entry.style.size = 16
        page.add(entry, height=72, margin=(8, 0))
        actions = Row(self)
        send = Button(self, text="Send")
        actions.add(send, width=0, height=48, weight=1)
        page.add(actions)
        self.set_content_view(page)
```

This small layout example demonstrates input/geometry only. Connect actions using ChatSession in the complete [chatbot source](../../examples/chatbot/app.py).

| Option | Meaning |
| --- | --- |
| `width`, `height` | dp numbers, `"match_parent"`, or `"wrap_content"` |
| `weight` | Share the row's remaining width or column's remaining height; use zero size on that axis |
| `margin` | dp, CSS order: one value, `(vertical, horizontal)`, or `(top, right, bottom, left)` |
| `set_padding(...)` | Inside spacing in dp; the same one/two/four-value convention |
| `password=True` | Masked single-line input; required for ChatSession's key field |
| `hint_color` | Any supported Anpyra color; `None` preserves Android's hint color |

Each child has one parent. Cycles, attaching a layout to itself, a second ScrollView child, and invalid dimensions/types are rejected. Screen is the Activity root; put a layout/widget inside it. `add()` supplies the parent layout geometry and overrides the child's earlier standalone width/height/margin parameters. Configure Button design before adding it.

## 🔗 ChatSession binding

The complete example creates the six views, then binds them:

```python
_chat = ChatSession(
    self,
    key_input=key_input,
    message_input=message_input,
    transcript=transcript,
    status=status,
    send_button=send_button,
    clear_button=clear_button,
    model="gpt-5.5",
)
```

Declare one controller with distinct views outside branches. Put the transcript directly inside a ScrollView to enable automatic scrolling after replies. ChatSession is a focused native controller; arbitrary Python `on_click` functions are still unsupported.

## 🌐 Requests and conversation memory

The worker sends `POST https://api.openai.com/v1/responses` directly from the phone. No Windows relay or Python server is needed. The current request profile uses the selected model (default `gpt-5.5`), reasoning effort `none`, a 1,500-output-token limit and `store: false`. The selected model must support this profile.

Successful history retains the user message and **all** response output items, including encrypted reasoning content when present. Incomplete/error responses do not enter history. Text and refusal content render as text; the app does not render Markdown or run returned code. See OpenAI's [conversation state guide](https://developers.openai.com/api/docs/guides/conversation-state) and [GPT-5.5 reference](https://developers.openai.com/api/docs/models/gpt-5.5).

## 🧯 Errors and current limits

CLI dumps preserve the terminal's encoding and escape unsupported Unicode characters in limited output pipes. Use `python -X utf8 -m anpyra check examples/chatbot --dump-dalvik` for UTF-8 redirected output.

| Status | What to check |
| --- | --- |
| Enter your temporary API key | The masked field is empty |
| Type a message first | Message contains only whitespace or is empty |
| Authentication failed | Key validity, expiry and project permissions |
| Model unavailable | The selected model's availability for that project |
| Rate limit or quota reached | API response 429; quota/credits or request rate must be resolved before retry |
| Network request failed | Internet, connection/read timeout, or unreadable JSON response |
| Response incomplete | Use a shorter request; the partial response was not added to history |

Connection timeout is 15 seconds; the read timeout is 90 seconds. There is no streaming, cancellation, automatic retry, durable history, file upload, tool execution or generic callback system. The response transcript is selectable text in a scrolling area. Layout/input apps have a 48-symbol source budget; at most 14 of those may be scalar int/bool locals.

The supplied temporary key's live API check returned exhausted quota. That result proves neither a live AI answer nor model-memory behavior. Controlled phone tests validate controller behavior separately; see [progress](../progress.md). OpenAI's [error-code guide](https://developers.openai.com/api/docs/guides/error-codes) distinguishes exhausted credits from temporary rate limits.
