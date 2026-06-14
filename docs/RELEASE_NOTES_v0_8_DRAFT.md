# DARWIN v0.8.0 Release Notes

Status: released on `main`.

DARWIN v0.8.0 has been merged to `main`, tagged as annotated `v0.8.0`, and
published as a GitHub release. No package publication was performed.

Current package and CLI version: `darwin-sim 0.8.0`.

## Highlights

- Added minimal persistent simulator-local authority outcome records through
  `AliasAuthorityOutcomeRecord`.
- Retained authority outcomes on the starting/requesting `RegistryHub` in
  `RegistryHub.authority_outcome_history`.
- Preserved successful approvals, fallback grants, name-taken conflicts,
  simulator-local policy denials, broken authority paths, and terminal
  authority-chain failures as compact retained summaries.
- Added read-only retained authority outcome query helpers through
  `query_authority_outcomes(...)`.
- Added compact JSON-safe `AuthorityOutcomeQueryResult` objects for query
  results.
- Added the read-only scenario assertion
  `authority_outcome_history_contains`.
- Added v0.8 scenarios `042_authority_outcome_history_success` and
  `043_authority_outcome_history_denials`.
- Exposed retained authority outcome summaries in detailed snapshots under
  `registry_hubs.<hub_id>.authority_outcome_history`.
- Exposed retained authority outcome summaries in existing JSON snapshot and
  scenario-result exports through the final detailed snapshot.
- Hardened tests and documentation for retained records, query filters,
  scenario assertion validation, diagnostics, snapshot/export visibility, and
  scenario listing coverage.
- Hardened scenario metadata/index checks so checked-in scenarios `001`
  through `043` remain discoverable without numbering gaps.

## Compatibility

- The package and CLI version now report `darwin-sim 0.8.0`.
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
- No package publication was performed.

## Current Limitations

- Retained authority outcomes are kept in memory on the requesting
  `RegistryHub`.
- Records are compact summaries, not full production audit events.
- Detailed snapshots and JSON exports expose the compact retained summaries,
  but compact `world.snapshot()` remains an ID-only overview.
- Retention is deterministic and JSON-safe, but it has no persistence layer
  outside the simulator process unless callers explicitly export scenario
  results or snapshots.
- The released scenario set is scenarios `001` through `043`.

## Validation Target

Final release validation passed on `main`:

```bash
python -m ruff check .
python -m pytest
python scripts/run_all_scenarios.py
python -m darwin.cli.main --version
```

Expected version output is:

```text
darwin-sim 0.8.0
```
