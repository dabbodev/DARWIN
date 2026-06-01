# DARWIN v0.3 Roadmap

DARWIN v0.3 is the simulator-only auth bridge track. It keeps symbolic auth as
the default and uses the explicit `hmac_sha256_experimental` mode only where a
scenario or focused test opts in.

## Completed So Far

- HMAC helper functions using Python standard-library `hmac`, `hashlib`, and
  deterministic JSON canonicalization.
- Packet and checkpoint HMAC verification paths behind opt-in
  `hmac_sha256_experimental` mode.
- Rolling proof HMAC helper for deterministic simulator tests.
- Scenario `012_hmac_checkpoint_success`.
- Scenario `013_hmac_packet_auth_failure`.
- Auth bridge documentation and audit pass.

## Remaining Candidates

- More HMAC edge-case scenarios, including missing secrets, missing tags,
  mismatched payload material, and checkpoint rejection paths.
- Session-secret lifecycle modeling.
- Key rotation simulation.
- Revocation interaction with HMAC mode.
- HMAC move-contract proof modeling, still simulator-only.
- v0.3 release cleanup, including final checklist pass, release notes, version
  bump decision, tag decision, and merge planning.

## Release Guardrails

- Do not replace symbolic auth as the default.
- Do not add production cryptography claims.
- Do not add key exchange, secure storage, certificate chains, or real
  networking as part of v0.3.
- Do not bump the package version to `0.3.0` until final release cleanup.
