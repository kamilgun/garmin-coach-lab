import json
from datetime import datetime

from garminconnect import Garmin

from coach_engine.metrics.activity_history import (
    build_activity_history,
    build_running_profile,
    summarize,
)
from coach_engine.workspace import get_runtime_workspace


def print_summary(summary):
    print(f"\nSon {summary['days']} gün")
    print("-" * 30)
    print(f"Aktivite sayısı : {summary['activity_count']}")
    print(f"Koşu sayısı     : {summary['running_count']}")
    print(f"Bisiklet sayısı : {summary['cycling_count']}")
    print(f"Toplam süre     : {summary['total_hours']} saat")
    print(f"Toplam mesafe   : {summary['total_km']} km")
    print(f"Ortalama nabız  : {summary['avg_hr']}")


def main():
    runtime = get_runtime_workspace()

    api = Garmin()
    api.login(str(runtime.garmin_tokenstore))

    # Garmin'den gelen aktivite detayları burada zaten mevcut.
    activities = api.get_activities(0, 100)

    summary_7 = summarize(activities, 7)
    summary_30 = summarize(activities, 30)

    activity_history = build_activity_history(activities, days=30)
    running_profile = build_running_profile(
        activity_history["activities"],
        window_days=30,
    )

    print_summary(summary_7)
    print_summary(summary_30)

    print("\nRunning profile")
    print("-" * 30)
    print(f"Analiz edilen koşu: {running_profile.get('runs_analyzed', 0)}")
    print(
        "Median pace       : "
        f"{running_profile.get('pace_distribution_display', {}).get('median')}"
    )

    runtime.data_dir.mkdir(parents=True, exist_ok=True)

    output = {
        "schema_version": "2.0",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        # Backward-compatible aggregate alanlar:
        "summary_7_days": summary_7,
        "summary_30_days": summary_30,
        # Weekly Plan Builder için serving layer:
        "activity_history_30_days": activity_history,
        "running_profile_30_days": running_profile,
    }

    with runtime.activity_summary_path.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(
        f"\nJSON yazıldı: {runtime.activity_summary_path}"
    )



if __name__ == "__main__":
    main()
