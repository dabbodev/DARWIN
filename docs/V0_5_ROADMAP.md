# DARWIN v0.5 Roadmap: Alias Registry Modeling

DARWIN v0.5 is planned as a simulator-only delegated naming release. It should
add Registry Hub alias behavior for short handles, progressive alias fallback,
and delegated alias bundles or zones without replacing canonical identity
chains.

v0.5 answers this simulator question:

```text
Can a device keep its truthful scoped identity chain while using an authorized
short alias granted by the highest registry scope policy allows?
```

## Status

Direct alias helper and scenario-runner slices are implemented on the v0.5
planning branch. This roadmap does not bump the package version, define real
DNS behavior, integrate an external registry, or claim production identity
proof.

The current stable package remains `darwin-sim 0.4.0`.

Completed v0.5 planning slices:

- Direct alias record/result models and in-memory Registry Hub alias storage.
- Direct `claim_alias(...)`, `resolve_alias(...)`, and `release_alias(...)`
  helpers for registered device aliases.
- Scenario runner support for direct alias claim, resolve, and release.
- Scenario assertions for alias resolution, alias status, inactive resolution,
  and canonical identity preservation.
- `026_alias_claim_success.yaml`.
- `027_alias_claim_conflict.yaml`.
- `028_alias_release_blocks_resolution.yaml`.

## Current v0.4 Foundation

DARWIN v0.4 provides the base concepts that alias registry modeling should
reuse:

- Registry Hubs and scoped device registration.
- Canonical scoped identity paths.
- Traffic Hubs and Logical Lanes.
- Checkpoints and relocation with `in_transit` behavior.
- Symbolic trust and quarantine.
- Optional simulator-only HMAC auth bridge behavior.
- Session-secret lifecycle modeling.
- HMAC-backed move-contract auth while preserving symbolic defaults.
- Scenario runner, scenario presets, scenario index, Mermaid export, and
  timeline export.

## Planned v0.5 Scope

v0.5 should model:

- Canonical identity chains as the truthful identity source.
- Device aliases that point to devices.
- Service aliases that point to services exposed by devices or hubs.
- Progressive alias claims that try a requested high-scope alias first and then
  grant the highest authorized fallback alias.
- Delegated alias bundles or alias zones.
- DNS-style public alias bundles for website or institution style lookup,
  still simulator-only.
- Explicit alias conflict detection.
- Symbolic proof and policy mode as the default.

The registry naming layer should stay separate from traffic routing. A
`traffic_path` describes where packets currently flow. An alias describes an
authorized shortcut that resolves to an identity or service.

## Core Naming Distinctions

Example canonical identity:

```text
global.us.west1.dist25.sf2.xfinity_301.node53.david_router.project_server
```

Example requested alias:

```text
global.david_server
```

Example fallback alias:

```text
global.us.west1.dist25.sf2.xfinity_301.david_server
```

The simulator should preserve these distinct fields:

- `canonical_identity_chain`: truthful scoped identity path.
- `alias` or `short_handle`: authorized shortcut.
- `alias_bundle` or `alias_zone`: delegated namespace containing many aliases.
- `traffic_path`: current routing path, not registry naming.

## Alias Taxonomy

Canonical identity chain:

- The durable, truthful identity path assigned through Registry Hub scope.
- Never replaced by an alias.
- Used as the final identity target for device resolution.

Device alias:

- A short handle that resolves to a registered device identity.
- Example: `global.us.west1.dist25.sf2.xfinity_301.david_server`.

Service alias:

- A short handle that resolves to a service target, with optional device
  identity context.
- Example: `global.us.west1.dist25.sf2.xfinity_301.project_api`.

Progressive alias:

- A claim flow, not a separate record type.
- Attempts a high-level alias and falls back to the highest scope allowed by
  authority and namespace policy.

Alias bundle or alias zone:

- A delegated mini-namespace that may contain child aliases.
- Example zone: `global.us.gov.ca`.

DNS-style public alias bundle:

- A public, policy-controlled alias zone for website or institution style
  lookup inside the simulator.
- Not real DNS, not domain registrar integration, and not a public CA model.

## Proposed Alias Record Fields

`AliasRecord` should remain plain simulator data. Proposed fields:

- `alias`
- `alias_type`
- `target_device_id`
- `target_service_id`
- `target_identity_chain`
- `requested_by_device_id`
- `requested_through_hub`
- `approved_by_registry_hub`
- `authority_scope`
- `authority_path`
- `status`
- `visibility`
- `ttl`
- `conflict_status`
- `auth_mode`
- `proof_mode`

`target_device_id` and `target_service_id` should be optional, but an active
alias must have enough target data to resolve deterministically.

`auth_mode` and `proof_mode` should default to symbolic simulator behavior.
Future HMAC-style alias proof modeling can be explored only as an explicit
simulator mode and must not be described as production identity verification.

## Progressive Alias Claim

A device may request a high-level alias. If the exact alias is unavailable or
the requesting registry path lacks authority, the registry chain can grant the
highest authorized fallback alias.

Example:

- Requested: `global.david_server`
- Granted: `global.us.west1.dist25.sf2.xfinity_301.david_server`
- Status: `fallback_granted`
- Reason: `insufficient_authority` or `name_taken`

The key policy decision should be the authority ceiling. A lower hub can ask
upward only when policy allows it. If upward approval fails, fallback must not
grant an alias above the highest approved scope.

## Alias Authority Rules

- A Registry Hub can grant aliases only within its authority scope.
- Parent registries may approve higher-scope aliases.
- A lower hub can request upward alias registration only if policy allows.
- Alias records must not replace canonical identity truth.
- Revoked or quarantined devices cannot create active aliases.
- Alias conflict detection must be explicit.
- Alias release should not delete or mutate canonical device identity.
- Expired aliases should resolve as inactive or expired, not missing, when the
  record is still retained for audit.

## Alias Bundles and Zones

Alias bundles are delegated mini-namespaces.

Example delegated zone:

```text
global.us.gov.ca
```

Delegated to:

```text
California government registry authority
```

Child aliases:

```text
global.us.gov.ca.website
global.us.gov.ca.dmv
global.us.gov.ca.tax
```

Bundle policy should define:

- Owning or delegated Registry Hub.
- Parent authority that approved delegation.
- Allowed alias types.
- Visibility rules.
- Conflict behavior inside the bundle.
- Whether child aliases inherit TTL or proof settings.

## DNS-Style Alias Bundles

DNS-style alias bundles are public, policy-controlled alias zones intended for
website or institution style lookup in the simulator.

They are useful for modeling:

- Public-facing institutional names.
- Delegated public namespace policy.
- Conflicts between requested public aliases.
- Lookup behavior that feels DNS-like while remaining a registry simulation.

Non-goals:

- No real DNS integration.
- No domain registrar integration.
- No public CA model.
- No production identity verification.
- No external registry dependency.

## Proposed Simulator Models

- `AliasRecord`
- `AliasClaimRequest`
- `AliasClaimResult`
- `AliasBundle`
- `AliasBundleClaim`
- `AliasResolutionResult`

Recommended result fields should include `success`, `status`, `reason`,
`requested_alias`, `granted_alias`, `authority_scope`, and conflict details
where relevant.

## Proposed Registry Helpers

- `claim_alias(...)`
- `resolve_alias(...)`
- `release_alias(...)`
- `claim_progressive_alias(...)`
- `suggest_alias_fallbacks(...)`
- `create_alias_bundle(...)`
- `claim_bundle_alias(...)`

Helper naming should avoid DNS server, registrar, certificate, or production
verification terms.

## Proposed Scenarios

- `026_alias_claim_success.yaml` - completed for direct alias claim and
  resolution.
- `027_alias_claim_conflict.yaml` - completed for direct alias conflict
  detection and original target preservation.
- `028_alias_release_blocks_resolution.yaml` - completed for direct alias
  release and inactive resolution behavior.
- `029_progressive_alias_fallback.yaml`
- `030_alias_rejects_quarantined_device.yaml`
- `031_alias_bundle_delegation.yaml`
- `032_dns_style_alias_bundle.yaml`

## Proposed Tests

- Alias record creation.
- Alias resolution to device identity.
- Alias conflict detection.
- Progressive fallback grants highest authorized scope.
- Fallback preserves authority ceiling.
- Unauthorized high-level alias fails or falls back.
- Quarantined device cannot claim an active alias.
- Revoked device cannot claim an active alias.
- Alias bundle creation.
- Child alias inside bundle.
- DNS-style bundle lookup remains simulator-only.
- Symbolic default behavior.

## Release Framing

Use:

```text
delegated naming simulation
alias registry modeling
simulator-only alias zones
```

Avoid:

```text
real DNS
public DNS replacement
domain registration
production identity proof
certificate-backed public naming
```

## Planning Validation

During the planning branch, validation should confirm the existing simulator
remains stable and the version is not bumped:

```bash
python -m ruff check .
python -m pytest
python scripts/run_all_scenarios.py
python -m darwin.cli.main --version
```

Expected CLI version:

```text
darwin-sim 0.4.0
```
