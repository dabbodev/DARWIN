# Retained Audit Direct Message-Delivery Expansion v1.10

Status: included in the v1.10.0 source-release snapshot in final validation as
`darwin-sim 1.10.0` behavior.

This specification extends DARWIN's deterministic retained-audit pipeline to
RegistryHub-local direct message-delivery result history. It adds no automatic
compaction, storage service, delivery enforcement, or cryptographic behavior.

## Supported History Order

The supported history-type order is:

1. `stream_offer_lifecycle_explanation`
2. `stream_offer_status_transition`
3. `rendezvous_poll_result`
4. `lane_admission_decision`
5. `encrypted_delivery_result`
6. `encryption_policy_decision`
7. `message_delivery_result`

The first six entries retain their v1.9 order, key shapes, serialization, and
behavior.

## Ownership and Result Metadata

`deliver_message_to_mailbox(...)` adds the owning RegistryHub ID as string
`metadata["registry_hub"]` on every returned and retained
`MessageDeliveryResult`. That owner is derived from the supplied
`RegistryHub`, overrides conflicting internal result metadata, and does not
come from an envelope field.

A directly constructed result participates in generic retained-audit helpers
only when `metadata["registry_hub"]` is a string. Missing, non-string, and
foreign owners are ignored deterministically.

This is an additive serialization change for helper-created delivery results:
the existing top-level `MessageDeliveryResult.to_summary()` fields and order
are unchanged, while its copied metadata mapping gains `registry_hub`.

## Record View and Exact Key

Classification and replay use only:

- top-level `message_id`, `recipient_address`, `resolved_mailbox_id`,
  `lane_signature`, `status`, and `reason`; and
- optional `metadata["source"]` when it is a string.

There is no request ID, offer ID, policy ID, endpoint grouping, fallback-action
grouping, audit-path grouping, metadata-note fallback, or nested result
interpretation. The exact key is:

```text
message_delivery_result:{index}:{hub_id|none}:{message_id}:{recipient_address}:{resolved_mailbox_id|none}:{lane_signature}:{status}:{reason|none}
```

Keys preserve caller-provided order. Existing retain-before-compact filter
precedence, post-classification `max_records`, unsupported-record behavior, and
read-only classification remain unchanged. v1.10 adds no message, mailbox, or
lane compaction-policy filters.

## Replay Summary Contract

`RetainedAuditReplaySummary` gains no field. Direct message-delivery results
contribute to the existing mappings as follows:

- every result contributes its top-level message ID and lane signature;
- a non-null `resolved_mailbox_id` contributes its mailbox ID;
- top-level status and reason contribute to their existing mappings;
- optional string `metadata["source"]` contributes to source grouping; and
- request, offer, and policy mappings remain empty for direct results.

All existing count validation, lexical sorting, copied serialization, history
grouping, and decision-category filtering behavior remains unchanged.

## Explicit Apply and State Isolation

An effective `message_delivery_result` apply selects only
`RegistryHub.message_delivery_results`:

- only currently matching candidate keys are removed;
- remaining records preserve append order;
- stale candidate keys are reported as missing;
- repeated apply is deterministic; and
- `message_delivery_history_mutated` is true only when a direct result is
  removed.

`delivery_state_mutated` remains false. Apply does not remove or rewrite inbox
envelopes, reverse a completed delivery, modify action results or events, or
re-evaluate fallback behavior. A compacted audit result may therefore still
have an unchanged envelope, event, or action-result representation.

All unrelated mutation flags remain false. Mixed or unsupported decisions are
deterministic no-ops. Apply does not mutate encrypted-delivery results,
encryption-policy decisions, lane/mailbox/endpoint registries, held offers,
alias or authority history, TrafficHub state or routing, canonical identities,
or compact snapshots.

## Scenario DSL, Snapshots, and Compatibility

The existing classify, replay, and apply actions accept
`message_delivery_result` and collect records from
`RegistryHub.message_delivery_results`. The existing `deliver_message` action
supplies results; it gains no new input or delivery behavior.

Scenarios `079` through `081` cover exact classification keys and ownership,
message/mailbox/lane/status/reason replay grouping and decision filters, and
isolated stale/repeated apply. Detailed snapshots expose copied owner metadata
and existing retained-audit summaries. Compact `world.snapshot()` remains
unchanged.

Existing public helper signatures, retained-audit dataclass fields, CLI
commands, scenario action types, assertion types, and snapshot section names
remain unchanged. Exact metadata-dictionary consumers must account for the
additive owner and apply mutation keys.

Record keys remain index-sensitive. Apply is safe for the unchanged selected
history and reports stale decisions through existing missing-key behavior.

## Limits and Non-Goals

This simulator-local, deterministic, source-only extension adds no new
compaction filters, nested gate or delivery replay dimensions, mixed or
multi-history apply, inbox deletion, automatic cleanup, workers, retries,
durable queues, live timers, live clocks, live polling, delivery enforcement,
delivery behavior changes, TrafficHub routing changes, compact snapshot
changes, canonical identity rewrites, networking, DNS, external services, real
cryptography, production E2EE, or production security, privacy, anonymity,
firewall, DDoS, compliance, or data-retention guarantees.
