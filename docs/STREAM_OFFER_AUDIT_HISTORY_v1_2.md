# DARWIN v1.2 Stream Offer Audit History

Sprint 6 adds RegistryHub-local retained history for explicit rendezvous poll
results and lane admission decisions. The history is simulator audit metadata
for explainability, assertions, and detailed snapshots. It is not a live
network log, socket trace, firewall log, DDoS log, privacy guarantee, or
anonymity guarantee.

## Purpose

Held stream offers already retain the pending rendezvous state on
`RegistryHub.held_stream_offers`. Sprint 6 keeps the outcomes of explicit
poll and admission actions next to that queue:

- `RegistryHub.rendezvous_poll_result_history`
- `RegistryHub.lane_admission_decision_history`

Both lists default to empty, preserve deterministic append order, and contain
the immutable `RendezvousPollResult` or `LaneAdmissionDecision` objects that
were explicitly recorded.

## Recording Helpers

Recording is explicit:

- `record_rendezvous_poll_result(registry_hub, result)`
- `record_lane_admission_decision(registry_hub, decision)`

The pure helpers remain read-only by default:

- `poll_held_stream_offers(...)` returns a `RendezvousPollResult` without
  mutating the hub.
- `evaluate_lane_admission_policy(...)` returns a `LaneAdmissionDecision`
  without mutating the hub.

Scenario actions record their explicit outcomes after evaluation. The same
objects are still appended to scenario action results for compatibility.

## Query Helpers

`query_rendezvous_poll_results(...)` reads only
`registry_hub.rendezvous_poll_result_history`. Filters are additive and
preserve append order:

- `request_id`
- `polling_hub_id`
- `parent_hub_id`
- `target_scope`
- `visibility_tier`
- `status`
- `reason`
- `matched_offer_id`

`query_lane_admission_decisions(...)` reads only
`registry_hub.lane_admission_decision_history`. Filters are additive and
preserve append order:

- `decision_id`
- `policy_id`
- `offer_id`
- `request_id`
- `hub_id`
- `requester_id`
- `target_handle`
- `target_scope`
- `lane_signature`
- `status`
- `reason`
- `allowed`

Empty matches return an empty list. Query helpers are read-only and do not
mutate retained histories, held offers, message inboxes, delivery results, or
TrafficHub state.

## Summaries

Use these helpers for copied JSON-safe summaries:

- `summarize_rendezvous_poll_results(...)`
- `summarize_lane_admission_decisions(...)`

The summaries use each retained record's `to_summary()` shape. Mutating a
summary does not mutate the retained history.

## Scenario Assertions

The existing assertions now prefer retained history:

- `rendezvous_poll_result_contains`
- `lane_admission_decision_contains`

If the relevant retained history is empty or unavailable, assertions fall back
to scenario action results for backwards compatibility. `held_stream_offer_contains`
continues to query `RegistryHub.held_stream_offers`.

## Snapshot Visibility

Detailed world snapshots include compact retained summaries under each
RegistryHub:

```text
registry_hubs.<hub_id>.held_stream_offers
registry_hubs.<hub_id>.rendezvous_poll_result_history
registry_hubs.<hub_id>.lane_admission_decision_history
```

Compact `world.snapshot()` output remains unchanged and does not include these
retained histories. Detailed snapshot entries are copied JSON-safe summaries,
not live mutable references.

## Privacy And Security Framing

Retained histories improve simulator explainability: they show which explicit
polls were evaluated and which symbolic lane admission decisions were made.

They also expose modeled metadata. Depending on the scenario, retained records
may include requester IDs, polling hub IDs, target handles, target scopes, lane
signatures, visibility tiers, statuses, reasons, matched offer IDs, and
JSON-safe metadata. Treat that metadata carefully in tests and examples.

These histories are not production network logs, not socket traces, not
production firewall or DDoS logs, not privacy or anonymity guarantees, and not
evidence of production security behavior.

## Non-Goals

Sprint 6 does not add:

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
