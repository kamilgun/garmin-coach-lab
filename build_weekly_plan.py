import argparse
import json
import os
import tempfile

from coach_engine.planning.weekly_plan import (
    build_weekly_plan_bundle,
)


COACH_CONTEXT_PATH = os.path.join("data", "coach_context.json")
CANDIDATES_PATH = os.path.join("data", "session_candidates.json")
SELECTION_PATH = os.path.join("data", "session_selection.json")
WEEKLY_PLAN_PATH = os.path.join("data", "weekly_plan.json")


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def write_json_atomic(path, data):
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)

    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=directory,
            prefix=".tmp_weekly_plan_",
            suffix=".json",
            delete=False,
        ) as temporary_file:
            json.dump(
                data,
                temporary_file,
                ensure_ascii=False,
                indent=2,
            )
            temporary_file.write("\n")
            temporary_path = temporary_file.name

        os.replace(temporary_path, path)
    except Exception:
        if temporary_path and os.path.exists(temporary_path):
            os.remove(temporary_path)
        raise


def print_summary(bundle):
    candidates = bundle["session_candidates"]
    selection = bundle["session_selection"]
    weekly_plan = bundle["weekly_plan"]

    print("\nWeekly Plan Builder")
    print("===================")
    print(f"Planner version: {bundle['planner_version']}")
    print(f"Planning engine: {bundle['planning_engine']}")
    print(f"Candidate count: {candidates.get('candidate_count', 0)}")
    print(f"Selected sessions: {selection.get('session_count', 0)}")
    print(f"Plan status: {weekly_plan.get('plan_status')}")
    print(f"Scheduled sessions: {weekly_plan.get('scheduled_count', 0)}")
    print(f"Unscheduled sessions: {weekly_plan.get('unscheduled_count', 0)}")

    horizon = weekly_plan.get("planning_horizon") or {}
    if horizon:
        print(
            "Planning horizon: "
            f"{horizon.get('start_date')} -> {horizon.get('end_date')}"
        )

    print("\nArtifacts:")
    print(f"- {CANDIDATES_PATH}")
    print(f"- {SELECTION_PATH}")
    print(f"- {WEEKLY_PLAN_PATH}")


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Coach Context'ten session candidates, selection ve "
            "rolling 7-day weekly plan üretir."
        )
    )
    parser.add_argument(
        "--start-date",
        help=(
            "Test veya replay için YYYY-MM-DD başlangıç tarihi. "
            "Verilmezse local sistem tarihi kullanılır."
        ),
    )
    parser.add_argument(
        "--print-json",
        action="store_true",
        help="Final weekly_plan JSON'unu terminale de yazdırır.",
    )
    args = parser.parse_args()

    if not os.path.exists(COACH_CONTEXT_PATH):
        raise FileNotFoundError(
            "data/coach_context.json bulunamadı. "
            "Önce build_coach_context.py çalıştır."
        )

    coach_context = load_json(COACH_CONTEXT_PATH)
    bundle = build_weekly_plan_bundle(
        coach_context,
        start_date=args.start_date,
    )

    # Ara artifact'ler debug ve lineage için korunur.
    write_json_atomic(
        CANDIDATES_PATH,
        bundle["session_candidates"],
    )
    write_json_atomic(
        SELECTION_PATH,
        bundle["session_selection"],
    )
    write_json_atomic(
        WEEKLY_PLAN_PATH,
        bundle["weekly_plan"],
    )

    print_summary(bundle)

    if args.print_json:
        print("\nFinal weekly_plan.json:")
        print(
            json.dumps(
                bundle["weekly_plan"],
                ensure_ascii=False,
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
