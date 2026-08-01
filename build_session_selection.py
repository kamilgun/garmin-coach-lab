import json
import os

from coach_engine.planning.session_selection import select_sessions


COACH_CONTEXT_PATH = os.path.join("data", "coach_context.json")
CANDIDATES_PATH = os.path.join("data", "session_candidates.json")
OUTPUT_PATH = os.path.join("data", "session_selection.json")


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def main():
    missing = [
        path
        for path in (COACH_CONTEXT_PATH, CANDIDATES_PATH)
        if not os.path.exists(path)
    ]

    if missing:
        raise FileNotFoundError(
            "Gerekli artifact bulunamadı: "
            + ", ".join(missing)
            + ". Önce build_coach_context.py ve "
            "build_session_candidates.py çalıştır."
        )

    coach_context = load_json(COACH_CONTEXT_PATH)
    candidate_artifact = load_json(CANDIDATES_PATH)

    selection = select_sessions(
        coach_context,
        candidate_artifact,
    )

    write_json(OUTPUT_PATH, selection)

    print(json.dumps(selection, ensure_ascii=False, indent=2))
    print(f"\nSession selection yazıldı: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
