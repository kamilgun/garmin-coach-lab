from build_coach_context import build_coach_context, write_json
from coach_engine.reporting.weekly_markdown import label

import json
import os
import sys


SCENARIOS = [
    "normal_week",
    "child_sick_week",
    "injury_week",
]


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


def run_context_for_scenario(scenario_name):
    scenario_path = f"data/scenarios/{scenario_name}.json"
    manual_context = load_json(scenario_path)

    write_json("data/manual_context.json", manual_context)

    coach_context = build_coach_context()

    return coach_context


def build_summary():
    lines = []

    lines.append("# Scenario Test Summary\n")
    lines.append(
        "Bu dosya aynı Garmin verisi üzerinde farklı manuel yaşam bağlamlarının "
        "final decision üzerindeki etkisini gösterir.\n"
    )

    lines.append(
        "| Scenario | Weekly Load | Running | Cycling | Priority | Override | Risk |"
    )
    lines.append(
        "|---|---|---|---|---|---|---|"
    )

    for scenario_name in SCENARIOS:
        coach_context = run_context_for_scenario(scenario_name)

        final_decision = coach_context.get("final_decision", {})
        rules = coach_context.get("rules", {})

        lines.append(
            "| "
            f"{scenario_name} | "
            f"{label(final_decision.get('weekly_load'))} | "
            f"{label(final_decision.get('running'))} | "
            f"{label(final_decision.get('cycling'))} | "
            f"{label(final_decision.get('priority'))} | "
            f"{final_decision.get('context_override_applied')} | "
            f"{label(rules.get('risk_level'))} |"
        )

    lines.append("\n## Yorum\n")
    lines.append(
        "- Normal haftada sistem koşu hacmini artırmadan bisikleti önceliklendiriyor."
    )
    lines.append(
        "- Çocuk hastalığı / uykusuzluk gibi yaşam bağlamlarında karar toparlanma yönüne yumuşuyor."
    )
    lines.append(
        "- Sakatlık notu girildiğinde sistem yine toparlanma öncelikli, kolay koşu yaklaşımına dönüyor."
    )

    return "\n".join(lines)


def main():
    configure_stdout()

    summary = build_summary()

    output_path = "data/scenario_test_summary.md"
    write_text(output_path, summary)

    print(summary)
    print(f"\nScenario test summary yazıldı: {output_path}")


if __name__ == "__main__":
    main()