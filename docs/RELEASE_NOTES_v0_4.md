# DARWIN Simulator v0.4.0 Release Notes

DARWIN v0.4.0 is a simulator-only move-contract auth modeling release. It
connects the relocation layer to opt-in HMAC-style move-contract verification
while preserving symbolic move contracts as the default behavior.

## Implemented Focus

- Added move-contract HMAC auth material helpers in
  `darwin/auth/move_contract.py`.
- Added deterministic helpers for building, signing, and verifying
  move-contract proof material with the existing v0.3 experimental HMAC bridge.
- Added `verify_move_contract_auth(...)` policy checks for symbolic and
  `hmac_sha256_experimental` move contracts.
- Integrated HMAC move-contract verification into relocation attachment updates.
- Preserved missing `auth_mode` and `auth_mode: symbolic` behavior on the
  existing `MoveContract.valid` path.

## Verification Policy

Symbolic move contracts still work by default. A move contract without
`auth_mode`, or with `auth_mode: symbolic`, uses the existing symbolic
`valid: true` / `valid: false` behavior.

When `auth_mode: hmac_sha256_experimental` is present, the simulator:

- Requires `session_id`, `move_nonce`, `move_counter`, and `move_auth_tag`.
- Looks up the simulator-local HMAC session.
- Rejects inactive sessions, stale counters, quarantined devices, and revoked
  devices.
- Binds the HMAC material to the device, passport, source and destination
  scopes, old and new attachments, nonce, session, counter, and simulated
  timestamp when present.
- Verifies the move auth tag before relocation updates attachment state or
  records the move.
- Advances the session counter only after successful verification.

## Scenarios

v0.4 adds checked-in scenarios `021` through `025`:

- `scenarios/021_hmac_move_contract_success.yaml`
- `scenarios/022_hmac_move_contract_tamper_failure.yaml`
- `scenarios/023_hmac_move_contract_expired_session.yaml`
- `scenarios/024_hmac_move_contract_revoked_device.yaml`
- `scenarios/025_symbolic_move_contract_still_works.yaml`

Together these cover HMAC move success, tampered move rejection, expired
session rejection, revoked-device rejection, and preservation of the default
symbolic move-contract path.

## Compatibility

- Existing symbolic move validation remains the default.
- Existing v0.1 through v0.3 scenarios continue to validate and run unchanged
  unless a scenario explicitly opts in to the v0.4 HMAC move-contract path.
- HMAC move-contract auth remains deterministic, local, and simulator-only.

## Safety Limits

v0.4 does not add production cryptography or production security behavior. It
does not add:

- Real networking.
- Key exchange.
- Secure storage.
- Public-key signatures.
- Certificate chains.
- Passport cryptography.
- Real network handoff.
- Encrypted transport.
- Production key lifecycle.
- Distributed consensus.

The HMAC helpers are test-fixture modeling utilities for simulator behavior,
not production cryptographic infrastructure.

## Validation

Release cleanup validation should include:

```bash
python -m ruff check .
python -m pytest
python scripts/run_all_scenarios.py
python -m darwin.cli.main --version
python -m darwin.cli.main scenario-index
python -m darwin.cli.main list-scenarios
python -m darwin.cli.main list-presets
```

Expected version:

```text
darwin-sim 0.4.0
```
