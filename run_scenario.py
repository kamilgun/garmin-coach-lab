from build_coach_context import build_coach_context, write_json
from coach_engine.reporting.weekly_markdown import render_weekly_review
from coach_engine.narration.llm_prompt import build_llm_coach_prompt

import argparse
import json
import os
import sys


def configure_stdout():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")


def load_json(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Dosya bulunamadı: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def run_scenario(scenario_name):
    scenario_path = f"data/scenarios/{scenario_name}.json"

    manual_context = load_json(scenario_path)

    write_json("data/manual_context.json", manual_context)

    coach_context = build_coach_context()
    write_json("data/coach_context.json", coach_context)

    weekly_review = render_weekly_review(coach_context)
    llm_prompt = build_llm_coach_prompt(coach_context)

    write_text(f"data/weekly_review_{scenario_name}.md", weekly_review)
    write_text(f"data/llm_coach_prompt_{scenario_name}.md", llm_prompt)

    # Ayrıca standart dosyaları da güncel tutuyoruz.
    write_text("data/weekly_review.md", weekly_review)
    write_text("data/llm_coach_prompt.md", llm_prompt)

    print(f"\nScenario çalıştı: {scenario_name}")
    print(f"- data/manual_context.json güncellendi")
    print(f"- data/coach_context.json güncellendi")
    print(f"- data/weekly_review_{scenario_name}.md yazıldı")
    print(f"- data/llm_coach_prompt_{scenario_name}.md yazıldı")

    final_decision = coach_context.get("final_decision", {})
    rules = coach_context.get("rules", {})

    print("\nFinal Decision:")
    print(f"- weekly_load: {final_decision.get('weekly_load')}")
    print(f"- running: {final_decision.get('running')}")
    print(f"- cycling: {final_decision.get('cycling')}")
    print(f"- priority: {final_decision.get('priority')}")
    print(f"- context_override_applied: {final_decision.get('context_override_applied')}")
    print(f"- risk_level: {rules.get('risk_level')}")


def main():
    configure_stdout()

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "scenario_name",
        help="Scenario adı. Örn: normal_week, child_sick_week, injury_week",
    )

    args = parser.parse_args()
    run_scenario(args.scenario_name)


if __name__ == "__main__":
    main()