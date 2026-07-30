# Retained Audit Batch Apply v1.12

Status: included in the v1.12.0 source-release snapshot validated on
2026-07-30 (America/Los_Angeles) with 991 passing tests as
`darwin-sim 1.12.0` behavior.

This specification composes DARWIN's existing explicit single-history
retained-audit apply decisions. It adds no automatic compaction, background
work, external store, rollback mechanism, or production retention behavior.

## Public Result Contract

`RetainedAuditCompactionBatchApplyResult` has four public constructor fields:

- `hub_id`
- `batch_id`
- `apply_results`
- `metadata`

It requires at least two
`RetainedAuditCompactionApplyResult` children from the same hub with distinct
supported history types. Children are stored in the canonical order defined by
`SUPPORTED_RETAINED_AUDIT_HISTORY_TYPES`:

1. `stream_offer_lifecycle_explanation`
2. `stream_offer_status_transition`
3. `rendezvous_poll_result`
4. `lane_admission_decision`
5. `encrypted_delivery_result`
6. `encryption_policy_decision`
7. `message_delivery_result`
8. `authority_outcome`

`history_types` returns that represented canonical order. `compacted_count`,
`retained_count`, `ignored_count`, `missing_count`, and `unsupported_count`
sum the corresponding child values. `to_summary()` and `to_dict()` expose:

```text
hub_id
batch_id
history_types
apply_results
compacted_count
retained_count
ignored_count
missing_count
unsupported_count
metadata
```

Nested results and metadata are copied into JSON-safe values. Mutating a
returned summary does not mutate the result or its children.

## Apply and Preflight Contract

The public helper is:

```python
apply_retained_audit_compaction_batch(
    registry_hub,
    decisions,
    *,
    batch_id,
    metadata=None,
)
```

The companion
`summarize_retained_audit_compaction_batch_apply_result(result)` returns a
copied summary. Both helpers and the result model are exported through the
existing registry and model public surfaces.

Before the first child mutation, batch apply requires:

- a `RegistryHub`;
- a nonblank `batch_id`;
- JSON-safe dictionary metadata when metadata is supplied;
- a list or tuple containing at least two decisions;
- only `RetainedAuditCompactionDecision` values;
- one matching hub ID across the batch;
- distinct history types;
- only the eight supported single-history labels; and
- selected histories containing only their expected supported record type.

`mixed` and unsupported history labels are rejected for batch application,
even though the existing single-history helper retains its deterministic
unsupported no-op behavior. All batch validation and selected-history
structural checks complete before the first child is applied. A failed
preflight leaves RegistryHub state byte-for-byte equivalent.

## Canonical Application and Stale Keys

Caller decision order has no effect on processing or nested result order.
Children are applied according to the supported history tuple. Because each
decision targets a distinct history, applying one child cannot shift another
child's index-sensitive keys.

Each child is applied through the unchanged
`apply_retained_audit_compaction_decision` helper:

- currently matching candidate keys are compacted;
- retained and ignored matches are reported;
- missing candidate keys are reported without aborting the batch; and
- remaining record order is preserved.

If one child decision is stale, another history can still compact. Repeating
an already applied batch is a deterministic no-op whose stale candidates are
reported as missing.

## Metadata Contract

Caller metadata is validated and copied before mutation. Generated batch
identity, canonical order, structural preflight, stale status, mutation facts,
and simulator safety flags are reserved; generated values override conflicting
caller keys.

The aggregate identifies explicit simulator-local batch apply and reports
whether any retained history changed. It also records the canonical history
list and batch size. It explicitly denies automatic cleanup, background
workers, retry loops, durable queues, live timers/clocks, delivery behavior or
TrafficHub changes, compact snapshot changes, canonical identity rewrites,
networking, DNS, external services, and cryptography.

Each nested result retains the existing single-apply shape and includes
generated batch ID, index, size, and canonical-order metadata. Existing
single-history metadata behavior outside batch apply is unchanged.

## Scenario DSL and Assertions

The scenario action is:

```yaml
- action: apply_retained_audit_compaction_batch
  registry_hub: registry_home_085
  batch_id: retained_audit_batch_085
  decision_policy_ids:
    authority_outcome: retained_audit_authority_085
    message_delivery_result: retained_audit_message_delivery_085
```

`decision_policy_ids` must be a mapping containing at least two supported
distinct history labels with nonblank policy IDs. Mapping keys make duplicate
history references unrepresentable after YAML parsing; the public helper
independently rejects duplicate decision histories. The runner resolves the
exact prior decision matching hub, history, and policy before apply.

The assertion
`retained_audit_compaction_batch_apply_result_contains` accepts:

- `batch_id`;
- exact canonical `history_types`;
- aggregate `compacted_count`, `retained_count`, `ignored_count`,
  `missing_count`, and `unsupported_count`; and
- a `history_type` plus optional child `policy_id` and
  `history_{category}_record_key`, `history_{category}_record_keys`, or
  `history_{category}_count` filters.

Per-history categories are `compacted`, `retained`, `ignored`, `missing`, and
`unsupported`. Per-history filters require `history_type`.

## Action Results and Snapshots

The scenario runner appends only
`RetainedAuditCompactionBatchApplyResult` to `World.action_results`. Nested
children do not enter the existing
`retained_audit_compaction_apply_results` stream.

Detailed snapshots append
`retained_audit_compaction_batch_apply_results` after existing retained-audit
result keys. Its aggregate and nested values are copied. Compact
`world.snapshot()` remains unchanged.

Scenarios `085` through `087` cover reverse-order canonical success,
stale/repeated application, and isolation from unselected histories, aliases,
conflicts, security events, delivery/encryption state, canonical identity,
TrafficHub state, and compact snapshots.

## Compatibility and Non-Goals

All eight history labels, exact record keys, policy behavior, decision models,
single-history APIs, replay summaries, actions, assertions, detailed keys, and
compact snapshots retain their prior behavior. v1.12 adds no new history,
filter, or replay dimension; direct mixed-decision apply; strict stale abort;
rollback or transaction machinery; automatic cleanup; workers; retries;
queues; live clocks; networking; DNS; external services; real cryptography;
production E2EE; or production security, privacy, compliance, or retention
guarantees.
