# DARWIN Encryption Registry v1.0

Status: v1.0 planning on `v1.0/planning`; current package and CLI version
on this branch report `darwin-sim 1.0.0`.

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
- `encryption_policy_decision_history`: append-ordered symbolic
  `EncryptionPolicyDecision` records retained by registered policy
  evaluation.

Each dictionary and history list defaults to empty, preserving existing hub
construction.

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
- `query_encryption_policy_decisions(...)`

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

Sprint 5 adds scenario DSL actions and assertions for these symbolic
registries and for registered policy decisions. That DSL surface still does
not call or alter `deliver_message_to_mailbox(...)`.

## Relationship to Envelopes and Policy Decisions

`evaluate_registered_mailbox_encryption_policy(...)` is a helper-level bridge
from RegistryHub storage to the existing pure policy evaluator. The lower-level
`evaluate_mailbox_encryption_policy(...)` remains pure and does not retain
history.

The helper:

1. Finds the deterministic policy for a mailbox.
2. Finds the mailbox encryption binding for that mailbox.
3. Resolves the binding's encryption identity and key bundle from the hub.
4. Calls `evaluate_mailbox_encryption_policy(...)`.
5. Appends the resulting `EncryptionPolicyDecision` to
   `registry_hub.encryption_policy_decision_history` by default.
6. Returns the retained `EncryptionPolicyDecision`.

If no policy is registered for the mailbox, the helper returns a deterministic
`plaintext_allowed` decision with `policy_id` set to
`no_registered_policy`.

Callers may pass `retain=False` to compute through registered records without
appending to decision history. Either way, the helper does not mutate
`TrafficHub`, mailboxes, inboxes, delivery results, aliases, lane registries,
adapter endpoints, messages, envelope metadata, or delivery behavior.

## Decision History Queries

`query_encryption_policy_decisions(...)` reads
`registry_hub.encryption_policy_decision_history` without mutation. Filters are
additive and preserve append order:

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

The helper returns retained `EncryptionPolicyDecision` objects. Their
`to_summary()` values are deterministic and JSON-safe.

## Snapshot Visibility

Detailed simulator snapshots include compact summaries of the four encryption
registry dictionaries and the append-ordered
`encryption_policy_decision_history` list. Compact `world.snapshot()` remains
unchanged.

Scenario policy decisions remain visible through scenario action results.
`encryption_policy_decision_contains` now prefers retained RegistryHub history
and falls back to action results for compatibility.

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
- delivery enforcement;
- production audit storage for policy decisions beyond compact simulator-local
  symbolic history.
