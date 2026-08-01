from copy import deepcopy

from coach_engine.contracts import (
    ArtifactContractError,
    validate_session_selection_v1,
    validate_weekly_plan_v1,
)
from coach_engine.planning.weekly_plan import (
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
                {"avg_hr": 143, "avg_pace_sec_per_km": 386},
                {"avg_hr": 142, "avg_pace_sec_per_km": 396},
                {"avg_hr": 134, "avg_pace_sec_per_km": 411},
                {"avg_hr": 151, "avg_pace_sec_per_km": 387},
                {"avg_hr": 143, "avg_pace_sec_per_km": 394},
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


def expect_failure(callback, expected_path):
    try:
        callback()
    except ArtifactContractError as exc:
        assert expected_path in str(exc), str(exc)
        return
    raise AssertionError("ArtifactContractError bekleniyordu.")


def run_tests():
    context = base_context()
    original_context = deepcopy(context)

    bundle = build_weekly_plan_bundle(
        context,
        start_date="2026-07-31",
    )

    assert context == original_context

    selection = bundle["session_selection"]
    weekly_plan = bundle["weekly_plan"]

    assert validate_session_selection_v1(selection) is selection
    assert validate_weekly_plan_v1(weekly_plan) is weekly_plan

    invalid = deepcopy(selection)
    invalid["schema_version"] = "2.0"
    expect_failure(
        lambda: validate_session_selection_v1(invalid),
        "$.schema_version",
    )

    invalid = deepcopy(selection)
    invalid["session_count"] = 99
    expect_failure(
        lambda: validate_session_selection_v1(invalid),
        "$.session_count",
    )

    invalid = deepcopy(selection)
    invalid["sessions"][0][
        "session_total_duration"
    ]["max"] = 46
    expect_failure(
        lambda: validate_session_selection_v1(invalid),
        "$.sessions[0].session_total_duration.max",
    )

    invalid = deepcopy(selection)
    invalid["sessions"][0]["pace_guidance"]["binding"] = True
    expect_failure(
        lambda: validate_session_selection_v1(invalid),
        "$.sessions[0].pace_guidance.binding",
    )

    invalid = deepcopy(weekly_plan)
    invalid["scheduled_count"] = 2
    expect_failure(
        lambda: validate_weekly_plan_v1(invalid),
        "$.scheduled_count",
    )

    invalid = deepcopy(weekly_plan)
    invalid["planning_horizon"]["end_date"] = "2026-08-07"
    expect_failure(
        lambda: validate_weekly_plan_v1(invalid),
        "$.planning_horizon.end_date",
    )

    invalid = deepcopy(weekly_plan)
    duplicate = deepcopy(invalid["sessions"][0])
    duplicate["session_id"] = "session_2"
    invalid["sessions"].append(duplicate)
    invalid["session_count"] = 2
    invalid["scheduled_count"] = 2
    invalid["schedule_summary"]["requested_sessions"] = 2
    invalid["schedule_summary"]["scheduled_sessions"] = 2
    expect_failure(
        lambda: validate_weekly_plan_v1(invalid),
        "$.sessions[1].scheduling.date",
    )

    invalid = deepcopy(weekly_plan)
    invalid["plan_status"] = "no_structured_training"
    expect_failure(
        lambda: validate_weekly_plan_v1(invalid),
        "$.plan_status",
    )

    illness_context = base_context()
    illness_context["final_decision"][
        "health_constraint"
    ] = "active_illness"

    illness_bundle = build_weekly_plan_bundle(
        illness_context,
        start_date="2026-07-31",
    )

    assert (
        illness_bundle["weekly_plan"]["plan_status"]
        == "no_structured_training"
    )
    validate_session_selection_v1(
        illness_bundle["session_selection"]
    )
    validate_weekly_plan_v1(illness_bundle["weekly_plan"])

    print("All artifact contract tests passed.")


if __name__ == "__main__":
    run_tests()
