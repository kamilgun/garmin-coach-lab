import argparse
import os
import subprocess
import sys
from datetime import datetime


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
    except subprocess.CalledProcessError as e:
        if allow_fail:
            print(f"[WARN] {name} başarısız oldu ama pipeline devam ediyor.")
            print(f"[WARN] Exit code: {e.returncode}")
            return False

        print(f"[ERROR] {name} başarısız oldu.")
        print(f"[ERROR] Exit code: {e.returncode}")
        raise

    return True


def print_artifacts(skip_llm):
    print("\n=== Pipeline tamamlandı ===")
    print(f"Zaman: {datetime.now().isoformat(timespec='seconds')}")

    print("\nÜretilen / güncellenen dosyalar:")
    print("- data/activity_summary.json")
    print("- data/performance_summary.json")
    print("- data/coach_context.json")
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
        help="OpenAI API çağrısını atlar; sadece llm_coach_prompt.md üretir.",
    )

    args = parser.parse_args()

    python_executable = sys.executable

    print("\nGarmin Coach Lab Pipeline")
    print("=========================")

    if args.skip_garmin:
        print("Garmin refresh: SKIPPED")
    else:
        print("Garmin refresh: ENABLED")

    if args.skip_llm:
        print("LLM API: SKIPPED")
    else:
        print("LLM API: ENABLED")

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

    run_step(
        "Weekly Review Markdown",
        [python_executable, "weekly_review.py"],
    )

    run_step(
        "Generate LLM Prompt",
        [python_executable, "generate_llm_prompt.py"],
    )

    if not args.skip_llm:
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError(
                "OPENAI_API_KEY bulunamadı. "
                "Ya environment variable olarak tanımla ya da --skip-llm kullan."
            )

        run_step(
            "Generate Coach Message",
            [python_executable, "generate_coach_message.py"],
        )

    print_artifacts(skip_llm=args.skip_llm)


if __name__ == "__main__":
    main()