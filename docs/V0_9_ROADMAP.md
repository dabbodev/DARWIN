# DARWIN v0.9 Roadmap: Mailbox / Chat Adapter Foundations

DARWIN v0.9 planning starts from the released v0.8.0 simulator on `main`.
The planning branch is `v0.9/planning`.

Recommended theme: DARWIN Mailbox / Chat Adapter Foundations.

v0.9 should remain simulator-first. It should not become a production chat
system, secure messaging product, DNS replacement, registrar system, public
CA, real networking replacement, or production identity/compliance layer.

## Core Concept

Add a simple DARWIN-addressed mailbox/chat foundation where DARWIN handles
identity-aware mailbox registration, alias resolution, adapter binding, and
delivery explainability. Transport stays local, in-memory, or adapter-mode
only.

The release should model how a DARWIN mailbox address can resolve through
existing RegistryHub authority without changing canonical identity truth,
TrafficHub routing, real DNS, external services, or production cryptography.

## Release Boundaries

In scope:

- Simulator-local mailbox identity and resource models.
- DARWIN mailbox address strings, such as `darwin://global.chat.neo/inbox`.
- RegistryHub-backed mailbox registration and alias resolution helpers.
- Simulator-local adapter endpoint records.
- Toy in-memory message envelopes and delivery results.
- Scenario coverage for delivery success and explainable failure.
- Documentation that keeps adapter and transport behavior explicitly
  simulator-only.

Out of scope:

- Real networking, sockets, or external services.
- Production chat, secure messaging, or public mailbox service behavior.
- DNS replacement, registrar integration, or public CA behavior.
- Production identity proof, audit/compliance behavior, or production
  cryptography.
- TrafficHub routing changes.
- Canonical identity rewrites.
- Version bump beyond `0.8.0` until release prep.

## Sprint 1: Mailbox Identity and Address Models

Goal: define the smallest simulator-local mailbox shape.

Candidate work:

- Add simulator-local mailbox identity/resource models.
- Define a DARWIN mailbox address shape, such as
  `darwin://global.chat.neo/inbox`.
- Keep addresses as simulator strings, not real URLs or DNS records.
- Bind mailbox records to stable simulator identity fields without changing
  canonical device identity.
- Do not implement message delivery yet.

Acceptance targets:

- Mailbox addresses parse or validate deterministically as simulator strings.
- Mailbox records can be created in tests without opening sockets or using
  external services.
- Docs clearly state that mailbox addresses are not real URLs or DNS.

## Sprint 2: Mailbox Registration and Registry Binding Helpers

Goal: register mailbox identities through existing RegistryHub concepts.

Candidate work:

- Register mailboxes against `RegistryHub`.
- Bind mailbox identity to device/canonical identity where appropriate.
- Preserve canonical identity truth.
- Keep aliases as authorized shortcuts.
- Reuse existing alias conflict and authority language where it fits.

Acceptance targets:

- A mailbox can be registered under an authorized RegistryHub scope.
- Alias shortcuts resolve to mailbox records without replacing canonical
  identity.
- Conflict handling remains deterministic and simulator-local.

## Sprint 3: Local Adapter Endpoint Records

Goal: model how a mailbox might expose local adapter availability without
opening real transport.

Candidate work:

- Add simulator-local adapter endpoint models, such as `in_memory`,
  `loopback_placeholder`, or `websocket_placeholder`.
- Do not open real sockets.
- Do not add external services.
- Model endpoint availability and stale endpoint behavior.
- Keep adapter records separate from TrafficHub routing.

Acceptance targets:

- Tests can mark an endpoint available, unavailable, or stale.
- Delivery planning can explain unavailable or stale endpoint failures.
- Placeholder endpoint types remain inert data, not live transports.

## Sprint 4: In-Memory Message Delivery Prototype

Goal: add a toy delivery path that proves address resolution and adapter
selection without production transport.

Candidate work:

- Add toy message envelopes and in-memory mailbox delivery.
- Deliver by resolving a DARWIN mailbox address through RegistryHub.
- Keep payloads symbolic/plaintext for now.
- Return structured delivery outcomes.
- Do not add production encryption.

Acceptance targets:

- A message envelope can be delivered to an in-memory mailbox.
- Unresolved mailbox and unavailable adapter outcomes are explicit.
- Payloads are test fixtures only and are not described as secure messaging.

## Sprint 5: Delivery Audit and Scenario Examples

Goal: make delivery decisions explainable in scenario output.

Candidate work:

- Add delivery result records explaining how an address resolved and why
  delivery succeeded or failed.
- Add scenarios for successful delivery, unresolved mailbox, alias conflict or
  stale endpoint, and delivery audit.
- Keep simulator-only framing clear.
- Avoid production audit/compliance claims.

Acceptance targets:

- Scenario assertions can validate delivery success and failure reasons.
- Delivery explainability shows address, registry resolution, adapter status,
  and terminal outcome.
- Scenario index coverage remains contiguous and discoverable.

## Sprint 6: Docs, Hardening, and Release Prep

Goal: prepare a clean v0.9 release candidate only after the simulator slices
are implemented and tested.

Candidate work:

- Regression tests for mailbox registration, adapter records, delivery, and
  delivery explainability.
- Documentation polish and scenario index checks.
- Release notes and checklist updates.
- Version bump only during release prep.

Acceptance targets:

- Ruff, pytest, scenario runner, and CLI version checks pass.
- Scenario documentation distinguishes local adapter simulation from real
  networking.
- Release-facing docs state that v0.9 remains simulator-only.

## Future Encryption Planning

v1.0 may model end-to-end encrypted mailbox delivery, but DARWIN should not
invent production cryptography.

Future work should evaluate established protocol patterns such as
Signal-style asynchronous messaging, MLS for groups, HPKE-style envelopes, or
Noise-style handshakes. v0.9 should not implement production encryption.

## Recommended First Implementation Sprint

Start with Sprint 1: mailbox identity and address models. It is the smallest
slice that creates a shared vocabulary for later registration, adapter, and
delivery work without changing simulator behavior outside the new mailbox
surface.

## Intentionally Deferred Work

- Real networking and socket transport.
- Production chat service behavior.
- Production encryption or secure messaging guarantees.
- DNS replacement, registrar integration, or public CA behavior.
- Production identity proof.
- Production audit or compliance behavior.
- TrafficHub routing changes.
- Canonical identity rewrites.
- Package publication, tagging, or release creation during planning.
