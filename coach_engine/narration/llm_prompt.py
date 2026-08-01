from typing import Any, Dict
import json


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
    "not_available": "Bu hafta uygun değil",

    # Cycling
    "add_easy_z2": "Kolay Z2 bisiklet/trainer seansı ekle",
    "add_or_maintain_z2": "Kolay Z2 bisiklet/trainer seansını ekle veya koru",
    "optional_easy_z2": "Opsiyonel kolay Z2 bisiklet/trainer",
    "optional_recovery": "Opsiyonel toparlanma seansı",
    "recovery_only": "Sadece toparlanma seansı",

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

    # Context
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

    # Status / target
    "target_met": "Hedef tamamlandı",
    "below_target": "Hedefin altında",

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
        return label_bool(value)
    return LABELS.get(value, str(value))


def label_bool(value):
    if value is True:
        return "Evet"
    if value is False:
        return "Hayır"
    return "-"


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


def format_json_block(data: Dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)



def build_weekly_plan_prompt_payload(
    weekly_plan: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """
    LLM'e yalnızca anlatması gereken deterministic plan alanlarını taşır.
    Bu fonksiyon karar veya plan üretmez.
    """

    if not weekly_plan:
        return {
            "available": False,
            "plan_status": "unavailable",
            "instruction": (
                "Weekly plan artifact'i yok. Kesin tarih, süre, pace veya "
                "mesafe uydurma; yalnızca final decision ve planning limits "
                "çerçevesini anlat."
            ),
        }

    sessions = []

    for session in weekly_plan.get("sessions") or []:
        scheduling = session.get("scheduling") or {}
        duration = session.get("duration") or {}
        total_duration = session.get("session_total_duration") or {}
        intensity = session.get("intensity") or {}
        pace = session.get("pace_guidance") or {}
        distance = session.get("distance_guidance") or {}

        add_ons = []
        for add_on in session.get("add_ons") or []:
            add_on_duration = add_on.get("duration") or {}
            add_ons.append(
                {
                    "type": add_on.get("type"),
                    "modality": add_on.get("modality"),
                    "duration_target_min": add_on_duration.get("target_min"),
                    "duration_range_min": {
                        "min": add_on_duration.get("min"),
                        "max": add_on_duration.get("max"),
                    },
                    "same_day_as_main_session": True,
                }
            )

        session_payload = {
            "session_id": session.get("session_id"),
            "date": scheduling.get("date"),
            "day": scheduling.get("day"),
            "day_label_tr": scheduling.get("day_label_tr"),
            "type": session.get("type"),
            "modality": session.get("modality"),
            "duration_target_min": duration.get("target_min"),
            "duration_range_min": {
                "min": duration.get("min"),
                "max": duration.get("max"),
            },
            "session_total_duration_target_min": total_duration.get(
                "target_min"
            ),
            "session_total_duration_range_min": {
                "min": total_duration.get("min"),
                "max": total_duration.get("max"),
            },
            "intensity_cap": intensity.get("cap"),
            "intensity_primary_guidance": intensity.get(
                "primary_guidance"
            ),
            "pace_guidance": {
                "available": bool(pace.get("available")),
                "binding": pace.get("binding"),
                "target_reference_display": pace.get(
                    "target_reference_display"
                ),
                "range_display": pace.get("range_display"),
                "primary_guidance": pace.get("primary_guidance"),
                "note": pace.get("note"),
            },
            "distance_guidance": {
                "available": bool(distance.get("available")),
                "binding": distance.get("binding"),
                "target_km": distance.get("target_km"),
                "range_km": distance.get("range_km"),
                "note": distance.get("note"),
            },
            "add_ons": add_ons,
            "flexibility": (
                (scheduling.get("flexibility") or {}).get(
                    "alternative_dates"
                )
            ),
        }
        sessions.append(session_payload)

    unscheduled_sessions = []

    for session in weekly_plan.get("unscheduled_sessions") or []:
        scheduling = session.get("scheduling") or {}
        unscheduled_sessions.append(
            {
                "session_id": session.get("session_id"),
                "type": session.get("type"),
                "reason_code": scheduling.get("reason_code"),
                "reason": scheduling.get("reason"),
            }
        )

    return {
        "available": True,
        "plan_status": weekly_plan.get("plan_status"),
        "planning_horizon": weekly_plan.get("planning_horizon"),
        "week_focus": weekly_plan.get("week_focus"),
        "priority": weekly_plan.get("priority"),
        "session_count": weekly_plan.get("session_count"),
        "scheduled_count": weekly_plan.get("scheduled_count"),
        "unscheduled_count": weekly_plan.get("unscheduled_count"),
        "sessions": sessions,
        "unscheduled_sessions": unscheduled_sessions,
        "avoid": weekly_plan.get("avoid") or [],
        "planner_version": weekly_plan.get("planner_version"),
        "planning_engine": weekly_plan.get("planning_engine"),
    }


def build_llm_coach_prompt(
    context: Dict[str, Any],
    weekly_plan: Dict[str, Any] | None = None,
) -> str:
    athlete = context.get("athlete", {})
    metrics = context.get("metrics", {})
    performance = context.get("performance", {})
    rules = context.get("rules", {})
    manual_context = context.get("manual_context", {})
    context_signals = context.get("context_signals", {})
    final_decision = context.get("final_decision", {})
    metadata = context.get("metadata", {})

    availability = manual_context.get("availability", {})
    recovery = manual_context.get("recovery", {})
    pain = manual_context.get("pain", {})
    life_load = manual_context.get("life_load", {})

    planning_limits = final_decision.get("planning_limits", {})
    context_reasons = final_decision.get(
        "context_reasons",
        context_signals.get("reasons", []),
    )

    race_predictor = performance.get("race_predictor") or {}

    cycling_mode = final_decision.get("cycling_mode")
    cycling_session_text = final_decision.get("cycling_session_text")

    bike_available = availability.get(
        "outdoor_bike_available",
        manual_context.get("bike_available"),
    )
    trainer_available = availability.get(
        "indoor_trainer_available",
        manual_context.get("trainer_available"),
    )
    running_available = availability.get(
        "running_available",
        manual_context.get("running_available"),
    )
    strength_available = availability.get("strength_available")
    weekly_plan_payload = build_weekly_plan_prompt_payload(weekly_plan)

    prompt = f"""
Sen destekleyici, gerçekçi ve temkinli bir dayanıklılık sporu koçusun.

Aşağıdaki veriler deterministik karar ve planlama motorları tarafından hazırlanmış Coach Context ve Weekly Plan çıktılarıdır.
Senin görevin karar vermek veya yeni plan oluşturmak değil; verilmiş kararı ve varsa kesin haftalık planı kullanıcıya doğal, kısa ve uygulanabilir bir dille anlatmaktır.

KRİTİK TALİMATLAR:
- final_decision içindeki kararları değiştirme.
- planning_limits içindeki max_sessions ve max_session_duration_min değerleri kesin üst sınırlardır.
- planning_limits.available_modalities dışında bir antrenman türü önerme.
- weekly_plan.available true ise WEEKLY PLAN — DEĞİŞTİRME bölümündeki tarih, gün, seans türü, seans sayısı, süre, yoğunluk üst sınırı ve add-on kararlarını değiştirme.
- weekly_plan.available true ise kendin yeni gün, alternatif seans veya ekstra çalışma seçme; yalnızca planner tarafından verilen planı anlat.
- weekly_plan.available false ise kesin tarih, süre, pace veya mesafe uydurma; yalnızca final_decision ve planning_limits çerçevesinde konuş.
- Pace ve mesafe alanlarında binding false ise bunları kesin hedef değil, bağlayıcı olmayan yakın dönem referansı olarak anlat; kolay/konuşma temposundaki eforu öncele.
- plan_status "no_structured_training" ise hiçbir yapılandırılmış antrenman önermeme.
- plan_status "partially_scheduled" veya "unscheduled" ise planlanamayan seansları yapılması gereken ek görevler gibi sunma.
- available_days boş değilse weekly plan yokken antrenmanı yalnızca bu günlerle uyumlu anlat; kendin yeni gün seçme.
- Yeni yoğun antrenman, interval, tempo koşusu, uzun koşu veya ekstra seans ekleme.
- context_adjustment "soft" ise yaşam bağlamının temel kararı tamamen değiştirmediğini, fakat süre/seans/uygulanabilirlik sınırları getirdiğini doğal biçimde açıkla.
- context_adjustment "strong" veya "hard" ise planın sağlık, toparlanma ya da yaşam yükü nedeniyle belirgin biçimde yumuşatıldığını açıkla.
- context_reasons içindeki gerekçeleri göz ardı etme; bunları tekrara düşmeden doğal dile çevir.
- context_override_applied false olsa bile context_adjustment "soft" ise yaşam bağlamını yok sayma.
- Haftanın seçilen niyetini yönlendirici bağlam olarak kullan; ancak bunu güvenlik ve plan sınırlarının önüne geçirme.
- Kullanıcıyı suçlayıcı, baskılayıcı veya aşırı motive edici bir dil kullanma.
- Tıbbi teşhis koyma.
- manual_context.pain.active_pain true ise yalnızca yapılandırılmış ağrı alanlarına dayanarak temkinli konuş; ağrının yerini veya şiddetini uydurma.
- recovery.illness_status "active" veya "recovering" ise bunu sağlık bağlamı olarak dikkate al; hastalık yoksa hastalıktan bahsetme.
- athlete.injury_risks alanındaki bilgileri aktif sakatlık gibi sunma; bunlar yalnızca geçmiş hassasiyetlerdir.
- Aktif ağrı/sakatlık hakkında karar verirken legacy injury_notes yerine manual_context.pain alanını esas al.
- Garmin Race Predictor verisini doğrudan yarış hedefi gibi sunma; yalnızca potansiyel/kondisyon sinyali olarak yorumla.
- Bisiklet/trainer önerisi verirken final_decision.cycling_session_text ve cycling_mode alanlarını esas al.
- cycling_mode "trainer" ise dışarıda bisiklet sürüşü önerme; "indoor trainer" veya verilen session text ifadesini kullan.
- cycling_mode "bike" ise trainer önerme; "bisiklet seansı" ifadesini kullan.
- cycling_mode "bike_or_trainer" ise "bisiklet/trainer seansı" diyebilirsin.
- cycling_mode "none" veya final_decision.cycling "not_available" ise bisiklet/trainer antrenmanı önerme.
- bike_available false ama trainer_available true ise "bisiklet imkanı yok" diye genelleme yapma; indoor trainer imkanını belirt.
- trainer_available false ama bike_available true ise trainer önerme.
- max_sessions 1 ise koşu, bisiklet ve mobiliteyi üç ayrı seans gibi sunma.
- max_sessions 1 ve Mobilite/Core "Opsiyonel" ya da "Önerilir" ise mobiliteyi ayrı seans yerine ana antrenmanın sonuna 5-10 dakikalık kısa ek çalışma olarak anlat.
- final_decision.strength_or_mobility "not_recommended" ise mobilite/core önermeme.
- Türkçe yaz.
- Kısa, insani ve uygulanabilir bir haftalık koç mesajı üret.
- Kararı açıklarken metrics, rules, manual_context, context_signals, final_decision ve weekly_plan bilgilerine dayan.
- weekly_plan.available true ise 'Ne yapılmalı?' bölümünde planlanan günü, ana seans süresini, toplam süreyi ve varsa add-on'u açıkça belirt.
- weekly_plan içindeki pace/distance binding false alanlarını zorunlu performans hedefi gibi sunma.
- Kaynak veride bulunmayan hedef, süre, tempo, nabız bölgesi veya antrenman detayı uydurma.

ÇIKTI FORMATI ZORUNLU:
Aşağıdaki Markdown başlıklarını aynen kullan. Başlıkları değiştirme, numaralandırmayı kaldırma, yeni başlık ekleme.

## 1. Kısa genel değerlendirme

## 2. Bu haftanın ana odağı

## 3. Ne yapılmalı?

## 4. Ne yapılmamalı?

## 5. Kısa motive edici kapanış

Her başlık altında kısa ve doğal bir açıklama yaz.
Toplam mesaj 220-340 kelime arasında olsun.
Madde işaretlerini yalnızca 3. ve 4. bölümlerde kullan.

ATHLETE:
- İsim: {label(athlete.get("name"))}
- Ana hedef: {label(athlete.get("primary_goal"))}
- Haftalık hedef: {format_json_block(athlete.get("weekly_target", {}))}
- Kısıtlar: {format_json_block({"constraints": athlete.get("constraints", [])})}
- Geçmiş hassasiyet/risk bilgileri: {format_json_block({"injury_risks": athlete.get("injury_risks", [])})}

METRICS:
- Son 7 gün toplam süre: {label(metrics.get("total_hours_7_days"))} saat
- Son 30 gün toplam süre: {label(metrics.get("total_hours_30_days"))} saat
- Son 7 gün mesafe: {label(metrics.get("weekly_distance_km"))} km
- Son 30 gün mesafe: {label(metrics.get("monthly_distance_km"))} km
- Koşu seansı: {label(metrics.get("running_sessions"))}
- Bisiklet/trainer seansı: {label(metrics.get("cycling_sessions"))}
- Load ratio: {label(metrics.get("load_ratio"))}
- 30 günlük haftalık ortalama: {label(metrics.get("rolling_30_weekly_hours"))} saat
- Önceki 23 güne göre haftalık tempo: {label(metrics.get("previous_23_weekly_hours"))} saat
- 7 günlük ortalama nabız: {label(metrics.get("avg_hr_7_days"))}

RULES:
- Progression durumu: {label(rules.get("progression_label"))}
- Progression açıklaması: {label(rules.get("progression_advice"))}
- Running decision: {label(rules.get("running_decision"))}
- Running target status: {label(rules.get("running_target_status"))}
- Cycling priority: {label(rules.get("cycling_priority"))}
- Intervals allowed: {label_bool(rules.get("intervals_allowed"))}
- Training load risk: {label(rules.get("training_load_risk_level", rules.get("risk_level")))}
- Context risk: {label(rules.get("context_risk_level"))}
- Combined risk: {label(rules.get("risk_level"))}

WEEKLY CHECK-IN / STRUCTURED CONTEXT:
- Haftanın niyeti: {label(manual_context.get("weekly_intent"))}
- Gerçekçi seans sayısı: {label(availability.get("max_sessions"))}
- Seans başına üst süre: {label(availability.get("max_session_duration_min"))} dakika
- Uygun günler: {label_list(availability.get("available_days"))}
- Enerji: {label(recovery.get("energy_level"))}
- Uyku / toparlanma: {label(recovery.get("sleep_quality"))}
- Mental yorgunluk: {label(recovery.get("mental_fatigue"))}
- Kas yorgunluğu: {label(recovery.get("muscle_soreness"))}
- Hastalık durumu: {label(recovery.get("illness_status", "none"))}
- Aktif ağrı: {label_bool(pain.get("active_pain"))}
- Ağrı bölgesi: {label(pain.get("pain_area"))}
- Ağrı şiddeti: {label(pain.get("pain_severity"))}/10
- Koşu sırasında artıyor: {label_bool(pain.get("pain_during_running"))}
- Ağrı notu: {label(pain.get("pain_note"))}
- İş yükü: {label(life_load.get("work_stress"))}
- Aile yükü: {label(life_load.get("family_load"))}
- Bakım sorumluluğu: {label(life_load.get("caregiving_load"))}
- Seyahat: {label_bool(life_load.get("travel"))}
- Rutin bozulması: {label(life_load.get("routine_disruption"))}
- Zaman baskısı: {label(life_load.get("time_pressure"))}
- Duygusal yük: {label(life_load.get("emotional_load"))}
- Kullanıcı notu: {label(manual_context.get("user_note"))}

CONTEXT SIGNALS:
- Context adjustment: {label(context_signals.get("adjustment_level"))}
- Health constraint: {label(context_signals.get("health_constraint"))}
- Recovery constraint: {label(context_signals.get("recovery_constraint"))}
- Life constraint: {label(context_signals.get("life_constraint"))}
- Availability constraint: {label(context_signals.get("availability_constraint"))}
- Context risk: {label(context_signals.get("context_risk_level"))}
- Intervals blocked by context: {label_bool(context_signals.get("intervals_blocked"))}
- Available modalities: {modality_label_list(context_signals.get("available_modalities"))}
- Context reasons: {format_json_block({"reasons": context_reasons})}

PLANNING LIMITS — KESİN SINIRLAR:
- Max sessions: {label(planning_limits.get("max_sessions"))}
- Max session duration: {label(planning_limits.get("max_session_duration_min"))} dakika
- Available days: {label_list(planning_limits.get("available_days"))}
- Available modalities: {modality_label_list(planning_limits.get("available_modalities"))}

EKİPMAN / BİSİKLET-TRAINER BAĞLAMI:
- cycling_mode: {cycling_mode_label(cycling_mode)}
- cycling_session_text: {label(cycling_session_text)}
- outdoor_bike_available: {label_bool(bike_available)}
- indoor_trainer_available: {label_bool(trainer_available)}
- running_available: {label_bool(running_available)}
- strength_available: {label_bool(strength_available)}

FINAL DECISION — DEĞİŞTİRME:
- Haftalık yük: {label(final_decision.get("weekly_load"))}
- Koşu: {label(final_decision.get("running"))}
- Bisiklet/Trainer: {label(final_decision.get("cycling"))}
- Cycling mode: {cycling_mode_label(cycling_mode)}
- Cycling session text: {label(cycling_session_text)}
- Mobilite/Core: {label(final_decision.get("strength_or_mobility"))}
- Öncelik: {label(final_decision.get("priority"))}
- Weekly intent: {label(final_decision.get("weekly_intent"))}
- Context adjustment: {label(final_decision.get("context_adjustment"))}
- Health constraint: {label(final_decision.get("health_constraint"))}
- Recovery constraint: {label(final_decision.get("recovery_constraint"))}
- Life constraint: {label(final_decision.get("life_constraint"))}
- Context override applied: {label_bool(final_decision.get("context_override_applied"))}
- Karar gerekçesi: {label(final_decision.get("reason"))}


WEEKLY PLAN — DEĞİŞTİRME:
{format_json_block(weekly_plan_payload)}

PERFORMANCE SIGNALS:
- Garmin Race Predictor tarihi: {label(race_predictor.get("calendar_date"))}
- 5K: {label(race_predictor.get("5k"))}
- 10K: {label(race_predictor.get("10k"))}
- Yarı maraton: {label(race_predictor.get("half_marathon"))}
- Maraton: {label(race_predictor.get("marathon"))}

METADATA:
- Engine version: {label(metadata.get("engine_version"))}
- Decision engine: {label(metadata.get("decision_engine"))}
- Generated at: {label(metadata.get("generated_at"))}
""".strip()

    return prompt
