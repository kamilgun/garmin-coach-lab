import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from coach_engine.workspace import (
    build_profile_runtime_env,
    get_profile_workspace,
)


REPO_ROOT = Path(__file__).resolve().parent

ACTIVITY_SAMPLE = (
    REPO_ROOT
    / "data"
    / "samples"
    / "activity_summary.sample.json"
)

PERFORMANCE_SAMPLE = (
    REPO_ROOT
    / "data"
    / "samples"
    / "performance_summary.sample.json"
)

ATHLETE_PROFILE_EXAMPLE = (
    REPO_ROOT / "athlete_profile.example.json"
)

GENERATED_ARTIFACTS = [
    "coach_context.json",
    "session_candidates.json",
    "session_selection.json",
    "weekly_plan.json",
    "weekly_review.md",
    "llm_coach_prompt.md",
]


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def snapshot_tree(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    return {
        str(file_path.relative_to(path)): file_hash(file_path)
        for file_path in sorted(path.rglob("*"))
        if file_path.is_file()
    }


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def build_manual_context() -> dict:
    return {
        "schema_version": "2.0",
        "context_period": "this_week",
        "availability": {
            "available_days": [],
            "max_sessions": 3,
            "max_session_duration_min": 60,
            "running_available": True,
            "outdoor_bike_available": True,
            "indoor_trainer_available": True,
            "strength_available": True,
        },
        "recovery": {
            "sleep_quality": "good",
            "energy_level": "normal",
            "mental_fatigue": "low",
            "muscle_soreness": "none",
            "illness_status": "none",
        },
        "pain": {
            "active_pain": False,
            "pain_area": None,
            "pain_severity": 0,
            "pain_during_running": False,
            "pain_note": "",
        },
        "life_load": {
            "work_stress": "normal",
            "family_load": "normal",
            "caregiving_load": "low",
            "travel": False,
            "routine_disruption": "low",
            "time_pressure": "normal",
            "emotional_load": "normal",
        },
        "weekly_intent": "maintain_consistency",
        "user_note": "",
    }


def seed_workspace(workspace, athlete_name: str):
    workspace.ensure_directories()

    if not ACTIVITY_SAMPLE.exists():
        raise AssertionError(
            f"Activity sample bulunamadı: {ACTIVITY_SAMPLE}"
        )

    if not PERFORMANCE_SAMPLE.exists():
        raise AssertionError(
            f"Performance sample bulunamadı: {PERFORMANCE_SAMPLE}"
        )

    if not ATHLETE_PROFILE_EXAMPLE.exists():
        raise AssertionError(
            "athlete_profile.example.json bulunamadı."
        )

    athlete = json.loads(
        ATHLETE_PROFILE_EXAMPLE.read_text(
            encoding="utf-8"
        )
    )

    athlete["name"] = athlete_name

    write_json(
        workspace.athlete_profile_path,
        athlete,
    )

    workspace.activity_summary_path.write_bytes(
        ACTIVITY_SAMPLE.read_bytes()
    )

    workspace.performance_summary_path.write_bytes(
        PERFORMANCE_SAMPLE.read_bytes()
    )

    write_json(
        workspace.manual_context_path,
        build_manual_context(),
    )


def run_script(workspace, script_name: str):
    env = os.environ.copy()
    env.update(
        build_profile_runtime_env(workspace)
    )

    result = subprocess.run(
        [
            sys.executable,
            script_name,
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    if result.returncode != 0:
        raise AssertionError(
            f"{script_name} başarısız oldu.\n"
            f"exit={result.returncode}\n\n"
            f"STDOUT:\n{result.stdout}\n\n"
            f"STDERR:\n{result.stderr}"
        )


def run_deterministic_profile_pipeline(workspace):
    scripts = [
        "build_coach_context.py",
        "build_weekly_plan.py",
        "weekly_review.py",
        "generate_llm_prompt.py",
    ]

    for script_name in scripts:
        run_script(
            workspace,
            script_name,
        )


def assert_expected_artifacts(workspace):
    missing = [
        artifact_name
        for artifact_name in GENERATED_ARTIFACTS
        if not (
            workspace.data_dir
            / artifact_name
        ).exists()
    ]

    if missing:
        raise AssertionError(
            "Eksik artifact'ler: "
            + ", ".join(missing)
        )


def assert_profile_identity(
    workspace,
    expected_name: str,
):
    coach_context = json.loads(
        workspace.coach_context_path.read_text(
            encoding="utf-8"
        )
    )

    actual_name = (
        coach_context
        .get("athlete", {})
        .get("name")
    )

    if actual_name != expected_name:
        raise AssertionError(
            "Profile identity karıştı. "
            f"Beklenen={expected_name!r}, "
            f"gelen={actual_name!r}"
        )


def run_tests():
    print("Profile Isolation Tests")
    print("=======================")

    with tempfile.TemporaryDirectory(
        prefix="garmin-coach-isolation-"
    ) as temp_dir:
        temp_root = Path(temp_dir)

        private_root = (
            temp_root / "private"
        )

        alpha = get_profile_workspace(
            "isolation_alpha",
            repo_root=temp_root,
            private_root=private_root,
        )

        beta = get_profile_workspace(
            "isolation_beta",
            repo_root=temp_root,
            private_root=private_root,
        )

        assert (
            alpha.data_dir
            != beta.data_dir
        )

        assert (
            alpha.garmin_tokenstore
            != beta.garmin_tokenstore
        )

        seed_workspace(
            alpha,
            "Isolation Alpha",
        )

        seed_workspace(
            beta,
            "Isolation Beta",
        )

        # -------------------------------------------------
        # A -> B isolation
        # -------------------------------------------------

        beta_before = snapshot_tree(
            beta.profile_dir
        )

        run_deterministic_profile_pipeline(
            alpha
        )

        beta_after = snapshot_tree(
            beta.profile_dir
        )

        assert beta_before == beta_after, (
            "Alpha pipeline çalışırken "
            "Beta workspace değişti."
        )

        assert_expected_artifacts(alpha)

        assert_profile_identity(
            alpha,
            "Isolation Alpha",
        )

        print(
            "[PASS] Alpha pipeline "
            "Beta workspace'e dokunmadı."
        )

        # -------------------------------------------------
        # B -> A isolation
        # -------------------------------------------------

        alpha_before = snapshot_tree(
            alpha.profile_dir
        )

        run_deterministic_profile_pipeline(
            beta
        )

        alpha_after = snapshot_tree(
            alpha.profile_dir
        )

        assert alpha_before == alpha_after, (
            "Beta pipeline çalışırken "
            "Alpha workspace değişti."
        )

        assert_expected_artifacts(beta)

        assert_profile_identity(
            beta,
            "Isolation Beta",
        )

        print(
            "[PASS] Beta pipeline "
            "Alpha workspace'e dokunmadı."
        )

        # -------------------------------------------------
        # Final identity checks
        # -------------------------------------------------

        assert_profile_identity(
            alpha,
            "Isolation Alpha",
        )

        assert_profile_identity(
            beta,
            "Isolation Beta",
        )

        print(
            "[PASS] Profile identity "
            "artifact'lerde korundu."
        )

    print()
    print(
        "All profile isolation tests passed."
    )


if __name__ == "__main__":
    run_tests()
