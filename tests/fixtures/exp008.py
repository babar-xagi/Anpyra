from pyandroid import Activity, TextView


def calculate_score(score: int, bonus: int) -> int:
    return score + bonus


class MainActivity(Activity):
    def on_create(self, state):
        score: int = 80
        bonus: int = 5
        final_score: int = calculate_score(score, bonus)

        title = TextView(self)

        if final_score >= 70:
            title.set_text("Passed from Python function!")
        else:
            title.set_text("Failed")

        self.set_content_view(title)
