# DARWIN v1.7.0 Release Notes

Status: v1.7.0 source-release snapshot. The historical `_DRAFT` filename is
retained for documentation-link compatibility; this content describes the
final source snapshot rather than an unfinished feature proposal.

The package and CLI report `darwin-sim 1.7.0`. Release publication is limited
to an annotated `v1.7.0` source tag and a GitHub release created from the exact
same commit. No package-index publication is performed.
No release assets are uploaded.

This document does not claim that those remote publication actions have
already occurred.

## Added in v1.7

- Retained-audit classification for RegistryHub-local rendezvous poll results
  and lane-admission decisions, preserving the v1.6 filter precedence and
  deterministic record order.
- Request-aware replay summaries through optional sorted `by_request_id`
  counts, with admission `offer_id` grouping and no expansion of poll
  `matched_offer_ids`.
- Explicit single-history compaction apply for poll-result or admission-
  decision history, with deterministic stale-key reporting and isolated
  mutation metadata.
- Scenario DSL support for the two new retained-history labels and request-ID
  summary assertions.
- Detailed debug snapshot coverage through the existing retained-audit result
  fields, with copy isolation and no compact snapshot change.
- CI validation on Python 3.11 through 3.14, exact CLI-version verification,
  and a separate Python 3.11 wheel-build/install smoke job with no upload.

## Scenario Coverage

Scenarios `070` through `072` cover the v1.7 extension:

- `070_retained_audit_poll_admission_classification`
- `071_retained_audit_poll_admission_replay`
- `072_retained_audit_poll_admission_apply`

The v1.7 source snapshot contains a contiguous checked-in scenario set from
`001` through `072`. Scenario `070` proves mixed classification is read-only;
scenario `071` proves request grouping and decision filtering; scenario `072`
proves separate explicit apply operations mutate only their selected history.

## Compatibility

- The existing v1.6 lifecycle explanation and status-transition record keys
  and behavior remain stable.
- Retain filters still run before compact filters, and `max_records` still
  applies after filter classification.
- Mixed-history decisions remain unsupported and do not mutate retained
  histories.
- Held offers, mailbox and encrypted delivery, TrafficHub routing, canonical
  identity, and compact `world.snapshot()` behavior are unchanged.
- Poll result ownership is derived from `parent_hub_id`; admission decision
  ownership is derived from `hub_id`. Missing and foreign hub IDs are ignored.

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

The CLI command must report `darwin-sim 1.7.0`, scenarios must run
contiguously from `001` through `072`, and the generated index must match the
checked-in index.

Final validation passed Ruff, 909 tests, all scenarios `001` through `072`,
exact checked-in index verification, the required CLI output, and an isolated
build/install/version smoke check for
`darwin_sim-1.7.0-py3-none-any.whl`. The wheel is not uploaded.

## Limits and Non-Goals

v1.7 remains simulator-local and symbolic. It adds no real networking,
sockets, HTTP/WebSocket behavior, DNS lookup, external services, real
cryptography, production E2EE, automatic compaction, cleanup workers, retry
loops, durable queues, live timers, live clocks, live polling, delivery
enforcement, delivery behavior changes, TrafficHub routing changes, compact
snapshot changes, canonical identity rewrites, or production security,
privacy, anonymity, firewall, DDoS, compliance, or data-retention guarantees.
