# DARWIN v0.1 Release Checklist

- [x] Tests pass with `python -m pytest`.
- [x] Ruff passes with `python -m ruff check .`.
- [x] CI workflow passes on push or pull request.
- [x] README quick-start commands have been checked against the repo.
- [x] Scenario listing and validation works with `python -m darwin.cli.main list-scenarios`.
- [x] Basic scenario validates with `python -m darwin.cli.main validate-scenario scenarios/001_basic_registration.yaml`.
- [x] Example scenario runs with `python -m darwin.cli.main run scenarios/001_basic_registration.yaml`.
- [x] Golden scenario regression suite passes with `python scripts/run_all_scenarios.py`.
- [x] Demo guide and CHANGELOG are up to date.
- [x] Architecture overview and release notes are present in `docs/`.
- [x] v0.2 roadmap is present in `docs/`.
- [x] Package version is confirmed as `0.1.0`.
- [x] Project metadata, README, and root `LICENSE` all identify the license as MIT.
- [x] Console script entry point `darwin-sim` is configured and usable.
- [x] No real cryptography, authentication, or networking claims are made.
- [x] Known limitations are listed in the README.

## Final Readiness Audit

- [x] README repo-relative doc and scenario references point to existing files.
- [x] `darwin.__version__`, `pyproject.toml`, CHANGELOG, and release notes all agree on `0.1.0`.
- [x] CI checks match the local release verification commands.
- [x] All checked-in YAML scenarios validate and run.
- [x] Release notes clearly state v0.1 limitations and non-goals.

# DARWIN v0.2 Release Checklist

- [ ] Tests pass with `python -m pytest`.
- [ ] Ruff passes with `python -m ruff check .`.
- [ ] All checked-in scenarios pass with `python scripts/run_all_scenarios.py`.
- [ ] Scenario listing works with `python -m darwin.cli.main list-scenarios`.
- [ ] Preset listing works with `python -m darwin.cli.main list-presets`.
- [ ] Scenario index is generated with `python -m darwin.cli.main scenario-index`.
- [ ] Preset scenario runs, including `scenarios/011_preset_lane_demo.yaml`.
- [ ] Full JSON export sanity check is run for snapshot, events, and result output.
- [ ] Mermaid export is checked with a representative scenario.
- [ ] Timeline Markdown and JSON exports are checked with a representative scenario.
- [ ] README and v0.2 docs are updated.
- [ ] CHANGELOG includes the dated `0.2.0` section.
- [ ] Final release notes are updated in `docs/RELEASE_NOTES_v0_2.md`.
- [ ] Documentation avoids production networking, DNS, or production cryptography claims.
- [ ] Package versioning and final release tag decision are handled separately from this checklist.

## v0.2 Manual Validation Commands

```bash
python -m pytest
python -m ruff check .
python scripts/run_all_scenarios.py
python -m darwin.cli.main --version
python -m darwin.cli.main list-scenarios
python -m darwin.cli.main scenario-index
python -m darwin.cli.main list-presets
python -m darwin.cli.main describe-scenario scenarios/011_preset_lane_demo.yaml
python -m darwin.cli.main expand-scenario scenarios/011_preset_lane_demo.yaml
python -m darwin.cli.main run scenarios/004_relocation_pause_resume.yaml --export-snapshot tmp_v02_snapshot.json --export-events tmp_v02_events.json --export-result tmp_v02_result.json --export-mermaid tmp_v02.mmd --export-timeline-md tmp_v02_timeline.md --export-timeline-json tmp_v02_timeline.json
```

# DARWIN v0.3 Auth Bridge Release Checklist

- [ ] Ruff passes with `python -m ruff check .`.
- [ ] Tests pass with `python -m pytest`.
- [ ] All checked-in scenarios pass with `python scripts/run_all_scenarios.py`.
- [ ] CLI version reports `darwin-sim 0.3.0`.
- [ ] Scenario listing works with `python -m darwin.cli.main list-scenarios`.
- [ ] Preset listing works with `python -m darwin.cli.main list-presets`.
- [ ] Scenario index is generated with `python -m darwin.cli.main scenario-index`.
- [ ] Representative HMAC session scenario is described with
  `python -m darwin.cli.main describe-scenario scenarios/017_hmac_session_rotation.yaml`.
- [ ] Representative HMAC quarantine/revocation scenario is described with
  `python -m darwin.cli.main describe-scenario scenarios/020_hmac_quarantine_blocks_checkpoint.yaml`.
- [ ] HMAC scenarios `012` through `020` validate and run:
  `scenarios/012_hmac_checkpoint_success.yaml`,
  `scenarios/013_hmac_packet_auth_failure.yaml`,
  `scenarios/014_hmac_checkpoint_tamper_failure.yaml`,
  `scenarios/015_hmac_missing_secret_failure.yaml`,
  `scenarios/016_hmac_rolling_proof_failure.yaml`,
  `scenarios/017_hmac_session_rotation.yaml`,
  `scenarios/018_hmac_session_expiration.yaml`,
  `scenarios/019_hmac_revoked_session_failure.yaml`, and
  `scenarios/020_hmac_quarantine_blocks_checkpoint.yaml`.
- [ ] Export sanity check is run for snapshot, events, result, Mermaid,
  timeline Markdown, and timeline JSON outputs.
- [ ] Auth bridge docs are checked in `docs/AUTH_BRIDGE_v0_3.md`.
- [ ] Final release notes are checked in `docs/RELEASE_NOTES_v0_3.md`.
- [ ] Symbolic auth default is confirmed.
- [ ] Package version is confirmed as `0.3.0`.
- [ ] Documentation avoids production cryptography, key exchange, secure
  storage, public-key signature, certificate chain, or real networking claims.
- [ ] Simulator-only and non-production language is checked in release-facing
  documentation.

## v0.3 Auth Bridge Manual Validation Commands

```bash
python -m ruff check .
python -m pytest
python scripts/run_all_scenarios.py
python -m darwin.cli.main --version
python -m darwin.cli.main scenario-index
python -m darwin.cli.main list-scenarios
python -m darwin.cli.main list-presets
python -m darwin.cli.main describe-scenario scenarios/017_hmac_session_rotation.yaml
python -m darwin.cli.main describe-scenario scenarios/020_hmac_quarantine_blocks_checkpoint.yaml
python -m darwin.cli.main run scenarios/012_hmac_checkpoint_success.yaml
python -m darwin.cli.main run scenarios/013_hmac_packet_auth_failure.yaml
python -m darwin.cli.main run scenarios/014_hmac_checkpoint_tamper_failure.yaml
python -m darwin.cli.main run scenarios/015_hmac_missing_secret_failure.yaml
python -m darwin.cli.main run scenarios/016_hmac_rolling_proof_failure.yaml
python -m darwin.cli.main run scenarios/017_hmac_session_rotation.yaml
python -m darwin.cli.main run scenarios/018_hmac_session_expiration.yaml
python -m darwin.cli.main run scenarios/019_hmac_revoked_session_failure.yaml
python -m darwin.cli.main run scenarios/020_hmac_quarantine_blocks_checkpoint.yaml
python -m darwin.cli.main run scenarios/020_hmac_quarantine_blocks_checkpoint.yaml --export-snapshot tmp_v03_snapshot.json --export-events tmp_v03_events.json --export-result tmp_v03_result.json --export-mermaid tmp_v03.mmd --export-timeline-md tmp_v03_timeline.md --export-timeline-json tmp_v03_timeline.json
```

# DARWIN v0.4 Move-Contract Auth Release Checklist

Do not merge, tag, create a GitHub release, rebase, force push, or publish as
part of this checklist.

- [ ] Ruff passes with `python -m ruff check .`.
- [ ] Tests pass with `python -m pytest`.
- [ ] All checked-in scenarios pass with `python scripts/run_all_scenarios.py`.
- [ ] CLI version reports `darwin-sim 0.4.0`.
- [ ] Scenario index is generated with `python -m darwin.cli.main scenario-index`.
- [ ] Scenario listing works with `python -m darwin.cli.main list-scenarios`.
- [ ] Preset listing works with `python -m darwin.cli.main list-presets`.
- [ ] HMAC move-contract scenarios validate and run individually:
  `scenarios/021_hmac_move_contract_success.yaml`,
  `scenarios/022_hmac_move_contract_tamper_failure.yaml`,
  `scenarios/023_hmac_move_contract_expired_session.yaml`, and
  `scenarios/024_hmac_move_contract_revoked_device.yaml`.
- [ ] Symbolic move-contract preservation scenario validates and runs:
  `scenarios/025_symbolic_move_contract_still_works.yaml`.
- [ ] Representative export sanity is checked for snapshot, events, result,
  Mermaid, timeline Markdown, and timeline JSON outputs.
- [ ] JSON export files parse.
- [ ] Mermaid export contains `flowchart LR`.
- [ ] Timeline Markdown export contains a table.
- [ ] Package version is confirmed as `0.4.0`.
- [ ] Final release notes are checked in `docs/RELEASE_NOTES_v0_4.md`.
- [ ] CHANGELOG contains a dated `0.4.0` release section.
- [ ] README links to `docs/RELEASE_NOTES_v0_4.md`.
- [ ] Symbolic move validation remains documented as the default.
- [ ] HMAC move proof is documented as opt-in through
  `hmac_sha256_experimental`.
- [ ] Simulator-only and non-production crypto language is checked in
  release-facing documentation.
- [ ] Documentation avoids production secure mobility, real signature,
  certificate-chain, key-exchange, secure-storage, encrypted-transport, and
  real-networking claims.

## v0.4 Release Validation Commands

```bash
python -m ruff check .
python -m pytest
python scripts/run_all_scenarios.py
python -m darwin.cli.main --version
python -m darwin.cli.main scenario-index
python -m darwin.cli.main list-scenarios
python -m darwin.cli.main list-presets
python -m darwin.cli.main validate-scenario scenarios/021_hmac_move_contract_success.yaml
python -m darwin.cli.main run scenarios/021_hmac_move_contract_success.yaml
python -m darwin.cli.main validate-scenario scenarios/022_hmac_move_contract_tamper_failure.yaml
python -m darwin.cli.main run scenarios/022_hmac_move_contract_tamper_failure.yaml
python -m darwin.cli.main validate-scenario scenarios/023_hmac_move_contract_expired_session.yaml
python -m darwin.cli.main run scenarios/023_hmac_move_contract_expired_session.yaml
python -m darwin.cli.main validate-scenario scenarios/024_hmac_move_contract_revoked_device.yaml
python -m darwin.cli.main run scenarios/024_hmac_move_contract_revoked_device.yaml
python -m darwin.cli.main validate-scenario scenarios/025_symbolic_move_contract_still_works.yaml
python -m darwin.cli.main run scenarios/025_symbolic_move_contract_still_works.yaml
python -m darwin.cli.main run scenarios/021_hmac_move_contract_success.yaml --export-snapshot tmp_v04_snapshot.json --export-events tmp_v04_events.json --export-result tmp_v04_result.json --export-mermaid tmp_v04.mmd --export-timeline-md tmp_v04_timeline.md --export-timeline-json tmp_v04_timeline.json
```

# DARWIN v0.5 Alias Registry Release Checklist

Do not merge, tag, create a GitHub release, rebase, force push, or publish as
part of this checklist.

- [ ] Ruff passes with `python -m ruff check .`.
- [ ] Tests pass with `python -m pytest`.
- [ ] All checked-in scenarios pass with `python scripts/run_all_scenarios.py`.
- [ ] CLI version reports `darwin-sim 0.5.0`.
- [ ] Scenario index is generated with `python -m darwin.cli.main scenario-index`.
- [ ] Scenario listing works with `python -m darwin.cli.main list-scenarios`.
- [ ] Preset listing works with `python -m darwin.cli.main list-presets`.
- [ ] Scenario `026_alias_claim_success` validates and runs.
- [ ] Scenario `027_alias_claim_conflict` validates and runs.
- [ ] Scenario `028_alias_release_blocks_resolution` validates and runs.
- [ ] Scenario `029_progressive_alias_fallback` validates and runs.
- [ ] Scenario `030_alias_bundle_delegation` validates and runs.
- [ ] Scenario `031_dns_style_alias_bundle` validates and runs.
- [ ] Representative export sanity is checked for snapshot, events, result,
  Mermaid, timeline Markdown, and timeline JSON outputs.
- [ ] JSON export files parse.
- [ ] Mermaid export contains `flowchart LR`.
- [ ] Timeline Markdown export contains a table.
- [ ] Package version is confirmed as `0.5.0`.
- [ ] Final release notes are checked in `docs/RELEASE_NOTES_v0_5.md`.
- [ ] CHANGELOG contains a dated `0.5.0` release section.
- [ ] README links to `docs/RELEASE_NOTES_v0_5.md`.
- [ ] Direct aliases, conflict/release behavior, progressive fallback, alias
  bundles, DNS-style alias bundles, and scenarios `026` through `031` are
  documented as implemented.
- [ ] Simulator-only alias and DNS-style wording is checked.
- [ ] Documentation avoids real DNS, public domain registration, production
  identity proof, public CA, production crypto, real networking, external
  registry, TrafficHub routing change, or canonical identity replacement
  claims.

## v0.5 Release Validation Commands

```bash
python -m ruff check .
python -m pytest
python scripts/run_all_scenarios.py
python -m darwin.cli.main --version
python -m darwin.cli.main scenario-index
python -m darwin.cli.main list-scenarios
python -m darwin.cli.main list-presets
python -m darwin.cli.main validate-scenario scenarios/026_alias_claim_success.yaml
python -m darwin.cli.main run scenarios/026_alias_claim_success.yaml
python -m darwin.cli.main validate-scenario scenarios/027_alias_claim_conflict.yaml
python -m darwin.cli.main run scenarios/027_alias_claim_conflict.yaml
python -m darwin.cli.main validate-scenario scenarios/028_alias_release_blocks_resolution.yaml
python -m darwin.cli.main run scenarios/028_alias_release_blocks_resolution.yaml
python -m darwin.cli.main validate-scenario scenarios/029_progressive_alias_fallback.yaml
python -m darwin.cli.main run scenarios/029_progressive_alias_fallback.yaml
python -m darwin.cli.main validate-scenario scenarios/030_alias_bundle_delegation.yaml
python -m darwin.cli.main run scenarios/030_alias_bundle_delegation.yaml
python -m darwin.cli.main validate-scenario scenarios/031_dns_style_alias_bundle.yaml
python -m darwin.cli.main run scenarios/031_dns_style_alias_bundle.yaml
python -m darwin.cli.main run scenarios/031_dns_style_alias_bundle.yaml --export-snapshot tmp_v05_snapshot.json --export-events tmp_v05_events.json --export-result tmp_v05_result.json --export-mermaid tmp_v05.mmd --export-timeline-md tmp_v05_timeline.md --export-timeline-json tmp_v05_timeline.json
```

# DARWIN v0.6 Alias Authority Chain Release Checklist

v0.6.0 has been merged to `main`, tagged as annotated `v0.6.0`, and published
as a GitHub release. No package publication was performed.

- [x] Ruff passes with `python -m ruff check .`.
- [x] Tests pass with `python -m pytest`.
- [x] All checked-in scenarios `001` through `036` pass with
  `python scripts/run_all_scenarios.py`.
- [x] CLI version reports `darwin-sim 0.6.0`.
- [x] Package version is confirmed as `0.6.0`.
- [x] v0.6 roadmap is checked in `docs/V0_6_ROADMAP.md`.
- [x] Alias authority chain design is checked in
  `docs/ALIAS_AUTHORITY_CHAIN_v0_6.md`.
- [x] v0.6 release notes are checked in
  `docs/RELEASE_NOTES_v0_6_DRAFT.md`.
- [x] CHANGELOG contains a dated `0.6.0` release section.
- [x] README links to the v0.6 docs.
- [x] Scenarios `032` through `036` are documented and discoverable.
- [x] Parent-chain models and helpers are documented as released behavior.
- [x] Documentation states that direct v0.5 alias behavior remains unchanged.
- [x] Documentation states that TrafficHub routing and canonical identity
  chains remain unchanged.
- [x] Documentation avoids real DNS, registrar integration, public CA,
  production identity proof, distributed consensus, external registry,
  TrafficHub routing change, or canonical identity replacement claims.
- [x] Merge, annotated tag, and GitHub release are complete.
- [x] Package publication was intentionally not performed.

## v0.6 Release-Prep Validation Commands

```bash
python -m ruff check .
python -m pytest
python scripts/run_all_scenarios.py
python -m darwin.cli.main --version
python -m darwin.cli.main scenario-index
python -m darwin.cli.main list-scenarios
```

# DARWIN v0.7 History, Audit, and Trace Explainability Release Checklist

v0.7.0 has been merged to `main`, tagged as annotated `v0.7.0`, and published
as a GitHub release. No package publication was performed.

- [x] Ruff passes with `python -m ruff check .`.
- [x] Tests pass with `python -m pytest`.
- [x] All checked-in scenarios `001` through `041` pass with
  `python scripts/run_all_scenarios.py`.
- [x] CLI version reports `darwin-sim 0.7.0`.
- [x] Package version is confirmed as `0.7.0`.
- [x] Scenario index is current and lists scenarios `001` through `041`
  without numbering gaps.
- [x] v0.7 release notes are checked in
  `docs/RELEASE_NOTES_v0_7_DRAFT.md`.
- [x] CHANGELOG contains a dated `0.7.0` release section.
- [x] README and v0.7 docs state that helper, assertion, and explanation
  layers are read-only.
- [x] Documentation states that RegistryHub retains terminal grant provenance,
  not full persistent failed authority-chain paths.
- [x] Documentation states that scenario `041` relies on in-memory denial
  explainability data.
- [x] Documentation avoids production audit/compliance guarantees, persistent
  failed-path audit storage, broad event-store claims, real DNS, registrar
  integration, public CA behavior, production identity proof, external
  services, TrafficHub routing changes, and canonical identity rewrites.
- [x] Merge, annotated tag, and GitHub release are complete.
- [x] Package publication was intentionally not performed.

## v0.7 Release Validation Commands

```bash
python -m ruff check .
python -m pytest
python scripts/run_all_scenarios.py
python -m darwin.cli.main --version
python -m darwin.cli.main scenario-index
python -m darwin.cli.main list-scenarios
```

# DARWIN v0.8 Retained Authority Outcomes Release Checklist

v0.8.0 has been merged to `main`, tagged as annotated `v0.8.0`, and published
as a GitHub release. No package publication was performed.

- [x] Ruff passes with `python -m ruff check .`.
- [x] Tests pass with `python -m pytest`.
- [x] All checked-in scenarios `001` through `043` pass with
  `python scripts/run_all_scenarios.py`.
- [x] CLI version reports `darwin-sim 0.8.0`.
- [x] Package version is confirmed as `0.8.0`.
- [x] Scenario index is current and lists scenarios `001` through `043`
  without numbering gaps.
- [x] Scenario metadata regression confirms scenarios `001` through `043` are
  contiguous and discoverable.
- [x] v0.8 release notes are checked in
  `docs/RELEASE_NOTES_v0_8_DRAFT.md`.
- [x] CHANGELOG contains a dated `0.8.0` release section.
- [x] README and v0.8 docs state that retained authority outcome history is
  simulator-local introspection on the requesting `RegistryHub`.
- [x] Documentation states that detailed snapshots and JSON result exports
  expose compact retained outcome summaries, while compact `world.snapshot()`
  remains unchanged.
- [x] Documentation avoids production audit/compliance guarantees, broad event
  store claims, real DNS, registrar integration, public CA behavior,
  production identity proof, external services, TrafficHub routing changes,
  canonical identity rewrites, and package-publication claims.
- [x] Merge, annotated tag, and GitHub release are complete.
- [x] Package publication was intentionally not performed.

## v0.8 Release Validation Commands

```bash
python -m ruff check .
python -m pytest
python scripts/run_all_scenarios.py
python -m darwin.cli.main --version
python -m darwin.cli.main scenario-index
python -m darwin.cli.main list-scenarios
```

# DARWIN v0.9 Mailbox Delivery Foundations Release-Prep Checklist

v0.9.0 has been merged to `main`, tagged as annotated `v0.9.0`, and published
as a GitHub release. No package publication was performed.

- [x] Ruff passes with `python -m ruff check .`.
- [x] Tests pass with `python -m pytest`.
- [x] All checked-in scenarios `001` through `046` pass with
  `python scripts/run_all_scenarios.py`.
- [x] CLI version reports `darwin-sim 0.9.0`.
- [x] Package version is confirmed as `0.9.0`.
- [x] Scenario index is current and lists scenarios `001` through `046`
  without numbering gaps.
- [x] Scenario metadata regression confirms scenarios `001` through `046` are
  contiguous and discoverable.
- [x] v0.9 scenarios `044` through `046` validate and run.
- [x] v0.9 release notes are checked in
  `docs/RELEASE_NOTES_v0_9_DRAFT.md`.
- [x] CHANGELOG contains a dated `0.9.0` release section.
- [x] README and v0.9 docs state that mailbox delivery is toy,
  RegistryHub-local, in-memory simulator behavior only.
- [x] Documentation avoids production chat, production encryption or E2EE,
  real networking, sockets, HTTP/WebSocket server/client behavior, DNS lookup
  or DNS replacement, registrar integration, public CA behavior, production
  identity proof, external services, durable queues, retry workers, TrafficHub
  routing changes, canonical identity rewrites, and package-publication
  claims.
- [x] Merge, annotated tag, and GitHub release are complete.
- [x] Package publication was intentionally not performed.

## v0.9 Release-Prep Validation Commands

```bash
python -m ruff check .
python -m pytest
python scripts/run_all_scenarios.py
python -m darwin.cli.main --version
python -m darwin.cli.main scenario-index
python -m darwin.cli.main list-scenarios
```

# DARWIN v1.0 Symbolic Encryption Release Checklist

v1.0.0 has been merged to `main`, tagged as annotated `v1.0.0`, and published
as a GitHub release. No package publication was performed.

- [x] Ruff passes with `python -m ruff check .`.
- [x] Tests pass with `python -m pytest`.
- [x] All checked-in scenarios `001` through `049` pass with
  `python scripts/run_all_scenarios.py`.
- [x] CLI version reports `darwin-sim 1.0.0`.
- [x] Package version is confirmed as `1.0.0`.
- [x] Scenario index is current and lists scenarios `001` through `049`
  without numbering gaps.
- [x] Scenario metadata regression confirms scenarios `001` through `049` are
  contiguous and discoverable.
- [x] v1.0 scenarios `047` through `049` validate and run.
- [x] v1.0 draft release notes are checked in
  `docs/RELEASE_NOTES_v1_0_DRAFT.md`.
- [x] CHANGELOG contains a dated `1.0.0` release section.
- [x] README and v1.0 docs state that symbolic encryption is simulator-only
  metadata, policy, registry, scenario, and audit modeling.
- [x] Documentation avoids real cryptography, key generation, private key
  storage, encryption/decryption, crypto library integration, production E2EE,
  secure messenger behavior, delivery enforcement, real networking, sockets,
  HTTP/WebSocket behavior, DNS lookup, external services, durable queues,
  retry workers, TrafficHub routing changes, canonical identity rewrites, and
  package-publication claims.
- [x] Merge, annotated tag, and GitHub release are complete.
- [x] Package publication was intentionally not performed.

## v1.0 Release Validation Commands

```bash
python -m ruff check .
python -m pytest
python scripts/run_all_scenarios.py
python -m darwin.cli.main --version
python -m darwin.cli.main scenario-index
python -m darwin.cli.main list-scenarios
```

# DARWIN v1.1 Symbolic Encrypted Delivery Release-Prep Checklist

v1.1.0 has been merged to `main`, tagged as annotated `v1.1.0`, and published
as a GitHub release. No package publication was performed.

- [x] Package version is confirmed as `1.1.0`.
- [x] CLI version reports `darwin-sim 1.1.0`.
- [x] Ruff passes with `python -m ruff check .`.
- [x] Tests pass with `python -m pytest`.
- [x] All checked-in scenarios `001` through `052` pass with
  `python scripts/run_all_scenarios.py`.
- [x] Scenario index is current and lists scenarios `001` through `052`
  without numbering gaps.
- [x] Scenario metadata regression confirms scenarios `001` through `052` are
  contiguous and discoverable.
- [x] v1.1 scenarios `050` through `052` validate and run.
- [x] v1.1 draft release notes are checked in
  `docs/RELEASE_NOTES_v1_1_DRAFT.md`.
- [x] CHANGELOG contains a dated `1.1.0` release section.
- [x] README and v1.1 docs state that symbolic encrypted delivery integration
  is opt-in, simulator-local policy/audit modeling.
- [x] Documentation states that existing plaintext delivery, TrafficHub
  routing, and canonical identity behavior remain unchanged.
- [x] Documentation avoids real cryptography, key generation, private key
  storage, encryption/decryption, crypto library integration, production E2EE,
  secure messenger behavior, default delivery enforcement, real networking,
  sockets, HTTP/WebSocket behavior, DNS lookup, external services, durable
  queues, retry workers, TrafficHub routing changes, canonical identity
  rewrites, and package-publication claims.
- [x] Merge to `main`, annotated tag, and GitHub release are complete.
- [x] Package publication was intentionally not performed.

## v1.1 Release-Prep Validation Commands

```bash
python -m ruff check .
python -m pytest
python scripts/run_all_scenarios.py
python -m darwin.cli.main --version
python -m darwin.cli.main scenario-index
python -m darwin.cli.main list-scenarios
```

# DARWIN v1.2 Pull-Based Lane Rendezvous Release Checklist

v1.2.0 has been merged to `main`, tagged as annotated `v1.2.0`, and published
as a GitHub release:
https://github.com/dabbodev/DARWIN/releases/tag/v1.2.0. No package
publication was performed.

- [x] Package version is confirmed as `1.2.0`.
- [x] CLI version reports `darwin-sim 1.2.0`.
- [x] Ruff passes with `python -m ruff check .`.
- [x] Tests pass with `python -m pytest`.
- [x] All checked-in scenarios `001` through `057` pass with
  `python scripts/run_all_scenarios.py`.
- [x] Scenario index is current and lists scenarios `001` through `057`
  without numbering gaps.
- [x] Scenario metadata regression confirms scenarios `001` through `057` are
  contiguous and discoverable.
- [x] v1.2 scenarios `053` through `057` validate and run.
- [x] v1.2 release notes are checked in
  `docs/RELEASE_NOTES_v1_2_DRAFT.md`.
- [x] CHANGELOG contains a dated `1.2.0` release section.
- [x] README and v1.2 docs state that pull-based lane rendezvous and stream
  offer admission remain simulator-local symbolic metadata, policy, and audit
  modeling only.
- [x] Documentation states that existing mailbox delivery, encrypted delivery,
  TrafficHub routing, alias, identity, scenario, snapshot, and retained-history
  behavior remain unchanged outside the explicit v1.2 stream offer surfaces.
- [x] Documentation avoids real networking, sockets, HTTP/WebSocket behavior,
  DNS lookup, registrar integration, public CA behavior, external services,
  real cryptography, key generation, private key storage, production E2EE,
  delivery enforcement, TrafficHub routing changes, canonical identity
  rewrites, and production anonymity/privacy/firewall/DDoS guarantees.
- [x] Merge to `main`, annotated tag, and GitHub release are complete.
- [x] No package publication was performed.

## v1.2 Release Validation Commands

```bash
python -m ruff check .
python -m pytest
python scripts/run_all_scenarios.py
python -m darwin.cli.main --version
python -m darwin.cli.main scenario-index
python -m darwin.cli.main list-scenarios
```

# DARWIN v1.3 Rendezvous Lifecycle Release Checklist

v1.3.0 has been merged to `main`, tagged as annotated `v1.3.0`, and published
as a GitHub release:
https://github.com/dabbodev/DARWIN/releases/tag/v1.3.0. No package
publication was performed, and no release assets were uploaded.

- [x] v1.3 planning roadmap seed is checked in at `docs/V1_3_ROADMAP.md`.
- [x] v1.3 release notes are checked in at
  `docs/RELEASE_NOTES_v1_3_DRAFT.md`.
- [x] Package version is confirmed as `1.3.0`.
- [x] CLI version reports `darwin-sim 1.3.0`.
- [x] README links to v1.3 release docs and records the published GitHub
  release URL.
- [x] Sprints 1 through 5 implementation scope is documented as
  simulator-local and symbolic.
- [x] v1.3 lifecycle history docs are checked in at
  `docs/STREAM_OFFER_LIFECYCLE_HISTORY_v1_3.md`.
- [x] v1.3 lifecycle planning/apply docs are checked in at
  `docs/STREAM_OFFER_LIFECYCLE_PLANNING_v1_3.md`.
- [x] v1.3 scenario DSL coverage was added after helper behavior stabilized.
- [x] Scenarios `058` through `060` validate and run.
- [x] Planning-branch scenario metadata is contiguous from `001` through
  `060`.
- [x] Scenario index is current and generated from deterministic scenario
  metadata.
- [x] v1.3 documentation readiness checks include the roadmap, release
  notes, lifecycle history docs, and lifecycle planning/apply docs.
- [x] v1.3 release notes summarize Sprints 1 through 6, including
  release-candidate hardening scope.
- [x] CHANGELOG contains a dated `1.3.0` release section.
- [x] v1.3 release notes are converted from draft/planning language to
  released status language.
- [x] Ruff passes with `python -m ruff check .`.
- [x] Tests pass with `python -m pytest` with 808 tests.
- [x] All checked-in scenarios `001` through `060` pass with
  `python scripts/run_all_scenarios.py`.
- [x] Documentation avoids production networking, sockets, HTTP/WebSocket
  behavior, DNS lookup, registrar integration, public CA behavior, external
  services, real cryptography, key generation, private key storage, production
  E2EE, delivery enforcement, automatic cleanup workers, retry loops, durable
  queues, live timers, live clocks, live polling, delivery behavior changes,
  compact snapshot changes, TrafficHub routing changes, canonical identity
  rewrites, and production anonymity/privacy/firewall/DDoS guarantees.
- [x] Existing mailbox delivery, encrypted delivery, TrafficHub routing,
  alias, identity, stream-offer polling/admission behavior, retained
  histories, and canonical identity behavior remain unchanged.
- [x] Merge to `main`, annotated tag, and GitHub release are complete.
- [x] No package publication was performed.
- [x] No release assets were uploaded.
- [x] No version bump, new feature behavior, new scenarios, compact snapshot
  change, automatic cleanup worker, retry loop, durable queue, live timer,
  networking, DNS, external service, real cryptography, delivery change,
  TrafficHub routing change, or canonical identity rewrite is added by
  post-release housekeeping.

## v1.3 Release Validation Commands

```bash
python -m ruff check .
python -m pytest
python scripts/run_all_scenarios.py
python -m darwin.cli.main --version
```

# DARWIN v1.4 Lifecycle Explanation Release Checklist

v1.4.0 is released on `main` as `darwin-sim 1.4.0`. The annotated `v1.4.0`
tag and GitHub release exist:
https://github.com/dabbodev/DARWIN/releases/tag/v1.4.0. No package publication
was performed, and no release assets were uploaded.

- [x] v1.4 planning roadmap seed is checked in at `docs/V1_4_ROADMAP.md`.
- [x] v1.4 draft release notes are checked in at
  `docs/RELEASE_NOTES_v1_4_DRAFT.md`.
- [x] v1.4 lifecycle explanation docs are checked in at
  `docs/STREAM_OFFER_LIFECYCLE_EXPLANATIONS_v1_4.md`.
- [x] v1.4 lifecycle audit summary docs are checked in at
  `docs/STREAM_OFFER_LIFECYCLE_AUDIT_SUMMARIES_v1_4.md`.
- [x] v1.4 retained explanation history docs are checked in at
  `docs/STREAM_OFFER_LIFECYCLE_EXPLANATION_HISTORY_v1_4.md`.
- [x] README links to the v1.4 release docs.
- [x] CHANGELOG contains a dated `1.4.0` release section.
- [x] Package version is confirmed as `1.4.0`.
- [x] CLI version reports `darwin-sim 1.4.0`.
- [x] Sprints 1 through 5 implementation scope is documented as
  simulator-local and symbolic.
- [x] Sprint 6 is v1.4 release-candidate hardening and documentation audit
  only.
- [x] Scenarios `061` through `063` validate and run.
- [x] Released scenario metadata is contiguous from `001` through `063`.
- [x] Scenario index is current and generated from deterministic scenario
  metadata.
- [x] v1.4 documentation readiness checks include the roadmap, draft release
  notes, lifecycle explanation docs, audit summary docs, and retained
  explanation history docs.
- [x] v1.4 draft release notes summarize Sprint 1 through Sprint 6 and
  release status without claiming package publication or release assets.
- [x] No new v1.4 feature behavior or scenarios are added by
  release-candidate hardening.
- [x] Planning scope is limited to lifecycle policy explanation and
  stream-offer audit summary candidates.
- [x] Documentation avoids production networking, sockets, HTTP/WebSocket
  behavior, DNS lookup, registrar integration, public CA behavior, external
  services, real cryptography, key generation, private key storage, production
  E2EE, delivery enforcement, automatic cleanup workers, retry loops, durable
  queues, live timers, live clocks, live polling, lifecycle mutation behavior
  beyond existing explicit helpers, delivery behavior changes, TrafficHub
  routing changes, compact snapshot changes, canonical identity rewrites, and
  production anonymity/privacy/firewall/DDoS guarantees.
- [x] v1.4 release prep does not add new feature behavior, new scenarios,
  lifecycle mutation behavior, compact snapshot changes, automatic cleanup
  workers, retry loops, durable queues, live timers, networking, DNS, external
  services, real cryptography, delivery changes, TrafficHub routing changes,
  or canonical identity rewrites.
- [x] Merge to `main`, annotated tag, and GitHub release are complete.
- [x] No release assets or package publication were performed.

## v1.4 Release Validation Commands

```bash
python -m ruff check .
python -m pytest
python scripts/run_all_scenarios.py
python -m darwin.cli.main --version
```

# DARWIN v1.5 Lifecycle Explanation Retention Release Checklist

v1.5.0 is released on `main` as `darwin-sim 1.5.0`. The annotated `v1.5.0`
tag and GitHub release exist:
https://github.com/dabbodev/DARWIN/releases/tag/v1.5.0. No package publication
was performed, and no release assets were uploaded.

- [x] v1.5 planning roadmap seed is checked in at `docs/V1_5_ROADMAP.md`.
- [x] v1.5 draft release-notes placeholder is checked in at
  `docs/RELEASE_NOTES_v1_5_DRAFT.md`.
- [x] v1.5 lifecycle explanation retention docs are checked in at
  `docs/STREAM_OFFER_LIFECYCLE_EXPLANATION_RETENTION_v1_5.md`.
- [x] v1.5 lifecycle explanation pruning docs are checked in at
  `docs/STREAM_OFFER_LIFECYCLE_EXPLANATION_PRUNING_v1_5.md`.
- [x] README links to the v1.5 release docs.
- [x] Planning scope is limited to lifecycle explanation retention policy and
  audit pruning summary candidates.
- [x] Sprint 1 through Sprint 5 implementation scope is documented as
  simulator-local and symbolic.
- [x] v1.5 release-candidate hardening and documentation audit is Sprint 6
  only and does not add new feature behavior.
- [x] Scenarios `064` through `066` validate and run.
- [x] Released scenario metadata is contiguous from `001` through `066`.
- [x] Scenario index is current and generated from deterministic scenario
  metadata.
- [x] v1.5 documentation readiness checks include the roadmap, draft release
  notes, lifecycle explanation retention docs, and lifecycle explanation
  pruning docs.
- [x] v1.5 draft release notes summarize Sprint 1 through Sprint 6 and
  release status without claiming package publication, release assets, or
  production behavior.
- [x] CHANGELOG contains a dated `1.5.0` release section.
- [x] Package version is confirmed as `1.5.0`.
- [x] CLI version reports `darwin-sim 1.5.0`.
- [x] Release docs avoid production networking, sockets, HTTP/WebSocket
  behavior, DNS lookup, registrar integration, public CA behavior, external
  services, real cryptography, key generation, private key storage, production
  E2EE, delivery enforcement, automatic cleanup workers, retry loops, durable
  queues, live timers, live clocks, live polling, retention/pruning behavior
  beyond explicit simulator helpers, delivery behavior changes, TrafficHub
  routing changes, compact snapshot changes, canonical identity rewrites, and
  production anonymity/privacy/firewall/DDoS guarantees.
- [x] Release prep does not add release assets, package publication, automatic
  cleanup workers, retry loops, durable queues, live timers, networking, DNS,
  external services, real cryptography, delivery changes, TrafficHub routing
  changes, compact snapshot changes, or canonical identity rewrites.
- [x] Merge to `main`, annotated tag, and GitHub release are complete.
- [x] No release assets or package publication were performed.

## v1.5 Release Validation Commands

```bash
python -m ruff check .
python -m pytest
python scripts/run_all_scenarios.py
python -m darwin.cli.main --version
```

# DARWIN v1.6 Retained Audit Compaction Release Checklist

v1.6.0 is released on `main` as `darwin-sim 1.6.0`. The annotated `v1.6.0`
tag and GitHub release exist:
https://github.com/dabbodev/DARWIN/releases/tag/v1.6.0. No package publication
was performed, and no release assets were uploaded.

- [x] v1.6 planning roadmap seed is checked in at `docs/V1_6_ROADMAP.md`.
- [x] v1.6 draft release-notes placeholder is checked in at
  `docs/RELEASE_NOTES_v1_6_DRAFT.md`.
- [x] README links to the v1.6 release docs.
- [x] Planning scope is limited to retained audit compaction and replay-summary
  candidates.
- [x] Candidate scope is simulator-local and symbolic.
- [x] Sprint 6 is v1.6 release-candidate hardening and documentation audit
  only; it does not add new feature behavior.
- [x] Documentation readiness/link checks include `docs/V1_6_ROADMAP.md`,
  `docs/RELEASE_NOTES_v1_6_DRAFT.md`,
  `docs/RETAINED_AUDIT_COMPACTION_POLICY_v1_6.md`,
  `docs/RETAINED_AUDIT_REPLAY_SUMMARIES_v1_6.md`, and
  `docs/RETAINED_AUDIT_COMPACTION_APPLY_v1_6.md`.
- [x] v1.6 draft release notes summarize Sprint 1 through Sprint 6 and release
  status without claiming package publication, release assets, or production
  behavior.
- [x] Released scenario metadata is contiguous from `001` through `069`.
- [x] `docs/SCENARIO_INDEX.md` is current and exactly generated from
  deterministic scenario metadata.
- [x] `CHANGELOG.md` contains a dated `1.6.0` release section.
- [x] Package version is confirmed as `1.6.0`.
- [x] CLI version reports `darwin-sim 1.6.0`.
- [x] No v1.6 feature behavior, scenario behavior, or tests for new feature
  behavior are added by the planning seed.
- [x] Release docs avoid production networking, sockets, HTTP/WebSocket
  behavior, DNS lookup, registrar integration, public CA behavior, external
  services, real cryptography, key generation, private key storage, production
  E2EE, delivery enforcement, automatic cleanup workers, retry loops, durable
  queues, live timers, live clocks, live polling, delivery behavior changes,
  TrafficHub routing changes, compact snapshot changes, canonical identity
  rewrites, and production security/privacy/anonymity/firewall/DDoS,
  compliance, or data-retention guarantees.
- [x] Release prep does not add compaction classification precedence changes,
  replay-summary semantic changes, compaction-apply semantic changes,
  automatic cleanup workers, retry loops, durable queues, live timers,
  networking, DNS, external services, real cryptography, delivery changes,
  TrafficHub routing changes, compact snapshot changes, or canonical identity
  rewrites.
- [x] Merge to `main`, annotated tag, and GitHub release are complete.
- [x] No release assets or package publication were performed.

## v1.6 Release Validation Commands

```bash
python -m ruff check .
python -m pytest
python scripts/run_all_scenarios.py
python -m darwin.cli.main --version
```

# DARWIN v1.7 Poll and Admission Retained-Audit Release Checklist

This checklist describes the immutable v1.7.0 source snapshot. Remote
publication state is intentionally not inferred from repository contents. The
publication procedure creates an annotated `v1.7.0` tag and GitHub source
release from the exact validated commit; it performs no package publication
and uploads no release assets.

- [x] v1.7 roadmap is checked in at `docs/V1_7_ROADMAP.md`.
- [x] v1.7 release notes are checked in at
  `docs/RELEASE_NOTES_v1_7_DRAFT.md`.
- [x] The cohesive poll/admission expansion specification is checked in at
  `docs/RETAINED_AUDIT_POLL_ADMISSION_v1_7.md`.
- [x] README links to all v1.7 release documents.
- [x] `CHANGELOG.md` contains a dated `1.7.0` source-release section.
- [x] Package and CLI metadata report `darwin-sim 1.7.0`.
- [x] `requires-python` remains `>=3.11`; classifiers cover Python 3.11,
  3.12, 3.13, and 3.14.
- [x] CI validates Python 3.11 through 3.14 and verifies exact CLI output.
- [x] CI has a separate Python 3.11 wheel build/install smoke job and no
  artifact or package upload step.
- [x] Existing supported retained-audit history types keep their v1.6 order,
  followed by poll-result and admission-decision histories.
- [x] Replay summaries expose optional sorted request-ID counts without
  expanding poll matched-offer IDs into offer grouping.
- [x] Explicit apply selects one supported history; mixed decisions remain
  read-only and unsupported for mutation.
- [x] Scenarios `070` through `072` cover classification, replay, and isolated
  apply; checked-in scenario metadata is contiguous from `001` through `072`.
- [x] Detailed retained-audit summaries remain copied and JSON-safe, and
  compact `world.snapshot()` remains unchanged.
- [x] Release documentation avoids claims of automatic cleanup, production
  retention/compliance, networking, cryptography, security, privacy,
  anonymity, firewall, DDoS, delivery, or routing behavior.
- [x] Ruff passes and pytest passes with 909 tests.
- [x] All scenarios `001` through `072` pass and the checked-in scenario index
  exactly matches deterministic generated metadata.
- [x] The CLI reports `darwin-sim 1.7.0`.
- [x] An isolated `darwin_sim-1.7.0-py3-none-any.whl` build, install, and
  out-of-tree version smoke check passes without uploading the wheel.

## v1.7 Source-Snapshot Validation Commands

These commands produced the checked results above. The checklist does not
infer remote tag/release existence from repository contents.

```bash
python -m ruff check .
python -m pytest
python scripts/run_all_scenarios.py
python -m darwin.cli.main scenario-index
python -m darwin.cli.main --version
python -m build --wheel
```

# DARWIN v1.8 Encrypted-Delivery Retained-Audit Release Checklist

This checklist describes the immutable v1.8.0 source snapshot. Remote
publication state is intentionally not inferred from repository contents. The
publication procedure creates an annotated `v1.8.0` tag and GitHub source
release from the exact validated commit; it performs no package publication
and uploads no release assets.

- [x] v1.8 roadmap is checked in at `docs/V1_8_ROADMAP.md`.
- [x] v1.8 release notes are checked in at
  `docs/RELEASE_NOTES_v1_8_DRAFT.md`.
- [x] The encrypted-delivery retained-audit specification is checked in at
  `docs/RETAINED_AUDIT_ENCRYPTED_DELIVERY_v1_8.md`.
- [x] README links to all v1.8 release documents.
- [x] `CHANGELOG.md` contains the dated `1.8.0` source-release section.
- [x] Package and CLI metadata report `darwin-sim 1.8.0`.
- [x] Existing retained-audit history types keep their v1.7 order and key
  behavior, followed by `encrypted_delivery_result`.
- [x] Encrypted result ownership uses only string `metadata["registry_hub"]`.
- [x] Replay summaries expose sorted, copied message-ID and mailbox-ID counts.
- [x] Explicit apply mutates only selected encrypted-delivery result history;
  policy decisions, direct delivery results, and inboxes remain unchanged.
- [x] Scenarios `073` through `075` cover classification, replay, and isolated
  apply; checked-in scenario metadata is contiguous from `001` through `075`.
- [x] Detailed retained-audit summaries remain copied and JSON-safe, and
  compact `world.snapshot()` remains unchanged.
- [x] Python 3.11 through 3.14 CI and exact CLI-version verification remain in
  place.
- [x] The Python 3.11 wheel build/install smoke job performs no upload.
- [x] Release documentation avoids production networking, cryptography,
  security, privacy, compliance, delivery, routing, and retention claims.
- [x] Ruff passes and pytest passes with 922 tests.
- [x] All scenarios `001` through `075` pass and the checked-in scenario index
  exactly matches deterministic generated metadata.
- [x] The CLI reports `darwin-sim 1.8.0`.
- [x] An isolated `darwin_sim-1.8.0-py3-none-any.whl` build, install, and
  out-of-tree version smoke check passes without uploading the wheel.
- [x] Ruff, pytest, all scenarios, exact scenario-index verification, CLI
  version output, and isolated wheel installation pass.

## v1.8 Source-Snapshot Validation Commands

```bash
python -m ruff check .
python -m pytest
python scripts/run_all_scenarios.py
python -m darwin.cli.main scenario-index
python -m darwin.cli.main --version
python -m build --wheel
```

# DARWIN v1.9 Encryption-Policy Retained-Audit Release Checklist

This checklist describes the immutable v1.9.0 source snapshot dated
2026-07-26 (America/Los_Angeles).
Remote publication state is intentionally not inferred from repository
contents. The publication procedure creates an annotated `v1.9.0` tag and
GitHub source release from the exact validated commit; it performs no package-
index publication and uploads no release assets.

- [x] v1.9 roadmap is checked in at `docs/V1_9_ROADMAP.md`.
- [x] v1.9 release notes retain the compatible path
  `docs/RELEASE_NOTES_v1_9_DRAFT.md`.
- [x] The encryption-policy retained-audit specification is checked in at
  `docs/RETAINED_AUDIT_ENCRYPTION_POLICY_v1_9.md`.
- [x] README links to all v1.9 release documents.
- [x] Package, CLI, smoke tests, and CI expect `darwin-sim 1.9.0`.
- [x] Existing retained-audit history types keep their v1.8 order and key
  behavior, followed by `encryption_policy_decision`.
- [x] Policy-decision ownership uses only string
  `metadata["registry_hub"]`.
- [x] Replay summaries expose sorted, copied policy-ID and lane-signature
  counts.
- [x] Explicit apply mutates only selected encryption-policy decision history;
  encrypted/direct delivery and nested policy snapshots remain unchanged.
- [x] Scenarios `076` through `078` cover classification, replay, and isolated
  apply; checked-in metadata is contiguous from `001` through `078`.
- [x] Detailed retained-audit summaries remain copied and JSON-safe, and
  compact `world.snapshot()` remains unchanged.
- [x] Python 3.11 through 3.14 CI and exact CLI-version verification remain in
  place.
- [x] CI fails when generated scenario-index stdout differs from
  `docs/SCENARIO_INDEX.md`.
- [x] The Python 3.11 wheel build/install smoke job performs no upload.
- [x] Release documentation avoids production networking, cryptography,
  security, privacy, compliance, delivery, routing, and retention claims.
- [x] The actual America/Los_Angeles release date is recorded as 2026-07-26.
- [x] Ruff passes and pytest passes with 935 tests.
- [x] Ruff, pytest, scenarios `001` through `078`, exact scenario-index
  comparison, CLI output, wheel build, isolated installation, and out-of-tree
  version smoke all pass.

## v1.9 Source-Snapshot Validation Commands

```bash
python -m ruff check .
python -m pytest
python scripts/run_all_scenarios.py
python -m darwin.cli.main scenario-index
python -m darwin.cli.main --version
python -m build --wheel
```

# DARWIN v1.10 Direct Message-Delivery Retained-Audit Release Checklist

This checklist describes the immutable v1.10.0 source snapshot dated
2026-07-27 (America/Los_Angeles). Remote publication state is intentionally
not inferred from repository contents. The publication procedure creates an
annotated `v1.10.0` tag and GitHub source release from the exact validated
commit; it performs no package-index publication and uploads no release
assets.

- [x] v1.10 roadmap is checked in at `docs/V1_10_ROADMAP.md`.
- [x] v1.10 release notes retain the compatible path
  `docs/RELEASE_NOTES_v1_10_DRAFT.md`.
- [x] The direct message-delivery retained-audit specification is checked in
  at `docs/RETAINED_AUDIT_MESSAGE_DELIVERY_v1_10.md`.
- [x] README links to all v1.10 release documents.
- [x] Package, CLI, smoke tests, and CI expect `darwin-sim 1.10.0`.
- [x] Existing retained-audit history types keep their v1.9 order and key
  behavior, followed by `message_delivery_result`.
- [x] Helper-created result ownership uses string
  `metadata["registry_hub"]` and overrides conflicting internal metadata.
- [x] Replay summaries reuse sorted, copied message, mailbox, lane, status,
  reason, and optional source counts without inferring other dimensions.
- [x] Explicit apply mutates only selected direct message-delivery result
  history; inboxes, completed delivery state, and unrelated histories remain
  unchanged.
- [x] Scenarios `079` through `081` cover classification, replay, and isolated
  apply; checked-in metadata is contiguous from `001` through `081`.
- [x] Detailed retained-audit summaries remain copied and JSON-safe, and
  compact `world.snapshot()` remains unchanged.
- [x] Python 3.11 through 3.14 CI and exact CLI-version verification remain in
  place.
- [x] CI fails when generated scenario-index stdout differs from
  `docs/SCENARIO_INDEX.md`.
- [x] The Python 3.11 wheel build/install smoke job performs no upload.
- [x] Release documentation avoids production networking, cryptography,
  security, privacy, compliance, delivery, routing, and retention claims.
- [x] The actual America/Los_Angeles release date is recorded as 2026-07-27.
- [x] Ruff passes and pytest passes with 950 tests.
- [x] Ruff, pytest, scenarios `001` through `081`, exact scenario-index
  comparison, CLI output, wheel build, isolated installation, and out-of-tree
  version smoke all pass.

## v1.10 Source-Snapshot Validation Commands

```bash
python -m ruff check .
python -m pytest
python scripts/run_all_scenarios.py
python -m darwin.cli.main scenario-index
python -m darwin.cli.main --version
python -m build --wheel
```

# DARWIN v1.11 Authority-Outcome Retained-Audit Release Checklist

This checklist describes the v1.11.0 source-release snapshot validated on
2026-07-29 (America/Los_Angeles) with 964 passing tests. Remote publication
state is intentionally not inferred from repository contents. The publication
procedure creates an
annotated `v1.11.0` tag and GitHub source release from the exact validated
commit; it performs no package-index publication and uploads no release
assets.

- [x] v1.11 roadmap is checked in at `docs/V1_11_ROADMAP.md`.
- [x] v1.11 release notes retain the compatible path
  `docs/RELEASE_NOTES_v1_11_DRAFT.md`.
- [x] The authority-outcome retained-audit specification is checked in at
  `docs/RETAINED_AUDIT_AUTHORITY_OUTCOME_v1_11.md`.
- [x] README links to all v1.11 release documents.
- [x] Package, CLI, smoke tests, and CI expect `darwin-sim 1.11.0`.
- [x] Existing retained-audit history types keep their v1.10 order and key
  behavior, followed by `authority_outcome`.
- [x] Authority ownership uses only string `requesting_hub`, and generic
  status filtering uses `final_status`.
- [x] Replay summaries expose sorted copied requested/granted alias,
  target-device, and path-hub counts.
- [x] Explicit apply mutates only selected authority outcome history; aliases,
  conflicts, security events, other histories, canonical identity, and
  TrafficHub state remain unchanged.
- [x] Scenarios `082` through `084` cover classification, replay, and isolated
  apply; checked-in metadata is contiguous from `001` through `084`.
- [x] Detailed retained-audit summaries remain copied and JSON-safe, and
  compact `world.snapshot()` remains unchanged.
- [x] Python 3.11 through 3.14 CI and exact CLI-version verification remain in
  place.
- [x] CI fails when generated scenario-index stdout differs from
  `docs/SCENARIO_INDEX.md`.
- [x] The Python 3.11 wheel build/install smoke job performs no upload.
- [x] Release documentation avoids production networking, cryptography,
  security, privacy, compliance, authority, and retention claims.
- [x] Record the actual America/Los_Angeles validation date: 2026-07-29.
- [x] Record the actual final pytest count: 964 passing tests.
- [x] Ruff, pytest, scenarios `001` through `084`, exact scenario-index
  comparison, CLI output, wheel build, isolated installation, and out-of-tree
  version smoke all pass.

## v1.11 Source-Snapshot Validation Commands

```bash
python -m ruff check .
python -m pytest
python scripts/run_all_scenarios.py
python -m darwin.cli.main scenario-index
python -m darwin.cli.main --version
python -m build --wheel
```

# DARWIN v1.12 Retained-Audit Batch Apply Release Checklist

This checklist describes the v1.12.0 source-release snapshot prepared and
validated on 2026-07-30 (America/Los_Angeles) with 991 passing tests. Remote
publication state is intentionally not inferred from repository contents. The
publication procedure creates an annotated
`v1.12.0` tag and GitHub source release from the exact validated commit; it
performs no package-index publication and uploads no release assets.

- [x] v1.12 roadmap is checked in at `docs/V1_12_ROADMAP.md`.
- [x] v1.12 release notes retain the compatible permanent path
  `docs/RELEASE_NOTES_v1_12_DRAFT.md`.
- [x] The retained-audit batch-apply specification is checked in at
  `docs/RETAINED_AUDIT_BATCH_APPLY_v1_12.md`.
- [x] README links to all v1.12 release documents.
- [x] Package, CLI, smoke tests, and CI expect `darwin-sim 1.12.0`.
- [x] All eight retained-audit history types preserve their v1.11 order, exact
  keys, policies, replay behavior, and single-history APIs.
- [x] Batch apply requires at least two distinct supported single-history
  decisions for the same RegistryHub and preflights the whole batch before
  mutation.
- [x] Canonical processing and nested results use the supported history order
  independently of caller order.
- [x] Stale child candidates are reported while current candidates in another
  selected history apply; repeats are deterministic no-ops.
- [x] Only aggregate batch results enter the action-result stream; detailed
  snapshots append copied batch results and compact snapshots remain
  unchanged.
- [x] Scenarios `085` through `087` cover canonical success, stale/repeated
  apply, and isolation; checked-in metadata is contiguous from `001` through
  `087`.
- [x] Unselected histories, aliases, conflicts, security events,
  delivery/encryption state, canonical identity, and TrafficHub state remain
  unchanged.
- [x] Python 3.11 through 3.14 CI and exact CLI-version verification remain in
  place.
- [x] CI fails when generated scenario-index stdout differs from
  `docs/SCENARIO_INDEX.md`.
- [x] The Python 3.11 wheel build/install smoke job performs no upload.
- [x] Release documentation avoids production networking, cryptography,
  security, privacy, compliance, and retention claims.
- [x] Record the actual America/Los_Angeles validation date: 2026-07-30.
- [x] Record the actual final pytest count: 991 passing tests.
- [x] Ruff, pytest, scenarios `001` through `087`, exact scenario-index
  comparison, CLI output, wheel build, isolated installation, and out-of-tree
  version smoke all pass.

## v1.12 Source-Snapshot Validation Commands

```bash
python -m ruff check .
python -m pytest
python scripts/run_all_scenarios.py
python -m darwin.cli.main scenario-index
python -m darwin.cli.main --version
python -m build --wheel
```

# DARWIN v1.13 Retained-Audit Batch Preview Release Checklist

This checklist describes the v1.13.0 source-release snapshot prepared with the
America/Los_Angeles validation date and final pytest count pending the first
complete passing release-gate set. Remote publication state is intentionally
not inferred from repository contents. The publication procedure creates an
annotated `v1.13.0` tag and GitHub source release from the exact validated
commit; it performs no package-index publication and uploads no release
assets.

- [x] v1.13 roadmap is checked in at `docs/V1_13_ROADMAP.md`.
- [x] v1.13 release notes retain the compatible permanent path
  `docs/RELEASE_NOTES_v1_13_DRAFT.md`.
- [x] The retained-audit batch-preview specification is checked in at
  `docs/RETAINED_AUDIT_BATCH_PREVIEW_v1_13.md`.
- [x] README and development guidance link to all v1.13 release documents.
- [x] Package, CLI, smoke tests, and both CI assertions expect exact output
  `darwin-sim 1.13.0`.
- [x] All eight retained-audit history types preserve their v1.12 order, exact
  keys, policies, replay behavior, and single/batch apply APIs and outputs.
- [x] Preview requires at least two distinct supported single-history
  decisions for one RegistryHub and shares complete structural preflight with
  apply before any write.
- [x] Public preview results and summarizers expose copied canonical child and
  aggregate would-compact, retained, ignored, missing, and unsupported values.
- [x] Batch apply maps the private shared evaluator to existing results and
  mutations without calling the public preview helper.
- [x] Present preview keys use current history order, missing keys use decision
  order, and valid preview unsupported values are empty.
- [x] `batch_id` is reusable correlation metadata only, not a reservation,
  uniqueness constraint, deduplication key, or idempotency ledger.
- [x] Generated metadata overrides caller conflicts and records canonical
  order, structural preflight, stale/would-mutate, read-only, unchanged-state
  parity, and simulator-safety facts without claiming runtime-confirmed parity.
- [x] Direct helper success and rejection preserve serialized RegistryHub,
  retained histories, and TrafficHub state.
- [x] Only aggregate preview results enter `World.action_results`; scenarios
  log `retained_audit_compaction_batch_previewed`, detailed snapshots append
  copied preview results after batch apply, and compact snapshots remain
  unchanged.
- [x] Scenarios `088` through `090` cover canonical preview/immediate apply
  parity, stale repeatability, and isolation; checked-in metadata is contiguous
  from `001` through `090`.
- [x] Python 3.11 through 3.14 CI and separate Python 3.11 wheel smoke remain in
  place.
- [x] CI fails when generated scenario-index stdout differs from
  `docs/SCENARIO_INDEX.md`.
- [x] The wheel is an isolated validation artifact; the workflow performs no
  upload or package-index publication.
- [x] Release documentation excludes automatic apply, preview ledgers,
  reservations/deduplication, strict stale aborts, transactions, new history
  types/filters/replay dimensions, mixed apply, background work, real
  networking/cryptography, and production guarantees.
- [ ] Run Ruff, pytest, scenarios `001` through `090`, exact scenario-index
  comparison, exact source CLI output, wheel build, isolated installation, and
  out-of-tree wheel CLI verification as one complete gate set.
- [ ] Record the actual America/Los_Angeles validation date only after that
  complete gate set passes. Pending validation.
- [ ] Record the actual final pytest count only after that complete gate set
  passes. Pending validation.
- [ ] Rerun the complete gate set after factualization without adding or
  removing tests.

## v1.13 Source-Snapshot Validation Commands

```bash
python -m ruff check .
python -m pytest
python scripts/run_all_scenarios.py
python -m darwin.cli.main scenario-index
python -m darwin.cli.main --version
python -m build --wheel
```
