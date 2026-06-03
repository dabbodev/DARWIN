# DARWIN Simulator v0.5.0 Draft Release Notes

Draft status: planning only. v0.5.0 has not been implemented, tagged, or
released. The current stable CLI version remains `darwin-sim 0.4.0`.

DARWIN v0.5 is planned as a simulator-only alias registry modeling release. It
is intended to add delegated naming behavior for Registry Hub aliases,
short-handles, progressive alias fallback, and delegated alias bundles or zones.

## Planned Focus

- Add alias records that point to canonical identity chains, devices, or
  services.
- Keep canonical identity chains as the truthful scoped identity source.
- Model device aliases and service aliases.
- Model progressive alias claims that can fall back from a requested high-scope
  alias to the highest authorized scope.
- Model alias bundles or zones as delegated mini-namespaces.
- Include DNS-style public alias bundles for simulator-only website or
  institution style lookup.
- Keep symbolic auth and proof behavior as the default.

## Planned Alias Claim Behavior

A device may request a high-level alias:

```text
global.david_server
```

If authority or namespace policy blocks that exact alias, the registry chain
may grant the highest authorized fallback alias:

```text
global.us.west1.dist25.sf2.xfinity_301.david_server
```

The result should clearly report:

- Requested alias.
- Granted alias.
- Status, such as `fallback_granted`.
- Reason, such as `insufficient_authority` or `name_taken`.
- Authority scope and authority path.

## Planned Models

- `AliasRecord`
- `AliasClaimRequest`
- `AliasClaimResult`
- `AliasBundle`
- `AliasBundleClaim`
- `AliasResolutionResult`

## Planned Registry Helpers

- `claim_alias(...)`
- `resolve_alias(...)`
- `release_alias(...)`
- `claim_progressive_alias(...)`
- `suggest_alias_fallbacks(...)`
- `create_alias_bundle(...)`
- `claim_bundle_alias(...)`

## Proposed Scenarios

- `scenarios/026_alias_claim_success.yaml`
- `scenarios/027_alias_claim_conflict.yaml`
- `scenarios/028_progressive_alias_fallback.yaml`
- `scenarios/029_alias_rejects_quarantined_device.yaml`
- `scenarios/030_alias_bundle_delegation.yaml`
- `scenarios/031_dns_style_alias_bundle.yaml`

## Compatibility Goals

- Existing v0.1 through v0.4 scenarios should keep running unchanged.
- Canonical identity chains should remain authoritative.
- Alias resolution should not mutate traffic routing.
- Symbolic behavior should remain the default proof posture.
- Revoked or quarantined devices should not be allowed to create active
  aliases.

## Safety Limits

v0.5 must remain simulator-only. It should not add:

- Real DNS integration.
- Domain registrar integration.
- Public CA behavior.
- Production identity verification.
- Real networking.
- Production cryptography.
- External registry integration.
- Public domain registration.

## Planning Validation

Planning validation should keep the released version unchanged:

```bash
python -m ruff check .
python -m pytest
python scripts/run_all_scenarios.py
python -m darwin.cli.main --version
```

Expected version:

```text
darwin-sim 0.4.0
```
