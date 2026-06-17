# DARWIN Encryption Policy Decisions v1.0

Status: v1.0 planning on `v1.0/planning`; current package and CLI version
remains `darwin-sim 0.9.0`.

DARWIN v1.0 Sprint 6 adds compact simulator-local retention for symbolic
mailbox encryption policy decisions. These records are audit summaries for the
simulator only. They are not proof of real encryption, production E2EE, or
secure delivery.

## Purpose

`EncryptionPolicyDecision` records summarize whether symbolic encrypted
envelope metadata satisfied a mailbox encryption policy for a lane and message.
Sprint 6 retains those decisions on the relevant `RegistryHub` when registered
policy evaluation is used.

Retained history lives at:

```python
registry_hub.encryption_policy_decision_history
```

The list defaults to empty and preserves append order.

## Pure vs Registered Evaluation

`evaluate_mailbox_encryption_policy(...)` remains the pure model-level helper.
It returns an `EncryptionPolicyDecision` and does not mutate a `RegistryHub`,
mailbox, message, inbox, delivery result, or scenario state.

`evaluate_registered_mailbox_encryption_policy(...)` resolves the registered
mailbox policy, binding, encryption identity, and key bundle from a
`RegistryHub`. By default it appends one compact decision to
`registry_hub.encryption_policy_decision_history` for each call and returns the
same decision.

Callers may pass `retain=False` to use registered records without appending to
history.

## Query Helper

`query_encryption_policy_decisions(...)` reads retained decisions without
mutation. Filters are optional and additive:

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

Results preserve append order and return an empty list when no retained
decision matches. Decision `to_summary()` output is deterministic and
JSON-safe.

## Snapshot Visibility

Detailed snapshots expose retained decisions at:

```text
registry_hubs.<hub_id>.encryption_policy_decision_history
```

The snapshot contains compact `EncryptionPolicyDecision.to_summary()` copies,
not live mutable references. Compact `world.snapshot()` remains unchanged.

## Scenario Assertions

The scenario assertion `encryption_policy_decision_contains` now prefers
retained `RegistryHub.encryption_policy_decision_history` records. It falls
back to scenario action results for compatibility with earlier Sprint 5
behavior.

## Explicit Non-Goals

Sprint 6 does not add:

- real cryptography;
- key generation;
- encryption or decryption;
- production E2EE;
- secure messenger behavior;
- delivery enforcement;
- crypto library integration;
- private key storage;
- secret material;
- networking;
- sockets;
- HTTP or WebSocket behavior;
- DNS lookup;
- registrar integration;
- public CA behavior;
- production identity proof;
- external services;
- durable queues or retry workers;
- TrafficHub routing changes;
- canonical identity rewrites;
- message delivery semantic changes.
