# DARWIN v1.10 Roadmap

Status: v1.10.0 source-release snapshot in final validation. The package and
CLI report `darwin-sim 1.10.0`.

This roadmap records the intended behavior of the v1.10.0 source snapshot
without using repository text as evidence of remote publication state. The
publication contract is an annotated `v1.10.0` tag and a GitHub source release
created from the same validated commit. Package-index publication and uploaded
release assets are out of scope.

## Goal

Extend DARWIN's deterministic retained-audit classification, replay, and
explicit single-history apply pipeline to
`RegistryHub.message_delivery_results`. The extension stays simulator-local,
deterministic, source-only, and symbolic and does not change message delivery
decisions or inbox behavior.

## Sprint 1: Direct Message-Delivery Classification

- Append `message_delivery_result` after the six v1.9 supported history types
  without changing their order, keys, serialization, or behavior.
- Add string `metadata["registry_hub"]` ownership to results created by
  `deliver_message_to_mailbox(...)`.
- Classify top-level message, recipient address, resolved mailbox, lane,
  status, and reason fields plus optional string `metadata["source"]`.
- Preserve retain-before-compact precedence, post-classification
  `max_records`, caller order, unsupported-record handling, and read-only
  classification.

## Sprint 2: Existing-Dimension Replay

- Reuse sorted, copied message-ID, mailbox-ID, and lane-signature mappings.
- Reuse status, reason, and source counts.
- Do not infer request IDs, offer IDs, policy IDs, endpoint groupings,
  fallback groupings, audit-path groupings, or nested delivery dimensions.
- Preserve all v1.9 replay and decision-category behavior.

## Sprint 3: Explicit Single-History Apply

- Select `RegistryHub.message_delivery_results` for the new history label.
- Remove only currently matching candidate keys, preserve remaining order,
  report stale keys as missing, and keep repeated apply deterministic.
- Set `message_delivery_history_mutated` only when a direct delivery result is
  removed.
- Leave inboxes, delivered envelopes, action results, events, encrypted
  delivery and policy histories, registry configuration, held offers,
  TrafficHub state and routing, canonical identities, and compact snapshots
  unchanged.

## Sprint 4: Scenario DSL and Coverage

- Reuse the existing deliver, classify, replay, and apply actions.
- Reuse existing retained-audit message, mailbox, lane, status, and reason
  assertions without adding a command or assertion type.
- Add scenarios `079` through `081` for classification, replay, and isolated
  apply.
- Keep scenario filenames and metadata contiguous from `001` through `081`,
  and enforce exact generated scenario-index equality in CI.

## Sprint 5: Compatibility and Debug Visibility

- Reuse the existing detailed retained-audit decision, replay, and apply
  sections with copied JSON-safe summaries.
- Keep compact `world.snapshot()` output unchanged.
- Prove all six v1.9 history key forms and replay fields retain their behavior.
- Document the additive `metadata["registry_hub"]` key on helper-created
  `MessageDeliveryResult` summaries and the new apply metadata flag.
- Keep mixed and unsupported apply decisions deterministic no-ops.

## Sprint 6: Source-Release Hardening

- Include this roadmap, the direct message-delivery specification, and release
  notes in documentation and release-readiness checks.
- Set package, CLI, smoke-test, and CI expectations to `1.10.0`.
- Retain Python 3.11 through 3.14 CI and the Python 3.11 isolated wheel
  build/install smoke job.
- Require Ruff, pytest, all scenarios, exact scenario-index comparison, exact
  CLI output, and isolated out-of-tree wheel verification.
- Record the actual America/Los_Angeles release date and final pytest count
  only after the complete release gates pass.

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
wheel must install in isolation and report `darwin-sim 1.10.0` from outside
the repository. The wheel is not uploaded.

The actual America/Los_Angeles release date and final passing pytest count
remain pending until every release gate succeeds.

## Non-Goals

v1.10 adds no new compaction filters, nested gate or delivery replay
dimensions, mixed or multi-history apply, deletion of inbox envelopes,
automatic cleanup, workers, retries, durable queues, live timers, live clocks,
live polling, delivery enforcement, delivery behavior changes, TrafficHub
routing changes, compact snapshot changes, canonical identity rewrites,
networking, DNS, external services, real cryptography, production E2EE, or
production security, privacy, anonymity, firewall, DDoS, compliance, or
data-retention guarantees.
