# DARWIN v0.7.0 Draft Release Notes

Status: unreleased release-prep work on `v0.7/planning`.

Current package and CLI version on this branch: `darwin-sim 0.7.0`.

These notes are release-prep material only. v0.7.0 has not been merged to
`main`, tagged, published as a GitHub release, packaged, or released.

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
- v0.7 release-prep scenarios `037` through `041`:
  `037_registry_history_alias_claim`,
  `038_registry_history_alias_conflict`,
  `039_authority_audit_trace_success`,
  `040_authority_audit_trace_fallback`, and
  `041_trace_explainability_denials`.
- Sprint 5 assertion diagnostics and validation hardening, including clearer
  count-style failure output, filter context, missing-RegistryHub diagnostics,
  and read-only assertion regression coverage.
- Documentation, scenario index, and draft release-note hardening that keeps
  scenarios `001` through `041` discoverable and gap-free.

## Simulator-Only Non-Goals

- No simulator runtime behavior changes are intended.
- No changes to alias claim, release, resolution, conflict, denial,
  quarantine, or explanation semantics.
- No persistent failed-path audit store.
- No TrafficHub routing changes.
- No canonical identity rewrite.
- No broad event store.
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

Expected version output:

```text
darwin-sim 0.7.0
```
