from __future__ import annotations

from typing import Any, Mapping

from .common import (
    ArtifactContractError,
    fail,
    require_bool,
    require_int,
    require_key,
    require_list,
    require_literal,
    require_mapping,
    require_string,
    validate_duration,
    validate_optional_metadata_strings,
    validate_string_list,
)


SESSION_SELECTION_SCHEMA_VERSION = "1.0"
SESSION_SELECTION_ARTIFACT = "session_selection"

VALID_SELECTION_STATUSES = {
    "ready",
    "no_session_selected",
    "no_structured_training",
}


def _validate_intensity(
    value: Any,
    *,
    path: str,
) -> Mapping[str, Any]:
    intensity = require_mapping(
        value,
        artifact=SESSION_SELECTION_ARTIFACT,
        path=path,
    )

    require_string(
        require_key(
            intensity,
            "cap",
            artifact=SESSION_SELECTION_ARTIFACT,
            path=path,
        ),
        artifact=SESSION_SELECTION_ARTIFACT,
        path=f"{path}.cap",
    )

    require_bool(
        require_key(
            intensity,
            "binding_cap",
            artifact=SESSION_SELECTION_ARTIFACT,
            path=path,
        ),
        artifact=SESSION_SELECTION_ARTIFACT,
        path=f"{path}.binding_cap",
    )

    require_bool(
        require_key(
            intensity,
            "no_unplanned_intensity",
            artifact=SESSION_SELECTION_ARTIFACT,
            path=path,
        ),
        artifact=SESSION_SELECTION_ARTIFACT,
        path=f"{path}.no_unplanned_intensity",
    )

    return intensity


def _validate_pace_guidance(
    value: Any,
    *,
    path: str,
) -> Mapping[str, Any]:
    pace = require_mapping(
        value,
        artifact=SESSION_SELECTION_ARTIFACT,
        path=path,
    )

    available = require_bool(
        require_key(
            pace,
            "available",
            artifact=SESSION_SELECTION_ARTIFACT,
            path=path,
        ),
        artifact=SESSION_SELECTION_ARTIFACT,
        path=f"{path}.available",
    )

    if not available:
        return pace

    binding = require_bool(
        require_key(
            pace,
            "binding",
            artifact=SESSION_SELECTION_ARTIFACT,
            path=path,
        ),
        artifact=SESSION_SELECTION_ARTIFACT,
        path=f"{path}.binding",
    )

    if binding:
        fail(
            SESSION_SELECTION_ARTIFACT,
            f"{path}.binding",
            "Weekly Plan v1 pace guidance bağlayıcı olamaz.",
        )

    require_int(
        require_key(
            pace,
            "target_reference_sec_per_km",
            artifact=SESSION_SELECTION_ARTIFACT,
            path=path,
        ),
        artifact=SESSION_SELECTION_ARTIFACT,
        path=f"{path}.target_reference_sec_per_km",
        minimum=1,
    )
    require_string(
        require_key(
            pace,
            "target_reference_display",
            artifact=SESSION_SELECTION_ARTIFACT,
            path=path,
        ),
        artifact=SESSION_SELECTION_ARTIFACT,
        path=f"{path}.target_reference_display",
    )

    range_seconds = require_mapping(
        require_key(
            pace,
            "range_sec_per_km",
            artifact=SESSION_SELECTION_ARTIFACT,
            path=path,
        ),
        artifact=SESSION_SELECTION_ARTIFACT,
        path=f"{path}.range_sec_per_km",
    )
    faster = require_int(
        require_key(
            range_seconds,
            "faster",
            artifact=SESSION_SELECTION_ARTIFACT,
            path=f"{path}.range_sec_per_km",
        ),
        artifact=SESSION_SELECTION_ARTIFACT,
        path=f"{path}.range_sec_per_km.faster",
        minimum=1,
    )
    slower = require_int(
        require_key(
            range_seconds,
            "slower",
            artifact=SESSION_SELECTION_ARTIFACT,
            path=f"{path}.range_sec_per_km",
        ),
        artifact=SESSION_SELECTION_ARTIFACT,
        path=f"{path}.range_sec_per_km.slower",
        minimum=1,
    )

    if faster > slower:
        fail(
            SESSION_SELECTION_ARTIFACT,
            f"{path}.range_sec_per_km",
            "faster değeri slower değerinden büyük olamaz.",
        )

    return pace


def _validate_distance_guidance(
    value: Any,
    *,
    path: str,
) -> Mapping[str, Any]:
    distance = require_mapping(
        value,
        artifact=SESSION_SELECTION_ARTIFACT,
        path=path,
    )

    available = require_bool(
        require_key(
            distance,
            "available",
            artifact=SESSION_SELECTION_ARTIFACT,
            path=path,
        ),
        artifact=SESSION_SELECTION_ARTIFACT,
        path=f"{path}.available",
    )

    if not available:
        return distance

    binding = require_bool(
        require_key(
            distance,
            "binding",
            artifact=SESSION_SELECTION_ARTIFACT,
            path=path,
        ),
        artifact=SESSION_SELECTION_ARTIFACT,
        path=f"{path}.binding",
    )

    if binding:
        fail(
            SESSION_SELECTION_ARTIFACT,
            f"{path}.binding",
            "Weekly Plan v1 mesafe rehberi bağlayıcı olamaz.",
        )

    target = require_key(
        distance,
        "target_km",
        artifact=SESSION_SELECTION_ARTIFACT,
        path=path,
    )

    if isinstance(target, bool) or not isinstance(target, (int, float)):
        fail(
            SESSION_SELECTION_ARTIFACT,
            f"{path}.target_km",
            "numeric olmalı.",
        )

    if target <= 0:
        fail(
            SESSION_SELECTION_ARTIFACT,
            f"{path}.target_km",
            "0 değerinden büyük olmalı.",
        )

    range_km = require_mapping(
        require_key(
            distance,
            "range_km",
            artifact=SESSION_SELECTION_ARTIFACT,
            path=path,
        ),
        artifact=SESSION_SELECTION_ARTIFACT,
        path=f"{path}.range_km",
    )

    minimum = range_km.get("min")
    maximum = range_km.get("max")

    if (
        isinstance(minimum, bool)
        or not isinstance(minimum, (int, float))
        or isinstance(maximum, bool)
        or not isinstance(maximum, (int, float))
    ):
        fail(
            SESSION_SELECTION_ARTIFACT,
            f"{path}.range_km",
            "min ve max numeric olmalı.",
        )

    if not 0 < minimum <= target <= maximum:
        fail(
            SESSION_SELECTION_ARTIFACT,
            f"{path}.range_km",
            "0 < min <= target_km <= max ilişkisi sağlanmalı.",
        )

    return distance


def _validate_add_on(
    add_on: Any,
    *,
    path: str,
    expected_date: str | None = None,
    require_inherited_schedule: bool = False,
) -> Mapping[str, Any]:
    value = require_mapping(
        add_on,
        artifact=SESSION_SELECTION_ARTIFACT,
        path=path,
    )

    require_string(
        require_key(
            value,
            "source_candidate_id",
            artifact=SESSION_SELECTION_ARTIFACT,
            path=path,
        ),
        artifact=SESSION_SELECTION_ARTIFACT,
        path=f"{path}.source_candidate_id",
    )
    require_string(
        require_key(
            value,
            "type",
            artifact=SESSION_SELECTION_ARTIFACT,
            path=path,
        ),
        artifact=SESSION_SELECTION_ARTIFACT,
        path=f"{path}.type",
    )
    require_string(
        require_key(
            value,
            "modality",
            artifact=SESSION_SELECTION_ARTIFACT,
            path=path,
        ),
        artifact=SESSION_SELECTION_ARTIFACT,
        path=f"{path}.modality",
    )

    validate_duration(
        require_key(
            value,
            "duration",
            artifact=SESSION_SELECTION_ARTIFACT,
            path=path,
        ),
        artifact=SESSION_SELECTION_ARTIFACT,
        path=f"{path}.duration",
    )
    _validate_intensity(
        require_key(
            value,
            "intensity",
            artifact=SESSION_SELECTION_ARTIFACT,
            path=path,
        ),
        path=f"{path}.intensity",
    )

    if require_inherited_schedule:
        scheduling = require_mapping(
            require_key(
                value,
                "scheduling",
                artifact=SESSION_SELECTION_ARTIFACT,
                path=path,
            ),
            artifact=SESSION_SELECTION_ARTIFACT,
            path=f"{path}.scheduling",
        )
        status = require_string(
            require_key(
                scheduling,
                "status",
                artifact=SESSION_SELECTION_ARTIFACT,
                path=f"{path}.scheduling",
            ),
            artifact=SESSION_SELECTION_ARTIFACT,
            path=f"{path}.scheduling.status",
        )

        if status != "inherits_main_session":
            fail(
                SESSION_SELECTION_ARTIFACT,
                f"{path}.scheduling.status",
                "inherits_main_session olmalı.",
            )

        inherited_date = require_string(
            require_key(
                scheduling,
                "date",
                artifact=SESSION_SELECTION_ARTIFACT,
                path=f"{path}.scheduling",
            ),
            artifact=SESSION_SELECTION_ARTIFACT,
            path=f"{path}.scheduling.date",
        )

        if expected_date is not None and inherited_date != expected_date:
            fail(
                SESSION_SELECTION_ARTIFACT,
                f"{path}.scheduling.date",
                "ana seans tarihiyle aynı olmalı.",
            )

    return value


def validate_prescribed_session_v1(
    session: Any,
    *,
    path: str,
    max_session_duration_min: int,
    expected_scheduling_status: str,
    validate_add_on_schedule: bool = False,
) -> Mapping[str, Any]:
    value = require_mapping(
        session,
        artifact=SESSION_SELECTION_ARTIFACT,
        path=path,
    )

    require_string(
        require_key(
            value,
            "session_id",
            artifact=SESSION_SELECTION_ARTIFACT,
            path=path,
        ),
        artifact=SESSION_SELECTION_ARTIFACT,
        path=f"{path}.session_id",
    )
    require_string(
        require_key(
            value,
            "source_candidate_id",
            artifact=SESSION_SELECTION_ARTIFACT,
            path=path,
        ),
        artifact=SESSION_SELECTION_ARTIFACT,
        path=f"{path}.source_candidate_id",
    )
    require_string(
        require_key(
            value,
            "modality",
            artifact=SESSION_SELECTION_ARTIFACT,
            path=path,
        ),
        artifact=SESSION_SELECTION_ARTIFACT,
        path=f"{path}.modality",
    )
    require_string(
        require_key(
            value,
            "type",
            artifact=SESSION_SELECTION_ARTIFACT,
            path=path,
        ),
        artifact=SESSION_SELECTION_ARTIFACT,
        path=f"{path}.type",
    )

    main_duration = validate_duration(
        require_key(
            value,
            "duration",
            artifact=SESSION_SELECTION_ARTIFACT,
            path=path,
        ),
        artifact=SESSION_SELECTION_ARTIFACT,
        path=f"{path}.duration",
    )
    total_duration = validate_duration(
        require_key(
            value,
            "session_total_duration",
            artifact=SESSION_SELECTION_ARTIFACT,
            path=path,
        ),
        artifact=SESSION_SELECTION_ARTIFACT,
        path=f"{path}.session_total_duration",
    )

    if total_duration["max"] > max_session_duration_min:
        fail(
            SESSION_SELECTION_ARTIFACT,
            f"{path}.session_total_duration.max",
            "planning limit üst süresini aşamaz.",
        )

    _validate_intensity(
        require_key(
            value,
            "intensity",
            artifact=SESSION_SELECTION_ARTIFACT,
            path=path,
        ),
        path=f"{path}.intensity",
    )
    _validate_pace_guidance(
        require_key(
            value,
            "pace_guidance",
            artifact=SESSION_SELECTION_ARTIFACT,
            path=path,
        ),
        path=f"{path}.pace_guidance",
    )
    _validate_distance_guidance(
        require_key(
            value,
            "distance_guidance",
            artifact=SESSION_SELECTION_ARTIFACT,
            path=path,
        ),
        path=f"{path}.distance_guidance",
    )

    scheduling = require_mapping(
        require_key(
            value,
            "scheduling",
            artifact=SESSION_SELECTION_ARTIFACT,
            path=path,
        ),
        artifact=SESSION_SELECTION_ARTIFACT,
        path=f"{path}.scheduling",
    )
    actual_status = require_string(
        require_key(
            scheduling,
            "status",
            artifact=SESSION_SELECTION_ARTIFACT,
            path=f"{path}.scheduling",
        ),
        artifact=SESSION_SELECTION_ARTIFACT,
        path=f"{path}.scheduling.status",
    )

    if actual_status != expected_scheduling_status:
        fail(
            SESSION_SELECTION_ARTIFACT,
            f"{path}.scheduling.status",
            f"{expected_scheduling_status} olmalı.",
        )

    expected_date = (
        scheduling.get("date")
        if expected_scheduling_status == "scheduled"
        else None
    )

    add_ons = require_list(
        require_key(
            value,
            "add_ons",
            artifact=SESSION_SELECTION_ARTIFACT,
            path=path,
        ),
        artifact=SESSION_SELECTION_ARTIFACT,
        path=f"{path}.add_ons",
    )

    add_on_target = 0
    add_on_min = 0
    add_on_max = 0

    for index, add_on in enumerate(add_ons):
        validated_add_on = _validate_add_on(
            add_on,
            path=f"{path}.add_ons[{index}]",
            expected_date=expected_date,
            require_inherited_schedule=validate_add_on_schedule,
        )
        add_on_duration = validated_add_on["duration"]
        add_on_target += add_on_duration["target_min"]
        add_on_min += add_on_duration["min"]
        add_on_max += add_on_duration["max"]

    if (
        total_duration["target_min"]
        != main_duration["target_min"] + add_on_target
    ):
        fail(
            SESSION_SELECTION_ARTIFACT,
            f"{path}.session_total_duration.target_min",
            "ana seans ve add-on target toplamına eşit olmalı.",
        )

    if total_duration["min"] != main_duration["min"] + add_on_min:
        fail(
            SESSION_SELECTION_ARTIFACT,
            f"{path}.session_total_duration.min",
            "ana seans ve add-on minimum toplamına eşit olmalı.",
        )

    if total_duration["max"] < main_duration["max"]:
        fail(
            SESSION_SELECTION_ARTIFACT,
            f"{path}.session_total_duration.max",
            "ana seans maksimumundan küçük olamaz.",
        )

    if total_duration["max"] > main_duration["max"] + add_on_max:
        fail(
            SESSION_SELECTION_ARTIFACT,
            f"{path}.session_total_duration.max",
            "ana seans ve add-on maksimum toplamını aşamaz.",
        )

    return value


def validate_session_selection_v1(
    artifact_data: Any,
) -> Mapping[str, Any]:
    artifact = require_mapping(
        artifact_data,
        artifact=SESSION_SELECTION_ARTIFACT,
        path="$",
    )

    schema_version = require_string(
        require_key(
            artifact,
            "schema_version",
            artifact=SESSION_SELECTION_ARTIFACT,
            path="$",
        ),
        artifact=SESSION_SELECTION_ARTIFACT,
        path="$.schema_version",
    )

    if schema_version != SESSION_SELECTION_SCHEMA_VERSION:
        fail(
            SESSION_SELECTION_ARTIFACT,
            "$.schema_version",
            f"{SESSION_SELECTION_SCHEMA_VERSION} olmalı.",
        )

    status = require_literal(
        require_key(
            artifact,
            "status",
            artifact=SESSION_SELECTION_ARTIFACT,
            path="$",
        ),
        VALID_SELECTION_STATUSES,
        artifact=SESSION_SELECTION_ARTIFACT,
        path="$.status",
    )

    if "generated_at" in artifact:
        validate_optional_metadata_strings(
            artifact,
            ("generated_at",),
            artifact=SESSION_SELECTION_ARTIFACT,
        )

    validate_optional_metadata_strings(
        artifact,
        (
            "source_candidate_schema_version",
            "source_candidate_generated_at",
            "source_engine_version",
            "planner_version",
            "planning_engine",
            "planning_stage",
            "source_coach_context_generated_at",
        ),
        artifact=SESSION_SELECTION_ARTIFACT,
    )

    if artifact.get("planning_stage") not in (
        None,
        "session_selection_and_prescription",
    ):
        fail(
            SESSION_SELECTION_ARTIFACT,
            "$.planning_stage",
            "session_selection_and_prescription olmalı.",
        )

    limits = require_mapping(
        require_key(
            artifact,
            "planning_limits",
            artifact=SESSION_SELECTION_ARTIFACT,
            path="$",
        ),
        artifact=SESSION_SELECTION_ARTIFACT,
        path="$.planning_limits",
    )
    max_sessions = require_int(
        require_key(
            limits,
            "max_sessions",
            artifact=SESSION_SELECTION_ARTIFACT,
            path="$.planning_limits",
        ),
        artifact=SESSION_SELECTION_ARTIFACT,
        path="$.planning_limits.max_sessions",
        minimum=1,
    )
    max_duration = require_int(
        require_key(
            limits,
            "max_session_duration_min",
            artifact=SESSION_SELECTION_ARTIFACT,
            path="$.planning_limits",
        ),
        artifact=SESSION_SELECTION_ARTIFACT,
        path="$.planning_limits.max_session_duration_min",
        minimum=1,
    )

    if "available_days" in limits:
        validate_string_list(
            limits["available_days"],
            artifact=SESSION_SELECTION_ARTIFACT,
            path="$.planning_limits.available_days",
        )

    if "available_modalities" in limits:
        validate_string_list(
            limits["available_modalities"],
            artifact=SESSION_SELECTION_ARTIFACT,
            path="$.planning_limits.available_modalities",
        )

    sessions = require_list(
        require_key(
            artifact,
            "sessions",
            artifact=SESSION_SELECTION_ARTIFACT,
            path="$",
        ),
        artifact=SESSION_SELECTION_ARTIFACT,
        path="$.sessions",
    )
    session_count = require_int(
        require_key(
            artifact,
            "session_count",
            artifact=SESSION_SELECTION_ARTIFACT,
            path="$",
        ),
        artifact=SESSION_SELECTION_ARTIFACT,
        path="$.session_count",
        minimum=0,
    )

    if session_count != len(sessions):
        fail(
            SESSION_SELECTION_ARTIFACT,
            "$.session_count",
            "sessions listesi uzunluğuna eşit olmalı.",
        )

    if status == "ready" and not sessions:
        fail(
            SESSION_SELECTION_ARTIFACT,
            "$.sessions",
            "ready durumunda en az bir seans olmalı.",
        )

    if status in {"no_session_selected", "no_structured_training"} and sessions:
        fail(
            SESSION_SELECTION_ARTIFACT,
            "$.sessions",
            f"{status} durumunda boş olmalı.",
        )

    session_ids: set[str] = set()
    expected_candidate_ids: list[str] = []

    for index, session in enumerate(sessions):
        validated = validate_prescribed_session_v1(
            session,
            path=f"$.sessions[{index}]",
            max_session_duration_min=max_duration,
            expected_scheduling_status="not_scheduled",
        )
        session_id = validated["session_id"]

        if session_id in session_ids:
            fail(
                SESSION_SELECTION_ARTIFACT,
                f"$.sessions[{index}].session_id",
                "benzersiz olmalı.",
            )

        session_ids.add(session_id)
        expected_candidate_ids.append(validated["source_candidate_id"])
        expected_candidate_ids.extend(
            add_on["source_candidate_id"]
            for add_on in validated["add_ons"]
        )

    selected_ids = validate_string_list(
        require_key(
            artifact,
            "selected_candidate_ids",
            artifact=SESSION_SELECTION_ARTIFACT,
            path="$",
        ),
        artifact=SESSION_SELECTION_ARTIFACT,
        path="$.selected_candidate_ids",
    )

    if (
        len(selected_ids) != len(expected_candidate_ids)
        or set(selected_ids) != set(expected_candidate_ids)
    ):
        fail(
            SESSION_SELECTION_ARTIFACT,
            "$.selected_candidate_ids",
            "seçilen ana seans ve add-on candidate id'leriyle eşleşmeli.",
        )

    require_list(
        require_key(
            artifact,
            "not_selected",
            artifact=SESSION_SELECTION_ARTIFACT,
            path="$",
        ),
        artifact=SESSION_SELECTION_ARTIFACT,
        path="$.not_selected",
    )

    summary = require_mapping(
        require_key(
            artifact,
            "selection_summary",
            artifact=SESSION_SELECTION_ARTIFACT,
            path="$",
        ),
        artifact=SESSION_SELECTION_ARTIFACT,
        path="$.selection_summary",
    )
    standalone_selected = require_int(
        require_key(
            summary,
            "standalone_selected",
            artifact=SESSION_SELECTION_ARTIFACT,
            path="$.selection_summary",
        ),
        artifact=SESSION_SELECTION_ARTIFACT,
        path="$.selection_summary.standalone_selected",
        minimum=0,
    )
    capacity_used = require_int(
        require_key(
            summary,
            "capacity_used",
            artifact=SESSION_SELECTION_ARTIFACT,
            path="$.selection_summary",
        ),
        artifact=SESSION_SELECTION_ARTIFACT,
        path="$.selection_summary.capacity_used",
        minimum=0,
    )
    capacity_limit = require_int(
        require_key(
            summary,
            "capacity_limit",
            artifact=SESSION_SELECTION_ARTIFACT,
            path="$.selection_summary",
        ),
        artifact=SESSION_SELECTION_ARTIFACT,
        path="$.selection_summary.capacity_limit",
        minimum=1,
    )

    if standalone_selected != len(sessions):
        fail(
            SESSION_SELECTION_ARTIFACT,
            "$.selection_summary.standalone_selected",
            "sessions listesi uzunluğuna eşit olmalı.",
        )

    if capacity_used != len(sessions):
        fail(
            SESSION_SELECTION_ARTIFACT,
            "$.selection_summary.capacity_used",
            "seçilen standalone seans sayısına eşit olmalı.",
        )

    if capacity_limit != max_sessions:
        fail(
            SESSION_SELECTION_ARTIFACT,
            "$.selection_summary.capacity_limit",
            "planning_limits.max_sessions ile eşleşmeli.",
        )

    if capacity_used > capacity_limit:
        fail(
            SESSION_SELECTION_ARTIFACT,
            "$.selection_summary.capacity_used",
            "capacity_limit değerini aşamaz.",
        )

    return artifact


__all__ = [
    "ArtifactContractError",
    "SESSION_SELECTION_SCHEMA_VERSION",
    "validate_prescribed_session_v1",
    "validate_session_selection_v1",
]
