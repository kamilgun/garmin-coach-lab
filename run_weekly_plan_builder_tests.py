from copy import deepcopy

from coach_engine.planning.weekly_plan import (
    PLANNER_VERSION,
    PLANNING_ENGINE,
    build_weekly_plan,
    build_weekly_plan_bundle,
)


def base_context():
    return {
        "training_profile": {
            "schema_version": "1.0",
            "data_available": True,
            "running_30_days": {
                "window_days": 30,
                "runs_analyzed": 6,
                "pace_guidance_available": True,
                "median_run_distance_km": 5.0,
                "median_run_duration_min": 32.5,
                "longest_run_distance_km": 7.54,
                "longest_run_duration_min": 51.7,
                "pace_distribution_sec_per_km": {
                    "faster_quartile_p25": 388,
                    "median": 394,
                    "slower_quartile_p75": 396,
                },
            },
            "recent_runs": [
                {
                    "avg_hr": 143,
                    "avg_pace_sec_per_km": 386,
                },
                {
                    "avg_hr": 142,
                    "avg_pace_sec_per_km": 396,
                },
                {
                    "avg_hr": 134,
                    "avg_pace_sec_per_km": 411,
                },
                {
                    "avg_hr": 151,
                    "avg_pace_sec_per_km": 387,
                },
                {
                    "avg_hr": 143,
                    "avg_pace_sec_per_km": 394,
                },
            ],
        },
        "rules": {
            "intervals_allowed": False,
        },
        "context_signals": {
            "health_constraint": "none",
            "weekly_intent": "maintain_consistency",
            "reasons": [],
        },
        "final_decision": {
            "weekly_load": "restart_easy",
            "running": "easy_only",
            "cycling": "not_available",
            "cycling_mode": "none",
            "strength_or_mobility": "optional",
            "priority": "consistency",
            "weekly_intent": "maintain_consistency",
            "health_constraint": "none",
            "planning_limits": {
                "max_sessions": 1,
                "max_session_duration_min": 45,
                "available_days": [
                    "monday",
                    "tuesday",
                    "wednesday",
                    "thursday",
                    "friday",
                    "saturday",
                    "sunday",
                ],
                "available_modalities": [
                    "running",
                    "strength_or_mobility",
                ],
            },
            "context_reasons": [],
            "reason": "Ritmi kolay koşuyla yeniden kur.",
        },
        "metadata": {
            "engine_version": "0.6.0",
            "generated_at": "2026-07-31T16:00:00",
        },
    }


def run_tests():
    context = base_context()
    original = deepcopy(context)

    bundle = build_weekly_plan_bundle(
        context,
        start_date="2026-07-31",
    )

    assert context == original
    assert bundle["planner_version"] == PLANNER_VERSION
    assert bundle["planning_engine"] == PLANNING_ENGINE

    candidates = bundle["session_candidates"]
    selection = bundle["session_selection"]
    plan = bundle["weekly_plan"]

    assert candidates["planning_stage"] == "candidate_generation"
    assert selection[
        "planning_stage"
    ] == "session_selection_and_prescription"
    assert plan["planning_stage"] == "rolling_7_day_scheduling"

    assert candidates["candidate_count"] == 2
    assert selection["session_count"] == 1
    assert plan["plan_status"] == "ready"
    assert plan["sessions"][0]["scheduling"]["date"] == "2026-08-03"
    assert plan["sessions"][0][
        "session_total_duration"
    ]["target_min"] == 43

    final_only = build_weekly_plan(
        context,
        start_date="2026-07-31",
    )
    assert final_only["plan_status"] == "ready"
    assert final_only["sessions"][0][
        "scheduling"
    ]["date"] == "2026-08-03"

    illness_context = base_context()
    illness_context["final_decision"][
        "health_constraint"
    ] = "active_illness"

    illness_bundle = build_weekly_plan_bundle(
        illness_context,
        start_date="2026-07-31",
    )

    assert illness_bundle["session_candidates"][
        "status"
    ] == "no_structured_training"
    assert illness_bundle["session_selection"][
        "status"
    ] == "no_structured_training"
    assert illness_bundle["weekly_plan"][
        "plan_status"
    ] == "no_structured_training"

    print("All weekly plan builder facade tests passed.")


if __name__ == "__main__":
    run_tests()
