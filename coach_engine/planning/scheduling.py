from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, timedelta
import math
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


WEEKLY_PLAN_SCHEMA_VERSION = "1.0"
HORIZON_DAYS = 7

DAY_NAMES = (
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
)

DAY_LABELS_TR = {
    "monday": "Pazartesi",
    "tuesday": "Salı",
    "wednesday": "Çarşamba",
    "thursday": "Perşembe",
    "friday": "Cuma",
    "saturday": "Cumartesi",
    "sunday": "Pazar",
}

DAY_ALIASES = {
    "mon": "monday",
    "monday": "monday",
    "pazartesi": "monday",
    "tue": "tuesday",
    "tues": "tuesday",
    "tuesday": "tuesday",
    "salı": "tuesday",
    "sali": "tuesday",
    "wed": "wednesday",
    "wednesday": "wednesday",
    "çarşamba": "wednesday",
    "carsamba": "wednesday",
    "thu": "thursday",
    "thur": "thursday",
    "thurs": "thursday",
    "thursday": "thursday",
    "perşembe": "thursday",
    "persembe": "thursday",
    "fri": "friday",
    "friday": "friday",
    "cuma": "friday",
    "sat": "saturday",
    "saturday": "saturday",
    "cumartesi": "saturday",
    "sun": "sunday",
    "sunday": "sunday",
    "pazar": "sunday",
}


def _unique(values: Iterable[str]) -> List[str]:
    result: List[str] = []

    for value in values:
        if value and value not in result:
            result.append(value)

    return result


def _parse_date(value: Optional[Any]) -> date:
    if value is None:
        return date.today()

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if isinstance(value, str):
        return date.fromisoformat(value)

    raise TypeError("start_date date, datetime, ISO string veya None olmalı.")


def _normalize_available_days(values: Sequence[Any]) -> List[str]:
    normalized: List[str] = []

    for value in values or []:
        key = str(value).strip().lower()
        canonical = DAY_ALIASES.get(key)

        if canonical and canonical not in normalized:
            normalized.append(canonical)

    return normalized


def _day_name(value: date) -> str:
    return DAY_NAMES[value.weekday()]


def _date_entry(start_date: date, value: date) -> Dict[str, Any]:
    day = _day_name(value)

    return {
        "date": value,
        "date_iso": value.isoformat(),
        "day": day,
        "day_label_tr": DAY_LABELS_TR[day],
        "day_offset": (value - start_date).days,
    }


def _horizon_dates(start_date: date) -> List[Dict[str, Any]]:
    return [
        _date_entry(
            start_date,
            start_date + timedelta(days=offset),
        )
        for offset in range(HORIZON_DAYS)
    ]


def _available_dates(
    horizon_dates: List[Dict[str, Any]],
    available_days: Sequence[Any],
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    normalized_days = _normalize_available_days(available_days)

    # Empty means "no weekday restriction", not "zero availability".
    if not available_days:
        return list(horizon_dates), {
            "input_days": [],
            "normalized_days": [],
            "empty_means": "all_days_available",
            "invalid_day_values_ignored": [],
        }

    invalid_values = [
        str(value)
        for value in available_days
        if str(value).strip().lower() not in DAY_ALIASES
    ]

    selected = [
        item
        for item in horizon_dates
        if item["day"] in normalized_days
    ]

    return selected, {
        "input_days": list(available_days),
        "normalized_days": normalized_days,
        "empty_means": None,
        "invalid_day_values_ignored": invalid_values,
    }


def _target_offsets(session_count: int) -> List[int]:
    """
    7 günlük pencere içinde dengeli hedef offset'ler üretir.

    Örnek:
    - 1 seans -> [3]
    - 2 seans -> [2, 4]
    - 3 seans -> [1, 3, 5]
    - 7 seans -> [0, 1, 2, 3, 4, 5, 6]
    """

    if session_count <= 0:
        return []

    return [
        min(
            HORIZON_DAYS - 1,
            math.floor(
                (index + 1) * HORIZON_DAYS / (session_count + 1)
            ),
        )
        for index in range(session_count)
    ]


def _choose_nearest_unused(
    available_dates: List[Dict[str, Any]],
    target_offset: int,
    used_dates: set[str],
) -> Optional[Dict[str, Any]]:
    choices = [
        item
        for item in available_dates
        if item["date_iso"] not in used_dates
    ]

    if not choices:
        return None

    # Eşit uzaklıkta hedefin ilerisindeki tarihi tercih eder.
    choices.sort(
        key=lambda item: (
            abs(item["day_offset"] - target_offset),
            0 if item["day_offset"] >= target_offset else 1,
            item["date_iso"],
        )
    )

    return choices[0]


def _schedule_flexibility(
    selected_date: Dict[str, Any],
    available_dates: List[Dict[str, Any]],
    all_scheduled_dates: set[str],
) -> Dict[str, Any]:
    alternatives = [
        item
        for item in available_dates
        if item["date_iso"] != selected_date["date_iso"]
        and item["date_iso"] not in all_scheduled_dates
    ]

    alternatives.sort(
        key=lambda item: (
            abs(item["day_offset"] - selected_date["day_offset"]),
            item["date_iso"],
        )
    )

    return {
        "flexible": bool(alternatives),
        "alternative_dates": [
            {
                "date": item["date_iso"],
                "day": item["day"],
                "day_label_tr": item["day_label_tr"],
            }
            for item in alternatives[:2]
        ],
        "note": (
            "Hedef gün uygun değilse listelenen alternatiflerden biri "
            "kullanılabilir; haftalık seans sayısı artırılmamalıdır."
            if alternatives
            else "Bu horizon içinde çakışmasız başka uygun gün bulunmuyor."
        ),
    }


def _scheduled_session(
    session: Dict[str, Any],
    selected_date: Dict[str, Any],
    target_offset: int,
    flexibility: Dict[str, Any],
) -> Dict[str, Any]:
    scheduled = deepcopy(session)

    scheduled["scheduling"] = {
        "status": "scheduled",
        "date": selected_date["date_iso"],
        "day": selected_date["day"],
        "day_label_tr": selected_date["day_label_tr"],
        "day_offset": selected_date["day_offset"],
        "target_day_offset": target_offset,
        "assignment_method": "nearest_available_day_to_balanced_target",
        "flexibility": flexibility,
    }

    # Add-on ayrı seans değildir; ana seansın gününü miras alır.
    for add_on in scheduled.get("add_ons", []):
        add_on["scheduling"] = {
            "status": "inherits_main_session",
            "date": selected_date["date_iso"],
            "day": selected_date["day"],
            "day_label_tr": selected_date["day_label_tr"],
        }

    return scheduled


def _unscheduled_session(
    session: Dict[str, Any],
    target_offset: int,
    reason_code: str,
    reason: str,
) -> Dict[str, Any]:
    unscheduled = deepcopy(session)

    unscheduled["scheduling"] = {
        "status": "unscheduled",
        "target_day_offset": target_offset,
        "reason_code": reason_code,
        "reason": reason,
    }

    return unscheduled


def schedule_weekly_plan(
    session_selection: Dict[str, Any],
    start_date: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Seçilmiş standalone seansları rolling 7 günlük pencereye yerleştirir.

    Kurallar:
    - Horizon bugün/start_date dahil 7 gündür.
    - available_days boşsa tüm günler kullanılabilir.
    - Aynı güne iki standalone seans atanmaz.
    - Seanslar mümkün olduğunca dengeli aralıklarla yerleştirilir.
    - Add-on ana seansın tarihini miras alır.
    - Uygun gün yetersizse seanslar sessizce üst üste bindirilmez;
      unscheduled olarak raporlanır.
    """

    if not isinstance(session_selection, dict):
        raise TypeError("session_selection bir dict olmalı.")

    resolved_start_date = _parse_date(start_date)
    resolved_end_date = resolved_start_date + timedelta(
        days=HORIZON_DAYS - 1
    )

    limits = session_selection.get("planning_limits") or {}
    input_available_days = limits.get("available_days") or []

    horizon_dates = _horizon_dates(resolved_start_date)
    available_dates, availability_resolution = _available_dates(
        horizon_dates,
        input_available_days,
    )

    sessions = [
        session
        for session in session_selection.get("sessions", [])
        if isinstance(session, dict)
    ]

    base_output = {
        "schema_version": WEEKLY_PLAN_SCHEMA_VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_selection_schema_version": session_selection.get(
            "schema_version"
        ),
        "source_selection_generated_at": session_selection.get(
            "generated_at"
        ),
        "source_engine_version": session_selection.get(
            "source_engine_version"
        ),
        "plan_status": None,
        "planning_horizon": {
            "type": "rolling_7_days",
            "start_date": resolved_start_date.isoformat(),
            "end_date": resolved_end_date.isoformat(),
            "days": HORIZON_DAYS,
            "includes_start_date": True,
        },
        "week_focus": session_selection.get("weekly_intent"),
        "priority": session_selection.get("priority"),
        "planning_limits": deepcopy(limits),
        "schedule_policy": {
            "same_day_standalone_sessions_allowed": False,
            "add_ons_inherit_main_session_date": True,
            "distribution_method": "balanced_targets_then_nearest_available_day",
            "available_days_empty_means": "all_days_available",
            "past_dates_allowed": False,
        },
        "availability_resolution": availability_resolution,
        "available_dates_in_horizon": [
            {
                "date": item["date_iso"],
                "day": item["day"],
                "day_label_tr": item["day_label_tr"],
                "day_offset": item["day_offset"],
            }
            for item in available_dates
        ],
        "avoid": deepcopy(session_selection.get("avoid") or []),
        "plan_reasons": _unique(
            session_selection.get("reasons") or []
        ),
    }

    if session_selection.get("status") == "no_structured_training":
        return {
            **base_output,
            "plan_status": "no_structured_training",
            "sessions": [],
            "session_count": 0,
            "scheduled_count": 0,
            "unscheduled_count": 0,
            "unscheduled_sessions": [],
            "schedule_summary": {
                "requested_sessions": 0,
                "scheduled_sessions": 0,
                "available_date_count": len(available_dates),
                "all_sessions_scheduled": True,
            },
        }

    if not sessions:
        return {
            **base_output,
            "plan_status": "no_sessions",
            "sessions": [],
            "session_count": 0,
            "scheduled_count": 0,
            "unscheduled_count": 0,
            "unscheduled_sessions": [],
            "schedule_summary": {
                "requested_sessions": 0,
                "scheduled_sessions": 0,
                "available_date_count": len(available_dates),
                "all_sessions_scheduled": True,
            },
        }

    targets = _target_offsets(len(sessions))
    used_dates: set[str] = set()
    assignments: List[Tuple[Dict[str, Any], Dict[str, Any], int]] = []
    unscheduled_sessions: List[Dict[str, Any]] = []

    for session, target_offset in zip(sessions, targets):
        selected_date = _choose_nearest_unused(
            available_dates,
            target_offset,
            used_dates,
        )

        if selected_date is None:
            reason_code = (
                "no_valid_available_day"
                if not available_dates
                else "insufficient_unique_available_dates"
            )
            reason = (
                "Rolling 7 günlük pencere içinde uygun gün bulunamadı."
                if not available_dates
                else (
                    "Standalone seans sayısı, rolling 7 günlük pencere "
                    "içindeki benzersiz uygun gün sayısını aşıyor."
                )
            )
            unscheduled_sessions.append(
                _unscheduled_session(
                    session,
                    target_offset,
                    reason_code,
                    reason,
                )
            )
            continue

        used_dates.add(selected_date["date_iso"])
        assignments.append(
            (session, selected_date, target_offset)
        )

    scheduled_sessions = []

    for session, selected_date, target_offset in assignments:
        flexibility = _schedule_flexibility(
            selected_date,
            available_dates,
            used_dates,
        )
        scheduled_sessions.append(
            _scheduled_session(
                session,
                selected_date,
                target_offset,
                flexibility,
            )
        )

    scheduled_sessions.sort(
        key=lambda session: session["scheduling"]["date"]
    )

    all_scheduled = len(unscheduled_sessions) == 0

    if all_scheduled:
        plan_status = "ready"
    elif scheduled_sessions:
        plan_status = "partially_scheduled"
    else:
        plan_status = "unscheduled"

    return {
        **base_output,
        "plan_status": plan_status,
        "sessions": scheduled_sessions,
        "session_count": len(scheduled_sessions),
        "scheduled_count": len(scheduled_sessions),
        "unscheduled_count": len(unscheduled_sessions),
        "unscheduled_sessions": unscheduled_sessions,
        "schedule_summary": {
            "requested_sessions": len(sessions),
            "scheduled_sessions": len(scheduled_sessions),
            "available_date_count": len(available_dates),
            "unique_dates_used": len(used_dates),
            "all_sessions_scheduled": all_scheduled,
        },
    }
