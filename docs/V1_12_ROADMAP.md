# DARWIN v1.12 Roadmap

Status: v1.12.0 source-release snapshot validated on 2026-07-30
(America/Los_Angeles) with 991 passing tests. The package and CLI report
`darwin-sim 1.12.0`.

This roadmap records the intended v1.12.0 source snapshot without using
repository text as evidence of remote publication state. The publication
contract is an annotated `v1.12.0` tag and a GitHub source release created
from the same validated commit. Package-index publication and uploaded release
assets are out of scope.

## Goal

Compose existing single-history retained-audit compaction decisions into one
deterministic multi-history batch. The batch stays simulator-local,
deterministic, source-only, explicit, and synchronous. It preserves all eight
history types, exact record keys, policy behavior, single-history APIs,
compact snapshots, and unrelated RegistryHub and TrafficHub state.

## Sprint 1: Public Batch Result

- Add `RetainedAuditCompactionBatchApplyResult` with public constructor fields
  `hub_id`, `batch_id`, `apply_results`, and `metadata`.
- Canonicalize nested results using
  `SUPPORTED_RETAINED_AUDIT_HISTORY_TYPES`.
- Expose canonical history types, copied child summaries, aggregate
  compacted/retained/ignored/missing/unsupported counts, and copied metadata.
- Preserve the existing single-result model and summaries unchanged.

## Sprint 2: Preflight and Explicit Apply

- Add `apply_retained_audit_compaction_batch` and its summary helper through
  the public model and registry surfaces.
- Require a nonblank batch ID, JSON-safe metadata, and at least two distinct
  supported single-history decisions for the same RegistryHub.
- Reject wrong types, hub mismatches, duplicate histories, `mixed`, unsupported
  labels, and selected-history structural mismatches before any mutation.
- Apply children in canonical history order, independent of caller order.
- Reuse existing single-history apply behavior so stale candidate keys are
  reported while current matches in other histories still compact.

## Sprint 3: Results, Metadata, and Snapshots

- Record only the aggregate batch result in `World.action_results`.
- Append the detailed snapshot key
  `retained_audit_compaction_batch_apply_results` after existing retained-audit
  result keys.
- Keep the existing single-result stream and compact `world.snapshot()`
  unchanged.
- Reserve generated batch identity, order, mutation, and safety metadata so
  caller metadata cannot override those facts.
- Keep nested child apply results available only through the aggregate.

## Sprint 4: Scenario DSL and Coverage

- Add action `apply_retained_audit_compaction_batch` with
  `registry_hub`, `batch_id`, and a `decision_policy_ids` mapping.
- Resolve exact prior hub/history/policy decisions, then canonicalize before
  calling the public helper.
- Add assertion
  `retained_audit_compaction_batch_apply_result_contains` for batch identity,
  exact history order, aggregate counts, and optional per-history
  policy/key/count filters.
- Add scenarios `085` through `087` for reverse-order success, stale/repeated
  apply, and state isolation.
- Keep scenario filenames and metadata contiguous from `001` through `087`,
  and enforce exact generated scenario-index equality in CI.

## Sprint 5: Compatibility and Isolation

- Preserve every existing history type, exact record key, replay mapping,
  policy field, decision model, single-history helper, action, assertion, and
  snapshot key.
- Leave unselected retained histories, aliases, conflicts, security events,
  delivery state, encryption state, canonical identity, TrafficHub state, and
  compact snapshots unchanged.
- Do not add new filters, replay dimensions, history types, mixed-decision
  apply, strict stale aborts, rollback, or transaction machinery.

## Sprint 6: Source-Release Hardening

- Include this roadmap, the batch-apply specification, and permanent `_DRAFT`
  release notes in documentation and release-readiness checks.
- Set package, CLI, smoke-test, and CI expectations to `1.12.0`.
- Retain Python 3.11 through 3.14 CI and the Python 3.11 isolated wheel
  build/install smoke job.
- Require Ruff, pytest, all scenarios, exact scenario-index comparison, exact
  source CLI output, and isolated out-of-tree wheel verification.
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
wheel must install in isolation and report `darwin-sim 1.12.0` from outside
the repository. The wheel is not uploaded.

Final validation passed Ruff, 991 tests, all scenarios `001` through `087`,
exact scenario-index comparison, exact source CLI output, wheel build,
isolated wheel installation, and out-of-tree wheel CLI verification.

## Non-Goals

v1.12 adds no new retained history types; new compaction filters or replay
dimensions; direct `mixed`-decision apply; strict stale-key aborts;
rollback/transaction machinery; automatic cleanup; workers; retries; queues;
live clocks; networking; DNS; external services; real cryptography; production
E2EE; or production security, privacy, anonymity, firewall, DDoS, compliance,
or data-retention guarantees.
