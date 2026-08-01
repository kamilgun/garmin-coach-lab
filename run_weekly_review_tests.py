from copy import deepcopy

from coach_engine.reporting.weekly_markdown import render_weekly_review


def coach_context():
    return {
        "schema_version": "2.0",
        "athlete": {
            "name": "Kamil",
            "primary_goal": "Endurance gelişimi",
            "weekly_target": {
                "running_sessions": 2,
                "cycling_sessions": 1,
                "strength_or_mobility_sessions": 1,
            },
        },
        "metrics": {
            "activity_count_7_days": 0,
            "activity_count_30_days": 6,
            "total_hours_7_days": 0.0,
            "total_hours_30_days": 3.47,
            "weekly_distance_km": 0.0,
            "monthly_distance_km": 31.55,
            "current_week_hours": 0.0,
            "weekly_baseline_hours": 1.06,
            "load_ratio": 0.0,
            "running_sessions": 0,
            "cycling_sessions": 0,
        },
        "training_profile": {
            "schema_version": "1.0",
            "data_available": True,
            "running_30_days": {
                "runs_analyzed": 6,
                "median_run_distance_km": 5.0,
                "median_run_duration_min": 32.5,
                "longest_run_distance_km": 7.54,
                "pace_distribution_display": {
                    "median": "6:34/km",
                },
            },
        },
        "performance": {
            "race_predictor": {
                "calendar_date": "2026-07-21",
                "5k": "0:24:20",
                "10k": "0:53:53",
                "half_marathon": "2:07:40",
                "marathon": "4:55:14",
            }
        },
        "rules": {
            "progression_label": "Ritim yeniden kurulmalı",
            "progression_advice": (
                "Kolay biçimde yeniden düzen kur."
            ),
            "intervals_allowed": False,
            "risk_level": "low",
            "training_load_risk_level": "low",
            "context_risk_level": "low",
        },
        "manual_context": {
            "schema_version": "2.0",
            "availability": {
                "available_days": [
                    "monday",
                    "tuesday",
                    "wednesday",
                    "thursday",
                    "friday",
                    "saturday",
                    "sunday",
                ],
                "max_sessions": 1,
                "max_session_duration_min": 45,
                "running_available": True,
                "outdoor_bike_available": False,
                "indoor_trainer_available": False,
                "strength_available": True,
            },
            "recovery": {
                "sleep_quality": "okay",
                "energy_level": "normal",
                "mental_fatigue": "medium",
                "muscle_soreness": "low",
                "illness_status": "none",
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
                "travel": True,
                "routine_disruption": "medium",
                "time_pressure": "normal",
                "emotional_load": "normal",
            },
            "weekly_intent": "maintain_consistency",
            "user_note": "",
        },
        "context_signals": {
            "adjustment_level": "soft",
            "available_modalities": [
                "running",
                "strength_or_mobility",
            ],
            "reasons": [
                "Bu hafta en fazla 1 antrenman gerçekçi.",
            ],
        },
        "final_decision": {
            "weekly_load": "restart_easy",
            "running": "easy_only",
            "cycling": "not_available",
            "strength_or_mobility": "optional",
            "priority": "consistency",
            "context_adjustment": "soft",
            "context_override_applied": False,
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
            "context_reasons": [
                "Bu hafta en fazla 1 antrenman gerçekçi.",
            ],
            "reason": (
                "Ritmi kolay koşuyla yeniden kur. "
                "Bu hafta en fazla 1 antrenman gerçekçi."
            ),
        },
        "metadata": {
            "engine_version": "0.6.0",
            "decision_engine": "rule_based_with_context_signals_v2",
            "generated_at": "2026-07-31T17:20:53",
        },
    }


def weekly_plan():
    return {
        "schema_version": "1.0",
        "generated_at": "2026-07-31T17:20:54",
        "planner_version": "0.1.0",
        "planning_engine": "rule_based_weekly_plan_v1",
        "planning_stage": "rolling_7_day_scheduling",
        "plan_status": "ready",
        "planning_horizon": {
            "type": "rolling_7_days",
            "start_date": "2026-07-31",
            "end_date": "2026-08-06",
            "days": 7,
        },
        "scheduled_count": 1,
        "unscheduled_count": 0,
        "session_count": 1,
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
                                "day_label_tr": "Pazar",
                            },
                            {
                                "date": "2026-08-04",
                                "day": "tuesday",
                                "day_label_tr": "Salı",
                            },
                        ]
                    },
                },
            }
        ],
        "unscheduled_sessions": [],
    }


def run_tests():
    context = coach_context()
    plan = weekly_plan()
    original_context = deepcopy(context)
    original_plan = deepcopy(plan)

    review = render_weekly_review(
        context,
        weekly_plan=plan,
    )

    assert context == original_context
    assert plan == original_plan

    expected_headings = [
        "## 1. Geçmiş Aktivite ve Yük",
        "## 2. Bu Haftanın Bağlamı",
        "## 3. Deterministik Karar",
        "## Deterministik Haftalık Plan",
        "## 5. Neden Bu Plan?",
        "## 6. Teknik Metadata",
    ]

    for heading in expected_headings:
        assert heading in review, heading

    removed_headings = [
        "## Koç Yorumu",
        "## Haftalık Hedef Durumu",
        "## Haftalık Check-in ve Yaşam Bağlamı",
        "## Yük ve Progression Sinyali",
        "## Performans Göstergeleri",
        "## Gelecek Hafta Uygulama Çerçevesi",
        "## Sistem Bilgisi",
    ]

    for heading in removed_headings:
        assert heading not in review, heading

    assert "Pazartesi (2026-08-03) — Kolay koşu" in review
    assert "hedef 35 dk" in review
    assert "hedef 43 dk" in review
    assert "6:34/km" in review
    assert "6:28/km–6:49/km" in review
    assert "5.3 km" in review
    assert "Mobilite/Core" in review
    assert "bağlayıcı değil" in review
    assert "Planner version: 0.1.0" in review
    assert "Planning engine: rule_based_weekly_plan_v1" in review

    repeated_reason = "Bu hafta en fazla 1 antrenman gerçekçi."
    assert review.count(repeated_reason) == 1

    fallback = render_weekly_review(context)
    assert "Weekly plan artifact'i bulunamadı" in fallback
    assert "Weekly plan artifact: Bulunamadı" in fallback

    illness_plan = {
        **plan,
        "plan_status": "no_structured_training",
        "sessions": [],
        "session_count": 0,
        "scheduled_count": 0,
        "unscheduled_count": 0,
    }
    illness_review = render_weekly_review(
        context,
        weekly_plan=illness_plan,
    )
    assert "yapılandırılmış antrenman planlanmadı" in illness_review

    print("All weekly review reporting tests passed.")


if __name__ == "__main__":
    run_tests()
