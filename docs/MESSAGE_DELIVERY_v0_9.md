# DARWIN In-Memory Message Delivery v0.9

Status: released in v0.9.0 on `main`; current package and CLI version is
`darwin-sim 0.9.0`.

DARWIN v0.9 Sprint 6 adds toy, simulator-local message envelopes and delivery
results for `basic_messaging:v1`. Sprint 7 exposes that helper path through
scenario DSL actions and assertions. The delivery helper proves that a DARWIN
mailbox address can resolve through `RegistryHub`, match a registered lane and
mailbox capability, select an inert in-memory endpoint, and append a message
to a local inbox.

This is not a production chat system, network protocol, secure messenger, or
encrypted delivery layer.

## RegistryHub Message Storage

`RegistryHub` now has two empty message stores by default:

- `message_inboxes`: maps `mailbox_id` to a list of `MessageEnvelope` records.
- `message_delivery_results`: retains `MessageDeliveryResult` records in
  deterministic append order.

The storage is process-local simulator state only. It is not durable storage,
a production queue, a retry scheduler, or an external service.

## Message Models

`MessageEnvelope` summaries are JSON-safe and include:

- `message_id`
- `sender_id`
- `recipient_address`
- `lane_signature`
- `payload_kind`
- `payload`
- `metadata`

`make_basic_message_envelope(...)` creates a pure `basic_messaging:v1`
envelope with `payload_kind` set to `text`. Payloads are plaintext symbolic
fixtures. They are not encrypted.

`MessageDeliveryResult` summaries are JSON-safe and include:

- `message_id`
- `recipient_address`
- `resolved_mailbox_id`
- `target_device_id`
- `lane_signature`
- `endpoint_id`
- `status`
- `reason`
- `fallback_action`
- `audit_path`
- `metadata`

Statuses are compact strings: `delivered`, `queued`, `held`, `bounced`,
`rejected`, and `failed`.

Failure reasons include missing mailboxes, missing lane definitions, missing
or disabled mailbox capabilities, endpoint problems, payload-kind mismatches,
quarantined recipients, in-transit devices, and unknown failures.

## Delivery Flow

`deliver_message_to_mailbox(registry_hub, message_envelope)` performs a
deterministic local decision:

1. Parse the DARWIN mailbox address already carried by the envelope.
2. Resolve the address through `RegistryHub.mailbox_address_index`.
3. Confirm the envelope lane is registered in `RegistryHub.lane_registry`.
4. Confirm the mailbox has an enabled capability for the lane.
5. Inspect existing target-device state when it is already present on the
   RegistryHub.
6. Select an available `in_memory` adapter endpoint for the mailbox and lane.
7. Append the envelope to `message_inboxes[mailbox_id]`.
8. Append the retained delivery result to `message_delivery_results`.

The helper does not call TrafficHub routing, mutate canonical identity, resolve
DNS, open sockets, encrypt payloads, or contact external services.

Read helpers:

- `get_mailbox_inbox(registry_hub, mailbox_id)`
- `list_message_delivery_results(...)`

Delivery result listing preserves append order and supports additive filters
for message ID, recipient address, mailbox ID, status, reason, and lane
signature.

## Scenario DSL Coverage

Sprint 7 adds scenario actions for registering lane definitions, mailboxes,
mailbox capabilities, inert adapter endpoints, and toy message envelopes. It
also adds assertions for registered mailboxes, mailbox lane support, retained
delivery results, and in-memory inbox contents.

Checked-in scenarios:

- `scenarios/044_mailbox_basic_message_delivery.yaml`
- `scenarios/045_mailbox_delivery_failures.yaml`
- `scenarios/046_mailbox_delivery_fallback_policy.yaml`

These scenarios use the same process-local helper path. They do not perform
network I/O, DNS lookup, external service calls, encryption, durable queueing,
retry scheduling, or TrafficHub routing.

## Fallback Policy Use

When a lane definition exists, delivery failures use that lane definition's
`LaneDeliveryFallbackPolicy`:

- Unknown recipient uses `unknown_recipient`.
- Missing or disabled mailbox capability uses `missing_lane_capability`.
- Missing, stale, disabled, unknown, or lane-mismatched in-memory endpoints use
  `adapter_unavailable`.
- Quarantined target devices use `quarantined`.
- In-transit target devices use `in_transit`.

Fallback actions map to result statuses:

- `reject` records `rejected`.
- `bounce` records `bounced`.
- `queue`, `queue_with_expiry`, and `queue_with_retry` record `queued`.
- `hold_until_relocation_resolves` and `manual_resolution_required` record
  `held`.

Queued and held results are retained simulator metadata only. Sprint 6 does
not add background retry workers, expiry processing, durable queues, or
scheduling.

If a lane definition is missing, no registered fallback policy exists for that
lane. The helper records a clear `lane_not_registered` result with a `reject`
fallback action.

## Relationship to Existing v0.9 Pieces

Lane registries remain scoped catalogs. A lane definition says that a lane
shape exists and carries fallback policy data.

Mailbox registries remain identity and address bookkeeping. A mailbox must be
registered and must have an enabled capability for the requested lane.

Adapter endpoint records remain inert metadata. Sprint 6 only treats an
`available` `in_memory` mailbox endpoint as enough to append to a simulator
inbox. Other adapter kinds remain descriptive and do not open transports.

## Limitations

v0.9 message delivery does not add:

- real networking;
- sockets;
- DNS lookup;
- HTTP or WebSocket clients or servers;
- external services;
- registrar integration;
- public CA behavior;
- production chat behavior;
- production encryption or E2EE;
- production identity proof;
- background retries;
- durable queues;
- TrafficHub routing changes;
- canonical identity rewrites;
- package publication.

Future work may build demo-app views over the local inbox and retained result
records. Those future layers should keep the same simulator-only boundary until
explicitly scoped otherwise.
