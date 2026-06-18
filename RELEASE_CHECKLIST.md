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

v1.1.0 is release-prep work on the `v1.1/planning` branch. It has not been
merged, tagged as `v1.1.0`, published as a GitHub release, or published as a
package.

- [x] Package version is updated to `1.1.0` on the planning branch.
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
- [x] CHANGELOG contains an unreleased `1.1.0` release-prep section.
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
- [x] Merge to `main` has not been performed.
- [x] Annotated tag `v1.1.0` has not been created.
- [x] GitHub release has not been created.
- [x] Package publication has not been performed.

## v1.1 Release-Prep Validation Commands

```bash
python -m ruff check .
python -m pytest
python scripts/run_all_scenarios.py
python -m darwin.cli.main --version
python -m darwin.cli.main scenario-index
python -m darwin.cli.main list-scenarios
```
