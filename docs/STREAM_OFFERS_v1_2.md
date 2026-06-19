# DARWIN v1.2 Stream Offers

Stream offers are simulator-local metadata records for future pull-based lane
rendezvous. A stream offer says that a requester wants to establish or deliver
over a symbolic DARWIN lane, but it does not deliver a message, open a socket,
perform lookup, enqueue durable work, or contact an external service.

The first v1.2 sprint adds compact model foundations:

- `StreamOffer`
- `StreamOfferStatus`
- `StreamOfferMode`
- `StreamOfferVisibility`
- `RendezvousRequest`
- Pure constructors, predicates, and JSON-safe summaries

These records are intended to give later sprints a stable shape for hub-held
offer queues, private polling descent, and lane admission policy without
changing v1.1 mailbox delivery, encrypted delivery, TrafficHub routing, alias
behavior, authority-chain behavior, retained outcomes, audit behavior, or
snapshots.

The second v1.2 sprint adds RegistryHub-local held offer queues. See
`docs/RENDEZVOUS_OFFER_QUEUES_v1_2.md` for queue helper behavior, duplicate
handling, query filters, status updates, and privacy/security framing.

The third v1.2 sprint adds helper-level private polling descent. See
`docs/PRIVATE_POLLING_DESCENT_v1_2.md` for poll result summaries,
discoverability matching, active/expired behavior, and explicit non-goals.

## Purpose

A `StreamOffer` represents a request to establish or deliver over a lane at a
later rendezvous point. The offer can later be held at a rendezvous hub,
discovered by a scoped private polling helper, and evaluated by lane admission
policy. In Sprint 1 it is just a deterministic record.

Core fields:

- `offer_id`: stable simulator ID for the offer.
- `requester_id`: symbolic device or hub requester ID.
- `target_handle`: symbolic target, such as a DARWIN mailbox address or
  alias-like handle.
- `lane_signature`: compact lane key such as `basic_messaging:v1`.
- `requested_mode`: symbolic mode, such as `message`, `stream`, `poll`, or
  `control`.
- `visibility_tier`: integer tier mirroring lane visibility semantics.
- `status`: simulator-local offer lifecycle label.
- `rendezvous_scope`: optional scope or hub layer where the offer may later be
  held.
- `created_order`: deterministic simulator-order counter, not wall-clock time.
- `expires_order`: optional deterministic simulator-order expiration counter.
- `metadata`: optional JSON-safe simulator metadata.

## Lane Signatures

`lane_signature` uses the same compact `lane_id:version` validation as v0.9
lane signatures. For example, `basic_messaging:v1` identifies the existing
toy mailbox messaging lane. Stream offers reference lanes; they do not register
new lanes, bind capabilities, or authorize delivery.

## Target Handles

`target_handle` is a symbolic target string. It may be a DARWIN mailbox address
such as:

```text
darwin://global.chat.neo/inbox
```

It may also be an alias-like simulator handle such as:

```text
alias:neo
```

The stream offer model stores the handle as metadata only. It does not resolve
mailboxes, aliases, DNS records, registrars, public CA state, or external
services.

## Rendezvous Requests

`RendezvousRequest` represents metadata for a child or private hub polling
upward for offers it may see.

Core fields:

- `request_id`
- `offer_id`
- `polling_hub_id`
- `requester_id`
- `target_scope`
- `visibility_tier`
- `metadata`

Sprint 3 uses rendezvous requests as inputs to explicit helper-level polling.
The request remains a JSON-safe record. It does not start live polling,
background polling, sockets, DNS lookup, external services, or delivery.

## RegistryHub Held Offer Queues

Sprint 2 adds RegistryHub-local held offer queues. These queues are explicit
in-memory simulator state, preserve deterministic append order, and remain
separate from message inboxes and delivery result history.

Queue helpers include:

- `hold_stream_offer(...)`
- `get_held_stream_offer(...)`
- `query_held_stream_offers(...)`
- `update_held_stream_offer_status(...)`
- `summarize_held_stream_offers(...)`

Holding a `created` offer stores it as `held`. Duplicate `offer_id` values are
rejected by default, and `replace_existing=True` replaces the existing record
in place. Query helpers are read-only and additive.

Sprint 2 still does not add durable queues, retry workers, background delivery
services, lane admission policy, scenario DSL actions, or scenario DSL
assertions.

## Private Polling Descent

Sprint 3 lets private child hubs explicitly poll an upstream rendezvous hub
for discoverable held stream offers. `poll_held_stream_offers(...)` reads only
the parent hub's `held_stream_offers`, applies deterministic visibility,
scope, lane, mode, status, and expiration filters, and returns a
`RendezvousPollResult`.

Polling is read-only by default. It does not update offer status, deliver
messages, write inboxes, append delivery results, call TrafficHub, or perform
admission policy. `mark_stream_offers_discoverable(...)` is an explicit helper
for marking selected held offers `discoverable` without delivery side effects.

Sprint 3 intentionally does not add live polling, socket listeners, HTTP,
WebSocket behavior, DNS lookup, or external service discovery.

## Future Lane Admission Policies

Later v1.2 work may evaluate discovered offers against hub-level admission
policy. Possible outcomes include passing an offer downward, holding it,
denying it, rate-limiting it, quarantining it, or requiring a later device
poll.

Sprint 1 and Sprint 2 intentionally do not add lane admission rules, firewall
behavior, production DDoS protection, scenario DSL actions, or scenario DSL
assertions.

## Example

```python
from darwin.models import make_basic_messaging_stream_offer

offer = make_basic_messaging_stream_offer(
    offer_id="offer_basic_001",
    requester_id="dev_A9F3",
    target_handle="darwin://global.chat.neo/inbox",
    rendezvous_scope="global.chat",
    created_order=3,
)

offer.to_summary()
```

Summary:

```json
{
  "offer_id": "offer_basic_001",
  "requester_id": "dev_A9F3",
  "target_handle": "darwin://global.chat.neo/inbox",
  "lane_signature": "basic_messaging:v1",
  "requested_mode": "message",
  "visibility_tier": 0,
  "status": "created",
  "rendezvous_scope": "global.chat",
  "created_order": 3,
  "expires_order": null,
  "metadata": {
    "simulator_local": true,
    "request_only": true,
    "delivery_behavior_changed": false,
    "networking": false
  }
}
```

## Status Vocabulary

Stream offer statuses:

- `created`: constructed record, not held or evaluated.
- `held`: future state for a rendezvous hub retaining an offer.
- `discoverable`: future state for an offer visible to a polling scope.
- `passed_down`: future state for an offer passed toward a child/private hub.
- `accepted`: terminal accepted state.
- `denied`: terminal denied state.
- `expired`: terminal expired state.
- `rate_limited`: terminal or policy-limited state.
- `quarantined`: terminal or security-policy-limited state.

Sprint 1 predicates use simple deterministic status groups:

- Active: `created`, `held`, `discoverable`, `passed_down`.
- Terminal: `accepted`, `denied`, `expired`, `rate_limited`, `quarantined`.
- Expired: status is `expired`, or `current_order >= expires_order` when an
  expiration order is set.

## Deterministic Order Fields

`created_order` and `expires_order` are simulator counters. They are not
wall-clock timestamps. They are intended to keep tests and scenario output
deterministic.

## Privacy And Security Framing

Stream offers can reduce direct endpoint exposure inside the simulator by
modeling a request as parked at a rendezvous layer rather than immediately
targeting a private endpoint.

They do not provide anonymity. Rendezvous layers may still observe requester
IDs, target handles, lane signatures, requested modes, timing/order fields,
visibility tiers, offer volume, and scoped metadata depending on modeled
visibility.

They are not production DDoS protection, not a firewall, not a secure messaging
protocol, and not production privacy infrastructure. v1.2 stream offer records
do not add real cryptography, production E2EE, key exchange, or
metadata-hiding guarantees.

## Non-Goals

Sprint 1 explicitly does not add:

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
