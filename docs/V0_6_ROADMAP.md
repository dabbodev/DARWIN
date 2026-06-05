# DARWIN v0.6 Roadmap: Alias Authority Chain Planning

DARWIN v0.6 is planned as a simulator-only alias authority negotiation
release. It extends the v0.5 progressive alias model from local-only fallback
to explicit parent-scope authority traversal between simulated Registry Hubs.

v0.6 should answer this simulator question:

```text
When a device behind a low-level Registry Hub requests a high-level alias, how
does the request climb upward, where does approval stop, and how is fallback
documented?
```

This roadmap tracks v0.6 alias authority-chain work. Sprint 1 data models,
Sprint 2 authority-step evaluation helpers, the Sprint 3 explicit parent-chain
traversal helper, the Sprint 4 claim-through-chain helper, and Sprint 5
scenario runner support are implemented on the feature branch. v0.6 remains
unreleased draft work; the current stable package remains `darwin-sim 0.5.0`.

## Status

Completed:

- Sprint 1 authority path data models:
  - `AliasAuthorityDecision`
  - `AliasAuthorityPath`
  - `AliasAuthorityPathSummary`
- Deterministic, JSON-safe dictionary helpers for authority path records.
- Unit coverage for authority path model serialization, ordering, summaries,
  and direct alias claim compatibility.
- Sprint 2 authority-step evaluation helper slice:
  - `is_alias_within_scope`
  - `fallback_alias_for_scope`
  - `can_continue_alias_upward`
  - `evaluate_alias_authority_step`
- Unit coverage for single-hub approval, upward continuation, fallback,
  insufficient authority, device blocking, active-name conflicts, and
  no-mutation behavior.
- Sprint 3 parent-chain traversal helper slice:
  - `evaluate_alias_authority_chain`
- Unit coverage for missing starts, start-hub approval, parent approval,
  root fallback, no-fallback rejection, broken parent paths, active-name
  conflicts, blocked devices, no-mutation behavior, and path summaries.
- Sprint 4 claim-through-chain helper slice:
  - `AliasAuthorityClaimResult`
  - `claim_alias_through_authority_chain`
- Unit coverage for parent-approved alias creation, fallback alias creation,
  conflict failure without overwrite, insufficient authority without fallback,
  broken parent failure, blocked device failure, authority path recording, and
  no-mutation failure behavior.
- Sprint 5 scenario runner support:
  - `claim_alias_through_authority_chain` action
  - `alias_authority_path_summary` assertion
  - compact `alias_authority_claims` detailed snapshot entries
  - scenarios `032` through `036`

Current hardening target:

- Keep alias authority-chain behavior simulator-only.
- Preserve v0.5 direct alias behavior.
- Preserve progressive local fallback behavior outside authority-chain claims.
- Preserve canonical identity truth.
- Preserve TrafficHub routing behavior.
- Polish draft docs, scenario discoverability, and regression coverage.

Not part of this feature-branch work:

- Version bump.
- Release, tag, or merge.
- Real DNS, registrar integration, public CA behavior, production identity
  proof, external services, TrafficHub routing changes, or canonical identity
  rewrites.

## Current v0.5 Foundation

v0.5 provides the foundation v0.6 should build on:

- Canonical identity chains remain the truthful identity source.
- Direct aliases can be claimed, resolved, and released.
- Duplicate active aliases are rejected through explicit conflict behavior.
- Released aliases are retained but do not resolve as active aliases.
- Quarantined and revoked devices cannot claim active aliases.
- Progressive alias fallback grants the highest locally authorized alias when
  the requesting RegistryHub lacks authority for the requested high-scope
  alias.
- Alias bundle records model delegated simulator namespaces.
- DNS-style alias bundle scenarios remain simulator-only naming records.
- Aliases do not affect TrafficHub routing, packet paths, attachments,
  passports, or canonical identity chains.

## Proposed v0.6 Scope

v0.6 should extend progressive aliases so a RegistryHub can evaluate an alias
claim through an explicit parent authority chain.

Proposed behavior:

- Alias claim requests can traverse parent Registry Hubs.
- Each RegistryHub in the path decides whether to approve, reject, continue
  upward, or offer fallback.
- The highest approved alias is granted.
- If the requested alias is unavailable or unauthorized, a fallback may be
  granted at the highest allowed scope.
- Every result records the authority path and the authority ceiling.

Current implementation slice:

- Authority path records can be constructed, appended, summarized, and
  serialized.
- One RegistryHub can be evaluated for one alias request through read-only
  authority-step helpers.
- Explicit parent RegistryHub links can be traversed through
  `evaluate_alias_authority_chain(...)`, producing an ordered
  `AliasAuthorityPath`.
- `claim_alias_through_authority_chain(...)` creates the requested alias only
  after `approved_here`, creates fallback aliases only after
  `fallback_granted`, and returns the full authority path in all outcomes.
- Failed chain claims do not mutate alias tables or record alias conflicts.
- Existing direct alias and progressive fallback behavior remains unchanged.
- Scenario runner support and scenarios `032` through `036` are implemented as
  unreleased draft behavior on the feature branch.

Example canonical identity:

```text
global.us.west1.dist25.sf2.xfinity_301.node53.david_router.project_server
```

Requested alias:

```text
global.david_server
```

Possible authority path:

```text
david_router -> node53 -> xfinity_301 -> sf2 -> dist25 -> west1 -> us -> global
```

Possible granted alias:

```text
global.us.west1.dist25.sf2.xfinity_301.david_server
```

Result:

```text
status: fallback_granted
authority_ceiling: global.us.west1.dist25.sf2.xfinity_301
```

## Proposed Models

The following names are planned for v0.6. They remain simulator data models and
should not imply DNS, registrar, public CA, or production identity-proof
behavior.

- Complete: `AliasAuthorityDecision`
- Complete: `AliasAuthorityPath`
- Complete: `AliasAuthorityPathSummary`
- Complete: `AliasAuthorityClaimResult`
- Future: `AliasAuthorityStep`
- Future: `AliasDelegationPolicy`
- Future: `AliasChainClaimRequest`

## Proposed Fields

`AliasChainClaimRequest` should carry:

- `requested_alias`
- `requested_local_name`
- `target_device_id`
- `requesting_hub_id`

`AliasChainClaimResult` should carry:

- `requested_alias`
- `requested_local_name`
- `target_device_id`
- `requesting_hub_id`
- `authority_path`
- `approved_by_hub`
- `authority_ceiling`
- `fallback_alias`
- `fallback_reason`
- `decision_chain`
- `final_status`

The result should also expose the granted alias through the existing alias
claim result pattern when an active alias is created.

## Proposed Helpers

Completed helper slice:

- `is_alias_within_scope(...)`
- `fallback_alias_for_scope(...)`
- `can_continue_alias_upward(...)`
- `evaluate_alias_authority_step(...)`
- `evaluate_alias_authority_chain(...)`
- `claim_alias_through_authority_chain(...)`

Completed scenario slice:

- Scenario runner action support for chain claims.
- Scenarios `032` through `036`.

Future helper candidates:

- `find_highest_authorized_alias_scope(...)`
- `record_alias_authority_decision(...)`
- `summarize_alias_authority_path(...)`

Helper names should stay registry-oriented and avoid terms that suggest real
DNS servers, domain registrars, certificate authorities, or production
verification.

## Authority Decisions

Proposed decision/status vocabulary:

- `approved_here`
- `continue_upward`
- `fallback_available`
- `name_taken`
- `insufficient_authority`
- `policy_denied`
- `device_blocked`
- `authority_path_broken`

The decision chain should record each evaluated hub and the decision reached
there. Normal policy outcomes should be returned as structured results rather
than raised as exceptions.

## Simulator Policy Rules

Proposed v0.6 rules:

- Parent chain must be explicit in the simulated registry setup.
- A hub can approve aliases inside its own scope.
- A hub can pass requests upward only if it has a parent.
- A hub can deny pass-up by policy.
- A request can fall back to the highest hub that allows fallback.
- Quarantined or revoked devices cannot claim aliases through the chain.
- Existing direct v0.5 alias behavior must remain unchanged.
- `alias_authority_policy` is simulator-local helper policy only. It is not
  registrar policy, DNS policy, CA policy, production identity proof, or an
  external authority service.
- Empty policy preserves default authority-chain helper behavior.

## Implemented Sprint 5 Scenarios

- `032_alias_authority_chain_success.yaml`
- `033_alias_authority_chain_fallback.yaml`
- `034_alias_authority_chain_name_taken.yaml`
- `035_alias_authority_chain_policy_denied.yaml`
- `036_alias_authority_chain_broken_parent.yaml`

Sprint 5 wires `claim_alias_through_authority_chain` into the scenario runner,
adds compact `alias_authority_path_summary` assertions, records authority-chain
claim summaries in detailed snapshots, and adds simulator-local policy keys for
approval, pass-up, and fallback gates.

## Implemented and Proposed Tests

- Parent chain construction.
- Authority path recording.
- High-level alias approval.
- Fallback to intermediate scope.
- Conflict at requested scope.
- Conflict at fallback scope.
- Policy denial.
- Missing parent or broken authority path.
- Quarantined or revoked device rejection.
- Direct v0.5 alias behavior unchanged.

## Compatibility

v0.6 should not change:

- Canonical identity chain truth.
- Direct alias claim, resolve, release, conflict, and inactive-release
  behavior.
- v0.5 progressive local fallback behavior except where it is explicitly used
  as the fallback case under the new chain workflow.
- Alias bundle records.
- TrafficHub routing and Logical Lane behavior.

## Non-Goals

v0.6 planning does not include:

- Real DNS.
- Registrar integration.
- Public CA behavior.
- Production identity proof.
- Distributed consensus.
- TrafficHub routing changes.
- Canonical identity rewrite.
- Real networking.
- External registry integration.

## Release Validation

Planning validation should confirm the existing stable simulator remains
unchanged:

```bash
python -m ruff check .
python -m pytest
python scripts/run_all_scenarios.py
python -m darwin.cli.main --version
```

Expected CLI version during planning:

```text
darwin-sim 0.5.0
```
