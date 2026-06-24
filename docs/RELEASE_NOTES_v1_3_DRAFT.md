# DARWIN v1.3 Release Notes Draft

Status: planning draft with Sprint 1 implemented on the v1.3 planning branch.
v1.3 is unreleased. DARWIN v1.2.0 remains the latest released version on
`main` as `darwin-sim 1.2.0`. The annotated `v1.2.0` tag and GitHub release
exist:
https://github.com/dabbodev/DARWIN/releases/tag/v1.2.0. No package
publication was performed.

This file is a draft for future v1.3 release notes. It does not describe
released v1.3 behavior and should not be treated as a release announcement.

## Candidate Theme

Rendezvous lifecycle and retained stream-offer status transitions.

Future v1.3 work may explore small simulator-first slices around:

- symbolic stream-offer expiration and cleanup helpers;
- retained stream-offer status transition history;
- read-only query and summarize helpers for lifecycle audit metadata;
- scenario DSL coverage after helper behavior lands;
- release-readiness documentation after scenario coverage exists.

## Sprint 1 Draft Note

Sprint 1 adds symbolic RegistryHub-local stream-offer lifecycle transition
history:

- `StreamOfferStatusTransition` and
  `StreamOfferStatusTransitionReason` models.
- `RegistryHub.stream_offer_status_transition_history`.
- Explicit make, record, query, and summarize helpers for retained transition
  history.
- An opt-in transition recording path on `update_held_stream_offer_status(...)`
  that leaves default behavior unchanged.
- Detailed snapshot visibility for copied transition summaries while compact
  `world.snapshot()` output remains unchanged.
- Documentation in `docs/STREAM_OFFER_LIFECYCLE_HISTORY_v1_3.md`.

No scenario DSL actions or assertions were added in Sprint 1.

## Current Draft Scope

Any future v1.3 implementation should preserve:

- existing mailbox delivery behavior;
- existing encrypted delivery behavior;
- existing TrafficHub routing behavior;
- existing canonical identity behavior;
- existing v1.2 stream offer, rendezvous poll, lane admission, retained
  history, snapshot, and scenario behavior unless a later accepted sprint
  explicitly scopes a simulator-local change.

## Expected Compatibility Framing

The checked-in released scenario set remains expected to run contiguously from
`001` through `057` until new v1.3 scenarios are intentionally added.

The package and CLI version remain `darwin-sim 1.2.0` during planning.

## Non-Goals

v1.3 planning does not add:

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
- version bumps beyond `1.2.0` during planning.

## Release Readiness

Not started. Before any future v1.3 release, this placeholder should be
replaced with a concrete implementation summary, scenario coverage, validation
results, compatibility notes, and final release status.
