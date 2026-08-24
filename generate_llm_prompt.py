import json
import os
from coach_engine.workspace import get_runtime_workspace
from coach_engine.narration.llm_prompt import build_llm_coach_prompt




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

    print(prompt)

    print(
        f"\nLLM coach prompt yazıldı: "
        f"{runtime.llm_coach_prompt_path}"
    )

    if weekly_plan is None:
        print(
            f"[WARN] {runtime.weekly_plan_path} bulunamadı; "
            "prompt kesin plan ayrıntıları olmadan üretildi."
        )


if __name__ == "__main__":
    main()
