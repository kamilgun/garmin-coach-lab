# Garmin Coach Lab — Artifact Contracts and Version Standard

## Purpose

An artifact contract defines the promise between a producer and its consumers:

- which fields exist
- which fields are required
- which types are allowed
- which values are valid
- what the fields mean
- which cross-field invariants must hold
- which schema version is being used

A JSON file being syntactically valid is not enough. It must also satisfy the business contract expected by downstream stages.

## Artifact contracts are not pipeline run logs

The current pipeline prints execution progress to the console and writes generated artifacts to disk.

The artifacts contain timestamps and engine/planner metadata, but the project does not yet create a central run manifest containing:

- run id
- pipeline start and end time
- step-level success or failure
- complete artifact list
- input/output fingerprints
- retry information

A future artifact such as `data/pipeline_run.json` may provide this observability. That is separate from schema and contract validation.

## Current contract scope

Phase 8.1C introduces producer-side validation for:

| Artifact | Schema | Role |
|---|---:|---|
| `session_selection.json` | `1.0` | Selection and prescription contract |
| `weekly_plan.json` | `1.0` | Rolling seven-day execution contract |

The validators allow unknown additional fields. They are strict about stable core fields and invariants.

This avoids blocking additive metadata while still detecting breaking or semantically invalid output.

## Implementation choice

The first implementation is dependency-free and uses explicit Python validators.

Reasons:

- no new runtime dependency
- minimal risk to the working local pipeline
- clear error paths
- easy integration into the current dictionary-based code
- simple migration path to Pydantic later

A future Pydantic migration may replace the implementation without changing the documented contract.

## Validation boundary

```text
Coach Context
→ Candidate Builder
→ Session Selection
→ validate_session_selection_v1()
→ Scheduler
→ Weekly Plan
→ validate_weekly_plan_v1()
→ atomic JSON writes
```

Invalid artifacts fail before they are written by `build_weekly_plan.py`.

## Session Selection v1 invariants

- `schema_version` must be `1.0`
- status must be one of:
  - `ready`
  - `no_session_selected`
  - `no_structured_training`
- `session_count` must equal the number of sessions
- selected standalone sessions must not exceed `max_sessions`
- each session id must be unique
- each selected session must still have `scheduling.status = not_scheduled`
- duration must satisfy `min <= target_min <= max`
- total session duration must include add-on duration
- total maximum duration must not exceed the planning limit
- pace and distance guidance, when available, must be non-binding
- `selected_candidate_ids` must match selected main and add-on candidates
- capacity summary values must agree with selected sessions and planning limits

## Weekly Plan v1 invariants

- `schema_version` must be `1.0`
- the horizon must be an inclusive rolling seven-day window
- the end date must equal the start date plus six days
- counts must match their corresponding lists
- scheduled standalone dates must be unique
- scheduled dates must fall inside the horizon
- the stored weekday must match the scheduled date
- add-ons must inherit the main session date
- `ready` requires at least one scheduled session and no unscheduled session
- `partially_scheduled` requires both scheduled and unscheduled sessions
- `unscheduled` requires no scheduled sessions and at least one unscheduled session
- `no_sessions` and `no_structured_training` require empty session lists
- schedule summary counts must match the final lists

## Version terminology

### `schema_version`

Version of the artifact structure and semantics.

Current format:

```text
major.minor
```

Increment the major version for breaking changes:

- remove a required field
- rename a required field
- change a field type
- change enum meaning
- change a cross-field invariant incompatibly

Increment the minor version for backward-compatible additions:

- add an optional field
- add optional metadata
- add a new non-breaking nested field

### `engine_version`

Version of Decision Engine business rules.

Examples:

- load threshold changes
- health-priority changes
- context override changes
- running/cycling decision-policy changes

Current Decision Engine version:

```text
0.6.0
```

### `planner_version`

Version of planning policy.

Examples:

- candidate ranking changes
- duration-policy changes
- add-on-policy changes
- scheduling-distribution changes
- alternative-date-policy changes

Current Planning Engine version:

```text
0.1.0
```

### `pipeline_version`

Version of orchestration and pipeline order.

Examples:

- adding or removing a pipeline stage
- changing stage order
- changing required preflight behavior

### Engine identity fields

These identify the implementation family rather than a semantic version:

```text
decision_engine = rule_based_with_context_signals_v2
planning_engine = rule_based_weekly_plan_v1
```

## Compatibility policy

Consumers of schema `1.x` may rely on all documented required fields and invariants.

Consumers must ignore unknown additional fields.

A producer must not emit a breaking shape under the same major schema version.

## Error behavior

Validation raises:

```text
ArtifactContractError
```

Example:

```text
weekly_plan contract violation at $.scheduled_count:
sessions listesi uzunluğuna eşit olmalı.
```

The error includes:

- artifact name
- exact JSON-style path
- violated rule

## Future contract order

After this first scope is stable:

1. `WeeklyPlanV1`
2. `SessionSelectionV1`
3. `CoachContextV2`
4. `ManualContextV2`
5. `ActivitySummaryV2`

The first two are implemented in this phase.
