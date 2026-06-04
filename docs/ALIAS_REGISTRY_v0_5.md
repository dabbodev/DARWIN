# DARWIN v0.5 Alias Registry

This document describes the implemented v0.5 Registry Hub alias model. Direct
alias helpers, basic progressive alias fallback, minimal alias bundles, and a
DNS-style public alias bundle scenario are implemented. DNS-style naming
remains simulator-only; real DNS integration is not implemented.

Aliases are authorized shortcuts. They do not replace canonical identity
chains, alter traffic paths, or integrate with real DNS.

## Helper Slice Status

Implemented in v0.5:

- Basic `AliasRecord` and direct alias result models.
- Registry Hub in-memory alias storage.
- `claim_alias(...)` for direct aliases targeting registered devices.
- `resolve_alias(...)` for active direct aliases.
- `release_alias(...)` preserving a released alias record.
- `claim_progressive_alias(...)` for authority-limited fallback claims.
- `suggest_alias_fallbacks(...)` and `highest_authorized_alias(...)` for the
  current local-authority fallback model.
- Basic `AliasBundle`, `AliasBundleClaimResult`, and
  `BundleAliasClaimResult` models.
- Registry Hub in-memory alias bundle storage.
- `create_alias_bundle(...)` for simulator-local delegated namespaces inside a
  RegistryHub authority scope.
- `claim_bundle_alias(...)` for child device aliases inside active bundles.
- `bundle_type`, `visibility`, and `allowed_record_types` storage for bundle
  records, including simulator-only DNS-style bundle metadata.
- Active alias conflict detection using the existing registry conflict table.
- Active bundle conflict detection for duplicate active bundle paths.
- Alias claim rejection for quarantined or revoked target devices.
- Scenario runner support for direct alias claim, progressive alias claim,
  bundle creation, child bundle alias claim, resolve, and release steps.
- Scenario assertions for alias resolution, alias status, inactive alias
  resolution, bundle status, child bundle alias resolution, granted alias
  provenance, authority ceiling, and canonical identity preservation.
- `scenarios/026_alias_claim_success.yaml` covering direct device alias claim
  and resolution.
- `scenarios/027_alias_claim_conflict.yaml` covering direct alias conflicts
  while preserving the original active owner.
- `scenarios/028_alias_release_blocks_resolution.yaml` covering release to an
  inactive retained alias record that no longer resolves.
- `scenarios/029_progressive_alias_fallback.yaml` covering a high-level alias
  request that falls back to the RegistryHub-authorized scope.
- `scenarios/030_alias_bundle_delegation.yaml` covering a delegated alias
  bundle with an active child alias.
- `scenarios/031_dns_style_alias_bundle.yaml` covering a public-style alias
  bundle with child aliases that resolve to registered device identities.

Not implemented yet:

- Parent-chain progressive alias negotiation.
- Real DNS integration.
- Domain registrar integration.
- Public CA modeling.
- Production identity proof for public aliases.
- Real network lookup.
- Service alias behavior beyond reserved model fields.
- Production cryptography or external proof flows for alias claims.

Alias helpers do not mutate device labels, passport IDs, attachments, canonical
identity chains, or TrafficHub routing state.

Scenario runner alias support calls the alias helper functions and records
structured step results for scenario assertions, but it does not add DNS-style
lookup, service alias behavior, TrafficHub routing changes, or canonical
identity rewrites.

## Design Goal

A device keeps its canonical identity chain but can request a shorter alias at
a higher registry scope when authorization and namespace policy allow it.

Example canonical identity:

```text
global.us.west1.dist25.sf2.xfinity_301.node53.david_router.project_server
```

Requested alias:

```text
global.david_server
```

Fallback alias:

```text
global.us.west1.dist25.sf2.xfinity_301.david_server
```

## Naming Boundaries

`canonical_identity_chain`:

- Truthful scoped identity path.
- Stable identity source for the simulator.
- Not shortened or replaced by alias claims.

`alias` or `short_handle`:

- Authorized shortcut that resolves to a device identity or service.
- May be scoped at a higher or lower registry level depending on authority.

`alias_bundle` or `alias_zone`:

- Delegated namespace containing many aliases.
- May be public-style or private policy-controlled.

`traffic_path`:

- Current route or attachment path.
- Remains separate from registry naming and alias resolution.

## Alias Types

Device alias:

- Resolves to a device ID and canonical identity chain.
- Should remain valid across relocation if the canonical identity remains
  valid.

Service alias:

- Resolves to a service ID, optionally with a target device ID and identity
  chain.
- Useful for modeling a project, API, website, or other logical service.

Progressive alias:

- A claim flow where a requested alias is tried first and a fallback alias may
  be granted.
- The resulting record is still an `AliasRecord`.

Alias bundle or zone:

- A delegated namespace root that can issue child aliases under its authority.

DNS-style public alias bundle:

- A simulator-only public naming zone.
- Intended to model public lookup policy without real DNS, registrars, public
  CA checks, production verification, or real network lookup.

## AliasRecord

Implemented fields:

- `alias`
- `alias_type`
- `target_device_id` optional
- `target_service_id` optional
- `target_identity_chain`
- `requested_by_device_id`
- `requested_through_hub`
- `approved_by_registry_hub`
- `authority_scope`
- `status`
- `visibility`
- `ttl` optional
- `conflict_id`
- `requested_alias`
- `granted_alias`
- `fallback_reason`
- `authority_ceiling`
- `fallback_from`

Future or reserved fields that are not implemented in v0.5:

- `authority_path`
- `conflict_status`
- `auth_mode`
- `proof_mode`

Suggested statuses:

- `active`
- `pending`
- `fallback_granted`
- `rejected`
- `conflict`
- `expired`
- `released`
- `revoked`

Suggested conflict statuses:

- `none`
- `name_taken`
- `reserved_name`
- `scope_conflict`
- `bundle_conflict`

Suggested visibility values:

- `private`
- `scope_local`
- `delegated_bundle`
- `public_simulated`

The default proof posture is symbolic. Any future alias proof data should model
simulator authorization behavior only.

## Claim Results

`AliasClaimResult` captures:

- `success`
- `status`
- `reason`
- `alias_record`
- `conflict_id`

`ProgressiveAliasClaimResult` captures requested alias, granted alias,
fallback reason, authority ceiling, and conflict details. Bundle helpers return
`AliasBundleClaimResult` and `BundleAliasClaimResult`.

`AliasClaimRequest` is not implemented in v0.5. If introduced later, it should
remain a simulator-local request DTO and should not imply registrar, DNS,
public CA, or production identity-proof behavior.

## Progressive Alias Fallback

The implemented basic progressive alias claim evaluates the requested alias
against the approving RegistryHub authority before proposing local fallbacks.

Example:

```text
requested: global.david_server
granted: global.us.west1.dist25.sf2.xfinity_301.david_server
status: fallback_granted
reason: insufficient_authority
```

Fallback also fails cleanly if the fallback alias is already active:

```text
reason: alias_conflict
```

Current implemented ordering:

1. Validate the target device exists.
2. Reject quarantined or revoked target devices.
3. If the requested alias is inside the RegistryHub authority scope, claim it
   directly.
4. If the requested alias is above the RegistryHub authority scope and fallback
   is allowed, grant `registry_hub.scope_path + "." + local_name`.
5. If fallback is disabled, reject with `insufficient_authority`.
6. If the fallback alias is already active, fail with `alias_conflict`.
7. Return explicit requested alias, granted alias, fallback reason, and
   authority ceiling.

Fallback must preserve the authority ceiling. A lower Registry Hub should not
grant an alias above its approved scope just because the fallback flow was
requested.

Parent-chain negotiation is not implemented in this slice.

## Authority Rules

- Registry Hubs grant aliases only inside their authority scope.
- Parent registries may approve aliases at higher scopes.
- Upward requests require policy permission.
- Quarantined devices cannot create active aliases.
- Revoked devices cannot create active aliases.
- Conflict detection is explicit and scenario-visible.
- Alias resolution never rewrites canonical identity truth.
- Alias release affects alias records, not device identity records.

## Alias Bundles

`AliasBundle` models delegated namespaces in the simulator registry only.

Example:

```text
bundle: global.us.gov.ca
delegated_to: registry_ca_gov
approved_by: registry_us_gov
```

Child aliases:

```text
global.us.gov.ca.website
global.us.gov.ca.dmv
global.us.gov.ca.tax
```

Implemented bundle fields:

- `bundle_path`
- `bundle_type`
- `delegated_to_registry_hub`
- `approved_by_registry_hub`
- `authority_scope`
- `status`
- `visibility`
- `allowed_record_types`
- `policy`
- `created_by_device_id`

`create_alias_bundle(...)` succeeds only when the bundle path is equal to or
inside the approving RegistryHub `scope_path`. This slice does not negotiate
with parent registries. Creating the same active bundle twice fails with
`bundle_conflict` and leaves the original bundle unchanged.

`claim_bundle_alias(...)` composes the full child alias as
`bundle_path + "." + child_name`, validates that the bundle exists and is
active, then creates a normal `AliasRecord`. Child bundle aliases therefore
resolve through the existing `resolve_alias(...)` helper. Missing bundles fail
with `bundle_not_found`; inactive bundles fail with `bundle_not_active`; active
child alias conflicts fail with `alias_conflict`.

Scenario `031_dns_style_alias_bundle.yaml` uses the same bundle machinery with
`bundle_type: dns_style_alias_zone`, `visibility: public`, and
`allowed_record_types: ["device_alias"]`. The public-style root
`global.us.gov.ca` and child aliases such as `global.us.gov.ca.website` are
plain simulator records. They do not register a domain, query DNS, prove a
real-world institution, model a public CA, perform a real network lookup, or
change the target devices' canonical identity chains.

## Resolution

`AliasResolutionResult` reports:

- `success`
- `status`
- `reason`
- `target_device_id`
- `target_identity_chain`

Implemented resolution distinguishes:

- Alias not found.
- Alias exists but is inactive.

Future resolution slices may distinguish:

- Alias exists but is expired.
- Alias exists but the target device is revoked or quarantined.
- Alias target is a service with no device target.

## Helpers

- `claim_alias(...)`
- `resolve_alias(...)`
- `release_alias(...)`
- `claim_progressive_alias(...)`
- `suggest_alias_fallbacks(...)`
- `create_alias_bundle(...)`
- `claim_bundle_alias(...)`

These helpers should return structured results instead of raising for normal
policy failures, matching the scenario-friendly style used elsewhere in the
simulator.

## Scenarios

- `026_alias_claim_success.yaml`: device claims an authorized scoped alias.
  Implemented as direct alias scenario-runner support.
- `027_alias_claim_conflict.yaml`: duplicate alias request returns conflict.
- `028_alias_release_blocks_resolution.yaml`: released alias remains retained
  but inactive and no longer resolves.
- `029_progressive_alias_fallback.yaml`: high-scope request falls back to the
  highest authorized scope. Implemented for local RegistryHub authority.
- `030_alias_bundle_delegation.yaml`: RegistryHub creates a delegated bundle
  and claims a child alias inside it.
- `031_dns_style_alias_bundle.yaml`: public-style alias bundle resolves inside
  simulator policy without real DNS, registrar integration, public CA modeling,
  production identity proof, or real network lookup.

## Test Coverage

- Alias record creation.
- Alias resolution to device identity.
- Alias conflict detection.
- Progressive fallback grants highest authorized scope.
- Fallback preserves authority ceiling.
- Unauthorized high-level alias fails or falls back.
- Quarantined device cannot claim active alias.
- Revoked device cannot claim active alias.
- Alias bundle creation.
- Child alias inside bundle.
- Symbolic default behavior.
- DNS-style public bundle remains simulator-only.

## Non-Goals

v0.5 alias registry behavior does not add:

- Real DNS integration.
- Domain registrar integration.
- Public CA modeling.
- Production identity verification.
- Real networking.
- Production cryptography.
- External registry integration.
- Persistent global namespace services.

## Recommended Language

Use:

```text
alias registry modeling
delegated naming simulation
simulator-only DNS-style alias bundle
```

Avoid:

```text
DNS implementation
domain registration
public identity proof
verified real-world institution
production naming infrastructure
```
