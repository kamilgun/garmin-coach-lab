from typing import Any, Dict


def value_or_dash(value):
    if value is None or value == "":
        return "-"
    return value


def bool_label(value):
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


def label(value):
    if value is None or value == "":
        return "-"
    if isinstance(value, bool):
        return bool_label(value)
    return LABELS.get(value, str(value))


def label_list(values):
    if not values:
        return "-"
    return ", ".join(label(value) for value in values)


def modality_label(value):
    modality_labels = {
        "running": "Koşu",
        "bike": "Bisiklet",
        "trainer": "Indoor trainer",
        "bike_or_trainer": "Bisiklet veya indoor trainer",
        "strength_or_mobility": "Mobilite/core",
    }
    return modality_labels.get(value, label(value))


def modality_label_list(values):
    if not values:
        return "-"
    return ", ".join(modality_label(value) for value in values)


def cycling_mode_label(value):
    cycling_mode_labels = {
        "bike": "Bisiklet",
        "trainer": "Indoor trainer",
        "bike_or_trainer": "Bisiklet veya indoor trainer",
        "none": "Uygun bisiklet/trainer imkanı yok",
    }
    return cycling_mode_labels.get(value, label(value))


def render_weekly_review(context: Dict[str, Any]) -> str:
    """
    Coach Context -> Markdown

    Bu renderer hesap yapmaz, karar vermez.
    Sadece hazır coach_context verisini okunabilir Markdown'a çevirir.
    """

    lines = []

    append_title(lines)
    append_activity_summary(lines, context)
    append_coach_intro(lines, context)
    append_targets(lines, context)
    append_load(lines, context)
    append_manual_context(lines, context)
    append_decision(lines, context)
    append_performance(lines, context)
    append_next_week(lines, context)
    append_metadata(lines, context)

    return "\n".join(lines)


def append_title(lines):
    lines.append("# Haftalık Garmin Coach Review\n")


def append_activity_summary(lines, context):
    metrics = context.get("metrics", {})

    lines.append("## Aktivite Özeti")
    lines.append(
        f"Son 7 günde {value_or_dash(metrics.get('activity_count_7_days'))} aktivite, "
        f"{value_or_dash(metrics.get('total_hours_7_days'))} saat, "
        f"{value_or_dash(metrics.get('weekly_distance_km'))} km."
    )
    lines.append(
        f"Son 30 günde {value_or_dash(metrics.get('activity_count_30_days'))} aktivite, "
        f"{value_or_dash(metrics.get('total_hours_30_days'))} saat, "
        f"{value_or_dash(metrics.get('monthly_distance_km'))} km."
    )


def append_coach_intro(lines, context):
    athlete = context.get("athlete", {})
    name = athlete.get("name")
    goal = athlete.get("primary_goal")

    lines.append("\n## Koç Yorumu")

    if name and goal:
        lines.append(
            f"Bu değerlendirme {name} için, "
            f"{goal} hedefi dikkate alınarak üretildi."
        )
    else:
        lines.append(
            "Bu değerlendirme mevcut coach context verilerine göre üretildi."
        )


def append_targets(lines, context):
    athlete = context.get("athlete", {})
    metrics = context.get("metrics", {})
    manual_context = context.get("manual_context", {})
    context_signals = context.get("context_signals", {})
    final_decision = context.get("final_decision", {})

    weekly_target = athlete.get("weekly_target", {})
    target_runs = weekly_target.get("running_sessions")
    target_cycling = weekly_target.get("cycling_sessions")
    target_mobility = weekly_target.get("strength_or_mobility_sessions")

    running_sessions = metrics.get("running_sessions")
    cycling_sessions = metrics.get("cycling_sessions")

    availability = manual_context.get("availability", {})
    running_available = context_signals.get(
        "running_available",
        availability.get(
            "running_available",
            manual_context.get("running_available", True),
        ),
    )
    cycling_available = context_signals.get("cycling_available")
    if cycling_available is None:
        bike_available = availability.get(
            "outdoor_bike_available",
            manual_context.get("bike_available", True),
        )
        trainer_available = availability.get(
            "indoor_trainer_available",
            manual_context.get("trainer_available", True),
        )
        cycling_available = bool(bike_available or trainer_available)

    strength_available = context_signals.get(
        "strength_available",
        availability.get("strength_available", True),
    )

    planning_limits = final_decision.get("planning_limits", {})
    max_sessions = planning_limits.get("max_sessions")

    lines.append("\n## Haftalık Hedef Durumu")

    if target_runs is not None:
        lines.append(f"- Koşu: {value_or_dash(running_sessions)}/{target_runs}")
        if not running_available:
            lines.append(
                "  Koşu bu hafta uygulanabilir olmadığı için hedef geçici olarak öncelik dışı."
            )
        elif running_sessions is not None and running_sessions >= target_runs:
            lines.append("  Koşu hedefi bu hafta tutmuş.")
        else:
            lines.append("  Koşu hedefi bu hafta tamamlanmamış.")
    else:
        lines.append("- Koşu hedefi tanımlı değil.")

    if target_cycling is not None:
        lines.append(f"- Bisiklet: {value_or_dash(cycling_sessions)}/{target_cycling}")
        if not cycling_available:
            lines.append(
                "  Bisiklet/trainer imkanı olmadığı için bu hafta bisiklet hedefi uygulanabilir değil."
            )
        elif cycling_sessions is not None and cycling_sessions >= target_cycling:
            lines.append("  Bisiklet hedefi bu hafta tutmuş.")
        else:
            lines.append("  Bisiklet hedefi bu hafta tamamlanmamış.")
    else:
        lines.append("- Bisiklet hedefi tanımlı değil.")

    if target_mobility is not None:
        if not strength_available:
            lines.append("- Mobilite/Core: Bu hafta uygun değil.")
        elif max_sessions == 1:
            lines.append(
                "- Mobilite/Core hedefi: Tek seans sınırı nedeniyle ayrı seans yerine "
                "ana antrenmana kısa bir ek çalışma olarak uygulanabilir."
            )
        else:
            lines.append(f"- Mobilite/Core hedefi: {target_mobility} seans")
    else:
        lines.append(
            "- Mobilite/Core: Garmin’den otomatik ölçülmüyor; manuel takip edilecek."
        )


def append_load(lines, context):
    metrics = context.get("metrics", {})
    rules = context.get("rules", {})

    lines.append("\n## Yük ve Progression Sinyali")
    lines.append(
        f"- Bu haftaki yük: "
        f"{value_or_dash(metrics.get('current_week_hours'))} saat"
    )
    lines.append(
        f"- 30 günlük haftalık ortalama: "
        f"{value_or_dash(metrics.get('rolling_30_weekly_hours'))} saat"
    )

    previous_23 = metrics.get("previous_23_weekly_hours")
    if previous_23 is not None:
        lines.append(f"- Önceki 23 güne göre haftalık tempo: {previous_23} saat")

    lines.append(
        f"- Kullanılan baseline: "
        f"{value_or_dash(metrics.get('weekly_baseline_hours'))} saat"
    )
    lines.append(f"- Load ratio: {value_or_dash(metrics.get('load_ratio'))}")
    lines.append(
        f"- Progression durumu: "
        f"{value_or_dash(rules.get('progression_label'))}"
    )

    progression_advice = rules.get("progression_advice")
    if progression_advice:
        lines.append(f"- Ham progression önerisi: {progression_advice}")

    context_adjustment = (
        context.get("final_decision", {}).get("context_adjustment")
        or context.get("context_signals", {}).get("adjustment_level")
    )
    if context_adjustment and context_adjustment != "none":
        lines.append(
            "- Final karar, bu ham sinyale haftalık check-in ve uygulanabilirlik "
            "kısıtlarını ekler."
        )


def append_manual_context(lines, context):
    manual_context = context.get("manual_context", {})
    context_signals = context.get("context_signals", {})
    final_decision = context.get("final_decision", {})

    availability = manual_context.get("availability", {})
    recovery = manual_context.get("recovery", {})
    pain = manual_context.get("pain", {})
    life_load = manual_context.get("life_load", {})

    context_adjustment = final_decision.get(
        "context_adjustment",
        context_signals.get("adjustment_level", "none"),
    )
    context_override = bool(final_decision.get("context_override_applied"))

    lines.append("\n## Haftalık Check-in ve Yaşam Bağlamı")

    if context_adjustment == "none":
        lines.append(
            "Check-in bilgileri temel antrenman kararına ek bir kısıt getirmedi."
        )
    elif context_adjustment == "soft" and not context_override:
        lines.append(
            "Yaşam bağlamı temel antrenman kararını tamamen değiştirmedi; "
            "ancak planı uygulanabilir süre, seans ve antrenman türü sınırları içinde tuttu."
        )
    elif context_adjustment == "soft":
        lines.append(
            "Haftalık check-in temel kararı yumuşattı ve planı daha uygulanabilir hale getirdi."
        )
    elif context_adjustment == "strong":
        lines.append(
            "Toparlanma, sağlık veya yaşam yükü sinyalleri planı belirgin biçimde yumuşattı."
        )
    else:
        lines.append(
            "Sağlık veya uygulanabilirlik sinyalleri nedeniyle koruyucu kısıtlamalar devreye girdi."
        )

    lines.append(
        f"- Haftanın önceliği: "
        f"{label(manual_context.get('weekly_intent'))}"
    )
    lines.append(
        f"- Gerçekçi seans sınırı: "
        f"{value_or_dash(availability.get('max_sessions'))}"
    )
    lines.append(
        f"- Bir seans için üst süre: "
        f"{value_or_dash(availability.get('max_session_duration_min'))} dakika"
    )

    available_days = availability.get("available_days") or []
    if available_days:
        lines.append(f"- Uygun günler: {label_list(available_days)}")

    lines.append(f"- Enerji: {label(recovery.get('energy_level'))}")
    lines.append(f"- Uyku / toparlanma: {label(recovery.get('sleep_quality'))}")
    lines.append(f"- Mental yorgunluk: {label(recovery.get('mental_fatigue'))}")
    lines.append(f"- Kas yorgunluğu: {label(recovery.get('muscle_soreness'))}")
    lines.append(f"- Hastalık durumu: {label(recovery.get('illness_status', 'none'))}")

    lines.append(f"- İş yükü: {label(life_load.get('work_stress'))}")
    lines.append(f"- Aile yükü: {label(life_load.get('family_load'))}")
    lines.append(f"- Bakım sorumluluğu: {label(life_load.get('caregiving_load'))}")
    lines.append(f"- Zaman baskısı: {label(life_load.get('time_pressure'))}")
    lines.append(f"- Duygusal yük: {label(life_load.get('emotional_load'))}")
    lines.append(f"- Seyahat: {bool_label(life_load.get('travel'))}")
    lines.append(
        f"- Rutin bozulması: {label(life_load.get('routine_disruption'))}"
    )

    lines.append(
        f"- Koşu mümkün: "
        f"{bool_label(availability.get('running_available'))}"
    )
    lines.append(
        f"- Outdoor bisiklet mümkün: "
        f"{bool_label(availability.get('outdoor_bike_available'))}"
    )
    lines.append(
        f"- Indoor trainer mümkün: "
        f"{bool_label(availability.get('indoor_trainer_available'))}"
    )
    lines.append(
        f"- Mobilite/core mümkün: "
        f"{bool_label(availability.get('strength_available'))}"
    )

    if pain.get("active_pain"):
        lines.append(
            f"- Aktif ağrı: {label(pain.get('pain_area'))}; "
            f"şiddet {value_or_dash(pain.get('pain_severity'))}/10"
        )
        lines.append(
            f"- Koşu sırasında artıyor: "
            f"{bool_label(pain.get('pain_during_running'))}"
        )
        if pain.get("pain_note"):
            lines.append(f"- Ağrı notu: {pain.get('pain_note')}")
    else:
        lines.append("- Aktif ağrı: Yok")

    context_reasons = final_decision.get(
        "context_reasons",
        context_signals.get("reasons", []),
    )
    if context_reasons:
        lines.append("- Planı etkileyen context sinyalleri:")
        for reason in context_reasons:
            lines.append(f"  - {reason}")

    user_note = manual_context.get("user_note")
    if user_note:
        lines.append(f"- Kullanıcı notu: {user_note}")


def append_decision(lines, context):
    final_decision = context.get("final_decision", {})
    rules = context.get("rules", {})
    planning_limits = final_decision.get("planning_limits", {})

    lines.append("\n## Koç Kararı")
    lines.append(f"- Haftalık yük: {label(final_decision.get('weekly_load'))}")
    lines.append(f"- Koşu: {label(final_decision.get('running'))}")
    lines.append(f"- Bisiklet/Trainer: {label(final_decision.get('cycling'))}")
    lines.append(
        f"- Mobilite/Core: "
        f"{label(final_decision.get('strength_or_mobility'))}"
    )
    lines.append(f"- Öncelik: {label(final_decision.get('priority'))}")
    lines.append(
        f"- Context uyarlaması: "
        f"{label(final_decision.get('context_adjustment'))}"
    )
    lines.append(
        f"- Antrenman yükü riski: "
        f"{label(rules.get('training_load_risk_level', rules.get('risk_level')))}"
    )
    lines.append(
        f"- Context riski: "
        f"{label(rules.get('context_risk_level'))}"
    )
    lines.append(f"- Birleşik risk seviyesi: {label(rules.get('risk_level'))}")
    lines.append(f"- Interval izni: {bool_label(rules.get('intervals_allowed'))}")

    if planning_limits:
        lines.append(
            f"- Plan sınırı: en fazla "
            f"{value_or_dash(planning_limits.get('max_sessions'))} seans, "
            f"seans başına "
            f"{value_or_dash(planning_limits.get('max_session_duration_min'))} dakika"
        )
        modalities = planning_limits.get("available_modalities") or []
        if modalities:
            lines.append(
                f"- Kullanılabilir antrenman türleri: "
                f"{modality_label_list(modalities)}"
            )

    reason = final_decision.get("reason")
    if reason:
        lines.append("")
        lines.append(reason)


def append_performance(lines, context):
    performance = context.get("performance", {})
    race = performance.get("race_predictor")

    lines.append("\n## Performans Göstergeleri")

    if not race:
        lines.append("Garmin Race Predictor verisi bulunamadı.")
        return

    lines.append(
        f"Garmin Race Predictor tarihi: "
        f"{value_or_dash(race.get('calendar_date'))}"
    )
    lines.append(f"- 5K: {value_or_dash(race.get('5k'))}")
    lines.append(f"- 10K: {value_or_dash(race.get('10k'))}")
    lines.append(
        f"- Yarı maraton: "
        f"{value_or_dash(race.get('half_marathon'))}"
    )
    lines.append(f"- Maraton: {value_or_dash(race.get('marathon'))}")
    lines.append(
        "Garmin performans tahminleri bir kondisyon sinyalidir; "
        "doğrudan yarış hedefi olarak yorumlanmamalıdır."
    )


def append_next_week(lines, context):
    final_decision = context.get("final_decision", {})
    rules = context.get("rules", {})
    metrics = context.get("metrics", {})
    manual_context = context.get("manual_context", {})

    weekly_load = final_decision.get("weekly_load")
    running = final_decision.get("running")
    cycling = final_decision.get("cycling")
    strength = final_decision.get("strength_or_mobility")
    intervals_allowed = rules.get("intervals_allowed")
    avg_hr_7_days = metrics.get("avg_hr_7_days")

    planning_limits = final_decision.get("planning_limits", {})
    max_sessions = planning_limits.get("max_sessions")
    max_duration = planning_limits.get("max_session_duration_min")
    cycling_session_text = final_decision.get("cycling_session_text")
    health_constraint = final_decision.get("health_constraint")
    pain = manual_context.get("pain", {})

    lines.append("\n## Gelecek Hafta Uygulama Çerçevesi")

    if max_sessions is not None:
        lines.append(
            f"- Toplam yapılandırılmış antrenman sayısını "
            f"{max_sessions} seansla sınırla."
        )
    if max_duration is not None:
        lines.append(
            f"- Her seansı en fazla {max_duration} dakika içinde tut."
        )

    if health_constraint == "active_illness":
        lines.append(
            "- Aktif hastalık nedeniyle bu hafta yapılandırılmış antrenman planlama; "
            "öncelik dinlenme ve toparlanma."
        )
        lines.append(
            "- Belirtiler sürerse veya kötüleşirse profesyonel sağlık desteği al."
        )
        return

    if weekly_load in ["reduce", "reduce_or_maintain"]:
        lines.append(
            "- Yükü artırma; kısa, kolay ve sürdürülebilir seçenekleri tercih et."
        )
    elif weekly_load == "maintain":
        lines.append("- Mevcut ritmi koru; ekstra yük ekleme.")
    elif weekly_load == "controlled_build":
        lines.append("- Hacim artacaksa küçük ve kontrollü tut.")
    elif weekly_load == "restart_easy":
        lines.append("- Öncelik kolay bir şekilde yeniden düzen kurmak.")
    else:
        lines.append("- Kontrollü kal; ani yük artışı yapma.")

    if running in ["easy_only", "maintain_easy"]:
        lines.append("- Koşu seçilirse kolay tempoda kal.")
    elif running == "controlled_increase":
        lines.append("- Koşu hacmi yalnızca küçük bir adımla artırılabilir.")
    elif running == "not_available":
        lines.append("- Koşu bu hafta plana alınmamalı.")

    if cycling in ["add_easy_z2", "add_or_maintain_z2"]:
        session_text = cycling_session_text or "kolay Z2 bisiklet/trainer seansı"
        if max_sessions == 1 and running != "not_available":
            lines.append(
                f"- Tek seans sınırı nedeniyle {session_text} ile koşuyu iki ayrı "
                "zorunlu seans gibi toplama; önceliğe uygun olanı seç."
            )
        else:
            lines.append(f"- {session_text.capitalize()} planlanabilir.")
    elif cycling in ["optional_easy_z2", "optional_recovery", "recovery_only"]:
        session_text = cycling_session_text or "kolay bisiklet/trainer seansı"
        if max_sessions == 1 and running != "not_available":
            lines.append(
                f"- {session_text.capitalize()} yalnızca koşunun yerine geçen "
                "opsiyonel alternatif olarak düşünülebilir."
            )
        else:
            lines.append(f"- {session_text.capitalize()} opsiyonel tutulmalı.")
    elif cycling == "not_available":
        lines.append("- Bisiklet/trainer bu hafta plana alınmamalı.")

    if not intervals_allowed:
        lines.append("- Sert interval veya tempo çalışması ekleme.")
    else:
        lines.append(
            "- Interval teorik olarak mümkün olsa da final karardaki sınırları aşma."
        )

    if avg_hr_7_days and avg_hr_7_days >= 150:
        lines.append(
            "- Son 7 günlük ortalama nabız yüksek olduğu için ekstra kontrollü kal."
        )

    if strength in ["recommended", "recommended_light", "optional"]:
        if max_sessions == 1:
            lines.append(
                "- Mobilite/core için ayrı seans açmak yerine ana antrenmanın sonuna "
                "5–10 dakikalık kısa bir ek çalışma koyabilirsin."
            )
        elif strength == "optional":
            lines.append(
                "- Mobilite/core opsiyonel bir destek çalışması olarak kalabilir."
            )
        else:
            lines.append("- Kısa bir mobilite/core çalışması eklenebilir.")
    elif strength == "not_recommended":
        lines.append("- Bu hafta ayrıca mobilite/core seansı önerilmiyor.")

    if pain.get("active_pain"):
        lines.append(
            "- Ağrı artarsa veya hareketi değiştirirse antrenmanı durdur ve "
            "profesyonel değerlendirme al."
        )


def append_metadata(lines, context):
    metadata = context.get("metadata", {})

    lines.append("\n## Sistem Bilgisi")
    lines.append(
        f"- Engine version: "
        f"{value_or_dash(metadata.get('engine_version'))}"
    )
    lines.append(
        f"- Decision engine: "
        f"{value_or_dash(metadata.get('decision_engine'))}"
    )
    lines.append(
        f"- Generated at: "
        f"{value_or_dash(metadata.get('generated_at'))}"
    )
