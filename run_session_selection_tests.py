from copy import deepcopy

from coach_engine.planning.session_selection import select_sessions


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
                "pace_distribution_sec_per_km": {
                    "faster_quartile_p25": 388,
                    "median": 394,
                    "slower_quartile_p75": 396,
                },
                "pace_distribution_display": {
                    "faster_quartile_p25": "6:28/km",
                    "median": "6:34/km",
                    "slower_quartile_p75": "6:36/km",
                },
            },
            "recent_runs": [
                {
                    "date": "2026-07-21",
                    "avg_hr": 143,
                    "avg_pace_sec_per_km": 386,
                },
                {
                    "date": "2026-07-16",
                    "avg_hr": 142,
                    "avg_pace_sec_per_km": 396,
                },
                {
                    "date": "2026-07-15",
                    "avg_hr": 134,
                    "avg_pace_sec_per_km": 411,
                },
                {
                    "date": "2026-07-11",
                    "avg_hr": 151,
                    "avg_pace_sec_per_km": 387,
                },
                {
                    "date": "2026-07-10",
                    "avg_hr": 143,
                    "avg_pace_sec_per_km": 394,
                },
            ],
        }
    }


def current_candidates():
    return {
        "schema_version": "1.0",
        "status": "ready",
        "generated_at": "2026-07-31T12:00:00",
        "source_engine_version": "0.6.0",
        "weekly_intent": "maintain_consistency",
        "priority": "consistency",
        "planning_limits": {
            "max_sessions": 1,
            "max_session_duration_min": 45,
            "available_days": [
                "monday",
                "wednesday",
            ],
            "available_modalities": [
                "running",
                "strength_or_mobility",
            ],
        },
        "candidates": [
            {
                "candidate_id": "running_easy",
                "modality": "running",
                "session_type": "easy_run",
                "recommendation": "recommended",
                "intensity_cap": "easy",
                "delivery_mode": "standalone",
                "standalone_capacity_cost": 1,
                "source_decision": "easy_only",
                "priority_rank": 1,
                "reason": "Kolay koşu ritmini yeniden kur.",
            },
            {
                "candidate_id": "mobility_core",
                "modality": "strength_or_mobility",
                "session_type": "mobility_core",
                "recommendation": "add_on",
                "intensity_cap": "light",
                "delivery_mode": "add_on",
                "standalone_capacity_cost": 0,
                "source_decision": "optional",
                "priority_rank": 2,
                "reason": "Mobiliteyi ana seansa ekle.",
            },
        ],
        "avoid": [
            "cycling",
            "interval",
            "tempo_run",
        ],
        "reasons": [
            "Ritmi yeniden kur.",
        ],
    }


def run_tests():
    # 1. Current context: one easy run + mobility add-on.
    current = select_sessions(
        base_context(),
        current_candidates(),
    )
    assert current["status"] == "ready"
    assert current["session_count"] == 1
    assert current["selection_summary"]["capacity_used"] == 1
    assert current["selection_summary"]["add_ons_selected"] == 1

    session = current["sessions"][0]
    assert session["type"] == "easy_run"
    assert session["duration"]["target_min"] == 35
    assert session["session_total_duration"]["target_min"] == 43
    assert session["session_total_duration"]["max"] <= 45
    assert len(session["add_ons"]) == 1
    assert session["pace_guidance"]["available"] is True
    assert session["pace_guidance"]["binding"] is False
    assert session["pace_guidance"]["range_display"]["faster"] == "6:28/km"
    assert session["pace_guidance"]["range_display"]["slower"] == "6:49/km"
    assert session["distance_guidance"]["available"] is True
    assert session["distance_guidance"]["binding"] is False

    # 2. Active illness: no sessions.
    illness_candidates = {
        **current_candidates(),
        "status": "no_structured_training",
        "candidates": [],
        "blocked_candidates": [
            {
                "candidate_id": "running_easy",
                "reason": "Aktif hastalık.",
            }
        ],
    }
    illness = select_sessions(
        base_context(),
        illness_candidates,
    )
    assert illness["status"] == "no_structured_training"
    assert illness["session_count"] == 0

    # 3. Capacity overflow: highest-ranked two standalone sessions.
    overflow_candidates = deepcopy(current_candidates())
    overflow_candidates["planning_limits"]["max_sessions"] = 2
    overflow_candidates["planning_limits"][
        "max_session_duration_min"
    ] = 60
    overflow_candidates["candidates"] = [
        {
            "candidate_id": "running_easy",
            "modality": "running",
            "session_type": "easy_run",
            "recommendation": "recommended",
            "intensity_cap": "easy",
            "delivery_mode": "standalone",
            "source_decision": "maintain_easy",
            "priority_rank": 1,
            "reason": "Run.",
        },
        {
            "candidate_id": "cycling_easy_z2",
            "modality": "indoor_trainer",
            "session_type": "easy_z2_cycling",
            "recommendation": "recommended",
            "intensity_cap": "easy_z2",
            "delivery_mode": "standalone",
            "source_decision": "add_easy_z2",
            "priority_rank": 2,
            "reason": "Ride.",
        },
        {
            "candidate_id": "mobility_core",
            "modality": "strength_or_mobility",
            "session_type": "mobility_core",
            "recommendation": "recommended",
            "intensity_cap": "light",
            "delivery_mode": "standalone",
            "source_decision": "recommended",
            "priority_rank": 3,
            "reason": "Mobility.",
        },
    ]
    overflow = select_sessions(
        base_context(),
        overflow_candidates,
    )
    assert overflow["session_count"] == 2
    assert [
        session["source_candidate_id"]
        for session in overflow["sessions"]
    ] == ["running_easy", "cycling_easy_z2"]
    assert overflow["not_selected"][0][
        "reason_code"
    ] == "standalone_capacity_limit"

    # 4. Trainer-only guidance.
    trainer_candidates = deepcopy(current_candidates())
    trainer_candidates["planning_limits"]["max_sessions"] = 1
    trainer_candidates["planning_limits"][
        "max_session_duration_min"
    ] = 40
    trainer_candidates["candidates"] = [
        {
            "candidate_id": "cycling_easy_z2",
            "modality": "indoor_trainer",
            "session_type": "easy_z2_cycling",
            "recommendation": "recommended",
            "intensity_cap": "easy_z2",
            "delivery_mode": "standalone",
            "source_decision": "add_easy_z2",
            "priority_rank": 1,
            "reason": "Trainer.",
        }
    ]
    trainer = select_sessions(
        base_context(),
        trainer_candidates,
    )
    trainer_session = trainer["sessions"][0]
    assert trainer_session["modality"] == "indoor_trainer"
    assert trainer_session["duration"]["target_min"] == 40
    assert trainer_session["pace_guidance"]["available"] is False
    assert trainer_session["distance_guidance"]["available"] is False

    # 5. Missing running profile: still valid, no invented guidance.
    no_profile = select_sessions(
        {},
        current_candidates(),
    )
    no_profile_session = no_profile["sessions"][0]
    assert no_profile_session["pace_guidance"]["available"] is False
    assert no_profile_session["distance_guidance"]["available"] is False

    # 6. Tight 25-minute limit keeps 20-minute run + 5-minute add-on.
    tight_candidates = deepcopy(current_candidates())
    tight_candidates["planning_limits"][
        "max_session_duration_min"
    ] = 25
    tight = select_sessions(
        base_context(),
        tight_candidates,
    )
    tight_session = tight["sessions"][0]
    assert tight_session["duration"]["target_min"] == 20
    assert tight_session["add_ons"][0]["duration"]["target_min"] == 5
    assert tight_session["session_total_duration"]["target_min"] == 25
    assert tight_session["session_total_duration"]["max"] <= 25

    # 7. Twenty-minute limit drops add-on rather than shrinking run too far.
    very_tight_candidates = deepcopy(current_candidates())
    very_tight_candidates["planning_limits"][
        "max_session_duration_min"
    ] = 20
    very_tight = select_sessions(
        base_context(),
        very_tight_candidates,
    )
    very_tight_session = very_tight["sessions"][0]
    assert very_tight_session["duration"]["target_min"] == 20
    assert very_tight_session["add_ons"] == []
    assert very_tight["selection_summary"]["add_ons_selected"] == 0
    assert very_tight["not_selected"][0][
        "reason_code"
    ] == "insufficient_session_duration"

    print("All session selection tests passed.")


if __name__ == "__main__":
    run_tests()
