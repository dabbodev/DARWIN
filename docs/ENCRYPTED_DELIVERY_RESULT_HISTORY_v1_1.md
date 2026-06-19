# DARWIN Encrypted Delivery Result History v1.1

Status: released in v1.1.0 on `main`. The current package and CLI version are
`darwin-sim 1.1.0`.

DARWIN v1.1 Sprint 5 adds RegistryHub-local retained wrapped encrypted
delivery result history. The retained records are compact symbolic audit
metadata for simulator runs. They are not real encrypted delivery, production
E2EE, secure messaging, or cryptographic protocol behavior.

## Purpose

`RegistryHub.encrypted_delivery_result_history` stores the
`EncryptedDeliveryResult` returned by
`evaluate_encrypted_delivery_request(...)`.

The history:

- defaults to an empty list;
- appends at most one wrapped result per helper call;
- preserves deterministic append order;
- stores compact JSON-safe summaries through `to_summary()`;
- is local to the `RegistryHub`;
- does not change `deliver_message_to_mailbox(...)` behavior.

Policy-check-only, gate-blocked, gate-allowed/no-attempt, invalid, and
explicit delivery-attempt paths are all retained by default.

## Policy Decisions Versus Wrapped Results

`RegistryHub.encryption_policy_decision_history` stores underlying
`EncryptionPolicyDecision` records created by registered symbolic policy
evaluation.

`RegistryHub.encrypted_delivery_result_history` stores the higher-level
wrapped result. Each wrapped result includes the encrypted delivery request
identity, gate decision, optional existing `MessageDeliveryResult`, delivery
attempt markers, and simulator audit metadata.

The two histories are intentionally separate. `retain_policy_decision`
controls policy-decision retention. `retain_result` controls wrapped-result
retention.

## Retention Controls

`evaluate_encrypted_delivery_request(...)` now accepts:

```python
retain_result=True
```

When `retain_result=True`, the helper appends the wrapped result to
`registry_hub.encrypted_delivery_result_history`. When `retain_result=False`,
the helper still returns the wrapped result but does not append it.

`attempt_delivery` remains separate:

- `attempt_delivery=False` returns and retains a not-delivered wrapped result;
- gate-blocked requests return and retain a blocked wrapped result without
  delivery;
- policy-check-only requests return and retain a policy-check-only wrapped
  result;
- `attempt_delivery=True` only calls the existing mailbox delivery helper when
  the gate allows delivery.

## Query Helper

Use `query_encrypted_delivery_results(...)` for read-only retained-history
queries. Filters are additive, omitted filters are ignored, and results are
returned in append order.

Supported filters:

- `request_id`
- `message_id`
- `mailbox_id`
- `lane_signature`
- `status`
- `reason`
- `delivery_attempted`
- `delivery_allowed`
- `policy_required`
- `gate_status`
- `gate_reason`
- `delivery_status`
- `delivery_reason`
- `endpoint_id`

Nested gate and delivery filters are evaluated from object fields or compact
summaries. The helper returns an empty list when no retained result matches
and does not mutate simulator state.

## Scenario Assertions

The scenario assertions:

- `encrypted_delivery_result_contains`
- `encrypted_delivery_audit_contains`

now prefer retained `RegistryHub.encrypted_delivery_result_history` records.
They fall back to scenario action results only when retained history is
unavailable or empty, preserving compatibility with older in-memory action
results.

Assertions remain read-only and keep existing count behavior:
`expected_count` is exact, `min_count` is lower-bound, and at least one match
is required when neither count field is supplied.

## Snapshot Visibility

Detailed snapshots include compact retained result summaries under each
registry hub:

```text
registry_hubs.<hub_id>.encrypted_delivery_result_history
```

The field is JSON-safe, deterministic, and copied from model summaries rather
than exposing live mutable model references.

Compact `world.snapshot()` output remains unchanged and does not include
retained encrypted delivery result history.

## Explicit Non-Goals

Sprint 5 does not add:

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
- canonical identity rewrites.
