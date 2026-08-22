from copy import deepcopy

from coach_engine.presentation.weekly_plan_view import (
    build_weekly_plan_view_model,
)


def coach_context():
    return {
        "manual_context": {
            "weekly_intent": "race_specific",
            "availability": {
                "max_sessions": 4,
                "max_session_duration_min": 90,
            },
        },
        "final_decision": {
            "weekly_load": "restart_easy",
            "running": "easy_only",
            "cycling": "not_available",
            "priority": "consistency",
            "planning_limits": {
                "max_sessions": 4,
                "max_session_duration_min": 90,
                "available_modalities": [
                    "running",
                    "strength_or_mobility",
                ],
            },
            "reason": (
                "Ritmi kolay koşuyla yeniden kur. "
                "Bu hafta en fazla 1 antrenman gerçekçi."
            ),
            "context_reasons": [
                "Bu hafta en fazla 1 antrenman gerçekçi.",
            ],
        },
        "context_signals": {
            "reasons": [
                "Bisiklet ve trainer kullanılamıyor.",
            ]
        },
        "rules": {
            "intervals_allowed": False,
            "progression_advice": (
                "Koşu yükünü hızlı artırma."
            ),
        },
    }


def weekly_plan():
    return {
        "schema_version": "1.0",
        "generated_at": "2026-07-31T17:20:54",
        "planner_version": "0.1.0",
        "planning_engine": "rule_based_weekly_plan_v1",
        "plan_status": "ready",
        "planning_horizon": {
            "start_date": "2026-07-31",
            "end_date": "2026-08-06",
        },
        "sessions": [
            {
                "session_id": "session_1",
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
                "intensity": {
                    "cap": "easy",
                },
                "pace_guidance": {
                    "available": True,
                    "binding": False,
                    "target_reference_display": "6:34/km",
                    "range_display": {
                        "faster": "6:28/km",
                        "slower": "6:49/km",
                    },
                },
                "distance_guidance": {
                    "available": True,
                    "binding": False,
                    "target_km": 5.3,
                    "range_km": {
                        "min": 4.4,
                        "max": 5.4,
                    },
                },
                "add_ons": [
                    {
                        "type": "mobility_core",
                        "duration": {
                            "target_min": 8,
                            "min": 5,
                            "max": 10,
                        },
                    }
                ],
                "scheduling": {
                    "status": "scheduled",
                    "date": "2026-08-03",
                    "day": "monday",
                    "day_label_tr": "Pazartesi",
                    "flexibility": {
                        "alternative_dates": [
                            {
                                "date": "2026-08-02",
                                "day": "sunday",
                            },
                            {
                                "date": "2026-08-04",
                                "day": "tuesday",
                            },
                        ]
                    },
                },
            }
        ],
        "unscheduled_sessions": [],
    }


def test_ready_plan():
    context = coach_context()
    plan = weekly_plan()
    original_context = deepcopy(context)
    original_plan = deepcopy(plan)

    view = build_weekly_plan_view_model(
        context,
        plan,
    )

    assert context == original_context
    assert plan == original_plan

    assert view["status"] == "ready"
    assert view["status_label"] == "Plan hazır"
    assert view["focus"] == (
        "Ritmi kolay ve uygulanabilir seanslarla yeniden kur"
    )
    assert view["session_count"] == 1
    assert view["total_duration_min"] == 43
    assert view["horizon_label"] == (
        "31 Temmuz – 6 Ağustos"
    )

    applied = view["applied_context"]
    assert applied["weekly_intent"] == "race_specific"
    assert applied["weekly_intent_label"] == "Yarışa hazırlanmak"
    assert applied["max_sessions"] == 4
    assert applied["max_session_duration_min"] == 90
    assert applied["planned_session_count"] == 1
    assert "hedef değil" in applied["capacity_notice"]
    assert "Interval, tempo ve uzun koşu" in applied["intent_notice"]

    session = view["sessions"][0]
    assert session["title"] == "Kolay koşu"
    assert session["date_label"] == (
        "3 Ağustos Pazartesi"
    )
    assert session["main_duration"]["primary"] == "35 dk"
    assert session["total_duration"]["primary"] == "43 dk"
    assert session["effort_label"] == (
        "Kolay / konuşma temposu"
    )
    assert session["pace"]["label"] == (
        "6:28/km–6:49/km · referans 6:34/km · "
        "bağlayıcı değil"
    )
    assert session["distance"]["label"] == (
        "yaklaşık 4.4–5.4 km · referans 5.3 km · "
        "bağlayıcı değil"
    )
    assert session["add_ons"][0]["label"] == (
        "8 dk Mobilite / Core"
    )
    assert session["alternatives"] == [
        "2 Ağustos Pazar",
        "4 Ağustos Salı",
    ]

    duplicate_reason = (
        "Bu hafta en fazla 1 antrenman gerçekçi."
    )
    assert view["reasons"].count(duplicate_reason) == 1


def test_missing_plan():
    view = build_weekly_plan_view_model(
        coach_context(),
        None,
    )

    assert view["status"] == "missing"
    assert view["session_count"] == 0
    assert view["sessions"] == []


def test_no_structured_training():
    plan = weekly_plan()
    plan["plan_status"] = "no_structured_training"
    plan["sessions"] = []

    view = build_weekly_plan_view_model(
        coach_context(),
        plan,
    )

    assert view["status"] == "no_structured_training"
    assert "Toparlanmayı" in view["focus"]


def test_partially_scheduled():
    plan = weekly_plan()
    plan["plan_status"] = "partially_scheduled"
    plan["unscheduled_sessions"] = [
        {
            "session_id": "session_2",
            "type": "easy_z2_cycling",
            "scheduling": {
                "status": "unscheduled",
                "reason": "Uygun ikinci gün bulunamadı.",
            },
        }
    ]

    view = build_weekly_plan_view_model(
        coach_context(),
        plan,
    )

    assert view["status"] == "partially_scheduled"
    assert len(view["unscheduled_sessions"]) == 1
    assert (
        view["unscheduled_sessions"][0]["reason"]
        == "Uygun ikinci gün bulunamadı."
    )


def test_optional_guidance_missing():
    plan = weekly_plan()
    session = plan["sessions"][0]
    session["pace_guidance"] = {
        "available": False,
        "binding": False,
    }
    session["distance_guidance"] = {
        "available": False,
        "binding": False,
    }

    view = build_weekly_plan_view_model(
        coach_context(),
        plan,
    )

    session_view = view["sessions"][0]
    assert session_view["pace"] is None
    assert session_view["distance"] is None


def test_invalid_plan_shape():
    view = build_weekly_plan_view_model(
        coach_context(),
        {
            "plan_status": "ready",
            "sessions": "not-a-list",
            "unscheduled_sessions": [],
        },
    )

    assert view["status"] == "invalid"
    assert view["status_tone"] == "error"



def test_unscheduled_plan():
    plan = weekly_plan()
    plan["plan_status"] = "unscheduled"
    plan["sessions"] = []
    plan["unscheduled_sessions"] = [
        {
            "session_id": "session_1",
            "type": "easy_run",
            "scheduling": {
                "status": "unscheduled",
                "reason": "Seçilen günlerle planlanamadı.",
            },
        }
    ]

    view = build_weekly_plan_view_model(
        coach_context(),
        plan,
    )

    assert view["status"] == "unscheduled"
    assert view["session_count"] == 0
    assert len(view["unscheduled_sessions"]) == 1


def test_no_sessions_plan():
    plan = weekly_plan()
    plan["plan_status"] = "no_sessions"
    plan["sessions"] = []
    plan["unscheduled_sessions"] = []

    view = build_weekly_plan_view_model(
        coach_context(),
        plan,
    )

    assert view["status"] == "no_sessions"
    assert view["sessions"] == []
    assert view["unscheduled_sessions"] == []

def run_tests():
    test_ready_plan()
    test_missing_plan()
    test_no_structured_training()
    test_partially_scheduled()
    test_unscheduled_plan()
    test_no_sessions_plan()
    test_optional_guidance_missing()
    test_invalid_plan_shape()

    print("All weekly plan view-model tests passed.")


if __name__ == "__main__":
    run_tests()
