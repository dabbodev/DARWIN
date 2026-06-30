# DARWIN v1.4.0 Draft Release Notes

Status: release-prep candidate on `v1.4/planning`. DARWIN v1.4.0 is
unreleased, untagged, and not merged to `main`. The branch package and CLI
version are `darwin-sim 1.4.0`; the latest published release remains
`darwin-sim 1.3.0` until a later explicit merge, tag, GitHub release, or
publication step.

Sprint 1 through Sprint 6 work exists on the v1.4 planning branch. These
release notes summarize the release-facing scope for lifecycle policy
explanation and stream-offer audit summaries. No package publication has been
performed, and no release assets have been uploaded.

This release-prep candidate is symbolic simulator metadata flow only. It is
not real networking, not a network service, not production DDoS protection,
not a firewall, not a privacy or anonymity system, not DNS, not an external
service, and not real cryptography or production E2EE.

## Release Theme

Lifecycle policy explanation and stream-offer audit summaries.

v1.4 adds:

- Read-only explanation helpers for stream-offer lifecycle plans.
- Read-only explanation helpers for lifecycle apply results.
- Grouped lifecycle audit summaries over retained stream-offer lifecycle
  transition history, grouped by hub, offer, status, reason, and optional
  explanation category.
- Retained RegistryHub-local lifecycle explanation history through explicit
  recording helpers.
- Scenario DSL coverage for lifecycle explanations, retained explanation
  history, and grouped lifecycle audit summaries.
- Scenarios `061` through `063`.
- Detailed snapshot/debug visibility for retained explanation history,
  explanation action results, and audit summary action results.
- Release-candidate hardening and documentation/readiness coverage through
  checked-in scenarios through `063`.
- v1.4 release prep sets the package and CLI version to `darwin-sim 1.4.0`.

## Compatibility

- Existing mailbox delivery behavior remains unchanged.
- Existing encrypted delivery behavior remains unchanged.
- Existing TrafficHub routing behavior remains unchanged.
- Existing alias, identity, stream-offer polling/admission, lifecycle
  planning, lifecycle apply, retained-history, snapshot, and scenario behavior
  remains unchanged outside explicitly scoped v1.4 helper surfaces.
- Existing retained lifecycle transition history remains unchanged.
- Compact `world.snapshot()` output remains unchanged.
- The branch scenario set is contiguous from `001` through `063`.
- Scenarios `061` through `063` cover v1.4 lifecycle explanation and audit
  summary behavior.
- No merge, tag, GitHub release, package publication, or release-asset upload
  has been performed.

## Sprint Summary

Sprint 1 adds `StreamOfferLifecycleExplanation` plus read-only helpers for
explaining existing lifecycle plans and apply results. The helpers classify
plan entries and apply-result outcomes into compact deterministic metadata and
return copied JSON-safe summaries. They do not mutate held offers, apply
plans, record transitions, delete offers, change compact snapshots, trigger
delivery, change TrafficHub routing, contact networks, use DNS, call external
services, or add real cryptography.

Sprint 2 adds `StreamOfferLifecycleAuditSummary` plus read-only helpers for
grouping retained stream-offer lifecycle transition history by offer ID, target
status, and reason, with optional caller-provided lifecycle explanations
grouped by category and reason. The helpers return deterministic copied
JSON-safe diagnostic metadata. They do not mutate held offers, apply plans,
record history, retain explanations, delete offers, change compact snapshots,
trigger delivery, change TrafficHub routing, contact networks, use DNS, call
external services, or add real cryptography.

Sprint 3 adds `RegistryHub.stream_offer_lifecycle_explanation_history` plus
explicit record, query, and summary helpers for retained
`StreamOfferLifecycleExplanation` records. The helpers preserve deterministic
append ordering and copied JSON-safe summaries, and detailed snapshots include
copied retained explanation history while compact snapshots remain unchanged.
They do not auto-record explanations, mutate held offers, mutate lifecycle
plans or apply results, mutate transition history, delete offers, run cleanup,
schedule retries, trigger delivery, change TrafficHub routing, contact
networks, use DNS, call external services, or add real cryptography.

Sprint 4 adds scenario DSL coverage for lifecycle plan explanations,
apply-result explanations, explicit retained explanation recording, and
grouped lifecycle audit summaries. Scenarios `061` through `063` cover
read-only plan classification, explicit retained apply-result explanation
history, and audit summary grouping by offer, status, reason, and category.
The DSL actions do not change lifecycle plan/apply semantics, mutate held
offers outside the existing explicit apply action, mutate transition history,
delete offers, change compact snapshots, trigger delivery, change TrafficHub
routing, contact networks, use DNS, call external services, or add real
cryptography.

Sprint 5 hardens detailed snapshot/debug visibility for existing v1.4
explanation and audit artifacts. Detailed snapshots include retained
explanation history under
`registry_hubs.<hub_id>.stream_offer_lifecycle_explanation_history`, recent
explanation action results under `stream_offer_lifecycle_explanations`, and
recent audit summary action results under
`stream_offer_lifecycle_audit_summaries`. Snapshot entries use copied
JSON-safe summary shapes and preserve deterministic ordering. Compact
`world.snapshot()` output remains unchanged.

Sprint 6 hardens release-readiness and documentation checks for the v1.4
planning branch. It ensures the v1.4 roadmap, draft release notes, lifecycle
explanation docs, audit summary docs, and retained explanation history docs
are included in documentation link/readiness coverage; confirms checked-in
scenario coverage remains contiguous from `001` through `063`; and keeps
`docs/SCENARIO_INDEX.md` generated from deterministic scenario metadata. This
sprint is release-candidate hardening and documentation audit only.

## Scenario Coverage

v1.4 scenarios:

- `scenarios/061_stream_offer_lifecycle_plan_explained.yaml`
- `scenarios/062_stream_offer_lifecycle_apply_explanation_retained.yaml`
- `scenarios/063_stream_offer_lifecycle_audit_summary.yaml`

These scenarios validate simulator-local lifecycle plan explanations,
apply-result explanations, explicit retained explanation history, audit
summary grouping, and detailed snapshot visibility. They do not deliver
messages, change TrafficHub routes, open sockets, perform DNS lookup, contact
external services, generate keys, encrypt payloads, enforce production
security, or change compact `world.snapshot()` output.

## Current Limitations

- v1.4.0 is prepared on `v1.4/planning` but has not been merged, tagged,
  released on GitHub, published as a package, or shipped with release assets.
- Lifecycle explanations are read-only summaries over existing lifecycle plan
  and apply-result metadata.
- Lifecycle audit summaries are read-only grouped summaries over retained
  transition history and optional caller-provided explanations.
- Retained explanation history is RegistryHub-local, in-memory, and recorded
  only through explicit helper or scenario action calls.
- Detailed snapshots may expose modeled metadata such as offer IDs, hub IDs,
  statuses, lifecycle reasons, actor IDs, request IDs, checked-at values,
  explanation categories, and JSON-safe scenario metadata.

## Non-Goals

v1.4 does not add:

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
- lifecycle mutation behavior;
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
- delivery behavior changes;
- mailbox delivery behavior changes;
- encrypted delivery behavior changes;
- TrafficHub routing changes;
- compact snapshot changes;
- canonical identity rewrites;
- package publication;
- release assets;
- merge, tag, or GitHub release;
- version bumps beyond `1.4.0`.

## Release Readiness

Release-prep validation for v1.4.0 is expected to pass
`python -m ruff check .`, `python -m pytest` with 836 tests,
`python scripts/run_all_scenarios.py` for scenarios `001` through `063`, and
`python -m darwin.cli.main --version` reporting `darwin-sim 1.4.0`.

The v1.4.0 branch remains ready for a later explicit merge, annotated tag,
GitHub release, and package-publication decision. Those steps are outside this
release-prep task.
