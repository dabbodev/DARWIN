# DARWIN Encrypted Delivery Results v1.1

Status: implemented on the unreleased `v1.1/planning` branch. The current
branch package and CLI version are `darwin-sim 1.1.0`.

DARWIN v1.1 adds opt-in wrapped symbolic encrypted delivery results,
compact audit metadata, and Sprint 5 RegistryHub-local retained wrapped-result
history. These helpers combine an
`EncryptedDeliveryRequest`, its `EncryptedDeliveryGateDecision`, and, only
when explicitly requested, an existing v0.9 `MessageDeliveryResult`.

This is simulator audit metadata only. It is not real encrypted delivery, not
production E2EE, not a secure messenger, and not a cryptographic protocol.

## Purpose

`EncryptedDeliveryResult` records the outcome of the helper-level symbolic
flow introduced across v1.1:

- evaluate the request with the symbolic policy gate;
- return the gate decision in every wrapped result;
- do not deliver by default;
- optionally call the existing in-memory mailbox delivery helper when
  `attempt_delivery=True`;
- include the existing `MessageDeliveryResult` only when that helper was
  called.

The result summary is deterministic and JSON-safe. It includes:

- `request_id`
- `message_id`
- `mailbox_id`
- `lane_signature`
- `gate_decision`
- `delivery_result`
- `status`
- `reason`
- `delivery_attempted`
- `delivery_allowed`
- `policy_required`
- `metadata`

`EncryptedDeliveryAuditEntry` provides a smaller audit-oriented view with:

- `request_id`
- `message_id`
- `mailbox_id`
- `lane_signature`
- `gate_status`
- `gate_reason`
- `delivery_status`
- `delivery_reason`
- `policy_id`
- `encryption_required`
- `envelope_accepted`
- `metadata`

## Relationship to EncryptedDeliveryRequest

`EncryptedDeliveryRequest` remains the explicit request input shape. It may
describe plaintext, symbolic encrypted, or policy-check-only intent.

The new `evaluate_encrypted_delivery_request(...)` helper accepts that request
and evaluates the existing policy gate. Policy-check-only requests never call
delivery. Blocked requests never call delivery. Allowed requests only call
delivery when the caller explicitly passes:

```python
attempt_delivery=True
```

## Relationship to EncryptedDeliveryGateDecision

Every wrapped result includes the symbolic `EncryptedDeliveryGateDecision`
from `evaluate_encrypted_delivery_request_policy(...)`.

Gate decisions remain the source of truth for:

- `delivery_allowed`
- `policy_required`
- `envelope_accepted`
- policy status and reason
- the underlying retained `EncryptionPolicyDecision`, when one was created

The wrapper does not add persistent gate-decision history. Sprint 5 retains
wrapped results separately on
`RegistryHub.encrypted_delivery_result_history`.

## Relationship to MessageDeliveryResult

v0.9 `MessageDeliveryResult` remains the retained result created by
`deliver_message_to_mailbox(...)`.

The wrapper does not replace or alter that model. When
`attempt_delivery=True` and the gate allows delivery, the helper calls:

```python
deliver_message_to_mailbox(registry_hub, request.message_envelope)
```

The returned `MessageDeliveryResult` is attached to the wrapped result. The
normal delivery helper still owns inbox mutation and retained delivery-result
append behavior.

If `attempt_delivery=False`, the wrapper returns an allowed but not-delivered
result and does not mutate message inboxes or retained message delivery
results.

## Default Behavior

The default is:

```python
attempt_delivery=False
```

This keeps symbolic encrypted delivery integration observable without changing
existing plaintext mailbox behavior. Direct calls to
`deliver_message_to_mailbox(...)` keep their released v0.9 semantics and do
not run encrypted delivery policy by default.

## Retention

The wrapper exposes:

```python
retain_policy_decision=True
```

This is passed through to the Sprint 2 gate helper. It controls only the
existing `RegistryHub.encryption_policy_decision_history` behavior.

Sprint 5 adds a separate retention flag:

```python
retain_result=True
```

By default, `evaluate_encrypted_delivery_request(...)` appends the returned
`EncryptedDeliveryResult` to:

```python
registry_hub.encrypted_delivery_result_history
```

Passing `retain_result=False` returns the wrapped result without appending it.
This does not affect `retain_policy_decision` and does not create queues,
retry workers, or background processing.

## Helpers and Predicates

Sprint 3 adds:

- `evaluate_encrypted_delivery_request(...)`
- `summarize_encrypted_delivery_result(...)`
- `build_encrypted_delivery_audit_entry(...)`
- `query_encrypted_delivery_results(...)`
- `is_encrypted_delivery_result_allowed(...)`
- `is_encrypted_delivery_result_delivered(...)`
- `is_encrypted_delivery_result_blocked(...)`

All helpers are deterministic and simulator-local.

## Scenario DSL Coverage

Sprint 4 exposes `evaluate_encrypted_delivery_request(...)` through the
scenario action `evaluate_encrypted_delivery_request`. The action appends the
wrapped `EncryptedDeliveryResult` to scenario action results and logs a
deterministic simulator event. `attempt_delivery` defaults to `false`.

Sprint 4 also adds read-only scenario assertions:

- `encrypted_delivery_result_contains`
- `encrypted_delivery_audit_contains`

Sprint 5 updates these assertions to prefer retained
`RegistryHub.encrypted_delivery_result_history` records, falling back to
scenario action results only when retained history is unavailable or empty.
They remain read-only and do not change `deliver_message_to_mailbox(...)`
behavior.

Detailed snapshots include compact retained wrapped-result summaries at:

```text
registry_hubs.<hub_id>.encrypted_delivery_result_history
```

Compact `world.snapshot()` output remains unchanged.

See `docs/ENCRYPTED_DELIVERY_RESULT_HISTORY_v1_1.md`.

Checked-in scenarios `050` through `052` cover policy-check-only, gate-allowed
no-attempt, gate-allowed explicit delivery, and gate-blocked no-delivery
paths.

## Explicit Non-Goals

Sprint 3 does not add:

- real cryptography;
- key generation;
- private key storage;
- secret material;
- encryption;
- decryption;
- production E2EE;
- secure messenger behavior;
- default delivery enforcement;
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
- default delivery enforcement;
- durable wrapped-result queues;
- retry workers.
