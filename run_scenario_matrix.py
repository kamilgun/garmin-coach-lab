import json
import os
import shutil
from datetime import datetime

from build_coach_context import build_coach_context


DATA_DIR = "data"
SAMPLES_DIR = os.path.join(DATA_DIR, "samples")
SCENARIO_MATRIX_PATH = os.path.join("scenarios", "scenario_matrix.json")
SUMMARY_PATH = os.path.join(DATA_DIR, "scenario_matrix_summary.md")

FILES_TO_BACKUP = [
    os.path.join(DATA_DIR, "activity_summary.json"),
    os.path.join(DATA_DIR, "performance_summary.json"),
    os.path.join(DATA_DIR, "manual_context.json"),
]


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def backup_files():
    backups = {}

    for path in FILES_TO_BACKUP:
        if os.path.exists(path):
            backup_path = path + ".bak"
            shutil.copy2(path, backup_path)
            backups[path] = backup_path
        else:
            backups[path] = None

    return backups


def restore_files(backups):
    for path, backup_path in backups.items():
        if backup_path and os.path.exists(backup_path):
            shutil.copy2(backup_path, path)
            os.remove(backup_path)
        elif os.path.exists(path):
            os.remove(path)


def prepare_sample_inputs():
    os.makedirs(DATA_DIR, exist_ok=True)

    shutil.copy2(
        os.path.join(SAMPLES_DIR, "activity_summary.sample.json"),
        os.path.join(DATA_DIR, "activity_summary.json"),
    )

    shutil.copy2(
        os.path.join(SAMPLES_DIR, "performance_summary.sample.json"),
        os.path.join(DATA_DIR, "performance_summary.json"),
    )


def compare_expected(actual, expected):
    failures = []

    for key, expected_value in expected.items():
        actual_value = actual.get(key)

        if actual_value != expected_value:
            failures.append(
                {
                    "key": key,
                    "expected": expected_value,
                    "actual": actual_value,
                }
            )

    return failures


def write_summary(results):
    lines = [
        "# Scenario Matrix Summary",
        "",
        f"Generated at: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "| Scenario | Status | Notes |",
        "|---|---|---|",
    ]

    for result in results:
        if result["status"] == "PASS":
            notes = "-"
        else:
            notes = "; ".join(
                f"{failure['key']}: expected={failure['expected']}, actual={failure['actual']}"
                for failure in result["failures"]
            )

        lines.append(
            f"| {result['name']} | {result['status']} | {notes} |"
        )

    with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    scenarios = load_json(SCENARIO_MATRIX_PATH)

    backups = backup_files()
    results = []

    try:
        prepare_sample_inputs()

        for scenario in scenarios:
            name = scenario["name"]
            manual_context = scenario["manual_context"]
            expected = scenario["expected"]

            write_json(
                os.path.join(DATA_DIR, "manual_context.json"),
                manual_context,
            )

            coach_context = build_coach_context()
            final_decision = coach_context["final_decision"]

            failures = compare_expected(final_decision, expected)

            status = "PASS" if not failures else "FAIL"

            results.append(
                {
                    "name": name,
                    "status": status,
                    "failures": failures,
                    "final_decision": final_decision,
                }
            )

            print(f"{name}: {status}")

            if failures:
                for failure in failures:
                    print(
                        f"  - {failure['key']}: "
                        f"expected={failure['expected']} "
                        f"actual={failure['actual']}"
                    )

        write_summary(results)

        failed_count = sum(1 for result in results if result["status"] == "FAIL")

        print(f"\nScenario summary yazıldı: {SUMMARY_PATH}")

        if failed_count:
            raise SystemExit(f"{failed_count} scenario failed.")

        print("All scenarios passed.")

    finally:
        restore_files(backups)


if __name__ == "__main__":
    main()