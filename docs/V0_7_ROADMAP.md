# DARWIN v0.7 Roadmap: Registry History, Authority Audit Trails, and Scenario Trace Explainability

DARWIN v0.7 is a planning simulator roadmap with Sprint 4 implementation now
implemented on the planning branch. The proposed theme is registry history,
authority audit trails, and scenario trace explainability.

The goal is to make existing registry and alias behavior easier to inspect
without changing simulator semantics, TrafficHub routing, canonical identity,
or the v0.6 alias authority-chain model.

## Status

Implementation status: Sprint 4 implemented on the planning branch.

Planning branch: `v0.7/planning`.

Released baseline: `darwin-sim 0.6.0` with scenarios `001` through `036`.

Version policy:

- Keep the simulator version at `0.6.0` during planning.
- Bump the version only during an explicit v0.7 release-prep step.

## Scope

v0.7 should stay simulator-first and documentation-friendly. The release
should make registry decisions easier to query, audit, and explain from tests,
scenario outputs, and compact snapshots.

In scope:

- Query helpers for registry and alias history already produced by simulator
  actions.
- Authority-chain audit trace export that makes v0.6 decisions easier to
  inspect.
- Human-readable scenario explanations for alias claim outcomes.
- Examples that teach how to read history and audit traces.
- Regression tests and documentation polish.

Out of scope:

- Real DNS.
- Registrar integration.
- Public CA behavior.
- Production identity proof.
- External services.
- Package publication during planning.
- TrafficHub routing changes.
- Canonical identity rewrite.
- Runtime refactors unrelated to history, audit trails, or explainability.

## Sprint 1: Registry History Query Helpers

Add small, read-only helpers for querying registry history from existing
simulator state.

Status: implemented for existing retained alias records, alias conflicts,
persisted alias authority grant provenance, and quarantine records. See
`docs/REGISTRY_HISTORY_QUERIES_v0_7.md`.

Candidate queries:

- Alias claims by alias, device, hub, status, and visibility.
- Alias releases and inactive alias records.
- Alias conflicts and conflict owners.
- Authority-chain decisions from v0.6 claim results.
- Quarantine, revocation, and security events relevant to alias eligibility.

Expected output should be deterministic, JSON-safe, and useful in tests and
scenario assertions.

Implemented helper-level outputs are deterministic, JSON-safe dataclass
results. Full failed authority-chain paths and broad append-only registry event
history remain deferred because RegistryHub does not currently persist them.

Non-goals:

- Do not add external storage.
- Do not add external service integration.
- Do not change how registry actions mutate state.

## Sprint 2: Authority-Chain Audit Trace Export

Make v0.6 authority decisions easier to inspect from scenario outputs while
preserving compact snapshot behavior.

Status: implemented as read-only helper-level summaries for in-memory
authority paths and retained RegistryHub authority grant provenance. See
`docs/AUTHORITY_AUDIT_TRACES_v0_7.md`.

Candidate work:

- Export ordered authority decisions for in-memory chain claim paths.
- Include requested alias, granted alias, authority ceiling, final status,
  decision count, path hubs, and policy stop reasons where retained or still
  available from the authority path.
- Keep compact helper-level summaries without changing normal snapshots.

Implemented helpers:

- `summarize_authority_decision(...)`
- `summarize_authority_path(...)`
- `build_authority_audit_trace(...)`

Current limit: failed authority-chain paths are only available from returned
claim/evaluation results. RegistryHub does not persist full failed paths after
the call, so the retained audit trace helper does not fabricate them.

Non-goals:

- Do not alter claim outcomes.
- Do not replace `alias_authority_path_summary`.
- Do not expand default snapshots into large trace dumps.

## Sprint 3: Scenario Trace Explainability

Add human-readable explanation output for why an alias claim succeeded, fell
back, conflicted, or was denied.

Status: implemented as deterministic helper-level explanations over Sprint 1
history query results and Sprint 2 authority audit trace summaries. See
`docs/TRACE_EXPLAINABILITY_v0_7.md`.

Candidate explanations:

- Requested alias approved by an authority hub.
- Requested alias fell back to the highest allowed scope.
- Requested alias conflicted with an active alias.
- Claim denied by simulator-local policy.
- Claim denied because the target device was quarantined or revoked.
- Claim failed because the authority parent path was broken.

The explanation layer should be derived from structured results and events. It
should not become a second source of truth.

Implemented helpers:

- `explain_authority_trace(...)`
- `explain_authority_traces(...)`
- `explain_alias_history_entry(...)`
- `explain_alias_conflict_entry(...)`
- `explain_quarantine_event_entry(...)`

Current limit: RegistryHub still does not persist full failed authority-chain
paths. Failed authority outcomes can be explained when the caller still has the
in-memory `AliasAuthorityPath` summary; retained RegistryHub grant traces can
explain stored approved and fallback grants.

## Sprint 4: Scenario DSL Assertions and Examples

Add read-only scenario assertions and examples that teach how to read registry
history, authority audit traces, and explanation output.

Status: implemented on the planning branch as scenario assertions and
scenarios `037` through `041`. The assertions are documented in
`docs/SCENARIO_DSL_v0_2.md`.

Implemented assertions:

- `alias_history_contains`
- `alias_conflict_history_contains`
- `authority_audit_trace_contains`
- `quarantine_history_contains`

Implemented scenarios:

- `037_registry_history_alias_claim`
- `038_registry_history_alias_conflict`
- `039_authority_audit_trace_success`
- `040_authority_audit_trace_fallback`
- `041_trace_explainability_denials`

These assertions use existing read-only helper outputs. They do not add new
scenario actions, change simulator runtime behavior, alter aliases, change
TrafficHub routing, rewrite canonical identity, or persist failed
authority-chain paths.

Candidate docs and scenarios:

- A focused guide for interpreting alias history records.
- A focused guide for interpreting authority-chain audit traces.
- Example scenario output snippets for success, fallback, conflict, policy
  denial, and broken parent paths.
- Scenario documentation that keeps scenarios `001` through `036` as the
  released v0.6 baseline while v0.7 planning scenarios begin at `037`.

Non-goals:

- Do not claim v0.7 behavior is released before release prep.
- Do not document real DNS, registrar, public CA, or production identity
  behavior as implemented.

## Sprint 5: Hardening and Release Prep

Harden the v0.7 slices once implementation exists.

Release-prep candidates:

- Regression tests for history query helpers.
- Regression tests for audit trace export shape.
- Regression tests for explanation text stability where text is public-facing.
- Scenario runner coverage for any new v0.7 scenarios.
- Docs polish across README, changelog, scenario DSL, and release notes.
- Version bump only at explicit release-prep time.

Validation target:

```bash
python -m ruff check .
python -m pytest
python scripts/run_all_scenarios.py
python -m darwin.cli.main --version
```

During planning, the expected version remains:

```text
darwin-sim 0.6.0
```

## Recommended First Implementation Sprint

Start with Sprint 1. Read-only registry history query helpers create a small,
safe foundation for audit trace export and human-readable explanations without
changing simulator behavior.
