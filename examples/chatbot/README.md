# 💬 Anpyra Chat

A standalone native Android chatbot using Screen, TextView, styled Buttons, Column/Row/ScrollView, TextInput and ChatSession. It calls OpenAI directly from the phone and accepts a temporary key at runtime.

Use the current editable source checkout; these new APIs are not in the published 0.1.3 package yet. From the repository root:

```powershell
uv pip install -e ".[dev]"
anpyra check examples/chatbot
anpyra build examples/chatbot
anpyra install examples/chatbot/build/dev.anpyra.chatbot.apk --launch
```

Enter the key in the masked field, type a message and press Send message. Successful turns remain in memory; New chat resets them. Closing/recreating the Activity clears the key and history. The app's selected model is `gpt-5.5`. API access and available quota are required for live replies.

The example keeps its visible screen awake during testing. Remove `title.style.keep_screen_on = True` for ordinary sleep behavior. It does not change system settings.

See the [detailed user guide](../../docs/user_guide/chatbot.md) for setup, layout concepts, usage and limitations, and the [file-by-file developer guide](../../docs/developer_guide/chatbot.md) for implementation and bug-fixing ownership.
