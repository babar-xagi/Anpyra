from anpyra import Activity
from anpyra.components import (
    Background,
    Border,
    Button,
    ButtonState,
    ButtonStyle,
    Font,
    Icon,
    Screen,
)


class MainActivity(Activity):
    def on_create(self, state):
        screen = Screen(self)
        screen.bg.color = "#142033"
        button = Button(self, text="Continue")
        button.style = ButtonStyle(
            color="white",
            size=18,
            font=Font(family="sans-serif", bold=True),
            all_caps=False,
            width=260,
            height=64,
            placement="center",
            padding=(12, 20),
            bg=Background(color="#2563eb"),
            border=Border("#93c5fd", width=2),
            corner_radius=16,
            pressed=ButtonState(bg=Background(color="#1e40af")),
            disabled=ButtonState(color="#94a3b8", bg=Background(color="#334155")),
            ripple_color="#50ffffff",
            icon=Icon("assets/arrow.png", size=24, position="end", tint="white"),
            icon_gap=12,
            elevation=4,
            content_description="Continue button",
        )
        screen.set_content(button)
        self.set_content_view(screen)
