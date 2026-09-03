from __future__ import annotations

from typing import Any, Dict, Optional


def _context_generated_at(
    coach_context: Optional[Dict[str, Any]],
) -> Optional[str]:
    if not coach_context:
        return None

    metadata = coach_context.get("metadata") or {}
    return metadata.get("generated_at")


def validate_artifact_lineage(
    coach_context: Optional[Dict[str, Any]],
    session_candidates: Optional[Dict[str, Any]],
    session_selection: Optional[Dict[str, Any]],
    weekly_plan: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Planning artifact zincirinin aynı coach-context lineage'ına
    ait olup olmadığını kontrol eder.

    Eksik downstream artifact tek başına hata değildir.
    Fakat mevcut bir artifact'in source dependency'si eksik veya
    uyuşmaz ise lineage invalid kabul edilir.
    """
    issues = []

    context_generated_at = _context_generated_at(
        coach_context
    )

    candidate_generated_at = (
        session_candidates.get("generated_at")
        if session_candidates
        else None
    )

    selection_generated_at = (
        session_selection.get("generated_at")
        if session_selection
        else None
    )

    def add_issue(
        artifact: str,
        code: str,
        message: str,
    ) -> None:
        issues.append(
            {
                "artifact": artifact,
                "code": code,
                "message": message,
            }
        )

    # Candidates -> Coach Context
    if session_candidates:
        if not coach_context:
            add_issue(
                "session_candidates.json",
                "missing_source_context",
                (
                    "Session candidates mevcut ancak "
                    "kaynak coach context bulunamadı."
                ),
            )
        else:
            source_context = session_candidates.get(
                "source_coach_context_generated_at"
            )

            if (
                source_context
                and context_generated_at
                and source_context != context_generated_at
            ):
                add_issue(
                    "session_candidates.json",
                    "stale_context_lineage",
                    (
                        "Session candidates mevcut coach "
                        "context'e ait değil."
                    ),
                )

    # Selection -> Candidates + Coach Context
    if session_selection:
        if not session_candidates:
            add_issue(
                "session_selection.json",
                "missing_source_candidates",
                (
                    "Session selection mevcut ancak "
                    "kaynak candidates artifact'i bulunamadı."
                ),
            )
        else:
            source_candidate = session_selection.get(
                "source_candidate_generated_at"
            )

            if (
                source_candidate
                and candidate_generated_at
                and source_candidate != candidate_generated_at
            ):
                add_issue(
                    "session_selection.json",
                    "stale_candidate_lineage",
                    (
                        "Session selection mevcut session "
                        "candidates artifact'ine ait değil."
                    ),
                )

            source_schema = session_selection.get(
                "source_candidate_schema_version"
            )
            candidate_schema = session_candidates.get(
                "schema_version"
            )

            if (
                source_schema
                and candidate_schema
                and source_schema != candidate_schema
            ):
                add_issue(
                    "session_selection.json",
                    "candidate_schema_mismatch",
                    (
                        "Session selection ile source "
                        "candidate schema sürümü uyuşmuyor."
                    ),
                )

        if not coach_context:
            add_issue(
                "session_selection.json",
                "missing_source_context",
                (
                    "Session selection mevcut ancak "
                    "kaynak coach context bulunamadı."
                ),
            )
        else:
            source_context = session_selection.get(
                "source_coach_context_generated_at"
            )

            if (
                source_context
                and context_generated_at
                and source_context != context_generated_at
            ):
                add_issue(
                    "session_selection.json",
                    "stale_context_lineage",
                    (
                        "Session selection mevcut coach "
                        "context'e ait değil."
                    ),
                )

    # Weekly Plan -> Selection + Coach Context
    if weekly_plan:
        if not session_selection:
            add_issue(
                "weekly_plan.json",
                "missing_source_selection",
                (
                    "Weekly plan mevcut ancak kaynak "
                    "session selection bulunamadı."
                ),
            )
        else:
            source_selection = weekly_plan.get(
                "source_selection_generated_at"
            )

            if (
                source_selection
                and selection_generated_at
                and source_selection != selection_generated_at
            ):
                add_issue(
                    "weekly_plan.json",
                    "stale_selection_lineage",
                    (
                        "Weekly plan mevcut session "
                        "selection artifact'ine ait değil."
                    ),
                )

            source_schema = weekly_plan.get(
                "source_selection_schema_version"
            )
            selection_schema = session_selection.get(
                "schema_version"
            )

            if (
                source_schema
                and selection_schema
                and source_schema != selection_schema
            ):
                add_issue(
                    "weekly_plan.json",
                    "selection_schema_mismatch",
                    (
                        "Weekly plan ile source selection "
                        "schema sürümü uyuşmuyor."
                    ),
                )

        if not coach_context:
            add_issue(
                "weekly_plan.json",
                "missing_source_context",
                (
                    "Weekly plan mevcut ancak kaynak "
                    "coach context bulunamadı."
                ),
            )
        else:
            source_context = weekly_plan.get(
                "source_coach_context_generated_at"
            )

            if (
                source_context
                and context_generated_at
                and source_context != context_generated_at
            ):
                add_issue(
                    "weekly_plan.json",
                    "stale_context_lineage",
                    (
                        "Weekly plan mevcut coach "
                        "context'e ait değil."
                    ),
                )

    return {
        "valid": not issues,
        "issue_count": len(issues),
        "issues": issues,
    }
