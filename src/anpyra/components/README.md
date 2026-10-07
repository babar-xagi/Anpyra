# 🧩 Android Components

`screen.py` contains the Screen authoring API, validated Background/Image/Gradient value objects and color/opacity parsing. Applications import these through `anpyra.components` or the package root.

Screen is an Android content-area container. Styles are compiled declarations; the host does not preview the UI. Compiler parsing lives in `compiler/screen_style.py`, native bindings in `android/screen.py` and background emission in `android/backgrounds.py`. Image validation/conversion/packaging lives in `android/assets.py`.

See the [screen guide](../../../docs/user_guide/screen.md), [native component internals](../../../docs/developer_guide/screen_styling.md) and [runnable example](../../../examples/screen_style/README.md).

## 🔤 TextView

[textview.py](textview.py) is the canonical TextView authoring implementation. It defines validated Font/Shadow/TextStyle values and writable editor property interfaces. Root and legacy imports re-export the same class. Parsing/merged state lives in compiler/text_style.py; native emission in android/textview.py; font validation in android/fonts.py and asset preparation in android/assets.py. See the [user guide](../../../docs/user_guide/textview.md) and [implementation guide](../../../docs/developer_guide/textview_styling.md).

## 🖱️ Unreleased event/state additions

[state.py](state.py) defines the typed State initializer. Button.on_click binds named Activity methods; TextView/input and view declarations expose supported runtime text/enabled primitives. Source validation lives in compiler/events.py, native behavior in android/events.py and shared composition in android/interactive.py. See the [user guide](../../../docs/user_guide/events.md) and [implementation map](../../../docs/developer_guide/events.md).

## 💬 Interactive components (0.1.4)

[layout.py](layout.py) declares Column/Row/ScrollView; [textinput.py](textinput.py) declares native keyboard/password input; [chat.py](chat.py) binds the standalone ChatSession. Validation belongs in compiler/interactive.py, native layout/input calls in android/layout.py and controller behavior in android/chat.py. See the [user guide](../../../docs/user_guide/chatbot.md) and [file map](../../../docs/developer_guide/chatbot.md).

## 🟦 Button

[button.py](button.py) owns the real Button subtype and immutable design/geometry/icon values. Shared text signatures remain in textview.py. Source parsing lives in compiler/button_style.py; native state/shape/ripple/layout/icon emission in android/button.py; icon fitting in android/icons.py; safe image decoding in android/assets.py. See the [user guide](../../../docs/user_guide/button.md) and [ownership guide](../../../docs/developer_guide/button_styling.md).
