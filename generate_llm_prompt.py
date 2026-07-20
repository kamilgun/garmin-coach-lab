from coach_engine.narration.llm_prompt import build_llm_coach_prompt

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


def write_prompt(prompt):
    path = "data/llm_coach_prompt.md"

    with open(path, "w", encoding="utf-8") as f:
        f.write(prompt)

    return path


def main():
    coach_context = load_coach_context()
    prompt = build_llm_coach_prompt(coach_context)

    output_path = write_prompt(prompt)

    print(prompt)
    print(f"\nLLM coach prompt yazıldı: {output_path}")


if __name__ == "__main__":
    main()