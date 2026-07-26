# DARWIN v1.9 Roadmap

Status: v1.9.0 source-release snapshot dated 2026-07-26
(America/Los_Angeles). The package and CLI report `darwin-sim 1.9.0`.

This roadmap records the intended behavior of the v1.9.0 source snapshot
without using repository text as evidence of remote publication state. The
publication contract is an annotated `v1.9.0` tag and a GitHub source release
created from the same validated commit. Package-index publication and uploaded
release assets are out of scope.

## Goal

Extend DARWIN's deterministic retained-audit classification, replay, and
explicit single-history apply pipeline to
`RegistryHub.encryption_policy_decision_history`. The extension stays
simulator-local, deterministic, source-only, and symbolic.

## Sprint 1: Encryption-Policy Classification

- Append `encryption_policy_decision` after the five v1.8 supported history
  types without changing their order, keys, serialization, or behavior.
- Derive ownership only from string `metadata["registry_hub"]`; ignore missing,
  non-string, and foreign owners deterministically.
- Classify top-level policy, mailbox, message, lane, status, and reason fields
  plus optional string `metadata["source"]`.
- Preserve retain-before-compact precedence, post-classification
  `max_records`, caller order, unsupported-record handling, and read-only
  classification.

## Sprint 2: Policy- and Lane-Aware Replay

- Append optional, sorted `by_policy_id` and `by_lane_signature` count mappings
  to `RetainedAuditReplaySummary`.
- Validate non-negative integer counts and return copied mappings from
  serialization helpers.
- Group only top-level policy and lane values. In particular, encrypted-
  delivery results contribute their top-level lane but not a nested gate
  policy.
- Preserve all v1.8 replay dimensions and decision-category behavior.

## Sprint 3: Explicit Single-History Apply

- Select `RegistryHub.encryption_policy_decision_history` for the new history
  label.
- Remove only currently matching candidate keys, preserve remaining order,
  report stale keys as missing, and keep repeated apply deterministic.
- Set `encryption_policy_history_mutated` only when a policy-decision record is
  removed.
- Leave encrypted and direct delivery results, nested policy snapshots,
  inboxes, registry configuration, held offers, TrafficHub state and routing,
  canonical identities, and compact snapshots unchanged.

## Sprint 4: Scenario DSL and Coverage

- Reuse the existing classify, replay, apply, and
  `evaluate_mailbox_encryption_policy` actions.
- Add policy-ID and lane-signature replay assertions without adding evaluator
  inputs or behavior.
- Add scenarios `076` through `078` for classification, replay, and isolated
  apply.
- Keep scenario filenames and metadata contiguous from `001` through `078`,
  and enforce exact generated scenario-index equality in CI.

## Sprint 5: Compatibility and Debug Visibility

- Reuse the existing detailed retained-audit decision, replay, and apply
  sections with copied JSON-safe summaries.
- Keep compact `world.snapshot()` output unchanged.
- Prove all five v1.8 history key forms and the existing replay fields retain
  their behavior.
- Keep mixed and unsupported apply decisions deterministic no-ops.

## Sprint 6: Source-Release Hardening

- Include this roadmap, the encryption-policy specification, and release notes
  in documentation and release-readiness checks.
- Set package, CLI, smoke-test, and CI expectations to `1.9.0`.
- Retain Python 3.11 through 3.14 CI and the Python 3.11 isolated wheel
  build/install smoke job.
- Require Ruff, pytest, all scenarios, exact scenario-index comparison, exact
  CLI output, and isolated out-of-tree wheel verification.
- Record the actual America/Los_Angeles release date and final pytest count
  only after the final passing validation. The recorded results are
  2026-07-26 and 935 tests.

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
wheel must install in isolation and report `darwin-sim 1.9.0` from outside the
repository. The wheel is not uploaded.

Final validation passed Ruff, 935 tests, all scenarios `001` through `078`,
exact checked-in scenario-index verification, CLI output
`darwin-sim 1.9.0`, and an isolated out-of-tree install/version smoke check for
`darwin_sim-1.9.0-py3-none-any.whl`.

## Non-Goals

v1.9 adds no direct message-delivery result compaction, nested gate or delivery
replay dimensions, new compaction filters, mixed or multi-history apply,
automatic cleanup, workers, retries, durable queues, live timers, live clocks,
live polling, delivery enforcement, delivery behavior changes, TrafficHub
routing changes, compact snapshot changes, canonical identity rewrites,
networking, DNS, external services, real cryptography, production E2EE, or
production security, privacy, anonymity, firewall, DDoS, compliance, or
data-retention guarantees.
