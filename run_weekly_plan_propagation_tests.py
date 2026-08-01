from copy import deepcopy

from coach_engine.narration.llm_prompt import build_llm_coach_prompt
from coach_engine.reporting.weekly_markdown import render_weekly_review


def coach_context():
    return {
        "athlete": {
            "name": "Kamil",
            "primary_goal": "Endurance gelişimi",
            "weekly_target": {
                "running_sessions": 2,
                "cycling_sessions": 1,
                "strength_or_mobility_sessions": 1,
            },
            "constraints": [],
            "injury_risks": [],
        },
        "metrics": {
            "activity_count_7_days": 0,
            "activity_count_30_days": 6,
            "total_hours_7_days": 0.0,
            "total_hours_30_days": 3.47,
            "weekly_distance_km": 0.0,
            "monthly_distance_km": 31.55,
            "current_week_hours": 0.0,
            "rolling_30_weekly_hours": 0.81,
            "previous_23_weekly_hours": 1.06,
            "weekly_baseline_hours": 1.06,
            "load_ratio": 0.0,
            "running_sessions": 0,
            "cycling_sessions": 0,
            "avg_hr_7_days": None,
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
            "progression_advice": "Kolay biçimde yeniden düzen kur.",
            "running_decision": "restart_easy",
            "running_target_status": "below_target",
            "cycling_priority": "high",
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
            "health_constraint": "none",
            "recovery_constraint": "none",
            "life_constraint": "soft",
            "availability_constraint": "very_limited",
            "context_risk_level": "low",
            "intervals_blocked": False,
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
            "cycling_mode": "none",
            "cycling_session_text": None,
            "strength_or_mobility": "optional",
            "priority": "consistency",
            "weekly_intent": "maintain_consistency",
            "context_adjustment": "soft",
            "health_constraint": "none",
            "recovery_constraint": "none",
            "life_constraint": "soft",
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
            "reason": "Ritmi kolay koşuyla yeniden kur.",
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
        "planner_version": "0.1.0",
        "planning_engine": "rule_based_weekly_plan_v1",
        "plan_status": "ready",
        "planning_horizon": {
            "type": "rolling_7_days",
            "start_date": "2026-07-31",
            "end_date": "2026-08-06",
            "days": 7,
        },
        "week_focus": "maintain_consistency",
        "priority": "consistency",
        "scheduled_count": 1,
        "unscheduled_count": 0,
        "session_count": 1,
        "avoid": [
            "cycling",
            "interval",
            "tempo_run",
        ],
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
                    "primary_guidance": "conversational_effort",
                },
                "pace_guidance": {
                    "available": True,
                    "binding": False,
                    "target_reference_display": "6:34/km",
                    "range_display": {
                        "faster": "6:28/km",
                        "slower": "6:49/km",
                    },
                    "primary_guidance": "conversational_effort",
                    "note": "Kolay efor pace'ten önceliklidir.",
                },
                "distance_guidance": {
                    "available": True,
                    "binding": False,
                    "target_km": 5.3,
                    "range_km": {
                        "min": 4.4,
                        "max": 5.4,
                    },
                    "note": "Süre ve kolay efor önceliklidir.",
                },
                "add_ons": [
                    {
                        "type": "mobility_core",
                        "modality": "strength_or_mobility",
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
    assert "## Deterministik Haftalık Plan" in review
    assert "Pazartesi (2026-08-03) — Kolay koşu" in review
    assert "hedef 35 dk" in review
    assert "hedef 43 dk" in review
    assert "6:34/km" in review
    assert "6:28/km–6:49/km" in review
    assert "5.3 km" in review
    assert "Mobilite/Core" in review
    assert "Planner version: 0.1.0" in review

    prompt = build_llm_coach_prompt(
        context,
        weekly_plan=plan,
    )

    assert "WEEKLY PLAN — DEĞİŞTİRME:" in prompt
    assert '"date": "2026-08-03"' in prompt
    assert '"duration_target_min": 35' in prompt
    assert '"session_total_duration_target_min": 43' in prompt
    assert '"binding": false' in prompt
    assert '"target_km": 5.3' in prompt
    assert '"duration_target_min": 8' in prompt
    assert (
        "tarih, gün, seans türü, seans sayısı, süre, "
        "yoğunluk üst sınırı ve add-on kararlarını değiştirme"
    ) in prompt

    fallback_review = render_weekly_review(context)
    assert "Weekly plan artifact'i bulunamadı" in fallback_review

    fallback_prompt = build_llm_coach_prompt(context)
    assert '"available": false' in fallback_prompt
    assert '"plan_status": "unavailable"' in fallback_prompt
    assert "kesin tarih, süre, pace veya mesafe uydurma" in fallback_prompt

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

    illness_prompt = build_llm_coach_prompt(
        context,
        weekly_plan=illness_plan,
    )
    assert '"plan_status": "no_structured_training"' in illness_prompt
    assert (
        'plan_status "no_structured_training" ise hiçbir '
        "yapılandırılmış antrenman önermeme"
    ) in illness_prompt

    print("All weekly plan propagation tests passed.")


if __name__ == "__main__":
    run_tests()
