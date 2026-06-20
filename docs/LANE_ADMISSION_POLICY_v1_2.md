# DARWIN v1.2 Lane Admission Policy

Lane admission policy is simulator-local helper behavior for deciding whether
a discovered `StreamOffer` can symbolically move downward from a rendezvous or
hub layer.

It is not a firewall implementation, not production DDoS protection, not a
network access-control system, not privacy or anonymity infrastructure, and
not a secure transport protocol.

## Purpose

Sprint 4 adds deterministic policy records and decisions:

- `LaneAdmissionPolicy`
- `LaneAdmissionDecision`
- `LaneAdmissionStatus`
- `LaneAdmissionReason`
- `make_lane_admission_policy(...)`
- `evaluate_lane_admission_policy(...)`
- `is_lane_admission_allowed(...)`
- `is_lane_admission_blocked(...)`
- `is_lane_admission_terminal(...)`

The helper evaluates supplied in-memory objects only. It does not mutate held
offers, mutate `RegistryHub`, deliver messages, call `TrafficHub`, open
sockets, perform DNS lookup, poll live services, or contact external systems.

## Relationship To StreamOffer

`StreamOffer` remains the input record for future pull-based lane rendezvous.
Lane admission reads the offer's requester ID, target handle, rendezvous
scope, lane signature, visibility tier, and status.

Admission does not register a lane, bind a mailbox, resolve a target handle,
write an inbox, append a delivery result, or alter TrafficHub routing.

Terminal stream offers are treated conservatively as invalid admission inputs.

## Relationship To RendezvousRequest

A `RendezvousRequest` can provide request context for an admission decision.
When present, its `request_id` is copied into the decision and its
`target_scope` is used as the evaluated target scope.

The request remains metadata for one explicit simulator helper call. It does
not start a live polling loop, open a socket, perform DNS lookup, or contact an
external service.

## Relationship To RendezvousPollResult

A `RendezvousPollResult` can prove that an offer was visible in a previous
explicit helper-level poll. When `LaneAdmissionPolicy.require_discoverable` is
true, the offer must appear in the poll result's `matched_offer_ids` and the
poll result must be `matched`.

If the offer is not discoverable through the supplied poll result, admission
returns a `requires_poll` decision with reason `not_discoverable`.

## Relationship To Scenario DSL

Sprint 5 exposes admission through `evaluate_lane_admission_policy` and
`lane_admission_decision_contains`. Scenario evaluation finds a held offer,
builds a simulator-local policy, optionally uses a prior poll request/result,
and appends the `LaneAdmissionDecision` to action results for assertions.

Scenario-level admission remains read-only by default. It does not mutate the
held offer, retain admission history on RegistryHub, deliver messages, call
TrafficHub, open sockets, perform DNS lookup, or start live polling.

## Policy Fields

`LaneAdmissionPolicy` records:

- `policy_id`
- `hub_id`
- `allowed_lane_signatures`
- `denied_lane_signatures`
- `allowed_requester_ids`
- `denied_requester_ids`
- `allowed_target_scopes`
- `denied_target_scopes`
- `max_visibility_tier`
- `require_discoverable`
- `default_status`
- `metadata`

Allowed lists are optional. When present, the offer must match the list or the
decision holds. Denied lists take precedence over allowed lists.

## Decision Fields

`LaneAdmissionDecision` records:

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
- `metadata`

`allowed` is true only when status is `pass_down`.

## Status Vocabulary

Lane admission statuses:

- `pass_down`: the offer may symbolically move downward.
- `hold`: the offer remains held for later policy or polling work.
- `deny`: the offer is denied.
- `rate_limited`: the offer is symbolically rate-limited.
- `quarantined`: the offer is symbolically quarantined.
- `requires_poll`: the policy requires a matching poll result first.

Blocked statuses are `deny`, `rate_limited`, and `quarantined`.

Terminal statuses are `pass_down`, `deny`, `rate_limited`, and
`quarantined`.

## Reason Vocabulary

Lane admission reasons:

- `accepted`
- `default_hold`
- `explicit_lane_denied`
- `explicit_requester_denied`
- `explicit_scope_denied`
- `lane_not_allowed`
- `requester_not_allowed`
- `scope_not_allowed`
- `visibility_tier_exceeded`
- `not_discoverable`
- `rate_limited`
- `quarantined`
- `invalid_offer`
- `invalid_policy`

## Deterministic Precedence

`evaluate_lane_admission_policy(...)` applies this order:

1. Invalid policy or offer.
2. Explicit denied requester.
3. Explicit denied lane signature.
4. Explicit denied target scope.
5. Visibility tier exceeded.
6. Required discoverability missing from the supplied poll result.
7. Allowed-list checks, when present.
8. Policy default status.

The helper is conservative. `pass_down` is the only allowed decision. `hold`,
`deny`, `rate_limited`, `quarantined`, and `requires_poll` are not allowed.

## Read-Only Behavior

Admission evaluation is read-only by default. It returns a new
`LaneAdmissionDecision` and does not mutate:

- The supplied policy.
- The supplied offer.
- The supplied rendezvous request.
- The supplied poll result.
- Any RegistryHub queue.
- Any message inbox or delivery result history.
- TrafficHub routes.

Decision metadata records this non-mutating scope with JSON-safe simulator
flags.

## Privacy And Security Framing

Lane admission can model hub-level filtering inside the simulator. It can help
test state machines where a hub decides whether a discovered offer is held,
passed downward, denied, rate-limited, quarantined, or made to wait for a
later poll.

It does not provide anonymity. Rendezvous and policy layers may still observe
requester IDs, target handles, target scopes, lane signatures, requested
modes, visibility tiers, timing/order fields, poll result metadata, and offer
volume depending on the modeled flow.

It is not production firewalling, not production DDoS protection, not a real
network access-control system, not production privacy infrastructure, and not
a secure transport protocol. It does not add real cryptography, production
E2EE, key exchange, metadata hiding, or traffic-analysis resistance.

## Non-Goals

Sprint 4 explicitly does not add:

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
