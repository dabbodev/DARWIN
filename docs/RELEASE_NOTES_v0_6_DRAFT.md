# DARWIN Simulator v0.6.0 Draft Release Notes

These are draft planning notes for a future v0.6 release. v0.6 is not
implemented or released. The current stable simulator version remains
`darwin-sim 0.5.0`.

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

## Planned Additions

- Alias claim requests that can traverse parent Registry Hubs.
- Authority path recording for chain-aware alias claims.
- Authority ceiling recording for successful fallback claims.
- Per-hub decisions to approve, reject, continue upward, or offer fallback.
- Structured decision chains for scenario assertions.
- Highest-approved alias selection.
- Highest-allowed fallback alias selection when the requested alias is
  unavailable or unauthorized.

## Proposed Models

- `AliasAuthorityStep`
- `AliasAuthorityPath`
- `AliasDelegationPolicy`
- `AliasAuthorityDecision`
- `AliasChainClaimRequest`
- `AliasChainClaimResult`

## Proposed Helpers

- `claim_alias_through_authority_chain(...)`
- `evaluate_alias_authority_step(...)`
- `find_highest_authorized_alias_scope(...)`
- `record_alias_authority_decision(...)`
- `summarize_alias_authority_path(...)`

## Proposed Decision Statuses

- `approved_here`
- `continue_upward`
- `fallback_available`
- `name_taken`
- `insufficient_authority`
- `policy_denied`
- `device_blocked`
- `authority_path_broken`

## Proposed Scenarios

Planned alias authority chain scenarios:

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
