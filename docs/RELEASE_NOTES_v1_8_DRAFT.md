# DARWIN v1.8.0 Release Notes

Status: v1.8.0 source-release snapshot. The historical `_DRAFT` filename is
retained for documentation-link compatibility; this content describes the
final source snapshot rather than an unfinished feature proposal.

The package and CLI report `darwin-sim 1.8.0`. Release publication is limited
to an annotated `v1.8.0` source tag and a GitHub release created from the exact
same commit. No package-index publication is performed.
No release assets are uploaded.

This document does not claim that those remote publication actions have
already occurred.

## Added in v1.8

- Retained-audit classification for RegistryHub-local encrypted-delivery
  results using explicit metadata ownership and top-level result outcomes.
- Deterministic encrypted-delivery result keys without changing v1.7 keys.
- Sorted replay counts by message ID and mailbox ID alongside existing request,
  status, reason, source, offer, and decision-category counts.
- Explicit single-history compaction apply for encrypted-delivery result
  history with deterministic missing-key and repeated-apply behavior.
- Scenario DSL support for the new history label, message/mailbox replay
  assertions, and explicit audit sources on encrypted-delivery evaluations.
- Detailed debug snapshot coverage through existing retained-audit result
  fields with copy isolation and no compact snapshot change.

## Scenario Coverage

Scenarios `073` through `075` cover the v1.8 extension:

- `073_retained_audit_encrypted_delivery_classification`
- `074_retained_audit_encrypted_delivery_replay`
- `075_retained_audit_encrypted_delivery_apply`

The v1.8 source snapshot contains a contiguous checked-in scenario set from
`001` through `075`.

## Compatibility

- The existing four retained-audit history types retain their order, keys, and
  behavior.
- Retain filters still run before compact filters, and `max_records` still
  applies after filter classification.
- Mixed-history decisions remain unsupported and do not mutate histories.
- Encryption-policy decisions, direct delivery results, mailbox inboxes, held
  offers, TrafficHub routing, canonical identity, and compact snapshots are
  unchanged by encrypted audit compaction.
- Missing, non-string, and foreign `metadata["registry_hub"]` owners are
  ignored deterministically.

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

The CLI command must report `darwin-sim 1.8.0`, scenarios must run
contiguously from `001` through `075`, and the generated index must match the
checked-in index. The wheel must install and report the same version in an
isolated out-of-tree smoke test; it is not uploaded.

Final validation passed Ruff, 922 tests, all scenarios `001` through `075`,
exact checked-in index verification, the required CLI output, and an isolated
build/install/version smoke check for
`darwin_sim-1.8.0-py3-none-any.whl`. The wheel is not uploaded.

## Limits and Non-Goals

v1.8 remains simulator-local and symbolic. It adds no policy-decision or direct
delivery-result compaction, nested gate/delivery replay dimensions, automatic
cleanup, workers, retries, durable queues, live timers, live clocks, live
polling, delivery enforcement, delivery behavior changes,
TrafficHub routing changes, compact snapshot changes, canonical identity
rewrites, real networking,
DNS, external services, real cryptography, production E2EE, or production
security, privacy, anonymity, firewall, DDoS, compliance, or
data-retention guarantees.
