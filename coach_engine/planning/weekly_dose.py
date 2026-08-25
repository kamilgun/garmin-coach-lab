from __future__ import annotations

import math
from typing import Any, Dict, Iterable, Optional


WEEKLY_DOSE_SCHEMA_VERSION = "1.0"

CYCLING_MODALITY_KEYS = {
    "cycling",
    "bike",
    "trainer",
    "bike_or_trainer",
    "outdoor_bike",
    "indoor_trainer",
}


def _safe_int(
    value: Any,
    default: int = 0,
    minimum: int = 0,
) -> int:
    try:
        normalized = int(value)
    except (TypeError, ValueError):
        normalized = default

    return max(minimum, normalized)


def _safe_float(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _round_to_step(
    value: float,
    step: int = 5,
) -> int:
    if step <= 0:
        return round(value)

    return int(
        math.floor(
            (value + step / 2) / step
        )
        * step
    )


def _has_cycling(
    modalities: Iterable[str],
) -> bool:
    return bool(
        set(modalities or [])
        .intersection(CYCLING_MODALITY_KEYS)
    )


def _allocation_order(
    priority: Optional[str],
    weekly_intent: Optional[str],
) -> tuple[str, ...]:
    if weekly_intent == "recover":
        return (
            "strength_or_mobility",
            "cycling",
            "running",
        )

    if weekly_intent == "return_after_break":
        return (
            "running",
            "strength_or_mobility",
            "cycling",
        )

    if priority == "bike":
        return (
            "cycling",
            "running",
            "strength_or_mobility",
        )

    if priority == "recovery":
        return (
            "strength_or_mobility",
            "cycling",
            "running",
        )

    return (
        "running",
        "cycling",
        "strength_or_mobility",
    )


def _allocate_sessions(
    requested: Dict[str, int],
    capacity: int,
    order: tuple[str, ...],
) -> Dict[str, int]:
    remaining = max(0, capacity)

    resolved = {
        "running": 0,
        "cycling": 0,
        "strength_or_mobility": 0,
    }

    for modality in order:
        if remaining <= 0:
            break

        requested_count = requested.get(
            modality,
            0,
        )

        selected = min(
            requested_count,
            remaining,
        )

        resolved[modality] = selected
        remaining -= selected

    return resolved


def _legacy_requested_sessions(
    final_decision: Dict[str, Any],
    available_modalities: set[str],
) -> Dict[str, int]:
    running = (
        1
        if (
            "running" in available_modalities
            and final_decision.get("running")
            not in {None, "not_available"}
        )
        else 0
    )

    cycling = (
        1
        if (
            _has_cycling(available_modalities)
            and final_decision.get("cycling")
            not in {None, "not_available"}
            and final_decision.get("cycling_mode")
            != "none"
        )
        else 0
    )

    strength = (
        1
        if (
            "strength_or_mobility"
            in available_modalities
            and final_decision.get(
                "strength_or_mobility"
            )
            not in {
                None,
                "not_available",
                "not_recommended",
            }
        )
        else 0
    )

    return {
        "running": running,
        "cycling": cycling,
        "strength_or_mobility": strength,
    }


def resolve_weekly_dose(
    coach_context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Haftalık hedefi, yakın dönem antrenman geçmişini ve bu haftanın
    kesin planlama sınırlarını birleştirerek uygulanabilir seans dozunu
    belirler.

    Temel prensip:
    - weekly_target normal frekans hedefidir,
    - max_sessions kesin üst sınırdır,
    - dönüş haftasında önce intensity ve duration azaltılır,
    - yakın dönem temel varsa frekans mümkün olduğunca korunur.
    """

    if not isinstance(coach_context, dict):
        raise TypeError(
            "coach_context bir dict olmalı."
        )

    athlete = (
        coach_context.get("athlete")
        or {}
    )

    weekly_target = athlete.get(
        "weekly_target"
    )

    training_profile = (
        coach_context.get("training_profile")
        or {}
    )

    running_profile = (
        training_profile.get("running_30_days")
        or {}
    )

    final_decision = (
        coach_context.get("final_decision")
        or {}
    )

    context_signals = (
        coach_context.get("context_signals")
        or {}
    )

    limits = (
        final_decision.get("planning_limits")
        or {}
    )

    available_modalities = set(
        limits.get("available_modalities")
        or []
    )

    max_sessions = _safe_int(
        limits.get("max_sessions"),
        default=3,
        minimum=1,
    )

    max_session_duration_min = _safe_int(
        limits.get(
            "max_session_duration_min"
        ),
        default=50,
        minimum=1,
    )

    available_days = list(
        limits.get("available_days")
        or []
    )

    unique_available_days = list(
        dict.fromkeys(available_days)
    )

    effective_capacity = max_sessions

    if unique_available_days:
        effective_capacity = min(
            effective_capacity,
            len(unique_available_days),
        )

    weekly_intent = final_decision.get(
        "weekly_intent",
        context_signals.get(
            "weekly_intent"
        ),
    )

    priority = final_decision.get(
        "priority"
    )

    health_constraint = final_decision.get(
        "health_constraint",
        context_signals.get(
            "health_constraint",
            "none",
        ),
    )

    runs_analyzed = _safe_int(
        running_profile.get(
            "runs_analyzed"
        ),
        default=0,
    )

    median_run_duration = _safe_float(
        running_profile.get(
            "median_run_duration_min"
        )
    )

    recent_running_base = (
        runs_analyzed >= 2
    )

    reasons = []

    if health_constraint == "active_illness":
        return {
            "schema_version": WEEKLY_DOSE_SCHEMA_VERSION,
            "source": "safety_override",
            "weekly_intent": weekly_intent,
            "effective_capacity": 0,
            "requested_sessions": {
                "running": 0,
                "cycling": 0,
                "strength_or_mobility": 0,
            },
            "resolved_sessions": {
                "running": 0,
                "cycling": 0,
                "strength_or_mobility": 0,
            },
            "recent_running_base": {
                "runs_analyzed_30_days": runs_analyzed,
                "available": recent_running_base,
            },
            "frequency_policy": "no_structured_training",
            "running_duration_target_min": None,
            "reasons": [
                "Aktif hastalık nedeniyle yapılandırılmış antrenman dozu sıfırlandı."
            ],
        }

    has_explicit_weekly_target = isinstance(
        weekly_target,
        dict,
    )

    if has_explicit_weekly_target:
        requested = {
            "running": _safe_int(
                weekly_target.get(
                    "running_sessions"
                ),
                default=0,
            ),
            "cycling": _safe_int(
                weekly_target.get(
                    "cycling_sessions"
                ),
                default=0,
            ),
            "strength_or_mobility": _safe_int(
                weekly_target.get(
                    "strength_or_mobility_sessions"
                ),
                default=0,
            ),
        }

        source = "athlete_weekly_target"

    else:
        requested = _legacy_requested_sessions(
            final_decision,
            available_modalities,
        )

        source = "legacy_final_decision_fallback"

    running_available = (
        "running" in available_modalities
        and final_decision.get("running")
        != "not_available"
    )

    cycling_available = (
        _has_cycling(
            available_modalities
        )
        and final_decision.get("cycling")
        != "not_available"
        and final_decision.get(
            "cycling_mode"
        )
        != "none"
    )

    strength_available = (
        "strength_or_mobility"
        in available_modalities
        and final_decision.get(
            "strength_or_mobility"
        )
        not in {
            "not_available",
            "not_recommended",
        }
    )

    if not running_available:
        requested["running"] = 0

    if not cycling_available:
        requested["cycling"] = 0

    if not strength_available:
        requested[
            "strength_or_mobility"
        ] = 0

    frequency_policy = (
        "target_normal_frequency"
    )

    running_duration_target_min = None

    if weekly_intent == "return_after_break":
        if requested["running"] > 0:
            if recent_running_base:
                frequency_policy = (
                    "preserve_frequency_reduce_duration"
                )

                reasons.append(
                    "Yakın dönem koşu temeli bulunduğu için dönüş haftasında koşu frekansı mümkün olduğunca korunur."
                )

            else:
                requested["running"] = min(
                    requested["running"],
                    1,
                )

                frequency_policy = (
                    "reduce_frequency_and_duration"
                )

                reasons.append(
                    "Yakın dönem koşu temeli yetersiz olduğu için dönüş haftasında koşu frekansı azaltıldı."
                )

            if recent_running_base:
                if median_run_duration is not None:
                    duration_target = (
                        median_run_duration
                        * 0.65
                    )

                    duration_target = (
                        _round_to_step(
                            duration_target,
                            step=5,
                        )
                    )

                    duration_target = max(
                        25,
                        duration_target,
                    )

                    duration_target = min(
                        30,
                        duration_target,
                    )
                else:
                    duration_target = 30
            else:
                duration_target = 25

            running_duration_target_min = min(
                duration_target,
                max_session_duration_min,
            )

    elif weekly_intent == "recover":
        effective_capacity = min(
            effective_capacity,
            1,
        )

        frequency_policy = (
            "recovery_frequency_cap"
        )

        reasons.append(
            "Toparlanma niyeti nedeniyle standalone antrenman kapasitesi bir seansla sınırlandı."
        )

    if has_explicit_weekly_target:
        reasons.append(
            "Normal haftalık frekans hedefi athlete.weekly_target alanından alındı."
        )

    order = _allocation_order(
        priority,
        weekly_intent,
    )

    resolved = _allocate_sessions(
        requested,
        effective_capacity,
        order,
    )

    return {
        "schema_version": WEEKLY_DOSE_SCHEMA_VERSION,
        "source": source,
        "weekly_intent": weekly_intent,
        "priority": priority,
        "effective_capacity": effective_capacity,
        "requested_sessions": requested,
        "resolved_sessions": resolved,
        "recent_running_base": {
            "runs_analyzed_30_days": runs_analyzed,
            "available": recent_running_base,
        },
        "frequency_policy": frequency_policy,
        "running_duration_target_min": (
            running_duration_target_min
        ),
        "allocation_order": list(order),
        "reasons": reasons,
    }
