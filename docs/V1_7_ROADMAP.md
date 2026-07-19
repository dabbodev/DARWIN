# DARWIN v1.7 Roadmap

Status: v1.7.0 source-release snapshot. The package and CLI report
`darwin-sim 1.7.0`.

This roadmap records the behavior in the v1.7.0 source snapshot without using
the repository as evidence of remote publication state. The publication
contract is an annotated `v1.7.0` tag and a GitHub source release created from
the same commit. Package-index publication and uploaded release assets are out
of scope.

## Goal

Extend the existing retained-audit compaction and replay helpers to the
RegistryHub-local rendezvous poll-result and lane-admission decision histories.
The extension remains deterministic, explicit, simulator-local, and symbolic.

## Sprint 1: Poll and Admission Classification

- Append `rendezvous_poll_result` and `lane_admission_decision` to the existing
  supported retained-audit history types without reordering the v1.6 entries.
- Adapt poll ownership through `parent_hub_id` and admission ownership through
  `hub_id`; ignore missing or foreign owners deterministically.
- Preserve v1.6 ordering, retain-before-compact filter precedence,
  `max_records`, and unsupported-record behavior.

## Sprint 2: Request-Aware Replay Summaries

- Add optional, deterministically sorted `by_request_id` counts to
  `RetainedAuditReplaySummary` and its JSON-safe summary.
- Group poll and admission records by request, status, reason, and metadata
  `source`; admission records also contribute their optional `offer_id`.
- Keep poll `matched_offer_ids` out of `by_offer_id` and do not add
  target-scope grouping.

## Sprint 3: Explicit Single-History Apply

- Extend `apply_retained_audit_compaction_decision(...)` to select either
  `rendezvous_poll_result_history` or `lane_admission_decision_history`.
- Require one selected supported history for effective mutation. Mixed
  decisions produce the existing deterministic unsupported/no-mutation
  result.
- Remove only currently matching candidate keys, preserve remaining order,
  report stale candidates as missing, and set only the applicable polling or
  admission mutation metadata flag.

## Sprint 4: Scenario DSL and Coverage

- Extend the existing classification, replay, and apply actions and assertions
  with the two new history labels and request-ID count checks.
- Add `070_retained_audit_poll_admission_classification` for mixed read-only
  classification and no mutation.
- Add `071_retained_audit_poll_admission_replay` for grouping and decision
  filtering, including a request ID shared across both histories.
- Add `072_retained_audit_poll_admission_apply` for isolated explicit poll and
  admission applies.
- Keep scenario metadata and `docs/SCENARIO_INDEX.md` contiguous from `001`
  through `072`.

## Sprint 5: Debug Visibility and Compatibility

- Reuse the existing detailed retained-audit decision, replay, and apply
  summary fields with copied JSON-safe data.
- Verify snapshot copy isolation and keep compact `world.snapshot()` output
  unchanged.
- Keep held offers, delivery state, TrafficHub routing, and canonical identity
  unchanged by compaction helpers.

## Sprint 6: Source-Release Hardening

- Include this roadmap, the v1.7 release notes, and the cohesive poll/admission
  specification in documentation readiness checks.
- Set package and CLI metadata to `1.7.0` and record the dated changelog entry.
- Validate Python 3.11, 3.12, 3.13, and 3.14 in CI while retaining
  `requires-python = ">=3.11"`.
- Verify exact CLI version output in CI and build/install a Python 3.11 wheel
  in a separate smoke job without uploading it.

## Release Gates

The source snapshot is accepted only after Ruff, pytest, all checked-in
scenarios `001` through `072`, exact scenario-index generation, CLI version
output, and the wheel-build smoke check pass. Final validation passed Ruff,
909 tests, all 72 scenarios, exact checked-in index verification, CLI output
`darwin-sim 1.7.0`, and an isolated wheel build/install/version smoke check.

## Non-Goals

v1.7 adds no automatic cleanup, background workers, retries, durable queues,
live timers, live clocks, live polling, delivery enforcement, delivery
behavior changes, TrafficHub routing changes, compact snapshot changes,
canonical identity rewrites, real networking, sockets, HTTP/WebSocket
behavior, DNS lookup, external services, real cryptography, production E2EE,
or production security, privacy, anonymity, firewall, DDoS, compliance, or
data-retention guarantees.
