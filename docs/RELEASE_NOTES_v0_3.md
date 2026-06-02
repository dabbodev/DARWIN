# DARWIN Simulator v0.3.0 Release Notes

DARWIN v0.3.0 is a simulator-only auth bridge release. It keeps symbolic auth
as the default while adding an explicit experimental
`hmac_sha256_experimental` path for deterministic HMAC-style packet,
checkpoint, rolling-proof, and session lifecycle checks.

## What v0.3 Adds Over v0.2

- Experimental HMAC-SHA256 auth bridge helpers using Python standard-library
  `hmac`, `hashlib`, and deterministic JSON canonicalization.
- Opt-in `hmac_sha256_experimental` auth mode. Symbolic auth remains the
  default for existing scenarios.
- Deterministic packet and checkpoint HMAC support for simulator checks.
- Rolling-proof HMAC helpers for focused auth bridge tests and scenarios.
- Centralized auth mode constants in `darwin/auth/modes.py`.
- HMAC edge-case coverage for tampered checkpoint material, tampered packet
  tags, missing secrets, and rolling-proof nonce/counter mismatches.
- Session-secret lifecycle modeling with simulator-local session creation,
  rotation, expiration, stale counter rejection, revocation, and quarantine
  interaction.
- Revocation and quarantine checks that block HMAC session proof verification
  and prevent valid HMAC checkpoints from restoring blocked devices.
- Auth bridge documentation in `docs/AUTH_BRIDGE_v0_3.md`.

## Checked-In v0.3 Scenarios

- `scenarios/012_hmac_checkpoint_success.yaml`
- `scenarios/013_hmac_packet_auth_failure.yaml`
- `scenarios/014_hmac_checkpoint_tamper_failure.yaml`
- `scenarios/015_hmac_missing_secret_failure.yaml`
- `scenarios/016_hmac_rolling_proof_failure.yaml`
- `scenarios/017_hmac_session_rotation.yaml`
- `scenarios/018_hmac_session_expiration.yaml`
- `scenarios/019_hmac_revoked_session_failure.yaml`
- `scenarios/020_hmac_quarantine_blocks_checkpoint.yaml`

## Run HMAC Scenarios

```bash
python -m darwin.cli.main describe-scenario scenarios/012_hmac_checkpoint_success.yaml
python -m darwin.cli.main describe-scenario scenarios/017_hmac_session_rotation.yaml
python -m darwin.cli.main describe-scenario scenarios/020_hmac_quarantine_blocks_checkpoint.yaml
python -m darwin.cli.main run scenarios/012_hmac_checkpoint_success.yaml
python -m darwin.cli.main run scenarios/013_hmac_packet_auth_failure.yaml
python -m darwin.cli.main run scenarios/014_hmac_checkpoint_tamper_failure.yaml
python -m darwin.cli.main run scenarios/015_hmac_missing_secret_failure.yaml
python -m darwin.cli.main run scenarios/016_hmac_rolling_proof_failure.yaml
python -m darwin.cli.main run scenarios/017_hmac_session_rotation.yaml
python -m darwin.cli.main run scenarios/018_hmac_session_expiration.yaml
python -m darwin.cli.main run scenarios/019_hmac_revoked_session_failure.yaml
python -m darwin.cli.main run scenarios/020_hmac_quarantine_blocks_checkpoint.yaml
```

## Run All Scenarios

```bash
python scripts/run_all_scenarios.py
```

## Safety Limits

v0.3 remains a deterministic simulator release. It is non-production and does
not provide:

- Production cryptography.
- Key exchange.
- Secure storage.
- Public-key signatures.
- Certificate chains.
- Real networking.

Scenario secrets are test fixtures only. Do not store real secrets in DARWIN
scenario files or documentation.

## Compatibility

- Symbolic auth remains the default.
- v0.2 scenarios should still validate and pass.
- Existing scenario semantics are not changed by the HMAC auth bridge unless a
  scenario explicitly opts in with `hmac_sha256_experimental`.
