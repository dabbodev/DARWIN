# DARWIN Simulator v0.6.0 Release Notes

These notes describe the published v0.6.0 release on `main`. The annotated
`v0.6.0` tag exists and the GitHub release has been published. No package
publication was performed. The file keeps the `_DRAFT` suffix for existing
repository links and release-readiness tests.

DARWIN means Direct-Access Registration Window Interface Network.

## Theme

v0.6 is a simulator-only alias authority chain release. It extends the v0.5
progressive alias fallback model from local RegistryHub authority to explicit
parent-scope authority traversal.

The core simulator behavior is:

```text
A low-level RegistryHub can request a high-level alias through its explicit
parent chain, record each authority decision, and grant either the requested
alias or the highest allowed fallback alias.
```

## Added

- Alias authority path data models:
  - `AliasAuthorityDecision`
  - `AliasAuthorityPath`
  - `AliasAuthorityPathSummary`
- Authority-step evaluation helpers:
  - `is_alias_within_scope(...)`
  - `fallback_alias_for_scope(...)`
  - `can_continue_alias_upward(...)`
  - `evaluate_alias_authority_step(...)`
- Parent-chain traversal through
  `evaluate_alias_authority_chain(...)`.
- Chain-aware claim result model and helper:
  - `AliasAuthorityClaimResult`
  - `claim_alias_through_authority_chain(...)`
- Scenario runner action support for
  `claim_alias_through_authority_chain`.
- Scenario assertion support through `alias_authority_path_summary`.
- Detailed snapshot visibility for authority-chain claims through compact
  `alias_authority_claims` entries.
- Event payload visibility for authority-chain success and failure paths,
  including requested alias, granted alias, authority ceiling, final path
  status, decision count, path hubs, and JSON-safe authority decisions.
- Simulator-local `alias_authority_policy` gates for approval, pass-up, and
  fallback behavior.
- Authority-chain scenarios `032` through `036`:
  - `scenarios/032_alias_authority_chain_success.yaml`
  - `scenarios/033_alias_authority_chain_fallback.yaml`
  - `scenarios/034_alias_authority_chain_name_taken.yaml`
  - `scenarios/035_alias_authority_chain_policy_denied.yaml`
  - `scenarios/036_alias_authority_chain_broken_parent.yaml`

## Behavior

- Authority-chain requests traverse explicit `RegistryHub.parent_hub_id`
  links from the requesting hub toward parent hubs.
- Each evaluated hub records a deterministic authority decision.
- A hub can approve an alias inside its scope, pass the request upward, offer
  fallback, deny by policy, report a conflict, block a quarantined or revoked
  device, or expose a broken parent path.
- Successful high-scope claims create the requested alias only after an
  `approved_here` authority path.
- Successful fallback claims create the fallback alias only after a
  `fallback_granted` authority path.
- Failed chain claims return their evaluated authority path without mutating
  alias tables or recording alias conflicts.
- Direct v0.5 alias helpers and local progressive fallback behavior remain
  unchanged outside the authority-chain workflow.

## Regression and Docs Hardening

Sprint 6 hardened release-facing behavior and documentation:

- Scenario discoverability confirms scenarios `032` through `036` are listed
  and tagged consistently.
- Event payload regression tests cover authority-chain success and failure
  data.
- Snapshot regression tests cover compact authority-chain claim summaries.
- Simulator-local policy tests cover empty policy defaults and approval,
  pass-up, and fallback gates.
- Failed-claim safety tests confirm rejected authority-chain claims do not
  create aliases or conflict records.
- Docs distinguish implemented simulator behavior from release operations and
  record that package publication was not performed for v0.6.0.

## Compatibility

v0.6 preserves:

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

v0.6 does not include:

- Real DNS.
- Registrar integration.
- Public CA behavior.
- Production identity proof.
- External services.
- TrafficHub routing changes.
- Canonical identity rewrite.
- DNS replacement behavior.
- Distributed consensus.
- Real networking or real network lookup.
- Production cryptography.
- External registry integration.

`alias_authority_policy` is simulator-local helper policy only. It is not
registrar policy, DNS policy, CA policy, production identity proof, or an
external authority service.

## Release Validation

Final release validation passed on `main`:

```bash
python -m ruff check .
python -m pytest
python scripts/run_all_scenarios.py
python -m darwin.cli.main --version
```

Expected CLI version:

```text
darwin-sim 0.6.0
```

The released scenario set is scenarios `001` through `036`.
