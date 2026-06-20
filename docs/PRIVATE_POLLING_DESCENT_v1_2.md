# DARWIN v1.2 Private Polling Descent

Private polling descent is a simulator-local helper flow where a child or
private hub issues one explicit `RendezvousRequest` against an upstream
rendezvous `RegistryHub` and receives the held stream offers that are
discoverable for that request.

It is not live polling, not a network protocol, not socket behavior, not DNS,
not durable messaging infrastructure, and not delivery.

## Purpose

Sprint 3 adds deterministic helper behavior for pull-based discovery:

- `RendezvousPollResult`
- `RendezvousPollStatus`
- `poll_held_stream_offers(...)`
- `mark_stream_offers_discoverable(...)`
- `stream_offer_matches_rendezvous_request(...)`
- `is_stream_offer_discoverable_to_request(...)`

The helper reads only `RegistryHub.held_stream_offers` on the parent or
rendezvous hub. It returns a compact poll result and does not mutate held
offers by default.

## Relationship To RendezvousRequest

`RendezvousRequest` supplies the polling metadata:

- `request_id`
- `polling_hub_id`
- `target_scope`
- `visibility_tier`
- JSON-safe metadata

The request represents one explicit simulator helper call. It does not start a
background poller, open a socket, perform DNS lookup, or contact an external
service.

## Relationship To Held Stream Offers

`poll_held_stream_offers(...)` scans the parent hub's
`held_stream_offers` list in append order. Matching offers are returned in the
same deterministic order through:

- `matched_offer_ids`
- `matched_offers`
- `matched_count` in the JSON-safe summary

The default poll is read-only. It does not update offer statuses, deliver
messages, write inboxes, append delivery results, or alter TrafficHub routes.

`mark_stream_offers_discoverable(...)` is separate and explicit. It marks
selected held offers as `discoverable`, preserves queue order, and shallow
merges JSON-safe metadata. It does not poll, deliver, or route.

## Matching Rules

A held stream offer is discoverable when:

- Its visibility tier is compatible with the request visibility tier.
- Its `rendezvous_scope` is absent or equals the request `target_scope`.
- Optional `lane_signature` matches, when supplied.
- Optional `requested_mode` matches, when supplied.
- It is active, unless `active_only=False`.
- It is not expired by `current_order`, when `current_order` is supplied and
  `active_only=True`.

The helper is conservative and deterministic. It does not perform admission
policy, trust negotiation, endpoint lookup, mailbox resolution, alias
resolution, or delivery.

## Visibility Tier Behavior

Sprint 3 treats the request visibility tier as the maximum offer tier the
polling hub may discover. For example:

- A tier `0` request can discover tier `0` offers.
- A tier `2` request can discover tier `0`, `1`, and `2` offers.
- A tier `2` request cannot discover tier `3`, `4`, or `5` offers.

This mirrors the existing tier ordering without introducing a new trust-context
model in this sprint. More detailed trust and admission behavior remains
deferred to later v1.2 work.

## Active And Expired Behavior

By default, polling returns active offers only. Active statuses are the same
structural group used by the stream offer model:

- `created`
- `held`
- `discoverable`
- `passed_down`

Terminal statuses are excluded when `active_only=True`. If `current_order` is
supplied, offers with `expires_order <= current_order` are also excluded.

Passing `active_only=False` includes structurally matching terminal and
expiration-by-order offers. It still does not mutate those offers.

## Poll Result Statuses

`RendezvousPollResult` uses compact statuses:

- `matched`
- `empty`
- `invalid_request`

Reasons include:

- `offers_available`
- `no_discoverable_offers`
- `invalid_request`
- `hub_missing`
- `scope_mismatch`

Summaries are copied and JSON-safe.

## Retained Poll History

Sprint 6 adds optional RegistryHub-local retention for explicit poll results:

- `record_rendezvous_poll_result(...)`
- `query_rendezvous_poll_results(...)`
- `summarize_rendezvous_poll_results(...)`

`poll_held_stream_offers(...)` remains read-only by default. Scenario
`poll_held_stream_offers` actions record the returned result on the
RegistryHub after evaluation and still append the request and result to action
results. Retained poll queries filter by request ID, polling hub ID, parent
hub ID, target scope, visibility tier, status, reason, and matched offer ID.
Detailed snapshots include compact retained poll summaries; compact
`world.snapshot()` output remains unchanged.

## Relationship To Lane Admission Policy

Private polling descent is discovery only. Sprint 4 adds separate lane
admission helpers that can consume a `RendezvousPollResult` as optional
context and decide whether a lane offer should pass downward, be held, be
denied, be rate-limited, be quarantined, or require another poll.

Discovery and admission remain separate. Polling does not evaluate policy, and
admission does not poll live services, deliver messages, or route traffic.

## Scenario DSL Coverage

Sprint 5 adds `poll_held_stream_offers` as a scenario action and
`rendezvous_poll_result_contains` as a read-only assertion. Sprint 6 changes
the assertion to prefer retained RegistryHub poll history and fall back to
scenario action results when retained history is empty or unavailable. The
action represents one explicit helper call and does not start a live poller,
socket listener, HTTP endpoint, WebSocket endpoint, DNS lookup, or external
service request.

## Privacy And Security Framing

Polling descent can reduce direct endpoint exposure inside the simulator by
modeling offers as discovered from a rendezvous layer instead of pushed
directly to a private endpoint.

It does not provide anonymity. Rendezvous layers may still observe timing,
volume, target handles or scopes, polling hub IDs, requester IDs, lane
signatures, requested modes, visibility tiers, expiration order, and other
modeled metadata.

It is not production DDoS protection, not a firewall product, not a secure
messaging protocol, and not production privacy infrastructure. Sprint 3 does
not add real cryptography, production E2EE, key exchange, or metadata-hiding
guarantees.

## Non-Goals

Sprint 3 explicitly does not add:

- Real networking.
- Sockets.
- HTTP or WebSocket behavior.
- Live polling loops.
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
