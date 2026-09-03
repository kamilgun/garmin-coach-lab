from copy import deepcopy

from coach_engine.artifact_lineage import (
    validate_artifact_lineage,
)


def artifacts():
    context = {
        "metadata": {
            "generated_at": "2026-08-27T14:48:25",
        }
    }

    candidates = {
        "schema_version": "1.0",
        "generated_at": "2026-08-27T14:48:26",
        "source_coach_context_generated_at": (
            "2026-08-27T14:48:25"
        ),
    }

    selection = {
        "schema_version": "1.0",
        "generated_at": "2026-08-27T14:48:27",
        "source_candidate_generated_at": (
            "2026-08-27T14:48:26"
        ),
        "source_candidate_schema_version": "1.0",
        "source_coach_context_generated_at": (
            "2026-08-27T14:48:25"
        ),
    }

    plan = {
        "schema_version": "1.0",
        "generated_at": "2026-08-27T14:48:28",
        "source_selection_generated_at": (
            "2026-08-27T14:48:27"
        ),
        "source_selection_schema_version": "1.0",
        "source_coach_context_generated_at": (
            "2026-08-27T14:48:25"
        ),
    }

    return context, candidates, selection, plan


def run_tests():
    # 1. Healthy lineage.
    context, candidates, selection, plan = artifacts()

    result = validate_artifact_lineage(
        context,
        candidates,
        selection,
        plan,
    )

    assert result["valid"] is True
    assert result["issue_count"] == 0

    # 2. New context + old plan chain is stale.
    new_context = deepcopy(context)
    new_context["metadata"]["generated_at"] = (
        "2026-08-31T15:00:00"
    )

    result = validate_artifact_lineage(
        new_context,
        candidates,
        selection,
        plan,
    )

    assert result["valid"] is False

    codes = {
        issue["code"]
        for issue in result["issues"]
    }

    assert "stale_context_lineage" in codes

    # 3. Old selection behind new candidates.
    changed_candidates = deepcopy(candidates)
    changed_candidates["generated_at"] = (
        "2026-08-31T15:01:00"
    )

    result = validate_artifact_lineage(
        context,
        changed_candidates,
        selection,
        plan,
    )

    assert result["valid"] is False

    codes = {
        issue["code"]
        for issue in result["issues"]
    }

    assert "stale_candidate_lineage" in codes

    # 4. Old plan behind new selection.
    changed_selection = deepcopy(selection)
    changed_selection["generated_at"] = (
        "2026-08-31T15:02:00"
    )

    result = validate_artifact_lineage(
        context,
        candidates,
        changed_selection,
        plan,
    )

    assert result["valid"] is False

    codes = {
        issue["code"]
        for issue in result["issues"]
    }

    assert "stale_selection_lineage" in codes

    # 5. Orphan plan is invalid.
    result = validate_artifact_lineage(
        context,
        candidates,
        None,
        plan,
    )

    assert result["valid"] is False

    codes = {
        issue["code"]
        for issue in result["issues"]
    }

    assert "missing_source_selection" in codes

    # 6. Missing downstream artifacts are okay.
    result = validate_artifact_lineage(
        context,
        None,
        None,
        None,
    )

    assert result["valid"] is True

    print("All artifact lineage tests passed.")


if __name__ == "__main__":
    run_tests()
