# DARWIN Encryption Identities v1.0

Status: v1.0 planning on `v1.0/planning`; current package and CLI version
remains `darwin-sim 0.9.0`.

DARWIN v1.0 Sprint 1 adds simulator-local encryption identity and key
reference records. These records describe how a mailbox, device, or future
resource can point at symbolic encryption metadata without adding real
cryptography, production E2EE, networking, delivery policy, or message
delivery behavior.

## Purpose

Encryption identity records give DARWIN a compact way to name the symbolic
encryption identity for a simulator subject. A subject can be a mailbox,
device, or future resource.

`EncryptionIdentity` summaries include:

- `encryption_identity_id`
- `subject_id`
- `subject_kind`
- `profile`
- `status`
- `metadata`

The default profile is `symbolic_e2ee_v1`. It is a simulator label only. It
does not name an implemented protocol, algorithm, cipher suite, key exchange,
or production security guarantee.

## Key Bundle References

`KeyBundleReference` records point at symbolic public key bundle references for
an encryption identity. The `public_ref` field is a symbolic reference string
for tests, summaries, and future policy decisions.

Key bundle summaries include:

- `key_bundle_id`
- `encryption_identity_id`
- `profile`
- `status`
- `public_ref`
- `created_order`
- `rotated_from`
- `metadata`

No private key material is stored. The model does not generate keys, derive
keys, encrypt, decrypt, sign, verify, or validate cryptographic material.

## Mailbox Encryption Bindings

`MailboxEncryptionBinding` records bind a mailbox to a symbolic encryption
identity and key bundle reference. Bindings may list lane signatures in
`required_for_lanes`, such as `basic_messaging:v1`, so future policy helpers
can decide whether a lane requires encrypted-envelope metadata.

Binding summaries include:

- `mailbox_id`
- `encryption_identity_id`
- `key_bundle_id`
- `required_for_lanes`
- `profile`
- `status`
- `metadata`

Sprint 1 bindings are model records only. They do not change mailbox
registration, capability binding, adapter endpoints, in-memory inbox storage,
message delivery results, TrafficHub routing, or canonical identity.

## Relationship to Mailbox Identity and Delivery

Mailbox identities remain the source of mailbox address and canonical device
identity information. Encryption identities are separate symbolic references
that can be attached to mailbox IDs in future policy layers without rewriting
canonical identity.

The v0.9 message delivery helper remains plaintext and toy-only. Sprint 1 does
not add encrypted delivery policy, scenario DSL actions, scenario DSL
assertions, or new scenario YAMLs.

Sprint 2 builds on these identity and key-bundle references with symbolic
encrypted-envelope metadata. See `docs/ENCRYPTED_ENVELOPES_v1_0.md`.

## Helpers

Sprint 1 adds pure deterministic helpers:

- `make_symbolic_encryption_identity(...)`
- `make_symbolic_key_bundle_reference(...)`
- `bind_mailbox_encryption_identity(...)`
- `is_encryption_identity_active(...)`
- `is_key_bundle_usable(...)`

These helpers create or inspect dataclass records. They do not mutate
`RegistryHub` or `TrafficHub`.

## Future Work

Sprint 2 adds symbolic encrypted-envelope metadata. Future v1.0 sprints may
add mailbox encryption policy helpers, scenario DSL coverage, and audit or
snapshot visibility. Those layers should continue using symbolic profile labels
and references until real cryptography is explicitly scoped outside this
planning line.

## Explicit Non-Goals

Sprint 1 does not add:

- real cryptography;
- key generation;
- private key storage;
- secret material;
- encryption or decryption;
- production E2EE;
- secure messenger behavior;
- crypto library integration;
- Signal, MLS, HPKE, or Noise implementation;
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
