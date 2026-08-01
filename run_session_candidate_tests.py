from copy import deepcopy

from coach_engine.planning.session_candidates import (
    build_session_candidates,
)


def base_context():
    return {
        "training_profile": {
            "schema_version": "1.0",
            "data_available": True,
            "running_30_days": {
                "runs_analyzed": 6,
                "median_run_duration_min": 32.5,
                "median_run_distance_km": 5.0,
                "longest_run_duration_min": 51.7,
                "longest_run_distance_km": 7.54,
                "pace_distribution_display": {
                    "median": "6:34/km",
                },
            },
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
                "available_days": ["monday", "wednesday"],
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
        },
    }


def candidate_ids(result):
    return [item["candidate_id"] for item in result["candidates"]]


def run_tests():
    # 1. Current one-session context.
    current = build_session_candidates(base_context())
    assert current["status"] == "ready"
    assert candidate_ids(current) == ["running_easy", "mobility_core"]
    assert current["candidates"][1]["delivery_mode"] == "add_on"
    assert current["standalone_capacity_requested"] == 1
    assert current["selection_required"] is False

    # 2. Active illness hard stop.
    illness_context = base_context()
    illness_context["final_decision"]["health_constraint"] = "active_illness"
    illness = build_session_candidates(illness_context)
    assert illness["status"] == "no_structured_training"
    assert illness["candidate_count"] == 0
    assert "structured_training" in illness["avoid"]

    # 3. Trainer-only context.
    trainer_context = base_context()
    trainer_context["final_decision"].update(
        {
            "running": "not_available",
            "cycling": "add_easy_z2",
            "cycling_mode": "trainer",
            "strength_or_mobility": "recommended",
            "priority": "bike",
            "planning_limits": {
                "max_sessions": 2,
                "max_session_duration_min": 50,
                "available_days": ["tuesday", "saturday"],
                "available_modalities": [
                    "cycling",
                    "strength_or_mobility",
                ],
            },
        }
    )
    trainer = build_session_candidates(trainer_context)
    assert trainer["candidates"][0]["modality"] == "indoor_trainer"
    assert trainer["candidates"][0]["session_type"] == "easy_z2_cycling"
    assert "running" in trainer["avoid"]

    # 4. Capacity overflow is flagged, not silently resolved.
    balanced_context = base_context()
    balanced_context["final_decision"].update(
        {
            "cycling": "add_or_maintain_z2",
            "cycling_mode": "bike_or_trainer",
            "strength_or_mobility": "recommended",
            "priority": "balanced",
            "planning_limits": {
                "max_sessions": 2,
                "max_session_duration_min": 60,
                "available_days": ["monday", "wednesday", "saturday"],
                "available_modalities": [
                    "running",
                    "cycling",
                    "strength_or_mobility",
                ],
            },
        }
    )
    balanced = build_session_candidates(balanced_context)
    assert balanced["candidate_count"] == 3
    assert balanced["standalone_capacity_requested"] == 3
    assert balanced["selection_required"] is True

    # 5. Recovery priority ranks mobility first.
    recovery_context = deepcopy(balanced_context)
    recovery_context["final_decision"].update(
        {
            "cycling": "optional_recovery",
            "priority": "recovery",
            "weekly_intent": "recover",
        }
    )
    recovery = build_session_candidates(recovery_context)
    assert recovery["candidates"][0]["candidate_id"] == "mobility_core"

    # 6. Missing training profile remains valid.
    no_profile_context = base_context()
    no_profile_context.pop("training_profile")
    no_profile = build_session_candidates(no_profile_context)
    running_candidate = no_profile["candidates"][0]
    assert running_candidate["training_reference"]["data_available"] is False

    print("All session candidate tests passed.")


if __name__ == "__main__":
    run_tests()
