import argparse
from datetime import date, datetime
import os
import subprocess
import sys


PIPELINE_VERSION = "0.8.0"


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


def check_required_paths(paths, errors):
    for path in paths:
        if not os.path.exists(path):
            errors.append(f"Gerekli dosya bulunamadı: {path}")


def preflight_check(args, python_executable):
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
            ["data/activity_summary.json"],
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

        if os.getenv("OPENAI_API_KEY"):
            print("OPENAI_API_KEY: OK")
        else:
            errors.append(
                "OPENAI_API_KEY bulunamadı. "
                ".env dosyası oluştur veya terminalde "
                "OPENAI_API_KEY tanımla."
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


def print_artifacts(skip_garmin, skip_llm):
    print("\n=== Pipeline tamamlandı ===")
    print(f"Pipeline version: {PIPELINE_VERSION}")
    print(f"Zaman: {datetime.now().isoformat(timespec='seconds')}")

    if skip_garmin:
        print("\nKullanılan mevcut Garmin artifact'leri:")
    else:
        print("\nGüncellenen Garmin artifact'leri:")

    print("- data/activity_summary.json")
    print("- data/performance_summary.json")

    print("\nDecision artifact:")
    print("- data/coach_context.json")

    print("\nPlanning artifact'leri:")
    print("- data/session_candidates.json")
    print("- data/session_selection.json")
    print("- data/weekly_plan.json")

    print("\nReporting / narration artifact'leri:")
    print("- data/weekly_review.md")
    print("- data/llm_coach_prompt.md")

    if not skip_llm:
        print("- data/coach_message.md")


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

    args = parser.parse_args()
    python_executable = sys.executable

    preflight_check(args, python_executable)

    print("\nGarmin Coach Lab Pipeline")
    print("=========================")
    print(f"Version: {PIPELINE_VERSION}")

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
    )


if __name__ == "__main__":
    main()
