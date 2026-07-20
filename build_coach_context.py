from coach_engine.metrics.load_metrics import compute_load_signals
from coach_engine.rules.progression import decide_progression

from datetime import datetime
import json
import os


ENGINE_VERSION = "0.4.0"


def load_json_if_exists(path, default=None):
    if not os.path.exists(path):
        return default

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def normalize_manual_context(manual_context):
    if manual_context is None:
        manual_context = {}

    return {
    "context_period": manual_context.get("context_period", "current_week"),
    "family_status": manual_context.get("family_status", "normal"),
    "sleep_disrupted": manual_context.get("sleep_disrupted", False),
    "workload": manual_context.get("workload", "normal"),
    "travel": manual_context.get("travel", False),
    "training_environment": manual_context.get("training_environment", "home"),
    "bike_available": manual_context.get("bike_available", True),
    "trainer_available": manual_context.get("trainer_available", True),
    "running_available": manual_context.get("running_available", True),
    "injury_notes": manual_context.get("injury_notes"),
    "energy_level": manual_context.get("energy_level", "normal"),
    "available_days": manual_context.get("available_days", []),
    "user_note": manual_context.get("user_note"),
    }


def build_athlete_context(profile):
    if profile is None:
        return {
            "name": None,
            "primary_goal": None,
            "weekly_target": {},
            "profile_last_reviewed": None,
        }

    return {
        "name": profile.get("name"),
        "primary_goal": profile.get("primary_goal"),
        "weekly_target": profile.get("weekly_target", {}),
        "constraints": profile.get("constraints", []),
        "injury_risks": profile.get("injury_risks", []),
        "equipment": profile.get("equipment", []),
        "profile_last_reviewed": profile.get("profile_last_reviewed"),
    }


def build_metrics_context(activity_data, load_signals):
    s7 = activity_data["summary_7_days"]
    s30 = activity_data["summary_30_days"]

    return {
        "total_hours_7_days": s7.get("total_hours"),
        "total_hours_30_days": s30.get("total_hours"),

        "current_week_hours": load_signals["current_week_hours"],
        "rolling_30_weekly_hours": load_signals["rolling_30_weekly_hours"],
        "previous_23_weekly_hours": load_signals["previous_23_weekly_hours"],
        "weekly_baseline_hours": load_signals["weekly_baseline_hours"],
        "load_ratio": load_signals["load_ratio"],

        "weekly_distance_km": s7.get("total_km"),
        "monthly_distance_km": s30.get("total_km"),

        "activity_count_7_days": s7.get("activity_count"),
        "activity_count_30_days": s30.get("activity_count"),

        "running_sessions": s7.get("running_count"),
        "cycling_sessions": s7.get("cycling_count"),

        "avg_hr_7_days": s7.get("avg_hr"),
        "avg_hr_30_days": s30.get("avg_hr"),
    }


def build_performance_context(performance_data):
    if not performance_data:
        return {
            "race_predictor": None
        }

    return {
        "race_predictor": performance_data.get("race_predictor")
    }


def derive_training_rules(load_signals, activity_data, athlete):
    s7 = activity_data["summary_7_days"]
    target = athlete.get("weekly_target", {})

    target_runs = target.get("running_sessions", 2)
    target_cycling = target.get("cycling_sessions", 1)

    status = load_signals["progression_status"]

    if status in ["spike_risk", "sharp_rebuild_low_absolute_load", "caution_growth"]:
        running_decision = "maintain"
        intervals_allowed = False
        risk_level = "medium" if status != "spike_risk" else "high"
    elif status in ["stable", "productive_build"]:
        running_decision = "controlled_increase"
        intervals_allowed = True
        risk_level = "low"
    elif status in ["below_baseline", "restart", "insufficient_data"]:
        running_decision = "restart_easy"
        intervals_allowed = False
        risk_level = "low"
    else:
        running_decision = "maintain"
        intervals_allowed = False
        risk_level = "medium"

    if s7.get("cycling_count", 0) < target_cycling:
        cycling_priority = "high"
    else:
        cycling_priority = "normal"

    if s7.get("running_count", 0) < target_runs:
        running_target_status = "below_target"
    else:
        running_target_status = "target_met"

    return {
        "progression_status": load_signals["progression_status"],
        "progression_label": load_signals["progression_label"],
        "progression_advice": load_signals["progression_advice"],
        "running_decision": running_decision,
        "running_target_status": running_target_status,
        "cycling_priority": cycling_priority,
        "intervals_allowed": intervals_allowed,
        "risk_level": risk_level,
    }


def has_manual_context_override(manual_context):
    family_status = manual_context.get("family_status")
    workload = manual_context.get("workload")
    energy_level = manual_context.get("energy_level")
    injury_notes = manual_context.get("injury_notes")

    if family_status not in [None, "normal"]:
        return True

    if manual_context.get("sleep_disrupted") is True:
        return True

    if workload in ["high", "very_high"]:
        return True

    # Travel tek başına override değildir.
    # Tatil/seyahat bilgisi apply_context_constraints içinde uygulanabilirlik için kullanılır.

    if energy_level in ["low", "very_low"]:
        return True

    if injury_notes:
        return True

    return False

def apply_context_constraints(decision, manual_context):
    decision = decision.copy()

    bike_available = manual_context.get("bike_available", True)
    trainer_available = manual_context.get("trainer_available", True)
    running_available = manual_context.get("running_available", True)
    training_environment = manual_context.get("training_environment")

    bike_unavailable = bike_available is False or trainer_available is False

    if bike_unavailable and decision.get("cycling") in [
        "add_easy_z2",
        "optional_easy_z2",
        "optional_recovery",
        "recovery_only",
    ]:
        decision["cycling"] = "not_available"

        if decision.get("priority") == "bike":
            decision["priority"] = "running_consistency"

        decision["reason"] = (
            decision.get("reason", "")
            + " Bu hafta bisiklet/trainer imkanı olmadığı için bisiklet önerisi uygulanabilir değil; "
            "öncelik koşu ritmini kolay seviyede korumaya ve mobiliteye kaydırıldı."
        ).strip()

    if running_available is False:
        decision["running"] = "not_available"
        decision["priority"] = "recovery"
        decision["weekly_load"] = "reduce_or_maintain"
        decision["reason"] = (
            decision.get("reason", "")
            + " Bu hafta koşu imkanı olmadığı için koşu önerisi de çıkarıldı."
        ).strip()

    if training_environment == "vacation":
        decision["reason"] = (
            decision.get("reason", "")
            + " Tatil bağlamı nedeniyle planın uygulanabilir ve esnek kalması öncelikli."
        ).strip()

    return decision

def build_final_decision(rules, manual_context):
    context_override = has_manual_context_override(manual_context)

    if context_override:
        decision = {
            "weekly_load": "reduce_or_maintain",
            "running": "easy_only",
            "cycling": "optional_recovery",
            "strength_or_mobility": "recommended_light",
            "priority": "recovery",
            "context_override_applied": True,
            "reason": (
                "Normal rule kararı manuel yaşam bağlamı nedeniyle yumuşatıldı. "
                "Uyku, aile, iş veya sakatlık bağlamı varken haftalık yükü artırmak yerine "
                "kolay ve sürdürülebilir antrenman tercih edilmeli."
            ),
        }

    elif rules["risk_level"] == "high":
        decision = {
            "weekly_load": "reduce",
            "running": "easy_only",
            "cycling": "recovery_only",
            "strength_or_mobility": "recommended_light",
            "priority": "recovery",
            "context_override_applied": False,
            "reason": (
                "Yük artışı yüksek risk seviyesinde. Koşu hacmi artırılmamalı; "
                "toparlanma ve düşük yoğunluk öncelikli olmalı."
            ),
        }

    elif rules["progression_status"] in ["sharp_rebuild_low_absolute_load", "caution_growth"]:
        decision = {
            "weekly_load": "maintain",
            "running": "maintain_easy",
            "cycling": "add_easy_z2",
            "strength_or_mobility": "recommended",
            "priority": "bike",
            "context_override_applied": False,
            "reason": (
                "Load ratio yüksek ama mutlak hacim düşük. Koşu hacmini artırmak yerine "
                "mevcut koşu ritmini koruyup kolay Z2 bisiklet eklemek daha güvenli."
            ),
        }

    elif rules["progression_status"] in ["stable", "productive_build"]:
        decision = {
            "weekly_load": "controlled_build",
            "running": "controlled_increase",
            "cycling": "add_or_maintain_z2",
            "strength_or_mobility": "recommended",
            "priority": "balanced",
            "context_override_applied": False,
            "reason": (
                "Yük dengeli görünüyor. Haftalık hacim küçük ve kontrollü şekilde artırılabilir."
            ),
        }

    elif rules["progression_status"] in ["below_baseline", "restart", "insufficient_data"]:
        decision = {
            "weekly_load": "restart_easy",
            "running": "easy_only",
            "cycling": "optional_easy_z2",
            "strength_or_mobility": "recommended",
            "priority": "consistency",
            "context_override_applied": False,
            "reason": (
                "Öncelik performans artışı değil, düzenli antrenman ritmini yeniden kurmak olmalı."
            ),
        }

    else:
        decision = {
            "weekly_load": "maintain",
            "running": "maintain_easy",
            "cycling": "add_easy_z2",
            "strength_or_mobility": "recommended",
            "priority": "bike",
            "context_override_applied": False,
            "reason": (
                "Load ratio yüksek ama mutlak hacim düşük. Koşu hacmini artırmak yerine "
                "mevcut koşu ritmini koruyup kolay Z2 bisiklet eklemek daha güvenli."
            ),
        }

    return apply_context_constraints(decision, manual_context)


def build_coach_context():
    activity_data = load_json_if_exists("data/activity_summary.json")
    performance_data = load_json_if_exists("data/performance_summary.json")
    athlete_profile = load_json_if_exists("athlete_profile.json")
    manual_context = load_json_if_exists("data/manual_context.json", default={})

    if activity_data is None:
        raise FileNotFoundError("data/activity_summary.json bulunamadı.")

    s7 = activity_data["summary_7_days"]
    s30 = activity_data["summary_30_days"]

    load_signals = compute_load_signals(s7, s30)
    progression_decision = decide_progression(load_signals)
    load_signals.update(progression_decision)

    athlete = build_athlete_context(athlete_profile)
    metrics = build_metrics_context(activity_data, load_signals)
    performance = build_performance_context(performance_data)
    manual_context = normalize_manual_context(manual_context)

    rules = derive_training_rules(load_signals, activity_data, athlete)
    final_decision = build_final_decision(rules, manual_context)

    return {
        "athlete": athlete,
        "metrics": metrics,
        "performance": performance,
        "rules": rules,
        "manual_context": manual_context,
        "final_decision": final_decision,
        "metadata": {
            "engine_version": ENGINE_VERSION,
            "decision_engine": "rule_based_with_manual_context",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
        },
    }


def main():
    coach_context = build_coach_context()
    write_json("data/coach_context.json", coach_context)

    print(json.dumps(coach_context, ensure_ascii=False, indent=2))
    print("\nCoach context yazıldı: data/coach_context.json")


if __name__ == "__main__":
    main()