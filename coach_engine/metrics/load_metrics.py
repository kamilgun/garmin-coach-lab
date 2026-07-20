def compute_load_signals(s7, s30):
    current_week_hours = float(s7.get("total_hours") or 0)
    last_30_days_hours = float(s30.get("total_hours") or 0)

    rolling_30_weekly_hours = (
        round(last_30_days_hours * 7 / 30, 2)
        if last_30_days_hours > 0
        else 0
    )

    previous_23_days_hours = max(last_30_days_hours - current_week_hours, 0)

    previous_23_weekly_hours = (
        round(previous_23_days_hours * 7 / 23, 2)
        if previous_23_days_hours > 0
        else None
    )

    baseline_candidates = [
        value
        for value in [rolling_30_weekly_hours, previous_23_weekly_hours]
        if value is not None and value > 0
    ]

    weekly_baseline_hours = max(baseline_candidates) if baseline_candidates else 0

    load_ratio = (
        round(current_week_hours / weekly_baseline_hours, 2)
        if weekly_baseline_hours > 0
        else None
    )

    return {
        "current_week_hours": current_week_hours,
        "rolling_30_weekly_hours": rolling_30_weekly_hours,
        "previous_23_weekly_hours": previous_23_weekly_hours,
        "weekly_baseline_hours": weekly_baseline_hours,
        "load_ratio": load_ratio,
    }