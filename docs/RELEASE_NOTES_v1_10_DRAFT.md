# DARWIN v1.10.0 Release Notes

Status: v1.10.0 source-release snapshot. The historical `_DRAFT` filename is
retained for documentation-link compatibility; this content describes the
final source snapshot rather than an unfinished feature proposal.

Release date: `2026-07-27` (America/Los_Angeles).

The package and CLI report `darwin-sim 1.10.0`. Release publication is limited
to an annotated `v1.10.0` source tag and a GitHub release created from the
exact same validated commit. No package-index publication is performed.
No release assets are uploaded.

This document does not claim that those remote publication actions have
already occurred.

## Added in v1.10

- `message_delivery_result` appended as the seventh retained-audit history
  type, preserving the order, keys, serialization, and behavior of all six
  v1.9 history types.
- Deterministic direct-delivery ownership through additive string
  `metadata["registry_hub"]` on results created by
  `deliver_message_to_mailbox(...)`.
- Exact keys using top-level message, recipient address, resolved mailbox,
  lane, status, and reason fields.
- Existing sorted, copied replay counts reused for message ID, mailbox ID,
  lane signature, status, reason, and optional source.
- Explicit single-history apply for direct message-delivery results with
  isolated mutation flags, stale-key reporting, and deterministic repeated
  apply.

## Scenario Coverage

Scenarios `079` through `081` cover the v1.10 extension:

- `079_retained_audit_message_delivery_classification`
- `080_retained_audit_message_delivery_replay`
- `081_retained_audit_message_delivery_apply`

The v1.10 source snapshot contains a checked-in scenario set from `001`
through `081`.

## Compatibility

- The six v1.9 retained-audit history types retain their order, record keys,
  and behavior; no retained-audit dataclass field or public helper signature
  changes.
- `MessageDeliveryResult.to_summary()` keeps its top-level field order, while
  helper-created result metadata gains the owning `registry_hub`.
- Retain filters still run before compact filters, and `max_records` still
  applies after classification.
- Missing, non-string, and foreign `metadata["registry_hub"]` owners are
  invisible to the generic retained-audit pipeline.
- Mixed and unsupported apply decisions remain deterministic no-ops.
- Direct-result apply leaves inboxes, delivered envelopes, events, action
  results, encrypted and policy histories, registry configuration, held
  offers, TrafficHub routing, canonical identity, and compact snapshots
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
`docs/SCENARIO_INDEX.md`. The CLI must report `darwin-sim 1.10.0`, and an
isolated installation of `darwin_sim-1.10.0-py3-none-any.whl` must report the
same version from outside the repository. The wheel is not uploaded.

Final validation passed `python -m ruff check .`, `python -m pytest` with 950
tests, all scenarios `001` through `081`, exact checked-in scenario-index
verification, CLI output `darwin-sim 1.10.0`, and an isolated out-of-tree
install/version smoke check for `darwin_sim-1.10.0-py3-none-any.whl`. The
wheel is not uploaded.

## Limits and Non-Goals

v1.10 remains simulator-local, deterministic, source-only, and symbolic. It
adds no new compaction filters, nested gate or delivery replay dimensions,
mixed or multi-history apply, inbox deletion, automatic cleanup, workers,
retries, durable queues, live timers, live clocks, live polling, delivery
enforcement, delivery behavior changes, TrafficHub routing changes, compact
snapshot changes, canonical identity rewrites, real networking, DNS, external
services, real cryptography, production E2EE, or production security, privacy,
anonymity, firewall, DDoS, compliance, or data-retention guarantees.
