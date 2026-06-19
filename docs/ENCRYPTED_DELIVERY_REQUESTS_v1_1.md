# DARWIN Encrypted Delivery Requests v1.1

Status: released in v1.1.0 on `main`. The current package and CLI version are
`darwin-sim 1.1.0`.

DARWIN v1.1 Sprint 1 adds simulator-local symbolic encrypted delivery request
models. These records describe delivery intent and metadata only. They can
carry a v0.9 plaintext `MessageEnvelope`, v1.0 `EncryptedEnvelopeMetadata`, or
both, without calling mailbox delivery or enforcing encryption policy.

This is not encrypted messaging. It is a compact request shape for later
opt-in encrypted delivery policy gates.

## Purpose

`EncryptedDeliveryRequest` gives future v1.1 policy-gate work one explicit
input record. The request summary includes:

- `request_id`
- `message_envelope`
- `encryption_metadata`
- `mode`
- `policy_required`
- `policy_id`
- `mailbox_id`
- `lane_signature`
- `metadata`

Summaries are deterministic and JSON-safe. If the request carries a
`MessageEnvelope`, its summary is embedded. If it carries
`EncryptedEnvelopeMetadata`, its summary is embedded. JSON-safe dictionaries
may also be supplied directly for tests or export-oriented layers.

## Relationship to v0.9 MessageEnvelope

v0.9 `MessageEnvelope` remains the plaintext toy simulator envelope used by
`basic_messaging:v1` mailbox delivery. A plaintext request can reference one
of those envelopes without changing the envelope or delivering it.

When a request is constructed from a message envelope and no explicit
`lane_signature` is supplied, the request preserves the message envelope lane
signature. For current basic-message helpers that is:

```text
basic_messaging:v1
```

The request model does not alter payloads, recipient addresses, inboxes,
delivery results, lane definitions, mailbox records, adapter endpoints,
TrafficHub state, or canonical identity.

## Relationship to v1.0 EncryptedEnvelopeMetadata

v1.0 `EncryptedEnvelopeMetadata` remains symbolic metadata for plaintext or
symbolically encrypted envelopes. A symbolic encrypted delivery request can
reference that metadata alongside the plaintext message envelope it describes.

The request model validates that message IDs match when both a message envelope
and encryption metadata expose `message_id`. It does not encrypt, decrypt,
wrap, unwrap, transform payloads, prove identity ownership, inspect key
material, or evaluate readiness.

## Modes

`EncryptedDeliveryRequestMode` uses controlled labels:

- `plaintext`
- `symbolic_encrypted`
- `policy_check_only`

Plaintext requests carry a message envelope and no encryption metadata.

Symbolic encrypted requests carry a message envelope plus symbolic encrypted
envelope metadata. The metadata may reference symbolic identity and key-bundle
records, but those references are not cryptographic proof.

Policy-check-only requests reserve a lane, mailbox, and optional policy
reference for a future policy gate without carrying a message envelope. They
do not deliver and do not evaluate policy.

`EncryptedDeliveryRequestStatus` is a structural label for helper inspection,
not an enforcement result. Status labels include `plaintext`,
`symbolic_encrypted`, `missing_envelope`, `policy_check_only`, and `invalid`.

## Helpers

Sprint 1 adds pure deterministic constructors:

- `make_plaintext_delivery_request(...)`
- `make_symbolic_encrypted_delivery_request(...)`
- `make_policy_check_only_delivery_request(...)`

It also adds pure predicates:

- `is_delivery_request_plaintext(...)`
- `is_delivery_request_symbolically_encrypted(...)`
- `delivery_request_requires_policy(...)`
- `delivery_request_status(...)`

These helpers construct or inspect records only. They do not mutate
`RegistryHub`, `TrafficHub`, message envelopes, symbolic envelope metadata,
mailbox inboxes, retained delivery results, encryption policy decision
history, scenario state, snapshots, or external systems.

## Policy Gate and Result Relationship

v1.1 Sprint 2 uses `EncryptedDeliveryRequest` as the input to an explicit
opt-in policy gate. `evaluate_encrypted_delivery_request_policy(...)`
evaluates registered mailbox encryption policy and returns an
`EncryptedDeliveryGateDecision`.

The gate is still separate from delivery. It does not call
`deliver_message_to_mailbox(...)`, does not mutate message inboxes, and does
not create message delivery results. Existing plaintext delivery remains
unchanged, and a plain call to `deliver_message_to_mailbox(...)` still follows
v0.9 behavior.

See `docs/ENCRYPTED_DELIVERY_POLICY_GATE_v1_1.md`.

v1.1 Sprint 3 adds `evaluate_encrypted_delivery_request(...)`, which wraps the
request, gate decision, and optional existing `MessageDeliveryResult` in an
`EncryptedDeliveryResult`. Its default remains `attempt_delivery=False`, so a
request can be evaluated without mutating inboxes or retained message delivery
results.

See `docs/ENCRYPTED_DELIVERY_RESULTS_v1_1.md`.

v1.1 Sprint 4 wires this helper-level request flow into the scenario DSL
through `evaluate_encrypted_delivery_request`. Scenario usage remains
symbolic and opt-in; it does not make encrypted delivery policy enforcement
the default.

See `docs/SCENARIO_DSL_v0_2.md`.

## Why This Is Separate From Delivery

`deliver_message_to_mailbox(...)` is the released v0.9 in-memory mailbox
delivery helper. It resolves mailboxes, checks registered lanes and mailbox
capabilities, selects in-memory adapter endpoints, appends to a
RegistryHub-local inbox, and retains delivery results.

Encrypted delivery requests are deliberately separate because v1.1 policy
integration is opt-in and observable before any delivery behavior is gated.
Sprint 1 creates the request shape. Sprint 2 adds a symbolic policy gate that
returns a decision without delivering. Sprint 3 adds an opt-in wrapper that
can include an existing delivery result only when explicitly requested. None
of these sprints force existing plaintext delivery to fail or add default
delivery enforcement.

## Explicit Non-Goals

Sprint 1 does not add:

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
- delivery enforcement;
- scenario DSL actions;
- scenario DSL assertions;
- new scenario YAMLs;
- networking;
- sockets;
- HTTP or WebSocket behavior;
- DNS lookup;
- registrar integration;
- public CA behavior;
- production identity proof;
- external services;
- durable queues;
- retry workers;
- TrafficHub routing changes;
- canonical identity rewrites.
