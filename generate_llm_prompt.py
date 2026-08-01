import json
import os

from coach_engine.narration.llm_prompt import build_llm_coach_prompt


COACH_CONTEXT_PATH = os.path.join("data", "coach_context.json")
WEEKLY_PLAN_PATH = os.path.join("data", "weekly_plan.json")
OUTPUT_PATH = os.path.join("data", "llm_coach_prompt.md")


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

    prompt = build_llm_coach_prompt(
        coach_context,
        weekly_plan=weekly_plan,
    )

    write_text(OUTPUT_PATH, prompt)

    print(prompt)
    print(f"\nLLM coach prompt yazıldı: {OUTPUT_PATH}")

    if weekly_plan is None:
        print(
            "[WARN] data/weekly_plan.json bulunamadı; "
            "prompt kesin plan ayrıntıları olmadan üretildi."
        )


if __name__ == "__main__":
    main()
