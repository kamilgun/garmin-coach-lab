from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional
from coach_engine.planning.weekly_dose import (
    resolve_weekly_dose,
)


SESSION_CANDIDATE_SCHEMA_VERSION = "1.0"

CYCLING_MODALITY_KEYS = {
    "cycling",
    "bike",
    "trainer",
    "bike_or_trainer",
    "outdoor_bike",
    "indoor_trainer",
}


def _unique(values: Iterable[str]) -> List[str]:
    result = []

    for value in values:
        if value and value not in result:
            result.append(value)

    return result


def _safe_int(value: Any, default: int, minimum: int = 0) -> int:
    try:
        normalized = int(value)
    except (TypeError, ValueError):
        normalized = default

    return max(minimum, normalized)


def _planning_limits(coach_context: Dict[str, Any]) -> Dict[str, Any]:
    final_decision = coach_context.get("final_decision", {})
    context_signals = coach_context.get("context_signals", {})
    manual_context = coach_context.get("manual_context", {})
    availability = manual_context.get("availability", {})

    source = final_decision.get("planning_limits") or {}

    max_sessions = _safe_int(
        source.get(
            "max_sessions",
            context_signals.get(
                "max_sessions",
                availability.get("max_sessions", 3),
            ),
        ),
        default=3,
        minimum=1,
    )

    max_session_duration_min = _safe_int(
        source.get(
            "max_session_duration_min",
            context_signals.get(
                "max_session_duration_min",
                availability.get("max_session_duration_min", 50),
            ),
        ),
        default=50,
        minimum=1,
    )

    available_days = source.get(
        "available_days",
        context_signals.get(
            "available_days",
            availability.get("available_days", []),
        ),
    )
    available_days = list(available_days or [])

    available_modalities = source.get(
        "available_modalities",
        context_signals.get("available_modalities", []),
    )
    available_modalities = list(available_modalities or [])

    return {
        "max_sessions": max_sessions,
        "max_session_duration_min": max_session_duration_min,
        "available_days": available_days,
        "available_modalities": available_modalities,
    }


def _running_reference(training_profile: Dict[str, Any]) -> Dict[str, Any]:
    running = training_profile.get("running_30_days") or {}
    pace_display = running.get("pace_distribution_display") or {}

    return {
        "data_available": bool(training_profile.get("data_available")),
        "runs_analyzed": running.get("runs_analyzed", 0),
        "median_run_duration_min": running.get("median_run_duration_min"),
        "median_run_distance_km": running.get("median_run_distance_km"),
        "longest_run_duration_min": running.get("longest_run_duration_min"),
        "longest_run_distance_km": running.get("longest_run_distance_km"),
        "observed_median_pace": pace_display.get("median"),
        "reference_only": True,
    }


def _candidate(
    *,
    candidate_id: str,
    modality: str,
    session_type: str,
    recommendation: str,
    intensity_cap: str,
    delivery_mode: str,
    capacity_cost: int,
    source_decision: str,
    reason: str,
    training_reference: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    candidate = {
        "candidate_id": candidate_id,
        "modality": modality,
        "session_type": session_type,
        "recommendation": recommendation,
        "intensity_cap": intensity_cap,
        "delivery_mode": delivery_mode,
        "standalone_capacity_cost": capacity_cost,
        "source_decision": source_decision,
        "reason": reason,
    }

    if training_reference is not None:
        candidate["training_reference"] = training_reference

    return candidate


def _cycling_modality(cycling_mode: Optional[str]) -> str:
    if cycling_mode == "trainer":
        return "indoor_trainer"

    if cycling_mode == "bike":
        return "outdoor_bike"

    return "cycling"


def _cycling_is_available(
    available_modalities: Iterable[str],
    cycling_mode: Optional[str],
) -> bool:
    modalities = set(available_modalities or [])

    if cycling_mode == "none":
        return False

    if modalities.intersection(CYCLING_MODALITY_KEYS):
        return True

    return False


def _priority_order(
    priority: Optional[str],
    weekly_intent: Optional[str],
) -> Dict[str, int]:
    if weekly_intent == "recover":
        return {
            "strength_or_mobility": 10,
            "cycling": 20,
            "indoor_trainer": 20,
            "outdoor_bike": 20,
            "running": 30,
        }

    if weekly_intent == "return_after_break":
        return {
            "running": 10,
            "strength_or_mobility": 20,
            "cycling": 30,
            "indoor_trainer": 30,
            "outdoor_bike": 30,
        }

    if priority == "bike":
        return {
            "cycling": 10,
            "indoor_trainer": 10,
            "outdoor_bike": 10,
            "running": 20,
            "strength_or_mobility": 30,
        }

    if priority == "recovery":
        return {
            "strength_or_mobility": 10,
            "cycling": 20,
            "indoor_trainer": 20,
            "outdoor_bike": 20,
            "running": 30,
        }

    return {
        "running": 10,
        "cycling": 20,
        "indoor_trainer": 20,
        "outdoor_bike": 20,
        "strength_or_mobility": 30,
    }


def _sort_and_rank(
    candidates: List[Dict[str, Any]],
    priority: Optional[str],
    weekly_intent: Optional[str],
) -> List[Dict[str, Any]]:
    order = _priority_order(priority, weekly_intent)
    recommendation_order = {
        "recommended": 0,
        "optional": 1,
        "add_on": 2,
    }

    sorted_candidates = sorted(
        candidates,
        key=lambda item: (
            order.get(item["modality"], 99),
            recommendation_order.get(item["recommendation"], 99),
            item["candidate_id"],
        ),
    )

    for rank, candidate in enumerate(sorted_candidates, start=1):
        candidate["priority_rank"] = rank

    return sorted_candidates


def _blocked(
    candidate_id: str,
    modality: str,
    source_decision: Optional[str],
    reason: str,
) -> Dict[str, Any]:
    return {
        "candidate_id": candidate_id,
        "modality": modality,
        "source_decision": source_decision,
        "reason": reason,
    }


def build_session_candidates(
    coach_context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Coach Context -> deterministik seans adayları.

    Bu katman:
    - kesin haftalık planı seçmez,
    - tarih atamaz,
    - süre/mesafe/pace reçetesi üretmez,
    - LLM kullanmaz.

    Yalnızca final_decision ve planning_limits ile uyumlu aday havuzunu
    üretir. Seçim ve ayrıntılandırma sonraki planning katmanlarının işidir.
    """

    if not isinstance(coach_context, dict):
        raise TypeError("coach_context bir dict olmalı.")

    final_decision = coach_context.get("final_decision") or {}
    rules = coach_context.get("rules") or {}
    context_signals = coach_context.get("context_signals") or {}
    training_profile = coach_context.get("training_profile") or {}
    metadata = coach_context.get("metadata") or {}

    limits = _planning_limits(coach_context)
    available_modalities = set(limits["available_modalities"])

    weekly_dose = resolve_weekly_dose(
        coach_context
    )

    dose_source = weekly_dose.get("source")

    dose_driven = (
        dose_source == "athlete_weekly_target"
    )

    dose_requested = (
        weekly_dose.get("requested_sessions")
        or {}
    )

    dose_resolved = (
        weekly_dose.get("resolved_sessions")
        or {}
    )


    def resolved_dose_count(
        modality: str,
        legacy_default: int,
    ) -> int:
        if not dose_driven:
            return legacy_default

        return _safe_int(
            dose_resolved.get(modality),
            default=0,
            minimum=0,
        )

    weekly_intent = final_decision.get(
        "weekly_intent",
        context_signals.get("weekly_intent"),
    )
    priority = final_decision.get("priority")
    health_constraint = final_decision.get(
        "health_constraint",
        context_signals.get("health_constraint", "none"),
    )

    candidates: List[Dict[str, Any]] = []
    blocked_candidates: List[Dict[str, Any]] = []
    avoid: List[str] = []
    reasons: List[str] = []

    context_reasons = final_decision.get(
        "context_reasons",
        context_signals.get("reasons", []),
    )
    reasons.extend(context_reasons or [])

    final_reason = final_decision.get("reason")
    if final_reason:
        reasons.append(final_reason)

    # Hard stop: active illness means no structured training candidate.
    if health_constraint == "active_illness":
        blocked_candidates.extend(
            [
                _blocked(
                    "running_easy",
                    "running",
                    final_decision.get("running"),
                    "Aktif hastalık nedeniyle yapılandırılmış koşu adayı oluşturulmadı.",
                ),
                _blocked(
                    "cycling_easy",
                    "cycling",
                    final_decision.get("cycling"),
                    "Aktif hastalık nedeniyle bisiklet/trainer adayı oluşturulmadı.",
                ),
                _blocked(
                    "mobility_core",
                    "strength_or_mobility",
                    final_decision.get("strength_or_mobility"),
                    "Aktif hastalık nedeniyle yapılandırılmış destek seansı oluşturulmadı.",
                ),
            ]
        )

        avoid.extend(
            [
                "structured_training",
                "interval",
                "tempo_run",
                "long_run",
                "extra_session",
            ]
        )

        return {
            "schema_version": SESSION_CANDIDATE_SCHEMA_VERSION,
            "status": "no_structured_training",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "source_engine_version": metadata.get("engine_version"),
            "weekly_intent": weekly_intent,
            "priority": priority,
            "planning_limits": deepcopy(limits),
            "weekly_dose": deepcopy(weekly_dose),
            "planner_policy": {
                "interval_candidates_enabled": False,
                "tempo_candidates_enabled": False,
                "long_run_candidates_enabled": False,
                "pace_or_distance_binding": False,
            },
            "candidates": [],
            "candidate_count": 0,
            "standalone_capacity_requested": 0,
            "standalone_capacity_limit": limits["max_sessions"],
            "selection_required": False,
            "blocked_candidates": blocked_candidates,
            "avoid": _unique(avoid),
            "reasons": _unique(reasons),
        }

    running_decision = final_decision.get("running")
    running_available = (
        "running" in available_modalities
        and running_decision != "not_available"
    )

    if running_available:
        if running_decision in {
            "easy_only",
            "maintain_easy",
            "controlled_increase",
        }:
            reason_map = {
                "easy_only": (
                    "Final karar koşuyu yalnızca kolay eforla sınırlandırıyor."
                ),
                "maintain_easy": (
                    "Final karar mevcut kolay koşu ritminin korunmasını istiyor."
                ),
                "controlled_increase": (
                    "Final karar yalnızca kontrollü bir artışa izin veriyor; "
                    "ilk aday yine kolay koşudur."
                ),
            }

            running_count = resolved_dose_count(
                "running",
                legacy_default=1,
            )

            if running_count == 0:
                blocked_candidates.append(
                    _blocked(
                        "running_easy",
                        "running",
                        running_decision,
                        (
                            "Weekly dose resolver bu hafta "
                            "standalone koşu seansı ayırmadı."
                        ),
                    )
                )

            else:
                for index in range(
                    1,
                    running_count + 1,
                ):
                    candidate_id = (
                        "running_easy"
                        if index == 1
                        else f"running_easy_{index}"
                    )

                    candidate = _candidate(
                        candidate_id=candidate_id,
                        modality="running",
                        session_type="easy_run",
                        recommendation="recommended",
                        intensity_cap="easy",
                        delivery_mode="standalone",
                        capacity_cost=1,
                        source_decision=running_decision,
                        reason=reason_map[
                            running_decision
                        ],
                        training_reference=(
                            _running_reference(
                                training_profile
                            )
                        ),
                    )

                    if dose_driven:
                        candidate["dose_sequence"] = {
                            "index": index,
                            "target_count": (
                                running_count
                            ),
                        }

                        duration_hint = (
                            weekly_dose.get(
                                "running_duration_target_min"
                            )
                        )

                        if duration_hint is not None:
                            candidate[
                                "duration_target_hint_min"
                            ] = duration_hint

                    candidates.append(candidate)
        else:
            blocked_candidates.append(
                _blocked(
                    "running_easy",
                    "running",
                    running_decision,
                    "Running decision desteklenen bir aday tipine dönüşmedi.",
                )
            )
    else:
        blocked_candidates.append(
            _blocked(
                "running_easy",
                "running",
                running_decision,
                (
                    "Koşu planning_limits içinde kullanılabilir değil."
                    if "running" not in available_modalities
                    else "Final karar koşuyu uygun görmüyor."
                ),
            )
        )
        avoid.append("running")

    cycling_decision = final_decision.get("cycling")
    cycling_mode = final_decision.get("cycling_mode")
    cycling_available = (
        _cycling_is_available(available_modalities, cycling_mode)
        and cycling_decision != "not_available"
    )

    if cycling_available:
        cycling_modality = _cycling_modality(cycling_mode)

        cycling_map = {
            "add_easy_z2": {
                "candidate_id": "cycling_easy_z2",
                "session_type": "easy_z2_cycling",
                "recommendation": "recommended",
                "intensity_cap": "easy_z2",
                "reason": "Final karar kolay Z2 bisiklet/trainer yükünü öneriyor.",
            },
            "add_or_maintain_z2": {
                "candidate_id": "cycling_easy_z2",
                "session_type": "easy_z2_cycling",
                "recommendation": "recommended",
                "intensity_cap": "easy_z2",
                "reason": "Final karar kolay Z2 bisiklet/trainer ritmini eklemeyi veya korumayı öneriyor.",
            },
            "optional_easy_z2": {
                "candidate_id": "cycling_optional_easy_z2",
                "session_type": "easy_z2_cycling",
                "recommendation": "optional",
                "intensity_cap": "easy_z2",
                "reason": "Final karar bisiklet/trainer seansını opsiyonel kolay Z2 olarak tutuyor.",
            },
            "optional_recovery": {
                "candidate_id": "cycling_optional_recovery",
                "session_type": "recovery_cycling",
                "recommendation": "optional",
                "intensity_cap": "recovery",
                "reason": "Final karar yalnızca opsiyonel toparlanma sürüşüne izin veriyor.",
            },
            "recovery_only": {
                "candidate_id": "cycling_recovery",
                "session_type": "recovery_cycling",
                "recommendation": "recommended",
                "intensity_cap": "recovery",
                "reason": "Final karar bisiklet/trainer seansını toparlanma yoğunluğuyla sınırlandırıyor.",
            },
        }

        config = cycling_map.get(cycling_decision)

        if config:
            cycling_count = resolved_dose_count(
                "cycling",
                legacy_default=1,
            )

            for index in range(
                1,
                cycling_count + 1,
            ):
                base_candidate_id = (
                    config["candidate_id"]
                )

                candidate_id = (
                    base_candidate_id
                    if index == 1
                    else (
                        f"{base_candidate_id}_{index}"
                    )
                )

                candidate = _candidate(
                    candidate_id=candidate_id,
                    modality=cycling_modality,
                    session_type=config[
                        "session_type"
                    ],
                    recommendation=config[
                        "recommendation"
                    ],
                    intensity_cap=config[
                        "intensity_cap"
                    ],
                    delivery_mode="standalone",
                    capacity_cost=1,
                    source_decision=cycling_decision,
                    reason=config["reason"],
                )

                if dose_driven:
                    candidate["dose_sequence"] = {
                        "index": index,
                        "target_count": (
                            cycling_count
                        ),
                    }

                candidates.append(candidate)
        else:
            blocked_candidates.append(
                _blocked(
                    "cycling_easy",
                    cycling_modality,
                    cycling_decision,
                    "Cycling decision desteklenen bir aday tipine dönüşmedi.",
                )
            )
    else:
        blocked_candidates.append(
            _blocked(
                "cycling_easy",
                _cycling_modality(cycling_mode),
                cycling_decision,
                (
                    "Bisiklet/trainer planning_limits içinde kullanılabilir değil."
                    if not _cycling_is_available(
                        available_modalities,
                        cycling_mode,
                    )
                    else "Final karar bisiklet/trainer seansını uygun görmüyor."
                ),
            )
        )
        avoid.append("cycling")

    strength_decision = final_decision.get("strength_or_mobility")
    strength_available = (
        "strength_or_mobility" in available_modalities
        and strength_decision != "not_recommended"
    )

    has_main_candidate = any(
        candidate["modality"] != "strength_or_mobility"
        and candidate["delivery_mode"] == "standalone"
        for candidate in candidates
    )

    strength_count = resolved_dose_count(
        "strength_or_mobility",
        legacy_default=1,
    )

    strength_requested = (
        _safe_int(
            dose_requested.get(
                "strength_or_mobility"
            ),
            default=0,
            minimum=0,
        )
        if dose_driven
        else 1
    )

    if (
        strength_available
        and strength_decision in {
            "recommended",
            "recommended_light",
            "optional",
        }
        and (
            strength_count > 0
            or (
                limits["max_sessions"] == 1
                and has_main_candidate
                and strength_requested > 0
            )
        )
    ):
        add_on_only = limits["max_sessions"] == 1 and has_main_candidate

        recommendation = (
            "add_on"
            if add_on_only
            else (
                "optional"
                if strength_decision == "optional"
                else "recommended"
            )
        )
        delivery_mode = "add_on" if add_on_only else "standalone"
        capacity_cost = 0 if add_on_only else 1

        session_type = (
            "light_mobility_core"
            if strength_decision == "recommended_light"
            else "mobility_core"
        )

        reason = (
            "Tek seans sınırı nedeniyle mobilite/core ayrı seans değil, "
            "ana seansa ek aday olarak üretildi."
            if add_on_only
            else "Final karar mobilite/core çalışmasını destekliyor."
        )

        candidates.append(
            _candidate(
                candidate_id="mobility_core",
                modality="strength_or_mobility",
                session_type=session_type,
                recommendation=recommendation,
                intensity_cap="light",
                delivery_mode=delivery_mode,
                capacity_cost=capacity_cost,
                source_decision=strength_decision,
                reason=reason,
            )
        )
    else:
        blocked_candidates.append(
            _blocked(
                "mobility_core",
                "strength_or_mobility",
                strength_decision,
                (
                    "Mobilite/core planning_limits içinde kullanılabilir değil."
                    if "strength_or_mobility" not in available_modalities
                    else "Final karar mobilite/core çalışmasını önermiyor."
                ),
            )
        )

    candidates = _sort_and_rank(
        candidates,
        priority=priority,
        weekly_intent=weekly_intent,
    )

    standalone_capacity_requested = sum(
        candidate["standalone_capacity_cost"]
        for candidate in candidates
    )
    selection_required = (
        standalone_capacity_requested > limits["max_sessions"]
    )

    if not rules.get("intervals_allowed", False):
        avoid.extend(["interval", "tempo_run"])

    # Candidate builder v1 deliberately does not create these sessions,
    # even when the broad rule layer allows intensity.
    avoid.extend(["unplanned_intensity", "long_run"])

    if selection_required:
        avoid.append("selecting_all_standalone_candidates")

    if limits["max_sessions"] == 1:
        avoid.append("extra_standalone_session")

    status = "ready" if candidates else "no_applicable_candidate"

    return {
        "schema_version": SESSION_CANDIDATE_SCHEMA_VERSION,
        "status": status,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_engine_version": metadata.get("engine_version"),
        "weekly_intent": weekly_intent,
        "priority": priority,
        "planning_limits": deepcopy(limits),
        "weekly_dose": deepcopy(weekly_dose),
        "planner_policy": {
            "interval_candidates_enabled": False,
            "tempo_candidates_enabled": False,
            "long_run_candidates_enabled": False,
            "pace_or_distance_binding": False,
        },
        "candidates": candidates,
        "candidate_count": len(candidates),
        "standalone_capacity_requested": standalone_capacity_requested,
        "standalone_capacity_limit": limits["max_sessions"],
        "selection_required": selection_required,
        "blocked_candidates": blocked_candidates,
        "avoid": _unique(avoid),
        "reasons": _unique(reasons),
    }
