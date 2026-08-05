# Retained Audit Strict-Stale Batch Apply v1.14

Status: included in the v1.14.0 source-release snapshot prepared for
validation. The actual America/Los_Angeles validation date and final pytest
count are pending the first complete passing release-gate set. The package and
CLI report `darwin-sim 1.14.0`.

This specification adds one opt-in fail-closed stale-candidate guard to
DARWIN's existing explicit retained-audit batch apply. The behavior remains
simulator-local, deterministic, synchronous, and source-only.

## Public Apply Contract

The existing helper appends one keyword-only parameter:

```python
apply_retained_audit_compaction_batch(
    registry_hub,
    decisions,
    *,
    batch_id,
    metadata=None,
    strict_stale_abort: bool = False,
) -> RetainedAuditCompactionBatchApplyResult
```

Existing parameter order and the result type are unchanged. Omission and
explicit `False` preserve v1.13 behavior. After the existing complete
read-only structural preflight and canonical evaluation, non-boolean values
raise:

```text
TypeError("strict_stale_abort must be a boolean")
```

Booleans are accepted exactly; integers, strings, `None`, lists, mappings,
and other truthy or falsey values are not coerced.

## Strict Stale Rejection

When `strict_stale_abort=True`, batch apply inspects the canonical
evaluations before constructing child results or performing a write. Missing
compaction-candidate keys are grouped by canonical
`SUPPORTED_RETAINED_AUDIT_HISTORY_TYPES` order. Within each history, missing
keys retain their original decision-key order.

If any selected history has a missing compaction-candidate key, apply raises:

```text
strict_stale_abort rejected batch {batch_id}: missing compaction candidate record keys {missing_by_history}
```

The rejection is batch-atomic:

- no current candidate is compacted, including a current key in the same
  decision as a missing key;
- no child or aggregate result is constructed or appended;
- no action-result entry, detailed-snapshot entry, or event is created; and
- the complete serialized RegistryHub remains byte-for-byte equivalent.

Repeated strict attempts against unchanged stale state reject identically.
An empty-candidate decision contributes no missing key and remains a valid
strict no-op.

Structural preflight retains precedence. Invalid hub identity, decisions,
history labels, duplicate histories, `mixed`, metadata, or selected-history
record structure fail under their existing errors before strict flag type or
stale evaluation can change the outcome.

## Default Compatibility

With the option omitted or explicitly false:

- one stale child can report missing keys while another selected history
  compacts current candidates;
- repeated batches remain deterministic missing-key no-ops;
- canonical child order, aggregate and child summaries, errors, events, and
  detailed snapshots retain their v1.13 shapes; and
- child metadata remains unchanged.

These omitted and explicit-false paths remain byte-compatible with v1.13.

The generated aggregate metadata field `strict_stale_abort` now records the
actual boolean option. Generated metadata overrides a caller-supplied value
with the same key. No other aggregate or child metadata contract changes.

## Preview Boundary

`preview_retained_audit_compaction_batch` remains read-only and unchanged.
It continues to report current would-compact and missing categories without a
strict option. Preview is point-in-time and correlation-only: it creates no
reservation, lock, deduplication record, or parity guarantee. An intervening
state change can therefore make a later strict apply reject.

## Scenario DSL and Assertion

The existing action accepts optional `strict_stale_abort`, parsed strictly as
a YAML boolean:

```yaml
- action: apply_retained_audit_compaction_batch
  registry_hub: registry_home_091
  batch_id: retained_audit_batch_091
  strict_stale_abort: true
  decision_policy_ids:
    authority_outcome: retained_audit_authority_091
    message_delivery_result: retained_audit_message_delivery_091
```

Omission defaults to false. Non-boolean values are rejected rather than
coerced. The existing assertion optionally filters the aggregate metadata
value:

```yaml
- type: retained_audit_compaction_batch_apply_result_contains
  registry_hub: registry_home_091
  batch_id: retained_audit_batch_091
  strict_stale_abort: true
  compacted_count: 2
  missing_count: 0
  expected_count: 1
```

All existing aggregate and per-history filters retain their behavior. The DSL
does not add expected-action-error handling; strict rejection paths are tested
directly in Python.

## Scenario Coverage

Scenarios `091` through `093` cover:

- `091_retained_audit_strict_stale_batch_success`: reverse-ordered fresh
  decisions apply canonically with strict metadata true and no missing keys;
- `092_retained_audit_strict_stale_batch_default_compatibility`: explicit
  false preserves legacy partial application with one stale child; and
- `093_retained_audit_strict_stale_batch_isolation`: strict success changes
  only selected histories while preserving identity, delivery, encryption,
  security, TrafficHub, and compact-snapshot boundaries.

The checked-in scenario set is contiguous from `001` through `093`.
Atomic exception paths, deterministic multi-history error ordering,
structural-preflight precedence, repeat rejection, zero-candidate strict
no-op, caller metadata precedence, preview behavior, and exact omitted/false
compatibility are covered by focused Python tests.

## Compatibility and Non-Goals

All eight history labels and their order, exact record keys, policies, replay
summaries, models, public exports, existing result and event types, snapshot
keys, filters, and replay dimensions retain their prior contracts. v1.14 adds
no strict mode to single-history apply or preview; automatic apply; preview
reservation; rollback or transactions; new histories, filters, or replay
dimensions; mixed apply; automatic cleanup; workers; retries; queues; live
clocks; networking; DNS; external services; real cryptography; production
E2EE; or production security, privacy, compliance, or retention guarantees.
