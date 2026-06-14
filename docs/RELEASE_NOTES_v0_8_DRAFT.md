# DARWIN v0.8 Draft Release Notes

Status: unreleased draft work on `v0.8/planning`.

Current package and CLI version: `darwin-sim 0.7.0`.

Do not treat this document as a release announcement. v0.8 has not been
merged, tagged, released, or published.

## Highlights

- Added minimal persistent simulator-local authority outcome records through
  `AliasAuthorityOutcomeRecord`.
- Retained authority outcomes on the starting/requesting `RegistryHub` in
  `RegistryHub.authority_outcome_history`.
- Preserved successful approvals, fallback grants, name-taken conflicts,
  simulator-local policy denials, broken authority paths, and other terminal
  authority-chain failures as compact retained summaries.
- Added read-only retained authority outcome query helpers through
  `query_authority_outcomes(...)`.
- Added the read-only scenario assertion
  `authority_outcome_history_contains`.
- Added draft v0.8 scenarios `042_authority_outcome_history_success` and
  `043_authority_outcome_history_denials`.
- Exposed retained authority outcome summaries in detailed snapshots under
  `registry_hubs.<hub_id>.authority_outcome_history`.
- Exposed retained authority outcome summaries in existing JSON snapshot and
  scenario-result exports through the final detailed snapshot.
- Hardened tests and documentation for retained records, query filters,
  scenario assertion validation, diagnostics, snapshot/export visibility, and
  scenario listing coverage.

## Compatibility

- The package and CLI version remain `darwin-sim 0.7.0` during v0.8 planning.
- Compact `world.snapshot()` output remains unchanged.
- Existing alias claim, release, resolve, conflict, denial, quarantine,
  fallback, and authority-chain behavior remains unchanged.
- TrafficHub routing behavior remains unchanged.
- Canonical identity behavior remains unchanged.
- No new scenario DSL actions are added.

## Simulator-Only Non-Goals

v0.8 retained authority outcome history is simulator-local introspection only.
It is not production audit or compliance infrastructure.

Non-goals:

- No production audit or compliance guarantees.
- No broad event store.
- No real DNS.
- No registrar integration.
- No public CA behavior.
- No production identity proof.
- No external services.
- No TrafficHub routing changes.
- No canonical identity rewrite.

## Current Limitations

- Retained authority outcomes are kept in memory on the requesting
  `RegistryHub`.
- Records are compact summaries, not full production audit events.
- Detailed snapshots and JSON exports expose the compact retained summaries,
  but compact `world.snapshot()` remains an ID-only overview.
- Retention is deterministic and JSON-safe, but it has no persistence layer
  outside the simulator process unless callers explicitly export scenario
  results or snapshots.
- v0.8 remains unreleased draft work until release prep intentionally bumps
  version, validates release artifacts, tags, and publishes a release.

## Validation Target

Before v0.8 release prep, the expected validation set is:

```bash
python -m ruff check .
python -m pytest
python scripts/run_all_scenarios.py
python -m darwin.cli.main --version
```

Expected version output remains:

```text
darwin-sim 0.7.0
```
