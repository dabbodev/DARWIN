# DARWIN v0.8 Roadmap: Persistent Simulator Audit Retention and Failed-Path Provenance

DARWIN v0.8 is planning-only and not implemented yet. The proposed theme is
persistent simulator audit retention and failed-path provenance.

v0.8 should remain simulator-first. It should make authority-chain outcomes
easier to inspect after scenario actions complete without becoming a production
audit, compliance, identity-proof, DNS, registrar, public CA, or external
service system.

## Status

Implementation status: not implemented.

Planning branch: `v0.8/planning`.

Starting released baseline: `darwin-sim 0.7.0` on `main`, with released
scenarios `001` through `041`.

Version policy:

- Keep the current version at `darwin-sim 0.7.0` during planning and early
  implementation.
- Bump only during v0.8 release prep.

## Scope

In scope:

- Compact persistent simulator records for successful and failed
  authority-chain outcomes.
- Read-only query helpers for retained failed-path provenance.
- Scenario assertions that prove denied, conflicted, and broken-parent
  authority outcomes remain explainable after action execution.
- Snapshot or export visibility if current repository conventions support it
  cleanly.
- Documentation that distinguishes retained provenance from in-memory
  `AliasAuthorityPath` data.

Out of scope:

- Real DNS.
- Registrar integration.
- Public CA behavior.
- Production identity proof.
- External services.
- Production audit or compliance behavior.
- Broad event stores.
- TrafficHub routing changes.
- Canonical identity rewrites.
- Runtime refactors unrelated to compact audit retention.
- Package publication before release prep.

## Sprint 1: Minimal Persistent Authority Outcome Records

Retain compact failed and successful authority-chain outcome summaries on
`RegistryHub`.

Candidate work:

- Add a small simulator-local retained outcome record for authority-chain
  attempts.
- Store requested alias, granted alias when present, target device, final
  status, reason, authority ceiling, path hubs, decision count, and compact
  decision summaries.
- Preserve existing in-memory `AliasAuthorityPath` behavior and action result
  shape.
- Keep retained records deterministic and JSON-safe.

Non-goals:

- Do not add a broad event store.
- Do not persist production audit records.
- Do not change alias claim semantics.

## Sprint 2: Failed-Path Query Helpers

Extend read-only history queries to include persisted failed authority
outcomes.

Candidate work:

- Add query helpers for retained authority outcomes by requested alias, granted
  alias, target device, final status, reason, hub, and outcome type.
- Keep deterministic ordering and JSON-safe dataclass results.
- Preserve v0.7 query helper behavior for retained alias records, conflicts,
  authority grant provenance, and quarantine records.

Non-goals:

- Do not require external storage.
- Do not mutate state from query helpers.
- Do not treat retained simulator summaries as compliance logs.

## Sprint 3: Scenario Assertions for Persisted Failed-Path Provenance

Add scenario assertions proving failed authority outcomes remain explainable
after action execution.

Candidate work:

- Add focused assertions for retained denied, conflict, and broken-parent
  authority outcomes.
- Cover policy denial, name conflict, broken parent, and fallback visibility
  with new scenarios or tightly scoped additions.
- Prove retained summaries are sufficient for deterministic explanation after
  the original action result has completed.

Non-goals:

- Do not alter existing v0.7 scenario semantics.
- Do not change TrafficHub routing, alias resolution, or canonical identity.
- Do not require golden-file churn unless already conventional.

## Sprint 4: Snapshot and Export Visibility

Add compact persisted audit retention visibility to snapshots or exports if
current repository conventions support it.

Candidate work:

- Add compact retained authority outcome visibility to detailed snapshots or
  explicit export paths.
- Keep default output small and deterministic.
- Include only JSON-safe summaries.
- Avoid golden-file churn unless snapshot or export conventions already expect
  the new data.

Non-goals:

- Do not add broad trace dumps to default snapshots.
- Do not introduce external export services.
- Do not imply production audit retention.

## Sprint 5: Documentation, Hardening, and Release Prep

Clarify retained versus in-memory provenance and prepare the release only after
implementation is complete.

Candidate work:

- Update docs to distinguish persisted simulator outcome summaries from
  in-memory `AliasAuthorityPath` data.
- Add regression tests for query ordering, JSON safety, assertion diagnostics,
  and scenario index coverage.
- Polish scenario docs and release-facing notes.
- Run Ruff, pytest, all scenarios, scenario index checks, and CLI version
  validation.
- Bump version only during release prep.

Non-goals:

- Do not tag, publish, or create a release during planning.
- Do not claim production audit/compliance guarantees.
- Do not add real DNS, registrar, CA, or production identity behavior.

## Recommended First Implementation Sprint

Start with Sprint 1. Minimal retained authority outcome records create the
smallest useful foundation for failed-path provenance while preserving v0.7
in-memory authority path behavior and existing scenario semantics.

## Deferred Work

- Production audit or compliance behavior.
- External storage, services, registrar integrations, public CA behavior, and
  real DNS.
- TrafficHub routing changes.
- Canonical identity model changes.
- Package publication, tagging, and release creation.
