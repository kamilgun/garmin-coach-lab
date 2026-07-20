from typing import Any, Dict


def value_or_dash(value):
    if value is None:
        return "-"
    return value


def bool_label(value):
    if value is True:
        return "Evet"
    if value is False:
        return "Hayır"
    return "-"

LABELS = {
    "normal": "Normal",
    "child_sick": "Çocuk hasta",
    "high": "Yüksek",
    "very_high": "Çok yüksek",
    "low": "Düşük",
    "very_low": "Çok düşük",

    "maintain": "Mevcut yükü koru",
    "reduce": "Yükü azalt",
    "reduce_or_maintain": "Yükü azalt veya koru",
    "controlled_build": "Kontrollü gelişim",
    "restart_easy": "Kolay başlangıç",

    "maintain_easy": "Kolay koşularla ritmi koru",
    "easy_only": "Sadece kolay koşu",
    "controlled_increase": "Kontrollü artır",

    "add_easy_z2": "Kolay Z2 bisiklet ekle",
    "optional_easy_z2": "Opsiyonel kolay Z2 bisiklet",
    "optional_recovery": "Opsiyonel recovery sürüş",
    "recovery_only": "Sadece recovery sürüş",

    "recommended": "Önerilir",
    "recommended_light": "Hafif mobilite/core önerilir",

    "bike": "Bisiklet öncelikli",
    "recovery": "Toparlanma öncelikli",
    "balanced": "Dengeli",
    "consistency": "Ritim / süreklilik",

    "medium": "Orta",
    "Sunday": "Pazar",
    "Monday": "Pazartesi",
    "Tuesday": "Salı",
    "Wednesday": "Çarşamba",
    "Thursday": "Perşembe",
    "Friday": "Cuma",
    "Saturday": "Cumartesi",

    "not_available": "Bu hafta uygun değil",
    "running_consistency": "Koşu ritmini koruma",
    "vacation": "Tatil",
    "home": "Ev rutini",
    "family_busy": "Aile yoğun",
}


def label(value):
    if value is None:
        return "-"
    return LABELS.get(value, value)


def label_list(values):
    if not values:
        return "-"
    return ", ".join(label(value) for value in values)

def render_weekly_review(context: Dict[str, Any]) -> str:
    """
    Coach Context -> Markdown

    Bu renderer hesap yapmaz, karar vermez.
    Sadece hazır coach_context verisini markdown formatına çevirir.
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

    weekly_target = athlete.get("weekly_target", {})

    target_runs = weekly_target.get("running_sessions")
    target_cycling = weekly_target.get("cycling_sessions")
    target_mobility = weekly_target.get("strength_or_mobility_sessions")

    running_sessions = metrics.get("running_sessions")
    cycling_sessions = metrics.get("cycling_sessions")

    bike_available = manual_context.get("bike_available", True)
    trainer_available = manual_context.get("trainer_available", True)
    bike_unavailable = bike_available is False or trainer_available is False

    lines.append("\n## Haftalık Hedef Durumu")

    if target_runs is not None:
        lines.append(f"- Koşu: {value_or_dash(running_sessions)}/{target_runs}")

        if running_sessions is not None and running_sessions >= target_runs:
            lines.append("  Koşu hedefi bu hafta tutmuş.")
        else:
            lines.append("  Koşu hedefi bu hafta tamamlanmamış.")
    else:
        lines.append("- Koşu hedefi tanımlı değil.")

    if target_cycling is not None:
        lines.append(f"- Bisiklet: {value_or_dash(cycling_sessions)}/{target_cycling}")

        if bike_unavailable:
            lines.append(
                "  Bisiklet/trainer imkanı olmadığı için bu hafta bisiklet hedefi uygulanabilir değil."
            )
        elif cycling_sessions is not None and cycling_sessions >= target_cycling:
            lines.append("  Bisiklet hedefi bu hafta tutmuş.")
        else:
            lines.append(
                "  Bisiklet hedefi bu hafta tamamlanmamış; öncelik buraya verilmeli."
            )
    else:
        lines.append("- Bisiklet hedefi tanımlı değil.")

    if target_mobility is not None:
        lines.append(f"- Mobilite/Core hedefi: {target_mobility} seans")
    else:
        lines.append("- Mobilite/Core: Garmin’den otomatik ölçülmüyor; manuel takip edilecek.")

    


def append_load(lines, context):
    metrics = context.get("metrics", {})
    rules = context.get("rules", {})

    lines.append("\n## Yük ve Progression Sinyali")

    lines.append(f"- Bu haftaki yük: {value_or_dash(metrics.get('current_week_hours'))} saat")
    lines.append(
        f"- 30 günlük haftalık ortalama: "
        f"{value_or_dash(metrics.get('rolling_30_weekly_hours'))} saat"
    )

    previous_23 = metrics.get("previous_23_weekly_hours")
    if previous_23 is not None:
        lines.append(f"- Önceki 23 güne göre haftalık tempo: {previous_23} saat")

    lines.append(f"- Kullanılan baseline: {value_or_dash(metrics.get('weekly_baseline_hours'))} saat")
    lines.append(f"- Load ratio: {value_or_dash(metrics.get('load_ratio'))}")
    lines.append(f"- Progression durumu: {value_or_dash(rules.get('progression_label'))}")

    progression_advice = rules.get("progression_advice")
    if progression_advice:
        lines.append(progression_advice)


def append_manual_context(lines, context):
    manual_context = context.get("manual_context", {})
    final_decision = context.get("final_decision", {})

    lines.append("\n## Yaşam Bağlamı")

    if final_decision.get("context_override_applied"):
        lines.append(
            "Bu hafta manuel yaşam bağlamı kararı etkiledi. "
            "Bu nedenle plan normal rule kararına göre yumuşatıldı."
        )
    else:
        lines.append("Bu hafta kararı değiştiren özel bir manuel yaşam bağlamı yok.")

    lines.append(f"- Aile durumu: {label(manual_context.get('family_status'))}")
    lines.append(f"- İş yoğunluğu: {label(manual_context.get('workload'))}")
    lines.append(f"- Enerji seviyesi: {label(manual_context.get('energy_level'))}")
    lines.append(f"- Seyahat: {bool_label(manual_context.get('travel'))}")
    lines.append(f"- Uyku bölündü mü?: {bool_label(manual_context.get('sleep_disrupted'))}")

    lines.append(
    f"- Antrenman ortamı: {label(manual_context.get('training_environment'))}"
    )
    lines.append(
        f"- Bisiklet imkanı: {bool_label(manual_context.get('bike_available'))}"
    )
    lines.append(
        f"- Trainer imkanı: {bool_label(manual_context.get('trainer_available'))}"
    )
    lines.append(
        f"- Koşu imkanı: {bool_label(manual_context.get('running_available'))}"
    )

    injury_notes = manual_context.get("injury_notes")
    if injury_notes:
        lines.append(f"- Ağrı / sakatlık notu: {injury_notes}")

    available_days = manual_context.get("available_days") or []
    if available_days:
        lines.append(f"- Uygun günler: {label_list(available_days)}")

    user_note = manual_context.get("user_note")
    if user_note:
        lines.append(f"- Kullanıcı notu: {user_note}")


def append_decision(lines, context):
    final_decision = context.get("final_decision", {})
    rules = context.get("rules", {})

    lines.append("\n## Koç Kararı")

    lines.append(f"- Haftalık yük: {label(final_decision.get('weekly_load'))}")
    lines.append(f"- Koşu: {label(final_decision.get('running'))}")
    lines.append(f"- Bisiklet: {label(final_decision.get('cycling'))}")
    lines.append(
        f"- Mobilite/Core: "
        f"{label(final_decision.get('strength_or_mobility'))}"
    )
    lines.append(f"- Öncelik: {label(final_decision.get('priority'))}")
    lines.append(f"- Risk seviyesi: {label(rules.get('risk_level'))}")
    lines.append(f"- Interval izni: {bool_label(rules.get('intervals_allowed'))}")

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

    lines.append(f"Garmin Race Predictor tarihi: {value_or_dash(race.get('calendar_date'))}")
    lines.append(f"- 5K: {value_or_dash(race.get('5k'))}")
    lines.append(f"- 10K: {value_or_dash(race.get('10k'))}")
    lines.append(f"- Yarı maraton: {value_or_dash(race.get('half_marathon'))}")
    lines.append(f"- Maraton: {value_or_dash(race.get('marathon'))}")

    lines.append(
        "Garmin performans tahminleri iyi bir kondisyon sinyali veriyor; "
        "ancak son 30 günlük hacim düşük olduğu için bunları şu aşamada doğrudan "
        "yarış hedefi değil, mevcut potansiyel göstergesi olarak okumak daha doğru."
    )


def append_next_week(lines, context):
    final_decision = context.get("final_decision", {})
    rules = context.get("rules", {})
    metrics = context.get("metrics", {})

    weekly_load = final_decision.get("weekly_load")
    running = final_decision.get("running")
    cycling = final_decision.get("cycling")
    intervals_allowed = rules.get("intervals_allowed")
    avg_hr_7_days = metrics.get("avg_hr_7_days")

    lines.append("\n## Gelecek Hafta Önerisi")

    if weekly_load in ["reduce", "reduce_or_maintain"]:
        lines.append("- Bu hafta yükü artırma; kolay ve kısa seanslar öncelikli olsun.")
    elif weekly_load == "maintain":
        lines.append("- Bu hafta koşu hacmini artırmadan mevcut ritmi koru.")
    elif weekly_load == "controlled_build":
        lines.append("- Hacim artırılacaksa küçük ve kontrollü artır.")
    elif weekly_load == "restart_easy":
        lines.append("- Öncelik yeniden düzen kurmak; 1 kolay koşu yeterli olabilir.")
    else:
        lines.append("- Genel yaklaşım: kontrollü kal, ani yük artışı yapma.")

    if running in ["easy_only", "maintain_easy"]:
        lines.append("- Koşular kolay tempoda kalmalı.")
    elif running == "controlled_increase":
        lines.append("- Koşuda küçük bir hacim artışı yapılabilir.")

    if cycling == "add_easy_z2":
        lines.append("- 30-45 dk kolay Z2 trainer seansı ekle.")
    elif cycling == "optional_easy_z2":
        lines.append("- Uygunsa kısa ve kolay bir Z2 trainer seansı ekle.")
    elif cycling == "optional_recovery":
        lines.append("- Bisiklet sadece opsiyonel recovery sürüş olarak düşünülsün.")
    elif cycling == "recovery_only":
        lines.append("- Bisiklet varsa sadece çok kolay recovery olmalı.")
    elif cycling == "not_available":
        lines.append("- Bu hafta bisiklet/trainer imkanı olmadığı için bisiklet antrenmanı plana alınmadı.")

    if intervals_allowed:
        lines.append("- Interval teorik olarak mümkün; yine de bu hafta öncelik Z2 olmalı.")
    else:
        lines.append("- Bu hafta sert interval ekleme.")

    if avg_hr_7_days and avg_hr_7_days >= 150:
        lines.append("- Ortalama nabız yüksek olduğu için ekstra dikkatli kal.")

    injury_notes = context.get("manual_context", {}).get("injury_notes")

    if injury_notes:
        lines.append(
            "- 1 mobilite veya core seansı ekle; mevcut ağrı/sakatlık notunu dikkate al."
        )
    else:
        lines.append(
            "- 1 mobilite veya core seansı ekle; genel hareket kalitesini destekle."
        )
    

def append_metadata(lines, context):
    metadata = context.get("metadata", {})

    lines.append("\n## Sistem Bilgisi")
    lines.append(f"- Engine version: {value_or_dash(metadata.get('engine_version'))}")
    lines.append(f"- Decision engine: {value_or_dash(metadata.get('decision_engine'))}")
    lines.append(f"- Generated at: {value_or_dash(metadata.get('generated_at'))}")