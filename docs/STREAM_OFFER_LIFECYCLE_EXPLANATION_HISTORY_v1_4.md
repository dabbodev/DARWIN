# DARWIN v1.4 Stream Offer Lifecycle Explanation History

Sprint 3 adds explicitly retained RegistryHub-local history for stream-offer
lifecycle explanations. Explanation history is symbolic simulator-local
diagnostic and audit metadata only. It exists to make caller-selected
`StreamOfferLifecycleExplanation` records inspectable in tests, docs, and
detailed snapshots without changing lifecycle planning, lifecycle apply,
delivery, routing, identity, networking, or cryptography behavior.

This feature does not add delivery behavior, TrafficHub routing, DNS,
networking, external services, real cryptography, or production security
behavior.

## Purpose

Lifecycle explanation records are retained on:

```text
RegistryHub.stream_offer_lifecycle_explanation_history
```

The retained list defaults to empty and preserves deterministic append order.
It contains existing immutable `StreamOfferLifecycleExplanation` records:

- `hub_id`
- `offer_id`
- `category`
- `reason`
- `status`
- optional `checked_at`
- optional `source`
- optional JSON-safe `details`

Explanation history is local to the in-memory simulator RegistryHub. It is not
durable evidence, production logging, compliance telemetry, security telemetry,
network logging, or a privacy-preserving trace.

## Recording Helpers

Recording is explicit:

- `record_stream_offer_lifecycle_explanation(registry_hub, explanation)`
- `record_stream_offer_lifecycle_explanations(registry_hub, explanations)`

The existing explanation helpers still return unretained records unless callers
explicitly pass those records to a recording helper. There is no automatic
recording from lifecycle planning, lifecycle apply, explanation generation,
audit summaries, scenario execution, cleanup, polling, delivery, or snapshots.

## Query And Summary Helpers

`query_stream_offer_lifecycle_explanations(...)` reads only
`registry_hub.stream_offer_lifecycle_explanation_history`. Filters are additive
and preserve append order:

- `hub_id`
- `offer_id`
- `category`
- `reason`
- `status`
- `source`

`summarize_stream_offer_lifecycle_explanation_history(registry_hub)` returns
copied JSON-safe summaries in append order. Mutating a copied summary does not
mutate retained history, explanation records, held offers, lifecycle plans,
apply results, transition history, or any TrafficHub state.

## Snapshot Visibility

Detailed world snapshots include copied explanation summaries under each
RegistryHub:

```text
registry_hubs.<hub_id>.stream_offer_lifecycle_explanation_history
```

Compact `world.snapshot()` output remains unchanged and does not include
explanation history.

## Read-Only Boundaries

Explanation history does not make policy decisions by itself. It records
caller-provided explanation metadata only.

Explanation history does not:

- mutate held offers;
- mutate lifecycle plans;
- mutate lifecycle apply results;
- mutate retained transition history;
- apply lifecycle plans;
- delete offers;
- run cleanup;
- schedule retries;
- trigger delivery;
- create delivery results;
- change message inboxes;
- change TrafficHub routing;
- change compact `world.snapshot()` output.

## Non-Goals

Sprint 3 does not add:

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
- package publication;
- release assets;
- merge, tag, GitHub release, or version bump beyond `1.3.0`.

