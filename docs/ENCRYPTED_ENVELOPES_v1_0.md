# DARWIN Encrypted Envelopes v1.0

Status: v1.0 planning on `v1.0/planning`; current package and CLI version
remains `darwin-sim 0.9.0`.

DARWIN v1.0 Sprint 2 adds simulator-local encrypted-envelope metadata. These
records describe whether a message is plaintext or symbolically encrypted, what
encryption identity and key bundle were referenced, and what compact audit
metadata should be retained for future policy work.

This is symbolic metadata only. Sprint 2 does not encrypt, decrypt, generate
keys, hide payloads, open network transports, change message delivery
semantics, or implement production E2EE.

## Purpose

`EncryptedEnvelopeMetadata` gives DARWIN a compact record for future encrypted
delivery policy and scenario assertions. It lets tests and docs distinguish:

- plaintext simulator messages;
- messages represented as symbolically encrypted;
- envelopes that require encryption but are not ready;
- failed symbolic envelope preparation.

Envelope metadata summaries include:

- `envelope_id`
- `message_id`
- `encryption_identity_id`
- `key_bundle_id`
- `profile`
- `state`
- `status`
- `algorithm_ref`
- `ciphertext_ref`
- `plaintext_ref`
- `metadata`

`EncryptionState` uses controlled labels such as `plaintext`,
`symbolically_encrypted`, `encryption_required`, and `encryption_failed`.

`EncryptionEnvelopeStatus` uses controlled labels such as `ready`,
`missing_key_bundle`, `unsupported_profile`, `stale_key_bundle`, and
`disabled_identity`.

## Relationship to Encryption Identities

Sprint 1 introduced `EncryptionIdentity`, `KeyBundleReference`, and
`MailboxEncryptionBinding`. Sprint 2 envelope metadata references those
records by ID:

- `encryption_identity_id` points at a simulator-local encryption identity.
- `key_bundle_id` points at a symbolic public key bundle reference.
- `profile` defaults to `symbolic_e2ee_v1`.

The IDs are references only. They are not proofs, certificates, private keys,
session keys, shared secrets, or cryptographic validation results.

## Relationship to Message Envelopes and Delivery

v0.9 `MessageEnvelope` records remain plaintext toy simulator envelopes for
`basic_messaging:v1`.

`SymbolicEncryptedMessageEnvelope` wraps a base `MessageEnvelope` with
`EncryptedEnvelopeMetadata` without mutating the original message. Its summary
includes:

- `message_id`
- `base_message`
- `encryption_metadata`
- `metadata`

Sprint 2 does not alter `deliver_message_to_mailbox(...)`, in-memory inbox
storage, delivery result retention, lane fallback policy, adapter endpoint
selection, `TrafficHub` routing, mailbox registration, or canonical identity.

## Symbolic Profile and References

The default profile is:

```text
symbolic_e2ee_v1
```

The default `algorithm_ref` for helper-created symbolic encrypted metadata is:

```text
symbolic-envelope
```

This is a label only. It is not an implemented cipher, protocol, key exchange,
signature scheme, or authenticated encryption mode.

`ciphertext_ref` is also symbolic. The helper can create references such as:

```text
symbolic://ciphertext/env_msg_001
```

That string is not ciphertext. It is an audit/test reference that future
policy and scenario layers can inspect without implying secret material exists.

`plaintext_ref` is optional symbolic provenance. It can identify a test fixture
or simulator-local provenance label, but Sprint 2 does not transform payloads
between plaintext and ciphertext.

## Helpers

Sprint 2 adds pure deterministic helpers:

- `make_symbolic_encrypted_envelope_metadata(...)`
- `wrap_message_symbolically(...)`
- `is_envelope_symbolically_encrypted(...)`
- `is_encryption_profile_supported(...)`
- `is_envelope_ready_for_delivery(...)`

These helpers create or inspect dataclass records. They do not mutate
`MessageEnvelope`, `RegistryHub`, `TrafficHub`, inboxes, retained delivery
results, lane definitions, mailbox records, adapter endpoints, or scenarios.

## Why No Encryption Happens

DARWIN remains simulator-first. The v1.0 planning line models the shape of
encrypted mailbox metadata before any production security implementation is
scoped.

Real encryption would require protocol selection, key lifecycle design,
identity proof, threat modeling, secure storage, interoperability testing, and
reviewed cryptographic libraries. Sprint 2 intentionally avoids those claims
and keeps envelope records as deterministic simulator data.

## Future Policy Relationship

Future v1.0 sprints may use envelope metadata with mailbox encryption policy
helpers. Those helpers may decide whether a lane requires symbolic encrypted
metadata and how missing, stale, disabled, or unsupported setup should be
reported.

Scenario DSL actions and assertions should wait until helper-level models and
policy outcomes are stable. No new scenario YAMLs are added by Sprint 2.

## Explicit Non-Goals

Sprint 2 does not add:

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
- encrypted delivery policy;
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
