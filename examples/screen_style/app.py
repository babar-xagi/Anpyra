from anpyra import Activity, TextView
from anpyra.components import Gradient, Image, Screen


class MainActivity(Activity):
    def on_create(self, state):
        screen = Screen(self)
        screen.style.bg.color = "#102030"
        screen.style.bg.gradient = Gradient(["#0f766e", "#2563eb"], direction="tl_br")
        screen.style.bg.image = Image("assets/wallpaper.png", fit="contain", opacity=0.75)
        screen.style.bg.opacity = 1.0
        title = TextView(self)
        title.set_text("A native screen, styled from Python")
        title.set_text_color("white")
        screen.set_content(title)
        self.set_content_view(screen)
