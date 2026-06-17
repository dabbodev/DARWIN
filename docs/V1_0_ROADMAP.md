# DARWIN v1.0 Roadmap: Encrypted Mailbox Model Foundations

DARWIN v1.0 planning starts from the released v0.9.0 simulator on `main`.
The planning branch is `v1.0/planning`. The current package and CLI version
remain `darwin-sim 0.9.0` until explicit release-prep work.

Recommended theme: Encrypted Mailbox Model Foundations.

v1.0 should remain simulator-first. It should not become a production secure
messenger, cryptographic library, Signal replacement, MLS implementation,
certificate authority, registrar, DNS replacement, or external network
service.

## Core Concept

Model how DARWIN mailbox identities bind to encryption identities, key bundle
records, encrypted-envelope metadata, and delivery policy.

DARWIN should not invent cryptography. v1.0 should use symbolic key material
and symbolic envelope state only. If future real crypto adapters are ever
scoped, they should use established libraries and protocols rather than
hand-rolled cryptographic primitives.

## Release Boundaries

In scope:

- Simulator-local encryption identity records.
- Symbolic key bundle reference records.
- Mailbox-to-encryption-identity binding semantics.
- Symbolic encrypted envelope metadata.
- Mailbox encryption delivery policy helpers.
- Scenario DSL coverage after helper-level models are stable.
- Compact deterministic snapshot and audit visibility.
- Documentation and release-prep hardening.

Out of scope:

- Real cryptography or custom cryptographic primitives.
- Production encryption or E2EE guarantees.
- Production chat or secure messenger behavior.
- Signal, MLS, HPKE, Noise, or public CA implementation.
- Real networking, sockets, HTTP/WebSocket clients or servers.
- DNS lookup, DNS replacement, registrar integration, or external services.
- Durable queues, retry workers, or background delivery.
- TrafficHub routing changes.
- Canonical identity rewrites.
- Version bump beyond `0.9.0` before release prep.

## Sprint 1: Encryption Identity and Key Reference Models

Status: implemented on the v1.0 planning branch.

Goal: define simulator-local records that let mailbox identities reference
encryption identities without performing cryptography.

Candidate work:

- Add simulator-local encryption identity records. Implemented in
  `darwin.models.encryption`.
- Add key bundle reference models. Implemented in
  `darwin.models.encryption`.
- Bind mailbox identity to encryption identity. Implemented as a pure
  `MailboxEncryptionBinding` model and helper, without RegistryHub mutation.
- Use symbolic key material only.
- Keep key IDs, bundle IDs, and profile names deterministic and JSON-safe.
- Do not implement encryption algorithms.

Acceptance targets:

- Mailbox records can reference an encryption identity without changing
  canonical device identity.
- Key bundle records summarize symbolic public key references without fake
  private key handling.
- Duplicate, missing, disabled, or stale key bundle cases are deterministic.
- Tests prove records are simulator-local data only.

Sprint 1 documentation: `docs/ENCRYPTION_IDENTITIES_v1_0.md`.

## Sprint 2: Encrypted Envelope Metadata Model

Status: implemented on the v1.0 planning branch.

Goal: represent encrypted delivery state symbolically, not cryptographically.

Candidate work:

- Add symbolic encrypted message envelope records. Implemented as
  `SymbolicEncryptedMessageEnvelope`.
- Track plaintext versus ciphertext state symbolically. Implemented as
  `EncryptedEnvelopeMetadata` with controlled `EncryptionState` labels.
- Model algorithm/profile labels, such as `symbolic_e2ee_v1`. Implemented with
  symbolic `profile`, `algorithm_ref`, `ciphertext_ref`, and optional
  `plaintext_ref` fields.
- Keep payload fields test-only and clearly non-secret.
- Do not implement encryption algorithms.

Acceptance targets:

- Envelope summaries distinguish plaintext test payloads from symbolic
  ciphertext references.
- Algorithm/profile labels validate deterministically.
- No helper produces real ciphertext, keys, signatures, or authentication
  tags.
- Existing plaintext toy delivery scenarios remain valid.

Sprint 2 documentation: `docs/ENCRYPTED_ENVELOPES_v1_0.md`.

## Sprint 3: Mailbox Encryption Policy Helpers

Status: implemented on the v1.0 planning branch.

Goal: model delivery policy decisions for encrypted-required lanes.

Candidate work:

- Model whether a mailbox requires encrypted delivery for a lane. Implemented
  as pure `MailboxEncryptionPolicy` records and lane-required predicates.
- Add policy outcomes for missing envelope metadata, missing or inactive
  identity, missing or unusable key bundle, unsupported profile, plaintext
  fallback, and not-ready envelope metadata.
- Keep delivery helper behavior simulator-local. Sprint 3 does not call or
  alter `deliver_message_to_mailbox(...)`.
- Preserve v0.9 mailbox delivery semantics for plaintext toy paths.

Acceptance targets:

- Policy helpers return deterministic accepted, plaintext-allowed, or rejected
  symbolic outcomes.
- Missing, stale, disabled, or unsupported encryption setup is visible in
  `EncryptionPolicyDecision` summaries.
- No networking, retry worker, durable queue, or production encryption behavior
  is introduced.

Sprint 3 documentation: `docs/ENCRYPTION_POLICY_v1_0.md`.

## Sprint 4: RegistryHub-Local Encryption Registry Helpers

Status: implemented on the v1.0 planning branch.

Goal: store symbolic encryption identities, key bundle references, mailbox
encryption bindings, and mailbox encryption policies on `RegistryHub` without
changing delivery behavior.

Candidate work:

- Add RegistryHub-local dictionaries for encryption identity, key bundle,
  mailbox encryption binding, and mailbox encryption policy records.
- Add registry helper functions to register, retrieve, list, and filter those
  records deterministically.
- Validate small useful cross-references, including registered mailboxes,
  registered encryption identities, and registered key bundle references.
- Add helper-level registered policy evaluation that resolves RegistryHub
  records and calls `evaluate_mailbox_encryption_policy(...)`.
- Preserve existing v0.9 delivery behavior and avoid scenario DSL changes.

Acceptance targets:

- RegistryHub construction still defaults all encryption registries to empty.
- Duplicate registration replaces records by deterministic registry key.
- Registered policy evaluation returns deterministic symbolic decisions
  without mutating delivery inboxes, retained results, mailbox state, lane
  registries, adapter endpoints, aliases, TrafficHub state, or canonical
  identity.
- Existing scenarios `001` through `046` continue to pass unchanged.

Sprint 4 documentation: `docs/ENCRYPTION_REGISTRY_v1_0.md`.

## Sprint 5: Scenario DSL and Scenarios for Symbolic Encrypted Delivery

Status: implemented on the v1.0 planning branch.

Goal: expose symbolic encrypted-delivery decisions only after helper models are
stable.

Candidate work:

- Add scenario actions/assertions for encryption identities and key bundle
  references after helper-level models are stable. Implemented as
  symbolic-only scenario DSL actions and read-only assertions.
- Add scenarios proving encrypted-required delivery succeeds or fails
  symbolically. Implemented as scenarios `047` through `049`.
- Preserve existing plaintext toy delivery scenarios.
- Keep scenario outputs deterministic and JSON-safe.

Acceptance targets:

- New scenarios demonstrate symbolic registry setup, encrypted-required
  success, missing envelope, unsupported profile, and inactive identity
  outcomes.
- Assertions read RegistryHub records or scenario action results and do not
  mutate state.
- Existing scenarios `001` through `046` continue to pass unchanged, and the
  current planning scenario set is contiguous through `049`.

Sprint 5 documentation: `docs/SCENARIO_DSL_v0_2.md`.

## Sprint 6: Audit and Snapshot Visibility

Status: implemented on the v1.0 planning branch.

Goal: make encrypted mailbox model state inspectable without implying real
secret handling.

Candidate work:

- Add compact visibility for encryption identity records. Implemented for
  RegistryHub-local encryption registry records in Sprint 4.
- Add compact visibility for policy decisions. Implemented as
  `RegistryHub.encryption_policy_decision_history`.
- Add read-only retained decision queries. Implemented as
  `query_encryption_policy_decisions(...)`.
- Do not expose fake secrets as real secrets.
- Keep output JSON-safe and deterministic.

Acceptance targets:

- Detailed snapshots expose encryption identity, key bundle, mailbox
  encryption binding, mailbox encryption policy, and retained policy-decision
  summaries.
- Compact `world.snapshot()` remains stable unless explicitly scoped.
- Output uses symbolic labels and references rather than secret-like values.

Sprint 4 already adds detailed snapshot visibility for RegistryHub-local
encryption registries. Sprint 6 adds retained policy-decision visibility after
scenario DSL behavior is scoped.

Sprint 6 documentation:
`docs/ENCRYPTION_POLICY_DECISIONS_v1_0.md`.

## Sprint 7: Docs, Hardening, and Release Prep

Status: implemented on the v1.0 planning branch as release-candidate
hardening; v1.0 remains unreleased and the version remains
`darwin-sim 0.9.0`.

Goal: polish the v1.0 planning line without expanding scope.

Candidate work:

- Regression tests for new records, helpers, scenario actions, and assertions.
- Docs polish for simulator-only encrypted mailbox modeling.
- Scenario index checks and scenario coverage validation.
- Draft release notes in `docs/RELEASE_NOTES_v1_0_DRAFT.md`.
- Version bump only during explicit future release prep.

Acceptance targets:

- Ruff, pytest, scenario runner, and CLI version checks pass.
- Scenario set remains contiguous.
- Docs avoid production secure messaging, custom cryptography, real networking,
  DNS, registrar, public CA, or external-service claims.
- Version remains `darwin-sim 0.9.0` until release prep explicitly changes it.

## Future Real Crypto Adapter Considerations

DARWIN should not invent production cryptography.

Future work may evaluate established patterns or libraries such as
Signal-style asynchronous messaging, MLS for groups, HPKE-style envelopes, or
Noise-style handshakes. v1.0 should not implement those protocols.

The v1.0 scope should model identity/key binding, policy decisions, symbolic
encrypted-envelope metadata, and audit semantics only.

## Recommended First Implementation Sprint

Start with Sprint 1: encryption identity and key reference models. This is the
smallest useful slice because it creates stable identity and key-bundle
references before envelope metadata, policy helpers, scenario DSL, or audit
visibility depend on them.

## Intentionally Deferred Work

- Real cryptography and production E2EE.
- Custom cryptographic primitives.
- Production secure messenger behavior.
- Signal, MLS, HPKE, Noise, CA, registrar, or DNS implementation.
- Real networking, sockets, HTTP/WebSocket behavior, and external services.
- Durable delivery queues, retry workers, and background services.
- TrafficHub routing changes.
- Canonical identity rewrites.
- Package publication, tagging, or release creation during planning.
