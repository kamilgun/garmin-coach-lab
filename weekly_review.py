import json
import os
import tempfile

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


def write_text_atomic(path, content):
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)

    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=directory,
            prefix=".tmp_weekly_review_",
            suffix=".md",
            delete=False,
        ) as temporary_file:
            temporary_file.write(content)
            temporary_file.write("\n")
            temporary_path = temporary_file.name

        os.replace(temporary_path, path)
    except Exception:
        if temporary_path and os.path.exists(temporary_path):
            os.remove(temporary_path)
        raise


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

    write_text_atomic(OUTPUT_PATH, review)

    print(review)
    print(f"\nMarkdown yazıldı: {OUTPUT_PATH}")

    if weekly_plan is None:
        print(
            "[WARN] data/weekly_plan.json bulunamadı; "
            "review fallback davranışıyla üretildi."
        )


if __name__ == "__main__":
    main()
