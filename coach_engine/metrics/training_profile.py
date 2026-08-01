from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List


TRAINING_PROFILE_SCHEMA_VERSION = "1.0"
RUNNING_TYPES = {"running", "trail_running", "treadmill_running"}


def get_default_running_profile() -> Dict[str, Any]:
    return {
        "window_days": 30,
        "runs_analyzed": 0,
        "pace_guidance_available": False,
        "pace_guidance_note": (
            "Running profile verisi bulunmadığı için pace ve mesafe rehberi "
            "henüz üretilemez."
        ),
        "total_run_distance_km": None,
        "total_run_duration_min": None,
        "median_run_distance_km": None,
        "median_run_duration_min": None,
        "longest_run_distance_km": None,
        "longest_run_duration_min": None,
        "pace_distribution_sec_per_km": {},
        "pace_distribution_display": {},
        "avg_hr_distribution": {},
    }


def normalize_running_profile(activity_data: Dict[str, Any]) -> Dict[str, Any]:
    source_profile = activity_data.get("running_profile_30_days")

    if not isinstance(source_profile, dict):
        return get_default_running_profile()

    normalized = get_default_running_profile()
    normalized.update(deepcopy(source_profile))

    normalized["window_days"] = source_profile.get("window_days", 30)
    normalized["runs_analyzed"] = source_profile.get("runs_analyzed", 0)
    normalized["pace_guidance_available"] = bool(
        source_profile.get("pace_guidance_available", False)
    )

    if normalized["pace_guidance_available"]:
        normalized.pop("pace_guidance_note", None)

    for field in (
        "pace_distribution_sec_per_km",
        "pace_distribution_display",
        "avg_hr_distribution",
    ):
        value = source_profile.get(field)
        normalized[field] = deepcopy(value) if isinstance(value, dict) else {}

    return normalized


def compact_recent_run(activity: Dict[str, Any]) -> Dict[str, Any]:
    start_time_local = activity.get("start_time_local")
    date = None

    if isinstance(start_time_local, str) and len(start_time_local) >= 10:
        date = start_time_local[:10]

    return {
        "activity_id": activity.get("activity_id"),
        "activity_name": activity.get("activity_name"),
        "date": date,
        "start_time_local": start_time_local,
        "type": activity.get("type"),
        "distance_km": activity.get("distance_km"),
        "duration_min": activity.get("duration_min"),
        "avg_pace_sec_per_km": activity.get("avg_pace_sec_per_km"),
        "avg_pace_display": activity.get("avg_pace_display"),
        "avg_hr": activity.get("avg_hr"),
        "max_hr": activity.get("max_hr"),
        "elevation_gain_m": activity.get("elevation_gain_m"),
        "aerobic_training_effect": activity.get("aerobic_training_effect"),
    }


def build_recent_runs(
    activity_data: Dict[str, Any],
    limit: int = 5,
) -> List[Dict[str, Any]]:
    history = activity_data.get("activity_history_30_days")

    if not isinstance(history, dict):
        return []

    activities = history.get("activities")

    if not isinstance(activities, list):
        return []

    runs = [
        activity
        for activity in activities
        if isinstance(activity, dict)
        and activity.get("type") in RUNNING_TYPES
    ]

    runs.sort(
        key=lambda activity: activity.get("start_time_local") or "",
        reverse=True,
    )

    return [
        compact_recent_run(activity)
        for activity in runs[: max(0, limit)]
    ]


def build_training_profile(
    activity_data: Dict[str, Any],
    recent_run_limit: int = 5,
) -> Dict[str, Any]:
    """
    Planner ve renderer katmanları için kompakt training profile üretir.

    Tam 30 günlük activity history coach_context içine kopyalanmaz.
    Yalnızca hesaplanmış running profile ve son birkaç koşunun gerekli
    alanları serving contract içine taşınır.
    """

    activity_data = activity_data or {}
    running_profile = normalize_running_profile(activity_data)
    recent_runs = build_recent_runs(
        activity_data,
        limit=recent_run_limit,
    )

    return {
        "schema_version": TRAINING_PROFILE_SCHEMA_VERSION,
        "source_activity_schema_version": activity_data.get("schema_version"),
        "running_30_days": running_profile,
        "recent_runs": recent_runs,
        "recent_runs_count": len(recent_runs),
        "recent_runs_limit": recent_run_limit,
        "data_available": bool(
            running_profile.get("runs_analyzed", 0) or recent_runs
        ),
    }
