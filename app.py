import html
import json
import shutil
import subprocess
import sys
from pathlib import Path
from datetime import datetime

import streamlit as st

from coach_engine.presentation import (
    build_weekly_plan_view_model,
)


DATA_DIR = Path("data")
SAMPLES_DIR = DATA_DIR / "samples"

MANUAL_CONTEXT_PATH = DATA_DIR / "manual_context.json"
ACTIVITY_SUMMARY_PATH = DATA_DIR / "activity_summary.json"
PERFORMANCE_SUMMARY_PATH = DATA_DIR / "performance_summary.json"
COACH_CONTEXT_PATH = DATA_DIR / "coach_context.json"
WEEKLY_PLAN_PATH = DATA_DIR / "weekly_plan.json"
SESSION_CANDIDATES_PATH = DATA_DIR / "session_candidates.json"
SESSION_SELECTION_PATH = DATA_DIR / "session_selection.json"
WEEKLY_REVIEW_PATH = DATA_DIR / "weekly_review.md"
COACH_MESSAGE_PATH = DATA_DIR / "coach_message.md"
FEEDBACK_LOG_PATH = DATA_DIR / "feedback_log.jsonl"

SAMPLE_ACTIVITY_SUMMARY_PATH = SAMPLES_DIR / "activity_summary.sample.json"
SAMPLE_PERFORMANCE_SUMMARY_PATH = SAMPLES_DIR / "performance_summary.sample.json"


WEEKLY_INTENT_OPTIONS = {
    "Toparlanmak": "recover",
    "Ritmi korumak": "maintain_consistency",
    "Kontrollü gelişmek": "build_carefully",
    "Aradan sonra geri dönmek": "return_after_break",
    "Yarışa hazırlanmak": "race_specific",
}

MAX_SESSIONS_OPTIONS = {
    "1 seans": 1,
    "2 seans": 2,
    "3 seans": 3,
    "4 seans": 4,
    "5+ seans": 5,
}

MAX_DURATION_OPTIONS = {
    "30 dk": 30,
    "45 dk": 45,
    "60 dk": 60,
    "75 dk": 75,
    "90+ dk": 90,
}

ENERGY_LEVEL_OPTIONS = {
    "Çok düşük": "very_low",
    "Düşük": "low",
    "Normal": "normal",
    "İyi": "high",
}

SLEEP_QUALITY_OPTIONS = {
    "Kötü": "poor",
    "Orta": "okay",
    "İyi": "good",
}

MENTAL_FATIGUE_OPTIONS = {
    "Düşük": "low",
    "Orta": "medium",
    "Yüksek": "high",
}

MUSCLE_SORENESS_OPTIONS = {
    "Yok": "none",
    "Hafif": "low",
    "Orta": "medium",
    "Belirgin": "high",
}

HEALTH_STATUS_OPTIONS = {
    "Yok": "none",
    "Ağrı veya fiziksel rahatsızlık var": "pain",
    "Hastalıktan yeni dönüyorum": "recovering",
    "Şu an hastayım": "active",
}

PAIN_SEVERITY_OPTIONS = {
    "Hafif": 2,
    "Orta": 5,
    "Belirgin": 8,
}

PAIN_AREA_OPTIONS = {
    "Ayak / ayak bileği": "foot",
    "Baldır": "calf",
    "Diz": "knee",
    "Kalça": "hip",
    "Bel": "lower_back",
    "Omuz": "shoulder",
    "Diğer": "other",
}

LIFE_EVENT_OPTIONS = [
    "İş yoğunluğu",
    "Aile / çocuk yoğunluğu",
    "Bakım sorumluluğu",
    "Seyahat",
    "Rutin dışı bir hafta",
    "Çok az zaman",
    "Duygusal olarak zor bir hafta",
    "Çok yoğun / kapasitem çok sınırlı",
]

AVAILABLE_DAY_OPTIONS = {
    "Pazartesi": "monday",
    "Salı": "tuesday",
    "Çarşamba": "wednesday",
    "Perşembe": "thursday",
    "Cuma": "friday",
    "Cumartesi": "saturday",
    "Pazar": "sunday",
}


LABELS = {
    # final decision
    "maintain": "Mevcut yükü koru",
    "reduce_or_maintain": "Azalt veya koru",
    "increase_carefully": "Dikkatli artır",
    "maintain_easy": "Kolay koşularla ritmi koru",
    "easy_only": "Sadece kolay koşu",
    "not_available": "Bu hafta uygun değil",
    "add_easy_z2": "Kolay Z2 bisiklet ekle",
    "optional_recovery": "Opsiyonel toparlanma",
    "recommended": "Önerilir",
    "bike": "Bisiklet öncelikli",
    "recommended_light": "Hafif mobilite/core önerilir",
    "not_recommended": "Önerilmez",
    "optional": "Opsiyonel",
    "running_consistency": "Koşu ritmini koruma",
    "recovery": "Toparlanma",
    "reduce": "Azalt",
    "recovery_only": "Sadece toparlanma",
    "controlled_build": "Kontrollü artır",
    "controlled_increase": "Kontrollü artır",
    "add_or_maintain_z2": "Kolay Z2 bisiklet/trainer ekle veya koru",
    "balanced": "Dengeli ilerleme",
    "restart_easy": "Kolay yeniden başlangıç",
    "optional_easy_z2": "Opsiyonel kolay Z2",
    "consistency": "Ritmi yeniden kurma",
    # rules
    "low": "Düşük",
    "medium": "Orta",
    "high": "Yüksek",
    "very_high": "Çok yüksek",
    "very_low": "Çok düşük",
    "caution_growth": "Dikkatli artış",
    "stable": "Stabil",
    "productive_build": "Üretken artış",
    "restart": "Yeniden başlangıç",
    "below_baseline": "Baz çizginin altında",
    "spike_risk": "Ani yük artışı riski",
    "sharp_rebuild_low_absolute_load": "Hızlı dönüş / düşük mutlak yük",
    # weekly check-in
    "recover": "Toparlanmak",
    "maintain_consistency": "Ritmi korumak",
    "build_carefully": "Kontrollü gelişmek",
    "return_after_break": "Aradan sonra geri dönmek",
    "race_specific": "Yarışa hazırlanmak",
    "poor": "Kötü",
    "okay": "Orta",
    "good": "İyi",
    "none": "Yok",
    "active": "Şu an hastayım",
    "recovering": "Hastalıktan yeni dönüyorum",
    "foot": "Ayak / ayak bileği",
    "calf": "Baldır",
    "knee": "Diz",
    "hip": "Kalça",
    "lower_back": "Bel",
    "shoulder": "Omuz",
    "other": "Diğer",
    # legacy context
    "normal": "Normal",
    "family_busy": "Aile yoğun",
    "child_sick": "Çocuk hasta",
    "home": "Ev rutini",
    "vacation": "Tatil",
    "travel": "Seyahat",
}



def label(value):
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "Evet" if value else "Hayır"
    return LABELS.get(value, str(value))

def get_cycling_mode_from_context(manual_context):
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
        return "bike_or_trainer"

    if trainer_available:
        return "trainer"

    if bike_available:
        return "bike"

    return "none"


def cycling_action_label(value, manual_context):
    mode = get_cycling_mode_from_context(manual_context)

    if value == "add_easy_z2":
        if mode == "trainer":
            return "Kolay Z2 trainer seansı ekle"
        if mode == "bike":
            return "Kolay Z2 bisiklet ekle"
        if mode == "bike_or_trainer":
            return "Kolay Z2 bisiklet/trainer ekle"
        return "Bu hafta uygun değil"

    if value == "add_or_maintain_z2":
        if mode == "trainer":
            return "Kolay Z2 trainer seansını ekle veya koru"
        if mode == "bike":
            return "Kolay Z2 bisiklet seansını ekle veya koru"
        if mode == "bike_or_trainer":
            return "Kolay Z2 bisiklet/trainer seansını ekle veya koru"
        return "Bu hafta uygun değil"

    if value == "optional_easy_z2":
        if mode == "trainer":
            return "Opsiyonel kolay Z2 trainer"
        if mode == "bike":
            return "Opsiyonel kolay Z2 bisiklet"
        if mode == "bike_or_trainer":
            return "Opsiyonel kolay Z2 bisiklet/trainer"
        return "Bu hafta uygun değil"

    return label(value)


def priority_action_label(value, manual_context):
    mode = get_cycling_mode_from_context(manual_context)

    if value == "bike":
        if mode == "trainer":
            return "Indoor trainer öncelikli"
        if mode == "bike":
            return "Bisiklet öncelikli"
        if mode == "bike_or_trainer":
            return "Bisiklet/trainer öncelikli"

    return label(value)


def ensure_data_dir():
    DATA_DIR.mkdir(exist_ok=True)


def load_json(path: Path, default=None):
    if not path.exists():
        return default

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def append_feedback(feedback):
    FEEDBACK_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    with FEEDBACK_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(feedback, ensure_ascii=False) + "\n")

def read_text(path: Path, default=""):
    if not path.exists():
        return default

    return path.read_text(encoding="utf-8")


def copy_sample_data():
    missing_samples = []

    if not SAMPLE_ACTIVITY_SUMMARY_PATH.exists():
        missing_samples.append(str(SAMPLE_ACTIVITY_SUMMARY_PATH))

    if not SAMPLE_PERFORMANCE_SUMMARY_PATH.exists():
        missing_samples.append(str(SAMPLE_PERFORMANCE_SUMMARY_PATH))

    if missing_samples:
        raise FileNotFoundError(
            "Sample data bulunamadı:\n" + "\n".join(missing_samples)
        )

    ensure_data_dir()

    shutil.copy2(SAMPLE_ACTIVITY_SUMMARY_PATH, ACTIVITY_SUMMARY_PATH)
    shutil.copy2(SAMPLE_PERFORMANCE_SUMMARY_PATH, PERFORMANCE_SUMMARY_PATH)


def run_local_pipeline(use_llm: bool = False):
    command = [
        sys.executable,
        "run_pipeline.py",
        "--skip-garmin",
    ]

    if not use_llm:
        command.append("--skip-llm")

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    return result


def find_label_by_value(options, value, fallback_label):
    for option_label, option_value in options.items():
        if option_value == value:
            return option_label

    return fallback_label


def get_context_value(context, section, key, legacy_key=None, default=None):
    section_data = context.get(section, {})

    if key in section_data:
        return section_data[key]

    if legacy_key and legacy_key in context:
        return context[legacy_key]

    return default


def get_default_manual_context():
    return {
        "schema_version": "2.0",
        "context_period": "current_week",
        "availability": {
            "available_days": [],
            "max_sessions": 3,
            "max_session_duration_min": 50,
            "running_available": True,
            "outdoor_bike_available": True,
            "indoor_trainer_available": True,
            "strength_available": True,
        },
        "recovery": {
            "sleep_quality": "okay",
            "energy_level": "normal",
            "mental_fatigue": "medium",
            "muscle_soreness": "low",
            "illness_status": "none",
        },
        "pain": {
            "active_pain": False,
            "pain_area": None,
            "pain_severity": 0,
            "pain_during_running": False,
            "pain_note": "",
        },
        "life_load": {
            "work_stress": "normal",
            "family_load": "normal",
            "caregiving_load": "low",
            "travel": False,
            "routine_disruption": "low",
            "time_pressure": "normal",
            "emotional_load": "normal",
        },
        "weekly_intent": "maintain_consistency",
        "user_note": "",
    }


def infer_health_status(existing_context):
    pain = existing_context.get("pain", {})
    recovery = existing_context.get("recovery", {})

    illness_status = recovery.get("illness_status", "none")
    if illness_status in ["active", "recovering"]:
        return illness_status

    if pain.get("active_pain") or existing_context.get("injury_notes"):
        return "pain"

    return "none"


def infer_life_events(existing_context):
    life_load = existing_context.get("life_load", {})
    events = []

    work_stress = life_load.get(
        "work_stress",
        existing_context.get("workload", "normal"),
    )
    family_status = existing_context.get("family_status", "normal")

    if work_stress == "very_high":
        events.append("Çok yoğun / kapasitem çok sınırlı")
    elif work_stress == "high":
        events.append("İş yoğunluğu")

    if life_load.get("family_load") == "high" or family_status in [
        "family_busy",
        "child_sick",
    ]:
        events.append("Aile / çocuk yoğunluğu")

    if life_load.get("caregiving_load") in ["medium", "high"]:
        events.append("Bakım sorumluluğu")

    if life_load.get("travel", existing_context.get("travel", False)):
        events.append("Seyahat")

    if life_load.get("routine_disruption") == "high":
        events.append("Rutin dışı bir hafta")

    if life_load.get("time_pressure") == "high":
        events.append("Çok az zaman")

    if life_load.get("emotional_load") == "high":
        events.append("Duygusal olarak zor bir hafta")

    return list(dict.fromkeys(events))


def get_file_status():
    return {
        "Activity": ACTIVITY_SUMMARY_PATH.exists(),
        "Performance": PERFORMANCE_SUMMARY_PATH.exists(),
        "Context": MANUAL_CONTEXT_PATH.exists(),
        "Coach Context": COACH_CONTEXT_PATH.exists(),
        "Weekly Plan": WEEKLY_PLAN_PATH.exists(),
        "Weekly Review": WEEKLY_REVIEW_PATH.exists(),
    }


def render_status_pills():
    statuses = get_file_status()

    cols = st.columns(len(statuses))

    for col, (name, exists) in zip(cols, statuses.items()):
        with col:
            if exists:
                st.success(f"{name} hazır")
            else:
                st.warning(f"{name} yok")


def render_sidebar_context_form(existing_context):
    st.sidebar.header("Haftalık Check-in")
    st.sidebar.caption(
        "Koçuna bu haftanın gerçek hayat koşullarını anlat. "
        "Yaklaşık 30 saniye sürer."
    )

    availability = existing_context.get("availability", {})
    recovery = existing_context.get("recovery", {})
    pain = existing_context.get("pain", {})

    weekly_intent_value = existing_context.get(
        "weekly_intent",
        "maintain_consistency",
    )
    weekly_intent_label = find_label_by_value(
        WEEKLY_INTENT_OPTIONS,
        weekly_intent_value,
        "Ritmi korumak",
    )

    max_sessions_value = int(availability.get("max_sessions", 3))
    if max_sessions_value >= 5:
        max_sessions_value = 5
    max_sessions_label = find_label_by_value(
        MAX_SESSIONS_OPTIONS,
        max_sessions_value,
        "3 seans",
    )

    max_duration_value = int(
        availability.get("max_session_duration_min", 50)
    )
    duration_candidates = list(MAX_DURATION_OPTIONS.values())
    nearest_duration = min(
        duration_candidates,
        key=lambda option: abs(option - max_duration_value),
    )
    max_duration_label = find_label_by_value(
        MAX_DURATION_OPTIONS,
        nearest_duration,
        "45 dk",
    )

    energy_value = get_context_value(
        existing_context,
        "recovery",
        "energy_level",
        legacy_key="energy_level",
        default="normal",
    )
    energy_label = find_label_by_value(
        ENERGY_LEVEL_OPTIONS,
        energy_value,
        "Normal",
    )

    sleep_quality_value = recovery.get("sleep_quality")
    if sleep_quality_value is None:
        sleep_quality_value = (
            "poor"
            if existing_context.get("sleep_disrupted", False)
            else "okay"
        )
    sleep_quality_label = find_label_by_value(
        SLEEP_QUALITY_OPTIONS,
        sleep_quality_value,
        "Orta",
    )

    weekly_intent = st.sidebar.selectbox(
        "Bu hafta önceliğin ne?",
        list(WEEKLY_INTENT_OPTIONS.keys()),
        index=list(WEEKLY_INTENT_OPTIONS.keys()).index(weekly_intent_label),
    )

    if WEEKLY_INTENT_OPTIONS[weekly_intent] == "race_specific":
        st.sidebar.caption(
            "Yarış niyeti mevcut güvenli adaylar arasında öncelik "
            "sinyalidir. Bu sürüm henüz interval, tempo veya uzun koşu "
            "üretmez."
        )

    max_sessions = st.sidebar.selectbox(
        "Bu hafta en fazla kaç antrenman mümkün?",
        list(MAX_SESSIONS_OPTIONS.keys()),
        index=list(MAX_SESSIONS_OPTIONS.keys()).index(max_sessions_label),
    )
    st.sidebar.caption(
        "Bu sayı plan hedefi değil, planner'ın aşamayacağı kapasite sınırıdır."
    )

    max_duration = st.sidebar.selectbox(
        "Bir antrenmana en fazla ne kadar süre ayırabilirsin?",
        list(MAX_DURATION_OPTIONS.keys()),
        index=list(MAX_DURATION_OPTIONS.keys()).index(max_duration_label),
    )
    st.sidebar.caption(
        "Bu süre önerilen hedef değil, tek seans için üst sınırdır."
    )

    energy_level = st.sidebar.selectbox(
        "Enerjin nasıl?",
        list(ENERGY_LEVEL_OPTIONS.keys()),
        index=list(ENERGY_LEVEL_OPTIONS.keys()).index(energy_label),
    )

    sleep_quality = st.sidebar.selectbox(
        "Uyku ve genel toparlanman nasıl?",
        list(SLEEP_QUALITY_OPTIONS.keys()),
        index=list(SLEEP_QUALITY_OPTIONS.keys()).index(sleep_quality_label),
    )

    st.sidebar.divider()
    st.sidebar.subheader("Bu haftanın gerçek hayatı")

    existing_life_events = infer_life_events(existing_context)
    no_special_condition = st.sidebar.checkbox(
        "Planı etkileyen özel bir durum yok",
        value=not existing_life_events,
        key="checkin_no_special_condition",
    )

    if no_special_condition:
        life_events = []
        st.sidebar.caption("Ek yaşam yükü seçilmedi.")
    else:
        life_events = st.sidebar.multiselect(
            "Planını etkileyebilecek durumlar",
            LIFE_EVENT_OPTIONS,
            default=existing_life_events,
            placeholder="Bir veya daha fazla durum seç",
        )

    st.sidebar.subheader("Antrenman imkânları")

    running_available = st.sidebar.checkbox(
        "Koşu mümkün",
        value=bool(
            get_context_value(
                existing_context,
                "availability",
                "running_available",
                legacy_key="running_available",
                default=True,
            )
        ),
    )
    outdoor_bike_available = st.sidebar.checkbox(
        "Outdoor bisiklet mümkün",
        value=bool(
            get_context_value(
                existing_context,
                "availability",
                "outdoor_bike_available",
                legacy_key="bike_available",
                default=True,
            )
        ),
    )
    indoor_trainer_available = st.sidebar.checkbox(
        "Indoor trainer mümkün",
        value=bool(
            get_context_value(
                existing_context,
                "availability",
                "indoor_trainer_available",
                legacy_key="trainer_available",
                default=True,
            )
        ),
    )
    strength_available = st.sidebar.checkbox(
        "Mobilite / core mümkün",
        value=bool(availability.get("strength_available", True)),
    )

    st.sidebar.subheader("Sağlık sinyali")

    existing_health_status = infer_health_status(existing_context)
    health_status_label = find_label_by_value(
        HEALTH_STATUS_OPTIONS,
        existing_health_status,
        "Yok",
    )
    health_status = st.sidebar.selectbox(
        "Sağlık açısından planı etkileyen bir durum var mı?",
        list(HEALTH_STATUS_OPTIONS.keys()),
        index=list(HEALTH_STATUS_OPTIONS.keys()).index(health_status_label),
    )
    health_status_value = HEALTH_STATUS_OPTIONS[health_status]

    pain_severity = 0
    pain_area = None
    pain_during_running = False
    pain_note = ""

    if health_status_value == "pain":
        existing_pain_severity = int(pain.get("pain_severity", 2) or 2)
        nearest_pain_severity = min(
            PAIN_SEVERITY_OPTIONS.values(),
            key=lambda option: abs(option - existing_pain_severity),
        )
        pain_severity_label = find_label_by_value(
            PAIN_SEVERITY_OPTIONS,
            nearest_pain_severity,
            "Hafif",
        )

        pain_severity_label_selected = st.sidebar.selectbox(
            "Ağrı ne düzeyde?",
            list(PAIN_SEVERITY_OPTIONS.keys()),
            index=list(PAIN_SEVERITY_OPTIONS.keys()).index(
                pain_severity_label
            ),
        )
        pain_severity = PAIN_SEVERITY_OPTIONS[
            pain_severity_label_selected
        ]

        existing_pain_area = pain.get("pain_area")
        pain_area_label = find_label_by_value(
            PAIN_AREA_OPTIONS,
            existing_pain_area,
            "Diğer",
        )
        pain_area_label_selected = st.sidebar.selectbox(
            "Nerede?",
            list(PAIN_AREA_OPTIONS.keys()),
            index=list(PAIN_AREA_OPTIONS.keys()).index(pain_area_label),
        )
        pain_area = PAIN_AREA_OPTIONS[pain_area_label_selected]

        pain_during_running = st.sidebar.checkbox(
            "Koşarken artıyor",
            value=bool(pain.get("pain_during_running", False)),
        )
        pain_note = st.sidebar.text_input(
            "Kısa ağrı notu",
            value=(
                pain.get("pain_note")
                or existing_context.get("injury_notes")
                or ""
            ),
            placeholder="İsteğe bağlı",
        )

    existing_available_days = get_context_value(
        existing_context,
        "availability",
        "available_days",
        legacy_key="available_days",
        default=[],
    ) or []
    existing_available_day_labels = [
        option_label
        for option_label, option_value in AVAILABLE_DAY_OPTIONS.items()
        if option_value in existing_available_days
    ]

    existing_mental_fatigue = recovery.get("mental_fatigue", "medium")
    mental_fatigue_label = find_label_by_value(
        MENTAL_FATIGUE_OPTIONS,
        existing_mental_fatigue,
        "Orta",
    )

    existing_muscle_soreness = recovery.get("muscle_soreness", "low")
    muscle_soreness_label = find_label_by_value(
        MUSCLE_SORENESS_OPTIONS,
        existing_muscle_soreness,
        "Hafif",
    )

    with st.sidebar.expander("İsteğe bağlı detaylar"):
        available_days = st.multiselect(
            "Hangi günler uygunsun?",
            list(AVAILABLE_DAY_OPTIONS.keys()),
            default=existing_available_day_labels,
        )
        mental_fatigue = st.selectbox(
            "Mental yorgunluk",
            list(MENTAL_FATIGUE_OPTIONS.keys()),
            index=list(MENTAL_FATIGUE_OPTIONS.keys()).index(
                mental_fatigue_label
            ),
        )
        muscle_soreness = st.selectbox(
            "Kas yorgunluğu",
            list(MUSCLE_SORENESS_OPTIONS.keys()),
            index=list(MUSCLE_SORENESS_OPTIONS.keys()).index(
                muscle_soreness_label
            ),
        )
        user_note = st.text_area(
            "Ek not",
            value=existing_context.get("user_note") or "",
            placeholder="Örn: Perşembe akşamı kesin boşum.",
            height=90,
        )

    very_busy = "Çok yoğun / kapasitem çok sınırlı" in life_events

    life_load = {
        "work_stress": (
            "very_high"
            if very_busy
            else "high"
            if "İş yoğunluğu" in life_events
            else "normal"
        ),
        "family_load": (
            "high"
            if "Aile / çocuk yoğunluğu" in life_events
            else "normal"
        ),
        "caregiving_load": (
            "high"
            if "Bakım sorumluluğu" in life_events
            else "low"
        ),
        "travel": "Seyahat" in life_events,
        "routine_disruption": (
            "high"
            if (
                "Rutin dışı bir hafta" in life_events
                or very_busy
            )
            else "medium"
            if "Seyahat" in life_events
            else "low"
        ),
        "time_pressure": (
            "high"
            if "Çok az zaman" in life_events or very_busy
            else "normal"
        ),
        "emotional_load": (
            "high"
            if "Duygusal olarak zor bir hafta" in life_events
            else "normal"
        ),
    }

    illness_status = (
        health_status_value
        if health_status_value in ["active", "recovering"]
        else "none"
    )

    manual_context = {
        "schema_version": "2.0",
        "context_period": "current_week",
        "availability": {
            "available_days": [
                AVAILABLE_DAY_OPTIONS[option_label]
                for option_label in available_days
            ],
            "max_sessions": MAX_SESSIONS_OPTIONS[max_sessions],
            "max_session_duration_min": MAX_DURATION_OPTIONS[max_duration],
            "running_available": running_available,
            "outdoor_bike_available": outdoor_bike_available,
            "indoor_trainer_available": indoor_trainer_available,
            "strength_available": strength_available,
        },
        "recovery": {
            "sleep_quality": SLEEP_QUALITY_OPTIONS[sleep_quality],
            "energy_level": ENERGY_LEVEL_OPTIONS[energy_level],
            "mental_fatigue": MENTAL_FATIGUE_OPTIONS[mental_fatigue],
            "muscle_soreness": MUSCLE_SORENESS_OPTIONS[muscle_soreness],
            "illness_status": illness_status,
        },
        "pain": {
            "active_pain": health_status_value == "pain",
            "pain_area": pain_area,
            "pain_severity": pain_severity,
            "pain_during_running": pain_during_running,
            "pain_note": pain_note.strip(),
        },
        "life_load": life_load,
        "weekly_intent": WEEKLY_INTENT_OPTIONS[weekly_intent],
        "user_note": user_note.strip(),
    }

    if st.sidebar.button(
        "Check-in'i kaydet",
        use_container_width=True,
        type="primary",
    ):
        write_json(MANUAL_CONTEXT_PATH, manual_context)
        st.sidebar.success(
            "Check-in kaydedildi. Yeni karar için pipeline'ı çalıştır."
        )

    return manual_context


def render_sidebar_actions(current_manual_context):
    st.sidebar.header("Çalıştır")

    if st.sidebar.button("Sample data kullan", use_container_width=True):
        try:
            copy_sample_data()
            st.sidebar.success("Sample data kopyalandı.")
            st.rerun()
        except Exception as exc:
            st.sidebar.error(str(exc))

    use_llm = st.sidebar.toggle(
        "LLM coach message üret",
        value=False,
        help="Kapalıyken OpenAI API çağrısı yapılmaz.",
    )

    if st.sidebar.button(
        "Check-in'i kaydet ve planı oluştur",
        use_container_width=True,
    ):
        write_json(
            MANUAL_CONTEXT_PATH,
            current_manual_context,
        )
        result = run_local_pipeline(use_llm=use_llm)

        st.session_state["last_pipeline_stdout"] = result.stdout
        st.session_state["last_pipeline_stderr"] = result.stderr
        st.session_state["last_pipeline_returncode"] = result.returncode

        if result.returncode == 0:
            st.sidebar.success(
                "Check-in kaydedildi ve plan güncellendi."
            )
            st.rerun()
        else:
            st.sidebar.error("Pipeline hata aldı.")


def render_hero(coach_context):
    st.title("Garmin Coach Lab")
    st.caption(
        "Local-first, context-aware endurance coaching prototype. "
        "Bu arayüz Garmin şifresi toplamaz."
    )

    if not coach_context:
        st.info(
            "Başlamak için soldan check-in kaydet, sample data seç "
            "veya mevcut local data ile pipeline çalıştır."
        )


def build_action_items(coach_context):
    if not coach_context:
        return []

    final_decision = coach_context.get("final_decision", {})
    rules = coach_context.get("rules", {})

    running = final_decision.get("running")
    cycling = final_decision.get("cycling")
    weekly_load = final_decision.get("weekly_load")
    strength = final_decision.get("strength_or_mobility")

    cycling_session_text = (
        final_decision.get("cycling_session_text")
        or "kolay Z2 bisiklet/trainer seansı"
    )

    actions = []

    if running == "maintain_easy":
        actions.append(
            "Koşu ritmini koru; koşuları kolay tempoda ve kontrollü tut."
        )
    elif running == "easy_only":
        actions.append(
            "Koşu yapacaksan sadece kolay koşu yap; performans zorlaması ekleme."
        )
    elif running == "controlled_increase":
        actions.append(
            "Koşu hacmini yalnızca küçük ve kontrollü bir artışla ilerlet."
        )
    elif running == "not_available":
        actions.append(
            "Bu hafta koşu mümkün değil; koşu yerine toparlanma ve uygun alternatiflere odaklan."
        )

    if cycling in ["add_easy_z2", "add_or_maintain_z2"]:
        actions.append(
            f"{cycling_session_text.capitalize()} ekleyerek aerobik yükü koşuyu artırmadan destekle."
        )
    elif cycling in ["optional_easy_z2", "optional_recovery", "recovery_only"]:
        actions.append(
            f"Uygun hissedersen düşük yoğunluklu {cycling_session_text} yapabilirsin."
        )
    elif cycling == "not_available":
        actions.append(
            "Bu hafta bisiklet/trainer antrenmanı uygulanabilir değil; planı buna göre sade tut."
        )

    if strength in ["recommended", "recommended_light"]:
        actions.append(
            "Haftaya kısa bir mobilite/core seansı ekle."
        )

    if weekly_load in ["reduce", "reduce_or_maintain"]:
        actions.insert(
            0,
            "Bu hafta ana hedef yük artırmak değil; toparlanmayı ve sürdürülebilirliği korumak."
        )
    elif weekly_load in ["maintain", "restart_easy"]:
        actions.insert(
            0,
            "Bu hafta ana hedef düzeni korumak; ekstra yük bindirmemek."
        )

    return actions[:3]


def build_avoid_items(coach_context):
    if not coach_context:
        return []

    final_decision = coach_context.get("final_decision", {})
    rules = coach_context.get("rules", {})

    avoids = []

    if not rules.get("intervals_allowed"):
        avoids.append("Interval, tempo koşusu veya yüksek yoğunluklu antrenman ekleme.")

    if final_decision.get("weekly_load") in ["maintain", "reduce", "reduce_or_maintain", "restart_easy"]:
        avoids.append("Koşu hacmini bu hafta belirgin şekilde artırma.")

    if final_decision.get("running") in ["easy_only", "maintain_easy"]:
        avoids.append("Koşuları yarış temposuna veya zorlayıcı tempoya taşıma.")

    if final_decision.get("cycling") == "not_available":
        avoids.append("Bisiklet/trainer imkanı yoksa bunu telafi etmek için koşu yükünü artırma.")

    if not avoids:
        avoids.append("Plan dışı sert antrenman ekleme; kontrollü ilerle.")

    return avoids[:3]


def render_main_output(coach_context):
    st.subheader("Bu hafta ne yapmalıyım?")

    if not coach_context:
        st.info("Önce context kaydedip pipeline çalıştırınca burada haftalık aksiyon özeti görünecek.")
        return

    final_decision = coach_context.get("final_decision", {})
    rules = coach_context.get("rules", {})
    manual_context = coach_context.get("manual_context", {})

    action_items = build_action_items(coach_context)
    avoid_items = build_avoid_items(coach_context)

    col1, col2 = st.columns([1.2, 1])

    with col1:
        action_html = "".join(f"<li>{item}</li>" for item in action_items)
        st.markdown(
            f"""
            <div class="coach-card coach-card-action">
                <h3>Bu hafta yap</h3>
                <ul>{action_html}</ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        avoid_html = "".join(f"<li>{item}</li>" for item in avoid_items)
        st.markdown(
            f"""
            <div class="coach-card coach-card-avoid">
                <h3>Bu hafta kaçın</h3>
                <ul>{avoid_html}</ul>
            </div>
            """,
            unsafe_allow_html=True,
        )



def escape_ui_text(value):
    if value is None:
        return "-"
    return html.escape(str(value))


def render_value_card(
    title,
    value,
    *,
    helper=None,
    tone="default",
):
    helper_html = (
        f'<div class="product-value-helper">'
        f'{escape_ui_text(helper)}</div>'
        if helper
        else ""
    )

    st.markdown(
        f"""
        <div class="product-value-card product-value-card-{tone}">
            <div class="product-value-title">
                {escape_ui_text(title)}
            </div>
            <div class="product-value-content">
                {escape_ui_text(value)}
            </div>
            {helper_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_guidance_box(
    title,
    value,
    *,
    tone="neutral",
):
    st.markdown(
        f"""
        <div class="product-guidance product-guidance-{tone}">
            <div class="product-guidance-title">
                {escape_ui_text(title)}
            </div>
            <div class="product-guidance-value">
                {escape_ui_text(value)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_message(view_model):
    tone = view_model.get("status_tone")
    message = view_model.get("status_message", "")

    if tone == "success":
        st.success(message)
    elif tone == "warning":
        st.warning(message)
    elif tone == "error":
        st.error(message)
    else:
        st.info(message)


def render_plan_empty_state(view_model):
    status = view_model.get("status")

    if status == "missing":
        with st.container(border=True):
            st.markdown("#### Haftalık planını oluştur")
            st.write(
                "Soldaki Weekly Check-in'i kaydet ve ardından "
                "**Pipeline çalıştır** düğmesine bas."
            )
            st.caption(
                "Plan hazır olduğunda kesin gün, süre, efor ve "
                "alternatif tarihler burada gösterilecek."
            )
        return True

    if status == "invalid":
        with st.container(border=True):
            st.markdown("#### Weekly plan okunamadı")
            st.write(
                "Artifact temel yapısal beklentileri karşılamıyor. "
                "Teknik sekmedeki Weekly Plan JSON ve pipeline logunu kontrol et."
            )
        return True

    if status == "no_structured_training":
        with st.container(border=True):
            st.markdown("#### Bu hafta toparlanma öncelikli")
            st.write(
                "Sağlık veya toparlanma kısıtı nedeniyle yapılandırılmış "
                "antrenman planlanmadı."
            )
            st.caption(
                "Sistem bu durumda performans hedefi eklemez ve planı "
                "zorla doldurmaz."
            )
        return False

    if status == "no_sessions":
        with st.container(border=True):
            st.markdown("#### Bu pencere için seans yok")
            st.write(
                "Karar artifact'i bu rolling yedi günlük pencere için "
                "uygulanabilir bir standalone seans üretmedi."
            )
        return False

    return False


def render_weekly_plan_product(coach_context, weekly_plan):
    view_model = build_weekly_plan_view_model(
        coach_context,
        weekly_plan,
    )

    render_status_message(view_model)

    status_tone = view_model.get("status_tone", "info")

    with st.container(border=True):
        st.markdown(
            f"""
            <div class="weekly-focus-card weekly-focus-{escape_ui_text(status_tone)}">
                <div class="weekly-focus-eyebrow">BU HAFTANIN ODAĞI</div>
                <div class="weekly-focus-title">
                    {escape_ui_text(view_model["focus"])}
                </div>
                <div class="weekly-focus-status">
                    {escape_ui_text(view_model["status_label"])}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        summary_col1, summary_col2 = st.columns(2)
        summary_col3, summary_col4 = st.columns(2)

        with summary_col1:
            render_value_card(
                "Planlanan seans",
                view_model["session_count"],
                helper="Standalone seans sayısı",
                tone="accent",
            )

        with summary_col2:
            duration = view_model["total_duration_min"]
            render_value_card(
                "Toplam yaklaşık süre",
                f"{duration} dk" if duration else "-",
                helper="Add-on süreleri dahil",
                tone="accent",
            )

        with summary_col3:
            render_value_card(
                "Plan penceresi",
                view_model["horizon_label"],
                helper="Rolling yedi gün",
            )

        with summary_col4:
            render_value_card(
                "Yoğunluk",
                view_model["intensity_summary"],
                helper="Ana efor sınırı",
            )

        constraints = view_model.get("constraints") or []
        if constraints:
            st.caption(" · ".join(constraints))

        applied_context = (
            view_model.get("applied_context") or {}
        )

        capacity_notice = applied_context.get(
            "capacity_notice"
        )
        if capacity_notice:
            render_guidance_box(
                "Check-in nasıl uygulandı?",
                capacity_notice,
                tone="neutral",
            )

        intent_notice = applied_context.get(
            "intent_notice"
        )
        if intent_notice:
            render_guidance_box(
                "Yarış niyeti hakkında",
                intent_notice,
                tone="reference",
            )

    should_stop = render_plan_empty_state(view_model)
    if should_stop:
        return view_model

    sessions = view_model.get("sessions") or []

    if sessions:
        st.markdown("### Antrenmanlar")

    for index, session in enumerate(sessions, start=1):
        with st.container(border=True):
            st.markdown(
                f"#### {index}. {session['date_label']} — "
                f"{session['title']}"
            )
            st.caption(session["modality"])

            detail_col1, detail_col2, detail_col3 = st.columns(
                [0.85, 0.85, 1.3]
            )

            with detail_col1:
                render_value_card(
                    "Ana çalışma",
                    session["main_duration"]["primary"],
                    helper=(
                        "Aralık: "
                        f"{session['main_duration']['range']}"
                        if session["main_duration"]["range"]
                        else None
                    ),
                    tone="accent",
                )

            with detail_col2:
                render_value_card(
                    "Toplam seans",
                    session["total_duration"]["primary"],
                    helper=(
                        "Aralık: "
                        f"{session['total_duration']['range']}"
                        if session["total_duration"]["range"]
                        else None
                    ),
                    tone="accent",
                )

            with detail_col3:
                render_value_card(
                    "Efor",
                    session["effort_label"],
                    helper="Birincil uygulama rehberi",
                )

            guidance_items = []

            if session.get("pace"):
                guidance_items.append(
                    (
                        "Pace referansı",
                        session["pace"]["label"],
                    )
                )

            if session.get("distance"):
                guidance_items.append(
                    (
                        "Mesafe referansı",
                        session["distance"]["label"],
                    )
                )

            if guidance_items:
                guidance_columns = st.columns(len(guidance_items))

                for column, (title, value) in zip(
                    guidance_columns,
                    guidance_items,
                ):
                    with column:
                        render_guidance_box(
                            title,
                            value,
                            tone="reference",
                        )

            add_ons = session.get("add_ons") or []
            if add_ons:
                add_on_labels = [
                    add_on["label"]
                    for add_on in add_ons
                ]
                render_guidance_box(
                    "Aynı gün eklenecek çalışma",
                    " · ".join(add_on_labels),
                    tone="addon",
                )

            alternatives = session.get("alternatives") or []
            if alternatives:
                st.caption(
                    "Esnek alternatifler: "
                    + " veya ".join(alternatives)
                )

    unscheduled = (
        view_model.get("unscheduled_sessions") or []
    )
    if unscheduled:
        st.markdown("### Takvime yerleşemeyen seanslar")
        for session in unscheduled:
            st.warning(
                f"**{session['title']}** — "
                f"{session['reason']}"
            )

    reasons = view_model.get("reasons") or []
    avoid_items = view_model.get("avoid_items") or []

    if reasons or avoid_items:
        st.markdown("### Planın Açıklaması")
        explanation_col1, explanation_col2 = st.columns(
            [1.45, 0.85]
        )

        with explanation_col1:
            with st.container(border=True):
                st.markdown("#### Neden bu plan?")
                if reasons:
                    for reason in reasons:
                        st.write(f"• {reason}")
                else:
                    st.caption(
                        "Karar artifact'i ek gerekçe taşımıyor."
                    )

        with explanation_col2:
            with st.container(border=True):
                st.markdown("#### Bu hafta kaçın")
                if avoid_items:
                    for item in avoid_items:
                        st.write(f"• {item}")
                else:
                    st.caption(
                        "Ek bir kaçınma kuralı bulunmuyor."
                    )

    return view_model


def render_primary_coach_message():
    coach_message = read_text(COACH_MESSAGE_PATH)

    st.subheader("Koç mesajı")

    if not coach_message:
        st.info(
            "Henüz LLM koç mesajı yok. Soldaki 'LLM coach message üret' seçeneğini açıp pipeline çalıştırırsan burada görünecek."
        )
        return

    preview_lines = [
        line.strip()
        for line in coach_message.splitlines()
        if line.strip() and not line.strip().startswith("##")
    ]

    preview_text = " ".join(preview_lines[:2])

    if len(preview_text) > 420:
        preview_text = preview_text[:420].rstrip() + "..."

    with st.container(border=True):
        st.markdown("#### Kısa özet")

        if preview_text:
            st.write(preview_text)
        else:
            st.markdown(coach_message)

        with st.expander("Detaylı koç mesajını göster"):
            st.markdown(coach_message)

            st.divider()

            st.markdown("#### Kopyalanabilir metin")
            st.code(coach_message, language="markdown")

            st.download_button(
                label="Koç mesajını indir",
                data=coach_message,
                file_name="coach_message.md",
                mime="text/markdown",
                key="download_primary_coach_message",
            )


def render_compact_metrics(coach_context):
    st.subheader("Antrenman özeti")

    if not coach_context:
        st.info("Henüz metrics yok.")
        return

    metrics = coach_context.get("metrics", {})
    performance = coach_context.get("performance", {})

    with st.container(border=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**Son 7 gün**")
            st.write(f"Süre: `{metrics.get('total_hours_7_days', '-')}` saat")
            st.write(f"Mesafe: `{metrics.get('weekly_distance_km', '-')}` km")
            st.write(f"Koşu: `{metrics.get('running_sessions', '-')}` seans")
            st.write(f"Bisiklet: `{metrics.get('cycling_sessions', '-')}` seans")

        with col2:
            st.markdown("**Son 30 gün**")
            st.write(f"Süre: `{metrics.get('total_hours_30_days', '-')}` saat")
            st.write(f"Mesafe: `{metrics.get('monthly_distance_km', '-')}` km")
            st.write(f"Ortalama nabız: `{metrics.get('avg_hr_30_days', '-')}`")
            st.write(f"7g ort. nabız: `{metrics.get('avg_hr_7_days', '-')}`")

        with col3:
            st.markdown("**Yük sinyali**")
            st.write(f"Load ratio: `{metrics.get('load_ratio', '-')}`")
            st.write(f"Haftalık baseline: `{metrics.get('weekly_baseline_hours', '-')}` saat")
            st.write(f"30g haftalık ort.: `{metrics.get('rolling_30_weekly_hours', '-')}` saat")
            st.write(f"Önceki tempo: `{metrics.get('previous_23_weekly_hours', '-')}` saat")

    race_predictor = performance.get("race_predictor")

    if race_predictor:
        with st.expander("Garmin Race Predictor sinyali"):
            st.json(race_predictor)

def render_decision_cards(coach_context):
    st.subheader("Koç kararı")

    if not coach_context:
        st.info("Henüz karar üretilecek veri yok.")
        return

    final_decision = coach_context.get("final_decision", {})
    rules = coach_context.get("rules", {})
    manual_context = coach_context.get("manual_context", {})

    first_row = st.columns(4)

    decision_values = [
        (
            "Haftalık yük",
            label(final_decision.get("weekly_load")),
        ),
        (
            "Koşu",
            label(final_decision.get("running")),
        ),
        (
            "Bisiklet / Trainer",
            cycling_action_label(
                final_decision.get("cycling"),
                manual_context,
            ),
        ),
        (
            "Risk",
            label(rules.get("risk_level")),
        ),
    ]

    for column, (title, value) in zip(
        first_row,
        decision_values,
    ):
        with column:
            render_value_card(title, value)

    second_row = st.columns(3)

    secondary_values = [
        (
            "Öncelik",
            priority_action_label(
                final_decision.get("priority"),
                manual_context,
            ),
        ),
        (
            "Interval",
            (
                "Serbest"
                if rules.get("intervals_allowed")
                else "Hayır"
            ),
        ),
        (
            "Mobilite / Core",
            label(
                final_decision.get(
                    "strength_or_mobility"
                )
            ),
        ),
    ]

    for column, (title, value) in zip(
        second_row,
        secondary_values,
    ):
        with column:
            render_value_card(title, value)


def render_metrics(coach_context):
    st.subheader("Metrikler")

    if not coach_context:
        st.info("Henüz metrics yok.")
        return

    metrics = coach_context.get("metrics", {})
    performance = coach_context.get("performance", {})

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Son 7 gün", f"{metrics.get('total_hours_7_days', '-')} saat")
        st.metric("Son 30 gün", f"{metrics.get('total_hours_30_days', '-')} saat")

    with col2:
        st.metric("7 gün mesafe", f"{metrics.get('weekly_distance_km', '-')} km")
        st.metric("30 gün mesafe", f"{metrics.get('monthly_distance_km', '-')} km")

    with col3:
        st.metric("Koşu seansı", metrics.get("running_sessions", "-"))
        st.metric("Bisiklet seansı", metrics.get("cycling_sessions", "-"))

    with col4:
        st.metric("Load ratio", metrics.get("load_ratio", "-"))
        st.metric("Ort. nabız", metrics.get("avg_hr_7_days", "-"))

    race_predictor = performance.get("race_predictor")

    if race_predictor:
        with st.expander("Garmin Race Predictor sinyali"):
            st.json(race_predictor)


def render_context_summary(coach_context):
    st.subheader("Haftalık yaşam bağlamı")

    if not coach_context:
        st.info("Henüz context yok.")
        return

    manual_context = coach_context.get("manual_context", {})
    availability = manual_context.get("availability", {})
    recovery = manual_context.get("recovery", {})
    pain = manual_context.get("pain", {})
    life_load = manual_context.get("life_load", {})

    available_days = availability.get("available_days", [])
    day_labels = [
        option_label
        for option_label, option_value in AVAILABLE_DAY_OPTIONS.items()
        if option_value in available_days
    ]

    life_signals = []
    if life_load.get("work_stress") in ["high", "very_high"]:
        life_signals.append(
            f"İş yükü: {label(life_load.get('work_stress'))}"
        )
    if life_load.get("family_load") == "high":
        life_signals.append("Aile yükü yüksek")
    if life_load.get("caregiving_load") in ["medium", "high"]:
        life_signals.append("Bakım sorumluluğu var")
    if life_load.get("travel"):
        life_signals.append("Seyahat var")
    if life_load.get("routine_disruption") in ["medium", "high"]:
        life_signals.append("Rutin bozulmuş")
    if life_load.get("time_pressure") == "high":
        life_signals.append("Zaman baskısı yüksek")
    if life_load.get("emotional_load") == "high":
        life_signals.append("Duygusal yük yüksek")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Plan sınırları**")
        st.write(
            f"Haftalık niyet: `{label(manual_context.get('weekly_intent'))}`"
        )
        st.write(
            f"Maksimum seans: `{availability.get('max_sessions', '-')}`"
        )
        st.write(
            "Maksimum süre: "
            f"`{availability.get('max_session_duration_min', '-')} dk`"
        )
        st.write(
            f"Uygun günler: `{', '.join(day_labels) if day_labels else '-'}`"
        )

    with col2:
        st.markdown("**Toparlanma**")
        st.write(f"Enerji: `{label(recovery.get('energy_level'))}`")
        st.write(f"Uyku: `{label(recovery.get('sleep_quality'))}`")
        st.write(
            f"Mental yorgunluk: `{label(recovery.get('mental_fatigue'))}`"
        )
        st.write(
            f"Kas yorgunluğu: `{label(recovery.get('muscle_soreness'))}`"
        )

    with col3:
        st.markdown("**İmkânlar ve hayat yükü**")
        st.write(
            "Koşu / Outdoor / Trainer / Core: "
            f"`{label(availability.get('running_available'))}` / "
            f"`{label(availability.get('outdoor_bike_available'))}` / "
            f"`{label(availability.get('indoor_trainer_available'))}` / "
            f"`{label(availability.get('strength_available'))}`"
        )
        st.write(
            "Yaşam sinyalleri: "
            f"`{', '.join(life_signals) if life_signals else 'Normal'}`"
        )

    illness_status = recovery.get("illness_status", "none")
    if illness_status == "active":
        st.warning("Kullanıcı şu an hasta olduğunu bildirdi.")
    elif illness_status == "recovering":
        st.info("Kullanıcı hastalıktan yeni döndüğünü bildirdi.")

    if pain.get("active_pain"):
        pain_text = (
            f"Aktif ağrı: {label(pain.get('pain_area'))}, "
            f"şiddet {pain.get('pain_severity', '-')}/10"
        )
        if pain.get("pain_during_running"):
            pain_text += ", koşarken artıyor"
        if pain.get("pain_note"):
            pain_text += f". {pain.get('pain_note')}"
        st.warning(pain_text)

    if manual_context.get("user_note"):
        st.info(manual_context.get("user_note"))


def render_feedback_form(coach_context):
    st.subheader("Bu karar nasıldı?")

    if not coach_context:
        st.info("Feedback verebilmek için önce coach context oluşturulmalı.")
        return

    final_decision = coach_context.get("final_decision", {})
    rules = coach_context.get("rules", {})
    metrics = coach_context.get("metrics", {})

    with st.form("feedback_form"):
        feeling = st.radio(
            "Bu haftalık öneri sana nasıl geldi?",
            [
                "Uygun görünüyor",
                "Biraz hafif",
                "Biraz ağır",
                "Bu hafta uygulamam zor",
                "Emin değilim",
            ],
            horizontal=True,
        )

        completed_last_plan = st.radio(
            "Önceki planı ne kadar uygulayabildin?",
            [
                "Tamamına yakın",
                "Kısmen",
                "Çok az",
                "Hiç",
                "Bu ilk değerlendirme",
            ],
            horizontal=True,
        )

        flags = st.multiselect(
            "Bu hafta öne çıkan durumlar",
            [
                "Enerjim düşüktü",
                "Uyku kötüydü",
                "Koşular iyi hissettirdi",
                "Bisiklet yapamadım",
                "Ağrı/sızı oldu",
                "Plan gerçekçiydi",
                "Plan fazla iddialıydı",
            ],
        )

        note = st.text_area(
            "Kısa not",
            placeholder="Örn: Koşular iyi geldi ama bisiklete fırsat bulamadım.",
            height=90,
        )

        submitted = st.form_submit_button("Feedback kaydet")

    if not submitted:
        return

    feedback = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "feeling": feeling,
        "completed_last_plan": completed_last_plan,
        "flags": flags,
        "note": note.strip() or None,
        "decision_snapshot": {
            "weekly_load": final_decision.get("weekly_load"),
            "running": final_decision.get("running"),
            "cycling": final_decision.get("cycling"),
            "priority": final_decision.get("priority"),
            "risk_level": rules.get("risk_level"),
            "load_ratio": metrics.get("load_ratio"),
        },
    }

    append_feedback(feedback)

    st.success("Feedback kaydedildi. Bu ileride karar motorunu kişiselleştirmek için kullanılabilir.")

def render_reports(
    coach_context,
    weekly_plan,
    session_candidates,
    session_selection,
):
    st.subheader("Teknik detaylar")

    weekly_review = read_text(WEEKLY_REVIEW_PATH)
    coach_message = read_text(COACH_MESSAGE_PATH)

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        [
            "Koç mesajı arşivi",
            "Teknik haftalık rapor",
            "Weekly Plan JSON",
            "Teknik context",
            "Planning lineage",
            "Çalıştırma logu",
        ]
    )

    with tab1:
        if coach_message:
            st.markdown(coach_message)

            st.divider()

            st.markdown("#### Kopyalanabilir metin")

            st.code(coach_message, language="markdown")

            st.download_button(
                label="Koç mesajını indir",
                data=coach_message,
                file_name="coach_message.md",
                mime="text/markdown",
                key="download_reports_coach_message",
            )
        else:
            st.info(
                "Henüz LLM coach message yok. Soldaki LLM toggle açıkken pipeline çalıştırırsan oluşur."
            )

    with tab2:
        if weekly_review:
            st.markdown(weekly_review)
        else:
            st.info("weekly_review.md henüz yok.")

    with tab3:
        if weekly_plan:
            st.json(weekly_plan)
        else:
            st.info("weekly_plan.json henüz yok.")

    with tab4:
        if coach_context:
            st.json(coach_context)
        else:
            st.info("coach_context.json henüz yok.")

    with tab5:
        lineage_col1, lineage_col2 = st.columns(2)

        with lineage_col1:
            st.markdown("#### Session candidates")
            if session_candidates:
                st.json(session_candidates)
            else:
                st.info("session_candidates.json henüz yok.")

        with lineage_col2:
            st.markdown("#### Session selection")
            if session_selection:
                st.json(session_selection)
            else:
                st.info("session_selection.json henüz yok.")

    with tab6:
        stdout = st.session_state.get("last_pipeline_stdout")
        stderr = st.session_state.get("last_pipeline_stderr")
        returncode = st.session_state.get("last_pipeline_returncode")

        if returncode is None:
            st.info("Bu oturumda henüz pipeline çalıştırılmadı.")
        else:
            st.write(f"Return code: `{returncode}`")

            if stdout:
                st.code(stdout, language="text")

            if stderr:
                st.code(stderr, language="text")


def render_product_workspace(
    coach_context,
    weekly_plan,
    session_candidates,
    session_selection,
):
    plan_tab, data_tab, feedback_tab, technical_tab = st.tabs(
        [
            "Haftalık Plan",
            "Veriler ve Karar",
            "Feedback",
            "Teknik Detaylar",
        ]
    )

    with plan_tab:
        render_weekly_plan_product(
            coach_context,
            weekly_plan,
        )

        st.divider()
        render_primary_coach_message()

    with data_tab:
        render_decision_cards(coach_context)

        st.divider()
        render_compact_metrics(coach_context)

        st.divider()
        render_context_summary(coach_context)

    with feedback_tab:
        render_feedback_form(coach_context)

    with technical_tab:
        with st.expander(
            "Local dosya durumu",
            expanded=False,
        ):
            render_status_pills()

        st.divider()

        render_reports(
            coach_context,
            weekly_plan,
            session_candidates,
            session_selection,
        )

def inject_custom_css():
    st.markdown(
        """
        <style>
        /* App background */
        .stApp {
            background: linear-gradient(180deg, #f7fbf8 0%, #ffffff 42%);
            color: #172033;
        }

        /* Main content spacing */
        .block-container {
            padding-top: 2.2rem;
            padding-bottom: 3rem;
            max-width: 1180px;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background: #eef5f2;
            border-right: 1px solid #d9e7e0;
        }

        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            color: #163b34;
        }

        /* Top header */
        [data-testid="stHeader"] {
            background: rgba(247, 251, 248, 0.85);
        }

        /* Headings */
        h1 {
            color: #102820;
            letter-spacing: -0.03em;
        }

        h2, h3 {
            color: #163b34;
            letter-spacing: -0.02em;
        }

        /* Generic bordered containers */
        [data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid #dce8e2;
            border-radius: 16px;
            background: #ffffff;
            box-shadow: 0 6px 18px rgba(24, 58, 49, 0.05);
        }

        /* Metrics */
        [data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #e2ebe6;
            border-radius: 14px;
            padding: 14px 16px;
            box-shadow: 0 4px 14px rgba(24, 58, 49, 0.04);
        }

        [data-testid="stMetricLabel"] {
            color: #5f6f68;
            font-weight: 600;
        }

        [data-testid="stMetricValue"] {
            color: #163b34;
        }

        /* Buttons */
        .stButton > button {
            border-radius: 10px;
            border: 1px solid #bdd8cc;
            background: #ffffff;
            color: #163b34;
            font-weight: 600;
        }

        .stButton > button:hover {
            border-color: #4c9a7c;
            color: #0f5f49;
            background: #f2faf6;
        }

        /* Download button */
        .stDownloadButton > button {
            border-radius: 10px;
            border: 1px solid #bdd8cc;
            background: #e8f5ef;
            color: #163b34;
            font-weight: 600;
        }

        /* Tabs */
        button[data-baseweb="tab"] {
            font-weight: 600;
        }

        /* Info / success boxes slightly softer */
        [data-testid="stAlert"] {
            border-radius: 14px;
        }

        /* Expander */
        details {
            border-radius: 12px;
        }



        /* Top-level workspace tabs */
        div[data-testid="stTabs"] button[data-baseweb="tab"] {
            min-height: 44px;
            padding-left: 16px;
            padding-right: 16px;
        }

        /* Product value cards: long text must wrap, never ellipsize */
        .product-value-card {
            min-height: 122px;
            height: 100%;
            padding: 15px 16px;
            border: 1px solid #e2ebe6;
            border-radius: 14px;
            background: #ffffff;
            box-shadow: 0 4px 14px rgba(24, 58, 49, 0.04);
            overflow-wrap: anywhere;
        }

        .product-value-card-accent {
            background: #f7fcf9;
            border-color: #cfe6da;
        }

        .product-value-title {
            color: #63736c;
            font-size: 0.84rem;
            line-height: 1.25;
            font-weight: 650;
            margin-bottom: 8px;
        }

        .product-value-content {
            color: #163b34;
            font-size: 1.43rem;
            line-height: 1.2;
            font-weight: 650;
            letter-spacing: -0.025em;
            white-space: normal;
            overflow: visible;
            text-overflow: clip;
        }

        .product-value-helper {
            color: #76857f;
            font-size: 0.78rem;
            line-height: 1.35;
            margin-top: 9px;
        }

        .product-guidance {
            height: 100%;
            padding: 13px 15px;
            border-radius: 12px;
            margin-top: 4px;
            margin-bottom: 8px;
            overflow-wrap: anywhere;
        }

        .product-guidance-neutral {
            background: #f8fbfa;
            border: 1px solid #dce8e2;
        }

        .product-guidance-reference {
            background: #f6f8f7;
            border: 1px solid #e2e8e5;
        }

        .product-guidance-addon {
            background: #f0faf4;
            border: 1px solid #cce8d7;
        }

        .product-guidance-title {
            color: #53645d;
            font-size: 0.79rem;
            font-weight: 750;
            margin-bottom: 5px;
        }

        .product-guidance-value {
            color: #24352f;
            font-size: 0.91rem;
            line-height: 1.45;
        }

        /* Weekly plan product view */
        .weekly-focus-card {
            padding: 4px 2px 18px 2px;
        }

        .weekly-focus-eyebrow {
            color: #5f6f68;
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.12em;
            margin-bottom: 8px;
        }

        .weekly-focus-title {
            color: #102820;
            font-size: 1.55rem;
            line-height: 1.25;
            font-weight: 750;
            letter-spacing: -0.025em;
            max-width: 820px;
        }

        .weekly-focus-status {
            display: inline-block;
            margin-top: 12px;
            padding: 6px 10px;
            border-radius: 999px;
            background: #e8f5ef;
            color: #176348;
            font-size: 0.85rem;
            font-weight: 700;
        }

        /* Small helper cards */
        .coach-card {
            border-radius: 16px;
            padding: 18px 20px;
            border: 1px solid #dce8e2;
            box-shadow: 0 6px 18px rgba(24, 58, 49, 0.05);
            margin-bottom: 8px;
        }

        .coach-card h3 {
            margin-top: 0;
            margin-bottom: 12px;
        }

        .coach-card ul {
            margin-bottom: 0;
        }

        .coach-card-action {
            background: #f0faf4;
            border-color: #cce8d7;
        }

        .coach-card-avoid {
            background: #fff8ed;
            border-color: #f1dfbf;
        }

        .coach-card-message {
            background: #ffffff;
            border-color: #dce8e2;
        }

        .muted-caption {
            color: #6b7a75;
            font-size: 0.9rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def main():
    st.set_page_config(
        page_title="Garmin Coach Lab",
        page_icon="🏃",
        layout="wide",
    )

    inject_custom_css()

    ensure_data_dir()

    existing_context = load_json(
        MANUAL_CONTEXT_PATH,
        default=get_default_manual_context(),
    )

    current_manual_context = render_sidebar_context_form(
        existing_context
    )
    st.sidebar.divider()
    render_sidebar_actions(current_manual_context)
    st.sidebar.divider()
    st.sidebar.caption(
        "Local mode: Garmin şifresi alınmaz. "
        "Bu arayüz mevcut local data veya sample data ile çalışır."
    )

    coach_context = load_json(COACH_CONTEXT_PATH, default=None)
    weekly_plan = load_json(WEEKLY_PLAN_PATH, default=None)
    session_candidates = load_json(
        SESSION_CANDIDATES_PATH,
        default=None,
    )
    session_selection = load_json(
        SESSION_SELECTION_PATH,
        default=None,
    )

    render_hero(coach_context)

    st.divider()

    render_product_workspace(
        coach_context,
        weekly_plan,
        session_candidates,
        session_selection,
    )


if __name__ == "__main__":
    main()