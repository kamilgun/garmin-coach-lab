from coach_engine.narration.llm_prompt import build_llm_coach_prompt
from coach_engine.narration.llm_client import generate_text

import json
import os
import sys


def configure_stdout():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")


def load_coach_context():
    path = "data/coach_context.json"

    if not os.path.exists(path):
        raise FileNotFoundError(
            "data/coach_context.json bulunamadı. "
            "Önce python build_coach_context.py çalıştır."
        )

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def main():
    configure_stdout()

    coach_context = load_coach_context()
    prompt = build_llm_coach_prompt(coach_context)

    write_text("data/llm_coach_prompt.md", prompt)

    coach_message = generate_text(prompt)

    write_text("data/coach_message.md", coach_message)

    print(coach_message)
    print("\nCoach message yazıldı: data/coach_message.md")


if __name__ == "__main__":
    main()