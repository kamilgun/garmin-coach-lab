from __future__ import annotations

from datetime import datetime, timedelta
from statistics import median
from typing import Any, Dict, Iterable, List, Optional


RUNNING_TYPES = {"running", "trail_running", "treadmill_running"}
CYCLING_TYPES = {"cycling", "indoor_cycling", "road_biking", "mountain_biking"}


def parse_start_time(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None

    formats = (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
    )

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    return None


def activity_type_key(activity: Dict[str, Any]) -> str:
    activity_type = activity.get("activityType") or {}
    return str(activity_type.get("typeKey") or "unknown")


def is_running(activity: Dict[str, Any]) -> bool:
    return activity_type_key(activity) in RUNNING_TYPES


def is_cycling(activity: Dict[str, Any]) -> bool:
    return activity_type_key(activity) in CYCLING_TYPES


def seconds_to_hours(seconds: float) -> float:
    return round(seconds / 3600, 2)


def seconds_to_minutes(seconds: float) -> float:
    return round(seconds / 60, 1)


def meters_to_km(meters: float) -> float:
    return round(meters / 1000, 2)


def pace_seconds_per_km(duration_sec: float, distance_m: float) -> Optional[int]:
    if duration_sec <= 0 or distance_m < 1000:
        return None

    return round(duration_sec / (distance_m / 1000))


def pace_display(seconds_per_km: Optional[float]) -> Optional[str]:
    if seconds_per_km is None:
        return None

    total_seconds = max(0, round(seconds_per_km))
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes}:{seconds:02d}/km"


def percentile(values: Iterable[float], quantile: float) -> Optional[float]:
    ordered = sorted(float(value) for value in values)

    if not ordered:
        return None

    if len(ordered) == 1:
        return ordered[0]

    position = (len(ordered) - 1) * quantile
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(ordered) - 1)
    fraction = position - lower_index

    return (
        ordered[lower_index]
        + (ordered[upper_index] - ordered[lower_index]) * fraction
    )


def activities_within_days(
    activities: Iterable[Dict[str, Any]],
    days: int,
    now: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    reference_time = now or datetime.now()
    cutoff = reference_time - timedelta(days=days)

    selected = []

    for activity in activities:
        start = parse_start_time(activity.get("startTimeLocal"))
        if start is not None and start >= cutoff:
            selected.append(activity)

    return selected


def normalize_activity(activity: Dict[str, Any]) -> Dict[str, Any]:
    duration_sec = float(activity.get("duration") or 0)
    distance_m = float(activity.get("distance") or 0)
    type_key = activity_type_key(activity)

    avg_pace_sec = None
    if type_key in RUNNING_TYPES:
        avg_pace_sec = pace_seconds_per_km(duration_sec, distance_m)

    return {
        "activity_id": activity.get("activityId"),
        "activity_name": activity.get("activityName"),
        "type": type_key,
        "start_time_local": activity.get("startTimeLocal"),
        "duration_sec": round(duration_sec, 1),
        "duration_min": seconds_to_minutes(duration_sec),
        "distance_m": round(distance_m, 1),
        "distance_km": meters_to_km(distance_m),
        "avg_hr": activity.get("averageHR"),
        "max_hr": activity.get("maxHR"),
        "avg_speed_mps": activity.get("averageSpeed"),
        "avg_pace_sec_per_km": avg_pace_sec,
        "avg_pace_display": pace_display(avg_pace_sec),
        "elevation_gain_m": activity.get("elevationGain"),
        "calories": activity.get("calories"),
        "aerobic_training_effect": activity.get("aerobicTrainingEffect"),
    }


def summarize(
    activities: Iterable[Dict[str, Any]],
    days: int,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    selected = activities_within_days(activities, days, now=now)

    total_duration = sum(float(a.get("duration") or 0) for a in selected)
    total_distance = sum(float(a.get("distance") or 0) for a in selected)
    avg_hrs = [
        float(a["averageHR"])
        for a in selected
        if a.get("averageHR") is not None
    ]

    running_count = sum(1 for activity in selected if is_running(activity))
    cycling_count = sum(1 for activity in selected if is_cycling(activity))

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


def build_running_profile(
    normalized_activities: Iterable[Dict[str, Any]],
    window_days: int = 30,
) -> Dict[str, Any]:
    runs = [
        activity
        for activity in normalized_activities
        if activity.get("type") in RUNNING_TYPES
        and (activity.get("distance_km") or 0) >= 1.0
        and (activity.get("duration_min") or 0) >= 10.0
        and activity.get("avg_pace_sec_per_km") is not None
    ]

    if not runs:
        return {
            "window_days": window_days,
            "runs_analyzed": 0,
            "pace_guidance_available": False,
            "pace_guidance_note": (
                "Yeterli geçerli koşu olmadığı için pace/mesafe rehberi üretilmedi."
            ),
        }

    paces = [activity["avg_pace_sec_per_km"] for activity in runs]
    distances = [activity["distance_km"] for activity in runs]
    durations = [activity["duration_min"] for activity in runs]
    avg_hrs = [
        float(activity["avg_hr"])
        for activity in runs
        if activity.get("avg_hr") is not None
    ]

    pace_p25 = round(percentile(paces, 0.25))
    pace_median = round(median(paces))
    pace_p75 = round(percentile(paces, 0.75))

    return {
        "window_days": window_days,
        "runs_analyzed": len(runs),
        "pace_guidance_available": True,
        "pace_guidance_method": (
            "Son 30 gündeki en az 1 km ve 10 dakika olan koşuların "
            "gözlenen pace dağılımı. Kolay efor, pace hedefinden önceliklidir."
        ),
        "total_run_distance_km": round(sum(distances), 2),
        "total_run_duration_min": round(sum(durations), 1),
        "median_run_distance_km": round(median(distances), 2),
        "median_run_duration_min": round(median(durations), 1),
        "longest_run_distance_km": round(max(distances), 2),
        "longest_run_duration_min": round(max(durations), 1),
        "pace_distribution_sec_per_km": {
            "faster_quartile_p25": pace_p25,
            "median": pace_median,
            "slower_quartile_p75": pace_p75,
        },
        "pace_distribution_display": {
            "faster_quartile_p25": pace_display(pace_p25),
            "median": pace_display(pace_median),
            "slower_quartile_p75": pace_display(pace_p75),
        },
        "avg_hr_distribution": {
            "median": round(median(avg_hrs), 1) if avg_hrs else None,
            "min": round(min(avg_hrs), 1) if avg_hrs else None,
            "max": round(max(avg_hrs), 1) if avg_hrs else None,
        },
    }


def build_activity_history(
    activities: Iterable[Dict[str, Any]],
    days: int = 30,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    selected = activities_within_days(activities, days, now=now)
    normalized = [normalize_activity(activity) for activity in selected]

    normalized.sort(
        key=lambda activity: activity.get("start_time_local") or "",
        reverse=True,
    )

    return {
        "window_days": days,
        "activity_count": len(normalized),
        "activities": normalized,
    }
