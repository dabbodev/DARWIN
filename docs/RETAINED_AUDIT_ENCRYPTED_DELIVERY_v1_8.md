# Retained Audit Encrypted Delivery Expansion v1.8

Status: included in the v1.8.0 source-release snapshot as
`darwin-sim 1.8.0` behavior.

This specification extends the v1.6 retained-audit pipeline and v1.7 history
set. It does not introduce a new storage model, automatic compaction, or
delivery behavior.

## Supported History Order

The supported history-type order is:

1. `stream_offer_lifecycle_explanation`
2. `stream_offer_status_transition`
3. `rendezvous_poll_result`
4. `lane_admission_decision`
5. `encrypted_delivery_result`

The first four entries and their key shapes remain unchanged.

## Ownership and Record View

An encrypted-delivery result belongs to the RegistryHub named by a string
`result.metadata["registry_hub"]`. Missing, non-string, and foreign ownership
values are ignored. Classification and replay use:

- top-level `request_id`, `message_id`, `mailbox_id`, `status`, and `reason`;
- `metadata["source"]` only when it is a string;
- no offer ID; and
- no fallback from `metadata["note"]` to source.

The deterministic key is:

```text
encrypted_delivery_result:{index}:{hub_id|none}:{request_id}:{message_id|none}:{mailbox_id|none}:{lane_signature|none}:{status}:{reason|none}
```

Keys preserve the caller-provided record order. Existing retain-before-compact
filter precedence and post-classification `max_records` behavior apply without
change.

## Replay Summary Contract

`RetainedAuditReplaySummary` adds copied, sorted `by_message_id` and
`by_mailbox_id` mappings. Records with a missing message or mailbox ID do not
contribute to those mappings. Existing request, status, reason, source, offer,
history-type, and decision-category counts remain unchanged.

This release does not add message/mailbox compaction-policy filters and does
not group nested gate status, gate reason, direct delivery status, or direct
delivery reason.

## Explicit Apply Contract

An effective apply decision selects exactly one supported history. For
`encrypted_delivery_result`, apply mutates only
`RegistryHub.encrypted_delivery_result_history`:

- currently matching candidate keys are removed;
- remaining result order is preserved;
- stale candidate keys are reported as missing;
- a repeated apply is deterministic; and
- `encrypted_delivery_history_mutated` is true only when a result was removed.

Mixed and unsupported decisions remain deterministic no-ops. Apply does not
mutate encryption-policy decision history, direct message-delivery results,
mailbox inboxes, gate decisions, held offers, TrafficHub state, or routing.

## Scenario and Snapshot Contract

Existing retained-audit scenario actions accept the new history label.
Encrypted-delivery evaluation steps may supply an optional `source` string,
which is copied to the retained result metadata for audit grouping. Replay
assertions accept `message_id`/`message_count` and
`mailbox_id`/`mailbox_count`.

Scenarios `073` through `075` cover classification, replay grouping and
decision filtering, isolated explicit apply, repeated apply, and unchanged
delivery/policy state. `World.detailed_snapshot()` reuses the existing retained-
audit result fields; compact `world.snapshot()` remains unchanged.

## Non-Goals

This extension provides no automatic compaction, policy-decision compaction,
direct delivery-result compaction, production retention or compliance,
background workers, retries, durable queues, live timers, networking, DNS,
external services, real cryptography, production E2EE, or delivery/routing
changes.
