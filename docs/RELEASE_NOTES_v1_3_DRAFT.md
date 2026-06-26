# DARWIN v1.3.0 Release Notes

Status: release prep is complete on `v1.3/planning` as
`darwin-sim 1.3.0`. No merge, tag, GitHub release, or package publication has
been performed by this release-prep step.

DARWIN v1.3 Sprints 1 through 6 add simulator-local rendezvous lifecycle and
retained stream-offer status transition modeling. It introduces retained
transition history, read-only lifecycle planning helpers, an explicit
lifecycle plan apply helper, scenario DSL coverage, scenarios `058` through
`060`, and detailed snapshot visibility for lifecycle plans, apply results,
and retained transition history.

This is symbolic simulator metadata flow only. It is not real networking, not
a network service, not production DDoS protection, not a firewall, not a
privacy or anonymity system, and not real cryptography or production E2EE.

## Sprint Summary

Sprint 1 added symbolic RegistryHub-local stream-offer lifecycle transition
history:

- `StreamOfferStatusTransition` and
  `StreamOfferStatusTransitionReason` models.
- `RegistryHub.stream_offer_status_transition_history`.
- Explicit make, record, query, and summarize helpers for retained transition
  history.
- An opt-in transition recording path on
  `update_held_stream_offer_status(...)` that leaves default behavior
  unchanged.
- Detailed snapshot visibility for copied transition summaries while compact
  `world.snapshot()` output remains unchanged.
- Documentation in `docs/STREAM_OFFER_LIFECYCLE_HISTORY_v1_3.md`.

Sprint 2 added deterministic read-only lifecycle planning helpers:

- `StreamOfferLifecyclePlan` for copied JSON-safe lifecycle planning metadata.
- `query_expired_held_stream_offers(...)` for active retained offers expired
  by an explicit simulator order.
- `plan_stream_offer_expiration(...)` for classifying expired, active,
  cleanup-candidate, and ignored retained offer IDs without mutating hub
  state.
- `summarize_stream_offer_lifecycle_plan(...)` for copied deterministic plan
  summaries.
- Documentation in `docs/STREAM_OFFER_LIFECYCLE_PLANNING_v1_3.md`.

Sprint 3 added explicit simulator-local lifecycle plan application:

- `StreamOfferLifecycleApplyResult` for copied JSON-safe application result
  metadata.
- `apply_stream_offer_lifecycle_plan(...)` for applying caller-provided
  lifecycle plans to eligible retained held offers.
- Eligible planned non-terminal expired offers are marked `expired`.
- Terminal, stale, and missing planned offers are reported deterministically.
- Held offers are not deleted.
- Transition recording uses the existing status update helper with reason
  `expired` by default and can be disabled with `record_transition=False`.
- Compact `world.snapshot()` output remains unchanged.

Sprint 4 added scenario DSL coverage and checked-in scenarios:

- `plan_stream_offer_expiration` as a read-only scenario action using explicit
  deterministic `checked_at`.
- `apply_stream_offer_lifecycle_plan` as an explicit scenario action using a
  prior action-result lifecycle plan or caller-provided lifecycle plan fields.
- `stream_offer_lifecycle_plan_contains` for lifecycle plan action results.
- `stream_offer_lifecycle_apply_result_contains` for apply result action
  results.
- `stream_offer_status_transition_contains` for retained transition history,
  with action-result fallback consistent with existing scenario assertions.
- Scenarios `058` through `060` for expiration planning, apply with retained
  transition recording, and apply without transition recording.

Sprint 5 hardened detailed snapshot/debug visibility:

- Retained `stream_offer_status_transition_history` remains visible under each
  detailed `RegistryHub` snapshot.
- Lifecycle plan action results are visible in detailed snapshots at top-level
  `stream_offer_lifecycle_plans`.
- Lifecycle apply action results are visible in detailed snapshots at
  top-level `stream_offer_lifecycle_apply_results`.
- Snapshot entries use existing copied JSON-safe `to_summary()` shapes and
  preserve deterministic action-result order.
- Focused tests cover detailed visibility, copied summaries, deterministic
  ordering, and unchanged compact `world.snapshot()` output.

Sprint 6 hardened release-candidate documentation and readiness checks:

- v1.3 roadmap, release notes, lifecycle history docs, and lifecycle
  planning/apply docs are included in documentation link/readiness checks.
- Scenario continuity checks cover checked-in scenarios from `001` through `060`.
- `docs/SCENARIO_INDEX.md` remains generated from deterministic scenario
  metadata.
- v1.3 docs summarize Sprints 1 through 5 and preserve simulator-local,
  symbolic caveats.

## Compatibility

- Existing mailbox delivery behavior remains unchanged.
- Existing encrypted delivery behavior remains unchanged.
- Existing TrafficHub routing behavior remains unchanged.
- Existing alias behavior remains unchanged.
- Existing identity and canonical identity behavior remains unchanged.
- Existing v1.2 stream offer, rendezvous poll, lane admission, retained
  history, snapshot, and scenario behavior remains unchanged outside the
  explicit v1.3 lifecycle helpers.
- Compact `world.snapshot()` output remains unchanged.
- The checked-in scenario set is expected to remain contiguous from `001`
  through `060`.
- The prepared package and CLI version are `darwin-sim 1.3.0`.
- No package publication was performed.

## Scenario Coverage

v1.3 scenarios:

- `scenarios/058_stream_offer_lifecycle_expiration_plan.yaml`
- `scenarios/059_stream_offer_lifecycle_apply_records_transition.yaml`
- `scenarios/060_stream_offer_lifecycle_apply_without_transition.yaml`

These scenarios validate simulator-local stream-offer lifecycle planning,
explicit lifecycle plan application, retained transition history, apply
results, and detailed snapshot visibility. They do not deliver messages,
change TrafficHub routes, open sockets, perform DNS lookup, contact external
services, generate keys, encrypt payloads, enforce production security, or
change compact `world.snapshot()` output.

## Current Limitations

- Held stream offers and retained transition histories are in-memory and
  RegistryHub-local.
- Lifecycle planning is read-only by default and only uses explicit simulator
  order values supplied by callers.
- Lifecycle apply is explicit, caller-driven, and only mutates eligible
  planned held offer statuses.
- Lifecycle apply does not delete held offers.
- Retained lifecycle transition histories are simulator audit metadata, not
  production logs, compliance evidence, or delivery records.
- Detailed snapshots may expose modeled metadata such as offer IDs, hub IDs,
  statuses, lifecycle reasons, actor IDs, request IDs, checked-at values, and
  JSON-safe scenario metadata.

## Non-Goals

v1.3 does not add:

- real networking;
- sockets;
- HTTP or WebSocket behavior;
- DNS lookup;
- registrar integration;
- public CA behavior;
- external services;
- live polling loops;
- durable queues;
- automatic cleanup workers;
- retry loops;
- live timers;
- live clocks;
- production DDoS guarantees;
- production firewall guarantees;
- production privacy guarantees;
- production anonymity guarantees;
- real cryptography;
- key generation;
- private key storage;
- encryption or decryption;
- production E2EE;
- delivery enforcement;
- mailbox delivery behavior changes;
- encrypted delivery behavior changes;
- TrafficHub routing changes;
- compact snapshot changes;
- canonical identity rewrites;
- merge to `main`;
- release tag creation;
- GitHub release publication;
- package publication;
- version bumps beyond `1.3.0`.

## Release Readiness

The v1.3.0 release-prep state is complete when full validation passes on
`v1.3/planning`: `python -m ruff check .`, `python -m pytest`,
`python scripts/run_all_scenarios.py` for scenarios `001` through `060`, and
`python -m darwin.cli.main --version` reporting `darwin-sim 1.3.0`.

No merge, tag, GitHub release, or package publication has been performed by
this release-prep step.
