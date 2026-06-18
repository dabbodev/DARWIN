# DARWIN Encrypted Delivery Requests v1.1

Status: implemented on the `v1.1/planning` branch. The current package and
CLI version remain `darwin-sim 1.0.0`.

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

## Future Policy Gate Relationship

Later v1.1 sprints can use `EncryptedDeliveryRequest` as the input to an
explicit opt-in policy gate. That future gate can evaluate registered mailbox
encryption policy before deciding whether a delivery helper should be called.

Sprint 1 does not perform that gate. `policy_required` and `policy_id` are
intent metadata only. Existing plaintext delivery remains unchanged, and a
plain call to `deliver_message_to_mailbox(...)` still follows v0.9 behavior.

## Why This Is Separate From Delivery

`deliver_message_to_mailbox(...)` is the released v0.9 in-memory mailbox
delivery helper. It resolves mailboxes, checks registered lanes and mailbox
capabilities, selects in-memory adapter endpoints, appends to a
RegistryHub-local inbox, and retains delivery results.

Encrypted delivery requests are deliberately separate because v1.1 policy
integration should be opt-in and observable before any delivery behavior is
gated. Sprint 1 creates the request shape only. It does not force existing
plaintext delivery to fail and does not add delivery enforcement.

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

