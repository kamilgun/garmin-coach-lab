import json
import os

from coach_engine.planning.session_candidates import (
    build_session_candidates,
)


COACH_CONTEXT_PATH = os.path.join("data", "coach_context.json")
OUTPUT_PATH = os.path.join("data", "session_candidates.json")


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def main():
    if not os.path.exists(COACH_CONTEXT_PATH):
        raise FileNotFoundError(
            "data/coach_context.json bulunamadı. "
            "Önce build_coach_context.py çalıştır."
        )

    coach_context = load_json(COACH_CONTEXT_PATH)
    candidates = build_session_candidates(coach_context)

    write_json(OUTPUT_PATH, candidates)

    print(json.dumps(candidates, ensure_ascii=False, indent=2))
    print(f"\nSession candidates yazıldı: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
