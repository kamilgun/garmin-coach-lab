"""Context Model v2 signal derivation and decision constraints.

This module translates structured weekly check-in data into deterministic,
explainable signals. It does not generate training plans and does not use an LLM.
"""

def _max_adjustment_level(*levels):
    ranking = {
        "none": 0,
        "soft": 1,
        "strong": 2,
        "hard": 3,
    }
    return max(levels, key=lambda level: ranking.get(level, 0))


def _max_risk_level(*levels):
    ranking = {
        "low": 0,
        "medium": 1,
        "high": 2,
    }
    return max(levels, key=lambda level: ranking.get(level, 0))


def get_cycling_availability(manual_context):
    availability = manual_context.get("availability", {})

    bike_available = bool(
        availability.get(
            "outdoor_bike_available",
            manual_context.get("bike_available", True),
        )
    )
    trainer_available = bool(
        availability.get(
            "indoor_trainer_available",
            manual_context.get("trainer_available", True),
        )
    )

    if bike_available and trainer_available:
        return {
            "available": True,
            "mode": "bike_or_trainer",
            "session_text": "kolay Z2 bisiklet/trainer seansı",
            "unavailable_text": None,
        }

    if trainer_available:
        return {
            "available": True,
            "mode": "trainer",
            "session_text": "kolay Z2 trainer seansı",
            "unavailable_text": None,
        }

    if bike_available:
        return {
            "available": True,
            "mode": "bike",
            "session_text": "kolay Z2 bisiklet seansı",
            "unavailable_text": None,
        }

    return {
        "available": False,
        "mode": "none",
        "session_text": None,
        "unavailable_text": (
            "Bu hafta dışarıda bisiklet veya indoor trainer imkanı olmadığı için "
            "bisiklet önerisi uygulanabilir değil"
        ),
    }


def derive_context_signals(manual_context):
    availability = manual_context.get("availability", {})
    recovery = manual_context.get("recovery", {})
    pain = manual_context.get("pain", {})
    life_load = manual_context.get("life_load", {})

    max_sessions = availability.get("max_sessions", 3)
    max_session_duration_min = availability.get("max_session_duration_min", 50)
    available_days = availability.get("available_days", []) or []

    running_available = bool(
        availability.get(
            "running_available",
            manual_context.get("running_available", True),
        )
    )
    strength_available = bool(availability.get("strength_available", True))
    cycling_availability = get_cycling_availability(manual_context)

    available_modalities = []
    if running_available:
        available_modalities.append("running")
    if cycling_availability["available"]:
        available_modalities.append(cycling_availability["mode"])
    if strength_available:
        available_modalities.append("strength_or_mobility")

    reasons = []

    if max_sessions == 1:
        reasons.append("Bu hafta en fazla 1 antrenman gerçekçi.")
    elif max_sessions == 2:
        reasons.append("Bu hafta en fazla 2 antrenman gerçekçi.")

    if max_session_duration_min <= 30:
        reasons.append(
            f"Bir antrenman için süre sınırı {max_session_duration_min} dakika."
        )
    elif max_session_duration_min <= 45:
        reasons.append(
            f"Bir antrenman için üst süre {max_session_duration_min} dakika."
        )

    health_constraint = "none"
    health_adjustment = "none"
    context_risk_level = "low"
    intervals_blocked = False
    override_required = False

    illness_status = recovery.get("illness_status", "none")
    active_pain = bool(pain.get("active_pain", False))
    pain_severity = int(pain.get("pain_severity", 0) or 0)
    pain_during_running = bool(pain.get("pain_during_running", False))

    if illness_status == "active":
        health_constraint = "active_illness"
        health_adjustment = "hard"
        context_risk_level = "high"
        intervals_blocked = True
        override_required = True
        reasons.append(
            "Aktif hastalık bildirildiği için antrenman yerine toparlanma öncelikli olmalı."
        )
    elif illness_status == "recovering":
        health_constraint = "recovering_illness"
        health_adjustment = "strong"
        context_risk_level = "medium"
        intervals_blocked = True
        override_required = True
        reasons.append(
            "Hastalıktan dönüş döneminde yük artışı yerine kolay ve kısa antrenman tercih edilmeli."
        )

    if active_pain and health_constraint != "active_illness":
        if pain_during_running or pain_severity >= 7:
            health_constraint = "running_pain"
            health_adjustment = "hard"
            context_risk_level = "high"
            reasons.append(
                "Koşu sırasında artan veya belirgin ağrı nedeniyle koşu önerisi kısıtlanmalı."
            )
        elif pain_severity >= 4:
            health_constraint = "moderate_pain"
            health_adjustment = "strong"
            context_risk_level = "medium"
            reasons.append(
                "Aktif orta düzey ağrı nedeniyle haftalık yük yumuşatılmalı."
            )
        else:
            health_constraint = "mild_pain"
            health_adjustment = "strong"
            context_risk_level = "medium"
            reasons.append(
                "Aktif hafif ağrı bildirildiği için performans artışı yerine kontrollü hareket edilmeli."
            )

        intervals_blocked = True
        override_required = True

    sleep_quality = recovery.get("sleep_quality", "okay")
    energy_level = recovery.get("energy_level", "normal")
    mental_fatigue = recovery.get("mental_fatigue", "medium")
    muscle_soreness = recovery.get("muscle_soreness", "low")

    recovery_constraint = "none"
    recovery_adjustment = "none"

    if energy_level == "very_low" or (
        energy_level == "low" and sleep_quality == "poor"
    ):
        recovery_constraint = "strong"
        recovery_adjustment = "strong"
        context_risk_level = _max_risk_level(context_risk_level, "medium")
        intervals_blocked = True
        override_required = True
        reasons.append(
            "Düşük enerji ve yetersiz toparlanma nedeniyle yük artırılmamalı."
        )
    elif (
        energy_level == "low"
        or sleep_quality == "poor"
        or mental_fatigue == "high"
        or muscle_soreness in ["medium", "high"]
    ):
        recovery_constraint = "soft"
        recovery_adjustment = "soft"
        intervals_blocked = True
        reasons.append(
            "Toparlanma sinyalleri nedeniyle yoğunluk ve hacim kontrollü tutulmalı."
        )

    life_score = 0
    non_travel_life_score = 0

    work_stress = life_load.get("work_stress", "normal")
    family_load = life_load.get("family_load", "normal")
    caregiving_load = life_load.get("caregiving_load", "low")
    routine_disruption = life_load.get("routine_disruption", "low")
    time_pressure = life_load.get("time_pressure", "normal")
    emotional_load = life_load.get("emotional_load", "normal")
    travel = bool(life_load.get("travel", False))

    if work_stress == "very_high":
        life_score += 2
        non_travel_life_score += 2
    elif work_stress == "high":
        life_score += 1
        non_travel_life_score += 1

    if family_load == "high":
        life_score += 1
        non_travel_life_score += 1

    if caregiving_load == "high":
        life_score += 2
        non_travel_life_score += 2
    elif caregiving_load == "medium":
        life_score += 1
        non_travel_life_score += 1

    if routine_disruption == "high":
        life_score += 2
        non_travel_life_score += 1
    elif routine_disruption == "medium":
        life_score += 1

    if time_pressure == "high":
        life_score += 1
        non_travel_life_score += 1

    if emotional_load == "high":
        life_score += 1
        non_travel_life_score += 1

    life_constraint = "none"
    life_adjustment = "none"

    if life_score >= 3:
        life_constraint = "strong"
        life_adjustment = "strong"
        context_risk_level = _max_risk_level(context_risk_level, "medium")
        intervals_blocked = True
        override_required = True
        reasons.append(
            "Toplam hayat yükü yüksek olduğu için plan sadeleştirilmeli ve yük artırılmamalı."
        )
    elif life_score >= 1:
        life_constraint = "soft"
        life_adjustment = "soft"

    if travel:
        reasons.append(
            "Seyahat nedeniyle planın gün ve antrenman türü açısından esnek kalması önemli."
        )

    availability_constraint = "none"
    availability_adjustment = "none"

    if not available_modalities:
        availability_constraint = "no_available_modality"
        availability_adjustment = "hard"
        context_risk_level = _max_risk_level(context_risk_level, "high")
        intervals_blocked = True
        override_required = True
        reasons.append("Bu hafta uygulanabilir bir antrenman türü seçilmedi.")
    elif max_sessions <= 1:
        availability_constraint = "very_limited"
        availability_adjustment = "soft"
    elif max_sessions == 2:
        availability_constraint = "limited"
        availability_adjustment = "soft"
    elif not running_available or not cycling_availability["available"]:
        availability_constraint = "limited_modalities"
        availability_adjustment = "soft"

    weekly_intent = manual_context.get("weekly_intent", "maintain_consistency")
    intent_adjustment = "none"

    if weekly_intent == "recover":
        intent_adjustment = "soft"
        intervals_blocked = True
        override_required = True
        reasons.append("Bu haftanın seçilen önceliği toparlanmak.")
    elif weekly_intent == "return_after_break":
        intent_adjustment = "soft"
        intervals_blocked = True
        override_required = True
        reasons.append("Bu haftanın seçilen önceliği aradan sonra kontrollü dönüş.")

    adjustment_level = _max_adjustment_level(
        health_adjustment,
        recovery_adjustment,
        life_adjustment,
        availability_adjustment,
        intent_adjustment,
    )

    softening_required = (
        recovery_constraint == "soft"
        or non_travel_life_score >= 1
        or routine_disruption == "high"
    )

    return {
        "adjustment_level": adjustment_level,
        "health_constraint": health_constraint,
        "recovery_constraint": recovery_constraint,
        "life_constraint": life_constraint,
        "availability_constraint": availability_constraint,
        "context_risk_level": context_risk_level,
        "intervals_blocked": intervals_blocked,
        "override_required": override_required,
        "softening_required": softening_required,
        "max_sessions": max_sessions,
        "max_session_duration_min": max_session_duration_min,
        "available_days": available_days,
        "weekly_intent": weekly_intent,
        "available_modalities": available_modalities,
        "running_available": running_available,
        "strength_available": strength_available,
        "cycling_available": cycling_availability["available"],
        "cycling_mode": cycling_availability["mode"],
        "reasons": reasons,
    }


def has_manual_context_override(manual_context):
    return derive_context_signals(manual_context)["override_required"]


def apply_context_signals_to_rules(rules, context_signals):
    effective_rules = dict(rules)
    training_load_risk = effective_rules.get("risk_level", "low")
    context_risk = context_signals.get("context_risk_level", "low")

    effective_rules["training_load_risk_level"] = training_load_risk
    effective_rules["context_risk_level"] = context_risk
    effective_rules["risk_level"] = _max_risk_level(
        training_load_risk,
        context_risk,
    )

    if context_signals.get("intervals_blocked"):
        effective_rules["intervals_allowed"] = False

    return effective_rules


def _append_decision_reason(decision, message):
    if not message:
        return

    current_reason = (decision.get("reason") or "").strip()
    if current_reason:
        decision["reason"] = f"{current_reason} {message}".strip()
    else:
        decision["reason"] = message.strip()


def apply_context_constraints(decision, manual_context, context_signals=None):
    context_signals = context_signals or derive_context_signals(manual_context)
    cycling_availability = get_cycling_availability(manual_context)

    decision = dict(decision)
    decision["cycling_mode"] = cycling_availability["mode"]
    decision["cycling_session_text"] = cycling_availability["session_text"]
    decision["weekly_intent"] = context_signals["weekly_intent"]
    decision["context_adjustment"] = context_signals["adjustment_level"]
    decision["health_constraint"] = context_signals["health_constraint"]
    decision["recovery_constraint"] = context_signals["recovery_constraint"]
    decision["life_constraint"] = context_signals["life_constraint"]
    decision["planning_limits"] = {
        "max_sessions": context_signals["max_sessions"],
        "max_session_duration_min": context_signals[
            "max_session_duration_min"
        ],
        "available_days": context_signals["available_days"],
        "available_modalities": context_signals["available_modalities"],
    }
    decision["context_reasons"] = list(context_signals["reasons"])

    health_constraint = context_signals["health_constraint"]
    weekly_intent = context_signals["weekly_intent"]

    if health_constraint == "active_illness":
        decision.update(
            {
                "weekly_load": "reduce",
                "running": "not_available",
                "cycling": "not_available",
                "strength_or_mobility": "not_recommended",
                "priority": "recovery",
                "context_override_applied": True,
                "reason": (
                    "Aktif hastalık bildirildiği için bu hafta yapılandırılmış antrenman "
                    "önerilmiyor; öncelik dinlenme ve toparlanma olmalı."
                ),
            }
        )

    elif health_constraint == "running_pain":
        decision.update(
            {
                "weekly_load": "reduce_or_maintain",
                "running": "not_available",
                "cycling": (
                    "optional_recovery"
                    if cycling_availability["available"]
                    else "not_available"
                ),
                "strength_or_mobility": (
                    "recommended_light"
                    if context_signals["strength_available"]
                    else "not_available"
                ),
                "priority": "recovery",
                "context_override_applied": True,
                "reason": (
                    "Koşu sırasında artan veya belirgin ağrı nedeniyle koşu bu hafta "
                    "önerilmiyor; yalnızca ağrısız ve düşük yoğunluklu alternatifler düşünülmeli."
                ),
            }
        )

    elif (
        health_constraint in ["recovering_illness", "moderate_pain", "mild_pain"]
        or context_signals["recovery_constraint"] == "strong"
        or context_signals["life_constraint"] == "strong"
        or weekly_intent == "recover"
    ):
        decision.update(
            {
                "weekly_load": "reduce_or_maintain",
                "running": (
                    "easy_only"
                    if context_signals["running_available"]
                    else "not_available"
                ),
                "cycling": (
                    "optional_recovery"
                    if cycling_availability["available"]
                    else "not_available"
                ),
                "strength_or_mobility": (
                    "recommended_light"
                    if context_signals["strength_available"]
                    else "not_available"
                ),
                "priority": "recovery",
                "context_override_applied": True,
                "reason": (
                    "Haftalık karar toparlanma, sağlık veya yaşam yükü sinyalleri "
                    "nedeniyle yumuşatıldı; kolay ve sürdürülebilir antrenman tercih edilmeli."
                ),
            }
        )

    elif weekly_intent == "return_after_break":
        decision.update(
            {
                "weekly_load": "restart_easy",
                "running": (
                    "easy_only"
                    if context_signals["running_available"]
                    else "not_available"
                ),
                "cycling": (
                    "optional_easy_z2"
                    if cycling_availability["available"]
                    else "not_available"
                ),
                "strength_or_mobility": (
                    "recommended_light"
                    if context_signals["strength_available"]
                    else "not_available"
                ),
                "priority": "consistency",
                "context_override_applied": True,
                "reason": (
                    "Aradan sonra dönüş niyeti nedeniyle öncelik performans artışı değil, "
                    "kolay ve düzenli antrenman ritmini yeniden kurmak."
                ),
            }
        )

    elif context_signals["softening_required"]:
        if decision.get("weekly_load") == "controlled_build":
            decision["weekly_load"] = "maintain"
            decision["running"] = "maintain_easy"
            decision["context_override_applied"] = True
            _append_decision_reason(
                decision,
                "Toparlanma veya yaşam yükü sinyalleri nedeniyle kontrollü artış bu hafta ertelendi.",
            )

    cycling_recommendations = {
        "add_easy_z2",
        "add_or_maintain_z2",
        "optional_easy_z2",
        "optional_recovery",
        "recovery_only",
        "recovery",
    }

    if (
        decision.get("cycling") in cycling_recommendations
        and not cycling_availability["available"]
    ):
        decision["cycling"] = "not_available"
        decision["cycling_session_text"] = None

        if decision.get("priority") in ["bike", "balanced"]:
            decision["priority"] = "running_consistency"

        _append_decision_reason(
            decision,
            (
                f"{cycling_availability['unavailable_text']}; öncelik uygun olan "
                "antrenman türlerine kaydırıldı."
            ),
        )

    if not context_signals["running_available"]:
        decision["running"] = "not_available"
        decision["priority"] = "recovery"
        decision["weekly_load"] = "reduce_or_maintain"
        decision["context_override_applied"] = True
        _append_decision_reason(
            decision,
            (
                "Bu hafta koşu imkanı olmadığı için koşu önerisi uygulanabilir değil; "
                "plan uygun düşük yoğunluklu alternatiflere göre sadeleştirildi."
            ),
        )

    if not context_signals["strength_available"]:
        decision["strength_or_mobility"] = "not_available"

    if (
        context_signals["max_sessions"] == 1
        and decision.get("strength_or_mobility")
        in ["recommended", "recommended_light"]
        and len(context_signals["available_modalities"]) > 1
    ):
        decision["strength_or_mobility"] = "optional"
        _append_decision_reason(
            decision,
            "Tek seans sınırı nedeniyle mobilite/core ayrı bir seans yerine kısa bir ek çalışma olabilir.",
        )

    user_facing_reason_prefixes = (
        "Bu hafta en fazla",
        "Bir antrenman için",
        "Seyahat nedeniyle",
    )
    for context_reason in context_signals["reasons"]:
        if context_reason.startswith(user_facing_reason_prefixes):
            _append_decision_reason(decision, context_reason)

    if decision.get("cycling") == "not_available":
        decision["cycling_session_text"] = None

    return decision

