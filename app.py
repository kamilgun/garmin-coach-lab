import json
import shutil
import subprocess
import sys
from pathlib import Path
from datetime import datetime

import streamlit as st


DATA_DIR = Path("data")
SAMPLES_DIR = DATA_DIR / "samples"

MANUAL_CONTEXT_PATH = DATA_DIR / "manual_context.json"
ACTIVITY_SUMMARY_PATH = DATA_DIR / "activity_summary.json"
PERFORMANCE_SUMMARY_PATH = DATA_DIR / "performance_summary.json"
COACH_CONTEXT_PATH = DATA_DIR / "coach_context.json"
WEEKLY_REVIEW_PATH = DATA_DIR / "weekly_review.md"
COACH_MESSAGE_PATH = DATA_DIR / "coach_message.md"
FEEDBACK_LOG_PATH = DATA_DIR / "feedback_log.jsonl"

SAMPLE_ACTIVITY_SUMMARY_PATH = SAMPLES_DIR / "activity_summary.sample.json"
SAMPLE_PERFORMANCE_SUMMARY_PATH = SAMPLES_DIR / "performance_summary.sample.json"


FAMILY_STATUS_OPTIONS = {
    "Normal": "normal",
    "Aile yoğun": "family_busy",
    "Çocuk hasta": "child_sick",
}

WORKLOAD_OPTIONS = {
    "Düşük": "low",
    "Normal": "normal",
    "Yüksek": "high",
    "Çok yüksek": "very_high",
}

TRAINING_ENVIRONMENT_OPTIONS = {
    "Ev rutini": "home",
    "Tatil": "vacation",
    "Seyahat": "travel",
}

ENERGY_LEVEL_OPTIONS = {
    "Düşük": "low",
    "Normal": "normal",
    "Yüksek": "high",
}

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
    # rules
    "low": "Düşük",
    "medium": "Orta",
    "high": "Yüksek",
    "caution_growth": "Dikkatli artış",
    "stable": "Stabil",
    "productive_build": "Üretken artış",
    "restart": "Yeniden başlangıç",
    "below_baseline": "Baz çizginin altında",
    "spike_risk": "Ani yük artışı riski",
    "sharp_rebuild_low_absolute_load": "Hızlı dönüş / düşük mutlak yük",
    # context
    "normal": "Normal",
    "family_busy": "Aile yoğun",
    "child_sick": "Çocuk hasta",
    "home": "Ev rutini",
    "vacation": "Tatil",
    "travel": "Seyahat",
    "reduce": "Azalt",
    "recovery_only": "Sadece toparlanma",
    "controlled_build": "Kontrollü artır",
    "controlled_increase": "Kontrollü artır",
    "add_or_maintain_z2": "Kolay Z2 bisiklet/trainer ekle veya koru",
    "balanced": "Dengeli ilerleme",
    "restart_easy": "Kolay yeniden başlangıç",
    "optional_easy_z2": "Opsiyonel kolay Z2",
    "consistency": "Ritmi yeniden kurma",
    "recommended_light": "Hafif mobilite/core önerilir",
}


def label(value):
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "Evet" if value else "Hayır"
    return LABELS.get(value, str(value))

def get_cycling_mode_from_context(manual_context):
    bike_available = bool(manual_context.get("bike_available", True))
    trainer_available = bool(manual_context.get("trainer_available", True))

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


def get_default_manual_context():
    return {
        "context_period": "current_week",
        "family_status": "normal",
        "sleep_disrupted": False,
        "workload": "normal",
        "travel": False,
        "training_environment": "home",
        "bike_available": True,
        "trainer_available": True,
        "running_available": True,
        "injury_notes": None,
        "energy_level": "normal",
        "available_days": [],
        "user_note": None,
    }


def get_file_status():
    return {
        "Activity": ACTIVITY_SUMMARY_PATH.exists(),
        "Performance": PERFORMANCE_SUMMARY_PATH.exists(),
        "Context": MANUAL_CONTEXT_PATH.exists(),
        "Coach Context": COACH_CONTEXT_PATH.exists(),
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
    st.sidebar.header("Güncel durum")

    family_status_label = find_label_by_value(
        FAMILY_STATUS_OPTIONS,
        existing_context.get("family_status", "normal"),
        "Normal",
    )

    workload_label = find_label_by_value(
        WORKLOAD_OPTIONS,
        existing_context.get("workload", "normal"),
        "Normal",
    )

    training_environment_label = find_label_by_value(
        TRAINING_ENVIRONMENT_OPTIONS,
        existing_context.get("training_environment", "home"),
        "Ev rutini",
    )

    energy_level_label = find_label_by_value(
        ENERGY_LEVEL_OPTIONS,
        existing_context.get("energy_level", "normal"),
        "Normal",
    )

    existing_available_days = existing_context.get("available_days", [])
    existing_available_day_labels = [
        option_label
        for option_label, option_value in AVAILABLE_DAY_OPTIONS.items()
        if option_value in existing_available_days
    ]

    family_status = st.sidebar.selectbox(
        "Aile durumu",
        list(FAMILY_STATUS_OPTIONS.keys()),
        index=list(FAMILY_STATUS_OPTIONS.keys()).index(family_status_label),
    )

    workload = st.sidebar.selectbox(
        "İş / günlük yük",
        list(WORKLOAD_OPTIONS.keys()),
        index=list(WORKLOAD_OPTIONS.keys()).index(workload_label),
    )

    energy_level = st.sidebar.selectbox(
        "Enerji seviyesi",
        list(ENERGY_LEVEL_OPTIONS.keys()),
        index=list(ENERGY_LEVEL_OPTIONS.keys()).index(energy_level_label),
    )

    training_environment = st.sidebar.selectbox(
        "Antrenman ortamı",
        list(TRAINING_ENVIRONMENT_OPTIONS.keys()),
        index=list(TRAINING_ENVIRONMENT_OPTIONS.keys()).index(
            training_environment_label
        ),
    )

    st.sidebar.divider()

    sleep_disrupted = st.sidebar.checkbox(
        "Uyku bölündü / kalitesizdi",
        value=bool(existing_context.get("sleep_disrupted", False)),
    )

    travel = st.sidebar.checkbox(
        "Seyahat / tatil var",
        value=bool(existing_context.get("travel", False)),
    )

    running_available = st.sidebar.checkbox(
        "Koşu mümkün",
        value=bool(existing_context.get("running_available", True)),
    )

    bike_available = st.sidebar.checkbox(
        "Dışarıda bisiklet mümkün",
        value=bool(existing_context.get("bike_available", True)),
    )

    trainer_available = st.sidebar.checkbox(
        "Indoor trainer mümkün",
        value=bool(existing_context.get("trainer_available", True)),
    )

    available_days = st.sidebar.multiselect(
        "Bu hafta uygun günler",
        list(AVAILABLE_DAY_OPTIONS.keys()),
        default=existing_available_day_labels,
    )

    injury_notes = st.sidebar.text_input(
        "Aktif ağrı / sakatlık notu",
        value=existing_context.get("injury_notes") or "",
        placeholder="Yoksa boş bırak",
    )

    user_note = st.sidebar.text_area(
        "Ek not",
        value=existing_context.get("user_note") or "",
        placeholder="Örn: Tatildeyim, koşabiliyorum ama bisiklet yok.",
        height=90,
    )

    manual_context = {
        "context_period": "current_week",
        "family_status": FAMILY_STATUS_OPTIONS[family_status],
        "sleep_disrupted": sleep_disrupted,
        "workload": WORKLOAD_OPTIONS[workload],
        "travel": travel,
        "training_environment": TRAINING_ENVIRONMENT_OPTIONS[training_environment],
        "bike_available": bike_available,
        "trainer_available": trainer_available,
        "running_available": running_available,
        "injury_notes": injury_notes.strip() or None,
        "energy_level": ENERGY_LEVEL_OPTIONS[energy_level],
        "available_days": [
            AVAILABLE_DAY_OPTIONS[option_label]
            for option_label in available_days
        ],
        "user_note": user_note.strip() or None,
    }

    if st.sidebar.button("Context kaydet", use_container_width=True):
        write_json(MANUAL_CONTEXT_PATH, manual_context)
        st.sidebar.success("Context kaydedildi.")

    return manual_context


def render_sidebar_actions():
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

    if st.sidebar.button("Pipeline çalıştır", use_container_width=True):
        result = run_local_pipeline(use_llm=use_llm)

        st.session_state["last_pipeline_stdout"] = result.stdout
        st.session_state["last_pipeline_stderr"] = result.stderr
        st.session_state["last_pipeline_returncode"] = result.returncode

        if result.returncode == 0:
            st.sidebar.success("Pipeline tamamlandı.")
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
            "Henüz coach_context.json bulunamadı. Soldan context kaydedip "
            "sample data ile pipeline çalıştırarak başlayabilirsin."
        )
        return

    final_decision = coach_context.get("final_decision", {})
    rules = coach_context.get("rules", {})

    progression_label = label(rules.get("progression_status"))
    manual_context = coach_context.get("manual_context", {})
    priority_label = priority_action_label(final_decision.get("priority"), manual_context)

    st.markdown(
        f"""
        ### Bu haftanın özeti

        **Karar:** {label(final_decision.get("weekly_load"))}  
        **Ana odak:** {priority_label}  
        **Progression sinyali:** {progression_label}
        """
    )


def render_decision_cards(coach_context):
    st.subheader("Koç kararı")

    if not coach_context:
        st.info("Henüz karar üretilecek veri yok.")
        return

    final_decision = coach_context.get("final_decision", {})
    rules = coach_context.get("rules", {})
    manual_context = coach_context.get("manual_context", {})

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Haftalık yük", label(final_decision.get("weekly_load")))

    with col2:
        st.metric("Koşu", label(final_decision.get("running")))

    with col3:
        st.metric("Bisiklet/Trainer", cycling_action_label(final_decision.get("cycling"), manual_context))

    with col4:
        st.metric("Risk", label(rules.get("risk_level")))

    col5, col6, col7 = st.columns(3)

    with col5:
        st.metric("Öncelik", priority_action_label(final_decision.get("priority"), manual_context))

    with col6:
        st.metric("Interval", "Serbest" if rules.get("intervals_allowed") else "Hayır")

    with col7:
        st.metric("Mobilite/Core", label(final_decision.get("strength_or_mobility")))

    reason = final_decision.get("reason")

    if reason:
        st.markdown("#### Neden?")
        st.info(reason)


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
    st.subheader("Yaşam bağlamı")

    if not coach_context:
        st.info("Henüz context yok.")
        return

    manual_context = coach_context.get("manual_context", {})

    col1, col2, col3 = st.columns(3)

    with col1:
        st.write(f"**Aile:** {label(manual_context.get('family_status'))}")
        st.write(f"**İş yükü:** {label(manual_context.get('workload'))}")
        st.write(f"**Enerji:** {label(manual_context.get('energy_level'))}")

    with col2:
        st.write(f"**Ortam:** {label(manual_context.get('training_environment'))}")
        st.write(f"**Seyahat:** {label(manual_context.get('travel'))}")
        st.write(f"**Uyku bölündü:** {label(manual_context.get('sleep_disrupted'))}")

    with col3:
        st.write(f"**Koşu mümkün:** {label(manual_context.get('running_available'))}")
        st.write(f"**Dışarıda bisiklet mümkün:** {label(manual_context.get('bike_available'))}")
        st.write(f"**Indoor trainer mümkün:** {label(manual_context.get('trainer_available'))}")

    if manual_context.get("injury_notes"):
        st.warning(f"Aktif ağrı notu: {manual_context.get('injury_notes')}")

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

def render_reports(coach_context):
    st.subheader("Raporlar")

    weekly_review = read_text(WEEKLY_REVIEW_PATH)
    coach_message = read_text(COACH_MESSAGE_PATH)

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "Koç mesajı",
            "Teknik haftalık rapor",
            "Teknik context",
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
        if coach_context:
            st.json(coach_context)
        else:
            st.info("coach_context.json henüz yok.")

    with tab4:
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


def main():
    st.set_page_config(
        page_title="Garmin Coach Lab",
        page_icon="🏃",
        layout="wide",
    )

    ensure_data_dir()

    existing_context = load_json(
        MANUAL_CONTEXT_PATH,
        default=get_default_manual_context(),
    )

    render_sidebar_context_form(existing_context)
    st.sidebar.divider()
    render_sidebar_actions()
    st.sidebar.divider()
    st.sidebar.caption(
        "Local mode: Garmin şifresi alınmaz. "
        "Bu arayüz mevcut local data veya sample data ile çalışır."
    )

    coach_context = load_json(COACH_CONTEXT_PATH, default=None)

    render_hero(coach_context)

    st.divider()

    render_status_pills()

    st.divider()

    render_decision_cards(coach_context)

    st.divider()

    render_metrics(coach_context)

    st.divider()

    render_context_summary(coach_context)

    st.divider()

    render_feedback_form(coach_context)

    st.divider()

    render_reports(coach_context)


if __name__ == "__main__":
    main()