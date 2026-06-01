# DARWIN v0.3 Release Notes Draft

DARWIN v0.3 adds a simulator-only experimental auth bridge over v0.2. Symbolic
auth remains the default, and HMAC behavior is available only through explicit
`hmac_sha256_experimental` scenario fields and focused tests.

## What v0.3 Adds Over v0.2

- Experimental HMAC-SHA256 helper functions using Python standard-library
  modules.
- Deterministic packet and checkpoint HMAC material for simulator checks.
- A rolling-proof HMAC helper for focused auth bridge tests.
- Centralized auth mode constants in `darwin/auth/modes.py`.
- Scenario `012_hmac_checkpoint_success`, which records a valid
  HMAC-authenticated checkpoint.
- Scenario `013_hmac_packet_auth_failure`, which rejects a tampered
  HMAC-authenticated lane packet.
- Auth bridge documentation in `docs/AUTH_BRIDGE_v0_3.md`.

## Run HMAC Scenarios

```bash
python -m darwin.cli.main describe-scenario scenarios/012_hmac_checkpoint_success.yaml
python -m darwin.cli.main describe-scenario scenarios/013_hmac_packet_auth_failure.yaml
python -m darwin.cli.main run scenarios/012_hmac_checkpoint_success.yaml
python -m darwin.cli.main run scenarios/013_hmac_packet_auth_failure.yaml
```

## Run All Scenarios

```bash
python scripts/run_all_scenarios.py
```

## Safety Limits

v0.3 remains a deterministic simulator release. It does not provide:

- Production cryptography.
- Key exchange.
- Secure storage.
- Certificate chains.
- Real networking.

Scenario secrets are test fixtures only. Do not store real secrets in DARWIN
scenario files or documentation.

## Compatibility

- Symbolic auth remains the default.
- v0.2 scenarios should still validate and pass.
- Existing scenario semantics are not changed by the HMAC auth bridge unless a
  scenario explicitly opts in with `hmac_sha256_experimental`.
