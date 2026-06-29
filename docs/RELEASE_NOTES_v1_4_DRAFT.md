# DARWIN v1.4.0 Draft Release Notes

Status: planning draft only. DARWIN v1.4.0 is unreleased, untagged, and not
merged to `main`. The latest released version remains `darwin-sim 1.3.0`.

Sprint 1 through Sprint 4 implementation work has started on the v1.4 planning
branch. These notes remain draft release-note material for a possible
simulator-first line around lifecycle policy explanation and stream-offer audit
summaries.

This draft is symbolic simulator planning only. It is not real networking, not
a network service, not production DDoS protection, not a firewall, not a
privacy or anonymity system, not DNS, not an external service, and not real
cryptography or production E2EE.

## Candidate Theme

Lifecycle policy explanation and stream-offer audit summaries.

Possible future slices may include:

- Read-only explanation helpers for stream-offer lifecycle plans. Sprint 1 adds
  this helper surface on the planning branch.
- Read-only explanation helpers for lifecycle apply results. Sprint 1 adds this
  helper surface on the planning branch.
- Summarized lifecycle audit views grouped by hub, offer, status, reason, and
  optional explanation category. Sprint 2 adds this helper surface on the
  planning branch.
- Retained explanation records only if consistent with existing
  RegistryHub-local audit-history patterns. Sprint 3 adds this explicitly
  recorded helper surface on the planning branch.
- Scenario DSL coverage after helper and model behavior is stable. Sprint 4
  adds this coverage on the planning branch.
- Limited detailed snapshot visibility for retained explanation history.
- Release-readiness documentation after scenario coverage exists.

## Compatibility Expectations

Any future v1.4 implementation should preserve these expectations unless a
later roadmap explicitly changes them:

- Existing mailbox delivery behavior remains unchanged.
- Existing encrypted delivery behavior remains unchanged.
- Existing TrafficHub routing behavior remains unchanged.
- Existing alias, identity, stream-offer polling/admission, lifecycle
  planning, lifecycle apply, retained-history, snapshot, and scenario behavior
  remains unchanged outside explicitly scoped v1.4 helper surfaces.
- Compact `world.snapshot()` output remains unchanged unless a later approved
  sprint explicitly scopes otherwise.
- The latest released package and CLI version remain `darwin-sim 1.3.0`
  during planning.
- The latest released scenario set remains contiguous from `001` through
  `060`. The v1.4 planning branch now has checked-in scenarios through `063`.

## Current Limitations

- v1.4 is not released.
- Sprint 1 is limited to read-only lifecycle explanation helpers and docs.
- Sprint 2 is limited to read-only grouped lifecycle audit summary helpers and
  docs.
- Sprint 3 is limited to explicitly retained RegistryHub-local lifecycle
  explanation history and docs.
- v1.4 planning scenarios `061` through `063` exist for lifecycle
  explanations and audit summaries.
- No v1.4 version bump has been performed.
- No v1.4 release has been merged, tagged, published, or packaged.

## Draft Sprint 1 Note

Sprint 1 adds `StreamOfferLifecycleExplanation` plus read-only helpers for
explaining existing lifecycle plans and apply results. The helpers classify
plan entries and apply-result outcomes into compact deterministic metadata and
return copied JSON-safe summaries. They do not mutate held offers, apply plans,
record transitions, delete offers, change compact snapshots, trigger delivery,
change TrafficHub routing, contact networks, use DNS, call external services,
or add real cryptography.

## Draft Sprint 2 Note

Sprint 2 adds `StreamOfferLifecycleAuditSummary` plus read-only helpers for
grouping retained stream-offer lifecycle transition history by offer ID, target
status, and reason, with optional caller-provided lifecycle explanations grouped
by category and reason. The helpers return deterministic copied JSON-safe
diagnostic metadata. They do not mutate held offers, apply plans, record
history, retain explanations, delete offers, change compact snapshots, trigger
delivery, change TrafficHub routing, contact networks, use DNS, call external
services, or add real cryptography.

## Draft Sprint 3 Note

Sprint 3 adds `RegistryHub.stream_offer_lifecycle_explanation_history` plus
explicit record, query, and summary helpers for retained
`StreamOfferLifecycleExplanation` records. The helpers preserve deterministic
append ordering and copied JSON-safe summaries, and detailed snapshots include
copied retained explanation history while compact snapshots remain unchanged.
They do not auto-record explanations, mutate held offers, mutate lifecycle
plans or apply results, mutate transition history, delete offers, run cleanup,
schedule retries, trigger delivery, change TrafficHub routing, contact
networks, use DNS, call external services, or add real cryptography.

## Draft Sprint 4 Note

Sprint 4 adds scenario DSL coverage for lifecycle plan explanations,
apply-result explanations, explicit retained explanation recording, and grouped
lifecycle audit summaries. Scenarios `061` through `063` cover read-only plan
classification, explicit retained apply-result explanation history, and audit
summary grouping by offer, status, reason, and category. The DSL actions do not
change lifecycle plan/apply semantics, mutate held offers outside the existing
explicit apply action, mutate transition history, delete offers, change compact
snapshots, trigger delivery, change TrafficHub routing, contact networks, use
DNS, call external services, or add real cryptography.

## Non-Goals

v1.4 planning does not add:

- real networking;
- sockets;
- HTTP or WebSocket behavior;
- DNS lookup;
- registrar integration;
- public CA behavior;
- external services;
- live polling loops;
- automatic cleanup workers;
- retry loops;
- durable queues;
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
- compact snapshot changes unless explicitly scoped later;
- canonical identity rewrites;
- package publication;
- release assets;
- merge, tag, or GitHub release;
- version bumps beyond `1.3.0` during planning.

## Release Readiness

Release readiness has not started. A future release-prep pass should only
convert this draft to release-facing status after approved implementation
slices, scenario coverage, documentation checks, and full validation exist.

Planning validation should keep reporting `darwin-sim 1.3.0` until an explicit
future version-bump sprint changes package metadata.
