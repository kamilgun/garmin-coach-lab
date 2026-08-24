import json
from pathlib import Path

from coach_engine.planning.session_candidates import (
    build_session_candidates,
)
from coach_engine.workspace import get_runtime_workspace


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path, data):
    path = Path(path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )

def main():
    runtime = get_runtime_workspace()

    if not runtime.coach_context_path.exists():
        raise FileNotFoundError(
            f"{runtime.coach_context_path} bulunamadı. "
            "Önce build_coach_context.py çalıştır."
        )

    coach_context = load_json(
        runtime.coach_context_path
    )

    candidates = build_session_candidates(
        coach_context
    )

    write_json(
        runtime.session_candidates_path,
        candidates,
    )

    print(
        json.dumps(
            candidates,
            ensure_ascii=False,
            indent=2,
        )
    )

    print(
        "\nSession candidates yazıldı: "
        f"{runtime.session_candidates_path}"
    )


if __name__ == "__main__":
    main()
