import argparse
import json
import os
import tempfile
from pathlib import Path

from coach_engine.workspace import get_runtime_workspace

from coach_engine.planning.weekly_plan import (
    build_weekly_plan_bundle,
)



def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def write_json_atomic(path, data):
    path = Path(path)
    directory = path.parent

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

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


def print_summary(bundle, runtime):
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
    print(f"- {runtime.session_candidates_path}")
    print(f"- {runtime.session_selection_path}")
    print(f"- {runtime.weekly_plan_path}")


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
    runtime = get_runtime_workspace()

    if not runtime.coach_context_path.exists():
        raise FileNotFoundError(
            f"{runtime.coach_context_path} bulunamadı. "
            "Önce build_coach_context.py çalıştır."
        )

    coach_context = load_json(
        runtime.coach_context_path
    )
    bundle = build_weekly_plan_bundle(
        coach_context,
        start_date=args.start_date,
    )

    # Ara artifact'ler debug ve lineage için korunur.
    write_json_atomic(
        runtime.session_candidates_path,
        bundle["session_candidates"],
    )

    write_json_atomic(
        runtime.session_selection_path,
        bundle["session_selection"],
    )

    write_json_atomic(
        runtime.weekly_plan_path,
        bundle["weekly_plan"],
    )

    print_summary(
        bundle,
        runtime,
    )

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
