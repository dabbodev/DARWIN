# DARWIN Encryption Registry v1.0

Status: v1.0 planning on `v1.0/planning`; current package and CLI version
remains `darwin-sim 0.9.0`.

DARWIN v1.0 Sprint 4 adds RegistryHub-local symbolic encryption registries.
These registries store encryption identities, key bundle references, mailbox
encryption bindings, and mailbox encryption policies as simulator bookkeeping
only.

This is not a key server, certificate authority, KMS, registrar, public
identity infrastructure, secure messenger, or production E2EE layer.

## Purpose

Sprint 1 through Sprint 3 added pure dataclass records and helper-level policy
evaluation. Sprint 4 gives a `RegistryHub` local storage surface for those
records so future scenario DSL work can register and inspect them without
changing message delivery behavior.

`RegistryHub` now stores:

- `encryption_identities`: maps `encryption_identity_id` to
  `EncryptionIdentity`.
- `key_bundle_references`: maps `key_bundle_id` to `KeyBundleReference`.
- `mailbox_encryption_bindings`: maps `mailbox_id` to
  `MailboxEncryptionBinding`.
- `mailbox_encryption_policies`: maps `policy_id` to
  `MailboxEncryptionPolicy`.

Each dictionary defaults to empty, preserving existing hub construction.

## Stored Records

Encryption identities name a symbolic encryption identity for a mailbox,
device, or future resource.

Key bundle references point at symbolic public references. They do not contain
private keys, generated keys, shared secrets, or cryptographic material.

Mailbox encryption bindings connect a registered mailbox to one symbolic
encryption identity and one symbolic key bundle reference. The current binding
registry uses `mailbox_id` as its key, so each mailbox has at most one active
binding record in this helper layer.

Mailbox encryption policies describe lane-specific symbolic encryption
requirements. They are stored by `policy_id`; helper lookup by mailbox returns
the first deterministic policy for that mailbox.

## Registry Helpers

Sprint 4 adds `darwin.registry.encryption_registry` helpers and exports them
through `darwin.registry`:

- `register_encryption_identity(...)`
- `get_encryption_identity(...)`
- `list_encryption_identities(...)`
- `register_key_bundle_reference(...)`
- `get_key_bundle_reference(...)`
- `list_key_bundle_references(...)`
- `register_mailbox_encryption_binding(...)`
- `get_mailbox_encryption_binding(...)`
- `list_mailbox_encryption_bindings(...)`
- `register_mailbox_encryption_policy(...)`
- `get_mailbox_encryption_policy(...)`
- `get_mailbox_encryption_policy_for_mailbox(...)`
- `list_mailbox_encryption_policies(...)`
- `evaluate_registered_mailbox_encryption_policy(...)`

Registration replaces records by deterministic registry key, matching existing
RegistryHub helper conventions.

## Relationship to Mailbox Registry

Mailbox encryption bindings and mailbox encryption policies require the target
`mailbox_id` to already exist in `registry_hub.mailboxes`.

Key bundle registration requires its referenced `encryption_identity_id` to
already exist in `registry_hub.encryption_identities`.

Mailbox encryption binding registration requires:

- a registered mailbox;
- a registered encryption identity;
- a registered key bundle reference;
- a key bundle whose `encryption_identity_id` matches the binding.

These checks are record cross-reference checks only. They do not prove identity
ownership, validate certificates, verify key material, or perform
cryptographic validation.

## Relationship to v0.9 Message Delivery

Sprint 4 does not call, wrap, or alter `deliver_message_to_mailbox(...)`.
Existing v0.9 plaintext toy delivery remains valid. Registered encryption
policies do not force plaintext delivery to fail, do not append inbox entries,
do not retain delivery results, and do not change lane fallback behavior.

The registries are available for future scenario and audit layers, but they are
not wired into delivery yet.

## Relationship to Envelopes and Policy Decisions

`evaluate_registered_mailbox_encryption_policy(...)` is a helper-level bridge
from RegistryHub storage to the existing pure policy evaluator.

The helper:

1. Finds the deterministic policy for a mailbox.
2. Finds the mailbox encryption binding for that mailbox.
3. Resolves the binding's encryption identity and key bundle from the hub.
4. Calls `evaluate_mailbox_encryption_policy(...)`.
5. Returns an `EncryptionPolicyDecision`.

If no policy is registered for the mailbox, the helper returns a deterministic
`plaintext_allowed` decision with `policy_id` set to
`no_registered_policy`.

The helper does not mutate `RegistryHub`, `TrafficHub`, mailboxes, inboxes,
delivery results, aliases, lane registries, adapter endpoints, messages, or
envelope metadata.

## Snapshot Visibility

Detailed simulator snapshots include compact summaries of the four encryption
registry dictionaries. Compact `world.snapshot()` remains unchanged.

## Explicit Non-Goals

Sprint 4 does not add:

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
- public key server behavior;
- certificate authority behavior;
- KMS behavior;
- networking;
- sockets;
- HTTP or WebSocket behavior;
- DNS lookup;
- registrar integration;
- public CA behavior;
- external services;
- durable queues or retry workers;
- message delivery semantic changes;
- TrafficHub routing changes;
- canonical identity rewrites;
- scenario DSL actions or assertions;
- new scenario YAMLs.
