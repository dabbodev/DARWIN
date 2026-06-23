# Changelog

## [1.2.0] - 2026-06-23

DARWIN v1.2.0 release prep is staged on `v1.2/planning`. This commit does not
merge to `main`, create a tag, create a GitHub release, or publish a package.

Added:

- v1.2 Sprint 1 simulator-local stream offer and rendezvous request models for
  symbolic pull-based lane rendezvous.
- v1.2 Sprint 2 RegistryHub-local held stream offer queues with deterministic
  append order, duplicate handling, replacement behavior, and read-only query
  filters.
- v1.2 Sprint 3 private polling descent helpers for one explicit simulator
  poll request over held stream offers.
- v1.2 Sprint 4 symbolic lane admission policy helpers with deterministic
  outcomes for pass-down, hold, deny, rate-limited, quarantined, and
  requires-poll decisions.
- v1.2 Sprint 5 scenario DSL actions and read-only assertions for held stream
  offers, rendezvous poll results, and lane admission decisions.
- v1.2 scenarios `053` through `057` for allowed, held/requires-poll, denied,
  rate-limited, and quarantined symbolic stream offer rendezvous outcomes.
- v1.2 Sprint 6 retained RegistryHub-local rendezvous poll result and lane
  admission decision histories, plus detailed snapshot visibility for held
  stream offers and retained poll/admission audit histories.
- v1.2 release prep updates the package and CLI version to
  `darwin-sim 1.2.0`.

Compatibility and limits:

- Existing mailbox delivery behavior remains unchanged.
- Existing encrypted delivery behavior remains unchanged.
- Existing TrafficHub routing behavior remains unchanged.
- Existing alias, identity, scenario, snapshot, and retained-history behavior
  remains unchanged outside the explicit v1.2 stream offer surfaces.
- The checked-in scenario set is expected to run contiguously from `001`
  through `057`, with scenarios `053` through `057` covering v1.2 symbolic
  stream offer rendezvous, private polling, and lane admission outcomes.
- No real networking, sockets, HTTP/WebSocket behavior, DNS lookup, registrar
  integration, public CA behavior, external services, real cryptography, key
  generation, private key storage, production E2EE, delivery enforcement,
  TrafficHub routing changes, canonical identity rewrites, production
  anonymity/privacy/firewall/DDoS guarantees, package publication, or
  additional release artifacts are added by this simulator work.

## [1.1.0] - 2026-06-19

DARWIN v1.1.0 has been merged to `main`, tagged as annotated `v1.1.0`, and
published as a GitHub release. No package publication was performed.

Added:

- v1.1 Sprint 1 simulator-local symbolic encrypted delivery request models for
  plaintext, symbolic encrypted, and policy-check-only request intent.
- Pure encrypted delivery request constructors, predicates, structural status
  helpers, JSON-safe summaries, and documentation.
- v1.1 Sprint 2 opt-in symbolic encrypted delivery policy gate decisions for
  accepted, plaintext-allowed, missing-policy, and policy-check-failed request
  outcomes.
- `evaluate_encrypted_delivery_request_policy(...)` helper for wrapping
  registered mailbox encryption policy decisions without delivering messages.
- Pure encrypted delivery gate predicates, JSON-safe summaries, retention
  controls for the existing policy decision history, and documentation.
- v1.1 Sprint 3 wrapped symbolic encrypted delivery results and compact audit
  metadata that combine a request, gate decision, and optional existing
  message delivery result.
- `evaluate_encrypted_delivery_request(...)` helper with
  `attempt_delivery=False` by default, plus JSON-safe result/audit summaries
  and pure wrapped-result predicates.
- v1.1 Sprint 4 scenario DSL action
  `evaluate_encrypted_delivery_request`, read-only encrypted delivery
  result/audit assertions, and scenarios `050` through `052` covering
  policy-check-only, gate-allowed no-attempt, explicit allowed delivery, and
  gate-blocked no-delivery paths.
- v1.1 Sprint 5 RegistryHub-local retained wrapped encrypted delivery result
  history, read-only `query_encrypted_delivery_results(...)` filters,
  retained-history-first scenario assertions, detailed snapshot visibility,
  and documentation for `retain_result` behavior.
- v1.1 Sprint 6 release-candidate hardening docs and draft release notes for
  symbolic encrypted delivery policy integration, with scenario index coverage
  remaining contiguous through `052`.
- v1.1 release prep updates the package and CLI version to
  `darwin-sim 1.1.0`.

Compatibility and limits:

- Existing `deliver_message_to_mailbox(...)` behavior remains unchanged.
- v1.1.0 is released on `main`; the package and CLI version report
  `darwin-sim 1.1.0`.
- The checked-in scenario set is expected to run contiguously from `001`
  through `052`, with scenarios `050` through `052` covering v1.1 symbolic
  encrypted delivery integration.
- No real cryptography, key generation, private key storage, encryption,
  decryption, production E2EE, default delivery enforcement, networking,
  external services, TrafficHub routing changes, canonical identity rewrites,
  package publication, or additional release artifacts are added by this
  simulator work.
- The annotated `v1.1.0` tag and GitHub release exist; no package publication
  was performed.

## [1.0.0] - 2026-06-17

DARWIN v1.0.0 has been merged to `main`, tagged as annotated `v1.0.0`, and
published as a GitHub release. No package publication was performed.

Added:

- v1.0 Sprint 1 simulator-local encryption identity, symbolic key bundle
  reference, and mailbox encryption binding models.
- Pure symbolic helpers for encryption identity creation, key bundle reference
  creation, mailbox encryption binding, and active/usable status predicates.
- v1.0 encryption identity documentation that keeps real cryptography,
  production E2EE, key generation, private key storage, networking, encrypted
  delivery policy, scenario DSL, and message delivery behavior explicitly
  deferred.
- v1.0 Sprint 2 simulator-local encrypted envelope metadata, symbolic
  encrypted message wrapper, envelope state/status labels, and pure readiness
  predicates.
- v1.0 encrypted envelope documentation that keeps real ciphertext,
  encryption/decryption, crypto libraries, production E2EE, delivery policy,
  scenario DSL, networking, and external services explicitly deferred.
- v1.0 Sprint 3 simulator-local mailbox encryption policy records, policy
  decision records, lane-required predicates, and accepted-decision
  predicates.
- Pure mailbox encryption policy evaluation for required lanes, plaintext
  fallback, missing envelope metadata, unsupported profiles, missing or
  inactive identities, missing or unusable key bundles, and not-ready
  envelopes without changing v0.9 delivery behavior.
- v1.0 mailbox encryption policy documentation that keeps real cryptography,
  key generation, encryption/decryption, production E2EE, scenario DSL,
  networking, and external services explicitly deferred.
- v1.0 Sprint 4 RegistryHub-local symbolic encryption registries for
  encryption identities, key bundle references, mailbox encryption bindings,
  and mailbox encryption policies.
- Registry helper functions to register, retrieve, list, filter, and evaluate
  registered symbolic mailbox encryption policy state without changing v0.9
  delivery behavior.
- Detailed snapshot visibility and documentation for RegistryHub-local
  encryption registries while keeping scenario DSL, real cryptography,
  networking, production E2EE, and delivery integration deferred.
- v1.0 Sprint 5 scenario DSL actions for registering symbolic encryption
  identities, key bundle references, mailbox encryption bindings, mailbox
  encryption policies, and evaluating registered mailbox encryption policy
  decisions.
- v1.0 Sprint 5 read-only scenario assertions for symbolic encryption
  registry records and policy decision action results.
- v1.0 scenarios `047` through `049` for symbolic encryption registry setup,
  successful required policy evaluation, and deterministic policy failures,
  without changing v0.9 plaintext delivery behavior.
- v1.0 Sprint 6 RegistryHub-local retained symbolic encryption policy decision
  history, read-only decision-history queries, and detailed snapshot visibility.
- v1.0 encryption policy decision history documentation that keeps real
  cryptography, key generation, encryption/decryption, production E2EE,
  delivery enforcement, networking, external services, and private key storage
  explicitly deferred.
- v1.0 Sprint 7 hardening for symbolic encryption models, registry behavior,
  scenario DSL validation, detailed snapshot visibility, scenario index
  freshness checks, documentation consistency, and draft release-note material.
- A checked-in scenario index regression that compares `docs/SCENARIO_INDEX.md`
  with the deterministic scenario metadata renderer for scenarios `001`
  through `049`.

Compatibility and limits:

- v1.0.0 is released on `main`; the package and CLI version report
  `darwin-sim 1.0.0`.
- The checked-in scenario set is expected to run contiguously from `001`
  through `049`, with scenarios `047` through `049` covering v1.0 symbolic
  encryption registry and policy-decision behavior.
- No real cryptography, key generation, private key storage, encryption,
  decryption, production E2EE, secure messenger behavior, crypto library
  integration, delivery enforcement, networking, DNS lookup, external
  services, TrafficHub routing changes, canonical identity rewrites, package
  publication, or additional release artifacts are added by the simulator
  work.
- The annotated `v1.0.0` tag and GitHub release exist; no package publication
  was performed.

## [0.9.0] - 2026-06-17

DARWIN v0.9.0 has been merged to `main`, tagged as annotated `v0.9.0`, and
published as a GitHub release. No package publication was performed.

Added:

- v0.9 Sprint 1 simulator-local lane signature, lane intent advertisement,
  visibility tier, and trust context models for typed lane intent discovery.
- Pure lane signature formatting/parsing and lane intent discovery helpers,
  keeping discovery visibility separate from future lane-use authorization.
- v0.9 lane signature documentation and revised roadmap ordering that places
  mailbox identity, registration, adapter records, and message delivery after
  lane intent foundations.
- v0.9 Sprint 2 simulator-local mailbox address, mailbox identity, and mailbox
  capability models for future DARWIN-addressed mailbox demos.
- Pure mailbox address formatting/parsing helpers for deterministic
  `darwin://scope.mailbox/resource` simulator strings.
- v0.9 mailbox addressing documentation that keeps registration, lane binding,
  adapter endpoints, delivery, networking, production chat, and production
  encryption explicitly deferred.
- v0.9 Sprint 3 simulator-local scoped lane definition, fallback policy, and
  lane registry status models for RegistryHub-local lane catalogs.
- RegistryHub lane registry storage plus pure helper functions to register,
  retrieve, list, filter, and discover scoped lane definitions.
- Deterministic `basic_messaging:v1` lane definition constructor and scoped
  lane registry documentation.
- v0.9 Sprint 4 RegistryHub-local mailbox registry storage and helper
  functions to register, retrieve, resolve, list, and filter mailbox
  identities.
- Strict mailbox capability binding helpers that require registered lane
  definitions, report enabled lane support, keep disabled capabilities from
  counting as supported, and replace duplicate capability IDs
  deterministically.
- v0.9 mailbox registry documentation that keeps mailbox registration and lane
  binding explicitly separate from adapters, delivery, networking, production
  chat, and production encryption.
- v0.9 Sprint 5 simulator-local adapter endpoint and hub topology
  advertisement models for inert adapter-shaped availability metadata.
- RegistryHub endpoint and topology storage plus helper functions to register,
  retrieve, list, and filter endpoint/topology records deterministically.
- Pure endpoint constructors for in-memory mailbox endpoints and domain-hint
  hub endpoints that construct records only.
- v0.9 adapter endpoint documentation that keeps domain, host, port, and path
  hints explicitly separate from networking, DNS lookup, sockets, deployment,
  delivery, and production chat behavior.
- v0.9 Sprint 6 simulator-local message envelope and retained delivery result
  models for toy `basic_messaging:v1` delivery.
- RegistryHub in-memory inbox/result storage plus helper functions to deliver
  to a registered mailbox, read mailbox inboxes, and filter retained delivery
  results in deterministic append order.
- Pure `make_basic_message_envelope(...)` constructor for symbolic plaintext
  test messages.
- v0.9 message delivery documentation that keeps in-memory delivery separate
  from networking, DNS lookup, sockets, production chat, production encryption,
  background retries, durable queues, and TrafficHub routing.
- v0.9 Sprint 7 scenario DSL actions for registering lane definitions,
  mailboxes, mailbox lane capabilities, inert adapter endpoints, and toy
  in-memory messages.
- v0.9 Sprint 7 scenario assertions for registered mailboxes, mailbox lane
  support, retained delivery results, and in-memory inbox contents.
- v0.9 scenarios `044` through `046` for successful in-memory mailbox
  delivery, deterministic failure outcomes, and lane fallback policy behavior.
- Detailed snapshot visibility for compact v0.9 RegistryHub state summaries,
  including lane registries, mailboxes, adapter endpoints, message inboxes,
  and retained delivery results.
- v0.9 Sprint 8 hardening for mailbox delivery scenario actions, read-only
  assertions, snapshot visibility, scenario index continuity, documentation,
  and draft release-note material.

Compatibility and limits:

- The package and CLI version now report `darwin-sim 0.9.0` on `main`.
- The checked-in scenario set is expected to run contiguously from `001`
  through `046`, with scenarios `044` through `046` covering v0.9 mailbox
  delivery.
- No real networking, sockets, DNS lookup, external services, TrafficHub
  routing changes, canonical identity changes, alias behavior changes,
  production chat behavior, production encryption, background retries, durable
  queues, or production message delivery are added.
- The annotated `v0.9.0` tag and GitHub release exist; no package publication
  was performed.

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
