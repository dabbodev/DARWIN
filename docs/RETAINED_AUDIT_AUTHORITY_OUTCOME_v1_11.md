# Retained Audit Authority-Outcome Expansion v1.11

Status: included in the v1.11.0 source-release snapshot validated on
2026-07-29 (America/Los_Angeles) as `darwin-sim 1.11.0` behavior.

This specification extends DARWIN's deterministic retained-audit pipeline to
RegistryHub-local authority outcome history. It adds no automatic compaction,
event store, alias deletion, authority enforcement, external storage, or
cryptographic behavior.

## Supported History Order

The supported history-type order is:

1. `stream_offer_lifecycle_explanation`
2. `stream_offer_status_transition`
3. `rendezvous_poll_result`
4. `lane_admission_decision`
5. `encrypted_delivery_result`
6. `encryption_policy_decision`
7. `message_delivery_result`
8. `authority_outcome`

The first seven entries retain their v1.10 order, key shapes, serialization,
and behavior.

## Ownership and Exact Key

An authority outcome participates only when its `requesting_hub` is a string
matching the supplied policy or replay hub. Missing, non-string, and foreign
owners are ignored deterministically. The existing authority-chain claim
helper already retains outcomes on the requesting RegistryHub; v1.11 does not
change claim behavior or add metadata.

The generic retained-audit status dimension uses top-level `final_status`.
The coarser returned claim `status` remains ungrouped but is retained in the
key:

```text
authority_outcome:{index}:{requesting_hub|none}:{record_id}:{requested_alias}:{granted_alias|none}:{target_device|none}:{final_status}:{status|none}:{reason|none}:{comma-joined-path-hubs|none}
```

Keys preserve caller-provided order. Existing retain-before-compact filter
precedence, post-classification `max_records`, unsupported-record behavior,
and read-only classification remain unchanged. v1.11 adds no alias, device,
path, authority-ceiling, or boolean compaction-policy filter.

## Replay Summary Contract

`RetainedAuditReplaySummary` adds four optional sorted count mappings at the
end of its public constructor and serialized summary:

- `by_requested_alias`
- `by_granted_alias`
- `by_target_device`
- `by_path_hub`

Every authority outcome contributes its requested alias. Only non-null
granted aliases and target devices contribute to `by_granted_alias` and
`by_target_device`. Every string element of `path_hubs` contributes one
occurrence to `by_path_hub`. Generic `by_status` uses `final_status`;
`by_reason` uses the top-level reason; source is `none`.

Returned claim status, authority ceiling, record ID, nested decisions, and
the fallback/conflict/policy/path boolean flags are not grouped. Existing
offer, request, message, mailbox, policy, and lane mappings remain empty for
authority outcomes.

The scenario assertion `retained_audit_replay_summary_contains` adds matching
value/count pairs:

- `requested_alias` and `requested_alias_count`
- `granted_alias` and `granted_alias_count`
- `target_device` and `target_device_count`
- `path_hub` and `path_hub_count`

No new action or assertion type is introduced.

## Explicit Apply and State Isolation

An effective `authority_outcome` apply selects only
`RegistryHub.authority_outcome_history`:

- only currently matching candidate keys are removed;
- remaining records preserve append order;
- stale candidate keys are reported as missing;
- repeated apply is deterministic; and
- `authority_history_mutated` is true only when an outcome is removed.

`alias_history_mutated` and every unrelated mutation flag remain false. Apply
does not remove or rewrite aliases, conflicts, security events, authority
configuration, other retained histories, action results, canonical identity,
TrafficHub state or routing, or compact snapshots. Mixed or unsupported
decisions remain deterministic no-ops.

## Scenario DSL, Snapshots, and Compatibility

The existing classify, replay, and apply actions accept `authority_outcome`
and collect records from `RegistryHub.authority_outcome_history`. Existing
`claim_alias_through_authority_chain` actions supply records and gain no new
input or behavior.

Scenarios `082` through `084` cover exact ownership and final-status
classification, alias/device/path replay through decision filters, and
isolated stale/repeated apply. Detailed snapshots expose copied new replay
mappings and the remaining authority history. Compact `world.snapshot()`
remains unchanged.

Existing retained-audit helper signatures, compaction policy fields, action
types, assertion types, authority outcome records, authority claim/query
helpers, CLI commands, and prior detailed-summary keys remain unchanged.
Exact-dictionary consumers must account for the four appended replay keys.

Record keys remain index-sensitive. Apply is safe for the unchanged selected
history and reports stale decisions through existing missing-key behavior.

## Limits and Non-Goals

This simulator-local, deterministic, source-only extension adds no
authority-ceiling, record-ID, returned-status, nested-decision, or boolean
replay grouping; new compaction filters; mixed or multi-history apply; broad
event store; alias, conflict, or security-event deletion; automatic cleanup;
workers; retries; durable queues; live clocks; networking; DNS; external
services; real cryptography; production E2EE; or production security,
privacy, anonymity, firewall, DDoS, compliance, or data-retention guarantees.
