# DARWIN v1.8 Roadmap

Status: v1.8.0 source-release snapshot. The package and CLI report
`darwin-sim 1.8.0`.

This roadmap records the behavior in the v1.8.0 source snapshot without using
the repository as evidence of remote publication state. The publication
contract is an annotated `v1.8.0` tag and a GitHub source release created from
the same commit. Package-index publication and uploaded release assets are out
of scope.

## Goal

Extend the retained-audit compaction, replay, and explicit apply helpers to
RegistryHub-local encrypted-delivery result history. The extension remains
deterministic, explicit, simulator-local, and symbolic.

## Sprint 1: Encrypted-Delivery Classification

- Append `encrypted_delivery_result` after the four v1.7 supported history
  types without reordering them.
- Derive ownership only from string `metadata["registry_hub"]`; ignore missing,
  non-string, and foreign owners deterministically.
- Classify top-level result status, reason, request ID, and optional
  `metadata["source"]` while preserving v1.7 ordering, filter precedence,
  `max_records`, and unsupported-record behavior.
- Use the documented deterministic encrypted-delivery result record key.

## Sprint 2: Message- and Mailbox-Aware Replay

- Add optional, sorted `by_message_id` and `by_mailbox_id` counts to
  `RetainedAuditReplaySummary` and its JSON-safe summary.
- Preserve request, status, reason, source, offer, history-type, and decision-
  category grouping semantics.
- Do not add nested gate/delivery outcome groupings or new compaction-policy
  filters.

## Sprint 3: Explicit Single-History Apply

- Extend explicit apply to select `encrypted_delivery_result_history`.
- Remove only currently matching candidate keys, preserve remaining order,
  report stale keys as missing, and support deterministic repeated apply.
- Set encrypted-delivery history mutation metadata only when records are
  removed.
- Leave encryption-policy decisions, direct delivery results, mailbox inboxes,
  gate decisions, held offers, and routing state unchanged.

## Sprint 4: Scenario DSL and Coverage

- Accept `encrypted_delivery_result` in the existing retained-audit scenario
  actions.
- Add message/mailbox replay count assertions and optional result-source input
  for encrypted-delivery scenario actions.
- Add scenarios `073` through `075` for classification, replay, and isolated
  explicit apply.
- Keep scenario metadata and `docs/SCENARIO_INDEX.md` contiguous from `001`
  through `075`.

## Sprint 5: Debug Visibility and Compatibility

- Reuse existing detailed retained-audit decision, replay, and apply fields
  with copied JSON-safe summaries.
- Verify message/mailbox grouping copy isolation.
- Keep compact `world.snapshot()` output and all v1.7 history keys unchanged.

## Sprint 6: Source-Release Hardening

- Include this roadmap, release notes, and the encrypted-delivery retained-
  audit specification in documentation readiness checks.
- Set package and CI version expectations to `1.8.0` and record the dated
  changelog entry.
- Retain Python 3.11 through 3.14 CI and the Python 3.11 wheel build/install
  smoke job without uploading the wheel.

## Release Gates

The source snapshot is accepted only after Ruff, pytest, all checked-in
scenarios `001` through `075`, exact scenario-index generation, CLI version
output, and the isolated wheel build/install/version smoke check pass. Final
validation passed Ruff, 922 tests, all 75 scenarios, exact checked-in index
verification, CLI output `darwin-sim 1.8.0`, and an isolated install/version
smoke check for `darwin_sim-1.8.0-py3-none-any.whl`.

## Non-Goals

v1.8 adds no encryption-policy decision compaction, direct message-delivery
audit compaction, nested gate/delivery replay dimensions, automatic cleanup,
background workers, retries, durable queues, live timers, live clocks, live
polling, delivery enforcement, delivery behavior changes, TrafficHub routing
changes, compact snapshot changes, canonical identity rewrites, real
networking, DNS, external services, real cryptography, production E2EE, or
production security, privacy, anonymity, firewall, DDoS, compliance, or data-
retention guarantees.
