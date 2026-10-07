"""Native standalone Responses client: UI listener, HTTPS worker and UI delivery."""

from ..compiler.ir import (
    ApplyScreenBackground,
    BindChatSession,
    LoadConst,
    NewLayout,
    SetScrollContent,
)
from .backgrounds import SDK_FIELD, background_fields
from .button import button_fields, button_strings
from .classes import ClassDefinition, MethodDefinition, write_classes
from .codegen import _walk_ops, generate_methods
from .dalvik import OP_IF_GE, OP_IF_LT, OP_IF_NE, OP_INVOKE_VIRTUAL, emit_invoke
from .dex_types import DexBuild, FieldKey, MethodKey, MethodListing
from .layout import EDIT, SCROLL, layout_strings
from .method_builder import MethodBuilder
from .screen import ACTIVITY_TYPE, screen_methods
from .textview import textview_fields, textview_strings

OBJECT = "Ljava/lang/Object;"
STRING = "Ljava/lang/String;"
VIEW = "Landroid/view/View;"
TEXT = "Landroid/widget/TextView;"
LISTENER = "Landroid/view/View$OnClickListener;"
RUNNABLE = "Ljava/lang/Runnable;"
GLOBAL_LAYOUT = "Landroid/view/ViewTreeObserver$OnGlobalLayoutListener;"
JSON = "Lorg/json/JSONObject;"
ARRAY = "Lorg/json/JSONArray;"
HTTP = "Ljava/net/HttpURLConnection;"
BUILDER = "Ljava/lang/StringBuilder;"
EXCEPTION = "Ljava/lang/Exception;"
ENDPOINT = "https://api.openai.com/v1/responses"


class ChatPlan:
    def __init__(self, app, binding):
        self.app, self.binding = app, binding
        self.builders = []
        self.main = app.class_descriptor
        ops = tuple(_walk_ops(app.operations))
        scrolls = {op.target for op in ops if isinstance(op, NewLayout) and op.kind == "ScrollView"}
        self.scroll = next(
            (
                op.receiver
                for op in ops
                if isinstance(op, SetScrollContent)
                and op.view == binding.transcript
                and op.receiver in scrolls
            ),
            None,
        )
        self.worker = self.main[:-1] + "$ChatWorker;"
        self.delivery = self.main[:-1] + "$ChatDelivery;"
        self.refs = screen_methods(self.main, tuple(_walk_ops(app.operations)))
        self.fields = {}
        self.literals = {
            "",
            "[]",
            binding.model,
            ENDPOINT,
            "UTF-8",
            "POST",
            "Content-Type",
            "application/json",
            "Authorization",
            "Bearer ",
            "role",
            "user",
            "content",
            "input",
            "model",
            "store",
            "reasoning",
            "effort",
            "none",
            "include",
            "reasoning.encrypted_content",
            "max_output_tokens",
            "output",
            "type",
            "message",
            "output_text",
            "text",
            "error",
            "status",
            "incomplete",
            "refusal",
            "Ready • gpt-5.5",
            "Thinking…",
            "Type a message first.",
            "Enter your temporary API key above.",
            "New chat started. Your key stays on this screen.",
            "You\n",
            "\n\nAnpyra\n",
            "\n\n",
            "Authentication failed. Check or renew your temporary key.",
            "This model is unavailable for your key.",
            "Rate limit or quota reached. Please try again later.",
            "The API request failed. Check your key/model and try again.",
            "Network request failed. Check internet and try again.",
            "The model did not return text. Try a shorter request.",
            "completed",
            "Response was incomplete. Try a shorter message.",
            "Reply received • ready",
            "Welcome! Enter your temporary key, then ask anything.\n\n",
        }
        for alias, view, descriptor in (
            ("key", binding.key_input, EDIT),
            ("message", binding.message_input, EDIT),
            ("transcript", binding.transcript, TEXT),
            ("status", binding.status, TEXT),
            ("send", binding.send_button, "Landroid/widget/Button;"),
            ("clear", binding.clear_button, "Landroid/widget/Button;"),
        ):
            self.fields[alias] = FieldKey(self.main, "chat_" + alias, descriptor)
        self.fields["busy"] = FieldKey(self.main, "chat_busy", "Z")
        self.fields["history"] = FieldKey(self.main, "chat_history", ARRAY)
        if self.scroll:
            self.fields["scroll"] = FieldKey(self.main, "chat_scroll", SCROLL)
            self.fields["scroll_pending"] = FieldKey(self.main, "chat_scroll_pending", "Z")
            self.add("scroll_layout", VIEW, "requestLayout")
            self.add(
                "scroll_observer", VIEW, "getViewTreeObserver", "Landroid/view/ViewTreeObserver;"
            )
            self.add(
                "scroll_bind",
                "Landroid/view/ViewTreeObserver;",
                "addOnGlobalLayoutListener",
                params=(GLOBAL_LAYOUT,),
            )
            self.add("scroll_bottom", SCROLL, "fullScroll", "Z", ("I",))
            self.add("scroll_run", self.main, "onGlobalLayout")
        for alias, descriptor in (
            ("activity", self.main),
            ("key", STRING),
            ("message", STRING),
            ("history", STRING),
        ):
            self.fields["w_" + alias] = FieldKey(self.worker, alias, descriptor)
        for alias, descriptor in (
            ("activity", self.main),
            ("text", STRING),
            ("pending", STRING),
            ("output", STRING),
            ("ok", "Z"),
        ):
            self.fields["d_" + alias] = FieldKey(self.delivery, alias, descriptor)
        self.fields["false"] = FieldKey("Ljava/lang/Boolean;", "FALSE", "Ljava/lang/Boolean;")
        self.fields["sdk"] = SDK_FIELD
        self.add("autofill", VIEW, "setImportantForAutofill", params=("I",))
        self.add(
            "password_mask",
            "Landroid/text/method/PasswordTransformationMethod;",
            "getInstance",
            "Landroid/text/method/PasswordTransformationMethod;",
        )
        self.add(
            "transformation",
            TEXT,
            "setTransformationMethod",
            params=("Landroid/text/method/TransformationMethod;",),
        )
        self.add("action_bar", ACTIVITY_TYPE, "getActionBar", "Landroid/app/ActionBar;")
        self.add("hide_bar", "Landroid/app/ActionBar;", "hide")
        self.add("window", ACTIVITY_TYPE, "getWindow", "Landroid/view/Window;")
        self.add("keyboard_mode", "Landroid/view/Window;", "setSoftInputMode", params=("I",))
        self.add("object_ctor", OBJECT, "<init>")
        self.add("click_bind", VIEW, "setOnClickListener", params=(LISTENER,))
        self.add("enabled", VIEW, "setEnabled", params=("Z",))
        self.add("get_text", EDIT, "getText", "Landroid/text/Editable;")
        self.add("to_string", OBJECT, "toString", STRING)
        self.add("trim", STRING, "trim", STRING)
        self.add("empty", STRING, "isEmpty", "Z")
        self.add("json_ctor", JSON, "<init>")
        self.add("json_string", JSON, "<init>", params=(STRING,))
        self.add("array_ctor", ARRAY, "<init>")
        self.add("array_string", ARRAY, "<init>", params=(STRING,))
        self.add("array_put", ARRAY, "put", ARRAY, (OBJECT,))
        self.add("array_length", ARRAY, "length", "I")
        self.add("array_item", ARRAY, "getJSONObject", JSON, ("I",))
        self.add("json_put", JSON, "put", JSON, (STRING, OBJECT))
        self.add("json_array", JSON, "optJSONArray", ARRAY, (STRING,))
        self.add("json_text", JSON, "optString", STRING, (STRING,))
        self.add("json_has", JSON, "has", "Z", (STRING,))
        self.add("equals", STRING, "equals", "Z", (OBJECT,))
        self.add("builder_ctor", BUILDER, "<init>")
        self.add("builder_append", BUILDER, "append", BUILDER, (STRING,))
        self.add("builder_text", BUILDER, "toString", STRING)
        self.add("set_text", TEXT, "setText", params=("Ljava/lang/CharSequence;",))
        self.add("append_text", TEXT, "append", params=("Ljava/lang/CharSequence;",))
        self.add("worker_ctor", self.worker, "<init>", params=(self.main, STRING, STRING, STRING))
        self.add("worker_run", self.worker, "run")
        self.add("delivery_ctor", self.delivery, "<init>", params=(self.main,))
        self.add("delivery_run", self.delivery, "run")
        self.add("thread_ctor", "Ljava/lang/Thread;", "<init>", params=(RUNNABLE,))
        self.add("thread_start", "Ljava/lang/Thread;", "start")
        self.add("ui_post", ACTIVITY_TYPE, "runOnUiThread", params=(RUNNABLE,))
        self.add("finishing", ACTIVITY_TYPE, "isFinishing", "Z")
        self.add("destroyed", ACTIVITY_TYPE, "isDestroyed", "Z")
        self.add("on_click", self.main, "onClick", params=(VIEW,))
        self.add("on_reply", self.main, "chatReply", params=(STRING, STRING, STRING, "Z"))
        self.add("init_chat", self.main, "initChat")
        self.add("url_ctor", "Ljava/net/URL;", "<init>", params=(STRING,))
        self.add("url_open", "Ljava/net/URL;", "openConnection", "Ljava/net/URLConnection;")
        self.add("http_method", HTTP, "setRequestMethod", params=(STRING,))
        self.add("http_connect_timeout", HTTP, "setConnectTimeout", params=("I",))
        self.add("http_read_timeout", HTTP, "setReadTimeout", params=("I",))
        self.add("http_output_flag", HTTP, "setDoOutput", params=("Z",))
        self.add("http_header", HTTP, "setRequestProperty", params=(STRING, STRING))
        self.add("http_output", HTTP, "getOutputStream", "Ljava/io/OutputStream;")
        self.add("http_input", HTTP, "getInputStream", "Ljava/io/InputStream;")
        self.add("http_code", HTTP, "getResponseCode", "I")
        self.add("http_disconnect", HTTP, "disconnect")
        self.add("utf8_bytes", STRING, "getBytes", "[B", (STRING,))
        self.add("write_bytes", "Ljava/io/OutputStream;", "write", params=("[B",))
        self.add("close_output", "Ljava/io/OutputStream;", "close")
        self.add(
            "reader_ctor",
            "Ljava/io/InputStreamReader;",
            "<init>",
            params=("Ljava/io/InputStream;", STRING),
        )
        self.add("buffer_ctor", "Ljava/io/BufferedReader;", "<init>", params=("Ljava/io/Reader;",))
        self.add("read_line", "Ljava/io/BufferedReader;", "readLine", STRING)
        self.add("close_reader", "Ljava/io/BufferedReader;", "close")
        self.add("integer", "Ljava/lang/Integer;", "valueOf", "Ljava/lang/Integer;", ("I",))

    def add(self, key, owner, name, returns="V", params=()):
        self.refs[key] = MethodKey(owner, name, returns, params)

    def builder(self, pools, registers=16, inputs=1, name=None):
        builder = MethodBuilder(pools, self.refs, self.fields, registers, inputs)
        self.builders.append((self.refs[name], builder))
        return builder

    def init(self, pools):
        b = self.builder(pools, 4, 1, "init_chat")
        b.create(0, ARRAY, "array_ctor")
        b.put(0, 3, "history")
        b.const(0, 0)
        b.put(0, 3, "busy")
        b.get(0, 3, "key")
        b.invoke("password_mask", (), static=True, result=1)
        b.invoke("transformation", (0, 1))
        if self.scroll:
            b.get(0, 3, "scroll")
            b.invoke("scroll_observer", (0,), result=0)
            b.invoke("scroll_bind", (0, 3))
        b.invoke("action_bar", (3,), result=0)
        b.zero(0, "no_bar")
        b.invoke("hide_bar", (0,))
        b.label("no_bar")
        b.invoke("window", (3,), result=0)
        b.const(1, 0x13)
        b.invoke("keyboard_mode", (0, 1))
        b.asm.emit("sget", 0, pools.fields[SDK_FIELD], SDK_FIELD.name, size=2)
        b.const(1, 26)
        b.compare(OP_IF_LT, 0, 1, "done")
        b.get(0, 3, "key")
        b.const(1, 8)
        b.invoke("autofill", (0, 1))
        b.label("done")
        b.asm.emit("return_void", size=1)
        return b.finish()

    def scroll_run(self, pools):
        b = self.builder(pools, 4, 1, "scroll_run")
        b.get(0, 3, "scroll_pending")
        b.zero(0, "done")
        b.const(0, 0)
        b.put(0, 3, "scroll_pending")
        b.get(0, 3, "scroll")
        b.const(1, 130)
        b.invoke("scroll_bottom", (0, 1))
        b.label("done")
        b.asm.emit("return_void", size=1)
        return b.finish()

    def click(self, pools):
        b = self.builder(pools, 16, 2, "on_click")
        b.get(0, 14, "busy")
        b.zero(0, "dispatch")
        b.jump("done")
        b.label("dispatch")
        b.get(0, 14, "clear")
        b.compare(OP_IF_NE, 0, 15, "send")
        b.create(0, ARRAY, "array_ctor")
        b.put(0, 14, "history")
        b.get(0, 14, "transcript")
        b.string(1, "Welcome! Enter your temporary key, then ask anything.\n\n")
        b.invoke("set_text", (0, 1))
        b.get(0, 14, "status")
        b.string(1, "New chat started. Your key stays on this screen.")
        b.invoke("set_text", (0, 1))
        b.jump("done")
        b.label("send")
        b.get(0, 14, "key")
        b.invoke("get_text", (0,), result=1)
        b.invoke("to_string", (1,), result=1)
        b.invoke("trim", (1,), result=1)
        b.invoke("empty", (1,), result=2)
        b.zero(2, "message")
        b.get(0, 14, "status")
        b.string(2, "Enter your temporary API key above.")
        b.invoke("set_text", (0, 2))
        b.jump("done")
        b.label("message")
        b.get(0, 14, "message")
        b.invoke("get_text", (0,), result=3)
        b.invoke("to_string", (3,), result=3)
        b.invoke("trim", (3,), result=3)
        b.invoke("empty", (3,), result=2)
        b.zero(2, "request")
        b.get(0, 14, "status")
        b.string(2, "Type a message first.")
        b.invoke("set_text", (0, 2))
        b.jump("done")
        b.label("request")
        b.const(2, 1)
        b.put(2, 14, "busy")
        for field in ("send", "clear", "message", "key"):
            b.get(0, 14, field)
            b.const(2, 0)
            b.invoke("enabled", (0, 2))
        b.get(0, 14, "status")
        b.string(2, "Thinking…")
        b.invoke("set_text", (0, 2))
        b.get(0, 14, "history")
        b.invoke("to_string", (0,), result=4)
        b.create(5, self.worker, "worker_ctor", (14, 1, 3, 4))
        b.create(6, "Ljava/lang/Thread;", "thread_ctor", (5,))
        b.invoke("thread_start", (6,))
        b.label("done")
        b.asm.emit("return_void", size=1)
        return b.finish()

    def worker_constructor(self, pools):
        b = self.builder(pools, 5, 5, "worker_ctor")
        b.invoke("object_ctor", (0,), direct=True)
        for register, field in (
            (1, "w_activity"),
            (2, "w_key"),
            (3, "w_message"),
            (4, "w_history"),
        ):
            b.put(register, 0, field)
        b.asm.emit("return_void", size=1)
        return b.finish()

    def delivery_constructor(self, pools):
        b = self.builder(pools, 2, 2, "delivery_ctor")
        b.invoke("object_ctor", (0,), direct=True)
        b.put(1, 0, "d_activity")
        b.asm.emit("return_void", size=1)
        return b.finish()

    def delivery_run(self, pools):
        b = self.builder(pools, 8, 1, "delivery_run")
        b.get(0, 7, "d_activity")
        b.invoke("finishing", (0,), result=1)
        b.zero(1, "alive")
        b.jump("done")
        b.label("alive")
        b.invoke("destroyed", (0,), result=1)
        b.zero(1, "reply")
        b.jump("done")
        b.label("reply")
        for register, name in ((1, "d_text"), (2, "d_pending"), (3, "d_output"), (4, "d_ok")):
            b.get(register, 7, name)
        b.invoke("on_reply", (0, 1, 2, 3, 4))
        b.label("done")
        b.asm.emit("return_void", size=1)
        return b.finish()

    def reply(self, pools):
        b = self.builder(pools, 16, 5, "on_reply")
        # Incoming: activity v11, response text v12, pending message v13,
        # serialized output items v14, success flag v15.
        b.const(0, 0)
        b.put(0, 11, "busy")
        for field in ("send", "clear", "message", "key"):
            b.get(0, 11, field)
            b.const(1, 1)
            b.invoke("enabled", (0, 1))
        b.zero(15, "failed")
        b.label("start")
        b.get(0, 11, "history")
        b.invoke("to_string", (0,), result=1)
        b.create(0, ARRAY, "array_string", (1,))
        b.create(1, JSON, "json_ctor")
        b.string(2, "role")
        b.string(3, "user")
        b.invoke("json_put", (1, 2, 3))
        b.string(2, "content")
        b.invoke("json_put", (1, 2, 13))
        b.invoke("array_put", (0, 1))
        b.create(1, ARRAY, "array_string", (14,))
        b.invoke("array_length", (1,), result=2)
        b.const(3, 0)
        b.label("outputs")
        b.compare(OP_IF_GE, 3, 2, "append")
        b.invoke("array_item", (1, 3), result=4)
        b.invoke("array_put", (0, 4))
        b.const(4, 1)
        b.asm.emit("int_binop", 0x90, 3, 3, 4, "add-int", size=2)
        b.jump("outputs")
        b.label("append")
        b.put(0, 11, "history")
        b.get(0, 11, "transcript")
        b.string(1, "You\n")
        b.invoke("append_text", (0, 1))
        b.invoke("append_text", (0, 13))
        b.string(1, "\n\nAnpyra\n")
        b.invoke("append_text", (0, 1))
        b.invoke("append_text", (0, 12))
        b.string(1, "\n\n")
        b.invoke("append_text", (0, 1))
        if self.scroll:
            b.const(0, 1)
            b.put(0, 11, "scroll_pending")
            b.get(0, 11, "scroll")
            b.invoke("scroll_layout", (0,))
        b.get(0, 11, "message")
        b.string(1, "")
        b.invoke("set_text", (0, 1))
        b.get(0, 11, "status")
        b.string(1, "Reply received • ready")
        b.invoke("set_text", (0, 1))
        b.label("end")
        b.jump("done")
        b.label("catch")
        b.asm.emit("move_exception", 0, size=1)
        b.jump("failed")
        b.label("failed")
        b.get(0, 11, "status")
        b.invoke("set_text", (0, 12))
        b.label("done")
        b.asm.emit("return_void", size=1)
        return b.finish(("start", "end", "catch", EXCEPTION))

    def worker_run(self, pools):
        b = self.builder(pools, 16, 1, "worker_run")
        b.const(14, 0)
        b.label("start")
        b.string(1, ENDPOINT)
        b.create(0, "Ljava/net/URL;", "url_ctor", (1,))
        b.invoke("url_open", (0,), result=0)
        b.asm.emit("check_cast", 0, pools.types[HTTP], HTTP, size=2)
        b.asm.emit("move_object", 14, 0, size=2)
        b.string(1, "POST")
        b.invoke("http_method", (14, 1))
        b.const(1, 15000)
        b.invoke("http_connect_timeout", (14, 1))
        b.const(1, 90000)
        b.invoke("http_read_timeout", (14, 1))
        b.const(1, 1)
        b.invoke("http_output_flag", (14, 1))
        b.string(1, "Content-Type")
        b.string(2, "application/json")
        b.invoke("http_header", (14, 1, 2))
        b.create(7, BUILDER, "builder_ctor")
        b.string(5, "Bearer ")
        b.invoke("builder_append", (7, 5))
        b.get(6, 15, "w_key")
        b.invoke("builder_append", (7, 6))
        b.invoke("builder_text", (7,), result=7)
        b.string(5, "Authorization")
        b.invoke("http_header", (14, 5, 7))
        b.create(2, JSON, "json_ctor")
        b.get(6, 15, "w_history")
        b.create(3, ARRAY, "array_string", (6,))
        b.create(4, JSON, "json_ctor")
        b.string(5, "role")
        b.string(6, "user")
        b.invoke("json_put", (4, 5, 6))
        b.string(5, "content")
        b.get(6, 15, "w_message")
        b.invoke("json_put", (4, 5, 6))
        b.invoke("array_put", (3, 4))
        b.string(5, "input")
        b.invoke("json_put", (2, 5, 3))
        b.string(5, "model")
        b.string(6, self.binding.model)
        b.invoke("json_put", (2, 5, 6))
        b.string(5, "store")
        field = self.fields["false"]
        b.asm.emit("sget_object", 6, pools.fields[field], field.name, size=2)
        b.invoke("json_put", (2, 5, 6))
        b.create(12, JSON, "json_ctor")
        b.string(5, "effort")
        b.string(6, "none")
        b.invoke("json_put", (12, 5, 6))
        b.string(5, "reasoning")
        b.invoke("json_put", (2, 5, 12))
        b.create(12, ARRAY, "array_ctor")
        b.string(6, "reasoning.encrypted_content")
        b.invoke("array_put", (12, 6))
        b.string(5, "include")
        b.invoke("json_put", (2, 5, 12))
        b.const(6, 1500)
        b.invoke("integer", (6,), static=True, result=6)
        b.string(5, "max_output_tokens")
        b.invoke("json_put", (2, 5, 6))
        b.invoke("to_string", (2,), result=9)
        b.string(5, "UTF-8")
        b.invoke("utf8_bytes", (9, 5), result=9)
        b.invoke("http_output", (14,), result=8)
        b.invoke("write_bytes", (8, 9))
        b.invoke("close_output", (8,))
        b.invoke("http_code", (14,), result=10)
        b.const(11, 200)
        b.compare(OP_IF_LT, 10, 11, "http_error")
        b.const(11, 300)
        b.compare(OP_IF_GE, 10, 11, "http_error")
        b.invoke("http_input", (14,), result=2)
        b.string(5, "UTF-8")
        b.create(3, "Ljava/io/InputStreamReader;", "reader_ctor", (2, 5))
        b.create(5, "Ljava/io/BufferedReader;", "buffer_ctor", (3,))
        b.create(3, BUILDER, "builder_ctor")
        b.label("read")
        b.invoke("read_line", (5,), result=6)
        b.zero(6, "read_done")
        b.invoke("builder_append", (3, 6))
        b.jump("read")
        b.label("read_done")
        b.invoke("close_reader", (5,))
        b.invoke("http_disconnect", (14,))
        b.const(14, 0)
        b.invoke("builder_text", (3,), result=3)
        b.create(4, JSON, "json_string", (3,))
        b.string(5, "status")
        b.invoke("json_text", (4, 5), result=6)
        b.string(5, "completed")
        b.invoke("equals", (6, 5), result=6)
        b.zero(6, "incomplete")
        b.string(5, "output")
        b.invoke("json_array", (4, 5), result=2)
        b.zero(2, "no_text")
        b.create(3, BUILDER, "builder_ctor")
        b.invoke("array_length", (2,), result=6)
        b.const(5, 0)
        b.label("output_loop")
        b.compare(OP_IF_GE, 5, 6, "parsed")
        b.invoke("array_item", (2, 5), result=7)
        b.string(11, "content")
        b.invoke("json_array", (7, 11), result=8)
        b.zero(8, "next_output")
        b.invoke("array_length", (8,), result=9)
        b.const(10, 0)
        b.label("content_loop")
        b.compare(OP_IF_GE, 10, 9, "next_output")
        b.invoke("array_item", (8, 10), result=12)
        b.string(11, "type")
        b.invoke("json_text", (12, 11), result=13)
        b.string(11, "output_text")
        b.invoke("equals", (13, 11), result=7)
        b.zero(7, "check_refusal")
        b.string(11, "text")
        b.invoke("json_text", (12, 11), result=13)
        b.invoke("builder_append", (3, 13))
        b.jump("next_content")
        b.label("check_refusal")
        b.string(11, "refusal")
        b.invoke("equals", (13, 11), result=7)
        b.zero(7, "next_content")
        b.invoke("json_text", (12, 11), result=13)
        b.invoke("builder_append", (3, 13))
        b.label("next_content")
        b.const(11, 1)
        b.asm.emit("int_binop", 0x90, 10, 10, 11, "add-int", size=2)
        b.jump("content_loop")
        b.label("next_output")
        b.const(11, 1)
        b.asm.emit("int_binop", 0x90, 5, 5, 11, "add-int", size=2)
        b.jump("output_loop")
        b.label("parsed")
        b.invoke("builder_text", (3,), result=3)
        b.invoke("empty", (3,), result=1)
        b.zero(1, "success")
        b.label("no_text")
        b.string(3, "The model did not return text. Try a shorter request.")
        b.string(2, "[]")
        b.const(1, 0)
        b.jump("dispatch")
        b.label("success")
        b.invoke("to_string", (2,), result=2)
        b.const(1, 1)
        b.jump("dispatch")
        b.label("incomplete")
        b.string(3, "Response was incomplete. Try a shorter message.")
        b.string(2, "[]")
        b.const(1, 0)
        b.jump("dispatch")
        b.label("http_error")
        b.invoke("http_disconnect", (14,))
        b.const(14, 0)
        b.string(3, "The API request failed. Check your key/model and try again.")
        for code, label, text in (
            (401, "auth", "Authentication failed. Check or renew your temporary key."),
            (403, "auth", "Authentication failed. Check or renew your temporary key."),
            (404, "model", "This model is unavailable for your key."),
            (429, "limit", "Rate limit or quota reached. Please try again later."),
        ):
            b.const(11, code)
            b.compare(OP_IF_NE, 10, 11, "skip_" + str(code))
            b.string(3, text)
            b.jump("error_done")
            b.label("skip_" + str(code))
        b.label("error_done")
        b.string(2, "[]")
        b.const(1, 0)
        b.label("end")
        b.jump("dispatch")
        b.label("catch")
        b.asm.emit("move_exception", 0, size=1)
        b.zero(14, "network_message")
        b.invoke("http_disconnect", (14,))
        b.label("network_message")
        b.string(3, "Network request failed. Check internet and try again.")
        b.string(2, "[]")
        b.const(1, 0)
        b.label("dispatch")
        b.get(4, 15, "w_activity")
        b.create(0, self.delivery, "delivery_ctor", (4,))
        b.put(3, 0, "d_text")
        b.put(2, 0, "d_output")
        b.put(1, 0, "d_ok")
        b.get(5, 15, "w_message")
        b.put(5, 0, "d_pending")
        b.invoke("ui_post", (4, 0))
        b.asm.emit("return_void", size=1)
        return b.finish(("start", "end", "catch", EXCEPTION))


def emit_chat_binding(
    op,
    asm,
    registers,
    this_register,
    methods,
    midx,
    fidx,
    argument_base,
    class_descriptor,
    scroll_symbol=None,
):
    if not isinstance(op, BindChatSession):
        return False
    asm.emit("move_object", 1, this_register, size=2)
    if scroll_symbol:
        asm.emit("move_object", 0, registers[scroll_symbol], size=2)
        field = FieldKey(class_descriptor, "chat_scroll", SCROLL)
        asm.emit("iput_object", 0, 1, fidx[field], field.name, size=2)
    for alias, name in (
        ("key", op.key_input),
        ("message", op.message_input),
        ("transcript", op.transcript),
        ("status", op.status),
        ("send", op.send_button),
        ("clear", op.clear_button),
    ):
        descriptor = (
            EDIT
            if alias in {"key", "message"}
            else "Landroid/widget/Button;"
            if alias in {"send", "clear"}
            else TEXT
        )
        field = FieldKey(class_descriptor, "chat_" + alias, descriptor)
        asm.emit("move_object", 0, registers[name], size=2)
        asm.emit("iput_object", 0, 1, fidx[field], field.name, size=2)
    key = methods["init_chat"]
    emit_invoke(
        asm, OP_INVOKE_VIRTUAL, midx[key], (this_register,), (key.owner,), argument_base, "initChat"
    )
    key = methods["click_bind"]
    for name in (op.send_button, op.clear_button):
        emit_invoke(
            asm,
            OP_INVOKE_VIRTUAL,
            midx[key],
            (registers[name], this_register),
            (key.owner, *key.parameters),
            argument_base,
            "View.setOnClickListener",
        )
    return True


def build_chat_dex(app):
    operations = tuple(_walk_ops(app.operations))
    bindings = [op for op in operations if isinstance(op, BindChatSession)]
    if len(bindings) != 1:
        raise ValueError("chat apps require exactly one ChatSession")
    plan = ChatPlan(app, bindings[0])
    fields = (
        set(background_fields(operations))
        | button_fields(operations)
        | textview_fields(operations)
        | set(plan.fields.values())
    )
    strings = {op.value for op in operations if isinstance(op, LoadConst) and op.type_name == "str"}
    strings.update(
        op.image_asset
        for op in operations
        if isinstance(op, ApplyScreenBackground) and op.image_asset is not None
    )
    strings.update(button_strings(operations))
    strings.update(textview_strings(operations))
    strings.update(layout_strings(operations))
    strings.update(plan.literals)
    helper_keys = {
        fn.name: MethodKey(app.class_descriptor, fn.name, "I", tuple("I" for _ in fn.parameters))
        for fn in app.functions
    }
    generated = {}

    def lifecycle(pools, which):
        if not generated:
            generated["methods"] = generate_methods(
                app,
                pools.types,
                pools.strings,
                pools.methods,
                helper_keys,
                plan.refs,
                pools.fields,
                chat_scroll=plan.scroll,
            )
        return getattr(generated["methods"], which)

    ui_methods = [
        MethodDefinition(
            plan.refs["app_constructor"], 0x10001, lambda p: lifecycle(p, "constructor_code"), True
        ),
        MethodDefinition(plan.refs["app_on_create"], 4, lambda p: lifecycle(p, "lifecycle_code")),
        MethodDefinition(plan.refs["init_chat"], 1, plan.init),
        MethodDefinition(plan.refs["on_click"], 1, plan.click),
        MethodDefinition(plan.refs["on_reply"], 1, plan.reply),
    ]
    if plan.scroll:
        ui_methods.append(MethodDefinition(plan.refs["scroll_run"], 1, plan.scroll_run))
    for key in helper_keys.values():

        def helper(pools, key=key):
            lifecycle(pools, "constructor_code")
            return next(row[2] for row in generated["methods"].helper_codes if row[0] == key)

        ui_methods.append(MethodDefinition(key, 9, helper, True))
    classes = [
        ClassDefinition(
            plan.main,
            ACTIVITY_TYPE,
            tuple(ui_methods),
            tuple((field, 2) for field in plan.fields.values() if field.owner == plan.main),
            (LISTENER, GLOBAL_LAYOUT) if plan.scroll else (LISTENER,),
        ),
        ClassDefinition(
            plan.worker,
            OBJECT,
            (
                MethodDefinition(plan.refs["worker_ctor"], 0x10001, plan.worker_constructor, True),
                MethodDefinition(plan.refs["worker_run"], 1, plan.worker_run),
            ),
            tuple((field, 2) for field in plan.fields.values() if field.owner == plan.worker),
            (RUNNABLE,),
        ),
        ClassDefinition(
            plan.delivery,
            OBJECT,
            (
                MethodDefinition(
                    plan.refs["delivery_ctor"], 0x10001, plan.delivery_constructor, True
                ),
                MethodDefinition(plan.refs["delivery_run"], 1, plan.delivery_run),
            ),
            tuple((field, 1) for field in plan.fields.values() if field.owner == plan.delivery),
            (RUNNABLE,),
        ),
    ]
    data = write_classes(
        classes, (*plan.refs.values(), *helper_keys.values()), fields, strings, (EXCEPTION,)
    )
    methods = generated["methods"]
    callbacks = tuple(
        MethodListing(
            f"{key.owner}->{key.name}",
            tuple(
                (
                    "this" if index == 0 else f"arg{index}",
                    typ,
                    builder.registers - builder.inputs + index,
                )
                for index, typ in enumerate((key.owner, *key.parameters))
            ),
            builder.code_units,
            builder.assembly_listing,
        )
        for key, builder in plan.builders
    )
    return DexBuild(
        data,
        methods.register_map,
        methods.code_units,
        methods.assembly_listing,
        (*methods.listings, *callbacks),
    )
