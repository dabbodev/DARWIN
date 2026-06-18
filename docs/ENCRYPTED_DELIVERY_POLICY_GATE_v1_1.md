# DARWIN Encrypted Delivery Policy Gate v1.1

Status: implemented on the `v1.1/planning` branch. The current package and
CLI version remain `darwin-sim 1.0.0`.

DARWIN v1.1 Sprint 2 adds an opt-in symbolic encrypted delivery policy gate.
The gate evaluates an `EncryptedDeliveryRequest` against registered mailbox
encryption policy and returns a deterministic `EncryptedDeliveryGateDecision`.

This is a simulator helper only. It is not delivery, not real encryption, not
production E2EE, and not default enforcement for plaintext mailbox delivery.

## Purpose

`evaluate_encrypted_delivery_request_policy(...)` lets tests and future
v1.1 work ask whether a request satisfies registered symbolic mailbox
encryption policy before any delivery helper is called.

The helper accepts:

- a `RegistryHub`;
- an `EncryptedDeliveryRequest`;
- `retain_decision`, which defaults to `True`.

It returns one `EncryptedDeliveryGateDecision` with:

- `request_id`
- `message_id`
- `mailbox_id`
- `lane_signature`
- `policy_id`
- `status`
- `reason`
- `policy_decision`
- `delivery_allowed`
- `policy_required`
- `envelope_accepted`
- `metadata`

The gate decision summary is deterministic and JSON-safe. Nested
`policy_decision` data is the compact `EncryptionPolicyDecision.to_summary()`
output when a registered policy check was performed.

## Relationship to EncryptedDeliveryRequest

`EncryptedDeliveryRequest` remains the request input shape introduced in
Sprint 1. It can describe plaintext, symbolic encrypted, or policy-check-only
intent.

The gate reads request metadata, including mailbox, lane, message, policy, and
symbolic envelope fields. It does not mutate the request, message envelope,
encrypted envelope metadata, mailbox inboxes, delivery results, lane
definitions, adapter endpoints, TrafficHub state, or canonical identity.

Plaintext requests with no required policy and no registered policy are
reported as `plaintext_allowed` with reason
`plaintext_no_policy_required`.

## Relationship to Registered Mailbox Encryption Policies

When a request references a policy, requires policy, or targets a mailbox with
registered policy, the gate calls
`evaluate_registered_mailbox_encryption_policy(...)`.

The registered evaluator resolves the mailbox policy, binding, encryption
identity, and symbolic key-bundle reference from the `RegistryHub`. The gate
wraps the resulting `EncryptionPolicyDecision` without changing its policy
semantics.

Accepted registered policy decisions become gate decisions with:

```text
status = allowed
reason = accepted
delivery_allowed = True
envelope_accepted = True
```

Rejected registered policy decisions become gate decisions with:

```text
status = policy_check_failed
delivery_allowed = False
```

The gate reason preserves the policy failure where possible, including
`missing_envelope`, `unsupported_profile`, `identity_inactive`,
`key_bundle_unusable`, and `envelope_not_ready`.

If a request requires policy and no registered policy is available, the gate
returns:

```text
status = policy_missing
reason = policy_not_found
delivery_allowed = False
```

If a request names a missing policy ID, the gate returns:

```text
status = policy_missing
reason = missing_policy_reference
delivery_allowed = False
```

## Retained Policy Decision History

Sprint 2 does not add persistent gate decision history.

When `retain_decision=True`, the underlying registered policy evaluator may
append exactly one `EncryptionPolicyDecision` to:

```python
registry_hub.encryption_policy_decision_history
```

When `retain_decision=False`, the gate still evaluates registered policy but
does not append the underlying policy decision. Gate decisions themselves are
returned to the caller only.

## Plaintext Delivery Remains Unchanged

`deliver_message_to_mailbox(...)` remains the v0.9 toy in-memory plaintext
delivery helper. Sprint 2 does not import it, call it, wrap it, or enforce
policy inside it.

Existing plaintext delivery keeps resolving mailboxes, checking lanes and
capabilities, selecting in-memory adapter endpoints, appending to inboxes, and
retaining delivery results exactly as before.

Using the gate is explicit. A caller must call the policy gate helper before
delivery if they want symbolic policy information.

## Why No Delivery Happens

Sprint 2 is deliberately scoped to policy-gate decisions. It proves the
request and policy layers can be connected without changing released mailbox
delivery semantics.

Sprint 3 adds that opt-in wrapper as
`evaluate_encrypted_delivery_request(...)`. It combines a gate decision and,
only when `attempt_delivery=True`, the existing underlying delivery result.
The policy gate itself remains delivery-free.

See `docs/ENCRYPTED_DELIVERY_RESULTS_v1_1.md`.

Sprint 4 exposes this opt-in gate path through scenario YAML with
`evaluate_encrypted_delivery_request` and read-only wrapped-result assertions.
Blocked gates still skip delivery, and plaintext delivery remains unchanged
unless the new action is used explicitly.

See `docs/SCENARIO_DSL_v0_2.md`.

Sprint 5 retains the higher-level wrapped results returned by
`evaluate_encrypted_delivery_request(...)` on
`RegistryHub.encrypted_delivery_result_history`. The policy gate itself still
does not retain gate decisions separately and still does not call mailbox
delivery. Underlying `EncryptionPolicyDecision` retention remains controlled
by `retain_decision` / `retain_policy_decision`.

See `docs/ENCRYPTED_DELIVERY_RESULT_HISTORY_v1_1.md`.

## Predicates

Sprint 2 adds pure predicates:

- `is_encrypted_delivery_gate_allowed(...)`
- `is_encrypted_delivery_gate_blocked(...)`

They inspect returned gate decisions only and do not mutate simulator state.

## Explicit Non-Goals

Sprint 2 does not add:

- real cryptography;
- key generation;
- private key storage;
- secret material;
- encryption;
- decryption;
- production E2EE;
- secure messenger behavior;
- delivery enforcement by default;
- crypto library integration;
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
- scenario DSL actions;
- scenario DSL assertions;
- new scenario YAMLs.
