# DARWIN v0.6 Alias Authority Chain

This document plans the v0.6 alias authority chain behavior for DARWIN. The
Sprint 1 authority path data models, Sprint 2 authority-step evaluation
helpers, Sprint 3 explicit parent-chain traversal helper, Sprint 4
claim-through-chain helper, and Sprint 5 scenario runner support are
implemented.

The goal is to extend v0.5 progressive alias fallback from a local
RegistryHub-only decision into an explicit parent-scope negotiation path.

DARWIN means Direct-Access Registration Window Interface Network.

## Core Question

When a device behind a low-level Registry Hub requests a high-level alias:

- Which Registry Hubs evaluate the request?
- Where does approval stop?
- Which scope becomes the authority ceiling?
- If the requested alias cannot be granted, what fallback is offered?
- How is the decision chain made visible in scenarios and test assertions?

## Foundation From v0.5

v0.6 should preserve these v0.5 behaviors:

- Canonical identity chain remains truth.
- Direct aliases resolve to canonical device identity records.
- Alias claim, resolve, and release behavior remains unchanged.
- Active alias conflicts preserve the original owner and reject the duplicate.
- Released aliases remain retained but inactive.
- Quarantined or revoked devices cannot claim aliases.
- Local progressive fallback records `requested_alias`, `granted_alias`,
  `fallback_reason`, and `authority_ceiling`.
- Alias bundles and DNS-style alias bundle records remain simulator-only.
- Aliases do not affect TrafficHub routing.

## Implementation Status

Implemented in Sprint 1:

- `AliasAuthorityDecision` records one hub-local decision in a deterministic,
  JSON-safe shape.
- `AliasAuthorityPath` records ordered authority decisions for a requested
  alias without performing traversal.
- `AliasAuthorityPathSummary` provides a compact summary with requested alias,
  granted alias, final status, authority ceiling, decision count, and path
  hubs.

Implemented in Sprint 2:

- `is_alias_within_scope(...)` checks alias authority using exact scope or dot
  segment-boundary matching.
- `fallback_alias_for_scope(...)` returns the deterministic local fallback
  alias for a scope and local name.
- `can_continue_alias_upward(...)` reports whether a RegistryHub has an
  explicit parent hub ID for future traversal.
- `evaluate_alias_authority_step(...)` evaluates one RegistryHub's read-only
  decision for one alias request and returns an `AliasAuthorityDecision`.
- Authority-step helpers do not claim aliases, record conflicts, mutate
  registry state, perform traversal, or negotiate with parent hubs.

Implemented in Sprint 3:

- `evaluate_alias_authority_chain(...)` walks explicit `RegistryHub`
  `parent_hub_id` links from a start hub to parent hubs.
- The traversal helper records ordered `AliasAuthorityDecision` entries into
  an `AliasAuthorityPath`.
- Traversal stops on approval, fallback availability, insufficient authority,
  active-name conflict, policy denial, blocked device, missing start hub,
  missing parent hub, or cycle detection.
- Broken parent paths deterministically return `authority_path_broken`; the
  helper does not attempt fallback after a missing parent.
- The traversal helper is evaluation-only. It does not claim aliases, create
  `AliasRecord` instances, record conflicts, mutate parent-chain state, change
  direct alias behavior, or change progressive local fallback behavior.

Implemented in Sprint 4:

- `AliasAuthorityClaimResult` records the chain claim outcome, requested alias,
  granted alias, created alias record, authority path, and authority ceiling.
- `claim_alias_through_authority_chain(...)` evaluates the explicit parent
  authority chain before creating any alias record.
- The helper creates the requested alias only when the authority path ends in
  `approved_here`.
- The helper creates the fallback alias only when the authority path ends in
  `fallback_granted`.
- Created alias records preserve requested/granted alias provenance, fallback
  reason when applicable, approved hub, authority scope, and authority ceiling.
- Failed paths return the evaluated authority path without mutating alias
  tables or recording conflicts.
- The helper is wired into scenario actions through
  `claim_alias_through_authority_chain`.

Implemented in Sprint 5:

- Scenario DSL action `claim_alias_through_authority_chain` records structured
  action results and deterministic success/failure events.
- Assertion `alias_authority_path_summary` compares compact authority path
  summaries for success and failure paths.
- Detailed snapshots include top-level `alias_authority_claims` entries for
  authority-chain claim results.
- Scenarios `032` through `036` cover success, fallback, name conflict, policy
  denial, and broken parent traversal.
- Minimal simulator-local policy keys `allow_approval`, `allow_pass_up`, and
  `allow_fallback` make policy stops observable in scenarios.

Not implemented yet:

- Runtime changes to direct alias claims or progressive fallback.

## Proposed Authority Chain Flow

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

Possible result:

```text
final_status: fallback_granted
fallback_reason: insufficient_authority
authority_ceiling: global.us.west1.dist25.sf2.xfinity_301
approved_by_hub: xfinity_301
```

Proposed evaluation order:

1. Validate the target device exists at the requesting RegistryHub.
2. Reject quarantined or revoked target devices before path traversal.
3. Build the explicit authority path from requesting hub to parent hubs.
4. Evaluate each authority step.
5. If a hub can approve the requested alias, grant it and stop.
6. If a hub cannot approve but can continue upward, record
   `continue_upward`.
7. If a hub cannot continue or policy denies pass-up, evaluate fallback at the
   highest allowed scope.
8. If the requested or fallback alias is already active, return a conflict
   status with the relevant scope and decision step.
9. Return the full authority path, decision chain, authority ceiling, and final
   status.

## Proposed Models

Implemented Sprint 1 models:

`AliasAuthorityDecision`:

- A single decision made at one authority step.
- Records hub ID, scope path, decision code, reason, evaluated alias, fallback
  alias, authority ceiling, and whether evaluation can continue upward.

`AliasAuthorityPath`:

- Ordered path record from the requesting hub toward future parent evaluation.
- Stores decisions in append order and can produce a deterministic dictionary
  or compact summary.

`AliasAuthorityPathSummary`:

- Scenario-friendly summary of requested alias, granted alias, final status,
  authority ceiling, decision count, and path hub IDs.

Implemented Sprint 4 model:

`AliasAuthorityClaimResult`:

- Structured result for chain-aware alias claims.
- Includes success, status, reason, requested alias, granted alias, created
  alias record, authority path, and authority ceiling.

Future proposed models:

`AliasAuthorityStep`:

- One RegistryHub evaluation point in an authority chain.
- Records hub ID, scope path, parent hub ID, and local policy outcome.

`AliasDelegationPolicy`:

- Simulator-local policy for whether a hub can approve, continue upward, deny
  pass-up, or allow fallback.

`AliasChainClaimRequest`:

- Structured request for parent-chain alias claiming.
- Should not imply DNS, registrar, public CA, or production identity proof.

`AliasChainClaimResult`:

- Structured result for scenarios and tests.
- Should include the final status, granted or fallback alias, authority path,
  decision chain, authority ceiling, and approving hub when available.

## Proposed Fields

Request fields:

- `requested_alias`
- `requested_local_name`
- `target_device_id`
- `requesting_hub_id`

Result fields:

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

The implementation may also carry `granted_alias`, `conflict_id`, and the
created `AliasRecord` to stay compatible with existing claim result patterns.

## Proposed Helper Functions

Implemented Sprint 2 helper functions:

`is_alias_within_scope(alias, scope_path)`:

- Returns true only when the alias equals the scope or begins at a dot segment
  boundary under the scope.

`fallback_alias_for_scope(scope_path, local_name)`:

- Returns the deterministic local fallback alias as `scope_path.local_name`.

`can_continue_alias_upward(registry_hub)`:

- Returns true when the hub has an explicit `parent_hub_id`.

`evaluate_alias_authority_step(...)`:

- Evaluates a single hub's authority and policy decision without mutation.
- Returns `approved_here`, `continue_upward`, `fallback_available`,
  `name_taken`, `insufficient_authority`, or `device_blocked` for the local
  decision slice.
- Does not claim aliases, create `AliasRecord` instances, record conflicts,
  traverse parent hubs, or alter existing direct alias and progressive fallback
  runtime behavior.

Implemented Sprint 3 traversal helper:

`evaluate_alias_authority_chain(registry_hubs, start_hub_id, requested_alias,
local_name, target_device_id, fallback_allowed=True)`:

- Walks explicit parent RegistryHub links and records one decision per
  evaluated hub.
- Returns an `AliasAuthorityPath` with final status, granted alias when
  approval or fallback is available, authority ceiling, and decision order.
- Stops deterministically at the first terminal decision.
- Returns `authority_path_broken` for missing start hubs, missing parent hubs,
  and cycle detection.
- Does not mutate alias tables, claim aliases, create conflicts, or wire into
  scenario/runtime alias claim actions.

Implemented Sprint 4 claim helper:

`claim_alias_through_authority_chain(...)`:

- Main entry point for chain-aware progressive alias claims.
- Uses `evaluate_alias_authority_chain(...)` first.
- Calls existing direct `claim_alias(...)` only after an approved or
  fallback-granted authority path.
- Creates the alias on the hub that made the terminal approved or fallback
  decision, not necessarily the starting hub.
- Returns failure without mutation for conflicts, insufficient authority,
  blocked devices, policy denial, or broken parent paths.

Future helpers:

`find_highest_authorized_alias_scope(...)`:

- Selects the highest scope that allows approval or fallback.

`record_alias_authority_decision(...)`:

- Appends one structured decision to the decision chain.

`summarize_alias_authority_path(...)`:

- Produces scenario-friendly summary text or structured path data.

## Authority Decision Vocabulary

- `approved_here`: the hub can grant the requested alias inside its authority.
- `continue_upward`: the hub cannot grant the requested alias but can pass the
  request to its parent.
- `fallback_available`: the hub can grant a lower-scope fallback alias.
- `name_taken`: the requested or fallback alias is already active.
- `insufficient_authority`: the hub cannot grant the requested scope.
- `policy_denied`: local policy denies approval, pass-up, or fallback.
- `device_blocked`: the target device is quarantined or revoked.
- `authority_path_broken`: traversal expected a parent hub that is missing.

## Policy Rules

- Parent chain must be explicit in the simulated registry setup.
- A hub can approve aliases inside its own scope.
- A hub can pass requests upward only if it has a parent.
- A hub can deny pass-up by policy.
- A request can fall back to the highest hub that allows fallback.
- Quarantined or revoked devices cannot claim aliases through the chain.
- Existing direct v0.5 alias behavior must remain unchanged.

## Fallback Recommendation

Prefer "highest authorized scope" semantics:

- The requested alias is attempted first.
- If full approval is not available, the simulator should choose the highest
  scope reached by the chain that both allows fallback and has no active alias
  conflict.
- `authority_ceiling` should name that highest approved fallback scope.
- `fallback_reason` should explain why the requested alias was not granted.
- `decision_chain` should make the stop point auditable.

This keeps local fallback from v0.5 intact while making parent negotiation
observable.

## Scenario Design Notes

Scenario assertions should be able to check:

- The granted alias.
- The requested alias.
- The final status.
- The authority path.
- The authority ceiling.
- The approving hub.
- The fallback reason.
- A specific decision in the decision chain.
- The target device canonical identity remains unchanged.

## Implemented Sprint 5 Scenarios

- `032_alias_authority_chain_success.yaml`: request climbs to a parent that
  can approve the high-level alias.
- `033_alias_authority_chain_fallback.yaml`: request climbs until policy stops
  upward traversal and grants the highest allowed fallback.
- `034_alias_authority_chain_name_taken.yaml`: requested high-scope alias is
  already active and the conflict is reported.
- `035_alias_authority_chain_policy_denied.yaml`: a hub denies pass-up or
  approval by policy.
- `036_alias_authority_chain_broken_parent.yaml`: traversal fails because the
  configured parent chain is incomplete.

## Implemented and Proposed Tests

- Parent chain construction.
- Authority path recording.
- High-level alias approval.
- Fallback to intermediate scope.
- Conflict at requested scope.
- Conflict at fallback scope.
- Policy denial.
- Missing parent or broken authority path.
- Quarantined or revoked rejection.
- Direct v0.5 alias behavior unchanged.

## Non-Goals

v0.6 alias authority chain behavior should not add:

- Real DNS.
- Registrar integration.
- Public CA behavior.
- Production identity proof.
- Distributed consensus.
- TrafficHub routing changes.
- Canonical identity rewrite.
- Real networking.
- External registry integration.
