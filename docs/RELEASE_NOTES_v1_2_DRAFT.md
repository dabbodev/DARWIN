# DARWIN v1.2.0 Release Notes

Status: released on `main` as `darwin-sim 1.2.0`. The annotated `v1.2.0` tag
and GitHub release exist:
https://github.com/dabbodev/DARWIN/releases/tag/v1.2.0. No package
publication was performed.

DARWIN v1.2 adds simulator-local pull-based lane rendezvous and stream offer
admission modeling. It introduces stream offer records, RegistryHub-local
held offer queues, private polling descent helpers, lane admission policy
decisions, scenario DSL coverage, retained audit histories, and detailed
snapshot visibility for those records.

This is symbolic simulator metadata flow only. It is not real networking, not
a network service, not production DDoS protection, not a firewall, not a
privacy or anonymity system, and not real cryptography or production E2EE.

## Sprint Summary

Sprint 1 added stream offer and rendezvous request models:

- `StreamOffer`, `StreamOfferStatus`, `StreamOfferMode`, and
  `StreamOfferVisibility`.
- `RendezvousRequest` metadata for one explicit polling request.
- Deterministic constructors, status predicates, validation, and JSON-safe
  summaries.
- Documentation in `docs/STREAM_OFFERS_v1_2.md`.

Sprint 2 added RegistryHub-local held stream offer queues:

- `RegistryHub.held_stream_offers` in-memory storage.
- Helpers to hold, get, query, update, and summarize held stream offers.
- Deterministic append order, duplicate handling, replacement behavior, and
  read-only query filters.
- Documentation in `docs/RENDEZVOUS_OFFER_QUEUES_v1_2.md`.

Sprint 3 added private polling descent helpers:

- `RendezvousPollResult` and `RendezvousPollStatus`.
- `poll_held_stream_offers(...)` for one explicit simulator poll request.
- Visibility, scope, lane, mode, active, and expiration matching helpers.
- Explicit `mark_stream_offers_discoverable(...)` status updates.
- Documentation in `docs/PRIVATE_POLLING_DESCENT_v1_2.md`.

Sprint 4 added lane admission policy helpers:

- `LaneAdmissionPolicy`, `LaneAdmissionDecision`,
  `LaneAdmissionStatus`, and `LaneAdmissionReason`.
- Pure lane admission evaluation with deterministic precedence.
- Outcomes for pass-down, hold, deny, rate-limited, quarantined, and
  requires-poll decisions.
- Documentation in `docs/LANE_ADMISSION_POLICY_v1_2.md`.

Sprint 5 added scenario DSL coverage and checked-in scenarios:

- Scenario actions for holding stream offers, polling held offers, marking
  offers discoverable, and evaluating admission policy.
- Read-only assertions for held offers, rendezvous poll results, and lane
  admission decisions.
- Scenarios `053` through `057` for allowed, held/requires-poll, denied,
  rate-limited, and quarantined symbolic outcomes.
- Detailed snapshot visibility for held stream offers.

Sprint 6 added retained audit history and hardening:

- `RegistryHub.rendezvous_poll_result_history`.
- `RegistryHub.lane_admission_decision_history`.
- Explicit record, query, and summarize helpers for retained poll results and
  admission decisions.
- Scenario assertions that prefer retained RegistryHub histories before
  falling back to action results.
- Detailed snapshot visibility for held offers, retained poll history, and
  retained admission history while compact `world.snapshot()` remains
  unchanged.
- Documentation in `docs/STREAM_OFFER_AUDIT_HISTORY_v1_2.md`.

## Compatibility

- Existing mailbox delivery behavior remains unchanged.
- Existing encrypted delivery behavior remains unchanged.
- Existing TrafficHub routing behavior remains unchanged.
- Existing alias, identity, scenario, snapshot, and retained-history behavior
  remains unchanged outside the explicit v1.2 stream offer surfaces.
- The checked-in scenario set is expected to remain contiguous from `001`
  through `057`.
- The released package and CLI version are `darwin-sim 1.2.0`.
- The annotated `v1.2.0` tag and GitHub release exist.
- No package publication was performed.

## Scenario Coverage

v1.2 scenarios:

- `scenarios/053_stream_offer_rendezvous_allowed.yaml`
- `scenarios/054_stream_offer_rendezvous_held.yaml`
- `scenarios/055_stream_offer_rendezvous_denied.yaml`
- `scenarios/056_stream_offer_rendezvous_rate_limited.yaml`
- `scenarios/057_stream_offer_rendezvous_quarantined.yaml`

These scenarios validate simulator-local stream offer retention, private
polling, retained poll history, lane admission decisions, retained admission
history, and detailed snapshot visibility. They do not deliver messages,
change TrafficHub routes, open sockets, perform DNS lookup, contact external
services, generate keys, encrypt payloads, or enforce production security.

## Current Limitations

- Held stream offers are in-memory and RegistryHub-local.
- Retained poll and admission histories are in-memory simulator audit
  metadata, not production logs.
- Private polling descent is one explicit helper call, not live polling or a
  background service.
- Lane admission policy is symbolic and deterministic; it is not production
  firewalling, DDoS mitigation, privacy protection, or access control.
- Rendezvous layers and retained histories may expose modeled metadata such
  as requester IDs, polling hub IDs, target handles, target scopes, lane
  signatures, visibility tiers, statuses, reasons, matched offer IDs, and
  JSON-safe scenario metadata.

## Non-Goals

v1.2 does not add:

- real networking;
- sockets;
- HTTP or WebSocket behavior;
- DNS lookup;
- registrar integration;
- public CA behavior;
- external services;
- live polling loops;
- durable queues;
- retry workers;
- production DDoS guarantees;
- production firewall guarantees;
- production privacy guarantees;
- production anonymity guarantees;
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
- package publication;
- version bumps beyond `1.2.0`.

## Release Readiness

The v1.2.0 release is complete after full validation, merge to `main`,
annotated tag creation, and GitHub release publication. Final validation
passed `python -m ruff check .`, `python -m pytest` with 777 tests,
`python scripts/run_all_scenarios.py` for scenarios `001` through `057`, and
`python -m darwin.cli.main --version` reporting `darwin-sim 1.2.0`. Package
publication was intentionally not performed.
