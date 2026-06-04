# DARWIN Simulator v0.5.0 Release Notes

DARWIN v0.5.0 is a simulator-only alias registry modeling release. It adds
Registry Hub alias behavior for direct device aliases, local progressive alias
fallback, and delegated alias bundles while preserving canonical identity and
TrafficHub routing behavior.

DARWIN means Direct-Access Registration Window Interface Network.

## Implemented

- Direct `AliasRecord` storage on `RegistryHub`.
- Direct alias lookup through `resolve_alias(...)`.
- Alias claim, resolve, and release helpers:
  `claim_alias(...)`, `resolve_alias(...)`, and `release_alias(...)`.
- Alias conflict behavior that rejects duplicate active aliases and preserves
  the original active owner.
- Alias release behavior that retains the alias record as `released` while
  blocking active resolution.
- Alias claim rejection for quarantined or revoked target devices.
- Scenario runner alias actions for direct alias claim, resolve, release,
  progressive alias claim, alias bundle creation, and child bundle alias claim.
- Scenario assertions for alias resolution, alias status, inactive alias
  resolution, bundle status, child bundle alias resolution, granted alias
  provenance, authority ceiling, and canonical identity preservation.
- Progressive alias fallback inside the approving RegistryHub authority scope.
- Authority ceiling behavior that records the highest local scope allowed for
  the granted alias and does not grant above that scope.
- Alias bundle records through `AliasBundle`.
- Delegated alias bundle creation through `create_alias_bundle(...)`.
- Child alias claims inside active bundles through `claim_bundle_alias(...)`.
- DNS-style alias bundle scenario support using simulator-local bundle records
  with public-style metadata.

## Scenarios

v0.5 adds alias registry scenarios `026` through `031`:

- `scenarios/026_alias_claim_success.yaml` covers direct alias claim and
  resolution for a registered device.
- `scenarios/027_alias_claim_conflict.yaml` covers direct alias conflict
  behavior while preserving the original active owner.
- `scenarios/028_alias_release_blocks_resolution.yaml` covers released aliases
  retained as inactive records that no longer resolve.
- `scenarios/029_progressive_alias_fallback.yaml` covers high-scope alias
  requests that fall back to the highest locally authorized RegistryHub scope.
- `scenarios/030_alias_bundle_delegation.yaml` covers delegated alias bundle
  creation and child device alias resolution.
- `scenarios/031_dns_style_alias_bundle.yaml` covers a public-style alias
  bundle modeled entirely inside the simulator.

## Implemented Models

- `AliasRecord`
- `AliasBundle`
- `AliasClaimResult`
- `AliasBundleClaimResult`
- `BundleAliasClaimResult`
- `ProgressiveAliasClaimResult`
- `AliasResolutionResult`
- `AliasReleaseResult`

`AliasClaimRequest` is not part of the implemented v0.5 model. If added later,
it should remain a simulator-local request DTO unless a future release expands
the alias workflow.

## Compatibility

- Existing v0.1 through v0.4 scenarios continue to validate and run.
- Canonical identity chains remain the authoritative identity source.
- Aliases do not replace canonical identity.
- Alias resolution does not mutate TrafficHub routing.
- Symbolic simulator behavior remains the default proof posture.

## Explicit Limits

v0.5.0 does not add:

- Real DNS integration.
- DNS replacement behavior.
- Domain registrar integration.
- Public CA behavior.
- Production identity proof.
- Real networking or real network lookup.
- Production cryptography.
- External registry integration.
- TrafficHub routing changes.
- Canonical identity replacement.

DNS-style alias bundles are naming records inside the simulator only. They do
not register domains, query DNS, prove a real-world institution, model a public
CA, or route traffic.
