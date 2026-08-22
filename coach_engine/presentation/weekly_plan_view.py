from __future__ import annotations

import re
from datetime import date
from typing import Any, Iterable, Mapping


VIEW_MODEL_VERSION = "0.1.0"

STATUS_PRESENTATION = {
    "ready": {
        "label": "Plan hazır",
        "tone": "success",
        "message": "Bu haftanın uygulanabilir planı hazır.",
    },
    "partially_scheduled": {
        "label": "Plan kısmen yerleştirildi",
        "tone": "warning",
        "message": (
            "Bazı geçerli seanslar plana yerleşti; bazıları için uygun gün "
            "bulunamadı."
        ),
    },
    "unscheduled": {
        "label": "Uygun gün bulunamadı",
        "tone": "warning",
        "message": (
            "Geçerli bir antrenman seçildi ancak mevcut gün kısıtlarıyla "
            "takvime yerleştirilemedi."
        ),
    },
    "no_sessions": {
        "label": "Planlanmış seans yok",
        "tone": "info",
        "message": "Bu rolling yedi günlük pencere için seans planlanmadı.",
    },
    "no_structured_training": {
        "label": "Yapılandırılmış plan yok",
        "tone": "warning",
        "message": (
            "Sağlık veya toparlanma kısıtı nedeniyle yapılandırılmış "
            "antrenman planlanmadı."
        ),
    },
    "missing": {
        "label": "Henüz plan üretilmedi",
        "tone": "info",
        "message": (
            "Weekly Check-in'i kaydedip pipeline'ı çalıştırdığında plan burada "
            "görünecek."
        ),
    },
    "invalid": {
        "label": "Plan okunamadı",
        "tone": "error",
        "message": (
            "Weekly plan artifact'i beklenen temel yapıyı taşımıyor. "
            "Teknik ayrıntıları kontrol et."
        ),
    },
}

SESSION_LABELS = {
    "easy_run": "Kolay koşu",
    "easy_z2_cycling": "Kolay Z2 bisiklet/trainer",
    "recovery_cycling": "Toparlanma sürüşü",
    "mobility_core": "Mobilite / Core",
    "light_mobility_core": "Hafif mobilite / Core",
}

MODALITY_LABELS = {
    "running": "Koşu",
    "cycling": "Bisiklet / Trainer",
    "strength_or_mobility": "Mobilite / Core",
}

INTENSITY_LABELS = {
    "easy": "Kolay / konuşma temposu",
    "easy_z2": "Kolay Z2",
    "recovery": "Çok kolay toparlanma eforu",
    "light": "Hafif ve kontrollü",
}

DAY_LABELS = {
    "monday": "Pazartesi",
    "tuesday": "Salı",
    "wednesday": "Çarşamba",
    "thursday": "Perşembe",
    "friday": "Cuma",
    "saturday": "Cumartesi",
    "sunday": "Pazar",
}

MONTH_LABELS = {
    1: "Ocak",
    2: "Şubat",
    3: "Mart",
    4: "Nisan",
    5: "Mayıs",
    6: "Haziran",
    7: "Temmuz",
    8: "Ağustos",
    9: "Eylül",
    10: "Ekim",
    11: "Kasım",
    12: "Aralık",
}


WEEKLY_INTENT_LABELS = {
    "recover": "Toparlanmak",
    "maintain_consistency": "Ritmi korumak",
    "build_carefully": "Kontrollü gelişmek",
    "return_after_break": "Aradan sonra geri dönmek",
    "race_specific": "Yarışa hazırlanmak",
}

FOCUS_BY_WEEKLY_LOAD = {
    "restart_easy": "Ritmi kolay ve uygulanabilir seanslarla yeniden kur",
    "maintain": "Mevcut ritmi sürdürülebilir biçimde koru",
    "reduce": "Yükü azalt ve toparlanmayı koru",
    "reduce_or_maintain": "Yükü artırmadan toparlanmayı ve ritmi koru",
    "controlled_build": "Yükü küçük ve kontrollü adımlarla geliştir",
}

FOCUS_BY_PRIORITY = {
    "recovery": "Toparlanmayı önceliklendir",
    "consistency": "Düzenli antrenman ritmini yeniden kur",
    "running_consistency": "Koşu ritmini kolay seanslarla koru",
    "bike": "Bisiklet/trainer ile aerobik tabanı destekle",
    "balanced": "Koşu ve bisikleti dengeli biçimde sürdür",
}


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _safe_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None

    if isinstance(value, int):
        return value

    if isinstance(value, float) and value.is_integer():
        return int(value)

    return None


def _nonempty_string(value: Any) -> str | None:
    if not isinstance(value, str):
        return None

    normalized = value.strip()
    return normalized or None


def _format_date(
    value: Any,
    *,
    day_value: Any = None,
    include_year: bool = False,
) -> str | None:
    raw = _nonempty_string(value)
    if not raw:
        return None

    try:
        parsed = date.fromisoformat(raw)
    except ValueError:
        return raw

    day_label = DAY_LABELS.get(
        str(day_value).lower(),
        DAY_LABELS.get(parsed.strftime("%A").lower()),
    )

    date_label = f"{parsed.day} {MONTH_LABELS[parsed.month]}"

    if include_year:
        date_label += f" {parsed.year}"

    if day_label:
        return f"{date_label} {day_label}"

    return date_label


def _format_horizon_date(value: Any) -> str | None:
    raw = _nonempty_string(value)
    if not raw:
        return None

    try:
        parsed = date.fromisoformat(raw)
    except ValueError:
        return raw

    return f"{parsed.day} {MONTH_LABELS[parsed.month]}"


def _format_horizon(horizon: Mapping[str, Any]) -> str:
    start = _format_horizon_date(
        horizon.get("start_date")
    )
    end = _format_horizon_date(
        horizon.get("end_date")
    )

    if start and end:
        return f"{start} – {end}"

    if start:
        return start

    if end:
        return end

    return "-"


def _format_duration(
    duration: Mapping[str, Any],
) -> dict[str, Any]:
    target = _safe_int(duration.get("target_min"))
    minimum = _safe_int(duration.get("min"))
    maximum = _safe_int(duration.get("max"))

    if target is not None:
        primary = f"{target} dk"
    elif minimum is not None and maximum is not None:
        primary = f"{minimum}–{maximum} dk"
    else:
        primary = "-"

    range_label = None
    if minimum is not None and maximum is not None:
        range_label = f"{minimum}–{maximum} dk"

    return {
        "target_min": target,
        "min": minimum,
        "max": maximum,
        "primary": primary,
        "range": range_label,
    }


def _format_pace(
    pace: Mapping[str, Any],
) -> dict[str, Any] | None:
    if not pace.get("available"):
        return None

    target = _nonempty_string(
        pace.get("target_reference_display")
    )
    display_range = _as_mapping(pace.get("range_display"))
    faster = _nonempty_string(display_range.get("faster"))
    slower = _nonempty_string(display_range.get("slower"))

    parts = []

    if faster and slower:
        parts.append(f"{faster}–{slower}")
    elif target:
        parts.append(target)

    if target and faster and slower:
        parts.append(f"referans {target}")

    parts.append("bağlayıcı değil")

    return {
        "label": " · ".join(parts),
        "target": target,
        "binding": bool(pace.get("binding")),
    }


def _format_distance(
    distance: Mapping[str, Any],
) -> dict[str, Any] | None:
    if not distance.get("available"):
        return None

    target = distance.get("target_km")
    distance_range = _as_mapping(distance.get("range_km"))
    minimum = distance_range.get("min")
    maximum = distance_range.get("max")

    parts = []

    if minimum is not None and maximum is not None:
        parts.append(f"yaklaşık {minimum}–{maximum} km")
    elif target is not None:
        parts.append(f"yaklaşık {target} km")

    if (
        target is not None
        and minimum is not None
        and maximum is not None
    ):
        parts.append(f"referans {target} km")

    parts.append("bağlayıcı değil")

    return {
        "label": " · ".join(parts),
        "target_km": target,
        "binding": bool(distance.get("binding")),
    }


def _normalize_reason(value: Any) -> str | None:
    if not isinstance(value, str):
        return None

    normalized = re.sub(r"\s+", " ", value).strip()
    normalized = normalized.lstrip("-• ").strip()
    return normalized or None


def _reason_key(value: str) -> str:
    return value.casefold().rstrip(".!?;: ")


def _split_sentences(value: Any) -> list[str]:
    normalized = _normalize_reason(value)
    if not normalized:
        return []

    return [
        part.strip()
        for part in re.split(r"(?<=[.!?])\s+", normalized)
        if part.strip()
    ]


def _dedupe_text(
    values: Iterable[Any],
    *,
    limit: int,
) -> list[str]:
    result = []
    seen = set()

    for value in values:
        normalized = _normalize_reason(value)
        if not normalized:
            continue

        key = _reason_key(normalized)
        if key in seen:
            continue

        seen.add(key)
        result.append(normalized)

        if len(result) >= limit:
            break

    return result


def _build_reasons(
    coach_context: Mapping[str, Any],
) -> list[str]:
    final_decision = _as_mapping(
        coach_context.get("final_decision")
    )
    context_signals = _as_mapping(
        coach_context.get("context_signals")
    )
    rules = _as_mapping(coach_context.get("rules"))

    candidates: list[Any] = []
    candidates.extend(
        _split_sentences(final_decision.get("reason"))
    )
    candidates.extend(
        _as_list(final_decision.get("context_reasons"))
    )
    candidates.extend(
        _as_list(context_signals.get("reasons"))
    )

    progression_advice = rules.get("progression_advice")
    if progression_advice:
        candidates.append(progression_advice)

    return _dedupe_text(candidates, limit=5)


def _build_avoid_items(
    coach_context: Mapping[str, Any],
) -> list[str]:
    final_decision = _as_mapping(
        coach_context.get("final_decision")
    )
    rules = _as_mapping(coach_context.get("rules"))

    avoids = []

    if rules.get("intervals_allowed") is False:
        avoids.append(
            "Interval, tempo koşusu veya plan dışı yüksek yoğunluk ekleme."
        )

    if final_decision.get("weekly_load") in {
        "maintain",
        "reduce",
        "reduce_or_maintain",
        "restart_easy",
    }:
        avoids.append(
            "Koşu hacmini veya toplam süreyi belirgin biçimde artırma."
        )

    if final_decision.get("running") in {
        "easy_only",
        "maintain_easy",
    }:
        avoids.append(
            "Kolay koşuyu yarış temposuna veya zorlayıcı tempoya taşıma."
        )

    if final_decision.get("cycling") == "not_available":
        avoids.append(
            "Bisiklet/trainer eksikliğini ek koşu yüküyle telafi etme."
        )

    return _dedupe_text(avoids, limit=3)


def _build_focus(
    coach_context: Mapping[str, Any],
    status: str,
) -> str:
    final_decision = _as_mapping(
        coach_context.get("final_decision")
    )

    if status == "no_structured_training":
        return "Toparlanmayı ve sağlık sinyallerini önceliklendir"

    weekly_load = final_decision.get("weekly_load")
    if weekly_load in FOCUS_BY_WEEKLY_LOAD:
        return FOCUS_BY_WEEKLY_LOAD[weekly_load]

    priority = final_decision.get("priority")
    if priority in FOCUS_BY_PRIORITY:
        return FOCUS_BY_PRIORITY[priority]

    reason_sentences = _split_sentences(
        final_decision.get("reason")
    )
    if reason_sentences:
        return reason_sentences[0]

    return "Bu haftanın uygulanabilir planını sürdür"


def _build_add_on(
    add_on: Mapping[str, Any],
) -> dict[str, Any]:
    duration = _format_duration(
        _as_mapping(add_on.get("duration"))
    )

    return {
        "title": SESSION_LABELS.get(
            add_on.get("type"),
            str(add_on.get("type") or "Ek çalışma"),
        ),
        "duration": duration,
        "label": (
            f"{duration['primary']} "
            f"{SESSION_LABELS.get(add_on.get('type'), 'Ek çalışma')}"
        ),
    }


def _build_session(
    session: Mapping[str, Any],
) -> dict[str, Any]:
    scheduling = _as_mapping(session.get("scheduling"))
    duration = _format_duration(
        _as_mapping(session.get("duration"))
    )
    total_duration = _format_duration(
        _as_mapping(session.get("session_total_duration"))
    )
    intensity = _as_mapping(session.get("intensity"))

    alternatives = []
    flexibility = _as_mapping(scheduling.get("flexibility"))

    for item in _as_list(
        flexibility.get("alternative_dates")
    ):
        item_mapping = _as_mapping(item)
        formatted = _format_date(
            item_mapping.get("date"),
            day_value=item_mapping.get("day"),
        )
        if formatted:
            alternatives.append(formatted)

    add_ons = [
        _build_add_on(_as_mapping(add_on))
        for add_on in _as_list(session.get("add_ons"))
    ]

    day_label = (
        _nonempty_string(scheduling.get("day_label_tr"))
        or DAY_LABELS.get(
            str(scheduling.get("day") or "").lower()
        )
    )

    date_label = _format_date(
        scheduling.get("date"),
        day_value=scheduling.get("day"),
    )

    return {
        "session_id": session.get("session_id"),
        "title": SESSION_LABELS.get(
            session.get("type"),
            str(session.get("type") or "Antrenman"),
        ),
        "modality": MODALITY_LABELS.get(
            session.get("modality"),
            str(session.get("modality") or "-"),
        ),
        "date": scheduling.get("date"),
        "day_label": day_label or "-",
        "date_label": date_label or "-",
        "main_duration": duration,
        "total_duration": total_duration,
        "effort_label": INTENSITY_LABELS.get(
            intensity.get("cap"),
            str(intensity.get("cap") or "-"),
        ),
        "pace": _format_pace(
            _as_mapping(session.get("pace_guidance"))
        ),
        "distance": _format_distance(
            _as_mapping(session.get("distance_guidance"))
        ),
        "add_ons": add_ons,
        "alternatives": alternatives,
        "scheduling_status": scheduling.get("status"),
    }


def _build_unscheduled_session(
    session: Mapping[str, Any],
) -> dict[str, Any]:
    scheduling = _as_mapping(session.get("scheduling"))

    return {
        "session_id": session.get("session_id"),
        "title": SESSION_LABELS.get(
            session.get("type"),
            str(session.get("type") or "Antrenman"),
        ),
        "reason": (
            _nonempty_string(scheduling.get("reason"))
            or "Mevcut gün kısıtlarıyla takvime yerleştirilemedi."
        ),
    }


def _build_constraints(
    coach_context: Mapping[str, Any],
) -> list[str]:
    final_decision = _as_mapping(
        coach_context.get("final_decision")
    )
    limits = _as_mapping(
        final_decision.get("planning_limits")
    )

    values = []

    max_sessions = _safe_int(limits.get("max_sessions"))
    if max_sessions is not None:
        values.append(
            f"En fazla {max_sessions} standalone seans"
        )

    max_duration = _safe_int(
        limits.get("max_session_duration_min")
    )
    if max_duration is not None:
        values.append(
            f"Seans başına en fazla {max_duration} dk"
        )

    modalities = [
        MODALITY_LABELS.get(value, str(value))
        for value in _as_list(
            limits.get("available_modalities")
        )
    ]
    if modalities:
        values.append(
            "Uygun türler: " + ", ".join(modalities)
        )

    return values



def _build_applied_context(
    coach_context: Mapping[str, Any],
    *,
    planned_session_count: int,
    planned_total_duration_min: int,
) -> dict[str, Any]:
    manual_context = _as_mapping(
        coach_context.get("manual_context")
    )
    final_decision = _as_mapping(
        coach_context.get("final_decision")
    )
    limits = _as_mapping(
        final_decision.get("planning_limits")
    )
    availability = _as_mapping(
        manual_context.get("availability")
    )

    weekly_intent = manual_context.get("weekly_intent")
    max_sessions = _safe_int(
        limits.get(
            "max_sessions",
            availability.get("max_sessions"),
        )
    )
    max_duration = _safe_int(
        limits.get(
            "max_session_duration_min",
            availability.get("max_session_duration_min"),
        )
    )

    capacity_notes = []

    if max_sessions is not None:
        capacity_notes.append(
            f"{max_sessions} seans bir hedef değil, "
            "planner'ın aşamayacağı üst sınırdır."
        )

        if planned_session_count < max_sessions:
            capacity_notes.append(
                f"Deterministik planner bu pencere için "
                f"{planned_session_count} standalone seans seçti."
            )

    if max_duration is not None:
        capacity_notes.append(
            f"{max_duration} dakika önerilen süre değil, "
            "tek seans için üst sınırdır."
        )

    intent_notice = None
    if weekly_intent == "race_specific":
        intent_notice = (
            "“Yarışa hazırlanmak” bu sürümde bir öncelik sinyalidir. "
            "Interval, tempo ve uzun koşu adayları henüz planner kapsamına "
            "alınmadığı için bu seçim tek başına daha sert veya daha uzun "
            "bir antrenman üretmez."
        )

    return {
        "weekly_intent": weekly_intent,
        "weekly_intent_label": WEEKLY_INTENT_LABELS.get(
            weekly_intent,
            str(weekly_intent or "-"),
        ),
        "max_sessions": max_sessions,
        "max_session_duration_min": max_duration,
        "planned_session_count": planned_session_count,
        "planned_total_duration_min": planned_total_duration_min,
        "capacity_notice": " ".join(capacity_notes) or None,
        "intent_notice": intent_notice,
    }

def build_weekly_plan_view_model(
    coach_context: Any,
    weekly_plan: Any,
) -> dict[str, Any]:
    """
    Serving artifact'lerini Streamlit'in kolayca gösterebileceği kullanıcı
    dilindeki bir view model'e dönüştürür.

    Bu fonksiyon karar veya plan üretmez. Tarih, süre, seans ve kısıtları
    değiştirmez.
    """

    context = _as_mapping(coach_context)

    if weekly_plan is None:
        status = "missing"
        status_meta = STATUS_PRESENTATION[status]

        return {
            "view_model_version": VIEW_MODEL_VERSION,
            "status": status,
            "status_label": status_meta["label"],
            "status_tone": status_meta["tone"],
            "status_message": status_meta["message"],
            "focus": _build_focus(context, status),
            "horizon_label": "-",
            "session_count": 0,
            "total_duration_min": 0,
            "intensity_summary": "-",
            "sessions": [],
            "unscheduled_sessions": [],
            "reasons": _build_reasons(context),
            "avoid_items": _build_avoid_items(context),
            "constraints": _build_constraints(context),
            "applied_context": _build_applied_context(
                context,
                planned_session_count=0,
                planned_total_duration_min=0,
            ),
            "metadata": {},
        }

    plan = _as_mapping(weekly_plan)
    raw_status = plan.get("plan_status")

    if raw_status not in STATUS_PRESENTATION:
        status = "invalid"
    elif not isinstance(plan.get("sessions"), list):
        status = "invalid"
    elif not isinstance(
        plan.get("unscheduled_sessions"),
        list,
    ):
        status = "invalid"
    else:
        status = str(raw_status)

    status_meta = STATUS_PRESENTATION[status]
    sessions = [
        _build_session(_as_mapping(session))
        for session in _as_list(plan.get("sessions"))
    ]
    unscheduled = [
        _build_unscheduled_session(
            _as_mapping(session)
        )
        for session in _as_list(
            plan.get("unscheduled_sessions")
        )
    ]

    total_duration = sum(
        session["total_duration"]["target_min"] or 0
        for session in sessions
    )

    intensity_values = _dedupe_text(
        [
            session["effort_label"]
            for session in sessions
            if session["effort_label"] != "-"
        ],
        limit=3,
    )

    return {
        "view_model_version": VIEW_MODEL_VERSION,
        "status": status,
        "status_label": status_meta["label"],
        "status_tone": status_meta["tone"],
        "status_message": status_meta["message"],
        "focus": _build_focus(context, status),
        "horizon_label": _format_horizon(
            _as_mapping(plan.get("planning_horizon"))
        ),
        "session_count": len(sessions),
        "total_duration_min": total_duration,
        "intensity_summary": (
            ", ".join(intensity_values)
            if intensity_values
            else "-"
        ),
        "sessions": sessions,
        "unscheduled_sessions": unscheduled,
        "reasons": _build_reasons(context),
        "avoid_items": _build_avoid_items(context),
        "constraints": _build_constraints(context),
        "applied_context": _build_applied_context(
            context,
            planned_session_count=len(sessions),
            planned_total_duration_min=total_duration,
        ),
        "metadata": {
            "schema_version": plan.get("schema_version"),
            "generated_at": plan.get("generated_at"),
            "planner_version": plan.get("planner_version"),
            "planning_engine": plan.get("planning_engine"),
        },
    }


__all__ = [
    "VIEW_MODEL_VERSION",
    "build_weekly_plan_view_model",
]
