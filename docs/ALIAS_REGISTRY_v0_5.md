# DARWIN v0.5 Alias Registry Planning

This document sketches the planned v0.5 Registry Hub alias model. The first
helper slice is implemented for basic direct aliases only; progressive
fallback, bundles, zones, and DNS-style integration remain planning topics.

Aliases are authorized shortcuts. They do not replace canonical identity
chains, alter traffic paths, or integrate with real DNS.

## Helper Slice Status

Implemented in the current v0.5 planning branch:

- Basic `AliasRecord` and direct alias result models.
- Registry Hub in-memory alias storage.
- `claim_alias(...)` for direct aliases targeting registered devices.
- `resolve_alias(...)` for active direct aliases.
- `release_alias(...)` preserving a released alias record.
- Active alias conflict detection using the existing registry conflict table.
- Alias claim rejection for quarantined or revoked target devices.

Not implemented yet:

- Progressive alias fallback.
- Alias bundles or zones.
- DNS-style public alias integration.
- Service alias behavior beyond reserved model fields.
- Production cryptography or external proof flows for alias claims.

Alias helpers do not mutate device labels, passport IDs, attachments, canonical
identity chains, or TrafficHub routing state.

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
  CA checks, or production verification.

## Proposed AliasRecord

Proposed fields:

- `alias`
- `alias_type`
- `target_device_id` optional
- `target_service_id` optional
- `target_identity_chain`
- `requested_by_device_id`
- `requested_through_hub`
- `approved_by_registry_hub`
- `authority_scope`
- `authority_path`
- `status`
- `visibility`
- `ttl` optional
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

The default proof posture should be symbolic. Alias proof data should model
simulator authorization behavior only.

## Proposed Claim Request and Result

`AliasClaimRequest` should capture:

- Requested alias.
- Alias type.
- Requesting device ID.
- Requesting hub.
- Target identity chain.
- Optional target service ID.
- Requested visibility.
- Requested TTL.
- Requested proof mode.

`AliasClaimResult` should capture:

- `success`
- `status`
- `reason`
- `requested_alias`
- `granted_alias`
- `alias_record`
- `authority_scope`
- `authority_path`
- `fallback_candidates`
- `conflict_alias`
- `conflict_status`

## Progressive Alias Fallback

Progressive alias claim should evaluate the requested alias against authority
and namespace policy before proposing fallbacks.

Example:

```text
requested: global.david_server
granted: global.us.west1.dist25.sf2.xfinity_301.david_server
status: fallback_granted
reason: insufficient_authority
```

Another valid reason:

```text
reason: name_taken
```

Recommended ordering:

1. Validate requesting device state.
2. Validate requested alias syntax and target.
3. Check whether requested alias is inside an authorized scope.
4. Check conflicts at that scope.
5. If blocked, compute fallback candidates from highest to lowest scope.
6. Grant the first candidate allowed by authority and conflict policy.
7. Return explicit reason and granted scope.

Fallback must preserve the authority ceiling. A lower Registry Hub should not
grant an alias above its approved scope just because the fallback flow was
requested.

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

`AliasBundle` should model delegated namespaces.

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

Proposed bundle fields:

- `bundle_root`
- `bundle_type`
- `delegated_to_registry_hub`
- `approved_by_registry_hub`
- `authority_scope`
- `status`
- `visibility`
- `allowed_alias_types`
- `default_ttl`
- `conflict_policy`
- `auth_mode`
- `proof_mode`

`AliasBundleClaim` should capture the child alias request, target, requesting
device or service, and result status.

## Resolution

`AliasResolutionResult` should report:

- `success`
- `status`
- `reason`
- `alias`
- `alias_type`
- `target_device_id`
- `target_service_id`
- `target_identity_chain`
- `resolved_record`
- `visibility`
- `authority_scope`

Resolution should distinguish:

- Alias not found.
- Alias exists but is inactive.
- Alias exists but is expired.
- Alias exists but the target device is revoked or quarantined.
- Alias target is a service with no device target.

## Proposed Helpers

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

## Scenario Plan

- `026_alias_claim_success.yaml`: device claims an authorized scoped alias.
- `027_alias_claim_conflict.yaml`: duplicate alias request returns conflict.
- `028_progressive_alias_fallback.yaml`: high-scope request falls back to the
  highest authorized scope.
- `029_alias_rejects_quarantined_device.yaml`: quarantined device cannot create
  an active alias.
- `030_alias_bundle_delegation.yaml`: parent registry delegates a bundle and a
  child alias is claimed inside it.
- `031_dns_style_alias_bundle.yaml`: public-style alias bundle resolves inside
  simulator policy without real DNS.

## Test Plan

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

v0.5 alias planning does not add:

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
