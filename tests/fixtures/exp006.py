from pyandroid import Activity, TextView


class MainActivity(Activity):
    def on_create(self, state):
        name: str = "Babar"
        age: int = 23
        active: bool = True

        title = TextView(self)

        if active:
            title.set_text(name)
        else:
            title.set_text("Inactive")

        self.set_content_view(title)
