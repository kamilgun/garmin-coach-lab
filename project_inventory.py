from __future__ import annotations

import argparse
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Iterable


IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".idea",
    ".vscode",
    ".agents",
    ".claude",
    "node_modules",
}

PRIVATE_OR_GENERATED_EXACT = {
    ".env",
    "athlete_profile.json",
    "data/activity_summary.json",
    "data/performance_summary.json",
    "data/manual_context.json",
    "data/coach_context.json",
    "data/session_candidates.json",
    "data/session_selection.json",
    "data/weekly_plan.json",
    "data/feedback_log.jsonl",
    "data/weekly_review.md",
    "data/llm_coach_prompt.md",
    "data/coach_message.md",
}

DUPLICATE_MARKERS = (
    "(1)",
    "(2)",
    "(3)",
    "_old",
    "_clean",
    "_updated",
    "_copy",
    " copy",
)

ROOT_SCRIPT_GROUPS = {
    "data_ingestion": {
        "activity_metrics.py",
        "performance_metrics.py",
    },
    "context_decision": {
        "build_coach_context.py",
        "update_manual_context.py",
    },
    "planning": {
        "build_session_candidates.py",
        "build_session_selection.py",
        "build_weekly_plan.py",
    },
    "reporting_narration": {
        "weekly_review.py",
        "generate_llm_prompt.py",
        "generate_coach_message.py",
    },
    "orchestration": {
        "run_pipeline.py",
    },
}


def run_git(root: Path, *args: str) -> list[str] | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            check=True,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None

    return [line for line in result.stdout.splitlines() if line.strip()]


def iter_repo_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue

        relative = path.relative_to(root)

        if any(part in IGNORED_DIRS for part in relative.parts):
            continue

        yield relative


def tree_lines(files: list[Path]) -> list[str]:
    tree: dict[str, dict] = {}

    for path in files:
        node = tree
        for part in path.parts:
            node = node.setdefault(part, {})

    lines: list[str] = []

    def walk(node: dict[str, dict], prefix: str = "") -> None:
        items = sorted(
            node.items(),
            key=lambda item: (bool(item[1]), item[0].lower()),
        )

        for index, (name, children) in enumerate(items):
            is_last = index == len(items) - 1
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{name}")

            if children:
                extension = "    " if is_last else "│   "
                walk(children, prefix + extension)

    walk(tree)
    return lines


def classify_root_scripts(files: list[Path]) -> dict[str, list[str]]:
    root_scripts = {
        path.name
        for path in files
        if len(path.parts) == 1 and path.suffix == ".py"
    }

    classified: dict[str, list[str]] = {}
    used: set[str] = set()

    for group, names in ROOT_SCRIPT_GROUPS.items():
        matches = sorted(root_scripts & names)
        classified[group] = matches
        used.update(matches)

    classified["tests_and_scenarios"] = sorted(
        name
        for name in root_scripts
        if (
            name.startswith("test_")
            or (
                name.startswith("run_")
                and ("test" in name or "scenario" in name)
            )
        )
        and name not in used
    )
    used.update(classified["tests_and_scenarios"])

    classified["other_root_scripts"] = sorted(root_scripts - used)

    return classified


def markdown_list(values: list[str], empty: str = "_None_") -> list[str]:
    return [f"- `{value}`" for value in values] if values else [empty]


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Garmin Coach Lab repository inventory and consolidation "
            "signals report."
        )
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root. Default: current directory.",
    )
    parser.add_argument(
        "--output",
        default="docs/PROJECT_INVENTORY.md",
        help="Markdown output path relative to repository root.",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    output_path = root / args.output

    files = list(iter_repo_files(root))
    tracked = run_git(root, "ls-files")
    git_status = run_git(root, "status", "--short")

    tracked_set = set(tracked or [])
    all_strings = [path.as_posix() for path in files]

    suffix_counts = Counter(
        path.suffix.lower() if path.suffix else "<no extension>"
        for path in files
    )

    duplicate_like = sorted(
        path
        for path in all_strings
        if any(marker in path.lower() for marker in DUPLICATE_MARKERS)
    )

    private_present = sorted(
        path for path in PRIVATE_OR_GENERATED_EXACT if path in all_strings
    )
    private_tracked = sorted(
        path for path in PRIVATE_OR_GENERATED_EXACT if path in tracked_set
    )

    test_scripts = sorted(
        path
        for path in all_strings
        if (
            path.startswith("tests/")
            or (
                path.endswith(".py")
                and (
                    "test" in Path(path).name.lower()
                    or "scenario" in Path(path).name.lower()
                )
            )
        )
    )

    package_files = sorted(
        path for path in all_strings if path.startswith("coach_engine/")
    )
    data_files = sorted(
        path for path in all_strings if path.startswith("data/")
    )
    scenario_files = sorted(
        path for path in all_strings if path.startswith("scenarios/")
    )
    docs_files = sorted(
        path for path in all_strings if path.startswith("docs/")
    )

    root_script_groups = classify_root_scripts(files)

    lines = [
        "# Garmin Coach Lab — Project Inventory",
        "",
        f"Generated at: `{datetime.now().isoformat(timespec='seconds')}`",
        f"Repository root: `{root}`",
        "",
        "## Summary",
        "",
        f"- Files scanned: **{len(files)}**",
        f"- Git-tracked files: **{len(tracked_set) if tracked is not None else 'unavailable'}**",
        f"- Root Python scripts: **{sum(len(v) for v in root_script_groups.values())}**",
        f"- `coach_engine/` files: **{len(package_files)}**",
        f"- Test/scenario files: **{len(test_scripts)}**",
        f"- Data files present: **{len(data_files)}**",
        "",
        "## Repository Tree",
        "",
        "```text",
        root.name + "/",
        *tree_lines(files),
        "```",
        "",
        "## Root Script Classification",
        "",
    ]

    group_labels = {
        "data_ingestion": "Data ingestion and metrics",
        "context_decision": "Context and decision",
        "planning": "Planning",
        "reporting_narration": "Reporting and narration",
        "orchestration": "Orchestration",
        "tests_and_scenarios": "Tests and scenario runners",
        "other_root_scripts": "Other root scripts",
    }

    for group, values in root_script_groups.items():
        lines.append(f"### {group_labels[group]}")
        lines.extend(markdown_list(values))
        lines.append("")

    lines.extend(
        [
            "## Package Modules",
            "",
            *markdown_list(package_files),
            "",
            "## Tests and Scenario Assets",
            "",
            *markdown_list(test_scripts),
            "",
            "## Scenario Files",
            "",
            *markdown_list(scenario_files),
            "",
            "## Documentation Files",
            "",
            *markdown_list(docs_files),
            "",
            "## Data Artifacts Present",
            "",
            *markdown_list(data_files),
            "",
            "## File Extension Counts",
            "",
        ]
    )

    for suffix, count in sorted(suffix_counts.items()):
        lines.append(f"- `{suffix}`: {count}")

    lines.extend(
        [
            "",
            "## Consolidation Signals",
            "",
            "### Duplicate-looking filenames",
            "",
            *markdown_list(duplicate_like),
            "",
            "### Private or generated artifacts present",
            "",
            *markdown_list(private_present),
            "",
            "### Private or generated artifacts tracked by Git",
            "",
        ]
    )

    if tracked is None:
        lines.append("_Git information unavailable._")
    else:
        lines.extend(markdown_list(private_tracked))

    lines.extend(["", "### Git working tree", ""])

    if git_status is None:
        lines.append("_Git status unavailable._")
    elif not git_status:
        lines.append("_Clean working tree._")
    else:
        lines.append("```text")
        lines.extend(git_status)
        lines.append("```")

    lines.extend(
        [
            "",
            "## Recommended Artifact Roles",
            "",
            "### Source and input",
            "- `athlete_profile.json` — local athlete profile",
            "- `data/activity_summary.json` — Garmin activity serving artifact",
            "- `data/performance_summary.json` — performance serving artifact",
            "- `data/manual_context.json` — weekly check-in",
            "",
            "### Decision serving",
            "- `data/coach_context.json` — deterministic decision contract",
            "",
            "### Planning debug and lineage",
            "- `data/session_candidates.json`",
            "- `data/session_selection.json`",
            "",
            "### Planning serving",
            "- `data/weekly_plan.json` — deterministic execution contract",
            "",
            "### Presentation",
            "- `data/weekly_review.md`",
            "- `data/llm_coach_prompt.md`",
            "- `data/coach_message.md`",
            "",
            "## 8.1A Exit Checklist",
            "",
            "- [ ] Repository tree reviewed",
            "- [ ] Root scripts classified",
            "- [ ] Generated/private files verified against `.gitignore`",
            "- [ ] Duplicate or obsolete files identified",
            "- [ ] Public serving artifacts distinguished from debug artifacts",
            "- [ ] README gaps listed",
            "- [ ] Phase 8.1B README update scope approved",
            "",
        ]
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"Inventory written: {output_path}")
    print(f"Files scanned: {len(files)}")

    if private_tracked:
        print("[WARN] Private/generated artifacts tracked by Git:")
        for path in private_tracked:
            print(f"  - {path}")

    if duplicate_like:
        print("[INFO] Duplicate-looking filenames found:")
        for path in duplicate_like:
            print(f"  - {path}")


if __name__ == "__main__":
    main()
