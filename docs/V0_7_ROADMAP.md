# DARWIN v0.7 Roadmap: Registry History, Authority Audit Trails, and Scenario Trace Explainability

DARWIN v0.7 is a planning simulator roadmap with Sprint 1 implementation now
in progress on the planning branch. The proposed theme is registry history,
authority audit trails, and scenario trace explainability.

The goal is to make existing registry and alias behavior easier to inspect
without changing simulator semantics, TrafficHub routing, canonical identity,
or the v0.6 alias authority-chain model.

## Status

Implementation status: Sprint 1 implemented on the planning branch.

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

Candidate work:

- Export ordered authority decisions for each chain claim.
- Include requested alias, granted alias, authority ceiling, final status,
  decision count, path hubs, and policy stop reasons.
- Keep compact summaries in normal snapshots.
- Add optional detailed export paths only where existing export patterns make
  sense.

Non-goals:

- Do not alter claim outcomes.
- Do not replace `alias_authority_path_summary`.
- Do not expand default snapshots into large trace dumps.

## Sprint 3: Scenario Trace Explainability

Add human-readable explanation output for why an alias claim succeeded, fell
back, conflicted, or was denied.

Candidate explanations:

- Requested alias approved by an authority hub.
- Requested alias fell back to the highest allowed scope.
- Requested alias conflicted with an active alias.
- Claim denied by simulator-local policy.
- Claim denied because the target device was quarantined or revoked.
- Claim failed because the authority parent path was broken.

The explanation layer should be derived from structured results and events. It
should not become a second source of truth.

## Sprint 4: Documentation and Scenario Examples

Add examples that teach how to read registry history, authority audit traces,
and explanation output.

Candidate docs and scenarios:

- A focused guide for interpreting alias history records.
- A focused guide for interpreting authority-chain audit traces.
- Example scenario output snippets for success, fallback, conflict, policy
  denial, and broken parent paths.
- Scenario documentation that keeps scenarios `001` through `036` as the
  released v0.6 baseline until v0.7 scenarios are intentionally added.

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
