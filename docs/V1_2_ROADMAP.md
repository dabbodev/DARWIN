# DARWIN v1.2 Roadmap: Pull-Based Lane Rendezvous and Stream Offer Admission

DARWIN v1.2 planning starts from the released v1.1.0 simulator on `main`.
The planning branch is `v1.2/planning`. The package and CLI version should
remain `darwin-sim 1.1.0` until explicit v1.2 release prep.

Recommended theme: Pull-Based Lane Rendezvous and Stream Offer Admission.

v1.2 should remain simulator-first. It should not become production
networking, a real DDoS protection system, a privacy or anonymity system,
DNS, registrar infrastructure, external service discovery, or a secure
messaging protocol.

## Core Concept

Model a pull-based communication lane establishment flow where senders create
stream offers that climb toward a public or rendezvous hub layer. Private
child hubs poll upward for pending stream offers, apply lane admission policy,
and decide whether to hold, pass downward, deny, rate-limit, quarantine, or
require a later device poll.

Device-facing hubs can later choose whether to auto-push, hold until device
poll, or deny. All of this should remain simulator records, helper functions,
scenario DSL behavior, tests, snapshots, and documentation. It should not open
sockets, poll live services, perform DNS lookup, contact registrars, integrate
external services, change TrafficHub routing, rewrite canonical identity, or
claim production security properties.

## Release Boundaries

In scope:

- Simulator-local stream offer records.
- RegistryHub-local held offer queues.
- Public or rendezvous hub storage modeled as in-memory simulator state.
- Private polling descent helpers with visibility and trust filters.
- Hub-level lane admission policy records and deterministic outcomes.
- Scenario DSL actions and assertions after helper behavior is stable.
- Snapshot and audit visibility for held offers, poll results, and admission
  decisions.
- Documentation that explains metadata and privacy limitations.

Out of scope:

- Real networking, sockets, HTTP, WebSocket, DNS, or service discovery.
- Live polling, background workers, durable queues, or retry services.
- Production DDoS protection or firewall claims.
- Privacy, anonymity, metadata-hiding, or traffic-analysis guarantees.
- Registrar integration, public CA behavior, or production identity proof.
- Real cryptography, key exchange, production E2EE, or secure messaging.
- TrafficHub routing changes.
- Canonical identity rewrites.
- Version bump beyond `1.1.0` before explicit release prep.
- Package publication, tagging, or release creation during planning.

## Key Concepts

Stream offer:

- A simulator-local request to establish or deliver over a lane.
- Carries target handle or address, lane signature, requester ID, requested
  mode, visibility tier, status, and metadata.
- Does not deliver payloads, perform network routing, or prove identity.

Rendezvous hub:

- A public or shared RegistryHub-layer record holder for pending offers.
- Stores offers that may be visible to scoped child hubs.
- Does not perform DNS, external service lookup, socket listening, or public
  infrastructure behavior.

Private polling descent:

- A helper flow where private or child hubs ask an upstream hub for
  discoverable offers they may see.
- Applies visibility and trust filters before admission policy.
- Remains an explicit simulator call, not live polling or background work.

Lane admission policy:

- Hub-level simulator rules for whether an offer may move downward.
- Separates discovery from admission.
- Produces deterministic outcomes such as `pass_down`, `hold`, `deny`,
  `rate_limited`, `quarantined`, and `requires_poll`.

Held stream request:

- An offer parked at a rendezvous or private hub until a child hub or device
  polls, policy changes, or a scenario inspects the retained state.
- Not a durable queue, retry worker, or guaranteed delivery mechanism.

Delivery mode:

- A simulator policy label for how a device-facing hub treats an admitted
  offer: `auto_push`, `hold_until_poll`, `deny`, `rate_limited`, or
  `quarantined`.

## Privacy and Security Framing

This model can reduce direct endpoint exposure inside the simulator by
showing an offer as parked at a rendezvous layer instead of immediately
targeting a private endpoint.

It provides simulator-level policy gates before private descent. Those gates
are useful for testing state machines, scenario assertions, and audit output,
but they are not production DDoS protection and are not a firewall product.

It is not an anonymity system. Rendezvous layers may still observe timing,
offer volume, requester metadata, lane signatures, target handles, visibility
tiers, and scoped metadata depending on the modeled visibility policy.

It is not a secure messaging protocol. v1.2 should not add real
cryptography, production E2EE, key exchange, transport encryption, or
metadata-hiding guarantees.

## Sprint 1: Stream Offer and Rendezvous Request Models

Status: implemented on `v1.2/planning`.

Goal: introduce the smallest simulator-local record shape for an offer to
establish or deliver over a lane.

Candidate work:

- Add a `StreamOffer` or `LaneStreamOffer` model.
- Include target handle or address, lane signature, requester ID, requested
  mode, visibility tier, status, and metadata.
- Add deterministic constructors, JSON-safe summaries, and pure predicates.
- Keep the model separate from mailbox delivery and TrafficHub routing.
- Add tests for construction, summary stability, status labels, and invalid
  combinations.

Acceptance targets:

- Offers are records only and do not mutate hubs by construction.
- No real networking, delivery behavior, DNS lookup, or external service
  behavior is added.
- Existing v1.1 encrypted delivery and v0.9 mailbox behavior remain
  unchanged.

Implemented scope:

- Added simulator-local `StreamOffer`, `StreamOfferStatus`,
  `StreamOfferMode`, `StreamOfferVisibility`, and `RendezvousRequest` models.
- Added deterministic constructors, pure predicates, and JSON-safe summaries.
- Documented Sprint 1 behavior in `docs/STREAM_OFFERS_v1_2.md`.
- Kept hub-held queues, private polling descent, admission policy, scenario
  DSL, delivery changes, and networking behavior deferred.

## Sprint 2: Rendezvous Hub Offer Queues

Status: implemented on `v1.2/planning`.

Goal: store held stream offers on RegistryHub-local rendezvous queues.

Candidate work:

- Add RegistryHub-local held offer queues.
- Model public or rendezvous layer storage as in-memory simulator state.
- Add register, get, list, and query helpers.
- Preserve deterministic append order and JSON-safe summaries.
- Add status transitions for held, withdrawn, expired-by-scenario, and
  superseded records if needed.

Acceptance targets:

- Offers remain simulator records only.
- Queue helpers are explicit and deterministic.
- No background retry workers, durable queues, sockets, or live polling are
  introduced.

Implemented scope:

- Added `RegistryHub.held_stream_offers` as in-memory simulator-local storage.
- Added helpers to hold, get, query, update, and summarize held stream offers.
- Preserved append order, duplicate rejection by default, deterministic
  replacement, JSON-safe summaries, and read-only additive query filters.
- Kept private polling descent, lane admission policy, scenario DSL changes,
  delivery changes, durable queues, retry workers, sockets, DNS lookup, and
  real networking deferred.

## Sprint 3: Private Polling Descent Helpers

Status: implemented on `v1.2/planning`.

Goal: let child or private hubs explicitly poll upward for stream offers they
may discover.

Candidate work:

- Add a helper for child/private hubs to poll an upstream rendezvous hub for
  discoverable stream offers.
- Apply visibility tier, target scope, requester, and trust filters.
- Preserve separation between discovery and admission.
- Return deterministic poll results without mutating private hub admission
  state unless the caller opts into retention.

Acceptance targets:

- Polling is a simulator helper call, not a live loop or socket listener.
- Visibility filters are testable and explain rejected discovery results.
- Admission decisions are still deferred to Sprint 4.

Implemented scope:

- Added `RendezvousPollResult` and `RendezvousPollStatus` models with
  JSON-safe summaries.
- Added `poll_held_stream_offers(...)` to return discoverable held stream
  offers for one explicit rendezvous request.
- Added pure request-matching and discoverability predicates.
- Added explicit `mark_stream_offers_discoverable(...)` status marking helper.
- Preserved append order, read-only polling by default, active/expired
  filtering, lane and mode filters, and visibility-tier compatibility.
- Kept lane admission policy, scenario DSL changes, delivery changes, live
  polling loops, durable queues, retry workers, sockets, DNS lookup, and real
  networking deferred.

## Sprint 4: Lane Admission Policy Helpers

Status: implemented on `v1.2/planning`.

Goal: add hub-level simulator policy for whether discovered offers can move
downward.

Candidate work:

- Add simulator-local admission policy records on RegistryHub or an adjacent
  policy module.
- Support outcomes: `pass_down`, `hold`, `deny`, `rate_limited`,
  `quarantined`, and `requires_poll`.
- Model basic firewall-like behavior without production security or DDoS
  protection claims.
- Record concise admission decision summaries for audit and snapshots.
- Keep TrafficHub routing unchanged.

Acceptance targets:

- Discovery and admission remain separate.
- Admission outcomes are deterministic and explainable.
- Denied, rate-limited, and quarantined offers do not deliver messages or
  mutate TrafficHub routes.

Implemented scope:

- Added simulator-local `LaneAdmissionPolicy`, `LaneAdmissionDecision`,
  `LaneAdmissionStatus`, and `LaneAdmissionReason` models.
- Added a pure `make_lane_admission_policy(...)` constructor and lane
  admission predicates for allowed, blocked, and terminal decisions.
- Added `evaluate_lane_admission_policy(...)` for deterministic read-only
  evaluation of a stream offer with optional rendezvous request and poll
  result context.
- Preserved explicit precedence for invalid inputs, deny lists, visibility,
  discoverability, allowed lists, and default policy status.
- Documented Sprint 4 behavior in `docs/LANE_ADMISSION_POLICY_v1_2.md`.
- Kept RegistryHub policy storage, retained decision history, scenario DSL
  changes, delivery changes, TrafficHub routing changes, live polling loops,
  durable queues, retry workers, sockets, DNS lookup, and real networking
  deferred.

## Sprint 5: Scenario DSL and Scenarios

Status: implemented on `v1.2/planning`.

Goal: expose the stable helper flow through scenario YAML after models,
queues, polling, and admission decisions are covered by focused tests.

Candidate work:

- Add scenario actions for stream offer creation, rendezvous queue retention,
  polling descent, and admission decisions.
- Add read-only assertions for held offers, poll results, and admission
  outcomes.
- Add scenarios for allowed offer, held offer, denied offer, rate-limited
  offer, and quarantined offer.
- Preserve existing mailbox delivery and encrypted delivery behavior.

Acceptance targets:

- Existing scenarios `001` through `052` continue to pass unchanged.
- New scenarios are contiguous and documented in `docs/SCENARIO_INDEX.md`
  when added.
- Scenario output clearly distinguishes discovery, admission, and delivery
  mode.

Implemented scope:

- Added scenario actions for holding stream offers, polling held offers,
  marking selected offers discoverable, and evaluating lane admission policy.
- Added read-only count-style assertions for held offers, rendezvous poll
  results, and lane admission decisions.
- Added scenarios `053` through `057` for allowed, requires-poll, denied,
  rate-limited, and quarantined stream offer outcomes.
- Added detailed snapshot visibility for `RegistryHub.held_stream_offers`.
- Kept poll results and admission decisions in scenario action results rather
  than adding retained RegistryHub admission history.
- Preserved mailbox delivery, encrypted delivery, TrafficHub routing,
  networking, live polling, durable queues, retry workers, DNS lookup,
  registrar/public CA behavior, real cryptography, and version behavior.

## Sprint 6: Snapshot, Audit Visibility, and Hardening

Status: implemented on `v1.2/planning`.

Goal: make retained offers and admission decisions inspectable without
claiming production privacy, security, or delivery guarantees.

Candidate work:

- Add any remaining detailed snapshot visibility for admission decisions if
  retained decision history becomes necessary.
- Add compact audit summaries for poll and admission results.
- Add docs and tests clarifying metadata and privacy limitations.
- Harden scenario index, metadata regression, and documentation consistency.
- Perform the v1.2 version bump only during explicit release prep.

Acceptance targets:

- Ruff, pytest, scenario runner, and CLI version checks pass.
- Version remains `darwin-sim 1.1.0` until release prep.
- Docs avoid production DDoS, anonymity, networking, DNS, registrar, public CA,
  real cryptography, TrafficHub routing, and canonical identity claims.

Implemented scope:

- Added `RegistryHub.rendezvous_poll_result_history` and
  `RegistryHub.lane_admission_decision_history` as default-empty append-order
  simulator-local histories.
- Added explicit record, query, and summarize helpers for retained poll
  results and lane admission decisions.
- Kept `poll_held_stream_offers(...)` and
  `evaluate_lane_admission_policy(...)` read-only by default.
- Updated scenario poll and admission actions to record their explicit
  outcomes while preserving scenario action results.
- Updated `rendezvous_poll_result_contains` and
  `lane_admission_decision_contains` to prefer retained RegistryHub history
  and fall back to action results when retained history is empty or
  unavailable.
- Added detailed snapshot visibility for compact retained poll and admission
  summaries alongside `held_stream_offers`; compact `world.snapshot()` remains
  unchanged.
- Documented Sprint 6 behavior in
  `docs/STREAM_OFFER_AUDIT_HISTORY_v1_2.md`.
- Preserved mailbox delivery, encrypted delivery, TrafficHub routing,
  networking, live polling, durable queues, retry workers, DNS lookup,
  registrar/public CA behavior, real cryptography, and version behavior.

## Recommended First Implementation Sprint

Start with Sprint 1: stream offer and rendezvous request models. This is the
smallest safe slice because it creates the explicit offer shape that queues,
polling, admission policy, scenarios, snapshots, and audit visibility can
reference without changing mailbox delivery, TrafficHub routing, or canonical
identity behavior.

## Intentionally Deferred Work

- Real networking, sockets, HTTP/WebSocket behavior, DNS lookup, and external
  services.
- Live polling, durable queues, retry workers, or background delivery
  services.
- Production DDoS protection, firewall guarantees, or abuse mitigation
  claims.
- Privacy, anonymity, metadata-hiding, or traffic-analysis guarantees.
- Registrar integration, public CA behavior, and production identity proof.
- Real cryptography, key exchange, production E2EE, and secure messaging
  protocols.
- TrafficHub routing changes.
- Canonical identity rewrites.
- Package publication, tagging, release creation, or version bump beyond
  `1.1.0` during planning.
