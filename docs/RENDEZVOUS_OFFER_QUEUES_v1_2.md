# DARWIN v1.2 Rendezvous Offer Queues

Rendezvous offer queues are RegistryHub-local, in-memory simulator records for
holding `StreamOffer` objects at a symbolic rendezvous layer. They model a hub
retaining offers for later discovery or policy evaluation, but they do not
deliver messages, open sockets, poll live services, enqueue durable jobs, or
contact external infrastructure.

## Purpose

A held stream offer queue lets a rendezvous `RegistryHub` retain requests in a
deterministic append order. This gives later v1.2 sprints a stable state
surface for private polling descent, lane admission policy, scenario DSL work,
snapshot visibility, and audit summaries.

The queue is intentionally small:

- `RegistryHub.held_stream_offers` stores `StreamOffer` records.
- `hold_stream_offer(...)` appends or replaces a held offer.
- `get_held_stream_offer(...)` returns one offer by ID.
- `query_held_stream_offers(...)` applies additive read-only filters.
- `update_held_stream_offer_status(...)` replaces a held offer with an updated
  immutable record.
- `summarize_held_stream_offers(...)` returns JSON-safe copied summaries.
- `poll_held_stream_offers(...)` reads the queue for discoverable offers.
- `mark_stream_offers_discoverable(...)` explicitly marks selected held offers
  as discoverable.
- `evaluate_lane_admission_policy(...)` can evaluate a held offer separately
  without mutating the queue.

## Relationship To StreamOffer

The queue stores existing `StreamOffer` records. If an offer is still in
`created` status when held, `hold_stream_offer(...)` stores a copy with status
`held`. Other valid statuses are retained.

Holding an offer does not register a lane, bind a mailbox, evaluate admission
policy, resolve a target handle, deliver a message, or alter TrafficHub
routing.

## Duplicate Behavior

Offer IDs are unique within one RegistryHub held queue.

By default, holding a second offer with an existing `offer_id` raises a
deterministic error and leaves the queue unchanged. Passing
`replace_existing=True` replaces the existing record in place, preserving the
original queue position.

## Status Updates

`update_held_stream_offer_status(...)` finds a held offer by `offer_id`,
validates the new status against the `StreamOfferStatus` vocabulary, and
stores an immutable replacement record at the same queue position.

Optional metadata is shallow-merged into the existing offer metadata and then
validated by the `StreamOffer` model. Metadata must remain JSON-safe simulator
data.

## Query Filters

`query_held_stream_offers(...)` reads only
`registry_hub.held_stream_offers`. Filters are additive and preserve append
order:

- `offer_id`
- `requester_id`
- `target_handle`
- `lane_signature`
- `requested_mode`
- `visibility_tier`
- `status`
- `rendezvous_scope`
- `active_only`
- `current_order`

When `active_only=True`, active structural statuses are returned and offers
expired by `current_order` are excluded. When `active_only=False`, terminal or
expiration-by-order offers are returned. Supplying `current_order` without
`active_only` does not mutate or filter the queue.

## Deterministic Simulator Order

The queue is a list. Helpers preserve append order for listing and query
results. Replacement updates keep the existing list index. There is no
background worker, retry loop, live poller, wall-clock scheduler, or durable
queue.

## JSON-Safe Summaries

Use `offer.to_summary()` or `summarize_held_stream_offers(...)` for copied,
JSON-safe dictionaries. Summary mutation does not mutate retained offers.

## Private Polling Descent

Sprint 3 adds private polling descent helpers. A child or private hub can
explicitly ask an upstream rendezvous hub for discoverable offers with
`poll_held_stream_offers(...)`, then receive a deterministic
`RendezvousPollResult`.

Polling reads only `held_stream_offers` and preserves append order. It matches
visibility tier, rendezvous scope, optional lane signature, optional requested
mode, active status, and deterministic expiration order. It is read-only by
default and does not update offer status, deliver messages, write inboxes,
append delivery results, call TrafficHub, or perform admission policy.

This remains a simulator helper call, not a live loop, socket listener, HTTP
endpoint, WebSocket endpoint, DNS lookup, or external service.

## Lane Admission Policy

Sprint 4 adds helper-level lane admission policy. Admission reads an offer,
an admission policy, and optional rendezvous request or poll result context,
then returns a deterministic decision such as hold, pass down, deny, rate
limit, quarantine, or require poll.

Admission does not mutate `held_stream_offers` by default. It also does not
deliver messages, write inboxes, append delivery results, call TrafficHub,
open sockets, perform DNS lookup, or run live polling loops.

## Scenario DSL Coverage

Sprint 5 adds scenario actions and assertions over the same held queue helper
surface. `hold_stream_offer` stores offers on `RegistryHub.held_stream_offers`,
`poll_held_stream_offers` records explicit poll results in scenario action
results, and `held_stream_offer_contains` reads the queue with additive
filters. Detailed scenario snapshots now include compact
`held_stream_offers` summaries for each RegistryHub.

This scenario layer remains symbolic metadata flow only. It does not make the
queue durable, start retry workers, run live polling loops, deliver messages,
or route TrafficHub traffic.

## Privacy And Security Framing

Held offers can reduce direct endpoint exposure inside the simulator by
modeling a request as parked at a rendezvous layer instead of immediately
targeting a private endpoint.

They do not provide anonymity. Rendezvous layers may still observe timing,
volume, requester IDs, target handles or scopes, lane signatures, requested
modes, visibility tiers, expiration order, and other metadata depending on the
modeled visibility.

They are not production DDoS protection, not a firewall product, not a secure
messaging protocol, and not production privacy infrastructure. v1.2 rendezvous
offer queues do not add real cryptography, production E2EE, key exchange, or
metadata-hiding guarantees.

## Non-Goals

Sprint 2 explicitly does not add:

- Real networking.
- Sockets.
- HTTP or WebSocket behavior.
- Live polling.
- DNS lookup.
- External services.
- Registrar integration.
- Public CA behavior.
- Production identity proof.
- Durable queues.
- Retry workers.
- Production DDoS/security/privacy/anonymity guarantees.
- Real cryptography or E2EE.
- Delivery behavior changes.
- TrafficHub routing changes.
- Canonical identity rewrites.
- Scenario DSL actions.
- Scenario DSL assertions.
- New scenario YAMLs.
