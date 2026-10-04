from anpyra import Activity, TextView


class MainActivity(Activity):
    def on_create(self, state):
        title = TextView(self)
        title.set_text("Hello from Anpyra!")
        self.set_content_view(title)
