# DARWIN v1.14 Roadmap

Status: v1.14.0 source-release snapshot prepared for validation. The actual
America/Los_Angeles validation date and final pytest count remain pending the
first complete passing release-gate set. The package and CLI report
`darwin-sim 1.14.0`.

This roadmap records the intended v1.14.0 source snapshot without using
repository text as evidence of remote publication state. The publication
contract is an annotated `v1.14.0` tag and a GitHub source release created
from the same validated commit. Package-index publication and uploaded release
assets are out of scope.

## Goal

Add an opt-in strict-stale guard to existing retained-audit batch apply.
Strict mode performs the existing complete read-only preflight and canonical
evaluation, then rejects the whole batch if any compaction candidate is
missing. The default remains the v1.13 nonfatal stale behavior. Preview stays
point-in-time and read-only and does not reserve state or promise later apply
success.

## Sprint 1: Strict Public Apply Contract

- Append keyword-only `strict_stale_abort: bool = False` to
  `apply_retained_audit_compaction_batch` without changing existing
  positional or keyword order.
- Preserve complete structural preflight and canonical eight-history
  evaluation before validating the strict flag.
- Reject non-boolean strict values without coercion.
- In strict mode, collect missing compaction-candidate keys in canonical
  history order and original decision-key order, then reject before the first
  result construction or write.

## Sprint 2: Atomicity and Compatibility

- Leave the complete serialized RegistryHub unchanged on strict rejection,
  including histories, apply-result streams, detailed snapshots, and events.
- Preserve empty-candidate strict decisions as valid no-ops.
- Reject a decision containing both current and missing candidate keys without
  compacting its current keys or any other selected history.
- Preserve byte-compatible omitted and explicit-false behavior, including
  partial application, missing-key reporting, repeat no-ops, child metadata,
  and result serialization.

## Sprint 3: Metadata and Scenario DSL

- Set aggregate `strict_stale_abort` metadata from the actual option and let
  generated metadata override caller attempts to spoof it.
- Keep child metadata, result types, snapshots, events, and exports unchanged.
- Extend `apply_retained_audit_compaction_batch` scenario actions with an
  optional strictly boolean `strict_stale_abort` field.
- Extend
  `retained_audit_compaction_batch_apply_result_contains` with an optional
  aggregate-metadata `strict_stale_abort` filter.

## Sprint 4: Coverage and Scenarios

- Prove strict success, invalid-type rejection, single- and multi-history
  atomic stale rejection, deterministic ordering, structural-preflight
  precedence, repeat rejection, zero-candidate no-op, generated-metadata
  precedence, preview behavior, and exact default compatibility in Python.
- Add scenarios `091` through `093` for strict success, explicit-false
  legacy compatibility, and strict isolation.
- Keep scenario filenames and metadata contiguous from `001` through `093`
  and enforce exact generated scenario-index equality in CI.
- Keep exception-path coverage in Python tests; the scenario DSL does not gain
  an expected-action-error mechanism.

## Sprint 5: Source-Release Hardening

- Include this roadmap, the strict-stale specification, and permanent
  `_DRAFT` release notes in documentation and release-readiness checks.
- Set package, CLI, smoke-test, source/wheel assertions, and CI expectations to
  exact output `darwin-sim 1.14.0`.
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

The generated scenario index must exactly match
`docs/SCENARIO_INDEX.md`. The exact
`darwin_sim-1.14.0-py3-none-any.whl` must install in isolation and report
`darwin-sim 1.14.0` from outside the repository. The wheel is a validation
artifact only and is not uploaded.

Final validation is pending the first complete passing gate set.

## Non-Goals

v1.14 adds no strict behavior to single-history apply or batch preview;
automatic apply; preview reservation or parity guarantees; rollback or
transactions; new models, exports, helpers, result/event types, snapshot keys,
histories, compaction filters, or replay dimensions; mixed apply; automatic
cleanup; workers; retries; queues; live clocks; networking; DNS; external
services; real cryptography; production E2EE; or production security, privacy,
anonymity, firewall, DDoS, compliance, or data-retention guarantees. It
performs no package-index publication and uploads no release assets.
