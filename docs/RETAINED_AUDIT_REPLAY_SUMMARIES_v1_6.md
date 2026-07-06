# Retained Audit Replay Summaries v1.6

Status: v1.6 Sprint 2 read-only helper. v1.6 is unreleased, and the
package version remains `darwin-sim 1.5.0`.

Retained audit replay summaries are symbolic simulator-local diagnostic
metadata only. They summarize explicit retained audit records that a caller
provides, preserving deterministic record-key order and grouped counts for
inspection.

Sprint 2 summarizes retained audit records but does not delete, compact,
mutate, rewrite, replace, schedule cleanup, replay network traffic, or trigger
delivery. The helpers do not inspect or mutate `RegistryHub` by themselves;
callers pass explicit retained records.

## Supported Record Families

Sprint 2 supports the same retained stream-offer audit families as Sprint 1:

- `stream_offer_lifecycle_explanation`
- `stream_offer_status_transition`

Unsupported retained-history families, records from another hub, and records
outside an explicit history-type filter are handled deterministically and are
not included in replay counts. Their generated keys are reported in summary
metadata as ignored or filtered diagnostic keys.

## Summary Model

`RetainedAuditReplaySummary` records:

- `hub_id`
- `history_type`
- `record_count`
- `record_keys`
- grouped counts by status, reason, source, and offer ID
- optional `first_record_key`
- optional `last_record_key`
- optional JSON-safe `metadata`

Record keys use the same deterministic sequence-style key shapes as the
Sprint 1 retained audit compaction helpers. Lifecycle explanations use the
existing lifecycle explanation key shape. Status transitions use the
deterministic transition key with the explicit sequence field when present.

## Helpers

Sprint 2 adds:

- `summarize_retained_audit_replay(...)`
- `summarize_retained_audit_replay_by_history_type(...)`
- `summarize_retained_audit_replay_by_reason(...)`

The helpers are pure and read-only. They accept explicit retained audit
records, do not require scenario context, and do not use wall-clock time or
live clocks.

`summarize_retained_audit_replay(...)` can optionally accept a
`RetainedAuditCompactionDecision` and summarize only records whose generated
keys are in the decision's retained set or compaction-candidate set. The
default summarizes all supported records for the requested hub. This filtering
does not reclassify records and does not change Sprint 1 compaction
classification semantics.

## Read-Only Boundaries

Replay summaries do not:

- mutate retained histories;
- mutate held offers;
- mutate `RegistryHub`;
- record new history;
- delete records;
- compact records;
- prune records;
- rewrite or replace records;
- schedule cleanup;
- run background workers;
- run retry loops;
- create durable queues;
- use live timers or live clocks;
- replay network traffic;
- trigger delivery;
- create delivery results;
- change message inboxes;
- change TrafficHub routing;
- change compact `world.snapshot()` output.

There are no background workers, retry loops, durable queues, live timers,
network logs, compliance systems, firewall or DDoS systems, privacy or
anonymity guarantees, or production security infrastructure.

Sprint 2 adds no delivery behavior, TrafficHub routing behavior, DNS,
networking, external service behavior, registrar behavior, public CA behavior,
real cryptography, key generation, private key storage, encryption,
decryption, production E2EE, delivery enforcement, scenario DSL actions,
scenario DSL assertions, detailed snapshot changes, compact snapshot changes,
or canonical identity rewrites.

## Non-Goals

Sprint 2 does not add:

- automatic cleanup workers;
- background services;
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
- compliance systems;
- production privacy guarantees;
- production anonymity guarantees;
- production security infrastructure;
- real cryptography;
- key generation;
- private key storage;
- production E2EE;
- delivery enforcement;
- mailbox delivery behavior changes;
- encrypted delivery behavior changes;
- TrafficHub routing changes;
- canonical identity rewrites;
- scenario DSL actions or assertions;
- detailed snapshot changes;
- compact snapshot changes;
- package publication;
- release assets;
- merge, tag, GitHub release, or version bump beyond `1.5.0`.
