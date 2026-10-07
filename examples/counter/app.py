from anpyra import Activity, State
from anpyra.components import (
    Background,
    Border,
    Button,
    ButtonStyle,
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
        self.count: int = State(0, persist=True)
        self.name: str = State("", persist=True)
        self.paused: bool = False
        screen = Screen(self)
        screen.bg.color = "#0b1220"
        page = Column(self)
        page.set_padding(18)
        title = TextView(self, text="Counter Lab")
        title.style.color = "#f1f5f9"
        title.style.size = 28
        title.style.font = Font(family="sans-serif", bold=True)
        title.style.keep_screen_on = True
        page.add(title, margin=(0, 0, 8, 0))
        subtitle = TextView(self, text="Python callbacks • Native Android state")
        subtitle.style.color = "#94a3b8"
        subtitle.style.size = 12
        page.add(subtitle, margin=(0, 0, 24, 0))
        number = TextView(self, text="0")
        number.style.color = "#2dd4bf"
        number.style.content_description = "counter-value"
        number.style.size = 64
        number.style.alignment = "center"
        number.style.padding = 12
        number.style.background_color = "#111d30"
        page.add(number, height=120, margin=(0, 0, 12, 0))
        self.number = number
        controls = Row(self)
        minus = Button(self, text="−")
        minus.style = ButtonStyle(
            color="#e2e8f0",
            size=24,
            all_caps=False,
            bg=Background(color="#18253b"),
            corner_radius=12,
            min_width=0,
            min_height=0,
        )
        plus = Button(self, text="+")
        plus.style = ButtonStyle(
            color="#042f2e",
            size=24,
            all_caps=False,
            bg=Background(color="#2dd4bf"),
            corner_radius=12,
            min_width=0,
            min_height=0,
        )
        reset = Button(self, text="Reset")
        reset.style = ButtonStyle(
            color="#e2e8f0",
            size=15,
            all_caps=False,
            bg=Background(color="#18253b"),
            corner_radius=12,
            min_width=0,
            min_height=0,
        )
        controls.add(minus, width=0, height=52, weight=1, margin=(0, 8, 0, 0))
        controls.add(plus, width=0, height=52, weight=1, margin=(0, 8, 0, 0))
        controls.add(reset, width=0, height=52, weight=1)
        page.add(controls, margin=(0, 0, 12, 0))
        self.plus = plus
        self.minus = minus
        plus.on_click(self.increment)
        minus.on_click(self.decrement)
        reset.on_click(self.reset_count)
        status = TextView(self, text="Ready")
        status.style.color = "#7dd3fc"
        status.style.content_description = "counter-status"
        status.style.size = 14
        page.add(status, margin=(0, 0, 24, 0))
        self.status = status
        entry = TextInput(self, hint="Enter your name", hint_color="#94a3b8")
        entry.style.color = "#f1f5f9"
        entry.style.content_description = "name-input"
        entry.style.size = 16
        entry.style.padding = 12
        entry.style.single_line = True
        entry.style.background_color = "#18253b"
        page.add(entry, height=52, margin=(0, 0, 10, 0))
        self.entry = entry
        preview = TextView(self, text="Your name preview appears here")
        preview.style.color = "#e2e8f0"
        preview.style.content_description = "name-preview"
        preview.style.size = 18
        preview.style.padding = 12
        page.add(preview, margin=(0, 0, 10, 0))
        self.preview = preview
        actions = Row(self)
        show = Button(self, text="Show name")
        show.style = ButtonStyle(
            color="#e2e8f0",
            size=14,
            all_caps=False,
            bg=Background(color="#18253b"),
            border=Border("#334155"),
            corner_radius=12,
            min_width=0,
            min_height=0,
        )
        pause = Button(self, text="Pause")
        pause.style = ButtonStyle(
            color="#e2e8f0",
            size=14,
            all_caps=False,
            bg=Background(color="#18253b"),
            border=Border("#334155"),
            corner_radius=12,
            min_width=0,
            min_height=0,
        )
        actions.add(show, width=0, height=52, weight=1, margin=(0, 8, 0, 0))
        actions.add(pause, width=0, height=52, weight=1)
        page.add(actions, margin=(0, 0, 10, 0))
        self.pause = pause
        show.on_click(self.show_name)
        pause.on_click(self.toggle_pause)
        recreate = Button(self, text="Recreate screen • restore count/name")
        recreate.style = ButtonStyle(
            color="#94a3b8",
            size=12,
            all_caps=False,
            bg=Background(color="#111d30"),
            corner_radius=12,
            min_width=0,
            min_height=0,
        )
        page.add(recreate, height=48)
        recreate.on_click(self.recreate_screen)
        scroll = ScrollView(self)
        scroll.set_content(page)
        screen.set_content(scroll)
        self.set_content_view(screen)
        self.restore_input()
        self.refresh()

    def increment(self):
        if not self.paused:
            self.count += 1
        self.refresh()

    def decrement(self):
        if not self.paused:
            self.count -= 1
        self.refresh()

    def reset_count(self):
        self.count = 0
        self.refresh()

    def toggle_pause(self):
        self.paused = not self.paused
        self.refresh()

    def show_name(self):
        self.name = self.entry.get_text()
        self.refresh()

    def restore_input(self):
        self.entry.set_text(self.name)

    def refresh(self):
        self.number.text = str(self.count)
        self.status.set_text("Paused: " + str(self.paused))
        self.plus.set_enabled(not self.paused)
        self.minus.set_enabled(not self.paused)
        if self.paused:
            self.pause.set_text("Resume")
        else:
            self.pause.set_text("Pause")
        if self.name:
            self.preview.set_text("Hello, " + self.name + "!")
        else:
            self.preview.set_text("Your name preview appears here")

    def recreate_screen(self):
        self.recreate()
