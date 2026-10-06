from anpyra import Activity
from anpyra.components import Font, Screen, Shadow, TextView


class MainActivity(Activity):
    def on_create(self, state):
        screen = Screen(self)
        screen.style.bg.color = "#142033"
        title = TextView(self, text="Anpyra Title\nNative Typography")
        title.style.color = "#F8CB62"
        title.style.size = 30
        title.style.font = Font(path="assets/AnpyraDemo.ttf", bold=True)
        title.style.alignment = "center"
        title.style.vertical_alignment = "center"
        title.style.width = "match_parent"
        title.style.height = "match_parent"
        title.style.padding = (20, 24)
        title.style.letter_spacing = 0.04
        title.style.line_spacing = (12, 1.1)
        title.style.include_font_padding = False
        title.style.shadow = Shadow("#80000000", radius=2, dx=1, dy=2)
        title.style.content_description = "Anpyra typography example"
        screen.set_content(title)
        self.set_content_view(screen)
