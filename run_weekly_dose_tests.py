from copy import deepcopy

from coach_engine.planning.weekly_dose import (
    resolve_weekly_dose,
)


def base_context():
    return {
        "athlete": {
            "weekly_target": {
                "running_sessions": 2,
                "cycling_sessions": 0,
                "strength_or_mobility_sessions": 1,
            },
        },
        "training_profile": {
            "data_available": True,
            "running_30_days": {
                "runs_analyzed": 4,
                "median_run_duration_min": 46.2,
            },
        },
        "context_signals": {
            "weekly_intent": "return_after_break",
            "health_constraint": "none",
        },
        "final_decision": {
            "running": "easy_only",
            "cycling": "not_available",
            "cycling_mode": "none",
            "strength_or_mobility": "not_available",
            "priority": "consistency",
            "weekly_intent": "return_after_break",
            "health_constraint": "none",
            "planning_limits": {
                "max_sessions": 3,
                "max_session_duration_min": 45,
                "available_days": [],
                "available_modalities": [
                    "running",
                ],
            },
        },
    }


def run_tests():
    # 1. Burcu-like regression:
    # recent base + target 2 + capacity >= 2
    # means two easy-return running sessions.
    context = base_context()

    dose = resolve_weekly_dose(context)

    assert dose["requested_sessions"]["running"] == 2
    assert dose["resolved_sessions"]["running"] == 2
    assert (
        dose["frequency_policy"]
        == "preserve_frequency_reduce_duration"
    )
    assert dose["running_duration_target_min"] == 30

    # 2. max_sessions remains a hard cap.
    limited = deepcopy(context)
    limited["final_decision"]["planning_limits"][
        "max_sessions"
    ] = 1

    dose = resolve_weekly_dose(limited)

    assert dose["resolved_sessions"]["running"] == 1
    assert dose["effective_capacity"] == 1

    # 3. Explicit available days also limit capacity.
    one_day = deepcopy(context)
    one_day["final_decision"]["planning_limits"][
        "available_days"
    ] = ["saturday"]

    dose = resolve_weekly_dose(one_day)

    assert dose["effective_capacity"] == 1
    assert dose["resolved_sessions"]["running"] == 1

    # 4. No meaningful recent running base:
    # reduce frequency as well as duration.
    no_base = deepcopy(context)
    no_base["training_profile"]["running_30_days"][
        "runs_analyzed"
    ] = 0

    dose = resolve_weekly_dose(no_base)

    assert dose["requested_sessions"]["running"] == 1
    assert dose["resolved_sessions"]["running"] == 1
    assert (
        dose["frequency_policy"]
        == "reduce_frequency_and_duration"
    )
    assert dose["running_duration_target_min"] == 25

    # 5. Active illness is a hard stop.
    illness = deepcopy(context)
    illness["final_decision"][
        "health_constraint"
    ] = "active_illness"

    dose = resolve_weekly_dose(illness)

    assert dose["effective_capacity"] == 0
    assert dose["resolved_sessions"]["running"] == 0
    assert (
        dose["frequency_policy"]
        == "no_structured_training"
    )

    # 6. Running unavailable means zero running dose.
    unavailable = deepcopy(context)
    unavailable["final_decision"][
        "running"
    ] = "not_available"
    unavailable["final_decision"][
        "planning_limits"
    ]["available_modalities"] = []

    dose = resolve_weekly_dose(unavailable)

    assert dose["resolved_sessions"]["running"] == 0

    # 7. Good conditions must not exceed weekly target.
    good = deepcopy(context)

    good["manual_context"] = {
        "recovery": {
            "sleep_quality": "good",
            "energy_level": "high",
        },
    }

    dose = resolve_weekly_dose(good)

    assert dose["resolved_sessions"]["running"] == 2
    assert dose["resolved_sessions"]["running"] != 3

    # 8. Missing athlete weekly target keeps legacy behavior.
    legacy = deepcopy(context)
    legacy.pop("athlete")

    dose = resolve_weekly_dose(legacy)

    assert (
        dose["source"]
        == "legacy_final_decision_fallback"
    )
    assert dose["resolved_sessions"]["running"] == 1

    print("All weekly dose tests passed.")


if __name__ == "__main__":
    run_tests()
