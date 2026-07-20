import json
import os
from datetime import datetime, timedelta
from garminconnect import Garmin

TOKENSTORE = r"C:\Users\TCKGUN\.garminconnect"


def seconds_to_hours(seconds):
    return round(seconds / 3600, 2)


def meters_to_km(meters):
    return round(meters / 1000, 2)


def summarize(activities, days):
    cutoff = datetime.now() - timedelta(days=days)

    selected = []
    for a in activities:
        start = datetime.strptime(a["startTimeLocal"], "%Y-%m-%d %H:%M:%S")
        if start >= cutoff:
            selected.append(a)

    total_duration = sum(a.get("duration") or 0 for a in selected)
    total_distance = sum(a.get("distance") or 0 for a in selected)
    avg_hrs = [a.get("averageHR") for a in selected if a.get("averageHR")]

    running_count = sum(
        1 for a in selected
        if a.get("activityType", {}).get("typeKey") == "running"
    )

    cycling_count = sum(
        1 for a in selected
        if a.get("activityType", {}).get("typeKey") in ["cycling", "indoor_cycling"]
    )

    avg_hr = round(sum(avg_hrs) / len(avg_hrs), 1) if avg_hrs else None

    return {
        "days": days,
        "activity_count": len(selected),
        "running_count": running_count,
        "cycling_count": cycling_count,
        "total_hours": seconds_to_hours(total_duration),
        "total_km": meters_to_km(total_distance),
        "avg_hr": avg_hr,
    }


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
    api = Garmin()
    api.login(TOKENSTORE)

    activities = api.get_activities(0, 100)

    summary_7 = summarize(activities, 7)
    summary_30 = summarize(activities, 30)

    print_summary(summary_7)
    print_summary(summary_30)

    os.makedirs("data", exist_ok=True)

    output = {
        "summary_7_days": summary_7,
        "summary_30_days": summary_30,
    }

    with open("data/activity_summary.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("\nJSON yazıldı: data/activity_summary.json")


if __name__ == "__main__":
    main()