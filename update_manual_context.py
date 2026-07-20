import json
import os
import sys


OUTPUT_PATH = "data/manual_context.json"


def configure_stdout():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")


def ask_choice(question, choices, default):
    print(f"\n{question}")
    print(f"Seçenekler: {', '.join(choices)}")
    value = input(f"Seçim [{default}]: ").strip()

    if not value:
        return default

    if value not in choices:
        print(f"Geçersiz seçim. Varsayılan kullanıldı: {default}")
        return default

    return value


def ask_bool(question, default=False):
    default_text = "e" if default else "h"
    value = input(f"{question} (e/h) [{default_text}]: ").strip().lower()

    if not value:
        return default

    return value in ["e", "evet", "y", "yes", "true", "1"]


def ask_text(question, default=None):
    if default:
        value = input(f"{question} [{default}]: ").strip()
    else:
        value = input(f"{question}: ").strip()

    if not value:
        return default

    return value


def ask_list(question):
    value = input(f"{question} (virgülle ayır, boş bırakabilirsin): ").strip()

    if not value:
        return []

    return [item.strip() for item in value.split(",") if item.strip()]


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    configure_stdout()

    print("\nGarmin Coach Lab - Güncel Durum Girişi")
    print("======================================")
    print(
        "Bu bilgiler Garmin'in bilmediği yaşam/antrenman bağlamını temsil eder.\n"
        "Koç kararı bu bilgilere göre yumuşatılabilir veya uygulanabilir hale getirilebilir."
    )

    family_status = ask_choice(
        "Aile / çocuk durumu nasıl?",
        ["normal", "child_sick", "family_busy"],
        "normal",
    )

    sleep_disrupted = ask_bool(
        "\nSon günlerde uyku bölündü mü?",
        default=False,
    )

    workload = ask_choice(
        "İş yoğunluğu nasıl?",
        ["low", "normal", "high", "very_high"],
        "normal",
    )

    travel = ask_bool(
        "\nSeyahat / tatil durumu var mı?",
        default=False,
    )

    training_environment = ask_choice(
        "Antrenman ortamı nedir?",
        ["home", "vacation", "travel", "hotel", "camp"],
        "home",
    )

    bike_available = ask_bool(
        "\nBisiklet imkanı var mı?",
        default=True,
    )

    trainer_available = ask_bool(
        "Trainer imkanı var mı?",
        default=True,
    )

    running_available = ask_bool(
        "Koşu imkanı var mı?",
        default=True,
    )

    energy_level = ask_choice(
        "Enerji seviyen nasıl?",
        ["very_low", "low", "normal", "high"],
        "normal",
    )

    injury_notes = ask_text(
        "\nAktif ağrı / sakatlık notu var mı? Yoksa boş bırak.",
        default=None,
    )

    available_days = ask_list(
        "\nBu hafta özellikle uygun olduğun günler var mı?"
    )

    user_note = ask_text(
        "\nEk not? Örn: Tatildeyim, bisiklet yok, koşu yapabiliyorum.",
        default=None,
    )

    manual_context = {
        "context_period": "current_week",
        "family_status": family_status,
        "sleep_disrupted": sleep_disrupted,
        "workload": workload,
        "travel": travel,
        "training_environment": training_environment,
        "bike_available": bike_available,
        "trainer_available": trainer_available,
        "running_available": running_available,
        "injury_notes": injury_notes,
        "energy_level": energy_level,
        "available_days": available_days,
        "user_note": user_note,
    }

    write_json(OUTPUT_PATH, manual_context)

    print("\nmanual_context.json güncellendi:")
    print(json.dumps(manual_context, ensure_ascii=False, indent=2))
    print(f"\nYazılan dosya: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()