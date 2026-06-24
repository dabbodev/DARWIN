# DARWIN v1.3 Roadmap Draft: Rendezvous Lifecycle and Retained Stream-Offer Status Transitions

Status: planning branch with Sprints 1 through 5 implemented. v1.3 is
unreleased.
DARWIN v1.2.0 remains the latest released version on `main` as
`darwin-sim 1.2.0`. The annotated `v1.2.0` tag and GitHub release exist:
https://github.com/dabbodev/DARWIN/releases/tag/v1.2.0. No package
publication was performed.

Recommended candidate theme: Rendezvous lifecycle and retained stream-offer
status transitions.

This roadmap is a seed for future planning. It does not lock implementation
scope, commit to a release date, or authorize feature work. Any later v1.3
sprint should remain simulator-first and symbolic unless explicitly scoped
otherwise.

v1.3 should not become production networking, a real DDoS protection system,
a firewall product, a privacy or anonymity system, DNS, registrar
infrastructure, external service discovery, a secure messaging protocol, or a
real cryptography project.

## Core Concept

Explore a small, simulator-local lifecycle layer for stream offers retained by
rendezvous and RegistryHub-local state.

v1.2 introduced stream offer records, held offer queues, private polling
descent helpers, symbolic lane admission policy, retained poll/admission
histories, scenarios, and detailed snapshot visibility. A possible v1.3 line
could focus on making retained stream-offer lifecycle movement easier to
inspect without changing delivery behavior, TrafficHub routing, canonical
identity, networking, or cryptography.

The primary planning question is:

```text
Can a retained stream offer move through explicit symbolic lifecycle states in
a deterministic, inspectable way without becoming delivery enforcement,
networking, durable queueing, or production security behavior?
```

## Planning Boundaries

Candidate in scope:

- Simulator-local stream-offer lifecycle status helpers.
- Symbolic expiration and cleanup helpers over retained offers.
- Retained stream-offer status transition history.
- Read-only query and summarize helpers for lifecycle audit metadata.
- Scenario DSL coverage only after helper behavior is stable.
- Documentation and release-readiness checks after scenario coverage exists.

Out of scope:

- Real networking, sockets, HTTP, WebSocket, DNS, or service discovery.
- Live polling loops, background workers, durable queues, retry services, or
  scheduler behavior.
- Production DDoS protection, firewall guarantees, abuse mitigation claims, or
  delivery guarantees.
- Privacy, anonymity, metadata-hiding, or traffic-analysis guarantees.
- Registrar integration, public CA behavior, or production identity proof.
- Real cryptography, key generation, private key storage, production E2EE, or
  secure messaging.
- TrafficHub routing changes.
- Canonical identity rewrites.
- Version bump beyond `1.2.0` during planning.
- Package publication.

## Candidate Concepts

Stream-offer lifecycle status:

- A simulator-local label describing where a retained offer sits in its
  explicit lifecycle.
- Possible future labels might describe held, discoverable, admitted,
  denied, expired, cleaned up, superseded, or withdrawn states.
- The exact vocabulary should be chosen during implementation planning, not
  locked by this roadmap draft.

Symbolic expiration:

- An explicit helper-level operation that marks or selects retained stream
  offers based on simulated time or scenario-provided metadata.
- It should not be a wall-clock timer, background worker, retry loop, durable
  queue, or live service.

Cleanup helper:

- A deterministic simulator helper that removes, marks, or summarizes retained
  offers according to explicit caller-provided criteria.
- It should not imply production retention policy, compliance deletion,
  guaranteed delivery cleanup, or external storage behavior.

Status transition history:

- Compact retained audit metadata for explicit stream-offer status changes.
- It should remain RegistryHub-local simulator state, not a production log or
  compliance audit trail.

Lifecycle audit query:

- Read-only filters and summaries over retained lifecycle metadata.
- Queries should preserve deterministic append order and expose only
  JSON-safe simulator summaries.

## Sprint 1: Retained Lifecycle Transition History

Status: implemented on the v1.3 planning branch.

Goal: add the smallest useful RegistryHub-local history for explicit symbolic
stream-offer status transitions without changing delivery, routing, polling,
admission, scenario DSL, or compact snapshot behavior.

Implemented work:

- Review existing `StreamOfferStatus` behavior and v1.2 retained offer helper
  boundaries.
- Add `StreamOfferStatusTransition` and
  `StreamOfferStatusTransitionReason` models with a small symbolic reason
  vocabulary.
- Retain transition records on
  `RegistryHub.stream_offer_status_transition_history`.
- Add explicit make, record, query, and summarize helpers for lifecycle
  history.
- Add an opt-in `update_held_stream_offer_status(..., record_transition=True)`
  path while preserving default behavior.
- Document Sprint 1 behavior in
  `docs/STREAM_OFFER_LIFECYCLE_HISTORY_v1_3.md`.

Acceptance targets:

- Existing v1.2 stream offer, poll, admission, history, snapshot, and scenario
  behavior remains unchanged except detailed snapshots now include copied
  transition-history summaries when records exist.
- Compact `world.snapshot()` output remains unchanged.
- No real networking, DNS lookup, external services, delivery enforcement,
  TrafficHub routing changes, canonical identity rewrites, real cryptography,
  or version bump is added.

## Sprint 2: Symbolic Expiration and Cleanup Planning Helpers

Status: implemented on the v1.3 planning branch.

Goal: add explicit read-only helper calls for symbolic stream-offer expiration
and cleanup planning.

Implemented work:

- Add `StreamOfferLifecyclePlan` for copied JSON-safe lifecycle planning
  metadata.
- Add `query_expired_held_stream_offers(...)` for active retained offers
  expired by an explicit simulator order.
- Add `plan_stream_offer_expiration(...)` for deterministic read-only
  expiration and cleanup-candidate classification.
- Add `summarize_stream_offer_lifecycle_plan(...)` for copied plan summaries.
- Document Sprint 2 behavior in
  `docs/STREAM_OFFER_LIFECYCLE_PLANNING_v1_3.md`.

Acceptance targets:

- Expiration and cleanup are explicit simulator helper calls, not live timers,
  background workers, durable queues, or retry services.
- Helpers do not deliver messages, enforce production policy, mutate
  TrafficHub routes, perform DNS lookup, or contact external services.
- Helpers do not remove offers, change statuses, or record transitions by
  default.
- Compact `world.snapshot()` output remains unchanged.

## Sprint 3: Explicit Lifecycle Plan Application Helper

Status: implemented on the v1.3 planning branch.

Goal: add an explicit opt-in helper for applying caller-provided lifecycle
plans without adding automatic cleanup or delivery behavior.

Implemented work:

- Add `StreamOfferLifecycleApplyResult` for copied JSON-safe apply result
  metadata.
- Add `apply_stream_offer_lifecycle_plan(...)` for explicit simulator-local
  mutation of eligible planned expired offers.
- Recheck plan eligibility against the explicit `plan.checked_at` simulator
  order before applying.
- Report skipped and missing offer IDs deterministically.
- Preserve retained held offers; no deletion is performed.
- Integrate optional transition recording using the existing status update
  helper with reason `expired`.
- Add `summarize_stream_offer_lifecycle_apply_result(...)`.
- Document Sprint 3 behavior in
  `docs/STREAM_OFFER_LIFECYCLE_PLANNING_v1_3.md`.

Acceptance targets:

- Lifecycle planning remains read-only until the explicit apply helper is
  called.
- Apply only mutates eligible offers listed in the provided plan.
- Terminal offers remain unchanged and missing IDs are reported.
- Transition history remains simulator audit metadata only.
- Retention does not become a production audit log, compliance store, delivery
  queue, cleanup daemon, timer, retry loop, or security guarantee.
- Compact `world.snapshot()` output remains unchanged.

## Sprint 4: Scenario DSL Coverage

Status: implemented on the v1.3 planning branch.

Goal: expose stable lifecycle helpers through scenario YAML after helper
behavior and summaries are covered by focused tests.

Implemented work:

- Add `plan_stream_offer_expiration` as a read-only scenario action requiring
  explicit deterministic `checked_at`.
- Add `apply_stream_offer_lifecycle_plan` as an explicit scenario action that
  uses either a prior action-result lifecycle plan or a caller-provided plan.
- Add `stream_offer_lifecycle_plan_contains`,
  `stream_offer_lifecycle_apply_result_contains`, and
  `stream_offer_status_transition_contains` assertions.
- Prefer retained transition history for transition assertions, with
  action-result fallback matching existing scenario assertion patterns.
- Add scenarios `058` through `060` for planning, apply with transition
  recording, and apply without transition recording.
- Update scenario validation, scenario index coverage, and DSL docs.

Acceptance targets:

- Existing scenarios `001` through `057` continue to pass unchanged, and the
  planning-branch scenario set is contiguous through `060`.
- New scenarios remain symbolic and make no networking, delivery, DNS,
  cryptography, TrafficHub, or canonical identity claims.
- Planning remains read-only; held offers are mutated only when a scenario
  explicitly runs the apply action.
- Held stream offers are not deleted.
- Compact `world.snapshot()` output remains unchanged.

## Sprint 5: Detailed Snapshot Lifecycle Artifact Visibility

Status: implemented on the v1.3 planning branch.

Goal: harden detailed snapshot/debug visibility for existing stream-offer
lifecycle artifacts without changing compact snapshots or adding lifecycle
behavior.

Implemented work:

- Confirm retained lifecycle transition history is exposed under each detailed
  `RegistryHub` snapshot.
- Add top-level detailed snapshot action-result summaries for
  `stream_offer_lifecycle_plans` and
  `stream_offer_lifecycle_apply_results`.
- Add focused tests for detailed lifecycle artifact visibility, copied
  summaries, deterministic action-result ordering, and unchanged compact
  snapshots.
- Update lifecycle planning/history docs, scenario DSL docs, and draft release
  notes.

Acceptance targets:

- Compact `world.snapshot()` output remains unchanged.
- Snapshot additions are copied JSON-safe summaries and preserve deterministic
  action-result order.
- No new lifecycle mutation behavior, cleanup worker, retry loop, durable
  queue, live timer, delivery behavior, networking, DNS, TrafficHub routing,
  canonical identity rewrite, version bump, or package publication is added.

## Recommended First Planning Step

Start by auditing v1.2 stream offer statuses and retained histories before
adding any feature code. The safest next decision is whether v1.3 needs a new
transition record shape or can reuse existing retained stream-offer and
admission/poll summaries.

## Intentionally Deferred Work

- Real networking, sockets, HTTP/WebSocket behavior, DNS lookup, and external
  services.
- Live polling, durable queues, retry workers, background cleanup services, or
  wall-clock schedulers.
- Production DDoS protection, firewall guarantees, abuse mitigation, or
  delivery guarantees.
- Privacy, anonymity, metadata-hiding, or traffic-analysis guarantees.
- Registrar integration, public CA behavior, and production identity proof.
- Real cryptography, key generation, private key storage, production E2EE, and
  secure messaging protocols.
- TrafficHub routing changes.
- Canonical identity rewrites.
- Package publication or version bump beyond `1.2.0` during planning.
