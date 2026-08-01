from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime
import json
import os
import re
from typing import Any, Dict, Iterable, List

from coach_engine.planning.session_candidates import (
    build_session_candidates,
)
from coach_engine.planning.session_selection import select_sessions
from coach_engine.planning.scheduling import schedule_weekly_plan


DEFAULT_MATRIX_PATH = os.path.join(
    "scenarios",
    "weekly_plan_scenario_matrix.json",
)
DEFAULT_SUMMARY_PATH = os.path.join(
    "data",
    "weekly_plan_scenario_summary.md",
)

PATH_TOKEN_PATTERN = re.compile(r"([^\.\[\]]+)|\[(\d+)\]")


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def deep_merge(base: Any, override: Any) -> Any:
    if isinstance(base, dict) and isinstance(override, dict):
        merged = deepcopy(base)

        for key, value in override.items():
            if key in merged:
                merged[key] = deep_merge(merged[key], value)
            else:
                merged[key] = deepcopy(value)

        return merged

    return deepcopy(override)


def parse_path(path: str) -> List[Any]:
    tokens: List[Any] = []

    for name, index in PATH_TOKEN_PATTERN.findall(path):
        if name:
            tokens.append(name)
        else:
            tokens.append(int(index))

    return tokens


def get_by_path(data: Any, path: str) -> Any:
    current = data

    for token in parse_path(path):
        if isinstance(token, int):
            if not isinstance(current, list):
                raise KeyError(
                    f"{path}: list beklenirken {type(current).__name__} bulundu."
                )
            current = current[token]
        else:
            if not isinstance(current, dict) or token not in current:
                raise KeyError(f"{path}: '{token}' bulunamadı.")
            current = current[token]

    return current


def remove_by_path(data: Dict[str, Any], path: str) -> None:
    tokens = parse_path(path)

    if not tokens:
        return

    current: Any = data

    for token in tokens[:-1]:
        if isinstance(token, int):
            if not isinstance(current, list) or token >= len(current):
                return
            current = current[token]
        else:
            if not isinstance(current, dict) or token not in current:
                return
            current = current[token]

    final_token = tokens[-1]

    if isinstance(final_token, int):
        if isinstance(current, list) and final_token < len(current):
            current.pop(final_token)
    elif isinstance(current, dict):
        current.pop(final_token, None)


def partial_dict_match(actual: Any, expected: Dict[str, Any]) -> bool:
    if not isinstance(actual, dict):
        return False

    for key, expected_value in expected.items():
        if key not in actual or actual[key] != expected_value:
            return False

    return True


def compare_expected(
    bundle: Dict[str, Any],
    scenario: Dict[str, Any],
) -> List[Dict[str, Any]]:
    failures: List[Dict[str, Any]] = []

    for path, expected in scenario.get("expected_equals", {}).items():
        try:
            actual = get_by_path(bundle, path)
        except (KeyError, IndexError) as exc:
            failures.append(
                {
                    "assertion": "equals",
                    "path": path,
                    "expected": expected,
                    "actual": f"<missing: {exc}>",
                }
            )
            continue

        if actual != expected:
            failures.append(
                {
                    "assertion": "equals",
                    "path": path,
                    "expected": expected,
                    "actual": actual,
                }
            )

    for assertion in scenario.get("expected_list_contains", []):
        path = assertion["path"]
        expected_match = assertion["match"]

        try:
            actual_list = get_by_path(bundle, path)
        except (KeyError, IndexError) as exc:
            failures.append(
                {
                    "assertion": "list_contains",
                    "path": path,
                    "expected": expected_match,
                    "actual": f"<missing: {exc}>",
                }
            )
            continue

        matched = (
            isinstance(actual_list, list)
            and any(
                partial_dict_match(item, expected_match)
                for item in actual_list
            )
        )

        if not matched:
            failures.append(
                {
                    "assertion": "list_contains",
                    "path": path,
                    "expected": expected_match,
                    "actual": actual_list,
                }
            )

    return failures


def run_scenario(
    scenario: Dict[str, Any],
    defaults: Dict[str, Any],
) -> Dict[str, Any]:
    coach_context = deep_merge(
        defaults.get("coach_context", {}),
        scenario.get("coach_context", {}),
    )

    for path in scenario.get("remove_paths", []):
        remove_by_path(coach_context, path)

    start_date = scenario.get(
        "start_date",
        defaults.get("start_date"),
    )

    candidate = build_session_candidates(coach_context)
    selection = select_sessions(coach_context, candidate)
    plan = schedule_weekly_plan(
        selection,
        start_date=start_date,
    )

    bundle = {
        "candidate": candidate,
        "selection": selection,
        "plan": plan,
    }
    failures = compare_expected(bundle, scenario)

    return {
        "name": scenario["name"],
        "description": scenario.get("description", ""),
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "bundle": bundle,
    }


def markdown_escape(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def write_summary(
    path: str,
    results: Iterable[Dict[str, Any]],
    matrix_path: str,
) -> None:
    results = list(results)
    passed = sum(result["status"] == "PASS" for result in results)
    failed = len(results) - passed

    lines = [
        "# Weekly Plan Scenario Matrix Summary",
        "",
        f"Generated at: {datetime.now().isoformat(timespec='seconds')}",
        f"Matrix: `{matrix_path}`",
        "",
        f"- Total: {len(results)}",
        f"- Passed: {passed}",
        f"- Failed: {failed}",
        "",
        "| Scenario | Status | Notes |",
        "|---|---|---|",
    ]

    for result in results:
        if result["status"] == "PASS":
            notes = result.get("description") or "-"
        else:
            notes = "; ".join(
                (
                    f"{failure['path']} "
                    f"expected={markdown_escape(failure['expected'])}, "
                    f"actual={markdown_escape(failure['actual'])}"
                )
                for failure in result["failures"]
            )

        lines.append(
            f"| {result['name']} | {result['status']} | "
            f"{markdown_escape(notes)} |"
        )

    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Phase 8 weekly planning chain scenario matrix'i çalıştırır."
        )
    )
    parser.add_argument(
        "--matrix",
        default=DEFAULT_MATRIX_PATH,
        help="Scenario matrix JSON yolu.",
    )
    parser.add_argument(
        "--summary",
        default=DEFAULT_SUMMARY_PATH,
        help="Markdown summary çıktı yolu.",
    )
    parser.add_argument(
        "--scenario",
        help="Yalnızca adı verilen scenario'yu çalıştır.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Başarısız assertion ayrıntılarını yazdır.",
    )
    args, _unknown = parser.parse_known_args()

    matrix = load_json(args.matrix)
    defaults = matrix.get("defaults", {})
    scenarios = matrix.get("scenarios", [])

    if args.scenario:
        scenarios = [
            scenario
            for scenario in scenarios
            if scenario.get("name") == args.scenario
        ]

        if not scenarios:
            raise SystemExit(
                f"Scenario bulunamadı: {args.scenario}"
            )

    results = []

    for scenario in scenarios:
        result = run_scenario(scenario, defaults)
        results.append(result)
        print(f"{result['name']}: {result['status']}")

        if args.verbose and result["failures"]:
            for failure in result["failures"]:
                print(
                    f"  - {failure['path']}: "
                    f"expected={failure['expected']!r}, "
                    f"actual={failure['actual']!r}"
                )

    write_summary(
        args.summary,
        results,
        args.matrix,
    )

    failed = [
        result
        for result in results
        if result["status"] == "FAIL"
    ]

    print(f"\nSummary yazıldı: {args.summary}")
    print(
        f"Result: {len(results) - len(failed)}/{len(results)} PASS"
    )

    if failed:
        raise SystemExit(
            f"{len(failed)} weekly plan scenario failed."
        )

    print("All weekly plan scenarios passed.")


if __name__ == "__main__":
    main()
