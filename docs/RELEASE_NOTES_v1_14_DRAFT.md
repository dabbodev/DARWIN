# DARWIN v1.14.0 Release Notes

Status: v1.14.0 source-release snapshot. The historical `_DRAFT` filename is
retained permanently for documentation-link compatibility.

Release date: 2026-08-05 (America/Los_Angeles).

Final pytest count: 1056 passing tests.

The package and CLI report `darwin-sim 1.14.0`. Release publication is
limited to an annotated `v1.14.0` source tag and a GitHub release created
from the exact same validated commit. No package-index publication is performed.
No release assets are uploaded.

This document records source-release requirements without using repository
text as evidence that remote publication has occurred.

## Added in v1.14

- Optional keyword-only `strict_stale_abort: bool = False` on existing
  `apply_retained_audit_compaction_batch`.
- Fail-closed whole-batch rejection when strict mode finds any missing
  compaction-candidate key after complete canonical preflight and evaluation.
- Deterministic missing-key diagnostics grouped by canonical history order and
  original decision-key order.
- An optional strictly boolean scenario-action field and aggregate-metadata
  assertion filter, both named `strict_stale_abort`.
- Scenarios `091` through `093` for strict success, explicit-false legacy
  compatibility, and state isolation.

## Atomicity and Compatibility

- Strict stale rejection occurs before child-result construction and before
  the first write. It creates no result, action-result entry, snapshot entry,
  or event and leaves the complete serialized RegistryHub unchanged.
- TrafficHub state, canonical identity, delivery, encryption, security, and
  compact snapshot boundaries remain unchanged outside selected retained
  histories.
- A decision mixing current and missing candidates rejects wholesale.
  Empty-candidate decisions remain valid strict no-ops.
- Existing structural preflight retains precedence over strict flag validation
  and stale rejection.
- Omitted or explicit false remains byte-compatible with v1.13 partial apply,
  missing-key reporting, repeat no-op behavior, child metadata, and result
  serialization.
- Generated aggregate metadata reports the actual strict flag and overrides
  caller spoofing. Child metadata is unchanged.
- Batch preview remains point-in-time and read-only. It creates no reservation
  and does not guarantee a later strict apply.

## Scenario Coverage

Scenarios `091` through `093` cover the v1.14 extension:

- `091_retained_audit_strict_stale_batch_success`
- `092_retained_audit_strict_stale_batch_default_compatibility`
- `093_retained_audit_strict_stale_batch_isolation`

The v1.14 source snapshot contains a checked-in scenario set from `001`
through `093`.

Strict exception paths remain in Python tests because the scenario DSL does
not add expected-action-error handling.

## Validation Contract

The source release is gated by:

```bash
python -m ruff check .
python -m pytest
python scripts/run_all_scenarios.py
python -m darwin.cli.main scenario-index
python -m darwin.cli.main --version
python -m build --wheel
```

The generated scenario-index stdout must exactly match
`docs/SCENARIO_INDEX.md`. The source and isolated-wheel CLI must report
`darwin-sim 1.14.0`; the wheel is a validation artifact only and is not
uploaded.

Final validation passed Ruff, 1056 tests, all scenarios `001` through `093`,
exact scenario-index comparison, exact source CLI output, wheel build,
isolated wheel installation, and out-of-tree wheel CLI verification.

## Limits and Non-Goals

v1.14 remains simulator-local, deterministic, source-only, and symbolic. It
adds no strict mode to single-history apply or batch preview; automatic apply;
preview reservation, lock, deduplication, or parity guarantees; rollback or
transactions; new models, exports, helpers, result/event types, snapshot keys,
histories, compaction filters, or replay dimensions; mixed apply; automatic
cleanup; workers; retries; queues; live clocks; networking; DNS; external
services; real cryptography; production E2EE; or production security, privacy,
anonymity, firewall, DDoS, compliance, or data-retention guarantees.
