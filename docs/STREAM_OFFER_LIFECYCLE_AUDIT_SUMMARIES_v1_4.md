# DARWIN v1.4 Stream Offer Lifecycle Audit Summaries

Sprint 2 adds deterministic read-only grouped summaries for retained
stream-offer lifecycle audit metadata. Audit summaries are symbolic
simulator-local diagnostic metadata only. They make existing
`RegistryHub.stream_offer_status_transition_history` records easier to inspect
without changing lifecycle planning, lifecycle apply, delivery, routing,
identity, networking, or cryptography behavior.

This feature does not add delivery behavior, TrafficHub routing, DNS,
networking, external services, real cryptography, or production security
behavior.

## Purpose

Lifecycle audit summaries group existing metadata from:

- retained `StreamOfferStatusTransition` records; and
- optional caller-provided `StreamOfferLifecycleExplanation` records.

The summary model is `StreamOfferLifecycleAuditSummary`. Each record contains:

- `hub_id`;
- `total_transitions`;
- `by_offer_id`;
- `by_status`;
- `by_reason`;
- `by_category`;
- `explanation_count`;
- optional JSON-safe `metadata`.

The grouping maps are deterministic and sorted by key. Transition status
counts use the transition `new_status`. If explanations are provided,
explanation offer IDs, statuses, reasons, and categories are included in the
same grouped diagnostic summary while `total_transitions` and
`explanation_count` remain separate.

These summaries do not make policy decisions by themselves. They describe
already-retained or caller-provided simulator metadata.

## Helpers

Sprint 2 adds:

- `summarize_stream_offer_lifecycle_audit(registry_hub, explanations=None)`
- `summarize_stream_offer_lifecycle_audit_by_offer(registry_hub, explanations=None)`
- `summarize_stream_offer_lifecycle_audit_by_reason(registry_hub, explanations=None)`

The helpers read only a `RegistryHub` and optional explanation records. They do
not require scenario context and do not use wall-clock time or live clocks.

## Read-Only Boundaries

Audit summaries do not:

- mutate held offers;
- mutate retained transition history;
- record new history;
- retain explanation records;
- apply lifecycle plans;
- delete offers;
- run cleanup;
- schedule retries;
- trigger delivery;
- create delivery results;
- change message inboxes;
- change TrafficHub routing;
- change compact `world.snapshot()` output.

Mutating a copied summary dictionary returned by `to_summary()` does not mutate
the summary model, retained history, explanation records, held offers, or any
RegistryHub state.

## Non-Goals

Sprint 2 does not add:

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
- compact snapshot changes;
- package publication;
- release assets;
- merge, tag, GitHub release, or version bump beyond `1.3.0`.
