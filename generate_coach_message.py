import json
import os
import sys

from coach_engine.narration.llm_client import generate_text
from coach_engine.narration.llm_prompt import build_llm_coach_prompt
from coach_engine.workspace import get_runtime_workspace

def configure_stdout():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")


def load_json(path, required=False):
    if not os.path.exists(path):
        if required:
            raise FileNotFoundError(
                f"{path} bulunamadı."
            )
        return None

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def main():
    configure_stdout()

    runtime = get_runtime_workspace()

    coach_context = load_json(
        runtime.coach_context_path,
        required=True,
    )

    weekly_plan = load_json(
        runtime.weekly_plan_path,
        required=False,
    )

    prompt = build_llm_coach_prompt(
        coach_context,
        weekly_plan=weekly_plan,
    )

    write_text(
        runtime.llm_coach_prompt_path,
        prompt,
    )

    coach_message = generate_text(prompt)

    write_text(
        runtime.coach_message_path,
        coach_message,
    )

    print(coach_message)

    print(
        f"\nCoach message yazıldı: "
        f"{runtime.coach_message_path}"
    )

    if weekly_plan is None:
        print(
            f"[WARN] {runtime.weekly_plan_path} bulunamadı; "
            "coach message kesin plan ayrıntıları olmadan üretildi."
        )

if __name__ == "__main__":
    main()