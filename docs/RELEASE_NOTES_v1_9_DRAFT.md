# DARWIN v1.9.0 Release Notes

Status: v1.9.0 source-release snapshot in final validation. The historical
`_DRAFT` filename is retained for documentation-link compatibility; this
content describes the intended final source snapshot rather than an unfinished
feature proposal.

The package and CLI report `darwin-sim 1.9.0`. Release publication is limited
to an annotated `v1.9.0` source tag and a GitHub release created from the exact
same validated commit. No package-index publication is performed.
No release assets are uploaded.

This document does not claim that those remote publication actions have
already occurred.

## Added in v1.9

- `encryption_policy_decision` appended as the sixth retained-audit history
  type, preserving the order, keys, serialization, and behavior of all five
  v1.8 history types.
- Deterministic policy-decision ownership and keys derived only from string
  RegistryHub metadata and top-level policy, mailbox, message, lane, status,
  and reason fields.
- Sorted, copied replay counts by policy ID and lane signature alongside all
  existing replay dimensions.
- Explicit single-history apply for encryption-policy decision history with
  deterministic stale-key and repeated-apply behavior.
- Scenario DSL replay assertions for policy and lane counts, detailed snapshot
  copy isolation, and exact scenario-index enforcement in CI.

## Scenario Coverage

Scenarios `076` through `078` cover the v1.9 extension:

- `076_retained_audit_encryption_policy_classification`
- `077_retained_audit_encryption_policy_replay`
- `078_retained_audit_encryption_policy_apply`

The v1.9 source snapshot contains a checked-in scenario set from `001` through `078`.

## Compatibility

- The five v1.8 retained-audit history types retain their order, record keys,
  and behavior; new replay dataclass fields are appended.
- Retain filters still run before compact filters, and `max_records` still
  applies after classification.
- Missing, non-string, and foreign `metadata["registry_hub"]` owners remain
  invisible to the generic retained-audit pipeline.
- Mixed and unsupported apply decisions remain deterministic no-ops.
- Policy-history apply leaves encrypted results and nested policy snapshots,
  direct delivery results, inboxes, registry configuration, held offers,
  TrafficHub routing, canonical identity, and compact snapshots unchanged.
- Additive `by_policy_id` and `by_lane_signature` keys can affect callers that
  compare serialized dictionaries exactly; all old fields and values remain.

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
`docs/SCENARIO_INDEX.md`. The CLI must report `darwin-sim 1.9.0`, and an
isolated installation of `darwin_sim-1.9.0-py3-none-any.whl` must report the
same version from outside the repository. The wheel is not uploaded.

The actual America/Los_Angeles release date and final pytest count will be
recorded only after the complete release gates pass.

## Limits and Non-Goals

v1.9 remains simulator-local, deterministic, source-only, and symbolic. It
adds no direct message-delivery result compaction, nested gate or delivery
replay dimensions, new compaction filters, mixed or multi-history apply,
automatic cleanup, workers, retries, durable queues, live timers, live clocks,
live polling, delivery enforcement, delivery behavior changes, TrafficHub routing changes,
compact snapshot changes, canonical identity rewrites, real networking,
DNS, external services, real cryptography, production E2EE, or
production security, privacy, anonymity, firewall, DDoS, compliance, or
data-retention guarantees.
