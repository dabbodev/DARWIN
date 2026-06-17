# DARWIN v0.9 Draft Release Notes

Status: unreleased release-prep work on `v0.9/planning`.

Current branch package and CLI version: `darwin-sim 0.9.0`.

These notes are release-ready draft notes for the planning branch only.
v0.9.0 has not been merged, tagged, published as a GitHub release, or
published as a package.

## Added

- Lane signature and lane intent discovery foundations for compact,
  simulator-local lane intent descriptions such as `basic_messaging:v1`.
- Lane visibility and trust-tier models that keep discoverability separate
  from lane-use authorization.
- Mailbox identity and DARWIN mailbox address models for deterministic
  simulator strings such as `darwin://global.chat.neo/inbox`.
- Scoped lane registry definitions on `RegistryHub`, including lane status,
  payload metadata, adapter kind metadata, and fallback policy records.
- Lane fallback policy models for deterministic delivery outcomes such as
  reject, bounce, queue, hold, and manual-resolution results.
- RegistryHub-local mailbox registration and lane binding helpers, including
  enabled/disabled mailbox capabilities.
- Simulator-local adapter endpoint and hub topology records. Endpoint records
  are inert metadata only.
- In-memory message envelope and retained delivery result helpers for toy
  `basic_messaging:v1` mailbox delivery.
- Scenario DSL actions for mailbox delivery setup and delivery:
  `register_lane_definition`, `register_mailbox`,
  `bind_mailbox_capability`, `register_adapter_endpoint`, and
  `deliver_message`.
- Scenario assertions for mailbox registration, mailbox lane support,
  retained delivery result contents, and in-memory inbox contents:
  `mailbox_registered`, `mailbox_supports_lane`,
  `message_delivery_result_contains`, and `mailbox_inbox_contains`.
- v0.9 scenarios `044` through `046`:
  `044_mailbox_basic_message_delivery`,
  `045_mailbox_delivery_failures`, and
  `046_mailbox_delivery_fallback_policy`.
- Detailed snapshot visibility for v0.9 RegistryHub state, including lane
  registries, mailboxes, address indexes, adapter endpoints, hub topology
  advertisements, message inbox summaries, and retained delivery result
  summaries.
- Tests and documentation hardening for scenario validation, read-only
  assertions, snapshot/export visibility, scenario index continuity, and
  simulator-only boundaries.
- Scenario index and snapshot regression hardening to keep scenarios `001`
  through `046` discoverable, contiguous, and reflected in detailed
  RegistryHub state snapshots.

## Scenario Coverage

- `044_mailbox_basic_message_delivery` demonstrates the happy path for
  RegistryHub-local mailbox registration, lane capability binding, inert
  in-memory endpoint selection, and successful toy message delivery.
- `045_mailbox_delivery_failures` demonstrates deterministic failure results
  for unknown recipients, missing mailbox capabilities, missing endpoints, and
  unavailable endpoints.
- `046_mailbox_delivery_fallback_policy` demonstrates how lane fallback policy
  fields map to retained delivery result statuses and fallback actions.

The checked-in scenario set is currently `001` through `046`.

## Compatibility

- The package and CLI version now report `darwin-sim 0.9.0` on
  `v0.9/planning`.
- Compact `world.snapshot()` output remains an ID-only overview.
- Detailed snapshots and JSON result exports expose compact v0.9 RegistryHub
  state summaries.
- Existing v0.8 alias, authority-chain, retained-outcome, audit, trace,
  snapshot, and TrafficHub routing behavior remains unchanged.

## Non-Goals

v0.9 mailbox delivery remains simulator-first and experimental. It does not
add:

- production chat system behavior;
- production encryption or E2EE;
- real networking;
- sockets;
- HTTP or WebSocket clients or servers;
- DNS lookup or DNS replacement behavior;
- registrar integration;
- public CA behavior;
- production identity proof;
- external services;
- durable queueing or retry workers;
- TrafficHub routing changes;
- canonical identity rewrites;
- package publication.

The in-memory mailbox delivery path is a toy simulator path for explaining
registration, lane support, adapter metadata, and delivery outcomes. It is not
a production messaging protocol.
