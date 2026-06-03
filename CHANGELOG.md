# Changelog

## [0.4.0] - 2026-05-31

DARWIN v0.4.0 is a simulator-only move-contract auth modeling release. It
connects the existing relocation layer to the v0.3 experimental HMAC bridge
while preserving symbolic move validation as the default.

Added:

- Optional `hmac_sha256_experimental` move-contract auth helpers for
  `MoveContract`.
- Deterministic move proof material binding device, passport, source and
  destination scopes, old and new attachments, nonce, session, counter, and
  simulated time when present.
- HMAC verification policy for move contracts, including session lookup, active
  session checks, device matching, stale-counter rejection, quarantined-device
  rejection, revoked-device rejection, and auth-tag verification before counter
  advancement.
- Relocation attachment update integration that verifies opt-in HMAC move
  contracts before updating attachment state or recording the move.
- HMAC move-contract success, tamper failure, expired-session, and
  revoked-device scenarios:
  `scenarios/021_hmac_move_contract_success.yaml`,
  `scenarios/022_hmac_move_contract_tamper_failure.yaml`,
  `scenarios/023_hmac_move_contract_expired_session.yaml`, and
  `scenarios/024_hmac_move_contract_revoked_device.yaml`.
- Symbolic move contract preservation scenario:
  `scenarios/025_symbolic_move_contract_still_works.yaml`.

Compatibility and limits:

- Symbolic move contracts remain the default.
- v0.4 does not add production cryptography, public-key signatures,
  certificate chains, key exchange, secure storage, encrypted transport, real
  networking, production key lifecycle, or distributed consensus.

## [0.3.0] - 2026-05-31

DARWIN v0.3.0 is a simulator-only auth bridge release. It keeps symbolic
authentication as the default while adding an explicit experimental path for
HMAC-style verification in selected scenarios.

Added:

- Experimental HMAC-SHA256 auth bridge helpers using Python standard-library
  `hmac`, `hashlib`, and deterministic JSON canonicalization.
- Opt-in `hmac_sha256_experimental` mode for packet, checkpoint, and
  rolling-proof simulator checks.
- HMAC-authenticated checkpoint scenario:
  `scenarios/012_hmac_checkpoint_success.yaml`.
- HMAC packet auth failure scenario:
  `scenarios/013_hmac_packet_auth_failure.yaml`.
- HMAC edge-case scenarios covering checkpoint material tampering, missing
  secrets, and rolling-proof nonce/counter failures:
  `scenarios/014_hmac_checkpoint_tamper_failure.yaml`,
  `scenarios/015_hmac_missing_secret_failure.yaml`, and
  `scenarios/016_hmac_rolling_proof_failure.yaml`.
- Simulator-local HMAC session lifecycle scenarios for rotation, expiration,
  stale counter rejection, and revoked session behavior:
  `scenarios/017_hmac_session_rotation.yaml`,
  `scenarios/018_hmac_session_expiration.yaml`, and
  `scenarios/019_hmac_revoked_session_failure.yaml`.
- Revocation/quarantine interaction scenario that keeps blocked devices from
  restoring trusted checkpoint state with a valid HMAC checkpoint:
  `scenarios/020_hmac_quarantine_blocks_checkpoint.yaml`.
- Centralized auth mode constants in `darwin/auth/modes.py`.
- Documentation warning that the auth bridge is simulator-only and is not
  production cryptography.

Compatibility and limits:

- Symbolic auth remains the default.
- v0.2 scenarios are expected to keep validating and running unchanged.
- v0.3 does not add real networking, key exchange, secure storage,
  public-key signatures, certificate chains, production cryptography, or
  production auth claims.

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
