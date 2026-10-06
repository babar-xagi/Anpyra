# 🧩 Android Components

`screen.py` contains the Screen authoring API, validated Background/Image/Gradient value objects and color/opacity parsing. Applications import these through `anpyra.components` or the package root.

Screen is an Android content-area container. Styles are compiled declarations; the host does not preview the UI. Compiler parsing lives in `compiler/screen_style.py`, native bindings in `android/screen.py` and background emission in `android/backgrounds.py`. Image validation/conversion/packaging lives in `android/assets.py`.

See the [screen guide](../../../docs/user_guide/screen.md), [native component internals](../../../docs/developer_guide/screen_styling.md) and [runnable example](../../../examples/screen_style/README.md).

## 🔤 TextView

[textview.py](textview.py) is the canonical TextView authoring implementation. It defines validated Font/Shadow/TextStyle values and writable editor property interfaces. Root and legacy imports re-export the same class. Parsing/merged state lives in compiler/text_style.py; native emission in android/textview.py; font validation in android/fonts.py and asset preparation in android/assets.py. See the [user guide](../../../docs/user_guide/textview.md) and [implementation guide](../../../docs/developer_guide/textview_styling.md).

## 🟦 Button

[button.py](button.py) owns the real Button subtype and immutable design/geometry/icon values. Shared text signatures remain in textview.py. Source parsing lives in compiler/button_style.py; native state/shape/ripple/layout/icon emission in android/button.py; icon fitting in android/icons.py; safe image decoding in android/assets.py. See the [user guide](../../../docs/user_guide/button.md) and [ownership guide](../../../docs/developer_guide/button_styling.md).
