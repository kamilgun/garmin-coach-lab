from coach_engine.metrics.load_metrics import compute_load_signals
from coach_engine.rules.progression import decide_progression

from datetime import datetime
import json
import os


ENGINE_VERSION = "0.5.0"


def load_json_if_exists(path, default=None):
    if not os.path.exists(path):
        return default

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_default_manual_context():
    return {
        "schema_version": "2.0",
        "context_period": "this_week",
        "availability": {
            "available_days": [],
            "max_sessions": 3,
            "max_session_duration_min": 50,
            "running_available": True,
            "outdoor_bike_available": True,
            "indoor_trainer_available": True,
            "strength_available": True,
        },
        "recovery": {
            "sleep_quality": "okay",
            "energy_level": "normal",
            "mental_fatigue": "medium",
            "muscle_soreness": "low",
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

def upgrade_manual_context_v1_to_v2(context):
    context = context or {}

    family_status = context.get("family_status", "normal")
    sleep_disrupted = bool(context.get("sleep_disrupted", False))
    workload = context.get("workload", "normal")
    travel = bool(context.get("travel", False))
    training_environment = context.get("training_environment", "home")
    bike_available = bool(context.get("bike_available", True))
    trainer_available = bool(context.get("trainer_available", True))
    running_available = bool(context.get("running_available", True))
    energy_level = context.get("energy_level", "normal")
    injury_notes = (context.get("injury_notes") or "").strip()

    family_load = "normal"
    caregiving_load = "low"

    if family_status in ["child_sick", "family_busy", "high"]:
        family_load = "high"
        caregiving_load = "medium"
    elif family_status in ["busy", "medium"]:
        family_load = "high"
        caregiving_load = "low"

    sleep_quality = "poor" if sleep_disrupted else "okay"

    routine_disruption = "low"
    if travel:
        routine_disruption = "medium"
    if training_environment in ["vacation", "away", "travel"]:
        routine_disruption = "medium"

    active_pain = bool(injury_notes)

    upgraded = get_default_manual_context()

    upgraded["context_period"] = context.get("context_period", "this_week")

    upgraded["availability"]["available_days"] = context.get("available_days", [])
    upgraded["availability"]["running_available"] = running_available
    upgraded["availability"]["outdoor_bike_available"] = bike_available
    upgraded["availability"]["indoor_trainer_available"] = trainer_available
    upgraded["availability"]["strength_available"] = True

    upgraded["recovery"]["sleep_quality"] = sleep_quality
    upgraded["recovery"]["energy_level"] = energy_level
    upgraded["recovery"]["mental_fatigue"] = "medium"
    upgraded["recovery"]["muscle_soreness"] = "low"

    upgraded["pain"]["active_pain"] = active_pain
    upgraded["pain"]["pain_area"] = None
    upgraded["pain"]["pain_severity"] = 2 if active_pain else 0
    upgraded["pain"]["pain_during_running"] = False
    upgraded["pain"]["pain_note"] = injury_notes

    upgraded["life_load"]["work_stress"] = workload
    upgraded["life_load"]["family_load"] = family_load
    upgraded["life_load"]["caregiving_load"] = caregiving_load
    upgraded["life_load"]["travel"] = travel
    upgraded["life_load"]["routine_disruption"] = routine_disruption
    upgraded["life_load"]["time_pressure"] = "normal"
    upgraded["life_load"]["emotional_load"] = "normal"

    upgraded["weekly_intent"] = "maintain_consistency"
    upgraded["user_note"] = context.get("user_note") or ""

    return upgraded

def normalize_enum(value, allowed_values, default):
    if value in allowed_values:
        return value
    return default


def normalize_bool(value, default=False):
    if isinstance(value, bool):
        return value
    if value in ["true", "True", "yes", "1", 1]:
        return True
    if value in ["false", "False", "no", "0", 0]:
        return False
    return default


def normalize_int(value, default, min_value=None, max_value=None):
    try:
        normalized = int(value)
    except (TypeError, ValueError):
        normalized = default

    if min_value is not None:
        normalized = max(min_value, normalized)

    if max_value is not None:
        normalized = min(max_value, normalized)

    return normalized


def add_legacy_manual_context_aliases(context):
    availability = context.get("availability", {})
    recovery = context.get("recovery", {})
    pain = context.get("pain", {})
    life_load = context.get("life_load", {})

    context["available_days"] = availability.get("available_days", [])
    context["running_available"] = availability.get("running_available", True)
    context["bike_available"] = availability.get("outdoor_bike_available", True)
    context["trainer_available"] = availability.get("indoor_trainer_available", True)

    context["energy_level"] = recovery.get("energy_level", "normal")
    context["sleep_disrupted"] = recovery.get("sleep_quality") == "poor"

    context["injury_notes"] = pain.get("pain_note", "")

    context["workload"] = life_load.get("work_stress", "normal")
    context["travel"] = life_load.get("travel", False)

    family_load = life_load.get("family_load", "normal")
    caregiving_load = life_load.get("caregiving_load", "low")

    if family_load == "high" or caregiving_load in ["medium", "high"]:
        context["family_status"] = "family_busy"
    else:
        context["family_status"] = "normal"

    if life_load.get("travel"):
        context["training_environment"] = "travel"
    else:
        context["training_environment"] = "home"

    return context


def normalize_manual_context(context):
    if not context:
        normalized = get_default_manual_context()
        return add_legacy_manual_context_aliases(normalized)

    if context.get("schema_version") != "2.0":
        context = upgrade_manual_context_v1_to_v2(context)

    default_context = get_default_manual_context()

    availability = {
        **default_context["availability"],
        **context.get("availability", {}),
    }

    recovery = {
        **default_context["recovery"],
        **context.get("recovery", {}),
    }

    pain = {
        **default_context["pain"],
        **context.get("pain", {}),
    }

    life_load = {
        **default_context["life_load"],
        **context.get("life_load", {}),
    }

    availability["available_days"] = availability.get("available_days") or []
    availability["max_sessions"] = normalize_int(
        availability.get("max_sessions"),
        default=3,
        min_value=1,
        max_value=7,
    )
    availability["max_session_duration_min"] = normalize_int(
        availability.get("max_session_duration_min"),
        default=50,
        min_value=15,
        max_value=180,
    )
    availability["running_available"] = normalize_bool(
        availability.get("running_available"),
        default=True,
    )
    availability["outdoor_bike_available"] = normalize_bool(
        availability.get("outdoor_bike_available"),
        default=True,
    )
    availability["indoor_trainer_available"] = normalize_bool(
        availability.get("indoor_trainer_available"),
        default=True,
    )
    availability["strength_available"] = normalize_bool(
        availability.get("strength_available"),
        default=True,
    )

    recovery["sleep_quality"] = normalize_enum(
        recovery.get("sleep_quality"),
        ["poor", "okay", "good"],
        "okay",
    )
    recovery["energy_level"] = normalize_enum(
        recovery.get("energy_level"),
        ["very_low", "low", "normal", "high"],
        "normal",
    )
    recovery["mental_fatigue"] = normalize_enum(
        recovery.get("mental_fatigue"),
        ["low", "medium", "high"],
        "medium",
    )
    recovery["muscle_soreness"] = normalize_enum(
        recovery.get("muscle_soreness"),
        ["none", "low", "medium", "high"],
        "low",
    )

    pain["active_pain"] = normalize_bool(
        pain.get("active_pain"),
        default=False,
    )
    pain["pain_severity"] = normalize_int(
        pain.get("pain_severity"),
        default=0,
        min_value=0,
        max_value=10,
    )
    pain["pain_during_running"] = normalize_bool(
        pain.get("pain_during_running"),
        default=False,
    )
    pain["pain_note"] = pain.get("pain_note") or ""

    if not pain["active_pain"]:
        pain["pain_severity"] = 0
        pain["pain_during_running"] = False

    life_load["work_stress"] = normalize_enum(
        life_load.get("work_stress"),
        ["low", "normal", "high", "very_high"],
        "normal",
    )
    life_load["family_load"] = normalize_enum(
        life_load.get("family_load"),
        ["low", "normal", "high"],
        "normal",
    )
    life_load["caregiving_load"] = normalize_enum(
        life_load.get("caregiving_load"),
        ["none", "low", "medium", "high"],
        "low",
    )
    life_load["travel"] = normalize_bool(
        life_load.get("travel"),
        default=False,
    )
    life_load["routine_disruption"] = normalize_enum(
        life_load.get("routine_disruption"),
        ["low", "medium", "high"],
        "low",
    )
    life_load["time_pressure"] = normalize_enum(
        life_load.get("time_pressure"),
        ["low", "normal", "high"],
        "normal",
    )
    life_load["emotional_load"] = normalize_enum(
        life_load.get("emotional_load"),
        ["low", "normal", "high"],
        "normal",
    )

    weekly_intent = normalize_enum(
        context.get("weekly_intent"),
        [
            "recover",
            "maintain_consistency",
            "build_carefully",
            "return_after_break",
            "race_specific",
        ],
        "maintain_consistency",
    )

    normalized = {
        "schema_version": "2.0",
        "context_period": context.get("context_period", "this_week"),
        "availability": availability,
        "recovery": recovery,
        "pain": pain,
        "life_load": life_load,
        "weekly_intent": weekly_intent,
        "user_note": context.get("user_note") or "",
    }

    return add_legacy_manual_context_aliases(normalized)


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

def get_cycling_availability(manual_context):
    bike_available = bool(manual_context.get("bike_available", True))
    trainer_available = bool(manual_context.get("trainer_available", True))

    if bike_available and trainer_available:
        return {
            "available": True,
            "mode": "bike_or_trainer",
            "session_text": "kolay Z2 bisiklet/trainer seansı",
            "unavailable_text": None,
        }

    if trainer_available:
        return {
            "available": True,
            "mode": "trainer",
            "session_text": "kolay Z2 trainer seansı",
            "unavailable_text": None,
        }

    if bike_available:
        return {
            "available": True,
            "mode": "bike",
            "session_text": "kolay Z2 bisiklet seansı",
            "unavailable_text": None,
        }

    return {
        "available": False,
        "mode": "none",
        "session_text": None,
        "unavailable_text": "Bu hafta dışarıda bisiklet veya indoor trainer imkanı olmadığı için bisiklet önerisi uygulanabilir değil",
    }

def apply_context_constraints(decision, manual_context):
    cycling_availability = get_cycling_availability(manual_context)

    cycling_recommendations = {
        "add_easy_z2",
        "add_or_maintain_z2",
        "optional_easy_z2",
        "optional_recovery",
        "recovery_only",
        "recovery",
    }

    if (
        decision.get("cycling") in cycling_recommendations
        and not cycling_availability["available"]
    ):
        decision["cycling"] = "not_available"

        if decision.get("priority") in ["bike", "balanced"]:
            decision["priority"] = "running_consistency"

        decision["reason"] += (
            f" {cycling_availability['unavailable_text']}; "
            "öncelik koşu ritmini kolay seviyede korumaya ve mobiliteye kaydırıldı."
        )

    if manual_context.get("running_available") is False:
        decision["running"] = "not_available"
        decision["priority"] = "recovery"
        decision["weekly_load"] = "reduce_or_maintain"
        decision["reason"] += (
            " Bu hafta koşu imkanı olmadığı için koşu önerisi uygulanabilir değil; "
            "öncelik toparlanma, mobilite ve mümkünse düşük yoğunluklu alternatiflere kaydırıldı."
        )

    if manual_context.get("training_environment") == "vacation":
        decision["reason"] += (
            " Tatil bağlamı nedeniyle planın uygulanabilir ve esnek kalması öncelikli."
        )

    return decision

def build_final_decision(rules, manual_context):
    cycling_availability = get_cycling_availability(manual_context)
    cycling_session_text = (
        cycling_availability["session_text"]
        or "kolay Z2 bisiklet/trainer seansı"
    )

    if cycling_availability["available"]:
        cycling_recommendation_reason = (
            "Koşu hacmini artırmak yerine mevcut koşu ritmini koruyup "
            f"{cycling_session_text} eklemek daha güvenli."
        )
    else:
        cycling_recommendation_reason = (
            "Koşu hacmini artırmak yerine mevcut koşu ritmini kolay seviyede "
            "korumak daha güvenli."
        )

    context_override = has_manual_context_override(manual_context)

    progression_status = rules.get("progression_status")
    risk_level = rules.get("risk_level")
    

    if context_override:
        decision = {
            "weekly_load": "reduce_or_maintain",
            "running": "easy_only",
            "cycling": "optional_recovery",
            "cycling_mode": cycling_availability["mode"],
            "cycling_session_text": cycling_session_text,
            "strength_or_mobility": "recommended_light",
            "priority": "recovery",
            "context_override_applied": True,
            "reason": (
                "Normal rule kararı manuel yaşam bağlamı nedeniyle yumuşatıldı. "
                "Uyku, aile, iş veya sakatlık bağlamı varken haftalık yükü artırmak yerine "
                "kolay ve sürdürülebilir antrenman tercih edilmeli."
            ),
        }

    elif risk_level == "high":
        decision = {
            "weekly_load": "reduce",
            "running": "easy_only",
            "cycling": "recovery_only",
            "cycling_mode": cycling_availability["mode"],
            "cycling_session_text": cycling_session_text,
            "strength_or_mobility": "recommended_light",
            "priority": "recovery",
            "context_override_applied": False,
            "reason": (
                "Yük artışı yüksek risk seviyesinde. Koşu hacmi artırılmamalı; "
                "toparlanma ve düşük yoğunluk öncelikli olmalı."
            ),
        }

    elif progression_status in ["sharp_rebuild_low_absolute_load", "caution_growth"]:
        decision = {
            "weekly_load": "maintain",
            "running": "maintain_easy",
            "cycling": "add_easy_z2",
            "cycling_mode": cycling_availability["mode"],
            "cycling_session_text": cycling_session_text,
            "strength_or_mobility": "recommended",
            "priority": "bike",
            "context_override_applied": False,
            "reason": (
                "Load ratio yüksek ama mutlak hacim düşük. "
                f"{cycling_recommendation_reason}"
            ),
        }

    elif progression_status in ["stable", "productive_build"]:
        decision = {
            "weekly_load": "controlled_build",
            "running": "controlled_increase",
            "cycling": "add_or_maintain_z2",
            "cycling_mode": cycling_availability["mode"],
            "cycling_session_text": cycling_session_text,
            "strength_or_mobility": "recommended",
            "priority": "balanced",
            "context_override_applied": False,
            "reason": (
                "Yük dengeli görünüyor. Haftalık hacim küçük ve kontrollü şekilde artırılabilir. "
                f"{cycling_recommendation_reason}"  
            ),
        }

    elif progression_status in ["below_baseline", "restart", "insufficient_data"]:
        decision = {
            "weekly_load": "restart_easy",
            "running": "easy_only",
            "cycling": "optional_easy_z2",
            "cycling_mode": cycling_availability["mode"],
            "cycling_session_text": cycling_session_text,
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
            "cycling_mode": cycling_availability["mode"],
            "cycling_session_text": cycling_session_text,
            "strength_or_mobility": "recommended",
            "priority": "bike",
            "context_override_applied": False,
            "reason": (
                "Load ratio yüksek ama mutlak hacim düşük. "
                f"{cycling_recommendation_reason}"
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