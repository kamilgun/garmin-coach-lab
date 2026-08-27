from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Sequence


TEST_SUITE_VERSION = "0.2.0"
DEFAULT_PIPELINE_START_DATE = "2026-07-31"
DEFAULT_SUMMARY_PATH = Path("data") / "test_suite_summary.md"


@dataclass(frozen=True)
class TestStep:
    step_id: str
    name: str
    command: tuple[str, ...]
    category: str


@dataclass
class TestResult:
    step: TestStep
    status: str
    return_code: int | None
    duration_seconds: float
    stdout: str = ""
    stderr: str = ""
    detail: str = ""


class WorkspaceSnapshot:
    """
    Test suite'in local runtime artifact'lerini kalıcı olarak değiştirmesini
    engeller.

    Korunan alanlar:
    - data/
    - athlete_profile.json

    Test sonunda, başarılı veya başarısız olmasına bakılmadan eski durum geri
    yüklenir.
    """

    def __init__(
        self,
        repo_root: Path,
        *,
        enabled: bool = True,
    ) -> None:
        self.repo_root = repo_root
        self.enabled = enabled
        self._temporary_directory: tempfile.TemporaryDirectory[str] | None = None
        self._backup_root: Path | None = None
        self._data_existed = False
        self._profile_existed = False

    def __enter__(self) -> "WorkspaceSnapshot":
        if not self.enabled:
            return self

        self._temporary_directory = tempfile.TemporaryDirectory(
            prefix="garmin_coach_test_snapshot_"
        )
        self._backup_root = Path(self._temporary_directory.name)

        data_path = self.repo_root / "data"
        profile_path = self.repo_root / "athlete_profile.json"

        self._data_existed = data_path.exists()
        self._profile_existed = profile_path.exists()

        if self._data_existed:
            shutil.copytree(
                data_path,
                self._backup_root / "data",
            )

        if self._profile_existed:
            shutil.copy2(
                profile_path,
                self._backup_root / "athlete_profile.json",
            )

        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        if not self.enabled:
            return

        assert self._backup_root is not None
        assert self._temporary_directory is not None

        data_path = self.repo_root / "data"
        profile_path = self.repo_root / "athlete_profile.json"

        if data_path.exists():
            shutil.rmtree(data_path)

        if self._data_existed:
            shutil.copytree(
                self._backup_root / "data",
                data_path,
            )

        if profile_path.exists():
            profile_path.unlink()

        if self._profile_existed:
            shutil.copy2(
                self._backup_root / "athlete_profile.json",
                profile_path,
            )

        self._temporary_directory.cleanup()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Garmin Coach Lab deterministic test ve smoke-test "
            "runner'larını tek komutta çalıştırır."
        )
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help=(
            "Başarılı adımların stdout/stderr çıktısını da gösterir. "
            "Hatalı adımların çıktısı her zaman gösterilir."
        ),
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="İlk başarısız adımda suite'i durdurur.",
    )
    parser.add_argument(
        "--skip-pipeline",
        action="store_true",
        help="Deterministic pipeline smoke testini atlar.",
    )
    parser.add_argument(
        "--keep-artifacts",
        action="store_true",
        help=(
            "Testlerden sonra data/ ve athlete_profile.json durumunu "
            "geri yüklemez. Normal kullanımda önerilmez."
        ),
    )
    parser.add_argument(
        "--pipeline-start-date",
        default=DEFAULT_PIPELINE_START_DATE,
        help=(
            "Pipeline smoke test için YYYY-MM-DD başlangıç tarihi. "
            f"Default: {DEFAULT_PIPELINE_START_DATE}"
        ),
    )
    parser.add_argument(
        "--summary-path",
        default=str(DEFAULT_SUMMARY_PATH),
        help=(
            "Markdown test özeti yolu. Boş string verilirse dosya yazılmaz. "
            f"Default: {DEFAULT_SUMMARY_PATH.as_posix()}"
        ),
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Çalıştırılacak adımları listeler ve çıkar.",
    )
    return parser.parse_args()


def build_steps(
    *,
    python_executable: str,
    skip_pipeline: bool,
    pipeline_start_date: str,
) -> list[TestStep]:
    steps = [
        TestStep(
            step_id="context_scenarios",
            name="Context Scenario Matrix",
            command=(
                python_executable,
                "run_scenario_matrix.py",
            ),
            category="scenario",
        ),
        TestStep(
            step_id="weekly_dose",
            name="Weekly Dose Tests",
            command=(
                python_executable,
                "run_weekly_dose_tests.py",
            ),
            category="unit",
        ),
        TestStep(
            step_id="session_candidates",
            name="Session Candidate Tests",
            command=(
                python_executable,
                "run_session_candidate_tests.py",
            ),
            category="unit",
        ),
        TestStep(
            step_id="session_selection",
            name="Session Selection Tests",
            command=(
                python_executable,
                "run_session_selection_tests.py",
            ),
            category="unit",
        ),
        TestStep(
            step_id="weekly_scheduling",
            name="Weekly Scheduling Tests",
            command=(
                python_executable,
                "run_weekly_scheduling_tests.py",
            ),
            category="unit",
        ),
        TestStep(
            step_id="weekly_plan_builder",
            name="Weekly Plan Builder Tests",
            command=(
                python_executable,
                "run_weekly_plan_builder_tests.py",
            ),
            category="integration",
        ),
        TestStep(
            step_id="weekly_plan_scenarios",
            name="Weekly Plan Scenario Matrix",
            command=(
                python_executable,
                "run_weekly_plan_scenario_matrix.py",
            ),
            category="scenario",
        ),
        TestStep(
            step_id="weekly_plan_view_model",
            name="Weekly Plan View-Model Tests",
            command=(
                python_executable,
                "run_weekly_plan_view_tests.py",
            ),
            category="presentation",
        ),
        TestStep(
            step_id="product_ui_structure",
            name="Product UI Structure Tests",
            command=(
                python_executable,
                "run_product_ui_structure_tests.py",
            ),
            category="presentation",
        ),
        TestStep(
            step_id="weekly_review_reporting",
            name="Weekly Review Reporting Tests",
            command=(
                python_executable,
                "run_weekly_review_tests.py",
            ),
            category="reporting",
        ),
        TestStep(
            step_id="weekly_plan_propagation",
            name="Weekly Plan Propagation Tests",
            command=(
                python_executable,
                "run_weekly_plan_propagation_tests.py",
            ),
            category="integration",
        ),
        TestStep(
            step_id="artifact_contracts",
            name="Artifact Contract Tests",
            command=(
                python_executable,
                "run_artifact_contract_tests.py",
            ),
            category="contract",
        ),
        TestStep(
            step_id="profile_isolation",
            name="Profile Isolation Tests",
            command=(
                python_executable,
                "run_profile_isolation_tests.py",
            ),
            category="integration",
        ),
    ]

    if not skip_pipeline:
        steps.append(
            TestStep(
                step_id="pipeline_smoke",
                name="Deterministic Pipeline Smoke Test",
                command=(
                    python_executable,
                    "run_pipeline.py",
                    "--skip-garmin",
                    "--skip-llm",
                    "--plan-start-date",
                    pipeline_start_date,
                ),
                category="smoke",
            )
        )

    return steps


def command_text(command: Sequence[str]) -> str:
    return subprocess.list2cmdline(list(command))


def ensure_script_exists(
    repo_root: Path,
    step: TestStep,
) -> str | None:
    if len(step.command) < 2:
        return "Geçersiz test komutu."

    script_path = repo_root / step.command[1]

    if not script_path.exists():
        return f"Gerekli script bulunamadı: {script_path}"

    return None


def copy_if_missing(
    source: Path,
    destination: Path,
) -> None:
    if destination.exists():
        return

    if not source.exists():
        raise FileNotFoundError(
            f"Smoke test girdisi bulunamadı: {source}"
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def prepare_pipeline_smoke_inputs(repo_root: Path) -> None:
    """
    Public clone üzerinde private runtime dosyaları yoksa sample/example
    girdilerinden geçici smoke-test girdileri oluşturur.

    WorkspaceSnapshot normal kullanımda bunları test sonunda geri kaldırır.
    """

    copy_if_missing(
        repo_root / "data" / "samples" / "activity_summary.sample.json",
        repo_root / "data" / "activity_summary.json",
    )
    copy_if_missing(
        repo_root / "data" / "samples" / "performance_summary.sample.json",
        repo_root / "data" / "performance_summary.json",
    )
    copy_if_missing(
        repo_root / "data" / "samples" / "manual_context.sample.json",
        repo_root / "data" / "manual_context.json",
    )
    copy_if_missing(
        repo_root / "athlete_profile.example.json",
        repo_root / "athlete_profile.json",
    )


def run_step(
    repo_root: Path,
    step: TestStep,
    *,
    verbose: bool,
) -> TestResult:
    missing_error = ensure_script_exists(repo_root, step)

    if missing_error:
        return TestResult(
            step=step,
            status="FAIL",
            return_code=None,
            duration_seconds=0.0,
            detail=missing_error,
        )

    if step.step_id == "pipeline_smoke":
        try:
            prepare_pipeline_smoke_inputs(repo_root)
        except Exception as exc:
            return TestResult(
                step=step,
                status="FAIL",
                return_code=None,
                duration_seconds=0.0,
                detail=str(exc),
            )

    environment = os.environ.copy()
    environment["PYTHONIOENCODING"] = "utf-8"
    environment["PYTHONUTF8"] = "1"

    existing_pythonpath = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = (
        str(repo_root)
        if not existing_pythonpath
        else os.pathsep.join([str(repo_root), existing_pythonpath])
    )

    started = time.perf_counter()

    try:
        completed = subprocess.run(
            list(step.command),
            cwd=repo_root,
            env=environment,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        duration = time.perf_counter() - started
        return TestResult(
            step=step,
            status="FAIL",
            return_code=None,
            duration_seconds=duration,
            detail=f"Process başlatılamadı: {exc}",
        )

    duration = time.perf_counter() - started
    status = "PASS" if completed.returncode == 0 else "FAIL"

    result = TestResult(
        step=step,
        status=status,
        return_code=completed.returncode,
        duration_seconds=duration,
        stdout=completed.stdout or "",
        stderr=completed.stderr or "",
    )

    if verbose or status == "FAIL":
        print_step_output(result)

    return result


def print_step_output(result: TestResult) -> None:
    if result.detail:
        print(f"\n  Detail:\n{indent(result.detail)}")

    if result.stdout.strip():
        print(f"\n  stdout:\n{indent(result.stdout.rstrip())}")

    if result.stderr.strip():
        print(f"\n  stderr:\n{indent(result.stderr.rstrip())}")


def indent(value: str, spaces: int = 4) -> str:
    prefix = " " * spaces
    return "\n".join(
        prefix + line
        for line in value.splitlines()
    )


def status_icon(status: str) -> str:
    return {
        "PASS": "[PASS]",
        "FAIL": "[FAIL]",
        "SKIP": "[SKIP]",
    }.get(status, f"[{status}]")


def print_header(
    repo_root: Path,
    steps: Sequence[TestStep],
    args: argparse.Namespace,
) -> None:
    print("\nGarmin Coach Lab Test Suite")
    print("===========================")
    print(f"Suite version: {TEST_SUITE_VERSION}")
    print(f"Python: {sys.executable}")
    print(f"Repository: {repo_root}")
    print(f"Steps: {len(steps)}")
    print(
        "Workspace restore: "
        + ("DISABLED" if args.keep_artifacts else "ENABLED")
    )
    print(
        "Pipeline smoke: "
        + ("SKIPPED" if args.skip_pipeline else "ENABLED")
    )

    if not args.skip_pipeline:
        print(
            "Pipeline plan start date: "
            f"{args.pipeline_start_date}"
        )


def print_step_start(
    index: int,
    total: int,
    step: TestStep,
) -> None:
    print(
        f"\n[{index}/{total}] {step.name}"
        f"  ({step.category})"
    )
    print(f"Command: {command_text(step.command)}")


def print_step_result(result: TestResult) -> None:
    return_code_text = (
        "-"
        if result.return_code is None
        else str(result.return_code)
    )
    print(
        f"{status_icon(result.status)} {result.step.name} "
        f"({result.duration_seconds:.2f}s, "
        f"exit={return_code_text})"
    )

    if result.detail and result.status == "FAIL":
        print(f"  {result.detail}")


def print_summary(
    results: Sequence[TestResult],
    total_duration: float,
) -> None:
    passed = sum(result.status == "PASS" for result in results)
    failed = sum(result.status == "FAIL" for result in results)
    skipped = sum(result.status == "SKIP" for result in results)

    print("\nTest Suite Summary")
    print("==================")

    for result in results:
        print(
            f"{status_icon(result.status):6} "
            f"{result.step.name:<38} "
            f"{result.duration_seconds:>7.2f}s"
        )

    print("")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Skipped: {skipped}")
    print(f"Duration: {total_duration:.2f}s")

    if failed:
        print("\nRESULT: FAILED")
    else:
        print("\nRESULT: PASSED")


def build_summary_markdown(
    results: Sequence[TestResult],
    *,
    repo_root: Path,
    total_duration: float,
    workspace_restored: bool,
) -> str:
    passed = sum(result.status == "PASS" for result in results)
    failed = sum(result.status == "FAIL" for result in results)
    skipped = sum(result.status == "SKIP" for result in results)

    lines = [
        "# Garmin Coach Lab — Test Suite Summary",
        "",
        f"- Generated at: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- Suite version: `{TEST_SUITE_VERSION}`",
        f"- Python: `{sys.executable}`",
        f"- Repository: `{repo_root}`",
        f"- Workspace restored: `{str(workspace_restored).lower()}`",
        f"- Total duration: `{total_duration:.2f}s`",
        "",
        "## Results",
        "",
        "| Status | Step | Category | Duration | Exit code |",
        "|---|---|---|---:|---:|",
    ]

    for result in results:
        exit_code = (
            "-"
            if result.return_code is None
            else str(result.return_code)
        )
        lines.append(
            f"| {result.status} | {result.step.name} | "
            f"{result.step.category} | "
            f"{result.duration_seconds:.2f}s | {exit_code} |"
        )

    lines.extend(
        [
            "",
            "## Totals",
            "",
            f"- Passed: **{passed}**",
            f"- Failed: **{failed}**",
            f"- Skipped: **{skipped}**",
            "",
            f"## Final Result: {'PASSED' if failed == 0 else 'FAILED'}",
            "",
        ]
    )

    if failed:
        lines.extend(
            [
                "## Failures",
                "",
            ]
        )

        for result in results:
            if result.status != "FAIL":
                continue

            lines.append(f"### {result.step.name}")
            lines.append("")
            lines.append(
                f"- Command: `{command_text(result.step.command)}`"
            )
            lines.append(
                f"- Exit code: `{result.return_code}`"
            )

            if result.detail:
                lines.append(f"- Detail: {result.detail}")

            lines.append("")

    return "\n".join(lines)


def write_summary(
    repo_root: Path,
    summary_path_value: str,
    content: str,
) -> Path | None:
    normalized = summary_path_value.strip()

    if not normalized:
        return None

    summary_path = Path(normalized)

    if not summary_path.is_absolute():
        summary_path = repo_root / summary_path

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        content + "\n",
        encoding="utf-8",
    )

    return summary_path


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parent
    python_executable = sys.executable

    steps = build_steps(
        python_executable=python_executable,
        skip_pipeline=args.skip_pipeline,
        pipeline_start_date=args.pipeline_start_date,
    )

    if args.list:
        print("Garmin Coach Lab test steps:")
        for index, step in enumerate(steps, start=1):
            print(
                f"{index}. {step.step_id}: {step.name} "
                f"[{step.category}]"
            )
            print(f"   {command_text(step.command)}")
        return 0

    print_header(repo_root, steps, args)

    results: list[TestResult] = []
    suite_started = time.perf_counter()
    interrupted = False

    try:
        with WorkspaceSnapshot(
            repo_root,
            enabled=not args.keep_artifacts,
        ):
            for index, step in enumerate(steps, start=1):
                print_step_start(index, len(steps), step)
                result = run_step(
                    repo_root,
                    step,
                    verbose=args.verbose,
                )
                results.append(result)
                print_step_result(result)

                if result.status == "FAIL" and args.fail_fast:
                    print("\nFail-fast enabled; suite durduruldu.")

                    for remaining_step in steps[index:]:
                        results.append(
                            TestResult(
                                step=remaining_step,
                                status="SKIP",
                                return_code=None,
                                duration_seconds=0.0,
                                detail="Fail-fast nedeniyle çalıştırılmadı.",
                            )
                        )

                    break
    except KeyboardInterrupt:
        interrupted = True
        print("\n[INTERRUPTED] Kullanıcı testi durdurdu.")
    finally:
        total_duration = time.perf_counter() - suite_started

    if interrupted:
        return 130

    print_summary(results, total_duration)

    summary_content = build_summary_markdown(
        results,
        repo_root=repo_root,
        total_duration=total_duration,
        workspace_restored=not args.keep_artifacts,
    )
    summary_path = write_summary(
        repo_root,
        args.summary_path,
        summary_content,
    )

    if summary_path is not None:
        print(f"\nSummary written: {summary_path}")

    has_failure = any(
        result.status == "FAIL"
        for result in results
    )

    return 1 if has_failure else 0


if __name__ == "__main__":
    raise SystemExit(main())
