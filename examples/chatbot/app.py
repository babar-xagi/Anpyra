from anpyra import Activity
from anpyra.components import (
    Background,
    Border,
    Button,
    ButtonStyle,
    ChatSession,
    Column,
    Font,
    Row,
    Screen,
    ScrollView,
    TextInput,
    TextView,
)


class MainActivity(Activity):
    def on_create(self, state):
        screen = Screen(self)
        screen.bg.color = "#0b1220"
        page = Column(self)
        page.set_padding(18)
        title = TextView(self, text="Anpyra Chat")
        title.style.color = "#f1f5f9"
        title.style.size = 28
        title.style.font = Font(family="sans-serif", bold=True)
        title.style.padding = (0, 0, 4, 0)
        title.style.keep_screen_on = True
        page.add(title)
        subtitle = TextView(self, text="Native Python → Android • GPT-5.5")
        subtitle.style.color = "#94a3b8"
        subtitle.style.size = 12
        page.add(subtitle, margin=(0, 0, 12, 0))
        key_input = TextInput(
            self, hint="Temporary OpenAI API key", password=True, hint_color="#94a3b8"
        )
        key_input.style.color = "#f1f5f9"
        key_input.style.size = 14
        key_input.style.background_color = "#18253b"
        key_input.style.padding = 12
        page.add(key_input, height=48, margin=(0, 0, 10, 0))
        scroll = ScrollView(self)
        transcript = TextView(
            self, text="Welcome! Enter your temporary key, then ask anything.\n\n"
        )
        transcript.style.color = "#e2e8f0"
        transcript.style.size = 16
        transcript.style.padding = 14
        transcript.style.line_spacing = (6, 1.1)
        transcript.style.selectable = True
        transcript.style.background_color = "#111d30"
        scroll.set_content(transcript)
        page.add(scroll, height=0, weight=1, margin=(0, 0, 8, 0))
        status = TextView(self, text="Ready • key stays in memory")
        status.style.color = "#7dd3fc"
        status.style.size = 12
        page.add(status, margin=(0, 0, 8, 0))
        message_input = TextInput(self, hint="Type your message…", hint_color="#94a3b8")
        message_input.style.color = "#f1f5f9"
        message_input.style.size = 16
        message_input.style.max_lines = 3
        message_input.style.background_color = "#18253b"
        message_input.style.padding = 12
        page.add(message_input, height=72, margin=(0, 0, 10, 0))
        controls = Row(self)
        send_button = Button(self, text="Send message")
        send_button.style = ButtonStyle(
            color="#042f2e",
            size=15,
            all_caps=False,
            bg=Background(color="#2dd4bf"),
            corner_radius=12,
            padding=8,
            ripple_color="#50ffffff",
            min_width=0,
            min_height=0,
        )
        clear_button = Button(self, text="New chat")
        clear_button.style = ButtonStyle(
            color="#cbd5e1",
            size=15,
            all_caps=False,
            bg=Background(color="#18253b"),
            border=Border("#334155"),
            corner_radius=12,
            padding=8,
            min_width=0,
            min_height=0,
        )
        controls.add(send_button, width=0, height=52, weight=2, margin=(0, 8, 0, 0))
        controls.add(clear_button, width=0, height=52, weight=1)
        page.add(controls)
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
        screen.set_content(page)
        self.set_content_view(screen)
