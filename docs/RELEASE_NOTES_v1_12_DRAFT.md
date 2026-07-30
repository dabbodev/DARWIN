# DARWIN v1.12.0 Release Notes

Status: v1.12.0 source-release snapshot prepared for validation. The
historical `_DRAFT` filename is retained permanently for documentation-link
compatibility.

Release date: pending the first complete passing release gate set
(America/Los_Angeles).

Final pytest count: pending the first complete passing release gate set.

The package and CLI report `darwin-sim 1.12.0`. Release publication is limited
to an annotated `v1.12.0` source tag and a GitHub release created from the
exact same validated commit. No package-index publication is performed.
No release assets are uploaded.

This document records local validation without using repository text as
evidence that remote publication has occurred.

## Added in v1.12

- `RetainedAuditCompactionBatchApplyResult` with canonical nested
  single-history results, aggregate category counts, and copied metadata.
- Public batch apply and summary helpers exported through existing model and
  registry surfaces.
- Whole-batch validation and structural preflight before the first mutation.
- Canonical processing using the unchanged eight-history supported order,
  independent of caller order.
- Stale-child reporting that does not block current candidates in another
  selected history.
- Aggregate-only scenario action-result recording and an appended copied
  detailed-snapshot section.
- A batch scenario action and assertion with exact history/policy resolution,
  aggregate filters, and per-history key/count filters.

## Scenario Coverage

Scenarios `085` through `087` cover the v1.12 extension:

- `085_retained_audit_batch_apply_success`
- `086_retained_audit_batch_apply_stale_repeat`
- `087_retained_audit_batch_apply_isolation`

The v1.12 source snapshot contains a checked-in scenario set from `001`
through `087`.

## Compatibility

- All eight v1.11 retained-audit history types retain their order, exact
  record keys, policies, summaries, and single-history behavior.
- Batch apply accepts at least two distinct supported single-history decisions
  for one RegistryHub; `mixed`, unsupported, duplicate, mismatched, malformed,
  and structurally invalid batches fail before mutation.
- Nested child apply results retain the existing single-result schema but do
  not enter the existing single-result action stream.
- Missing candidate keys remain nonfatal and deterministic.
- Caller metadata is copied and cannot override generated identity, order,
  mutation, or safety facts.
- Detailed snapshots append one new copied aggregate result key. Compact
  `world.snapshot()` output remains unchanged.
- Batch apply leaves unselected histories, aliases, conflicts, security
  events, delivery/encryption state, canonical identity, and TrafficHub state
  unchanged.

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
`docs/SCENARIO_INDEX.md`. The CLI must report `darwin-sim 1.12.0`, and an
isolated installation of `darwin_sim-1.12.0-py3-none-any.whl` must report the
same version from outside the repository. The wheel is not uploaded.

Final validation facts are pending the first complete passing release gate
set.

## Limits and Non-Goals

v1.12 remains simulator-local, deterministic, source-only, and symbolic. It
adds no new retained history types; new compaction filters or replay
dimensions; direct `mixed`-decision apply; strict stale-key aborts; rollback
or transaction machinery; automatic cleanup; workers; retries; durable
queues; live clocks; networking; DNS; external services; real cryptography;
production E2EE; or production security, privacy, anonymity, firewall, DDoS,
compliance, or data-retention guarantees.
