# DARWIN v1.1 Roadmap: Symbolic Encrypted Delivery Policy Integration

DARWIN v1.1 planning starts from the released v1.0.0 simulator on `main`.
The planning branch is `v1.1/planning`. During release prep, the current
branch package and CLI version have been updated to `darwin-sim 1.1.0`.

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
- Version bump beyond `1.1.0`.

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

Status: implemented on `v1.1/planning`.

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

Implemented scope:

- `EncryptedDeliveryGateDecision`, `EncryptedDeliveryGateStatus`, and
  `EncryptedDeliveryGateReason` model opt-in symbolic gate outcomes.
- `evaluate_encrypted_delivery_request_policy(...)` evaluates an
  `EncryptedDeliveryRequest` against registered mailbox encryption policy
  without calling `deliver_message_to_mailbox(...)`.
- Gate decisions wrap the existing `EncryptionPolicyDecision` summary when
  registered policy evaluation runs.
- `retain_decision` controls the existing
  `RegistryHub.encryption_policy_decision_history` behavior. Sprint 2 does
  not add separate persistent gate-decision history.
- Pure gate predicates expose allowed and blocked outcomes without mutation.
- Existing plaintext delivery, message inboxes, retained message delivery
  results, TrafficHub routing, canonical identity, and scenario DSL behavior
  remain unchanged.

See `docs/ENCRYPTED_DELIVERY_POLICY_GATE_v1_1.md`.

## Sprint 3: Encrypted Delivery Result and Audit Metadata

Status: implemented on `v1.1/planning`.

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

Implemented scope:

- `EncryptedDeliveryResult`, `EncryptedDeliveryResultStatus`, and
  `EncryptedDeliveryAuditEntry` model wrapped symbolic encrypted delivery
  outcomes and compact audit metadata.
- `evaluate_encrypted_delivery_request(...)` evaluates the Sprint 2 gate and
  defaults to `attempt_delivery=False`, so allowed requests are reported as
  not delivered unless the caller explicitly opts into delivery.
- When `attempt_delivery=True` and the gate allows delivery, the wrapper calls
  the existing `deliver_message_to_mailbox(...)` helper with the request's
  base `MessageEnvelope` and attaches the resulting `MessageDeliveryResult`.
- Blocked and policy-check-only requests do not mutate inboxes or retained
  message delivery results.
- `retain_policy_decision` passes through to the existing retained
  `EncryptionPolicyDecision` history. Sprint 3 does not add persistent
  wrapped-result history.
- Existing plaintext delivery, message inboxes, retained message delivery
  results, TrafficHub routing, canonical identity, and scenario DSL behavior
  remain unchanged unless the new opt-in wrapper is used.

See `docs/ENCRYPTED_DELIVERY_RESULTS_v1_1.md`.

## Sprint 4: Scenario DSL and Scenarios

Status: implemented on `v1.1/planning`.

Implemented work:

- Added `evaluate_encrypted_delivery_request` as an opt-in scenario action for
  helper-level symbolic encrypted delivery requests and wrapped results.
- Added read-only `encrypted_delivery_result_contains` and
  `encrypted_delivery_audit_contains` assertions.
- Added scenarios `050` through `052` for policy-check-only, gate-allowed
  no-attempt, gate-allowed explicit delivery, and gate-blocked no-delivery
  paths.
- Preserve existing v0.9 plaintext delivery scenarios and v1.0 symbolic policy
  scenarios.

Acceptance targets:

- Scenario coverage demonstrates accepted and rejected opt-in gates.
- The scenario index remains contiguous through `052`.
- Existing scenarios `001` through `049` continue to pass unchanged.

## Sprint 5: Retained Wrapped Result History and Snapshot Visibility

Status: implemented on `v1.1/planning`.

Goal: retain compact wrapped encrypted delivery result history on each
`RegistryHub`, make it queryable, expose it in detailed snapshots, and keep
symbolic-only behavior clear.

Implemented work:

- Added `RegistryHub.encrypted_delivery_result_history` with deterministic
  append-order retention.
- Updated `evaluate_encrypted_delivery_request(...)` to retain one wrapped
  `EncryptedDeliveryResult` by default, with `retain_result=False` for
  no-retention helper usage.
- Added read-only `query_encrypted_delivery_results(...)` filters over
  retained wrapped results.
- Updated encrypted delivery scenario assertions to prefer retained history and
  fall back to scenario action results only when retained history is
  unavailable or empty.
- Added detailed snapshot visibility at
  `registry_hubs.<hub_id>.encrypted_delivery_result_history`.
- Preserved compact `world.snapshot()` behavior.
- Kept plaintext delivery, TrafficHub routing, canonical identity, inbox, and
  normal message delivery result behavior unchanged except for explicit
  `attempt_delivery=True` calls through the existing delivery helper.

Acceptance targets:

- Wrapped results are queryable from retained RegistryHub history.
- Detailed snapshots expose concise symbolic wrapped-result summaries.
- Docs avoid production cryptography, E2EE, networking, DNS, registrar, public
  CA, external-service, durable-queue, TrafficHub, or canonical identity
  claims.

See `docs/ENCRYPTED_DELIVERY_RESULT_HISTORY_v1_1.md`.

## Sprint 6: Release-Candidate Hardening and Release Prep

Status: implemented on `v1.1/planning` as release-candidate hardening. v1.1
remains unreleased release-prep work and the package/CLI version is
`darwin-sim 1.1.0`.

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
- Version reports `darwin-sim 1.1.0` during release prep.
- Release-facing docs remain clear that v1.1 is simulator-only symbolic policy
  integration.

Implemented scope:

- Audited encrypted delivery request, policy gate, wrapped result, scenario
  DSL, assertion, retained history, and detailed snapshot behavior against the
  v1.1 simulator-only boundaries.
- Added draft release notes at `docs/RELEASE_NOTES_v1_1_DRAFT.md`.
- Confirmed the checked-in scenario index and scenario metadata coverage for
  scenarios `001` through `052`.
- Preserved existing plaintext delivery, compact snapshot, TrafficHub routing,
  canonical identity, and version behavior.
- Completed the release-prep version bump to `darwin-sim 1.1.0` without
  merging, tagging, creating a GitHub release, or publishing packages.

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
- Package publication, tagging, release creation, or version bump beyond
  `1.1.0`.
