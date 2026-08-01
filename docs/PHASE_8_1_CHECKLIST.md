# Phase 8.1 — Consolidation Checklist

## Goal

Stabilize and document the Phase 8 architecture before beginning the Weekly Plan Product UI.

## Workstream

### 8.1A — System inventory and project tree

- [ ] Generate `docs/PROJECT_INVENTORY.md`
- [ ] Review tracked/private/generated files
- [ ] Identify duplicate, obsolete, or exploratory files
- [ ] Confirm source, serving, debug, and presentation artifact roles
- [ ] Freeze the current Phase 8 project tree

**Exit artifact:** `docs/PROJECT_INVENTORY.md`

### 8.1B — README Phase 8 update

- [ ] Replace the pre-planner architecture
- [ ] Document Decision Engine vs Planning Engine
- [ ] Add the full artifact lineage
- [ ] Add current pipeline commands
- [ ] Add current test commands
- [ ] Add one real anonymized weekly-plan example
- [ ] Update roadmap to Phase 9–13

**Exit artifact:** updated `README.md`

### 8.1C — Artifact contracts and version standard

- [ ] Define shared artifact metadata
- [ ] Document schema/version ownership
- [ ] Add validation for `WeeklyPlanV1`
- [ ] Add validation for `SessionSelectionV1`
- [ ] Decide whether to introduce Pydantic now or incrementally

**Exit artifact:** contract document plus initial validation models

### 8.1D — Test consolidation

- [ ] Add one test entry point
- [ ] Group unit, integration, and scenario tests
- [ ] Keep existing runners compatible during migration
- [ ] Produce one summary result

**Exit criterion:** one command runs the complete deterministic test suite

### 8.1E — Reporting polish

- [ ] Separate history, decision, and plan sections
- [ ] Remove semantic reason duplication
- [ ] Keep technical explainability
- [ ] Preserve weekly-plan propagation and fallbacks

**Exit artifact:** simplified `weekly_review.md`

### 8.1F — Consolidation verification

- [ ] Compile check
- [ ] Context scenario matrix
- [ ] Weekly-plan scenario matrix
- [ ] Propagation tests
- [ ] Full local deterministic pipeline
- [ ] Privacy/tracked-file check

**Exit criterion:** Phase 8.1 complete and ready for Phase 9 UI

## Scope Guard

Not part of consolidation:

- New workout types
- Interval or tempo planning
- Plan execution tracking
- Feedback-based adaptation
- Garmin workout write-back
- Cloud or multi-user deployment
