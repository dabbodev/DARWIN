# DARWIN v1.3 Release Notes Draft

Status: planning draft with Sprints 1 through 5 implemented on the v1.3
planning branch. v1.3 is unreleased. DARWIN v1.2.0 remains the latest released
version on `main` as `darwin-sim 1.2.0`. The annotated `v1.2.0` tag and GitHub
release exist:
https://github.com/dabbodev/DARWIN/releases/tag/v1.2.0. No package
publication was performed.

This file is a draft for future v1.3 release notes. It does not describe
released v1.3 behavior and should not be treated as a release announcement.

## Candidate Theme

Rendezvous lifecycle and retained stream-offer status transitions.

Future v1.3 work may explore small simulator-first slices around:

- symbolic stream-offer expiration and cleanup helpers;
- retained stream-offer status transition history;
- read-only query and summarize helpers for lifecycle audit metadata;
- scenario DSL coverage after helper behavior lands;
- release-readiness documentation after scenario coverage exists.

## Sprint 1 Draft Note

Sprint 1 adds symbolic RegistryHub-local stream-offer lifecycle transition
history:

- `StreamOfferStatusTransition` and
  `StreamOfferStatusTransitionReason` models.
- `RegistryHub.stream_offer_status_transition_history`.
- Explicit make, record, query, and summarize helpers for retained transition
  history.
- An opt-in transition recording path on `update_held_stream_offer_status(...)`
  that leaves default behavior unchanged.
- Detailed snapshot visibility for copied transition summaries while compact
  `world.snapshot()` output remains unchanged.
- Documentation in `docs/STREAM_OFFER_LIFECYCLE_HISTORY_v1_3.md`.

No scenario DSL actions or assertions were added in Sprint 1.

## Sprint 2 Draft Note

Sprint 2 adds deterministic read-only stream-offer lifecycle planning helpers:

- `StreamOfferLifecyclePlan` for copied JSON-safe lifecycle planning metadata.
- `query_expired_held_stream_offers(...)` for active retained offers expired by
  an explicit simulator order.
- `plan_stream_offer_expiration(...)` for classifying expired, active, cleanup
  candidate, and ignored retained offer IDs without mutating hub state.
- `summarize_stream_offer_lifecycle_plan(...)` for copied deterministic plan
  summaries.
- Documentation in `docs/STREAM_OFFER_LIFECYCLE_PLANNING_v1_3.md`.

No scenario DSL actions or assertions were added in Sprint 2. No apply helper
was added; lifecycle planning remains read-only by default.

## Sprint 3 Draft Note

Sprint 3 adds an explicit simulator-local lifecycle plan application helper:

- `StreamOfferLifecycleApplyResult` for copied JSON-safe application result
  metadata.
- `apply_stream_offer_lifecycle_plan(...)` for applying caller-provided
  lifecycle plans to eligible retained held offers.
- `summarize_stream_offer_lifecycle_apply_result(...)` for copied
  deterministic result summaries.
- Eligible planned non-terminal expired offers are marked `expired`.
- Terminal or stale planned offers are skipped deterministically.
- Missing planned offer IDs are reported deterministically.
- Held offers are not deleted.
- Transition recording is enabled by default through the existing status update
  helper with reason `expired`, and can be disabled with
  `record_transition=False`.
- Compact `world.snapshot()` output remains unchanged.

No scenario DSL actions or assertions were added in Sprint 3. No automatic
cleanup workers, retry loops, durable queues, live timers, delivery behavior,
TrafficHub routing, DNS, networking, external service, real cryptography, or
canonical identity behavior were added.

## Sprint 4 Draft Note

Sprint 4 adds scenario DSL coverage for the existing lifecycle planning and
explicit apply helpers:

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

Planning remains read-only. Apply mutates only eligible planned held offers
and never deletes held offers. No automatic cleanup workers, retry loops,
durable queues, live timers, live clocks, live polling, delivery behavior,
TrafficHub routing, DNS, networking, external services, real cryptography,
compact snapshot changes, or canonical identity behavior were added.

## Sprint 5 Draft Note

Sprint 5 hardens detailed snapshot/debug visibility for existing lifecycle
artifacts:

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

No compact snapshot changes, lifecycle behavior changes, automatic cleanup
workers, retry loops, durable queues, live timers, delivery behavior,
TrafficHub routing, DNS, networking, external services, real cryptography,
canonical identity behavior, version bump, package publication, merge, tag, or
release were added.

## Current Draft Scope

Any future v1.3 implementation should preserve:

- existing mailbox delivery behavior;
- existing encrypted delivery behavior;
- existing TrafficHub routing behavior;
- existing canonical identity behavior;
- existing v1.2 stream offer, rendezvous poll, lane admission, retained
  history, snapshot, and scenario behavior unless a later accepted sprint
  explicitly scopes a simulator-local change.

## Expected Compatibility Framing

The checked-in released scenario set remains expected to run contiguously from
`001` through `057`. The v1.3 planning-branch scenario set is now contiguous
from `001` through `060`.

The package and CLI version remain `darwin-sim 1.2.0` during planning.

## Non-Goals

v1.3 planning does not add:

- real networking;
- sockets;
- HTTP or WebSocket behavior;
- DNS lookup;
- registrar integration;
- public CA behavior;
- external services;
- live polling loops;
- durable queues;
- retry workers;
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
- canonical identity rewrites;
- package publication;
- version bumps beyond `1.2.0` during planning.

## Release Readiness

Not started. Before any future v1.3 release, this placeholder should be
replaced with a concrete implementation summary, scenario coverage, validation
results, compatibility notes, and final release status.
