from pyandroid import Activity, TextView


class MainActivity(Activity):
    def on_create(self, state):
        title = TextView(self)
        title.set_text("Hello from real Python source!")
        self.set_content_view(title)
