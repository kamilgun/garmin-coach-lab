from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, Optional

from ..contracts import (
    validate_session_selection_v1,
    validate_weekly_plan_v1,
)
from .scheduling import schedule_weekly_plan
from .session_candidates import build_session_candidates
from .session_selection import select_sessions


PLANNER_VERSION = "0.1.0"
PLANNING_ENGINE = "rule_based_weekly_plan_v1"
PLANNING_BUNDLE_SCHEMA_VERSION = "1.0"


def _attach_stage_metadata(
    artifact: Dict[str, Any],
    *,
    stage: str,
    coach_context: Dict[str, Any],
) -> Dict[str, Any]:
    enriched = deepcopy(artifact)
    coach_metadata = coach_context.get("metadata") or {}

    enriched["planner_version"] = PLANNER_VERSION
    enriched["planning_engine"] = PLANNING_ENGINE
    enriched["planning_stage"] = stage
    enriched["source_coach_context_generated_at"] = coach_metadata.get(
        "generated_at"
    )

    return enriched


def build_weekly_plan_bundle(
    coach_context: Dict[str, Any],
    start_date: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Coach Context'ten tüm deterministic planning zincirini çalıştırır.

    Zincir:
        coach_context
        -> session candidates
        -> session selection / prescription
        -> rolling 7-day weekly plan

    Dönüş değeri hem final planı hem de debug/lineage amacıyla ara
    artifact'leri içerir.
    """

    if not isinstance(coach_context, dict):
        raise TypeError("coach_context bir dict olmalı.")

    candidate_artifact = build_session_candidates(coach_context)
    candidate_artifact = _attach_stage_metadata(
        candidate_artifact,
        stage="candidate_generation",
        coach_context=coach_context,
    )

    selection_artifact = select_sessions(
        coach_context,
        candidate_artifact,
    )
    selection_artifact = _attach_stage_metadata(
        selection_artifact,
        stage="session_selection_and_prescription",
        coach_context=coach_context,
    )
    validate_session_selection_v1(selection_artifact)

    weekly_plan = schedule_weekly_plan(
        selection_artifact,
        start_date=start_date,
    )
    weekly_plan = _attach_stage_metadata(
        weekly_plan,
        stage="rolling_7_day_scheduling",
        coach_context=coach_context,
    )
    validate_weekly_plan_v1(weekly_plan)

    generated_at = datetime.now().isoformat(timespec="seconds")

    return {
        "schema_version": PLANNING_BUNDLE_SCHEMA_VERSION,
        "planner_version": PLANNER_VERSION,
        "planning_engine": PLANNING_ENGINE,
        "generated_at": generated_at,
        "source_engine_version": (
            (coach_context.get("metadata") or {}).get("engine_version")
        ),
        "source_coach_context_generated_at": (
            (coach_context.get("metadata") or {}).get("generated_at")
        ),
        "session_candidates": candidate_artifact,
        "session_selection": selection_artifact,
        "weekly_plan": weekly_plan,
    }


def build_weekly_plan(
    coach_context: Dict[str, Any],
    start_date: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Dış tüketiciler için yalnızca final weekly_plan artifact'ini döndürür.
    """

    bundle = build_weekly_plan_bundle(
        coach_context,
        start_date=start_date,
    )
    return bundle["weekly_plan"]
