# Changelog

## [0.2.0] - 2026-05-31

DARWIN v0.2.0 is the active simulator consolidation release for improving
scenario authoring, inspection, and export readiness while preserving
deterministic in-memory execution.

Added:

- Structured scenario validation with field locations and actionable
  suggestions for common scenario authoring errors.
- JSON export improvements for final snapshots, event logs, and scenario run
  results.
- Route-cost routing and routing policy support for deterministic symbolic
  route selection.
- Mermaid visualization export for scenario topology, attached devices, and
  logical lane route comments.
- Relocation edge-case scenarios covering timeout, invalid move contracts,
  duplicate device claims, and unreachable relocation resume paths.
- Timeline trace export in JSON and Markdown formats with optional entity and
  event-type filters.
- Scenario DSL presets for reusable simulator setup.
- Scenario library indexing and scenario description CLI support.

Non-goals remain unchanged: v0.2 does not add production networking,
production cryptography, DNS integration, async runtime behavior, or a web UI.

## v0.1.0

DARWIN v0.1.0 is a simulator-first behavioral release for the Direct-Access
Registration Window Interface Network model.

Implemented:

- Scoped Registry Hub registration, label resolution, and same-scope conflict
  handling.
- Registry summaries, checkpoints, timeout state, and relocation records.
- Traffic Hub route selection, direct attachments, logical lanes, sequence
  state, pause/resume behavior, and symbolic packet delivery.
- Relocation flow with `in_transit`, lane pause, move contract creation,
  attachment update, reroute, and resume.
- Symbolic trust/auth behavior including rolling-proof failure, quarantine, and
  packet/checkpoint auth-tag rejection paths.
- Metrics and advisory growth recommendations, including
  `create_traffic_bridge`.
- Deterministic YAML/JSON scenario parsing, validation, execution, event logs,
  final snapshots, and CLI commands.
- Golden scenario regression coverage for validating and running all checked-in
  scenario YAML files.
- v0.1 demo guide and compact all-scenarios runner script.

Non-goals:

- No real networking, sockets, packet capture, or external service dependency.
- No production cryptography, key management, signatures, HMACs, CMACs, or
  replay protection.
- No real DNS behavior or DNS replacement.
- No kernel, driver, router, or network-stack integration.
- No async/distributed runtime, web UI, automatic topology mutation, or
  production performance work.
