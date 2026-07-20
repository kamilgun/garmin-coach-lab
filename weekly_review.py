from coach_engine.reporting.weekly_markdown import render_weekly_review

import json
import os


def load_coach_context():
    path = "data/coach_context.json"

    if not os.path.exists(path):
        raise FileNotFoundError(
            "data/coach_context.json bulunamadı. "
            "Önce python build_coach_context.py çalıştır."
        )

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    coach_context = load_coach_context()
    review = render_weekly_review(coach_context)

    print(review)

    with open("data/weekly_review.md", "w", encoding="utf-8") as f:
        f.write(review)

    print("\nMarkdown yazıldı: data/weekly_review.md")


if __name__ == "__main__":
    main()