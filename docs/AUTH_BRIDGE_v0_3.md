# DARWIN v0.3 Experimental Auth Bridge

This document describes the simulator-only v0.3 bridge from symbolic auth
booleans toward deterministic HMAC-style verification.

## Status

This is not production cryptography. It is only a DARWIN simulator experiment
for packets, checkpoints, and rolling proof scenarios.

Planning docs:

- `docs/V0_3_ROADMAP.md`
- `docs/RELEASE_NOTES_v0_3.md`

## What It Does

- Keeps `symbolic` auth as the default mode.
- Adds explicit opt-in mode `hmac_sha256_experimental`.
- Uses Python standard-library `hmac`, `hashlib`, and `json`.
- Canonicalizes payload material with deterministic JSON before signing.
- Verifies tags with `hmac.compare_digest()`.
- Reuses the existing `invalid_auth_tag` rejection path for packet and
  checkpoint failures.

## What It Does Not Do

- No real networking.
- No DNS integration.
- No async runtime.
- No web UI.
- No production cryptography.
- No custom cryptographic primitive.
- No key exchange.
- No public-key signatures.
- No certificate chains.
- No hardware identity.
- No secure storage.
- No real device secrets.

## Why HMAC-SHA256 From The Standard Library

HMAC-SHA256 is available in Python's standard library and gives the simulator a
deterministic, well-known tag verification shape without adding dependencies or
inventing a custom primitive.

## Scenario Usage

Scenarios opt in per step:

```yaml
auth_mode: hmac_sha256_experimental
auth_secret: test_secret_simulator_only
```

Packet scenarios can intentionally tamper the generated tag:

```yaml
tamper_auth_tag: true
```

Checkpoint scenarios can force invalid auth with:

```yaml
auth_tag_valid: false
```

They can also model material tampering after tag creation:

```yaml
tamper_payload_after_tag: true
```

Rolling-proof scenarios can generate a test tag from step fields and then
tamper the verified material:

```yaml
tamper_nonce: true
tamper_counter: true
```

Secrets in scenarios are deterministic test fixtures only. Do not store real
secrets in DARWIN scenarios or documentation.

## Session Lifecycle Modeling

v0.3 also includes simulator-local session secret records owned by a
`RegistryHub`. These records are deterministic test/demo fixtures. They do not
perform key exchange, secure storage, production key management, networking, or
public-key signing.

A local session records:

- The session ID, device ID, owning hub ID, and scope.
- The opt-in auth mode, currently `hmac_sha256_experimental`.
- A deterministic test secret supplied by the scenario or test.
- The current rolling-proof counter.
- Optional integer simulated-time `created_at` and `expires_at` values.
- Session state and rotation index.

Session creation only succeeds for devices already registered with the owning
`RegistryHub`. Expiration uses integer simulated time: when
`current_time >= expires_at`, the session becomes `expired` and cannot verify
rolling proof material. Rotation replaces the test secret, increments
`rotation_index`, and resets `current_counter` to `0`.

Session-bound rolling proof verification requires a counter strictly greater
than the stored session counter. Successful verification advances the stored
counter. Reusing a counter, lowering a counter, using an expired session, or
using a tag generated with an old secret fails cleanly.

Revocation and quarantine are simulator trust states, not cryptographic
protocols. A local session can be explicitly revoked, and every local session
for a device can be revoked together. When a registered device is quarantined,
active local sessions for that device become `quarantined`. HMAC session proof
verification only succeeds for `active` sessions whose device is not currently
`quarantined` or `revoked`.

Checkpoint updates also respect explicit device trust state. If a registered
device is already `quarantined` or `revoked`, a valid HMAC checkpoint is
rejected with `device_quarantined` or `device_revoked` and does not update the
trusted checkpoint, attachment, or device state back to online/active.

Scenario actions:

```yaml
- action: create_local_session
  registry_hub: hub_home_001
  device: dev_A9F3
  session_id: session_001
  auth_secret: test_secret_simulator_only
  ttl: 10

- action: rotate_local_session
  registry_hub: hub_home_001
  session_id: session_001
  new_auth_secret: new_test_secret_simulator_only

- action: revoke_local_session
  registry_hub: hub_home_001
  session_id: session_001
  reason: operator_revocation

- action: expire_local_sessions
  registry_hub: hub_home_001
  current_time: 12

- action: verify_hmac_session_proof
  registry_hub: hub_home_001
  session_id: session_001
  counter: 1
  nonce: nonce_001
  requested_capability: send_normal_traffic
```

Checked-in HMAC scenarios:

- `scenarios/012_hmac_checkpoint_success.yaml`
- `scenarios/013_hmac_packet_auth_failure.yaml`
- `scenarios/014_hmac_checkpoint_tamper_failure.yaml`
- `scenarios/015_hmac_missing_secret_failure.yaml`
- `scenarios/016_hmac_rolling_proof_failure.yaml`
- `scenarios/017_hmac_session_rotation.yaml`
- `scenarios/018_hmac_session_expiration.yaml`
- `scenarios/019_hmac_revoked_session_failure.yaml`
- `scenarios/020_hmac_quarantine_blocks_checkpoint.yaml`

## Edge-Case Coverage

The v0.3 simulator tests and scenarios cover these failure boundaries:

- Wrong HMAC secret.
- Checkpoint or packet material changed after tag creation.
- Missing HMAC secret/configuration.
- Rolling-proof nonce mismatch.
- Rolling-proof counter mismatch.
- Session expiration blocks rolling-proof verification.
- Session rotation invalidates proof tags generated with the old secret.
- Session counters reject same-counter and lower-counter reuse.
- Revoked sessions reject rolling-proof verification.
- Device quarantine marks active local sessions quarantined.
- Valid HMAC checkpoints from quarantined or revoked devices are rejected
  without reviving trusted device state.
- Quarantined source devices remain blocked even when packet HMAC verifies.
- Default packet and checkpoint construction still uses symbolic auth.

Failed packet auth reuses `invalid_auth_tag` and prevents delivery. Failed
checkpoint auth rejects the update and leaves the previous trusted checkpoint
state in place. Failed rolling proofs reuse the existing quarantine path.

## Future Work

- Add explicit auth configuration objects to scenario setup if the simulator
  grows beyond per-step test fixtures.
- Expand trace exports to show auth mode and verification outcome.
