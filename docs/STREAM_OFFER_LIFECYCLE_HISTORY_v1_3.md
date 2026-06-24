# DARWIN v1.3 Stream Offer Lifecycle History

Sprint 1 adds RegistryHub-local retained history for explicit stream-offer
status transitions. The history is symbolic simulator audit metadata only. It
exists to make helper-driven lifecycle changes inspectable in tests, docs, and
detailed snapshots.

This feature does not add delivery behavior, TrafficHub routing, DNS,
networking, external services, real cryptography, or production security
behavior.

## Purpose

Held stream offers remain stored on:

```text
RegistryHub.held_stream_offers
```

Lifecycle transition metadata is retained separately on:

```text
RegistryHub.stream_offer_status_transition_history
```

The retained list defaults to empty and preserves deterministic append order.
It contains immutable `StreamOfferStatusTransition` records describing an
explicit symbolic status movement:

- `offer_id`
- `previous_status`
- `new_status`
- `reason`
- `hub_id`
- optional `actor_id`
- optional `request_id`
- optional JSON-safe `metadata`
- optional deterministic `sequence`

## Reasons

The v1.3 Sprint 1 reason vocabulary is intentionally small:

- `status_updated`
- `expired`
- `manual_hold`
- `manual_deny`
- `manual_quarantine`

Reasons are labels for simulator explainability. They are not production
policy decisions, enforcement outcomes, compliance evidence, or network logs.

## Recording Helpers

Recording is explicit:

- `make_stream_offer_status_transition(...)`
- `record_stream_offer_status_transition(registry_hub, transition)`

`update_held_stream_offer_status(...)` remains compatible by default and does
not record transition history unless called with `record_transition=True`.
That opt-in path records the previous status, new status, reason, hub ID, and
optional actor/request/metadata/sequence fields.

The recording helpers do not deliver messages, create delivery results,
mutate TrafficHub routing, contact networks, perform DNS lookup, or evaluate
cryptographic state.

## Query Helpers

`query_stream_offer_status_transitions(...)` reads only
`registry_hub.stream_offer_status_transition_history`. Filters are additive
and preserve append order:

- `offer_id`
- `hub_id`
- `previous_status`
- `new_status`
- `status`
- `reason`
- `actor_id`
- `request_id`

The `status` filter matches either previous or new status. Empty matches
return an empty list. Query helpers are read-only and do not mutate retained
history, held stream offers, message inboxes, delivery results, or TrafficHub
state.

## Summaries

Use `summarize_stream_offer_status_transitions(...)` for copied JSON-safe
summaries in append order. Mutating a summary does not mutate retained
history.

## Snapshot Visibility

Detailed world snapshots include copied transition summaries under each
RegistryHub:

```text
registry_hubs.<hub_id>.stream_offer_status_transition_history
```

Compact `world.snapshot()` output remains unchanged and does not include
transition history.

## Non-Goals

Sprint 1 does not add:

- real networking;
- sockets;
- HTTP or WebSocket behavior;
- DNS lookup;
- registrar integration;
- public CA behavior;
- external services;
- cleanup workers;
- retry loops;
- background jobs;
- durable queues;
- clocks, timers, or live polling;
- production DDoS guarantees;
- production firewall guarantees;
- production privacy or anonymity guarantees;
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
- scenario DSL changes;
- package publication;
- version bumps beyond `1.2.0` during planning.
