# DARWIN v0.4 Move-Contract Auth Planning

This document proposes how DARWIN can model authenticated move contracts in
v0.4 while staying simulator-only and non-production.

The key recommendation is to treat move-contract auth as an opt-in extension
of the v0.3 HMAC bridge. Symbolic move contracts remain the default behavior.

## Status

Planning plus unit-level policy helper slices. The simulator now has
deterministic move-contract HMAC helper functions and a
`verify_move_contract_auth(registry_hub, move_contract)` policy helper in
`darwin/auth/move_contract.py`.

The policy helper verifies symbolic or experimental HMAC move-contract auth and
advances the local session counter only after successful HMAC verification. It
is not wired into `update_attachment_after_move()` yet, so relocation behavior
and scenario semantics remain unchanged in this slice.

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

## Verification Policy

`verify_move_contract_auth(registry_hub, move_contract)` returns
`MoveAuthVerificationResult`:

- `success`
- `status`
- `reason`
- `auth_mode`
- `session_id`
- `move_counter`

For missing `auth_mode` or `auth_mode: symbolic`, the helper preserves the
existing symbolic contract meaning:

- `valid: true` succeeds.
- `valid: false` fails with `symbolic_move_invalid`.
- No session fields are required.

For `auth_mode: hmac_sha256_experimental`, the helper:

1. Requires `session_id`, `move_nonce`, `move_counter`, and `move_auth_tag`.
2. Locates `session_id` in `RegistryHub.local_sessions`.
3. Requires the session state to be `active`.
4. Requires the session device ID to match `move_contract.device_id`.
5. Rejects registered local devices whose state is `quarantined` or `revoked`.
6. Requires `move_counter` to be strictly greater than
   `session.current_counter`.
7. Builds deterministic move proof material from the contract fields.
8. Verifies `move_auth_tag` using the session secret.
9. Advances `session.current_counter` to `move_counter` only after success.

The helper does not apply attachment updates, record moves, resume relocation,
or alter relocation flow controls.

## Failure Reasons

Stable failure reasons for this slice:

- `missing_move_session`
- `missing_move_auth_fields`
- `move_session_not_found`
- `move_session_inactive`
- `move_session_device_mismatch`
- `device_quarantined`
- `device_revoked`
- `stale_move_counter`
- `invalid_move_auth_tag`
- `symbolic_move_invalid`

Unknown non-symbolic auth modes are rejected with
`unsupported_move_auth_mode`.

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

## Session and Counter Behavior

Session states:

- `active` can succeed if all other checks pass.
- `expired`, `revoked`, `quarantined`, `rotated`, or any other non-active state
  fails with `move_session_inactive`.
- If the registered local device is already `quarantined` or `revoked`, the
  helper returns the device-specific reason before evaluating counter freshness
  or the HMAC tag.

Counter freshness:

- If `session.current_counter == 5`, `move_counter == 6` succeeds and advances
  the session counter to `6`.
- `move_counter == 5` fails with `stale_move_counter`.
- `move_counter == 4` fails with `stale_move_counter`.
- Failed verification never advances the counter.
- Re-verifying the same successful HMAC contract fails as stale because the
  first verification already advanced the counter.

## Proposed Objects

`MoveAuthMaterial`:

- A small optional object or helper output for deterministic move proof fields.
- Should be plain data.
- Should avoid production cryptography language.

`MoveAuthVerificationResult`:

- `success`
- `status`
- `reason`
- `auth_mode`
- `session_id`
- `move_counter`

`MoveContract`:

- May grow optional auth fields.
- Should preserve existing constructor behavior for symbolic tests.

## Future Scenario Plan

These are deferred until relocation integration is wired:

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
- Confirm `move_session_inactive`.

`024_hmac_move_contract_revoked_device.yaml`:

- Create a local session.
- Revoke the device or its sessions.
- Confirm `device_revoked` or `move_session_inactive`, depending on whether the
  future integration checks registered device state before session state.

`025_symbolic_move_contract_still_works.yaml`:

- Exercise the existing symbolic move contract path.
- Confirm no HMAC fields are required.

## Current Policy Test Plan

- `move_auth_material` canonical output is deterministic.
- Symbolic move contracts with `valid: true` pass without session fields.
- Symbolic move contracts with `valid: false` fail with `symbolic_move_invalid`.
- Valid HMAC move auth succeeds for an active matching session.
- Tampered destination fails.
- Tampered old attachment fails.
- Wrong nonce fails.
- Wrong session ID fails.
- Stale counter fails.
- Counter advances only after success.
- Expired or otherwise inactive session fails with `move_session_inactive`.
- Revoked registered device fails with `device_revoked`.
- Quarantined registered device fails with `device_quarantined`.
- Failed verification does not update attachments, record moves, or advance
  counters.

## Future Integration Test Plan

After relocation integration is wired, add tests that prove a verified HMAC move
contract can update registry attachment state and that failed HMAC verification
keeps attachments, recorded moves, paused lanes, and relocation flow controls in
their existing failure-safe states.

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
