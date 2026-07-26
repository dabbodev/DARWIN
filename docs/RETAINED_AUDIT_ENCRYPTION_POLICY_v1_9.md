# Retained Audit Encryption-Policy Expansion v1.9

Status: included in the v1.9.0 source-release snapshot as
`darwin-sim 1.9.0` behavior.

This specification extends DARWIN's deterministic retained-audit pipeline to
RegistryHub-local encryption-policy decision history. It adds no automatic
compaction, storage service, delivery enforcement, or cryptographic behavior.

## Supported History Order

The supported history-type order is:

1. `stream_offer_lifecycle_explanation`
2. `stream_offer_status_transition`
3. `rendezvous_poll_result`
4. `lane_admission_decision`
5. `encrypted_delivery_result`
6. `encryption_policy_decision`

The first five entries retain their v1.8 order, key shapes, serialization, and
behavior.

## Ownership and Record View

An `EncryptionPolicyDecision` belongs to the RegistryHub named by a string
`metadata["registry_hub"]`. Missing, non-string, and foreign owners are ignored
deterministically. Classification and replay use only:

- top-level `policy_id`, `mailbox_id`, `message_id`, `lane_signature`,
  `status`, and `reason`; and
- optional `metadata["source"]` when it is a string.

There is no offer ID, request ID, metadata-note fallback, nested gate
interpretation, or nested delivery interpretation. The exact key is:

```text
encryption_policy_decision:{index}:{hub_id|none}:{policy_id}:{mailbox_id}:{message_id|none}:{lane_signature}:{status}:{reason|none}
```

Keys preserve caller-provided order. Existing retain-before-compact filter
precedence, post-classification `max_records`, unsupported-record behavior, and
read-only classification remain unchanged. v1.9 adds no policy, mailbox,
message, or lane compaction-policy filters.

## Replay Summary Contract

`RetainedAuditReplaySummary` appends optional `by_policy_id` and
`by_lane_signature` mappings after all v1.8 fields. Both are validated as
non-negative integer count mappings, stored with lexically sorted keys, and
returned as copied mappings by `to_summary()` and `to_dict()`.

Only top-level values contribute:

- encryption-policy decisions contribute their policy and lane;
- lane-admission decisions contribute their existing policy and lane;
- encrypted-delivery results contribute their top-level lane but no nested
  gate policy; and
- missing values contribute nothing.

The scenario assertion
`retained_audit_replay_summary_contains` accepts
`policy_id`/`policy_count` and
`lane_signature`/`lane_signature_count`. Existing history, request, message,
mailbox, offer, status, reason, source, and decision-category behavior remains
unchanged.

## Explicit Apply and State Isolation

An effective `encryption_policy_decision` apply selects only
`RegistryHub.encryption_policy_decision_history`:

- only currently matching candidate keys are removed;
- remaining records preserve append order;
- stale candidate keys are reported as missing;
- repeated apply is deterministic; and
- `encryption_policy_history_mutated` is true only when a policy-decision
  record is removed.

All unrelated mutation flags remain false. Mixed or unsupported decisions are
deterministic no-ops.

Policy-history apply does not mutate encrypted-delivery results or their
nested immutable policy snapshots, direct delivery results, mailbox inboxes,
encryption registry configuration, held offers, TrafficHub state or routing,
canonical identities, or compact snapshots.

## Scenario DSL, Snapshots, and Compatibility

The existing classify, replay, and apply actions accept
`encryption_policy_decision` and collect records from the corresponding
RegistryHub history. The existing `evaluate_mailbox_encryption_policy` action
is reused without new evaluator input or behavior.

Scenarios `076` through `078` cover exact classification keys and ownership,
policy/lane/message/mailbox/status/reason replay grouping and decision filters,
and isolated stale/repeated apply. Detailed snapshots expose copied new replay
mappings through the existing retained-audit sections. Compact
`world.snapshot()` remains unchanged.

The additive replay mappings can affect consumers that compare serialized
dictionaries exactly. Existing fields retain their positions and values, and
the new dataclass fields are appended.

Record keys remain index-sensitive. Apply is safe for the unchanged selected
history and reports stale decisions through existing missing-key behavior.
Removing a policy-history record while an encrypted result retains its nested
immutable copy is expected.

## Limits and Non-Goals

This simulator-local, deterministic, source-only extension adds no direct
message-delivery result compaction, nested gate or delivery replay dimensions,
new compaction filters, mixed or multi-history apply, automatic cleanup,
workers, retries, durable queues, live timers, live clocks, live polling,
delivery enforcement, delivery behavior changes, TrafficHub routing changes,
compact snapshot changes, canonical identity rewrites, networking, DNS,
external services, real cryptography, production E2EE, or production security,
privacy, anonymity, firewall, DDoS, compliance, or data-retention guarantees.
