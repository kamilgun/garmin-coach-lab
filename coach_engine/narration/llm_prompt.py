from typing import Any, Dict
import json


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
    "low_risk": "Düşük",
    "high_risk": "Yüksek",

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


def format_json_block(data: Dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def build_llm_coach_prompt(context: Dict[str, Any]) -> str:
    athlete = context.get("athlete", {})
    metrics = context.get("metrics", {})
    performance = context.get("performance", {})
    rules = context.get("rules", {})
    manual_context = context.get("manual_context", {})
    final_decision = context.get("final_decision", {})
    metadata = context.get("metadata", {})

    race_predictor = performance.get("race_predictor") or {}

    prompt = f"""
Sen destekleyici, gerçekçi ve temkinli bir dayanıklılık sporu koçusun.

Aşağıdaki veriler bir karar motoru tarafından hazırlanmış Coach Context çıktısıdır.
Senin görevin karar vermek değil, verilmiş kararı kullanıcıya doğal ve motive edici bir dille anlatmaktır.

KRİTİK TALİMATLAR:
- final_decision içindeki kararları değiştirme.
- Yeni yoğun antrenman, interval, tempo koşusu veya uzun koşu ekleme.
- Eğer context_override_applied true ise, yaşam bağlamının planı neden yumuşattığını açıkla.
- Kullanıcıyı suçlayıcı, baskılayıcı veya aşırı motive edici bir dil kullanma.
- Tıbbi teşhis koyma. Ağrı/sakatlık varsa profesyonel destek almasını önerebilirsin.
- Garmin Race Predictor verisini doğrudan yarış hedefi gibi sunma; yalnızca potansiyel/kondisyon sinyali olarak yorumla.
- athlete.injury_risks alanındaki bilgileri aktif sakatlık gibi sunma; bunlar yalnızca geçmiş/hassasiyet riskleridir.
- Sadece manual_context.injury_notes doluysa aktif ağrı/sakatlık notundan bahset.
- Türkçe yaz.
- Kısa, insani ve uygulanabilir bir haftalık koç mesajı üret.
- Kararı açıklarken metrics, rules, manual_context ve final_decision bilgilerine dayan.
- Eğer final_decision.cycling "Bu hafta uygun değil" ise bisiklet antrenmanı önermeye çalışma.
- Eğer manual_context içinde bisiklet/trainer imkanı yoksa bunu kısa ve doğal şekilde açıklayabilirsin.

ÇIKTI FORMATI ZORUNLU:
Aşağıdaki Markdown başlıklarını aynen kullan. Başlıkları değiştirme, numaralandırmayı kaldırma, yeni başlık ekleme.

## 1. Kısa genel değerlendirme

## 2. Bu haftanın ana odağı

## 3. Ne yapılmalı?

## 4. Ne yapılmamalı?

## 5. Kısa motive edici kapanış

Her başlık altında kısa ve doğal bir açıklama yaz.
Toplam mesaj 250-400 kelime arasında olsun.
Madde işaretlerini yalnızca 3. ve 4. bölümlerde kullan.

ATHLETE:
- İsim: {label(athlete.get("name"))}
- Ana hedef: {label(athlete.get("primary_goal"))}
- Haftalık hedef: {format_json_block(athlete.get("weekly_target", {}))}
- Kısıtlar: {format_json_block({"constraints": athlete.get("constraints", [])})}
- Sakatlık riskleri: {format_json_block({"injury_risks": athlete.get("injury_risks", [])})}

METRICS:
- Son 7 gün toplam süre: {label(metrics.get("total_hours_7_days"))} saat
- Son 30 gün toplam süre: {label(metrics.get("total_hours_30_days"))} saat
- Son 7 gün mesafe: {label(metrics.get("weekly_distance_km"))} km
- Son 30 gün mesafe: {label(metrics.get("monthly_distance_km"))} km
- Koşu seansı: {label(metrics.get("running_sessions"))}
- Bisiklet seansı: {label(metrics.get("cycling_sessions"))}
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
- Risk level: {label(rules.get("risk_level"))}

MANUAL CONTEXT:
- Aile durumu: {label(manual_context.get("family_status"))}
- Uyku bölündü mü?: {label_bool(manual_context.get("sleep_disrupted"))}
- İş yoğunluğu: {label(manual_context.get("workload"))}
- Seyahat: {label_bool(manual_context.get("travel"))}
- Enerji seviyesi: {label(manual_context.get("energy_level"))}
- Ağrı/sakatlık notu: {label(manual_context.get("injury_notes"))}
- Uygun günler: {label_list(manual_context.get("available_days"))}
- Kullanıcı notu: {label(manual_context.get("user_note"))}
- Antrenman ortamı: {label(manual_context.get("training_environment"))}
- Bisiklet imkanı: {label_bool(manual_context.get("bike_available"))}
- Trainer imkanı: {label_bool(manual_context.get("trainer_available"))}
- Koşu imkanı: {label_bool(manual_context.get("running_available"))}

FINAL DECISION:
- Haftalık yük: {label(final_decision.get("weekly_load"))}
- Koşu: {label(final_decision.get("running"))}
- Bisiklet: {label(final_decision.get("cycling"))}
- Mobilite/Core: {label(final_decision.get("strength_or_mobility"))}
- Öncelik: {label(final_decision.get("priority"))}
- Context override applied: {label_bool(final_decision.get("context_override_applied"))}
- Karar gerekçesi: {label(final_decision.get("reason"))}

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