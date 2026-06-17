# DARWIN Mailbox Encryption Policy v1.0

Status: v1.0 planning on `v1.0/planning`; current package and CLI version
remains `darwin-sim 0.9.0`.

DARWIN v1.0 Sprint 3 adds simulator-local mailbox encryption policy helpers.
These helpers decide whether a mailbox lane requires symbolic encrypted
envelope metadata and whether the supplied symbolic identity, key bundle, and
envelope metadata satisfy that requirement.

This is helper-level policy evaluation only. Sprint 3 does not encrypt,
decrypt, generate keys, change delivery behavior, add scenario DSL support, or
implement production E2EE.

## Purpose

`MailboxEncryptionPolicy` records describe a mailbox-local encryption
requirement for one or more lane signatures. A common policy can require
symbolic encryption for `basic_messaging:v1` while leaving unrelated lanes
outside the requirement.

Policy summaries include:

- `policy_id`
- `mailbox_id`
- `required_for_lanes`
- `allowed_profiles`
- `require_active_identity`
- `require_usable_key_bundle`
- `allow_plaintext_fallback`
- `metadata`

The default allowed profile is `symbolic_e2ee_v1`. It is a simulator label
only. It is not a cipher, key exchange, protocol, or security guarantee.

## Policy Decisions

`EncryptionPolicyDecision` records are returned by
`evaluate_mailbox_encryption_policy(...)`. They summarize the outcome without
mutating messages, mailboxes, registries, hubs, inboxes, or retained delivery
results.

Decision summaries include:

- `policy_id`
- `mailbox_id`
- `lane_signature`
- `message_id`
- `status`
- `reason`
- `encryption_required`
- `envelope_accepted`
- `profile`
- `encryption_identity_id`
- `key_bundle_id`
- `metadata`

Decision statuses include `accepted`, `plaintext_allowed`,
`missing_envelope`, `needs_encryption`, `missing_identity`,
`missing_key_bundle`, `unsupported_profile`, `identity_inactive`,
`key_bundle_unusable`, and `envelope_not_ready`.

## Relationship to Encryption Identities

Sprint 1 introduced `EncryptionIdentity`, `KeyBundleReference`, and
`MailboxEncryptionBinding`.

Sprint 3 policy helpers can require:

- an active `EncryptionIdentity`;
- a usable `KeyBundleReference`;
- envelope metadata that references the same symbolic profile family.

These checks are record-state checks only. They do not prove ownership,
validate certificates, verify signatures, derive shared secrets, or inspect
key material.

## Relationship to Symbolic Encrypted Envelopes

Sprint 2 introduced `EncryptedEnvelopeMetadata` and
`SymbolicEncryptedMessageEnvelope`.

Sprint 3 evaluates envelope metadata by checking:

- whether the lane requires symbolic encryption;
- whether envelope metadata is present;
- whether the envelope profile is allowed by policy;
- whether the envelope state is `symbolically_encrypted`;
- whether the envelope is ready for future delivery-policy use.

The evaluator does not create ciphertext, hide payloads, transform message
content, or unwrap encrypted data.

## Relationship to v0.9 Mailbox Delivery

v0.9 mailbox delivery remains a toy, in-memory, RegistryHub-local simulator
path. Sprint 3 does not call `deliver_message_to_mailbox(...)`, does not
append to mailbox inboxes, does not retain message delivery results, and does
not change lane fallback behavior.

Existing plaintext delivery scenarios remain valid. A policy decision can be
computed by tests or future layers, but Sprint 3 does not force plaintext
delivery to fail.

## Lane-Specific Example

```python
policy = make_mailbox_encryption_policy(
    policy_id="policy_mailbox_neo",
    mailbox_id="mailbox_neo",
    required_for_lanes=("basic_messaging:v1",),
)

decision = evaluate_mailbox_encryption_policy(
    policy,
    lane_signature="basic_messaging:v1",
    message_id="msg_001",
    envelope_metadata=envelope_metadata,
    encryption_identity=identity,
    key_bundle=key_bundle,
)
```

If the lane is not listed in `required_for_lanes`, the helper returns
`plaintext_allowed` with `encryption_required` set to `False`.

## Policy Outcomes

Missing envelope:

- Required lane, no envelope metadata, and no plaintext fallback returns
  `missing_envelope`.

Unsupported profile:

- Envelope metadata whose `profile` is not in `allowed_profiles` returns
  `unsupported_profile`.

Missing or inactive identity:

- If `require_active_identity` is true and no identity is supplied, the helper
  returns `missing_identity`.
- If an identity is supplied but not active, the helper returns
  `identity_inactive`.

Missing or unusable key bundle:

- If `require_usable_key_bundle` is true and no key bundle is supplied, the
  helper returns `missing_key_bundle`.
- If a key bundle is supplied but not active, the helper returns
  `key_bundle_unusable`.

Not-ready envelope:

- If symbolic envelope metadata fails the readiness predicate after the
  identity and key bundle checks pass, the helper returns
  `envelope_not_ready`.

Plaintext fallback:

- If `allow_plaintext_fallback` is true, a required lane without envelope
  metadata returns `plaintext_allowed` with reason
  `plaintext_fallback_allowed`.

## Why This Is Helper-Level Only

Sprint 3 keeps policy evaluation as pure dataclass input and output. That gives
future scenario DSL and delivery-policy work stable statuses and summaries
without changing the v0.9 delivery surface.

Policy helpers do not mutate:

- `RegistryHub`;
- `TrafficHub`;
- mailbox records;
- message envelopes;
- symbolic envelope metadata;
- encryption identities;
- key bundle references;
- in-memory inboxes;
- retained delivery results.

## Future Integration

Future v1.0 sprints may wire these decisions into scenario DSL actions,
scenario assertions, retained audit visibility, snapshots, or explicit
delivery-policy checks.

Those layers should continue to treat Sprint 3 decisions as symbolic simulator
records until production cryptography is separately scoped and reviewed.

Sprint 4 adds RegistryHub-local encryption registry helpers and
`evaluate_registered_mailbox_encryption_policy(...)`, which resolves stored
identity, key bundle, binding, and policy records before calling this pure
evaluator. It remains helper-level only and does not alter delivery behavior.
See `docs/ENCRYPTION_REGISTRY_v1_0.md`.

Sprint 5 wires registered policy evaluation into scenario YAML through the
symbolic-only `evaluate_mailbox_encryption_policy` action and
`encryption_policy_decision_contains` assertion. See
`docs/SCENARIO_DSL_v0_2.md`.

Sprint 6 retains compact symbolic decisions from registered policy evaluation
on `RegistryHub.encryption_policy_decision_history` and exposes
`query_encryption_policy_decisions(...)`. This retention belongs to the
registered RegistryHub helper only. The pure
`evaluate_mailbox_encryption_policy(...)` function remains non-mutating and
does not store audit history. See
`docs/ENCRYPTION_POLICY_DECISIONS_v1_0.md`.

## Explicit Non-Goals

Sprint 3 does not add:

- real cryptography;
- key generation;
- encryption or decryption;
- production E2EE;
- secure messenger behavior;
- crypto library integration;
- Signal, MLS, HPKE, or Noise implementation;
- private key storage;
- secret material;
- production identity proof;
- message delivery semantic changes;
- scenario DSL actions or assertions;
- networking;
- sockets;
- HTTP or WebSocket behavior;
- DNS lookup;
- registrar integration;
- public CA behavior;
- external services;
- durable queues or retry workers;
- TrafficHub routing changes;
- canonical identity rewrites.
