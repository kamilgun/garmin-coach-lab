from __future__ import annotations

from datetime import timedelta
from typing import Any, Mapping

from .common import (
    fail,
    require_bool,
    require_int,
    require_key,
    require_list,
    require_literal,
    require_mapping,
    require_string,
    require_iso_date,
    validate_optional_metadata_strings,
    validate_string_list,
)
from .session_selection import validate_prescribed_session_v1


WEEKLY_PLAN_SCHEMA_VERSION = "1.0"
WEEKLY_PLAN_ARTIFACT = "weekly_plan"

VALID_PLAN_STATUSES = {
    "ready",
    "partially_scheduled",
    "unscheduled",
    "no_sessions",
    "no_structured_training",
}

DAY_NAMES = (
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
)


def _validate_unscheduled_session(
    session: Any,
    *,
    path: str,
    max_session_duration_min: int,
) -> Mapping[str, Any]:
    value = validate_prescribed_session_v1(
        session,
        path=path,
        max_session_duration_min=max_session_duration_min,
        expected_scheduling_status="unscheduled",
        validate_add_on_schedule=False,
    )

    scheduling = value["scheduling"]
    require_string(
        require_key(
            scheduling,
            "reason_code",
            artifact=WEEKLY_PLAN_ARTIFACT,
            path=f"{path}.scheduling",
        ),
        artifact=WEEKLY_PLAN_ARTIFACT,
        path=f"{path}.scheduling.reason_code",
    )
    require_string(
        require_key(
            scheduling,
            "reason",
            artifact=WEEKLY_PLAN_ARTIFACT,
            path=f"{path}.scheduling",
        ),
        artifact=WEEKLY_PLAN_ARTIFACT,
        path=f"{path}.scheduling.reason",
    )

    return value


def validate_weekly_plan_v1(
    artifact_data: Any,
) -> Mapping[str, Any]:
    artifact = require_mapping(
        artifact_data,
        artifact=WEEKLY_PLAN_ARTIFACT,
        path="$",
    )

    schema_version = require_string(
        require_key(
            artifact,
            "schema_version",
            artifact=WEEKLY_PLAN_ARTIFACT,
            path="$",
        ),
        artifact=WEEKLY_PLAN_ARTIFACT,
        path="$.schema_version",
    )

    if schema_version != WEEKLY_PLAN_SCHEMA_VERSION:
        fail(
            WEEKLY_PLAN_ARTIFACT,
            "$.schema_version",
            f"{WEEKLY_PLAN_SCHEMA_VERSION} olmalı.",
        )

    plan_status = require_literal(
        require_key(
            artifact,
            "plan_status",
            artifact=WEEKLY_PLAN_ARTIFACT,
            path="$",
        ),
        VALID_PLAN_STATUSES,
        artifact=WEEKLY_PLAN_ARTIFACT,
        path="$.plan_status",
    )

    validate_optional_metadata_strings(
        artifact,
        (
            "generated_at",
            "source_selection_schema_version",
            "source_selection_generated_at",
            "source_engine_version",
            "planner_version",
            "planning_engine",
            "planning_stage",
            "source_coach_context_generated_at",
        ),
        artifact=WEEKLY_PLAN_ARTIFACT,
    )

    if artifact.get("planning_stage") not in (
        None,
        "rolling_7_day_scheduling",
    ):
        fail(
            WEEKLY_PLAN_ARTIFACT,
            "$.planning_stage",
            "rolling_7_day_scheduling olmalı.",
        )

    horizon = require_mapping(
        require_key(
            artifact,
            "planning_horizon",
            artifact=WEEKLY_PLAN_ARTIFACT,
            path="$",
        ),
        artifact=WEEKLY_PLAN_ARTIFACT,
        path="$.planning_horizon",
    )

    horizon_type = require_string(
        require_key(
            horizon,
            "type",
            artifact=WEEKLY_PLAN_ARTIFACT,
            path="$.planning_horizon",
        ),
        artifact=WEEKLY_PLAN_ARTIFACT,
        path="$.planning_horizon.type",
    )

    if horizon_type != "rolling_7_days":
        fail(
            WEEKLY_PLAN_ARTIFACT,
            "$.planning_horizon.type",
            "rolling_7_days olmalı.",
        )

    start_date = require_iso_date(
        require_key(
            horizon,
            "start_date",
            artifact=WEEKLY_PLAN_ARTIFACT,
            path="$.planning_horizon",
        ),
        artifact=WEEKLY_PLAN_ARTIFACT,
        path="$.planning_horizon.start_date",
    )
    end_date = require_iso_date(
        require_key(
            horizon,
            "end_date",
            artifact=WEEKLY_PLAN_ARTIFACT,
            path="$.planning_horizon",
        ),
        artifact=WEEKLY_PLAN_ARTIFACT,
        path="$.planning_horizon.end_date",
    )
    days = require_int(
        require_key(
            horizon,
            "days",
            artifact=WEEKLY_PLAN_ARTIFACT,
            path="$.planning_horizon",
        ),
        artifact=WEEKLY_PLAN_ARTIFACT,
        path="$.planning_horizon.days",
        minimum=1,
    )

    if days != 7:
        fail(
            WEEKLY_PLAN_ARTIFACT,
            "$.planning_horizon.days",
            "7 olmalı.",
        )

    if end_date != start_date + timedelta(days=6):
        fail(
            WEEKLY_PLAN_ARTIFACT,
            "$.planning_horizon.end_date",
            "start_date + 6 gün olmalı.",
        )

    if "includes_start_date" in horizon:
        includes_start = require_bool(
            horizon["includes_start_date"],
            artifact=WEEKLY_PLAN_ARTIFACT,
            path="$.planning_horizon.includes_start_date",
        )
        if not includes_start:
            fail(
                WEEKLY_PLAN_ARTIFACT,
                "$.planning_horizon.includes_start_date",
                "true olmalı.",
            )

    limits = require_mapping(
        require_key(
            artifact,
            "planning_limits",
            artifact=WEEKLY_PLAN_ARTIFACT,
            path="$",
        ),
        artifact=WEEKLY_PLAN_ARTIFACT,
        path="$.planning_limits",
    )
    max_duration = require_int(
        require_key(
            limits,
            "max_session_duration_min",
            artifact=WEEKLY_PLAN_ARTIFACT,
            path="$.planning_limits",
        ),
        artifact=WEEKLY_PLAN_ARTIFACT,
        path="$.planning_limits.max_session_duration_min",
        minimum=1,
    )

    if "available_days" in limits:
        validate_string_list(
            limits["available_days"],
            artifact=WEEKLY_PLAN_ARTIFACT,
            path="$.planning_limits.available_days",
        )

    sessions = require_list(
        require_key(
            artifact,
            "sessions",
            artifact=WEEKLY_PLAN_ARTIFACT,
            path="$",
        ),
        artifact=WEEKLY_PLAN_ARTIFACT,
        path="$.sessions",
    )
    unscheduled = require_list(
        require_key(
            artifact,
            "unscheduled_sessions",
            artifact=WEEKLY_PLAN_ARTIFACT,
            path="$",
        ),
        artifact=WEEKLY_PLAN_ARTIFACT,
        path="$.unscheduled_sessions",
    )

    session_count = require_int(
        require_key(
            artifact,
            "session_count",
            artifact=WEEKLY_PLAN_ARTIFACT,
            path="$",
        ),
        artifact=WEEKLY_PLAN_ARTIFACT,
        path="$.session_count",
        minimum=0,
    )
    scheduled_count = require_int(
        require_key(
            artifact,
            "scheduled_count",
            artifact=WEEKLY_PLAN_ARTIFACT,
            path="$",
        ),
        artifact=WEEKLY_PLAN_ARTIFACT,
        path="$.scheduled_count",
        minimum=0,
    )
    unscheduled_count = require_int(
        require_key(
            artifact,
            "unscheduled_count",
            artifact=WEEKLY_PLAN_ARTIFACT,
            path="$",
        ),
        artifact=WEEKLY_PLAN_ARTIFACT,
        path="$.unscheduled_count",
        minimum=0,
    )

    if session_count != len(sessions):
        fail(
            WEEKLY_PLAN_ARTIFACT,
            "$.session_count",
            "scheduled sessions listesi uzunluğuna eşit olmalı.",
        )

    if scheduled_count != len(sessions):
        fail(
            WEEKLY_PLAN_ARTIFACT,
            "$.scheduled_count",
            "sessions listesi uzunluğuna eşit olmalı.",
        )

    if unscheduled_count != len(unscheduled):
        fail(
            WEEKLY_PLAN_ARTIFACT,
            "$.unscheduled_count",
            "unscheduled_sessions listesi uzunluğuna eşit olmalı.",
        )

    if plan_status == "ready":
        if not sessions or unscheduled:
            fail(
                WEEKLY_PLAN_ARTIFACT,
                "$.plan_status",
                "ready için en az bir scheduled ve sıfır unscheduled seans gerekir.",
            )
    elif plan_status == "partially_scheduled":
        if not sessions or not unscheduled:
            fail(
                WEEKLY_PLAN_ARTIFACT,
                "$.plan_status",
                "partially_scheduled için iki liste de boş olmamalı.",
            )
    elif plan_status == "unscheduled":
        if sessions or not unscheduled:
            fail(
                WEEKLY_PLAN_ARTIFACT,
                "$.plan_status",
                "unscheduled için scheduled boş, unscheduled dolu olmalı.",
            )
    elif plan_status in {"no_sessions", "no_structured_training"}:
        if sessions or unscheduled:
            fail(
                WEEKLY_PLAN_ARTIFACT,
                "$.plan_status",
                f"{plan_status} için iki seans listesi de boş olmalı.",
            )

    used_dates: set[str] = set()
    session_ids: set[str] = set()

    for index, session in enumerate(sessions):
        path = f"$.sessions[{index}]"
        validated = validate_prescribed_session_v1(
            session,
            path=path,
            max_session_duration_min=max_duration,
            expected_scheduling_status="scheduled",
            validate_add_on_schedule=True,
        )

        session_id = validated["session_id"]
        if session_id in session_ids:
            fail(
                WEEKLY_PLAN_ARTIFACT,
                f"{path}.session_id",
                "benzersiz olmalı.",
            )
        session_ids.add(session_id)

        scheduling = validated["scheduling"]
        scheduled_date_text = require_string(
            require_key(
                scheduling,
                "date",
                artifact=WEEKLY_PLAN_ARTIFACT,
                path=f"{path}.scheduling",
            ),
            artifact=WEEKLY_PLAN_ARTIFACT,
            path=f"{path}.scheduling.date",
        )
        scheduled_date = require_iso_date(
            scheduled_date_text,
            artifact=WEEKLY_PLAN_ARTIFACT,
            path=f"{path}.scheduling.date",
        )

        if not start_date <= scheduled_date <= end_date:
            fail(
                WEEKLY_PLAN_ARTIFACT,
                f"{path}.scheduling.date",
                "planning horizon içinde olmalı.",
            )

        if scheduled_date_text in used_dates:
            fail(
                WEEKLY_PLAN_ARTIFACT,
                f"{path}.scheduling.date",
                "aynı güne iki standalone seans atanamaz.",
            )
        used_dates.add(scheduled_date_text)

        day = require_string(
            require_key(
                scheduling,
                "day",
                artifact=WEEKLY_PLAN_ARTIFACT,
                path=f"{path}.scheduling",
            ),
            artifact=WEEKLY_PLAN_ARTIFACT,
            path=f"{path}.scheduling.day",
        )
        expected_day = DAY_NAMES[scheduled_date.weekday()]

        if day != expected_day:
            fail(
                WEEKLY_PLAN_ARTIFACT,
                f"{path}.scheduling.day",
                f"tarihle uyumlu olarak {expected_day} olmalı.",
            )

    for index, session in enumerate(unscheduled):
        path = f"$.unscheduled_sessions[{index}]"
        validated = _validate_unscheduled_session(
            session,
            path=path,
            max_session_duration_min=max_duration,
        )

        session_id = validated["session_id"]
        if session_id in session_ids:
            fail(
                WEEKLY_PLAN_ARTIFACT,
                f"{path}.session_id",
                "scheduled ve unscheduled listeleri arasında benzersiz olmalı.",
            )
        session_ids.add(session_id)

    summary = require_mapping(
        require_key(
            artifact,
            "schedule_summary",
            artifact=WEEKLY_PLAN_ARTIFACT,
            path="$",
        ),
        artifact=WEEKLY_PLAN_ARTIFACT,
        path="$.schedule_summary",
    )
    requested = require_int(
        require_key(
            summary,
            "requested_sessions",
            artifact=WEEKLY_PLAN_ARTIFACT,
            path="$.schedule_summary",
        ),
        artifact=WEEKLY_PLAN_ARTIFACT,
        path="$.schedule_summary.requested_sessions",
        minimum=0,
    )
    summary_scheduled = require_int(
        require_key(
            summary,
            "scheduled_sessions",
            artifact=WEEKLY_PLAN_ARTIFACT,
            path="$.schedule_summary",
        ),
        artifact=WEEKLY_PLAN_ARTIFACT,
        path="$.schedule_summary.scheduled_sessions",
        minimum=0,
    )
    all_sessions_scheduled = require_bool(
        require_key(
            summary,
            "all_sessions_scheduled",
            artifact=WEEKLY_PLAN_ARTIFACT,
            path="$.schedule_summary",
        ),
        artifact=WEEKLY_PLAN_ARTIFACT,
        path="$.schedule_summary.all_sessions_scheduled",
    )

    if requested != len(sessions) + len(unscheduled):
        fail(
            WEEKLY_PLAN_ARTIFACT,
            "$.schedule_summary.requested_sessions",
            "scheduled + unscheduled toplamına eşit olmalı.",
        )

    if summary_scheduled != len(sessions):
        fail(
            WEEKLY_PLAN_ARTIFACT,
            "$.schedule_summary.scheduled_sessions",
            "sessions listesi uzunluğuna eşit olmalı.",
        )

    if all_sessions_scheduled != (len(unscheduled) == 0):
        fail(
            WEEKLY_PLAN_ARTIFACT,
            "$.schedule_summary.all_sessions_scheduled",
            "unscheduled listesiyle tutarlı olmalı.",
        )

    return artifact


__all__ = [
    "WEEKLY_PLAN_SCHEMA_VERSION",
    "validate_weekly_plan_v1",
]
