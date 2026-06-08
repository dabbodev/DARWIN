# DARWIN v0.7 Draft Release Notes

Status: unreleased draft work on `v0.7/planning`.

Current package and CLI version: `darwin-sim 0.6.0`.

These notes are draft release-note material only. v0.7 has not been tagged,
merged, packaged, or released.

## Draft Highlights

- Read-only RegistryHub history query helpers for retained alias records, alias
  conflicts, persisted terminal alias authority grant provenance, and
  quarantine/security records.
- Read-only authority audit trace summaries for in-memory authority paths and
  retained RegistryHub grant provenance.
- Deterministic trace explanation helpers for authority traces, alias history
  entries, alias conflict entries, and quarantine event entries.
- Scenario DSL assertions for registry history, authority audit trace, and
  explanation checks:
  `alias_history_contains`, `alias_conflict_history_contains`,
  `authority_audit_trace_contains`, and `quarantine_history_contains`.
- v0.7 draft scenarios `037` through `041`:
  `037_registry_history_alias_claim`,
  `038_registry_history_alias_conflict`,
  `039_authority_audit_trace_success`,
  `040_authority_audit_trace_fallback`, and
  `041_trace_explainability_denials`.
- Sprint 5 tests and documentation hardening for assertion validation, failure
  output, scenario coverage, and retained-data limitations.

## Simulator-Only Non-Goals

- No simulator runtime behavior changes are intended.
- No changes to alias claim, release, resolution, conflict, denial,
  quarantine, or explanation semantics.
- No TrafficHub routing changes.
- No canonical identity rewrite.
- No new persistent history storage or broad event store.
- No external services.
- No real DNS, registrar integration, public CA behavior, or production
  identity proof.
- No production audit or compliance guarantees.

## Retained-Data Limitations

RegistryHub retains terminal grant provenance, not full persistent failed
authority-chain paths. Retained RegistryHub audit traces can explain approved
and fallback grants that were stored as terminal provenance.

Denied authority-chain outcomes are explainable only while the caller still
has the in-memory action-result authority path or a summary derived from it.
Scenario `041_trace_explainability_denials` demonstrates that scenario-run-only
path, not persistent failed-path audit storage.

## Draft Validation Target

```bash
python -m ruff check .
python -m pytest
python scripts/run_all_scenarios.py
python -m darwin.cli.main --version
```

Expected version output remains:

```text
darwin-sim 0.6.0
```
