# DARWIN v1.11.0 Release Notes

Status: v1.11.0 source-release preparation. The historical `_DRAFT` filename
is retained permanently for documentation-link compatibility.

Release date: pending the first complete passing release-gate set.

The package and CLI report `darwin-sim 1.11.0`. Release publication is limited
to an annotated `v1.11.0` source tag and a GitHub release created from the
exact same validated commit. No package-index publication is performed.
No release assets are uploaded.

This document does not claim that validation or remote publication has already
occurred.

## Added in v1.11

- `authority_outcome` appended as the eighth retained-audit history type,
  preserving the order, keys, serialization, and behavior of all seven v1.10
  history types.
- Deterministic ownership through string
  `AliasAuthorityOutcomeRecord.requesting_hub`.
- Generic retained-audit status filtering and grouping based on authority
  `final_status`, while the returned claim `status` remains in exact keys.
- Sorted copied replay maps for requested aliases, granted aliases, target
  devices, and every retained path hub.
- Explicit single-history apply for authority outcomes using the existing
  `authority_history_mutated` flag, stale-key reporting, and deterministic
  repeated apply.

## Scenario Coverage

Scenarios `082` through `084` cover the v1.11 extension:

- `082_retained_audit_authority_outcome_classification`
- `083_retained_audit_authority_outcome_replay`
- `084_retained_audit_authority_outcome_apply`

The v1.11 source preparation contains a checked-in scenario set from `001`
through `084`.

## Compatibility

- The seven v1.10 retained-audit history types retain their order, record
  keys, replay mappings, and behavior.
- Existing retained-audit helper signatures, compaction policy fields, action
  types, assertion types, authority outcome records, authority claim/query
  helpers, and CLI command shapes remain unchanged.
- `RetainedAuditReplaySummary` adds four optional fields at the end of its
  constructor and four appended serialized mappings.
- Retain filters still run before compact filters, and `max_records` still
  applies after classification.
- Missing, non-string, and foreign requesting-hub owners are invisible to the
  generic retained-audit pipeline.
- Mixed and unsupported apply decisions remain deterministic no-ops.
- Authority apply leaves aliases, conflicts, security events, other retained
  histories, action results, canonical identity, TrafficHub routing, and
  compact snapshots unchanged.

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
`docs/SCENARIO_INDEX.md`. The CLI must report `darwin-sim 1.11.0`, and an
isolated installation of `darwin_sim-1.11.0-py3-none-any.whl` must report the
same version from outside the repository. The wheel is not uploaded.

Final validation results and the actual America/Los_Angeles release date are
pending the first complete release-gate pass.

## Limits and Non-Goals

v1.11 remains simulator-local, deterministic, source-only, and symbolic. It
adds no authority-ceiling, record-ID, returned-status, nested-decision, or
boolean replay grouping; new compaction filters; mixed or multi-history apply;
broad event store; alias, conflict, or security-event deletion; automatic
cleanup; workers; retries; durable queues; live clocks; networking; DNS;
external services; real cryptography; production E2EE; or production
security, privacy, anonymity, firewall, DDoS, compliance, or data-retention
guarantees.
