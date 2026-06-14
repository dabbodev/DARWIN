# Changelog

## [Unreleased]

No post-v0.8 release changes yet.

## [0.8.0] - 2026-06-14

DARWIN v0.8.0 has been merged to `main`, tagged as annotated `v0.8.0`, and
published as a GitHub release. No package publication was performed.

Added:

- v0.8 Sprint 1 simulator-local authority outcome retention on
  `RegistryHub.authority_outcome_history`, with compact
  `AliasAuthorityOutcomeRecord` summaries for successful approvals, fallback
  grants, conflict/name-taken outcomes, simulator-local policy denials, broken
  authority paths, and other terminal authority-chain failures.
- v0.8 Sprint 2 read-only `query_authority_outcomes(...)` helper for
  retained authority outcome summaries, with additive filters and deterministic
  append-order results.
- v0.8 Sprint 3 read-only scenario assertion
  `authority_outcome_history_contains` for retained authority outcome records.
- v0.8 Sprint 4 compact detailed snapshot and JSON export visibility for
  retained authority outcome records on each requesting `RegistryHub`.
- v0.8 scenarios `042` and `043` for retained approval, fallback,
  conflict, policy-denied, and broken-path authority outcomes.
- v0.8 authority outcome retention documentation.
- v0.8 authority outcome query documentation.
- v0.8 Sprint 5 hardening documentation and draft release-note material for
  retained records, queries, assertions, snapshot/export visibility, and
  scenario coverage.

Compatibility and limits:

- v0.8.0 is released on `main`; the package and CLI version report
  `darwin-sim 0.8.0`.
- The annotated `v0.8.0` tag and GitHub release exist; no package publication
  was performed.
- No scenario DSL actions, TrafficHub routing changes, canonical identity
  changes, broad event store, production audit/compliance behavior, external
  services, DNS, registrar integration, public CA behavior, or production
  identity proof are added.

## [0.7.0] - 2026-06-09

DARWIN v0.7.0 has been merged to `main`, tagged as annotated `v0.7.0`, and
published as a GitHub release. No package publication was performed.

Added:

- v0.7 read-only RegistryHub history query helpers for retained
  alias records, alias conflicts, persisted alias authority grant provenance,
  and quarantine records.
- v0.7 registry history query documentation.
- v0.7 read-only authority audit trace summary helpers for
  in-memory authority paths and retained RegistryHub authority grant
  provenance.
- v0.7 authority audit trace summary documentation.
- v0.7 deterministic trace explanation helpers for authority
  audit summaries, alias history entries, alias conflict entries, and
  quarantine event entries.
- v0.7 trace explainability documentation.
- v0.7 read-only scenario assertions for alias history, alias
  conflict history, authority audit traces, and quarantine history.
- v0.7 scenarios `037` through `041` for registry history, authority
  audit traces, fallback traces, and in-memory denial explainability.
- v0.7 Sprint 5 hardening for scenario assertion validation, failure output,
  read-only assertion regression coverage, documentation consistency, and draft
  v0.7 release-note material.

Compatibility and limits:

- v0.7.0 is released on `main`; the package and CLI version report
  `darwin-sim 0.7.0`.
- The annotated `v0.7.0` tag and GitHub release exist; no package publication
  was performed.
- v0.7 helper, assertion, and explanation layers are read-only and do not
  change alias outcomes, TrafficHub routing, canonical identity, or simulator
  runtime behavior.
- RegistryHub retains terminal grant provenance, not full persistent failed
  authority-chain paths. Scenario `041` explains denial from in-memory
  action-result authority path data.
- No production audit/compliance guarantees, external services, DNS,
  registrar integration, public CA behavior, or production identity proof are
  added.

## [0.6.0] - 2026-06-06

DARWIN v0.6.0 is a simulator-only alias authority chain modeling release. It
adds explicit parent-scope alias authority traversal while preserving canonical
identity truth, direct alias behavior, local progressive fallback, alias
bundles, and TrafficHub routing behavior.

Added:

- Alias authority path data models for deterministic decision recording:
  `AliasAuthorityDecision`, `AliasAuthorityPath`, and
  `AliasAuthorityPathSummary`.
- Authority-step evaluation helpers for scope checks, fallback alias
  selection, upward traversal eligibility, and one-hub authority decisions.
- Parent-chain traversal through explicit `RegistryHub.parent_hub_id` links.
- Chain-aware claim helper `claim_alias_through_authority_chain(...)` and
  result model `AliasAuthorityClaimResult`.
- Scenario runner action `claim_alias_through_authority_chain`.
- Scenario assertion `alias_authority_path_summary`.
- Detailed snapshot entries for authority-chain claims.
- Event payload visibility for authority-chain success and failure paths.
- Simulator-local `alias_authority_policy` gates for approval, pass-up, and
  fallback.
- Alias authority-chain scenarios `032` through `036`:
  `scenarios/032_alias_authority_chain_success.yaml`,
  `scenarios/033_alias_authority_chain_fallback.yaml`,
  `scenarios/034_alias_authority_chain_name_taken.yaml`,
  `scenarios/035_alias_authority_chain_policy_denied.yaml`, and
  `scenarios/036_alias_authority_chain_broken_parent.yaml`.

Compatibility and limits:

- Direct v0.5 aliases, local progressive fallback, alias bundles, canonical
  identity chains, and TrafficHub routing behavior remain unchanged.
- v0.6 does not add real DNS, registrar integration, public CA behavior,
  production identity proof, external services, TrafficHub routing changes, or
  canonical identity rewrite.

## [0.5.0] - 2026-06-04

DARWIN v0.5.0 is a simulator-only alias registry modeling release. It adds
Registry Hub aliases, local progressive fallback, and delegated alias bundles
without changing canonical identity or TrafficHub routing behavior.

Added:

- Direct alias records and direct alias lookup for registered devices.
- Alias claim, resolve, and release helpers.
- Alias conflict behavior that rejects duplicate active aliases and preserves
  the original active owner.
- Alias release behavior that keeps retained released records from resolving.
- Alias claim rejection for quarantined or revoked target devices.
- Progressive alias fallback to the highest locally authorized RegistryHub
  scope, including authority ceiling reporting.
- Alias bundle records and child alias claims inside active bundles.
- DNS-style alias bundle scenario support using simulator-local public-style
  bundle metadata only.
- Scenario runner alias actions and assertions for direct aliases, progressive
  fallback, alias bundles, inactive aliases, authority ceilings, and canonical
  identity preservation.
- Alias scenarios `026` through `031`:
  `scenarios/026_alias_claim_success.yaml`,
  `scenarios/027_alias_claim_conflict.yaml`,
  `scenarios/028_alias_release_blocks_resolution.yaml`,
  `scenarios/029_progressive_alias_fallback.yaml`,
  `scenarios/030_alias_bundle_delegation.yaml`, and
  `scenarios/031_dns_style_alias_bundle.yaml`.

Compatibility and limits:

- Aliases remain simulator-only registry shortcuts.
- DNS-style alias bundles are not real DNS, registrar integration, public CA
  behavior, production identity proof, or real network lookup.
- Aliases do not replace canonical identity and do not change TrafficHub
  routing.

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
