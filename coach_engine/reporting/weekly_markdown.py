from __future__ import annotations

import re
from typing import Any, Dict, Iterable


def value_or_dash(value: Any) -> Any:
    if value is None or value == "":
        return "-"
    return value


def bool_label(value: Any) -> str:
    if value is True:
        return "Evet"
    if value is False:
        return "Hayır"
    return "-"


LABELS = {
    # Common values
    "normal": "Normal",
    "child_sick": "Çocuk hasta",
    "family_busy": "Aile yoğun",
    "high": "Yüksek",
    "very_high": "Çok yüksek",
    "low": "Düşük",
    "very_low": "Çok düşük",
    "medium": "Orta",
    "none": "Yok",
    "okay": "Orta",
    "good": "İyi",
    "poor": "Kötü",
    "active": "Aktif",
    "recovering": "Hastalıktan dönüş",

    # Weekly load / running
    "maintain": "Mevcut yükü koru",
    "reduce": "Yükü azalt",
    "reduce_or_maintain": "Yükü azalt veya koru",
    "controlled_build": "Kontrollü gelişim",
    "restart_easy": "Kolay başlangıç",
    "maintain_easy": "Kolay koşularla ritmi koru",
    "easy_only": "Sadece kolay koşu",
    "controlled_increase": "Kontrollü artır",

    # Cycling
    "add_easy_z2": "Kolay Z2 bisiklet/trainer ekle",
    "add_or_maintain_z2": "Kolay Z2 bisiklet/trainer ekle veya koru",
    "optional_easy_z2": "Opsiyonel kolay Z2 bisiklet/trainer",
    "optional_recovery": "Opsiyonel toparlanma sürüşü",
    "recovery_only": "Sadece toparlanma sürüşü",
    "not_available": "Bu hafta uygun değil",

    # Strength / mobility
    "recommended": "Önerilir",
    "recommended_light": "Hafif mobilite/core önerilir",
    "optional": "Opsiyonel",
    "not_recommended": "Önerilmez",

    # Priority
    "bike": "Bisiklet/trainer öncelikli",
    "recovery": "Toparlanma öncelikli",
    "balanced": "Dengeli",
    "consistency": "Ritim / süreklilik",
    "running_consistency": "Koşu ritmini koruma",

    # Weekly intent
    "recover": "Toparlanmak",
    "maintain_consistency": "Ritmi korumak",
    "build_carefully": "Kontrollü gelişmek",
    "return_after_break": "Aradan sonra geri dönmek",
    "race_specific": "Yarışa hazırlanmak",

    # Context adjustment / constraints
    "soft": "Hafif uyarlama",
    "strong": "Belirgin uyarlama",
    "hard": "Koruyucu kısıtlama",
    "active_illness": "Aktif hastalık",
    "recovering_illness": "Hastalıktan dönüş",
    "running_pain": "Koşuyu etkileyen ağrı",
    "moderate_pain": "Orta düzey aktif ağrı",
    "mild_pain": "Hafif aktif ağrı",
    "very_limited": "Çok sınırlı",
    "limited": "Sınırlı",
    "limited_modalities": "Antrenman türleri sınırlı",
    "no_available_modality": "Uygulanabilir antrenman türü yok",

    # Modalities / equipment
    "bike_or_trainer": "Bisiklet veya indoor trainer",
    "trainer": "Indoor trainer",
    "bike": "Bisiklet",
    "running": "Koşu",
    "strength_or_mobility": "Mobilite/core",

    # Pain areas
    "foot": "Ayak / ayak bileği",
    "calf": "Baldır",
    "knee": "Diz",
    "hip": "Kalça",
    "lower_back": "Bel",
    "shoulder": "Omuz",
    "other": "Diğer",

    # Environment
    "vacation": "Tatil",
    "travel": "Seyahat",
    "home": "Ev rutini",

    # Plan statuses
    "ready": "Hazır",
    "partially_scheduled": "Kısmen planlandı",
    "unscheduled": "Planlanamadı",
    "no_sessions": "Seans yok",
    "no_structured_training": "Yapılandırılmış antrenman yok",
    "unavailable": "Kullanılamıyor",

    # Days
    "Sunday": "Pazar",
    "Monday": "Pazartesi",
    "Tuesday": "Salı",
    "Wednesday": "Çarşamba",
    "Thursday": "Perşembe",
    "Friday": "Cuma",
    "Saturday": "Cumartesi",
    "sunday": "Pazar",
    "monday": "Pazartesi",
    "tuesday": "Salı",
    "wednesday": "Çarşamba",
    "thursday": "Perşembe",
    "friday": "Cuma",
    "saturday": "Cumartesi",
}


SESSION_TYPE_LABELS = {
    "easy_run": "Kolay koşu",
    "easy_z2_cycling": "Kolay Z2 bisiklet/trainer",
    "recovery_cycling": "Toparlanma sürüşü",
    "mobility_core": "Mobilite/Core",
    "light_mobility_core": "Hafif mobilite/Core",
}


INTENSITY_LABELS = {
    "easy": "Kolay / konuşma temposu",
    "easy_z2": "Kolay Z2",
    "recovery": "Çok kolay toparlanma eforu",
    "light": "Hafif ve kontrollü",
}


def label(value: Any) -> str:
    if value is None or value == "":
        return "-"
    if isinstance(value, bool):
        return bool_label(value)
    return LABELS.get(value, str(value))


def label_list(values: Iterable[Any] | None) -> str:
    if not values:
        return "-"
    return ", ".join(label(value) for value in values)


def modality_label(value: Any) -> str:
    return LABELS.get(value, label(value))


def modality_label_list(values: Iterable[Any] | None) -> str:
    if not values:
        return "-"
    return ", ".join(modality_label(value) for value in values)


def session_type_label(value: Any) -> str:
    return SESSION_TYPE_LABELS.get(value, str(value_or_dash(value)))


def intensity_label(value: Any) -> str:
    return INTENSITY_LABELS.get(value, str(value_or_dash(value)))


def _format_duration_range(duration: Dict[str, Any] | None) -> str:
    if not duration:
        return "-"

    target = duration.get("target_min")
    minimum = duration.get("min")
    maximum = duration.get("max")

    parts = []

    if target is not None:
        parts.append(f"hedef {target} dk")

    if minimum is not None and maximum is not None:
        parts.append(f"aralık {minimum}–{maximum} dk")

    return ", ".join(parts) if parts else "-"


def _format_alternatives(scheduling: Dict[str, Any] | None) -> str | None:
    flexibility = (scheduling or {}).get("flexibility") or {}
    alternatives = flexibility.get("alternative_dates") or []

    if not alternatives:
        return None

    return ", ".join(
        (
            f"{item.get('day_label_tr') or label(item.get('day'))} "
            f"({item.get('date')})"
        )
        for item in alternatives
    )


def _join_compact(parts: Iterable[str | None]) -> str:
    return " · ".join(
        str(part)
        for part in parts
        if part not in (None, "", "-")
    )


def _normalize_reason(value: str) -> str:
    normalized = re.sub(r"\s+", " ", value).strip()
    normalized = normalized.lstrip("-• ").strip()
    return normalized


def _reason_key(value: str) -> str:
    normalized = _normalize_reason(value).casefold()
    return normalized.rstrip(".!?;: ")


def _split_reason_sentences(value: str | None) -> list[str]:
    if not value:
        return []

    normalized = _normalize_reason(value)
    if not normalized:
        return []

    return [
        part.strip()
        for part in re.split(r"(?<=[.!?])\s+", normalized)
        if part.strip()
    ]


def _collect_plan_reasons(
    context: Dict[str, Any],
    *,
    limit: int = 5,
) -> list[str]:
    final_decision = context.get("final_decision", {})
    context_signals = context.get("context_signals", {})
    rules = context.get("rules", {})

    candidates: list[str] = []
    candidates.extend(
        _split_reason_sentences(final_decision.get("reason"))
    )

    for reason in (
        final_decision.get("context_reasons")
        or context_signals.get("reasons")
        or []
    ):
        if reason:
            candidates.append(str(reason))

    progression_advice = rules.get("progression_advice")
    if progression_advice:
        candidates.append(str(progression_advice))

    reasons: list[str] = []
    seen: set[str] = set()

    for candidate in candidates:
        normalized = _normalize_reason(candidate)
        key = _reason_key(normalized)

        if not normalized or key in seen:
            continue

        seen.add(key)
        reasons.append(normalized)

        if len(reasons) >= limit:
            break

    return reasons


def render_weekly_review(
    context: Dict[str, Any],
    weekly_plan: Dict[str, Any] | None = None,
) -> str:
    """
    Coach Context + optional Weekly Plan -> Markdown.

    Bu renderer hesap yapmaz, karar vermez veya plan değiştirmez.
    Hazır serving artifact'lerini daha kısa ve açıklanabilir bir teknik
    rapora dönüştürür.
    """

    lines: list[str] = []

    append_title(lines, context)
    append_history_and_load(lines, context)
    append_week_context(lines, context)
    append_decision(lines, context)
    append_weekly_plan(lines, weekly_plan)
    append_plan_reasons(lines, context)
    append_metadata(lines, context, weekly_plan)

    return "\n".join(lines)


def append_title(
    lines: list[str],
    context: Dict[str, Any],
) -> None:
    athlete = context.get("athlete", {})
    name = athlete.get("name")
    goal = athlete.get("primary_goal")

    lines.append("# Haftalık Garmin Coach Review")
    lines.append("")

    if name and goal:
        lines.append(
            f"**Sporcu:** {name}  \n"
            f"**Ana hedef:** {goal}"
        )
    elif name:
        lines.append(f"**Sporcu:** {name}")
    elif goal:
        lines.append(f"**Ana hedef:** {goal}")

    lines.append(
        "\nBu rapor, deterministik karar ve haftalık plan artifact'lerinin "
        "teknik ve açıklanabilir özetidir."
    )


def append_history_and_load(
    lines: list[str],
    context: Dict[str, Any],
) -> None:
    metrics = context.get("metrics", {})
    rules = context.get("rules", {})
    athlete = context.get("athlete", {})
    training_profile = context.get("training_profile", {})
    performance = context.get("performance", {})

    lines.append("\n## 1. Geçmiş Aktivite ve Yük")

    lines.append(
        "- Son 7 gün: "
        f"{value_or_dash(metrics.get('activity_count_7_days'))} aktivite · "
        f"{value_or_dash(metrics.get('total_hours_7_days'))} saat · "
        f"{value_or_dash(metrics.get('weekly_distance_km'))} km"
    )
    lines.append(
        "- Son 30 gün: "
        f"{value_or_dash(metrics.get('activity_count_30_days'))} aktivite · "
        f"{value_or_dash(metrics.get('total_hours_30_days'))} saat · "
        f"{value_or_dash(metrics.get('monthly_distance_km'))} km"
    )

    weekly_target = athlete.get("weekly_target", {})
    target_parts = []

    if weekly_target.get("running_sessions") is not None:
        target_parts.append(
            "Koşu "
            f"{value_or_dash(metrics.get('running_sessions'))}/"
            f"{weekly_target.get('running_sessions')}"
        )

    if weekly_target.get("cycling_sessions") is not None:
        target_parts.append(
            "Bisiklet/trainer "
            f"{value_or_dash(metrics.get('cycling_sessions'))}/"
            f"{weekly_target.get('cycling_sessions')}"
        )

    if target_parts:
        lines.append(
            f"- Haftalık seans durumu: {' · '.join(target_parts)}"
        )

    baseline_text = _join_compact(
        [
            (
                "Bu hafta "
                f"{value_or_dash(metrics.get('current_week_hours'))} saat"
            ),
            (
                "baseline "
                f"{value_or_dash(metrics.get('weekly_baseline_hours'))} saat"
            ),
            (
                "load ratio "
                f"{value_or_dash(metrics.get('load_ratio'))}"
            ),
        ]
    )
    lines.append(f"- Yük karşılaştırması: {baseline_text}")
    lines.append(
        f"- Progression sinyali: "
        f"{value_or_dash(rules.get('progression_label'))}"
    )

    running = training_profile.get("running_30_days") or {}
    if training_profile.get("data_available") or running.get("runs_analyzed"):
        profile_parts = [
            f"{value_or_dash(running.get('runs_analyzed'))} koşu",
        ]

        median_distance = running.get("median_run_distance_km")
        median_duration = running.get("median_run_duration_min")
        longest_distance = running.get("longest_run_distance_km")

        if median_distance is not None and median_duration is not None:
            profile_parts.append(
                f"medyan {median_distance} km / {median_duration} dk"
            )

        if longest_distance is not None:
            profile_parts.append(
                f"en uzun {longest_distance} km"
            )

        lines.append(
            f"- 30 günlük koşu profili: "
            f"{' · '.join(profile_parts)}"
        )

        pace_display = running.get("pace_distribution_display") or {}
        observed_median_pace = pace_display.get("median")

        if observed_median_pace:
            lines.append(
                f"- Gözlenen medyan koşu pace'i: "
                f"{observed_median_pace}; kolay koşu hedefi değildir."
            )

    race = performance.get("race_predictor") or {}
    if race:
        race_parts = [
            f"5K {value_or_dash(race.get('5k'))}",
            f"10K {value_or_dash(race.get('10k'))}",
            f"Yarı maraton {value_or_dash(race.get('half_marathon'))}",
            f"Maraton {value_or_dash(race.get('marathon'))}",
        ]
        lines.append(
            "- Garmin Race Predictor: "
            f"{' · '.join(race_parts)}"
        )
        lines.append(
            "  Bu değerler kondisyon sinyalidir; doğrudan yarış hedefi değildir."
        )


def append_week_context(
    lines: list[str],
    context: Dict[str, Any],
) -> None:
    manual_context = context.get("manual_context", {})
    context_signals = context.get("context_signals", {})
    final_decision = context.get("final_decision", {})

    availability = manual_context.get("availability", {})
    recovery = manual_context.get("recovery", {})
    pain = manual_context.get("pain", {})
    life_load = manual_context.get("life_load", {})
    planning_limits = final_decision.get("planning_limits", {})

    lines.append("\n## 2. Bu Haftanın Bağlamı")
    lines.append(
        f"- Haftanın niyeti: "
        f"{label(manual_context.get('weekly_intent'))}"
    )

    max_sessions = planning_limits.get(
        "max_sessions",
        availability.get("max_sessions"),
    )
    max_duration = planning_limits.get(
        "max_session_duration_min",
        availability.get("max_session_duration_min"),
    )
    available_days = planning_limits.get(
        "available_days",
        availability.get("available_days"),
    )
    available_modalities = planning_limits.get(
        "available_modalities",
        context_signals.get("available_modalities"),
    )

    feasibility_parts = [
        (
            f"en fazla {max_sessions} standalone seans"
            if max_sessions is not None
            else None
        ),
        (
            f"seans başına en fazla {max_duration} dk"
            if max_duration is not None
            else None
        ),
    ]
    lines.append(
        f"- Uygulanabilirlik: {_join_compact(feasibility_parts) or '-'}"
    )

    if available_days:
        lines.append(
            f"- Uygun günler: {label_list(available_days)}"
        )

    if available_modalities:
        lines.append(
            "- Kullanılabilir antrenman türleri: "
            f"{modality_label_list(available_modalities)}"
        )

    recovery_summary = _join_compact(
        [
            f"uyku {label(recovery.get('sleep_quality'))}",
            f"enerji {label(recovery.get('energy_level'))}",
            f"mental yorgunluk {label(recovery.get('mental_fatigue'))}",
            f"kas yorgunluğu {label(recovery.get('muscle_soreness'))}",
            f"hastalık {label(recovery.get('illness_status', 'none'))}",
        ]
    )
    lines.append(f"- Toparlanma: {recovery_summary}")

    life_summary = _join_compact(
        [
            f"iş {label(life_load.get('work_stress'))}",
            f"aile {label(life_load.get('family_load'))}",
            f"bakım {label(life_load.get('caregiving_load'))}",
            f"zaman baskısı {label(life_load.get('time_pressure'))}",
            f"duygusal yük {label(life_load.get('emotional_load'))}",
            f"seyahat {bool_label(life_load.get('travel'))}",
            f"rutin bozulması {label(life_load.get('routine_disruption'))}",
        ]
    )
    lines.append(f"- Yaşam yükü: {life_summary}")

    if pain.get("active_pain"):
        pain_text = (
            f"{label(pain.get('pain_area'))} · "
            f"{value_or_dash(pain.get('pain_severity'))}/10 · "
            f"koşuda artış {bool_label(pain.get('pain_during_running'))}"
        )
        lines.append(f"- Aktif ağrı: {pain_text}")

        if pain.get("pain_note"):
            lines.append(f"- Ağrı notu: {pain.get('pain_note')}")
    else:
        lines.append("- Aktif ağrı: Yok")

    user_note = manual_context.get("user_note")
    if user_note:
        lines.append(f"- Kullanıcı notu: {user_note}")


def append_decision(
    lines: list[str],
    context: Dict[str, Any],
) -> None:
    final_decision = context.get("final_decision", {})
    rules = context.get("rules", {})

    lines.append("\n## 3. Deterministik Karar")
    lines.append(
        f"- Haftalık yön: {label(final_decision.get('weekly_load'))}"
    )
    lines.append(
        f"- Öncelik: {label(final_decision.get('priority'))}"
    )
    lines.append(
        f"- Koşu: {label(final_decision.get('running'))}"
    )
    lines.append(
        f"- Bisiklet/Trainer: {label(final_decision.get('cycling'))}"
    )
    lines.append(
        "- Mobilite/Core: "
        f"{label(final_decision.get('strength_or_mobility'))}"
    )
    lines.append(
        f"- Context uyarlaması: "
        f"{label(final_decision.get('context_adjustment'))}"
    )
    lines.append(
        f"- Interval izni: "
        f"{bool_label(rules.get('intervals_allowed'))}"
    )

    risk_summary = _join_compact(
        [
            (
                "yük "
                f"{label(rules.get('training_load_risk_level'))}"
                if rules.get("training_load_risk_level") is not None
                else None
            ),
            (
                "context "
                f"{label(rules.get('context_risk_level'))}"
                if rules.get("context_risk_level") is not None
                else None
            ),
            (
                "birleşik "
                f"{label(rules.get('risk_level'))}"
                if rules.get("risk_level") is not None
                else None
            ),
        ]
    )
    if risk_summary:
        lines.append(f"- Risk özeti: {risk_summary}")


def append_weekly_plan(
    lines: list[str],
    weekly_plan: Dict[str, Any] | None,
) -> None:
    # Heading deliberately remains stable because other artifacts and tests
    # use it as a propagation anchor.
    lines.append("\n## Deterministik Haftalık Plan")

    if not weekly_plan:
        lines.append(
            "Weekly plan artifact'i bulunamadı. Karar ve uygulanabilirlik "
            "çerçevesi korunur; ancak kesin gün, süre, pace veya mesafe "
            "ayrıntısı gösterilemez."
        )
        return

    status = weekly_plan.get("plan_status")
    horizon = weekly_plan.get("planning_horizon") or {}

    summary_parts = [
        f"durum {label(status)}",
        (
            f"pencere {value_or_dash(horizon.get('start_date'))} → "
            f"{value_or_dash(horizon.get('end_date'))}"
            if horizon
            else None
        ),
        (
            "planlanan "
            f"{value_or_dash(weekly_plan.get('scheduled_count', weekly_plan.get('session_count')))}"
        ),
        (
            "planlanamayan "
            f"{value_or_dash(weekly_plan.get('unscheduled_count', 0))}"
        ),
    ]
    lines.append(f"- Plan özeti: {_join_compact(summary_parts)}")

    if status == "no_structured_training":
        lines.append(
            "Aktif sağlık veya toparlanma kısıtı nedeniyle "
            "yapılandırılmış antrenman planlanmadı."
        )
        return

    sessions = weekly_plan.get("sessions") or []

    if not sessions:
        lines.append(
            "Bu rolling yedi günlük pencere için planlanmış seans yok."
        )

    for index, session in enumerate(sessions, start=1):
        scheduling = session.get("scheduling") or {}
        date_value = scheduling.get("date")
        day_label = (
            scheduling.get("day_label_tr")
            or label(scheduling.get("day"))
        )
        session_type = session_type_label(session.get("type"))

        lines.append("")
        lines.append(
            f"### {index}. {day_label or '-'} "
            f"({date_value or '-'}) — {session_type}"
        )

        duration = session.get("duration") or {}
        total_duration = session.get("session_total_duration") or {}
        intensity = session.get("intensity") or {}

        lines.append(
            f"- Ana çalışma süresi: {_format_duration_range(duration)}"
        )
        lines.append(
            "- Toplam seans süresi: "
            f"{_format_duration_range(total_duration)}"
        )
        lines.append(
            "- Efor üst sınırı: "
            f"{intensity_label(intensity.get('cap'))}"
        )

        pace = session.get("pace_guidance") or {}
        if pace.get("available"):
            pace_range = pace.get("range_display") or {}
            lines.append(
                "- Pace referansı: "
                f"{value_or_dash(pace.get('target_reference_display'))}; "
                f"yaklaşık "
                f"{value_or_dash(pace_range.get('faster'))}–"
                f"{value_or_dash(pace_range.get('slower'))}; "
                "bağlayıcı değil"
            )

        distance = session.get("distance_guidance") or {}
        if distance.get("available"):
            distance_range = distance.get("range_km") or {}
            lines.append(
                "- Yaklaşık mesafe: "
                f"{value_or_dash(distance.get('target_km'))} km; "
                f"aralık "
                f"{value_or_dash(distance_range.get('min'))}–"
                f"{value_or_dash(distance_range.get('max'))} km; "
                "bağlayıcı değil"
            )

        add_ons = session.get("add_ons") or []
        for add_on in add_ons:
            add_on_duration = add_on.get("duration") or {}
            lines.append(
                "- Add-on: "
                f"{session_type_label(add_on.get('type'))}, "
                f"{_format_duration_range(add_on_duration)}, "
                "ana seansla aynı gün"
            )

        alternatives = _format_alternatives(scheduling)
        if alternatives:
            lines.append(
                f"- Esnek alternatif günler: {alternatives}"
            )

    unscheduled = weekly_plan.get("unscheduled_sessions") or []
    if unscheduled:
        lines.append("")
        lines.append("### Planlanamayan geçerli seanslar")

        for session in unscheduled:
            scheduling = session.get("scheduling") or {}
            lines.append(
                f"- {session_type_label(session.get('type'))}: "
                f"{value_or_dash(scheduling.get('reason'))}"
            )


def append_plan_reasons(
    lines: list[str],
    context: Dict[str, Any],
) -> None:
    reasons = _collect_plan_reasons(context)

    lines.append("\n## 5. Neden Bu Plan?")

    if not reasons:
        lines.append(
            "Mevcut karar artifact'i ek bir gerekçe taşımıyor."
        )
        return

    for reason in reasons:
        lines.append(f"- {reason}")


def append_metadata(
    lines: list[str],
    context: Dict[str, Any],
    weekly_plan: Dict[str, Any] | None,
) -> None:
    metadata = context.get("metadata", {})
    manual_context = context.get("manual_context", {})

    lines.append("\n## 6. Teknik Metadata")
    lines.append(
        "- Coach context schema: "
        f"{value_or_dash(context.get('schema_version'))}"
    )
    lines.append(
        "- Manual context schema: "
        f"{value_or_dash(manual_context.get('schema_version'))}"
    )
    lines.append(
        "- Engine version: "
        f"{value_or_dash(metadata.get('engine_version'))}"
    )
    lines.append(
        "- Decision engine: "
        f"{value_or_dash(metadata.get('decision_engine'))}"
    )
    lines.append(
        "- Coach context generated at: "
        f"{value_or_dash(metadata.get('generated_at'))}"
    )

    if not weekly_plan:
        lines.append("- Weekly plan artifact: Bulunamadı")
        return

    lines.append(
        "- Weekly plan schema: "
        f"{value_or_dash(weekly_plan.get('schema_version'))}"
    )
    lines.append(
        "- Planner version: "
        f"{value_or_dash(weekly_plan.get('planner_version'))}"
    )
    lines.append(
        "- Planning engine: "
        f"{value_or_dash(weekly_plan.get('planning_engine'))}"
    )
    lines.append(
        "- Planning stage: "
        f"{value_or_dash(weekly_plan.get('planning_stage'))}"
    )
    lines.append(
        "- Weekly plan generated at: "
        f"{value_or_dash(weekly_plan.get('generated_at'))}"
    )


__all__ = [
    "render_weekly_review",
]
