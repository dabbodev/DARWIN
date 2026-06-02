# DARWIN v0.4 Roadmap: Move-Contract Auth Modeling

DARWIN v0.4 is planned as a simulator-only move-contract auth modeling
release. The goal is to connect the existing relocation layer to the v0.3
experimental auth bridge without replacing symbolic move validation as the
default.

v0.4 should answer this planning question:

```text
How can a Move Contract prove, in simulator-only form, that a device authorized
a move from one attachment/scope to another?
```

## Current v0.3 Foundation

DARWIN v0.3 already provides the pieces needed for a careful v0.4 extension:

- Symbolic auth remains the default.
- `hmac_sha256_experimental` is opt-in.
- HMAC helpers use Python standard-library `hmac`, `hashlib`, deterministic
  JSON canonicalization, and `hmac.compare_digest()`.
- Local auth sessions are simulator-owned records with deterministic test
  secrets.
- Rolling proof helpers bind device, hub, session, counter, nonce, and
  requested capability.
- Session lifecycle modeling includes creation, rotation, expiration, stale
  counter rejection, explicit revocation, and quarantine interaction.
- Revoked or quarantined devices cannot restore trusted checkpoint state with a
  valid HMAC checkpoint.
- Relocation, in-transit state, lane pause/resume, and symbolic
  `MoveContract.valid` validation already exist.

## Proposed v0.4 Scope

v0.4 adds an optional HMAC-backed proof model for move contracts while leaving
existing symbolic behavior untouched.

The implemented direction is:

- Keep `MoveContract.valid` as the default symbolic validation path.
- Allow move contracts to opt in to `hmac_sha256_experimental`.
- Reuse v0.3 local session records and counter freshness rules.
- Add deterministic move-proof material helpers rather than a new crypto
  primitive.
- Report clean simulator failure reasons that scenario assertions can inspect.

## Proposed Move Contract Fields

`MoveContract` may optionally include:

- `auth_mode`
- `move_auth_tag`
- `move_nonce`
- `session_id`
- `move_counter`
- `proof_context`

`proof_context` should be small, deterministic simulator metadata. It can
describe why the proof was generated, such as `relocation_resume`, without
claiming real device-held secret storage or production authorization.

## Proposed HMAC Move Proof Material

The v0.4 proof material should bind all fields that define the move:

- `device_id`
- `passport_id`
- `from_scope`
- `to_scope`
- `old_attachment`
- `new_attachment`
- `move_nonce`
- `session_id`
- `move_counter`
- `timestamp` or `current_time` when already simulated by the scenario

This prevents a proof generated for one destination, old attachment, session,
nonce, or counter from being reused for another simulated move.

## Proposed Validation Rules

### Symbolic Mode

- Use existing move-contract behavior.
- `valid=True` contracts that match the device and passport can update
  attachment state.
- `valid=False`, wrong device ID, or wrong passport ID remains rejected by the
  existing symbolic path.

### HMAC Mode

For `auth_mode: hmac_sha256_experimental`, validation requires:

- The referenced local session exists.
- The device is not revoked.
- The device is not quarantined.
- The session is active.
- The move counter is strictly newer than the session counter.
- The move HMAC tag verifies against deterministic move proof material.
- The move fields being applied match the fields covered by proof material.

On success, the simulator verifies move auth, advances the local session
counter, updates attachment state using the existing move flow, and records the
move.

## Proposed Failure Reasons

Clean failure reasons should remain scenario-friendly and deterministic:

- `invalid_move_auth_tag`
- `missing_move_session`
- `move_session_inactive`
- `device_revoked`
- `device_quarantined`
- `stale_move_counter`
- `move_contract_rejected`

Move-contract integration preserves the existing clean result shape:
`update_attachment_after_move()` returns `move_contract_rejected` with the auth
failure reason when HMAC verification fails.

## Proposed Simulator Objects

The implementation pass should consider:

- Extending `MoveContract` with optional auth fields.
- Adding `MoveAuthMaterial` for deterministic proof material construction.
- Adding `MoveAuthResult` for move-specific verification outcomes.
- Keeping HMAC helper names explicitly experimental.

Avoid production signature terminology. This is not a passport signature, a CA
model, a handoff certificate, or device-held secure-key proof.

## Scenarios

- `021_hmac_move_contract_success.yaml`
- `022_hmac_move_contract_tamper_failure.yaml`
- `023_hmac_move_contract_expired_session.yaml`
- `024_hmac_move_contract_revoked_device.yaml`
- `025_symbolic_move_contract_still_works.yaml`

## Tests

- HMAC move proof material is deterministic.
- Valid HMAC move contract updates attachment.
- Tampered destination fails.
- Tampered old attachment fails.
- Wrong nonce fails.
- Stale counter fails.
- Expired session fails.
- Revoked device fails.
- Quarantined device fails.
- Symbolic move contract behavior still works.

## Non-Goals

v0.4 must not add:

- Real signatures.
- CA or certificate-chain modeling.
- Passport cryptography.
- Real network handoff.
- Encrypted transport.
- Production key lifecycle.
- Distributed consensus.
- Key exchange.
- Secure storage.
- Custom crypto primitives.

## Release Framing

v0.4 should be described as move-contract auth modeling, not production secure
mobility.

It remains a deterministic simulator layer for testing DARWIN protocol behavior
around relocation, session state, revocation, quarantine, and proof freshness.

## Planning Validation

During this planning branch, the package version should remain `0.3.0`.

Expected validation commands:

```bash
python -m ruff check .
python -m pytest
python scripts/run_all_scenarios.py
python -m darwin.cli.main --version
```

Expected CLI version:

```text
darwin-sim 0.3.0
```
