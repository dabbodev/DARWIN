# DARWIN Scenario Index

Scenarios are deterministic, support presets through `use`, and are simulator-only.

| Scenario | Category | Description | Tags |
| --- | --- | --- | --- |
| `001_basic_registration` - Basic registration | registry | Registers one device, resolves its label, and confirms the registry event. | `registration`, `label`, `checkpoint` |
| `002_name_conflict` - Name conflict | registry | Registers two devices with the same label and records the deterministic conflict handling. | `registration`, `label-conflict`, `conflict` |
| `003_lane_open_and_send` - Lane open and send | lane | Opens a logical lane across traffic hubs and sends one payload. | `lane`, `traffic`, `sequence` |
| `004_relocation_pause_resume` - Relocation pause and resume | relocation | Pauses a lane during relocation, moves the target device, and resumes traffic on the new route. | `relocation`, `lane`, `flow-control` |
| `005_relocation_timeout` - Relocation timeout keeps lane held | relocation | Expires a relocation hold and verifies that traffic remains paused after timeout. | `relocation`, `timeout`, `flow-control` |
| `006_mac_spoof_symbolic_failure` - Symbolic spoof failure | security | Rejects an invalid symbolic rolling proof and quarantines the device. | `symbolic-trust`, `spoofing`, `quarantine` |
| `007_congestion_bridge_recommendation` - Congestion bridge recommendation | metrics | Records sustained cross-tree traffic and proposes a traffic bridge recommendation. | `metrics`, `recommendation`, `cross-tree-traffic` |
| `008_invalid_move_contract` - Invalid move contract keeps relocation paused | relocation | Rejects an invalid move contract and keeps relocation flow control active. | `relocation`, `move-contract`, `validation` |
| `009_duplicate_device_claim` - Duplicate device claim during relocation | security | Simulates a duplicate device claim while relocation is paused. | `relocation`, `duplicate-device`, `conflict` |
| `010_unreachable_relocation_resume` - Unreachable relocation resume keeps flow control | relocation | Attempts to resume relocation traffic when the moved target has no reachable route. | `relocation`, `routing`, `flow-control` |
| `011_preset_lane_demo` - Preset lane demo | preset | Uses a built-in two-branch setup preset to open a lane with minimal YAML. | `preset`, `lane`, `two-branch-network` |
| `012_hmac_checkpoint_success` - HMAC checkpoint success | security | Records a test-only HMAC-authenticated checkpoint. | `hmac`, `checkpoint`, `simulator-only` |
| `013_hmac_packet_auth_failure` - HMAC packet auth failure | security | Rejects a lane packet with a tampered test-only HMAC tag. | `hmac`, `packet-auth`, `simulator-only` |
| `014_hmac_checkpoint_tamper_failure` - HMAC checkpoint tamper failure | security | Rejects a checkpoint whose payload is changed after a test-only HMAC tag is created. | `hmac`, `checkpoint`, `tamper`, `simulator-only` |
| `015_hmac_missing_secret_failure` - HMAC missing secret failure | security | Rejects an HMAC-mode lane packet when no simulator test secret is supplied. | `hmac`, `packet-auth`, `missing-secret`, `simulator-only` |
| `016_hmac_rolling_proof_failure` - HMAC rolling proof failure | security | Rejects test-only HMAC rolling proofs when nonce or counter material changes after tag creation. | `hmac`, `rolling-proof`, `quarantine`, `simulator-only` |
| `017_hmac_session_rotation` - HMAC session rotation | security | Rotates a simulator-local HMAC session secret and rejects proof material signed with the old secret. | `hmac`, `session`, `rotation`, `simulator-only` |
| `018_hmac_session_expiration` - HMAC session expiration | security | Expires a simulator-local HMAC session using integer simulated time and blocks proof verification. | `hmac`, `session`, `expiration`, `simulator-only` |
| `019_hmac_revoked_session_failure` - HMAC revoked session failure | security | Revokes a simulator-local HMAC session and rejects later rolling proof verification. | `hmac`, `session`, `revocation`, `simulator-only` |
| `020_hmac_quarantine_blocks_checkpoint` - HMAC quarantine blocks checkpoint | security | Quarantines a registered device and rejects a later valid HMAC checkpoint that tries to restore online state. | `hmac`, `checkpoint`, `quarantine`, `simulator-only` |
| `021_hmac_move_contract_success` - HMAC move contract success | relocation | Applies an opt-in simulator-only HMAC-authenticated move contract and updates attachment state. | `relocation`, `move-contract`, `hmac`, `simulator-only` |
| `022_hmac_move_contract_tamper_failure` - HMAC move contract tamper failure | security | Computes a valid move auth tag, tampers the destination attachment, and rejects the move. | `relocation`, `move-contract`, `hmac`, `tamper`, `simulator-only` |
| `023_hmac_move_contract_expired_session` - HMAC move contract expired session | security | Expires a simulator-local move auth session before applying an HMAC move contract. | `relocation`, `move-contract`, `hmac`, `session`, `expiration`, `simulator-only` |
| `024_hmac_move_contract_revoked_device` - HMAC move contract revoked device | security | Revokes a registered device before applying an otherwise valid HMAC move contract. | `relocation`, `move-contract`, `hmac`, `revocation`, `simulator-only` |
| `025_symbolic_move_contract_still_works` - Symbolic move contract still works | relocation | Applies the default symbolic move contract path without HMAC session fields. | `relocation`, `move-contract`, `symbolic` |
| `026_alias_claim_success` - Alias claim success | registry | direct alias claim and resolution for a registered device | `alias`, `registry`, `direct_alias` |
| `027_alias_claim_conflict` - Alias claim conflict | registry | direct alias conflict preserves the original alias owner | `alias`, `conflict`, `registry` |
| `028_alias_release_blocks_resolution` - Alias release blocks resolution | registry | released aliases are retained but inactive and no longer resolve | `alias`, `release`, `registry` |
| `029_progressive_alias_fallback` - Progressive alias fallback | registry | progressive alias request falls back to the highest locally authorized scope | `alias`, `progressive_alias`, `fallback`, `registry` |
| `030_alias_bundle_delegation` - Alias bundle delegation | registry | delegated alias bundle creates a child alias for a registered device | `alias`, `bundle`, `delegation`, `registry` |
| `031_dns_style_alias_bundle` - DNS-style alias bundle | registry | DNS-style public alias bundle modeled as a simulator-only delegated alias zone | `alias`, `bundle`, `dns_style`, `public_alias`, `registry` |
| `032_alias_authority_chain_success` - Alias authority-chain success | registry | low-level registry request climbs through explicit parents and is approved by the global hub | `alias`, `alias_authority_chain`, `registry` |
| `033_alias_authority_chain_fallback` - Alias authority-chain fallback | registry | parent policy stops pass-up and grants the highest allowed fallback alias | `alias`, `alias_authority_chain`, `fallback`, `registry` |
| `034_alias_authority_chain_name_taken` - Alias authority-chain name taken | registry | high-scope alias conflict is reported without overwriting the original owner | `alias`, `alias_authority_chain`, `conflict`, `registry` |
| `035_alias_authority_chain_policy_denied` - Alias authority-chain policy denied | registry | parent policy denies pass-up and fallback, producing a rejected claim without creating aliases | `alias`, `alias_authority_chain`, `policy`, `registry` |
| `036_alias_authority_chain_broken_parent` - Alias authority-chain broken parent | registry | parent-chain traversal fails because the configured parent hub is missing | `alias`, `alias_authority_chain`, `authority_path_broken`, `registry` |
| `037_registry_history_alias_claim` - Registry history alias claim | registry | read-only alias history assertions observe a retained direct alias claim and release | `alias`, `registry_history`, `v0.7` |
| `038_registry_history_alias_conflict` - Registry history alias conflict | registry | read-only alias conflict history assertions observe a direct alias conflict | `alias`, `conflict`, `registry_history`, `v0.7` |
| `039_authority_audit_trace_success` - Authority audit trace success | registry | retained authority audit trace assertions observe a successful parent-approved alias claim | `alias`, `alias_authority_chain`, `authority_audit`, `v0.7` |
| `040_authority_audit_trace_fallback` - Authority audit trace fallback | registry | retained authority audit trace assertions observe a simulator-local fallback grant | `alias`, `alias_authority_chain`, `authority_audit`, `fallback`, `v0.7` |
| `041_trace_explainability_denials` - Trace explainability denials | registry | scenario-run-only in-memory authority path explanation covers a simulator-local policy denial | `alias`, `alias_authority_chain`, `trace_explainability`, `policy`, `v0.7` |
