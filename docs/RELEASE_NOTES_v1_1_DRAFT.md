# DARWIN v1.1.0 Release Notes

Status: unreleased release-prep work on the `v1.1/planning` branch. The
current branch package and CLI version are `darwin-sim 1.1.0`. Do not treat
v1.1.0 as released until merge, tagging, GitHub release publication, and any
explicit publication steps are performed separately.

DARWIN v1.1.0 prepares simulator-local symbolic encrypted delivery policy
integration for release. It connects v1.0 symbolic mailbox encryption policy
decisions to v0.9 toy in-memory mailbox delivery through explicit request,
gate, result, audit, retention, snapshot, and scenario DSL surfaces.

This is policy and audit modeling only. It is not real encryption, not
production E2EE, not a secure messenger, and not cryptographic protocol
behavior.

## Highlights

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
- Added v1.1 scenarios `050` through `052` for policy-check-only,
  gate-allowed/no-attempt, explicit gate-allowed delivery, and gate-blocked
  no-delivery paths.
- Added detailed snapshot visibility at
  `registry_hubs.<hub_id>.encrypted_delivery_result_history` while keeping
  compact `world.snapshot()` unchanged.
- Hardened the scenario index, metadata regression coverage, tests, and docs
  for request models, policy gates, wrapped results, retained history,
  scenario assertions, and simulator-only boundaries.

## Compatibility

- Existing `deliver_message_to_mailbox(...)` behavior remains unchanged.
- Existing plaintext `deliver_message` scenarios remain unchanged.
- Encrypted delivery integration remains opt-in and simulator-local.
- TrafficHub routing and canonical identity behavior remain unchanged.
- The current branch scenario set is contiguous from `001` through `052`.
- The current branch package and CLI version are `darwin-sim 1.1.0`.
- Merge, tag, GitHub release creation, and package publication have not been
  performed.

## Scenario Coverage

v1.1 scenarios:

- `scenarios/050_symbolic_encrypted_delivery_policy_check.yaml`
- `scenarios/051_symbolic_encrypted_delivery_allowed.yaml`
- `scenarios/052_symbolic_encrypted_delivery_blocked.yaml`

These scenarios validate symbolic request/gate/result/audit behavior only.
They do not add production encrypted messaging, networking, DNS lookup,
external services, or default delivery enforcement.

## Current Limitations

- Wrapped encrypted delivery result history is in-memory and RegistryHub-local.
- Query helpers are read-only filters over retained simulator records.
- Audit entries are compact simulator metadata, not compliance logs.
- Policy checks depend on v1.0 symbolic policy records and symbolic envelope
  metadata only.
- Explicit delivery still delegates to the existing toy in-memory mailbox
  delivery helper when `attempt_delivery=True` and the gate allows it.

## Non-Goals

v1.1.0 does not add:

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

This branch is release-prep ready after the full validation set passes. The
release itself remains deferred: do not merge, tag, create a GitHub release,
or publish packages as part of this draft release-prep state.
