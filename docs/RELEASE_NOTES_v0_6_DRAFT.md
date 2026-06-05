# DARWIN Simulator v0.6.0 Draft Release Notes

These are draft notes for a future v0.6 release. v0.6 authority-chain work is
unreleased feature-branch behavior, not a released simulator version. The
current stable simulator version remains `darwin-sim 0.5.0`.

DARWIN means Direct-Access Registration Window Interface Network.

## Planned Theme

v0.6 is planned as a simulator-only alias authority chain release. It should
extend v0.5 progressive alias fallback from local RegistryHub authority to
explicit parent-scope authority negotiation.

The core behavior to model:

```text
A low-level RegistryHub can request a high-level alias through its explicit
parent chain, record each authority decision, and grant either the requested
alias or the highest allowed fallback alias.
```

## Draft Additions

- Alias claim requests that can traverse parent Registry Hubs.
- Authority path recording for chain-aware alias claims.
- Authority ceiling recording for successful fallback claims.
- Per-hub decisions to approve, reject, continue upward, or offer fallback.
- Structured decision chains for scenario assertions.
- Highest-approved alias selection.
- Highest-allowed fallback alias selection when the requested alias is
  unavailable or unauthorized.

## Feature-Branch Draft State

- Sprint 1 added authority path models:
  - `AliasAuthorityDecision`
  - `AliasAuthorityPath`
  - `AliasAuthorityPathSummary`
- Sprint 2 added authority evaluation helpers:
  - `is_alias_within_scope(...)`
  - `fallback_alias_for_scope(...)`
  - `can_continue_alias_upward(...)`
  - `evaluate_alias_authority_step(...)`
- Sprint 3 added explicit parent-chain traversal through
  `evaluate_alias_authority_chain(...)`.
- Sprint 4 added `AliasAuthorityClaimResult` and
  `claim_alias_through_authority_chain(...)`.
- Sprint 5 added scenario runner support:
  - `claim_alias_through_authority_chain` action
  - `alias_authority_path_summary` assertion
  - compact `alias_authority_claims` detailed snapshot entries
  - simulator-local `alias_authority_policy` gates
  - scenarios `032` through `036`
- Sprint 6 hardens draft docs, scenario discoverability, event/snapshot
  regression checks, and simulator-local policy coverage.

## Draft Models

- `AliasAuthorityPath`
- `AliasAuthorityPathSummary`
- `AliasAuthorityDecision`
- `AliasAuthorityClaimResult`

## Draft Helpers

- `claim_alias_through_authority_chain(...)`
- `evaluate_alias_authority_step(...)`
- `evaluate_alias_authority_chain(...)`
- `is_alias_within_scope(...)`
- `fallback_alias_for_scope(...)`
- `can_continue_alias_upward(...)`

## Proposed Decision Statuses

- `approved_here`
- `continue_upward`
- `fallback_available`
- `name_taken`
- `insufficient_authority`
- `policy_denied`
- `device_blocked`
- `authority_path_broken`

## Draft Scenario Coverage

- `scenarios/032_alias_authority_chain_success.yaml`
- `scenarios/033_alias_authority_chain_fallback.yaml`
- `scenarios/034_alias_authority_chain_name_taken.yaml`
- `scenarios/035_alias_authority_chain_policy_denied.yaml`
- `scenarios/036_alias_authority_chain_broken_parent.yaml`

## Planned Compatibility

v0.6 should preserve:

- Canonical identity chains as authoritative identity truth.
- Direct v0.5 alias claim, resolve, release, conflict, and inactive-release
  behavior.
- Existing local progressive fallback semantics where no parent-chain claim is
  used.
- Alias bundle records and DNS-style simulator-only bundle behavior.
- TrafficHub routing behavior.
- Symbolic simulator proof posture.
- Canonical identity chains as truthful records; aliases are authorized
  shortcuts only.

## Explicit Limits

v0.6 planning does not include:

- Real DNS.
- DNS replacement behavior.
- Domain registrar integration.
- Public CA behavior.
- Production identity proof.
- Distributed consensus.
- Real networking or real network lookup.
- Production cryptography.
- External registry integration.
- TrafficHub routing changes.
- Canonical identity replacement.
- Public release, tag, merge, or version bump.

`alias_authority_policy` is simulator-local helper policy only. It is not
registrar policy, DNS policy, CA policy, production identity proof, or an
external authority service.

## Planning Validation

During this planning pass, validation should confirm the stable simulator has
not changed:

```bash
python -m ruff check .
python -m pytest
python scripts/run_all_scenarios.py
python -m darwin.cli.main --version
```

Expected CLI version:

```text
darwin-sim 0.5.0
```
