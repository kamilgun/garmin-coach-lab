import json
import os

from coach_engine.reporting.weekly_markdown import render_weekly_review


COACH_CONTEXT_PATH = os.path.join("data", "coach_context.json")
WEEKLY_PLAN_PATH = os.path.join("data", "weekly_plan.json")
OUTPUT_PATH = os.path.join("data", "weekly_review.md")


def load_json(path, required=False):
    if not os.path.exists(path):
        if required:
            raise FileNotFoundError(f"{path} bulunamadı.")
        return None

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def write_text(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        file.write(content)
        file.write("\n")


def main():
    coach_context = load_json(
        COACH_CONTEXT_PATH,
        required=True,
    )
    weekly_plan = load_json(
        WEEKLY_PLAN_PATH,
        required=False,
    )

    review = render_weekly_review(
        coach_context,
        weekly_plan=weekly_plan,
    )

    write_text(OUTPUT_PATH, review)

    print(review)
    print(f"\nMarkdown yazıldı: {OUTPUT_PATH}")

    if weekly_plan is None:
        print(
            "[WARN] data/weekly_plan.json bulunamadı; "
            "review eski fallback davranışıyla üretildi."
        )


if __name__ == "__main__":
    main()
