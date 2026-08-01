from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import math
from typing import Any, Dict, Iterable, List, Optional, Tuple


SESSION_SELECTION_SCHEMA_VERSION = "1.0"


def _unique(values: Iterable[str]) -> List[str]:
    result: List[str] = []

    for value in values:
        if value and value not in result:
            result.append(value)

    return result


def _safe_int(
    value: Any,
    default: int,
    minimum: Optional[int] = None,
    maximum: Optional[int] = None,
) -> int:
    try:
        normalized = int(value)
    except (TypeError, ValueError):
        normalized = default

    if minimum is not None:
        normalized = max(minimum, normalized)

    if maximum is not None:
        normalized = min(maximum, normalized)

    return normalized


def _safe_float(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _round_to_step(value: float, step: int = 5) -> int:
    if step <= 0:
        return round(value)

    return int(math.floor((value + step / 2) / step) * step)


def _clamp(value: int, minimum: int, maximum: int) -> int:
    if maximum < minimum:
        return maximum

    return max(minimum, min(maximum, value))


def _pace_display(seconds_per_km: Optional[float]) -> Optional[str]:
    if seconds_per_km is None:
        return None

    total_seconds = max(0, round(seconds_per_km))
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes}:{seconds:02d}/km"


def _candidate_rank(candidate: Dict[str, Any]) -> Tuple[int, int, str]:
    recommendation_order = {
        "recommended": 0,
        "optional": 1,
        "add_on": 2,
    }

    return (
        _safe_int(candidate.get("priority_rank"), 999, minimum=1),
        recommendation_order.get(candidate.get("recommendation"), 99),
        str(candidate.get("candidate_id") or ""),
    )


def _running_profile(coach_context: Dict[str, Any]) -> Dict[str, Any]:
    training_profile = coach_context.get("training_profile") or {}
    running = training_profile.get("running_30_days") or {}

    if not isinstance(running, dict):
        return {}

    return running


def _recent_runs(coach_context: Dict[str, Any]) -> List[Dict[str, Any]]:
    training_profile = coach_context.get("training_profile") or {}
    recent = training_profile.get("recent_runs") or []

    if not isinstance(recent, list):
        return []

    return [item for item in recent if isinstance(item, dict)]


def _duration_bounds(
    target: int,
    available_max: int,
    lower_delta: int,
    upper_delta: int,
    absolute_min: int,
) -> Dict[str, Any]:
    available_max = max(1, available_max)
    target = _clamp(target, min(absolute_min, available_max), available_max)

    minimum = max(
        min(absolute_min, available_max),
        target - lower_delta,
    )
    maximum = min(available_max, target + upper_delta)

    if maximum < target:
        target = maximum

    if minimum > target:
        minimum = target

    return {
        "target_min": target,
        "min": minimum,
        "max": maximum,
        "binding_max": True,
    }


def _running_duration(
    candidate: Dict[str, Any],
    coach_context: Dict[str, Any],
    available_max: int,
) -> Dict[str, Any]:
    profile = _running_profile(coach_context)
    observed_median = _safe_float(profile.get("median_run_duration_min"))
    source_decision = candidate.get("source_decision")

    if source_decision == "controlled_increase":
        base = observed_median * 1.10 if observed_median else 40
        policy_cap = 45
        method = "observed_median_plus_small_controlled_increase"
    elif source_decision == "maintain_easy":
        base = observed_median if observed_median else 35
        policy_cap = 40
        method = "maintain_observed_median"
    else:
        base = observed_median if observed_median else 30
        policy_cap = 35
        method = "restart_or_easy_only_from_observed_median"

    effective_max = min(available_max, policy_cap)
    target = _round_to_step(min(base, effective_max), step=5)

    guidance = _duration_bounds(
        target=target,
        available_max=effective_max,
        lower_delta=5,
        upper_delta=5,
        absolute_min=20,
    )
    guidance.update(
        {
            "method": method,
            "observed_median_duration_min": observed_median,
        }
    )
    return guidance


def _cycling_duration(
    candidate: Dict[str, Any],
    available_max: int,
) -> Dict[str, Any]:
    if candidate.get("intensity_cap") == "recovery":
        target = min(30, available_max)
        return {
            **_duration_bounds(
                target=_round_to_step(target, step=5),
                available_max=available_max,
                lower_delta=10,
                upper_delta=5,
                absolute_min=20,
            ),
            "method": "recovery_cycling_policy",
        }

    target = min(45, available_max)
    return {
        **_duration_bounds(
            target=_round_to_step(target, step=5),
            available_max=available_max,
            lower_delta=10,
            upper_delta=5,
            absolute_min=25,
        ),
        "method": "easy_z2_cycling_policy",
    }


def _mobility_duration(available_max: int) -> Dict[str, Any]:
    target = min(20, available_max)

    return {
        **_duration_bounds(
            target=_round_to_step(target, step=5),
            available_max=available_max,
            lower_delta=5,
            upper_delta=5,
            absolute_min=15,
        ),
        "method": "mobility_core_policy",
    }


def _duration_guidance(
    candidate: Dict[str, Any],
    coach_context: Dict[str, Any],
    available_max: int,
) -> Dict[str, Any]:
    modality = candidate.get("modality")

    if modality == "running":
        return _running_duration(candidate, coach_context, available_max)

    if modality in {
        "cycling",
        "indoor_trainer",
        "outdoor_bike",
    }:
        return _cycling_duration(candidate, available_max)

    return _mobility_duration(available_max)


def _pace_guidance(
    candidate: Dict[str, Any],
    coach_context: Dict[str, Any],
) -> Dict[str, Any]:
    if candidate.get("modality") != "running":
        return {
            "available": False,
            "reason": "Pace rehberi bu seans türü için uygulanabilir değil.",
        }

    profile = _running_profile(coach_context)
    distribution = profile.get("pace_distribution_sec_per_km") or {}

    median_sec = _safe_float(distribution.get("median"))
    p25_sec = _safe_float(distribution.get("faster_quartile_p25"))
    p75_sec = _safe_float(distribution.get("slower_quartile_p75"))

    if median_sec is None:
        candidate_reference = candidate.get("training_reference") or {}
        display_value = candidate_reference.get("observed_median_pace")

        return {
            "available": False,
            "observed_median_display": display_value,
            "reason": (
                "Sayısal pace dağılımı bulunmadığı için güvenilir aralık "
                "hesaplanamadı."
            ),
        }

    faster_sec = max(
        p25_sec if p25_sec is not None else median_sec,
        median_sec - 10,
    )
    slower_sec = max(
        p75_sec if p75_sec is not None else median_sec,
        median_sec + 15,
    )

    if slower_sec <= faster_sec:
        slower_sec = faster_sec + 15

    recent = _recent_runs(coach_context)
    lower_hr_runs = []

    valid_hr_runs = [
        run
        for run in recent
        if _safe_float(run.get("avg_hr")) is not None
        and _safe_float(run.get("avg_pace_sec_per_km")) is not None
    ]

    if valid_hr_runs:
        sorted_by_hr = sorted(
            valid_hr_runs,
            key=lambda run: _safe_float(run.get("avg_hr")) or 999,
        )
        lower_half_size = max(1, math.ceil(len(sorted_by_hr) / 2))
        lower_hr_runs = sorted_by_hr[:lower_half_size]

    lower_hr_paces = [
        _safe_float(run.get("avg_pace_sec_per_km"))
        for run in lower_hr_runs
    ]
    lower_hr_paces = [
        value for value in lower_hr_paces if value is not None
    ]

    lower_hr_reference = None
    if lower_hr_paces:
        ordered = sorted(lower_hr_paces)
        middle = len(ordered) // 2

        if len(ordered) % 2:
            lower_hr_reference = ordered[middle]
        else:
            lower_hr_reference = (
                ordered[middle - 1] + ordered[middle]
            ) / 2

        slower_sec = max(slower_sec, lower_hr_reference)

    return {
        "available": True,
        "type": "observed_reference",
        "primary_guidance": "conversational_effort",
        "binding": False,
        "target_reference_sec_per_km": round(median_sec),
        "target_reference_display": _pace_display(median_sec),
        "range_sec_per_km": {
            "faster": round(faster_sec),
            "slower": round(slower_sec),
        },
        "range_display": {
            "faster": _pace_display(faster_sec),
            "slower": _pace_display(slower_sec),
        },
        "source": "running_profile_30_days_and_recent_runs",
        "lower_hr_reference_sec_per_km": (
            round(lower_hr_reference)
            if lower_hr_reference is not None
            else None
        ),
        "lower_hr_reference_display": _pace_display(lower_hr_reference),
        "note": (
            "Bu aralık yakın dönem koşularından türetilmiş bağlayıcı olmayan "
            "bir referanstır. Kolay, konuşma temposundaki efor pace'ten "
            "önceliklidir."
        ),
    }


def _distance_guidance(
    candidate: Dict[str, Any],
    duration: Dict[str, Any],
    pace: Dict[str, Any],
) -> Dict[str, Any]:
    if candidate.get("modality") != "running":
        return {
            "available": False,
            "reason": (
                "Bisiklet/trainer ve mobilite seanslarında süre ve efor "
                "mesafeden daha güvenilir birincil rehberdir."
            ),
        }

    if not pace.get("available"):
        return {
            "available": False,
            "reason": (
                "Pace referansı bulunmadığı için mesafe aralığı "
                "hesaplanmadı."
            ),
        }

    median_pace = pace["target_reference_sec_per_km"]
    faster_pace = pace["range_sec_per_km"]["faster"]
    slower_pace = pace["range_sec_per_km"]["slower"]

    minimum_km = duration["min"] * 60 / slower_pace
    target_km = duration["target_min"] * 60 / median_pace
    maximum_km = duration["max"] * 60 / faster_pace

    return {
        "available": True,
        "type": "approximate_from_duration_and_observed_pace",
        "binding": False,
        "target_km": round(target_km, 1),
        "range_km": {
            "min": round(minimum_km, 1),
            "max": round(maximum_km, 1),
        },
        "note": (
            "Mesafe yaklaşık bir sonuçtur. Süre sınırı ve kolay efor "
            "mesafe hedefinden önceliklidir."
        ),
    }


def _intensity_guidance(candidate: Dict[str, Any]) -> Dict[str, Any]:
    intensity_cap = candidate.get("intensity_cap")

    primary_map = {
        "easy": "conversational_effort",
        "easy_z2": "steady_easy_z2_effort",
        "recovery": "very_easy_recovery_effort",
        "light": "light_controlled_mobility",
    }

    return {
        "cap": intensity_cap,
        "primary_guidance": primary_map.get(
            intensity_cap,
            "controlled_effort",
        ),
        "binding_cap": True,
        "no_unplanned_intensity": True,
    }


def _minimum_main_duration(candidate: Dict[str, Any]) -> int:
    if candidate.get("modality") in {
        "running",
        "cycling",
        "indoor_trainer",
        "outdoor_bike",
    }:
        return 20

    return 15


def _add_on_duration(
    main_candidate: Dict[str, Any],
    max_session_duration_min: int,
) -> Optional[Dict[str, Any]]:
    available_for_add_on = (
        max_session_duration_min
        - _minimum_main_duration(main_candidate)
    )

    if available_for_add_on < 5:
        return None

    target = 8 if available_for_add_on >= 8 else 5

    return {
        "target_min": target,
        "min": 5,
        "max": min(10, available_for_add_on),
        "binding_max": True,
        "method": "mobility_add_on_policy",
    }


def _build_add_on(
    candidate: Dict[str, Any],
    duration: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "source_candidate_id": candidate.get("candidate_id"),
        "type": candidate.get("session_type"),
        "modality": candidate.get("modality"),
        "duration": duration,
        "intensity": _intensity_guidance(candidate),
        "reason": candidate.get("reason"),
    }


def _build_session(
    session_number: int,
    candidate: Dict[str, Any],
    coach_context: Dict[str, Any],
    max_session_duration_min: int,
    add_ons: List[Dict[str, Any]],
) -> Dict[str, Any]:
    reserved_add_on_target = sum(
        item["duration"]["target_min"] for item in add_ons
    )
    reserved_add_on_max = sum(
        item["duration"]["max"] for item in add_ons
    )

    available_main_max = max(
        1,
        max_session_duration_min - reserved_add_on_max,
    )

    duration = _duration_guidance(
        candidate,
        coach_context,
        available_main_max,
    )
    pace = _pace_guidance(candidate, coach_context)
    distance = _distance_guidance(candidate, duration, pace)

    total_target = duration["target_min"] + reserved_add_on_target
    total_min = duration["min"] + sum(
        item["duration"]["min"] for item in add_ons
    )
    total_max = min(
        max_session_duration_min,
        duration["max"] + reserved_add_on_max,
    )

    return {
        "session_id": f"session_{session_number}",
        "source_candidate_id": candidate.get("candidate_id"),
        "modality": candidate.get("modality"),
        "type": candidate.get("session_type"),
        "recommendation": candidate.get("recommendation"),
        "priority_rank": candidate.get("priority_rank"),
        "source_decision": candidate.get("source_decision"),
        "duration": duration,
        "session_total_duration": {
            "target_min": total_target,
            "min": total_min,
            "max": total_max,
            "binding_max": True,
        },
        "intensity": _intensity_guidance(candidate),
        "pace_guidance": pace,
        "distance_guidance": distance,
        "add_ons": add_ons,
        "reason": candidate.get("reason"),
        "scheduling": {
            "status": "not_scheduled",
            "note": "Gün ve tarih ataması Phase 8.0E'de yapılacak.",
        },
    }


def select_sessions(
    coach_context: Dict[str, Any],
    candidate_artifact: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Aday havuzundan kapasiteye uygun seansları seçer ve reçetelendirir.

    Bu katman:
    - max_sessions sınırını uygular,
    - priority_rank sırasına göre standalone adayları seçer,
    - add-on adaylarını uygun ana seansa bağlar,
    - süre/intensity/pace/mesafe rehberi üretir,
    - gün veya tarih atamaz.
    """

    if not isinstance(coach_context, dict):
        raise TypeError("coach_context bir dict olmalı.")

    if not isinstance(candidate_artifact, dict):
        raise TypeError("candidate_artifact bir dict olmalı.")

    limits = candidate_artifact.get("planning_limits") or {}
    max_sessions = _safe_int(
        limits.get("max_sessions"),
        default=1,
        minimum=1,
    )
    max_session_duration_min = _safe_int(
        limits.get("max_session_duration_min"),
        default=45,
        minimum=1,
    )

    base_output = {
        "schema_version": SESSION_SELECTION_SCHEMA_VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_candidate_schema_version": candidate_artifact.get(
            "schema_version"
        ),
        "source_candidate_generated_at": candidate_artifact.get(
            "generated_at"
        ),
        "source_engine_version": candidate_artifact.get(
            "source_engine_version"
        ),
        "weekly_intent": candidate_artifact.get("weekly_intent"),
        "priority": candidate_artifact.get("priority"),
        "planning_limits": deepcopy(limits),
        "selection_policy": {
            "standalone_order": "candidate_priority_rank",
            "max_sessions_binding": True,
            "duration_limit_binding": True,
            "pace_binding": False,
            "distance_binding": False,
            "add_on_counts_as_standalone_session": False,
            "scheduling_included": False,
        },
        "avoid": deepcopy(candidate_artifact.get("avoid") or []),
        "reasons": deepcopy(candidate_artifact.get("reasons") or []),
    }

    if candidate_artifact.get("status") == "no_structured_training":
        return {
            **base_output,
            "status": "no_structured_training",
            "sessions": [],
            "session_count": 0,
            "selected_candidate_ids": [],
            "not_selected": deepcopy(
                candidate_artifact.get("blocked_candidates") or []
            ),
            "selection_summary": {
                "standalone_selected": 0,
                "add_ons_selected": 0,
                "capacity_used": 0,
                "capacity_limit": max_sessions,
            },
        }

    candidates = [
        candidate
        for candidate in candidate_artifact.get("candidates", [])
        if isinstance(candidate, dict)
    ]

    standalone = sorted(
        [
            candidate
            for candidate in candidates
            if candidate.get("delivery_mode") == "standalone"
        ],
        key=_candidate_rank,
    )
    add_on_candidates = sorted(
        [
            candidate
            for candidate in candidates
            if candidate.get("delivery_mode") == "add_on"
        ],
        key=_candidate_rank,
    )

    selected_standalone = standalone[:max_sessions]
    not_selected: List[Dict[str, Any]] = []

    for candidate in standalone[max_sessions:]:
        not_selected.append(
            {
                "candidate_id": candidate.get("candidate_id"),
                "modality": candidate.get("modality"),
                "reason_code": "standalone_capacity_limit",
                "reason": (
                    "Aday geçerli ancak max_sessions sınırı nedeniyle bu "
                    "plan taslağına seçilmedi."
                ),
            }
        )

    attached_add_ons: Dict[str, List[Dict[str, Any]]] = {
        str(candidate.get("candidate_id")): []
        for candidate in selected_standalone
    }

    add_ons_selected = 0

    for add_on_candidate in add_on_candidates:
        if not selected_standalone:
            not_selected.append(
                {
                    "candidate_id": add_on_candidate.get("candidate_id"),
                    "modality": add_on_candidate.get("modality"),
                    "reason_code": "no_selected_main_session",
                    "reason": (
                        "Add-on için bağlanabileceği seçilmiş bir ana seans "
                        "bulunmadı."
                    ),
                }
            )
            continue

        main_candidate = selected_standalone[0]
        add_on_duration = _add_on_duration(
            main_candidate,
            max_session_duration_min,
        )

        if add_on_duration is None:
            not_selected.append(
                {
                    "candidate_id": add_on_candidate.get("candidate_id"),
                    "modality": add_on_candidate.get("modality"),
                    "reason_code": "insufficient_session_duration",
                    "reason": (
                        "Ana seansın anlamlı minimum süresini koruyarak "
                        "add-on için yeterli süre ayrılamadı."
                    ),
                }
            )
            continue

        main_key = str(main_candidate.get("candidate_id"))
        attached_add_ons[main_key].append(
            _build_add_on(add_on_candidate, add_on_duration)
        )
        add_ons_selected += 1

    sessions = []

    for index, candidate in enumerate(selected_standalone, start=1):
        candidate_key = str(candidate.get("candidate_id"))
        sessions.append(
            _build_session(
                session_number=index,
                candidate=candidate,
                coach_context=coach_context,
                max_session_duration_min=max_session_duration_min,
                add_ons=attached_add_ons.get(candidate_key, []),
            )
        )

    selected_candidate_ids = [
        session["source_candidate_id"] for session in sessions
    ]

    for session in sessions:
        selected_candidate_ids.extend(
            add_on["source_candidate_id"]
            for add_on in session.get("add_ons", [])
        )

    status = "ready" if sessions else "no_session_selected"

    return {
        **base_output,
        "status": status,
        "sessions": sessions,
        "session_count": len(sessions),
        "selected_candidate_ids": selected_candidate_ids,
        "not_selected": not_selected,
        "selection_summary": {
            "standalone_selected": len(sessions),
            "add_ons_selected": add_ons_selected,
            "capacity_used": len(sessions),
            "capacity_limit": max_sessions,
        },
    }
