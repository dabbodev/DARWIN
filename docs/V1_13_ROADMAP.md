# DARWIN v1.13 Roadmap

Status: v1.13.0 source-release snapshot validated on 2026-08-01
(America/Los_Angeles) with 1021 passing tests. The package and CLI report
`darwin-sim 1.13.0`.

This roadmap records the intended v1.13.0 source snapshot without using
repository text as evidence of remote publication state. The publication
contract is an annotated `v1.13.0` tag and a GitHub source release created
from the same validated commit. Package-index publication and uploaded release
assets are out of scope.

## Goal

Add a deterministic, read-only preview for at least two existing retained-
audit compaction decisions. The preview uses the same canonical preflight and
evaluation as explicit batch apply, but performs no mutation and creates no
reservation or durable ledger. All eight retained history types, exact record
keys, apply behavior, compact snapshots, and unrelated RegistryHub and
TrafficHub state remain compatible.

## Sprint 1: Public Preview Results

- Add `RetainedAuditCompactionPreviewResult` for one evaluated history with
  would-compact, retained, ignored, missing, and unsupported keys and counts.
- Add `RetainedAuditCompactionBatchPreviewResult` with canonical child order,
  copied child summaries, aggregate category counts, and copied metadata.
- Export copied public summarizers for both result types while preserving all
  existing decision and apply result shapes.

## Sprint 2: Canonical Read-Only Preview

- Add `preview_retained_audit_compaction_batch` with `registry_hub`, at least
  two distinct supported single-history decisions, nonblank `batch_id`, and
  optional JSON-safe metadata.
- Share one private preflight/evaluator between batch preview and batch apply.
  Apply maps evaluations to existing mutations and results; it does not call
  the public preview helper.
- Validate the entire selected batch before any write and reject malformed
  inputs, duplicates, `mixed`, unsupported histories, hub mismatches, invalid
  metadata, and structurally corrupt selected histories.
- Preserve current candidate ordering and nonfatal stale-key behavior. A
  valid preview always reports an empty unsupported category.

## Sprint 3: Metadata, Parity, and Isolation

- Treat `batch_id` as reusable correlation metadata only, never as a
  reservation, uniqueness constraint, deduplication key, or idempotency
  ledger.
- Reserve generated identity, canonical-order, structural-preflight, stale,
  would-mutate, read-only, apply-parity, and simulator-safety facts so caller
  metadata cannot override them.
- State that preview/apply parity requires unchanged hub state and is not
  runtime-confirmed by the preview.
- Prove direct preview success and rejection leave serialized RegistryHub,
  retained histories, and TrafficHub state unchanged.

## Sprint 4: Scenario DSL and Coverage

- Add action `preview_retained_audit_compaction_batch` with `registry_hub`,
  `batch_id`, `decision_policy_ids`, and optional metadata.
- Add assertion
  `retained_audit_compaction_batch_preview_result_contains` for batch identity,
  exact history order, aggregate counts, and per-history policy/key/count
  filters.
- Record only the aggregate preview in `World.action_results`, log
  `retained_audit_compaction_batch_previewed`, and append copied detailed
  `retained_audit_compaction_batch_preview_results` after the existing batch-
  apply section. Keep compact `world.snapshot()` unchanged.
- Add scenarios `088` through `090` for reverse-order canonical preview plus
  immediate apply parity, stale repeatability, and broad state isolation.
- Keep scenario filenames and metadata contiguous from `001` through `090`
  and enforce exact generated scenario-index equality in CI.

## Sprint 5: Compatibility

- Preserve all eight history labels and their order, exact keys, policies,
  replay summaries, single and batch apply outputs/errors, metadata behavior,
  nonfatal stale semantics, existing action-result streams, and existing
  detailed snapshot keys.
- Leave unselected histories, aliases, conflicts, security events, delivery
  and encryption state, canonical identity, TrafficHub state, and compact
  snapshots unchanged.
- Add no standalone single-history preview helper, action, or assertion.

## Sprint 6: Source-Release Hardening

- Include this roadmap, the batch-preview specification, and permanent
  `_DRAFT` release notes in documentation and release-readiness checks.
- Set package, CLI, smoke-test, source/wheel assertions, and CI expectations to
  exact output `darwin-sim 1.13.0`.
- Retain Python 3.11 through 3.14 CI and the separate Python 3.11 isolated
  wheel build/install smoke job.
- Require Ruff, pytest, all scenarios, exact scenario-index comparison, exact
  source CLI output, wheel build, and isolated out-of-tree wheel verification.
- Record the actual America/Los_Angeles validation date and final pytest count
  only after the complete release gates first pass.

## Release Gates

The source snapshot is accepted only after these checks pass on the release
branch and again on the exact merged `main` commit:

```bash
python -m ruff check .
python -m pytest
python scripts/run_all_scenarios.py
python -m darwin.cli.main scenario-index
python -m darwin.cli.main --version
python -m build --wheel
```

The generated scenario index must exactly match `docs/SCENARIO_INDEX.md`. The
exact `darwin_sim-1.13.0-py3-none-any.whl` must install in isolation and report
`darwin-sim 1.13.0` from outside the repository. The wheel is a validation
artifact only and is not uploaded.

Final validation passed Ruff, 1021 tests, all scenarios `001` through `090`,
exact scenario-index comparison, exact source CLI output, wheel build,
isolated wheel installation, and out-of-tree wheel CLI verification.

## Non-Goals

v1.13 adds no automatic apply; preview ledger, reservation, uniqueness, or
deduplication behavior; strict stale abort; rollback or transactions; new
history types; new compaction filters or replay dimensions; mixed apply;
automatic cleanup; workers; retries; queues; live clocks; networking; DNS;
external services; real cryptography; production E2EE; or production security,
privacy, anonymity, firewall, DDoS, compliance, or data-retention guarantees.
It performs no package-index publication and uploads no release assets.
