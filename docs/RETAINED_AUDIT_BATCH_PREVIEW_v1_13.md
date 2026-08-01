# Retained Audit Batch Preview v1.13

Status: included in the v1.13.0 source-release snapshot validated on
2026-08-01 (America/Los_Angeles) with 1021 passing tests. The package and CLI
report `darwin-sim 1.13.0`.

This specification adds a deterministic, point-in-time preview for DARWIN's
existing retained-audit batch compaction decisions. Preview is simulator-local,
read-only, and synchronous. It performs no automatic apply, reservation,
deduplication, background work, external persistence, or production retention
behavior.

## Public Result Contracts

`RetainedAuditCompactionPreviewResult` serializes fields in this order:

```text
hub_id
policy_id
history_type
would_compact_record_keys
retained_record_keys
ignored_record_keys
missing_record_keys
unsupported_record_keys
would_compact_count
retained_count
ignored_count
missing_count
unsupported_count
metadata
```

The result validates required identity strings, copied key sequences,
nonnegative counts, and copied JSON-safe metadata.

`RetainedAuditCompactionBatchPreviewResult` is constructed with `hub_id`,
`batch_id`, `preview_results`, and optional metadata. It requires at least two
preview children from the same hub with distinct supported history types and
canonicalizes them using `SUPPORTED_RETAINED_AUDIT_HISTORY_TYPES`. Its summary
serializes:

```text
hub_id
batch_id
history_types
preview_results
would_compact_count
retained_count
ignored_count
missing_count
unsupported_count
metadata
```

`history_types` exposes the represented canonical order. Aggregate counts sum
their matching child counts. `to_summary()`, `to_dict()`, nested results, and
metadata are copied so mutating returned values cannot mutate a result or its
children.

The copied public summarizers are:

```python
summarize_retained_audit_compaction_preview_result(result)
summarize_retained_audit_compaction_batch_preview_result(result)
```

## Preview Helper and Preflight

The only public preview helper is:

```python
preview_retained_audit_compaction_batch(
    registry_hub,
    decisions,
    *,
    batch_id,
    metadata=None,
)
```

There is no standalone single-history preview helper, scenario action, or
assertion. `batch_id` is reusable correlation metadata only: it is not a
reservation, uniqueness constraint, deduplication key, or idempotency ledger.

Before evaluation, preview requires:

- a `RegistryHub` and nonblank `batch_id`;
- JSON-safe dictionary metadata when supplied;
- a list or tuple containing at least two decisions;
- only `RetainedAuditCompactionDecision` values for the supplied hub;
- distinct history types from the eight supported single-history labels; and
- selected histories containing only their expected supported record type.

`mixed`, unsupported, duplicate, mismatched, malformed, and structurally
corrupt inputs are rejected under the same canonical batch preflight as apply.
All selected histories are validated before any apply write. A private shared
evaluator feeds both public operations: preview maps evaluations into preview
results, while apply maps the same evaluations into the existing apply results
and canonical mutations. Batch apply does not call the public preview helper.

## Category and Ordering Semantics

Caller decision order does not affect child ordering. For each selected
history:

- `would_compact_record_keys` contains currently present candidate keys in
  current history order;
- retained and ignored keys contain only currently present matching keys in
  current history order;
- missing keys contain absent candidate keys in decision order; and
- unsupported keys are always empty for a valid batch preview.

Missing candidate keys are nonfatal. One stale decision can report missing
keys while a current decision reports would-compact keys. Zero-candidate and
repeated previews are deterministic.

An immediate batch apply against unchanged RegistryHub state matches the
preview category-by-category after renaming `would_compact` to `compacted` and
excluding intentionally different operation metadata. Preview is point-in-
time only; it does not reserve state or guarantee parity after an intervening
change.

## Metadata Contract

Caller metadata is validated and deep-copied before evaluation. Generated
facts override conflicting caller keys. Aggregate metadata includes these
reserved facts:

- `simulator_local`, `explicit_preview`, `batch_preview`, `batch_id`,
  `batch_id_correlation_only`, `batch_size`, and `history_types`;
- `canonical_batch_order` and `structural_preflight_passed`;
- `stale_keys_reported`, `would_mutate_registry_hub`, and
  `would_mutate_retained_history`;
- `read_only=True`, `registry_hub_mutated=False`,
  `retained_history_mutated=False`, `records_compacted=False`,
  `records_deleted=False`, and `records_rewritten=False`;
- `apply_parity_requires_unchanged_state=True` and
  `apply_parity_runtime_confirmed=False`; and
- simulator-safety negatives `automatic_cleanup`, `cleanup_scheduled`,
  `background_worker`, `retry_loop`, `durable_queue`, `live_timer`,
  `live_clock`, `delivery_behavior_changed`, `traffic_hub_state_changed`,
  `traffic_hub_routing_changed`, `compact_snapshot_changed`,
  `canonical_identity_rewritten`, `networking`, `dns_lookup`,
  `external_services`, and `cryptography`.

The preview never claims runtime-confirmed apply parity. Child metadata also
records canonical batch identity, index, size, read-only preview context, and
`would_mutate_selected_history` without applying that mutation.

## Read-Only and State Boundaries

Direct helper success and every rejection leave the serialized RegistryHub,
all retained histories, and TrafficHub state unchanged. In particular, preview
does not remove, reorder, or rewrite records and does not alter apply results,
aliases, conflicts, security events, delivery/encryption state, canonical
identity, or routing.

Scenario execution intentionally appends one aggregate preview result and one
diagnostic event to `World`; it therefore does not claim whole-`World` byte
identity. Compact `world.snapshot()` remains unchanged.

## Scenario DSL and Assertions

The scenario action is:

```yaml
- action: preview_retained_audit_compaction_batch
  registry_hub: registry_home_088
  batch_id: retained_audit_batch_088
  decision_policy_ids:
    authority_outcome: retained_audit_authority_088
    message_delivery_result: retained_audit_message_delivery_088
  metadata:
    caller_order: reverse_canonical
```

`decision_policy_ids` must map at least two supported distinct history labels
to nonblank policy IDs. The runner resolves exact prior decisions matching hub,
history, and policy, then canonicalizes them before calling the public helper.

The assertion is:

```yaml
- type: retained_audit_compaction_batch_preview_result_contains
  registry_hub: registry_home_088
  batch_id: retained_audit_batch_088
  history_types:
    - message_delivery_result
    - authority_outcome
  would_compact_count: 2
  retained_count: 2
  missing_count: 0
  expected_count: 1
```

It accepts `batch_id`, exact canonical `history_types`, and aggregate
`would_compact_count`, `retained_count`, `ignored_count`, `missing_count`, and
`unsupported_count`. Per-history filters require `history_type` and may add
`policy_id` plus `history_{category}_record_key`,
`history_{category}_record_keys`, or `history_{category}_count`, where category
is `would_compact`, `retained`, `ignored`, `missing`, or `unsupported`.
Counts and `expected_count` are nonnegative integers.

The runner appends only `RetainedAuditCompactionBatchPreviewResult` to
`World.action_results` and logs
`retained_audit_compaction_batch_previewed`. Nested preview children do not
enter an independent action-result stream. Detailed snapshots append copied
`retained_audit_compaction_batch_preview_results` after the existing
`retained_audit_compaction_batch_apply_results` key. Every prior detailed key
and compact `world.snapshot()` retain their order and behavior.

Scenarios `088` through `090` cover reverse-order canonical preview followed
by same-ID immediate apply parity, one-stale/one-current repeatability, and
isolation from selected and unselected histories, identity, aliases,
conflicts, security, delivery, encryption, TrafficHub, compact snapshots, and
nonaggregate action-result streams.

## Compatibility and Non-Goals

All eight history labels and their order, exact record keys, decision and
policy models, replay summaries, single/batch apply outputs and errors,
nonfatal stale behavior, existing actions/assertions, detailed snapshots, and
compact snapshots retain their prior behavior.

v1.13 adds no automatic apply; preview ledger; reservation, uniqueness,
deduplication, or idempotency behavior; strict stale abort; rollback or
transactions; new histories, filters, or replay dimensions; mixed apply;
automatic cleanup; workers; retries; queues; live clocks; networking; DNS;
external services; real cryptography; production E2EE; or production security,
privacy, compliance, or retention guarantees.
