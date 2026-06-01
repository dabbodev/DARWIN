# DARWIN v0.3 Experimental Auth Bridge

This document describes the simulator-only v0.3 bridge from symbolic auth
booleans toward deterministic HMAC-style verification.

## Status

This is not production cryptography. It is only a DARWIN simulator experiment
for packets, checkpoints, and rolling proof scenarios.

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

Checkpoint scenarios can also force invalid auth with:

```yaml
auth_tag_valid: false
```

Secrets in scenarios are deterministic test fixtures only. Do not store real
secrets in DARWIN scenarios or documentation.

## Future Work

- Add explicit auth configuration objects to scenario setup if the simulator
  grows beyond per-step test fixtures.
- Model rolling proof sessions without adding key exchange or production claims.
- Expand trace exports to show auth mode and verification outcome.
