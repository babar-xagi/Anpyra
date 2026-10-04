from pyandroid import Activity, TextView


class MainActivity(Activity):
    def on_create(self, state):
        name: str = "Babar"
        age: int = 23
        score: int = 80
        bonus: int = 5
        final_score: int = score + bonus

        title = TextView(self)

        if age >= 18:
            if final_score >= 90:
                title.set_text("Excellent")
            elif final_score >= 70:
                title.set_text(name)
            else:
                title.set_text("Keep learning")
        else:
            title.set_text("Minor")

        self.set_content_view(title)
