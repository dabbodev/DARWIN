# DARWIN v1.1 Draft Release Notes

Status: unreleased draft work on the `v1.1/planning` branch. The current
package and CLI version remain `darwin-sim 1.0.0`. Do not treat v1.1 as
released until explicit release prep, tagging, and release publication occur.

DARWIN v1.1 adds simulator-local symbolic encrypted delivery policy
integration. It connects v1.0 symbolic mailbox encryption policy decisions to
v0.9 toy in-memory mailbox delivery through explicit request, gate, result,
audit, retention, snapshot, and scenario DSL surfaces.

This is policy and audit modeling only. It is not real encryption, not
production E2EE, not a secure messenger, and not cryptographic protocol
behavior.

## Draft Highlights

- Added symbolic encrypted delivery request models for plaintext,
  symbolic-encrypted, and policy-check-only intent.
- Added the opt-in `evaluate_encrypted_delivery_request_policy(...)` gate for
  registered mailbox encryption policy checks before delivery.
- Added wrapped `EncryptedDeliveryResult` records and compact
  `EncryptedDeliveryAuditEntry` metadata.
- Kept `evaluate_encrypted_delivery_request(...)` defaulted to
  `attempt_delivery=False`; delivery occurs only when explicitly requested and
  the symbolic gate allows it.
- Added retained wrapped encrypted delivery result history at
  `RegistryHub.encrypted_delivery_result_history`.
- Added read-only `query_encrypted_delivery_results(...)` filters over
  retained wrapped results while preserving append order.
- Added the scenario DSL action `evaluate_encrypted_delivery_request`.
- Added read-only scenario assertions
  `encrypted_delivery_result_contains` and
  `encrypted_delivery_audit_contains`.
- Added v1.1 draft scenarios `050` through `052` for policy-check-only,
  gate-allowed/no-attempt, explicit gate-allowed delivery, and gate-blocked
  no-delivery paths.
- Added detailed snapshot visibility at
  `registry_hubs.<hub_id>.encrypted_delivery_result_history` while keeping
  compact `world.snapshot()` unchanged.
- Hardened tests and docs for request models, policy gates, wrapped results,
  retained history, scenario assertions, scenario index coverage, and
  simulator-only boundaries.

## Compatibility

- Existing `deliver_message_to_mailbox(...)` behavior remains unchanged.
- Existing plaintext `deliver_message` scenarios remain unchanged.
- Encrypted delivery integration remains opt-in and simulator-local.
- TrafficHub routing and canonical identity behavior remain unchanged.
- The current planning scenario set is contiguous from `001` through `052`.
- The package and CLI version remain `darwin-sim 1.0.0`.
- No package publication was performed.

## Scenario Coverage

v1.1 draft scenarios:

- `scenarios/050_symbolic_encrypted_delivery_policy_check.yaml`
- `scenarios/051_symbolic_encrypted_delivery_allowed.yaml`
- `scenarios/052_symbolic_encrypted_delivery_blocked.yaml`

These scenarios validate symbolic request/gate/result/audit behavior only.
They do not add production encrypted messaging, networking, DNS lookup,
external services, or default delivery enforcement.

## Non-Goals

v1.1 does not add:

- real cryptography;
- key generation;
- private key storage;
- secret material;
- encryption;
- decryption;
- production E2EE;
- secure messenger behavior;
- crypto library integration;
- Signal implementation;
- MLS implementation;
- HPKE implementation;
- Noise implementation;
- default delivery enforcement;
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
- package publication.

## Release Readiness

This draft is intended to support release-candidate review only. Before any
v1.1 release, run the full validation set, confirm the versioning plan, update
release metadata deliberately, and avoid package publication unless explicitly
planned.
