# DARWIN v0.4 Move-Contract Auth Planning

This document proposes how DARWIN can model authenticated move contracts in
v0.4 while staying simulator-only and non-production.

The key recommendation is to treat move-contract auth as an opt-in extension
of the v0.3 HMAC bridge. Symbolic move contracts remain the default behavior.

## Status

Planning plus first helper slice. The simulator now has deterministic
move-contract HMAC helper functions in `darwin/auth/move_contract.py`, but the
helpers are not wired into relocation behavior yet.

Related documents:

- `docs/AUTH_BRIDGE_v0_3.md`
- `docs/V0_4_ROADMAP.md`
- `docs/RELEASE_NOTES_v0_4_DRAFT.md`

## Design Question

A move contract currently records a symbolic claim:

```text
This device moved from old attachment/scope to new attachment/scope.
```

v0.4 should model this stronger simulator-only question:

```text
Did the same simulated device session authorize this exact move?
```

The proof should cover the old location, new location, identity, passport,
nonce, session, and counter so a successful proof cannot be replayed against a
different simulated move.

## Compatibility Rule

Existing symbolic move validation remains supported:

```yaml
valid: true
```

or:

```yaml
valid: false
```

If no explicit HMAC auth mode is present, relocation should continue to use the
existing symbolic contract path.

## Proposed MoveContract Shape

The current contract fields remain:

- `move_id`
- `passport_id`
- `device_id`
- `from_scope`
- `to_scope`
- `old_attachment`
- `new_attachment`
- `valid`
- `timestamp`

The v0.4 implementation may add optional fields:

- `auth_mode`
- `move_auth_tag`
- `move_nonce`
- `session_id`
- `move_counter`
- `proof_context`

Example planning shape:

```yaml
move_contract:
  move_id: move_dev_B2C8_hub_2
  passport_id: passport_dev_B2C8
  device_id: dev_B2C8
  from_scope: global.family.home
  to_scope: global.family.office
  old_attachment: hub_3
  new_attachment: hub_2
  valid: true
  timestamp: 12
  auth_mode: hmac_sha256_experimental
  session_id: session_move_001
  move_counter: 3
  move_nonce: nonce_move_001
  proof_context: relocation_resume
  move_auth_tag: generated_test_tag
```

`move_auth_tag` is a deterministic simulator tag, not a production signature.

As of the first v0.4 helper slice, `MoveContract` includes these optional auth
fields for tests and future integration. Existing symbolic constructors and
relocation behavior remain supported.

## Proposed Move Proof Material

The proof helper should produce deterministic canonical JSON over:

```text
device_id
passport_id
from_scope
to_scope
old_attachment
new_attachment
move_nonce
session_id
move_counter
timestamp/current_time when present
proof_context when present
```

The timestamp rule should be conservative: include the value when it is already
part of the simulated move contract or scenario step, but do not introduce wall
clock time.

The first helper slice uses the existing v0.3 HMAC bridge:

- `canonical_json`
- `compute_hmac_tag`
- `verify_hmac_tag`

`build_move_auth_material(...)` and
`move_auth_material_from_contract(...)` produce the fixed proof field set above,
including `timestamp` only when present. `compute_move_auth_tag(...)` and
`verify_move_auth_tag(...)` normalize material before tagging so dict field order
does not affect the tag. Missing required fields raise `ValueError` on compute
and return `False` on verify.

## Proposed HMAC Validation Flow

For `auth_mode: hmac_sha256_experimental`:

1. Locate `session_id` in the owning `RegistryHub.local_sessions`.
2. Reject with `missing_move_session` if it does not exist.
3. Reject with `expired_move_session` if simulated time expires it.
4. Reject with `revoked_device` if the device is revoked.
5. Reject with `quarantined_device` if the device is quarantined.
6. Reject with `stale_move_counter` if the counter is not newer.
7. Build move proof material from the contract fields being applied.
8. Verify `move_auth_tag` using the session secret.
9. Reject with `invalid_move_auth_tag` if verification fails.
10. Apply the existing attachment update flow.
11. Advance the session counter after success.

The move layer should not advance the session counter on failure.

## Field-Binding Requirements

The implementation should explicitly test that a valid tag for one move fails
when any of these fields change:

- `to_scope`
- `new_attachment`
- `from_scope`
- `old_attachment`
- `device_id`
- `passport_id`
- `move_nonce`
- `session_id`
- `move_counter`

This is protocol-behavior modeling only. It is meant to expose whether DARWIN's
relocation state machine reacts correctly to proof success and failure.

## Expected Failure Behavior

Failures should be clean and observable:

- The attachment must not update.
- The move should not be recorded as successful.
- Paused relocation flow controls should remain paused where the existing
  relocation behavior already does that.
- Scenario assertions should be able to inspect a stable reason string.

Recommended failure reasons:

- `invalid_move_auth_tag`
- `missing_move_session`
- `expired_move_session`
- `revoked_device`
- `quarantined_device`
- `stale_move_counter`
- `move_contract_rejected`

## Proposed Objects

`MoveAuthMaterial`:

- A small optional object or helper output for deterministic move proof fields.
- Should be plain data.
- Should avoid production cryptography language.

`MoveAuthResult`:

- `auth_mode`
- `success`
- `reason`
- Optional `session_id`
- Optional `move_counter`

`MoveContract`:

- May grow optional auth fields.
- Should preserve existing constructor behavior for symbolic tests.

## Scenario Plan

`021_hmac_move_contract_success.yaml`:

- Register a device.
- Create a local HMAC session.
- Mark the device in transit.
- Pause lanes.
- Apply an HMAC-authenticated move contract.
- Confirm attachment updates and lanes can resume.

`022_hmac_move_contract_tamper_failure.yaml`:

- Generate proof for one destination.
- Tamper `new_attachment` or `to_scope`.
- Confirm `invalid_move_auth_tag` and unchanged attachment.

`023_hmac_move_contract_expired_session.yaml`:

- Create a local session with TTL.
- Advance simulated time past expiration.
- Confirm `expired_move_session`.

`024_hmac_move_contract_revoked_device.yaml`:

- Create a local session.
- Revoke the device or its sessions.
- Confirm `revoked_device` and unchanged attachment.

`025_symbolic_move_contract_still_works.yaml`:

- Exercise the existing symbolic move contract path.
- Confirm no HMAC fields are required.

## Test Plan

- `move_auth_material` canonical output is deterministic.
- Valid HMAC move contract updates the registry attachment.
- Tampered destination fails.
- Tampered old attachment fails.
- Wrong nonce fails.
- Wrong session ID fails.
- Stale counter fails.
- Counter advances only after success.
- Expired session fails.
- Revoked device fails.
- Quarantined device fails.
- Existing symbolic `valid=True` move contract still succeeds.
- Existing symbolic `valid=False` move contract still fails.

## Non-Goals

This planning track does not add:

- Production secure mobility.
- Real signatures.
- CA validation.
- Certificate chains.
- Passport cryptography.
- Real network handoff.
- Encrypted transport.
- Key exchange.
- Secure storage.
- Production key lifecycle.
- Distributed consensus.

## Recommended Release Language

Use:

```text
move-contract auth modeling
```

Avoid:

```text
secure handoff
signed move contract
production mobility auth
device-held cryptographic proof
```

The feature is a deterministic simulator layer for testing relocation behavior
under explicit opt-in proof checks.
