from copy import deepcopy

from coach_engine.planning.scheduling import schedule_weekly_plan


def base_selection():
    return {
        "schema_version": "1.0",
        "generated_at": "2026-07-31T16:29:15",
        "source_engine_version": "0.6.0",
        "weekly_intent": "maintain_consistency",
        "priority": "consistency",
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
        "status": "ready",
        "sessions": [
            {
                "session_id": "session_1",
                "source_candidate_id": "running_easy",
                "modality": "running",
                "type": "easy_run",
                "duration": {
                    "target_min": 35,
                    "min": 30,
                    "max": 35,
                },
                "session_total_duration": {
                    "target_min": 43,
                    "min": 35,
                    "max": 45,
                },
                "add_ons": [
                    {
                        "source_candidate_id": "mobility_core",
                        "type": "mobility_core",
                    }
                ],
                "scheduling": {
                    "status": "not_scheduled",
                },
            }
        ],
        "avoid": [
            "cycling",
            "interval",
            "tempo_run",
        ],
        "reasons": [
            "Ritmi kolay koşuyla yeniden kur.",
        ],
    }


def make_session(number):
    return {
        "session_id": f"session_{number}",
        "source_candidate_id": f"candidate_{number}",
        "modality": "running",
        "type": "easy_run",
        "add_ons": [],
        "scheduling": {
            "status": "not_scheduled",
        },
    }


def run_tests():
    # 1. Friday start + all days + one session -> Monday.
    current = schedule_weekly_plan(
        base_selection(),
        start_date="2026-07-31",
    )
    assert current["plan_status"] == "ready"
    assert current["planning_horizon"]["start_date"] == "2026-07-31"
    assert current["planning_horizon"]["end_date"] == "2026-08-06"
    assert current["sessions"][0]["scheduling"]["date"] == "2026-08-03"
    assert current["sessions"][0]["scheduling"]["day"] == "monday"
    assert current["sessions"][0]["scheduling"]["day_label_tr"] == "Pazartesi"
    assert current["sessions"][0]["add_ons"][0][
        "scheduling"
    ]["date"] == "2026-08-03"

    # 2. Monday/Wednesday restriction -> one session picks Monday.
    restricted = deepcopy(base_selection())
    restricted["planning_limits"]["available_days"] = [
        "monday",
        "wednesday",
    ]
    restricted_result = schedule_weekly_plan(
        restricted,
        start_date="2026-07-31",
    )
    assert restricted_result["sessions"][0][
        "scheduling"
    ]["date"] == "2026-08-03"
    assert len(
        restricted_result["available_dates_in_horizon"]
    ) == 2

    # 3. Empty available_days means all days.
    unrestricted = deepcopy(base_selection())
    unrestricted["planning_limits"]["available_days"] = []
    unrestricted_result = schedule_weekly_plan(
        unrestricted,
        start_date="2026-07-31",
    )
    assert len(
        unrestricted_result["available_dates_in_horizon"]
    ) == 7
    assert unrestricted_result["availability_resolution"][
        "empty_means"
    ] == "all_days_available"

    # 4. Three sessions -> Saturday, Monday, Wednesday.
    three = deepcopy(base_selection())
    three["planning_limits"]["max_sessions"] = 3
    three["sessions"] = [
        make_session(1),
        make_session(2),
        make_session(3),
    ]
    three_result = schedule_weekly_plan(
        three,
        start_date="2026-07-31",
    )
    assert [
        session["scheduling"]["date"]
        for session in three_result["sessions"]
    ] == [
        "2026-08-01",
        "2026-08-03",
        "2026-08-05",
    ]

    # 5. Two sessions, only Monday and Wednesday -> both schedule.
    two_restricted = deepcopy(base_selection())
    two_restricted["planning_limits"]["max_sessions"] = 2
    two_restricted["planning_limits"]["available_days"] = [
        "monday",
        "wednesday",
    ]
    two_restricted["sessions"] = [
        make_session(1),
        make_session(2),
    ]
    two_restricted_result = schedule_weekly_plan(
        two_restricted,
        start_date="2026-07-31",
    )
    assert [
        session["scheduling"]["date"]
        for session in two_restricted_result["sessions"]
    ] == [
        "2026-08-03",
        "2026-08-05",
    ]
    assert two_restricted_result["plan_status"] == "ready"

    # Alternatives must not collide with another scheduled session.
    for session in two_restricted_result["sessions"]:
        alternatives = session["scheduling"]["flexibility"][
            "alternative_dates"
        ]
        assert alternatives == []

    # 6. More sessions than unique available dates -> partial, no stacking.
    overflow = deepcopy(two_restricted)
    overflow["planning_limits"]["max_sessions"] = 3
    overflow["sessions"] = [
        make_session(1),
        make_session(2),
        make_session(3),
    ]
    overflow_result = schedule_weekly_plan(
        overflow,
        start_date="2026-07-31",
    )
    assert overflow_result["plan_status"] == "partially_scheduled"
    assert overflow_result["scheduled_count"] == 2
    assert overflow_result["unscheduled_count"] == 1
    assert overflow_result["unscheduled_sessions"][0][
        "scheduling"
    ]["reason_code"] == "insufficient_unique_available_dates"

    # 7. Invalid day values only -> no valid date.
    invalid = deepcopy(base_selection())
    invalid["planning_limits"]["available_days"] = [
        "moon_day",
    ]
    invalid_result = schedule_weekly_plan(
        invalid,
        start_date="2026-07-31",
    )
    assert invalid_result["plan_status"] == "unscheduled"
    assert invalid_result["scheduled_count"] == 0
    assert invalid_result["unscheduled_sessions"][0][
        "scheduling"
    ]["reason_code"] == "no_valid_available_day"

    # 8. Turkish aliases normalize correctly.
    turkish = deepcopy(base_selection())
    turkish["planning_limits"]["available_days"] = [
        "Pazartesi",
        "Çarşamba",
    ]
    turkish_result = schedule_weekly_plan(
        turkish,
        start_date="2026-07-31",
    )
    assert turkish_result["availability_resolution"][
        "normalized_days"
    ] == ["monday", "wednesday"]
    assert turkish_result["sessions"][0][
        "scheduling"
    ]["date"] == "2026-08-03"

    # 9. Active illness/no structured training remains empty.
    illness = deepcopy(base_selection())
    illness["status"] = "no_structured_training"
    illness["sessions"] = []
    illness_result = schedule_weekly_plan(
        illness,
        start_date="2026-07-31",
    )
    assert illness_result["plan_status"] == "no_structured_training"
    assert illness_result["session_count"] == 0

    print("All weekly scheduling tests passed.")


if __name__ == "__main__":
    run_tests()
