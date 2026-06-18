# DARWIN v1.1 Roadmap: Symbolic Encrypted Delivery Policy Integration

DARWIN v1.1 planning starts from the released v1.0.0 simulator on `main`.
The planning branch is `v1.1/planning`. The current package and CLI version
must remain `darwin-sim 1.0.0` until explicit release prep.

Recommended theme: Symbolic Encrypted Delivery Policy Integration.

v1.1 should remain simulator-first. It should not become a production secure
messenger, cryptographic library, Signal replacement, MLS implementation,
certificate authority, registrar, DNS replacement, or external network
service.

## Core Concept

Connect v1.0 symbolic encryption policy decisions to v0.9 mailbox delivery in
a controlled, opt-in simulator mode.

Existing plaintext delivery behavior must remain unchanged unless an explicit
symbolic encryption policy gate is requested. v1.1 should model policy
integration, audit semantics, and delivery gating only. It should not add real
cryptography, key generation, private key storage, encryption/decryption,
networking, DNS lookup, registrar integration, public CA behavior, external
services, durable queues, retry workers, TrafficHub routing changes, or
canonical identity rewrites.

## Release Boundaries

In scope:

- Helper-level symbolic delivery request records.
- Explicit opt-in symbolic encryption policy gate helpers.
- Deterministic delivery-gate decisions before mailbox delivery.
- Result or wrapper metadata that records symbolic policy checks.
- Scenario DSL coverage after helper behavior is stable.
- Compact detailed snapshot visibility if it follows existing conventions.
- Documentation and release-candidate hardening.

Out of scope:

- Real cryptography or custom cryptographic primitives.
- Production E2EE or secure messenger behavior.
- Signal, MLS, HPKE, Noise, CA, registrar, or DNS implementation.
- Key generation, private key storage, secret material, encryption, or
  decryption.
- Real networking, sockets, HTTP/WebSocket behavior, DNS lookup, or external
  services.
- Durable queues, retry workers, or background delivery services.
- Default enforcement inside existing plaintext delivery helpers.
- TrafficHub routing changes.
- Canonical identity rewrites.
- Version bump beyond `1.0.0` before explicit release prep.

## Sprint 1: Symbolic Encrypted Delivery Request Model

Status: implemented on `v1.1/planning`.

Goal: introduce a helper-level delivery request model that can carry either a
plaintext message envelope or symbolic encrypted envelope metadata.

Candidate work:

- Add a small delivery request record for simulator-local mailbox delivery
  experiments.
- Allow the request to reference a v0.9 plaintext message envelope or v1.0
  symbolic encrypted envelope metadata.
- Keep the request separate from existing `deliver_message_to_mailbox(...)`.
- Preserve existing delivery semantics and existing mailbox inbox behavior.
- Do not add scenario DSL changes until helper behavior is stable.

Acceptance targets:

- Plaintext delivery helpers continue to work unchanged.
- Request summaries are deterministic and JSON-safe.
- No helper performs encryption, decryption, key generation, networking, or
  mailbox mutation by itself.

Implemented scope:

- `EncryptedDeliveryRequest`, `EncryptedDeliveryRequestMode`, and
  `EncryptedDeliveryRequestStatus` model request intent separately from
  mailbox delivery.
- Pure constructors cover plaintext, symbolic encrypted, and
  policy-check-only request records.
- Pure predicates expose plaintext, symbolic encrypted, policy-required, and
  structural status checks without evaluating policy or delivering messages.
- The request layer preserves message envelope lane signatures, keeps
  summaries JSON-safe, and does not mutate message envelopes, symbolic
  encrypted envelope metadata, `RegistryHub`, or in-memory inbox state.

See `docs/ENCRYPTED_DELIVERY_REQUESTS_v1_1.md`.

## Sprint 2: Opt-In Encrypted Delivery Policy Gate

Goal: add an explicit helper that evaluates registered mailbox encryption
policy before delivery.

Candidate work:

- Resolve registered mailbox encryption policy state from a `RegistryHub`.
- Evaluate the v1.0 symbolic encryption policy decision for the request.
- Return a deterministic gate decision before any delivery helper is called.
- Keep policy enforcement opt-in; do not enforce policy in existing delivery
  helpers by default.
- Keep missing envelope, unsupported profile, missing binding, inactive
  identity, unusable key bundle, and plaintext fallback outcomes deterministic.

Acceptance targets:

- Gate decisions are stable and explain accepted or rejected delivery attempts.
- Existing plaintext delivery tests and scenarios remain unchanged when no
  policy gate is requested.
- No real cryptography or external service behavior is introduced.

## Sprint 3: Encrypted Delivery Result and Audit Metadata

Goal: extend or wrap delivery results with symbolic encryption decision
summaries.

Candidate work:

- Add a wrapper result that can include the policy gate decision and the
  underlying delivery result when delivery proceeds.
- Track whether symbolic policy was checked, accepted, or rejected.
- Preserve v0.9 delivery result records and inbox behavior.
- Avoid durable queues, retry workers, background processing, or external
  delivery state.

Acceptance targets:

- Accepted gated delivery can expose both policy and delivery summaries.
- Rejected gated delivery records a symbolic rejection without mutating inboxes.
- Existing retained delivery result behavior remains unchanged unless the new
  opt-in wrapper is used.

## Sprint 4: Scenario DSL and Scenarios

Goal: add scenario actions and assertions only after helper-level behavior is
stable.

Candidate work:

- Add explicit scenario actions for opt-in symbolic encrypted delivery gating.
- Add read-only assertions for gate decisions and wrapped delivery outcomes.
- Add scenarios proving symbolic encrypted delivery accepted, missing envelope
  rejected, unsupported profile rejected, and plaintext delivery remains
  unchanged when no policy gate is requested.
- Preserve existing v0.9 plaintext delivery scenarios and v1.0 symbolic policy
  scenarios.

Acceptance targets:

- Scenario coverage demonstrates accepted and rejected opt-in gates.
- The scenario index remains contiguous and current.
- Existing scenarios `001` through `049` continue to pass unchanged.

## Sprint 5: Snapshot Visibility and Docs Hardening

Goal: make symbolic encrypted delivery gate decisions inspectable without
implying production security behavior.

Candidate work:

- Add compact detailed snapshot visibility for symbolic encrypted delivery
  gate decisions, if useful and consistent with existing conventions.
- Preserve compact `world.snapshot()` behavior unless existing conventions say
  otherwise.
- Keep docs explicit about symbolic-only semantics.
- Document that plaintext delivery behavior remains unchanged unless a gate is
  requested.

Acceptance targets:

- Detailed snapshots or result exports expose concise symbolic gate summaries.
- Docs avoid production cryptography, E2EE, networking, DNS, registrar, public
  CA, external-service, durable-queue, TrafficHub, or canonical identity
  claims.

## Sprint 6: Release-Candidate Hardening and Release Prep

Goal: harden the v1.1 planning line after implementation slices are complete.

Candidate work:

- Regression tests for request models, gate helpers, result wrappers,
  scenario actions, assertions, and snapshot visibility.
- Documentation polish and scenario index checks.
- Full validation with Ruff, pytest, scenario runner, and CLI version checks.
- Version bump only during explicit release prep.

Acceptance targets:

- Ruff, pytest, scenario runner, and CLI version checks pass.
- Scenario set remains contiguous.
- Version remains `darwin-sim 1.0.0` until release prep.
- Release-facing docs remain clear that v1.1 is simulator-only symbolic policy
  integration.

## Future Real Crypto Adapter Considerations

DARWIN should not invent production cryptography.

Future work may evaluate established protocol or library patterns such as
Signal-style asynchronous messaging, MLS for groups, HPKE-style envelopes, or
Noise-style handshakes. v1.1 should not implement those protocols.

v1.1 should model policy integration, audit semantics, and delivery gating
only. Any future real-crypto adapter work should be separately scoped, use
reviewed libraries or protocols, and avoid custom cryptographic primitives.

## Recommended First Implementation Sprint

Start with Sprint 1: symbolic encrypted delivery request model. This is the
smallest useful slice because it creates the explicit request shape that later
policy gates, result wrappers, scenarios, and snapshot visibility can reference
without changing existing plaintext delivery helpers.

## Intentionally Deferred Work

- Real cryptography and production E2EE.
- Custom cryptographic primitives.
- Signal, MLS, HPKE, Noise, CA, registrar, or DNS implementation.
- Key generation, private key storage, secret material, encryption, or
  decryption.
- Production secure messenger behavior.
- Real networking, sockets, HTTP/WebSocket behavior, DNS lookup, and external
  services.
- Durable delivery queues, retry workers, and background services.
- Default enforcement inside existing plaintext delivery helpers.
- TrafficHub routing changes.
- Canonical identity rewrites.
- Package publication, tagging, release creation, or version bump during
  planning.
