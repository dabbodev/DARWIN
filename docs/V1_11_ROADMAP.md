# DARWIN v1.11 Roadmap

Status: v1.11.0 source-release snapshot validated on 2026-07-29
(America/Los_Angeles) with 964 passing tests. The package and CLI report
`darwin-sim 1.11.0`.

This roadmap records the intended v1.11.0 source snapshot without using
repository text as evidence of remote publication state. The publication
contract is an annotated `v1.11.0` tag and a GitHub source release created
from the same validated commit. Package-index publication and uploaded release
assets are out of scope.

## Goal

Extend DARWIN's deterministic retained-audit classification, replay, and
explicit single-history apply pipeline to
`RegistryHub.authority_outcome_history`. The extension stays simulator-local,
deterministic, source-only, and symbolic and does not change authority-chain
claims, alias resolution, conflicts, canonical identity, or TrafficHub state.

## Sprint 1: Authority-Outcome Classification

- Append `authority_outcome` after the seven v1.10 supported history types
  without changing their order, keys, serialization, or behavior.
- Use string `AliasAuthorityOutcomeRecord.requesting_hub` as the owning
  RegistryHub; ignore missing, non-string, and foreign owners.
- Map the generic retained-audit status dimension to `final_status`.
- Preserve the returned claim `status` in the exact record key without using
  it for generic status filters.
- Preserve retain-before-compact precedence, post-classification
  `max_records`, caller order, unsupported-record handling, and read-only
  classification.

## Sprint 2: Authority Replay Dimensions

- Add sorted copied replay mappings for requested aliases, granted aliases,
  target devices, and each retained path hub.
- Reuse existing history, final-status, reason, source, and decision-category
  groupings.
- Do not add authority-ceiling, record-ID, returned-status, nested-decision,
  or boolean groupings.
- Do not add alias, device, or path compaction filters.

## Sprint 3: Explicit Single-History Apply

- Select `RegistryHub.authority_outcome_history` for the new history label.
- Remove only currently matching candidate keys, preserve remaining order,
  report stale keys as missing, and keep repeated apply deterministic.
- Set the existing `authority_history_mutated` metadata flag only when an
  authority outcome is removed.
- Leave aliases, conflicts, security events, authority configuration, other
  retained histories, action results, canonical identity, TrafficHub state,
  and compact snapshots unchanged.

## Sprint 4: Scenario DSL and Coverage

- Reuse the existing authority-chain claim, classify, replay, and apply
  actions.
- Extend the existing replay assertion with alias, device, and path-hub
  value/count pairs; add no new action or assertion type.
- Add scenarios `082` through `084` for classification, replay, and isolated
  apply.
- Keep scenario filenames and metadata contiguous from `001` through `084`,
  and enforce exact generated scenario-index equality in CI.

## Sprint 5: Compatibility and Debug Visibility

- Keep the first seven history labels, keys, replay mappings, and apply
  behavior unchanged.
- Preserve `AliasAuthorityOutcomeRecord`, authority claim/query helpers,
  existing helper signatures, CLI commands, and existing detailed-summary key
  order.
- Append `by_requested_alias`, `by_granted_alias`, `by_target_device`, and
  `by_path_hub` to detailed replay summaries.
- Keep compact `world.snapshot()` output unchanged.

## Sprint 6: Source-Release Hardening

- Include this roadmap, the authority-outcome retained-audit specification,
  and release notes in documentation and release-readiness checks.
- Set package, CLI, smoke-test, and CI expectations to `1.11.0`.
- Retain Python 3.11 through 3.14 CI and the Python 3.11 isolated wheel
  build/install smoke job.
- Require Ruff, pytest, all scenarios, exact scenario-index comparison, exact
  CLI output, and isolated out-of-tree wheel verification.
- Record the actual America/Los_Angeles release date and final pytest count
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
wheel must install in isolation and report `darwin-sim 1.11.0` from outside
the repository. The wheel is not uploaded.

Final validation passed Ruff, 964 tests, all scenarios `001` through `084`,
exact scenario-index comparison, exact source CLI output, wheel build,
isolated wheel installation, and out-of-tree wheel CLI verification.

## Non-Goals

v1.11 adds no authority-ceiling, record-ID, returned-status, nested-decision,
or boolean replay grouping; new compaction filters; mixed or multi-history
apply; alias, conflict, security-event, or canonical-identity deletion;
automatic cleanup; workers; retries; durable queues; live timers; live clocks;
networking; DNS; external services; real cryptography; production E2EE; or
production security, privacy, anonymity, firewall, DDoS, compliance, or
data-retention guarantees.
