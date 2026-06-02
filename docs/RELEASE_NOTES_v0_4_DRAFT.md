# DARWIN Simulator v0.4 Draft Release Notes

Draft status: planning only. v0.4 has not been implemented or released.

The planned v0.4 theme is move-contract auth modeling. The release should
connect DARWIN's relocation and move-contract layer to the v0.3 experimental
HMAC auth bridge while keeping symbolic move validation as the default.

## Planned Focus

- Add optional HMAC move-contract proof modeling behind
  `hmac_sha256_experimental`.
- Preserve existing symbolic `MoveContract.valid` behavior.
- Bind move proof material to device, passport, source scope, destination
  scope, old attachment, new attachment, nonce, session, counter, and simulated
  time when present.
- Reuse v0.3 local session lifecycle rules for active sessions, expiration,
  stale counter rejection, revocation, and quarantine.
- Keep all behavior deterministic, local, and simulator-only.

## Proposed Scenarios

- `scenarios/021_hmac_move_contract_success.yaml`
- `scenarios/022_hmac_move_contract_tamper_failure.yaml`
- `scenarios/023_hmac_move_contract_expired_session.yaml`
- `scenarios/024_hmac_move_contract_revoked_device.yaml`
- `scenarios/025_symbolic_move_contract_still_works.yaml`

These scenarios are proposed only and are not expected to exist during the
planning pass.

## Proposed Failure Reasons

- `invalid_move_auth_tag`
- `missing_move_session`
- `expired_move_session`
- `revoked_device`
- `quarantined_device`
- `stale_move_counter`
- `move_contract_rejected`

## Safety Limits

v0.4 must remain non-production and simulator-only. It should not add:

- Real networking.
- Production cryptography.
- Key exchange.
- Secure storage.
- Public-key signatures.
- Certificate chains.
- Passport cryptography.
- Real network handoff.
- Encrypted transport.
- Production key lifecycle.
- Distributed consensus.
- Custom crypto primitives.

## Compatibility

- Symbolic move validation remains the default.
- HMAC move proof is opt-in.
- Existing v0.1 through v0.3 scenarios should continue to run unchanged unless
  a scenario explicitly opts in to the new v0.4 HMAC move-contract path.

## Planning Validation

The planning branch should still report the released v0.3 version:

```bash
python -m darwin.cli.main --version
```

Expected:

```text
darwin-sim 0.3.0
```
