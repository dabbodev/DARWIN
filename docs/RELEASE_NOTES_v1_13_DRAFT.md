# DARWIN v1.13.0 Release Notes

Status: v1.13.0 source-release snapshot preparation. The historical `_DRAFT`
filename is retained permanently for documentation-link compatibility.

Release date: pending validation (America/Los_Angeles).

Final pytest count: pending complete release validation.

The package and CLI report `darwin-sim 1.13.0`. Release publication is limited
to an annotated `v1.13.0` source tag and a GitHub release created from the
exact same validated commit. No package-index publication is performed.
No release assets are uploaded.

This document records preparation requirements without using repository text
as evidence that remote publication has occurred.

## Added in v1.13

- `RetainedAuditCompactionPreviewResult` and
  `RetainedAuditCompactionBatchPreviewResult` with canonical copied summaries
  and would-compact/retained/ignored/missing/unsupported categories.
- Copied public summarizers plus
  `preview_retained_audit_compaction_batch` through existing model and registry
  surfaces; no standalone single-history preview API is added.
- One private canonical preflight/evaluator shared by preview and existing
  batch apply without making apply call the public preview helper.
- Read-only point-in-time evaluation with exact current-history ordering,
  deterministic stale-key reporting, and unchanged-state apply-parity terms.
- Caller metadata isolation and reserved correlation, preflight, would-mutate,
  read-only, parity, and simulator-safety facts.
- Aggregate-only scenario result recording, diagnostic event logging, and one
  appended copied detailed-snapshot section.
- A batch-preview scenario action and assertion with exact history/policy
  resolution, aggregate filters, and per-history key/count filters.

## Scenario Coverage

Scenarios `088` through `090` cover the v1.13 extension:

- `088_retained_audit_batch_preview_success`
- `089_retained_audit_batch_preview_stale`
- `090_retained_audit_batch_preview_isolation`

The v1.13 source snapshot contains a checked-in scenario set from `001`
through `090`.

## Compatibility

- All eight v1.12 retained-audit history labels retain their order, exact
  record keys, policies, replay summaries, and single/batch apply behavior.
- Preview accepts at least two distinct supported single-history decisions for
  one RegistryHub; `mixed`, unsupported, duplicate, mismatched, malformed, and
  structurally invalid batches fail without mutation.
- Would-compact, retained, and ignored keys follow current history order;
  missing keys follow decision order; unsupported is empty for valid previews.
- Missing candidates remain nonfatal, and repeated previews are deterministic.
- `batch_id` is reusable correlation metadata only, never a reservation,
  uniqueness constraint, deduplication key, or idempotency ledger.
- Immediate preview/apply parity requires unchanged hub state and is not
  runtime-confirmed by preview.
- Direct helper success and rejection preserve serialized RegistryHub and
  TrafficHub state. Scenario execution records only the documented aggregate
  result and event side effects.
- Detailed snapshots append one copied aggregate preview key after batch apply.
  Existing detailed streams and compact `world.snapshot()` remain unchanged.

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
`docs/SCENARIO_INDEX.md`. The CLI must report `darwin-sim 1.13.0`, and an
isolated installation of `darwin_sim-1.13.0-py3-none-any.whl` must report the
same version from outside the repository. The wheel is not uploaded.

Preparation status: the validation date and final pytest count remain pending.
No complete passing release-gate set is claimed by this document yet.

## Limits and Non-Goals

v1.13 remains simulator-local, deterministic, source-only, and symbolic. It
adds no automatic apply; preview ledger, reservation, uniqueness,
deduplication, or idempotency behavior; strict stale-key abort; rollback or
transactions; new retained history types; new compaction filters or replay
dimensions; mixed apply; automatic cleanup; workers; retries; queues; live
clocks; networking; DNS; external services; real cryptography; production
E2EE; or production security, privacy, anonymity, firewall, DDoS, compliance,
or data-retention guarantees.
