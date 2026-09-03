import argparse
from datetime import date, datetime
import os
import subprocess
import sys
from pathlib import Path
from coach_engine.openai_config import (
    validate_openai_api_key,
)

from coach_engine.workspace import (
    build_profile_runtime_env,
    get_enabled_profiles,
    get_profile_workspace,
    get_runtime_workspace,
)


PIPELINE_VERSION = "0.9.0"


def configure_stdout():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")


def run_step(name, command, allow_fail=False):
    print(f"\n=== {name} ===")
    print("Komut:", " ".join(command))

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    try:
        subprocess.run(
            command,
            check=True,
            env=env,
        )
    except subprocess.CalledProcessError as error:
        if allow_fail:
            print(
                f"[WARN] {name} başarısız oldu ama pipeline devam ediyor."
            )
            print(f"[WARN] Exit code: {error.returncode}")
            return False

        print(f"[ERROR] {name} başarısız oldu.")
        print(f"[ERROR] Exit code: {error.returncode}")
        raise

    return True


def load_env_file_if_available():
    if not os.path.exists(".env"):
        print(".env file: NOT FOUND")
        return

    try:
        from dotenv import load_dotenv
    except ImportError:
        print(
            ".env file: FOUND, but python-dotenv is not installed"
        )
        return

    load_dotenv()
    print(".env file: LOADED")


def can_import(module_name):
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False


def parse_iso_date(value):
    try:
        date.fromisoformat(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "Tarih YYYY-MM-DD formatında olmalı."
        ) from error

    return value

def configure_profile_runtime(profile_id):
    if not profile_id:
        return get_runtime_workspace()

    enabled_profiles = {
        profile.profile_id: profile
        for profile in get_enabled_profiles()
    }

    if profile_id not in enabled_profiles:
        available = ", ".join(
            sorted(enabled_profiles.keys())
        ) or "(none)"

        raise RuntimeError(
            f"Profile '{profile_id}' bulunamadı veya aktif değil. "
            f"Aktif profiller: {available}"
        )

    workspace = get_profile_workspace(
        profile_id,
        repo_root=Path.cwd(),
    )

    workspace.ensure_directories()

    os.environ.update(
        build_profile_runtime_env(workspace)
    )

    return get_runtime_workspace()    


def check_required_paths(paths, errors):
    for path in paths:
        if not os.path.exists(path):
            errors.append(f"Gerekli dosya bulunamadı: {path}")


def preflight_check(args, python_executable, runtime,):
    print("\n=== Preflight Check ===")
    print(f"Pipeline version: {PIPELINE_VERSION}")
    print(f"Python executable: {python_executable}")
    print(f"Working directory: {os.getcwd()}")

    load_env_file_if_available()

    errors = []

    required_scripts = [
        "build_coach_context.py",
        "build_weekly_plan.py",
        "weekly_review.py",
        "generate_llm_prompt.py",
    ]

    if not args.skip_garmin:
        required_scripts.extend(
            [
                "activity_metrics.py",
                "performance_metrics.py",
            ]
        )
    else:
        check_required_paths(
            [runtime.activity_summary_path],
            errors,
        )

    if not args.skip_llm:
        required_scripts.append("generate_coach_message.py")

    check_required_paths(required_scripts, errors)

    if can_import("coach_engine.planning.weekly_plan"):
        print("weekly plan builder: OK")
    else:
        errors.append(
            "coach_engine.planning.weekly_plan import edilemedi. "
            "Planning dosyalarının doğru konumda olduğunu kontrol et."
        )

    if not args.skip_garmin:
        if can_import("garminconnect"):
            print("garminconnect: OK")
        else:
            errors.append(
                "garminconnect paketi bulunamadı. "
                "Çözüm: python -m pip install -r requirements.txt"
            )

    if not args.skip_llm:
        if can_import("openai"):
            print("openai: OK")
        else:
            errors.append(
                "openai paketi bulunamadı. "
                "Çözüm: python -m pip install -r requirements.txt"
            )

    api_key_valid, api_key_error = (
        validate_openai_api_key(
            os.getenv("OPENAI_API_KEY")
        )
    )

    if api_key_valid:
        print("OPENAI_API_KEY: OK")
    else:
        errors.append(
            (
                api_key_error
                or "OPENAI_API_KEY geçerli değil."
            )
            + " .env dosyasını veya environment "
            "variable değerini kontrol et."
        )

    if errors:
        error_message = "\n".join(
            f"- {error}" for error in errors
        )
        raise RuntimeError(
            "Preflight check başarısız oldu:\n"
            f"{error_message}"
        )

    print("Preflight check: OK")


def print_artifacts(skip_garmin,skip_llm,runtime,):
    print("\n=== Pipeline tamamlandı ===")
    print(f"Pipeline version: {PIPELINE_VERSION}")
    print(f"Zaman: {datetime.now().isoformat(timespec='seconds')}")

    if skip_garmin:
        print("\nKullanılan mevcut Garmin artifact'leri:")
    else:
        print("\nGüncellenen Garmin artifact'leri:")

    print(f"- {runtime.activity_summary_path}")
    print(f"- {runtime.performance_summary_path}")

    print("\nDecision artifact:")
    print(f"- {runtime.coach_context_path}")

    print("\nPlanning artifact'leri:")
    print(f"- {runtime.session_candidates_path}")
    print(f"- {runtime.session_selection_path}")
    print(f"- {runtime.weekly_plan_path}")

    print("\nReporting / narration artifact'leri:")
    print(f"- {runtime.weekly_review_path}")
    print(f"- {runtime.llm_coach_prompt_path}")

    if not skip_llm:
        print(f"- {runtime.coach_message_path}")


def main():
    configure_stdout()

    parser = argparse.ArgumentParser(
        description="Garmin Coach Lab uçtan uca pipeline runner"
    )

    parser.add_argument(
        "--skip-garmin",
        action="store_true",
        help=(
            "Garmin'den yeni veri çekmeden mevcut "
            "activity_summary/performance_summary dosyalarını kullanır."
        ),
    )

    parser.add_argument(
        "--skip-llm",
        action="store_true",
        help=(
            "OpenAI API çağrısını atlar; "
            "yalnızca llm_coach_prompt.md üretir."
        ),
    )

    parser.add_argument(
        "--plan-start-date",
        type=parse_iso_date,
        help=(
            "Weekly plan için YYYY-MM-DD başlangıç tarihi. "
            "Verilmezse local sistem tarihi kullanılır."
        ),
    )

    parser.add_argument(
        "--profile",
        help=(
            "Local profile ID. Örn: kamil veya burcu. "
            "Verilmezse legacy single-profile workspace kullanılır."
        ),
    )

    args = parser.parse_args()

    runtime = configure_profile_runtime(
        args.profile
    )

    python_executable = sys.executable

    preflight_check(
        args,
        python_executable,
        runtime,
    )

    print("\nGarmin Coach Lab Pipeline")
    print("=========================")
    print(f"Version: {PIPELINE_VERSION}")
    
    if runtime.profile_id:
        print(f"Profile: {runtime.profile_id}")
        print(f"Data workspace: {runtime.data_dir}")
    else:
        print("Profile: legacy")
        print(f"Data workspace: {runtime.data_dir}")

    if args.skip_garmin:
        print("Garmin refresh: SKIPPED")
    else:
        print("Garmin refresh: ENABLED")

    if args.skip_llm:
        print("LLM API: SKIPPED")
    else:
        print("LLM API: ENABLED")

    if args.plan_start_date:
        print(
            f"Weekly plan start date: {args.plan_start_date}"
        )
    else:
        print("Weekly plan start date: LOCAL TODAY")

    if not args.skip_garmin:
        run_step(
            "Activity Metrics",
            [python_executable, "activity_metrics.py"],
        )

        run_step(
            "Performance Metrics",
            [python_executable, "performance_metrics.py"],
        )

    run_step(
        "Build Coach Context",
        [python_executable, "build_coach_context.py"],
    )

    planning_command = [
        python_executable,
        "build_weekly_plan.py",
    ]

    if args.plan_start_date:
        planning_command.extend(
            ["--start-date", args.plan_start_date]
        )

    run_step(
        "Build Deterministic Weekly Plan",
        planning_command,
    )

    run_step(
        "Weekly Review Markdown",
        [python_executable, "weekly_review.py"],
    )

    run_step(
        "Generate LLM Prompt",
        [python_executable, "generate_llm_prompt.py"],
    )

    if not args.skip_llm:
        run_step(
            "Generate Coach Message",
            [python_executable, "generate_coach_message.py"],
        )

    print_artifacts(
        skip_garmin=args.skip_garmin,
        skip_llm=args.skip_llm,
        runtime=runtime,
    )


if __name__ == "__main__":
    main()
