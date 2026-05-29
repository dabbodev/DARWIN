# Changelog

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
