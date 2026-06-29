# DARWIN v1.4 Stream Offer Lifecycle Explanations

Sprint 1 adds deterministic read-only explanation helpers for the v1.3
stream-offer lifecycle plan and apply-result models. Explanations are symbolic
simulator-local diagnostic metadata only. They make existing lifecycle helper
outputs easier to inspect in tests and docs without changing lifecycle
planning, lifecycle apply, delivery, routing, identity, networking, or
cryptography behavior.

This feature does not add delivery behavior, TrafficHub routing, DNS,
networking, external services, real cryptography, or production security
behavior.

## Purpose

Lifecycle explanations describe existing helper outputs:

- `StreamOfferLifecyclePlan`
- `StreamOfferLifecycleApplyResult`

The explanation model is `StreamOfferLifecycleExplanation`. Each record
contains:

- `hub_id`
- `offer_id`
- `category`
- `reason`
- `status`
- optional `checked_at`
- optional `source`
- optional JSON-safe `details`

Explanation categories are intentionally small:

- `expired`
- `active`
- `applied`
- `skipped`
- `missing`
- `terminal`

Reasons are simulator labels for why the explanation record exists. They are
not production policy decisions, enforcement outcomes, compliance evidence,
network logs, security telemetry, or privacy-preserving traces.

## Helpers

Sprint 1 adds:

- `explain_stream_offer_lifecycle_plan(plan)`
- `explain_stream_offer_lifecycle_apply_result(result)`
- `summarize_stream_offer_lifecycle_explanations(explanations)`

`explain_stream_offer_lifecycle_plan(...)` reads only a provided lifecycle
plan. It explains:

- expired plan entries as `expired`;
- cleanup-only candidates as `terminal` cleanup candidates;
- active plan entries as `active`;
- ignored plan entries as skipped/ignored diagnostics.

Expired offers can also be cleanup candidates in the existing plan model. The
explanation keeps one record per offer ID and marks that overlap in copied
`details`.

`explain_stream_offer_lifecycle_apply_result(...)` reads only a provided apply
result. It explains:

- `applied_offer_ids` as `applied`;
- `skipped_offer_ids` as `skipped`;
- `missing_offer_ids` as `missing`.

`summarize_stream_offer_lifecycle_explanations(...)` returns copied JSON-safe
summaries in the provided order. Mutating a summary does not mutate the
explanation records, a lifecycle plan, an apply result, held offers, or any
RegistryHub state.

## Read-Only Boundaries

Explanations do not make policy decisions by themselves. They describe
classification and apply-result metadata that already exists.

Explanation helpers do not:

- mutate held offers;
- apply lifecycle plans;
- delete offers;
- record transitions;
- run cleanup;
- schedule retries;
- trigger delivery;
- create delivery results;
- change message inboxes;
- change TrafficHub routing;
- change compact `world.snapshot()` output.

They do not read wall-clock time, use live clocks, start timers, poll in the
background, or require scenario context.

## Snapshot Visibility

Sprint 5 exposes recent explanation action results in detailed world
snapshots:

```text
stream_offer_lifecycle_explanations
```

The snapshot entries are copied `StreamOfferLifecycleExplanation.to_summary()`
records in action-result order. Mutating detailed snapshot output does not
mutate explanation records or RegistryHub state. Compact `world.snapshot()`
output remains unchanged and does not include explanation action results.

## Non-Goals

Sprint 1 does not add:

- background workers;
- automatic cleanup workers or cleanup daemons;
- retry loops;
- durable queues;
- live timers;
- live clocks;
- live polling;
- sockets;
- HTTP or WebSocket behavior;
- network logs;
- DNS lookup;
- registrar integration;
- public CA behavior;
- external services;
- firewall or DDoS systems;
- production privacy or anonymity guarantees;
- production security infrastructure;
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
- scenario DSL actions or assertions;
- retained explanation history;
- package publication;
- release assets;
- merge, tag, GitHub release, or version bump beyond `1.4.0`.
