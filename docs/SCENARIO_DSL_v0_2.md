# DARWIN Scenario DSL v0.2

v0.2 adds optional built-in setup presets to reduce repeated YAML in simulator
scenarios. Presets expand to ordinary `setup` data before validation and before
the deterministic runner creates the world.

## Presets

Use presets with a top-level `use` list:

```yaml
scenario_id: 011_preset_lane_demo
name: Preset lane demo
use:
  - two_branch_network
steps:
  - action: open_lane
    source: dev_A9F3
    target: dev_B2C8
    traffic_hub: hub_1
    lane_id: lane_001
assertions:
  - type: lane_state
    traffic_hub: hub_1
    lane: lane_001
    expected: active
```

Available built-in presets:

| Preset | Purpose |
| --- | --- |
| `single_home_network` | One hybrid home hub with two common devices. |
| `two_branch_network` | Home and office registries, three traffic hubs, and home-to-office links. |
| `relocation_network` | Home and office registries with a relocation target traffic hub. |

List them from the CLI:

```powershell
python -m darwin.cli.main list-presets
```

## Expansion

Expansion is deterministic and uses plain setup data:

```powershell
python -m darwin.cli.main expand-scenario scenarios/011_preset_lane_demo.yaml
```

If PyYAML is installed, the command prints YAML. Otherwise it prints JSON.

## Merge Rules

Explicit scenario setup extends preset setup. For these list-based sections,
entries with the same key replace preset entries:

| Section | Merge key |
| --- | --- |
| `devices` | `device_id` |
| `registry_hubs` | `hub_id` |
| `traffic_hubs` | `hub_id` |
| `hybrid_hubs` | `hub_id` |
| `links` | `from`, `to` |

Example override:

```yaml
use:
  - two_branch_network
setup:
  devices:
    - device_id: dev_A9F3
      label: tablet
      registry_hub: registry_home
      traffic_hub: hub_1
```

`dev_A9F3` keeps the preset placement but uses the explicit device entry.

Unknown preset names fail validation at `use[n]`. Existing scenarios that do
not use presets remain valid and run through the same setup path as before.

## Library Metadata

Scenarios can include optional top-level metadata for discovery and generated
documentation:

```yaml
category: relocation
description: Pauses a lane during relocation and resumes it on the new route.
tags:
  - relocation
  - lane
demonstrates:
  - Lane pause and resume behavior during relocation.
expected_result: The lane returns to active state.
```

Supported categories are `registry`, `traffic`, `lane`, `relocation`,
`security`, `metrics`, `preset`, and `visualization`. Unknown categories warn
during validation instead of failing.

List scenario metadata from the CLI:

```powershell
python -m darwin.cli.main list-scenarios
```

Describe one scenario:

```powershell
python -m darwin.cli.main describe-scenario scenarios/004_relocation_pause_resume.yaml
```

Generate the Markdown index:

```powershell
python -m darwin.cli.main scenario-index
```

## v0.3 Auth Bridge Scenarios

The v0.3 auth bridge adds simulator-only HMAC scenarios without changing v0.2
scenario semantics. Symbolic auth remains the default; HMAC checks require
explicit `auth_mode: hmac_sha256_experimental` in the scenario step.

Checked-in auth bridge scenarios:

- `scenarios/012_hmac_checkpoint_success.yaml`
- `scenarios/013_hmac_packet_auth_failure.yaml`
- `scenarios/014_hmac_checkpoint_tamper_failure.yaml`
- `scenarios/015_hmac_missing_secret_failure.yaml`
- `scenarios/016_hmac_rolling_proof_failure.yaml`
- `scenarios/017_hmac_session_rotation.yaml`
- `scenarios/018_hmac_session_expiration.yaml`
- `scenarios/019_hmac_revoked_session_failure.yaml`
- `scenarios/020_hmac_quarantine_blocks_checkpoint.yaml`

Together, scenarios `012` through `020` cover packet and checkpoint HMAC
success/failure paths, HMAC edge cases, session-secret lifecycle behavior,
rotation, expiration, stale counter rejection, and revocation/quarantine
interaction.

## v0.4 Move-Contract Auth Scenarios

The v0.4 move-contract auth slice extends `move_device` with explicit,
simulator-only HMAC fields. Missing `auth_mode` remains symbolic.

Supported HMAC `move_device` fields:

- `auth_mode: hmac_sha256_experimental`
- `session_id`
- `auth_secret`
- `move_nonce`
- `move_counter`
- `move_auth_tag`
- `tamper_move_auth_tag`
- `tamper_to_scope`
- `tamper_new_attachment`
- `tamper_old_attachment`

Additional assertions for move-contract scenarios:

- `move_recorded`
- `latest_step_reason`

Checked-in move-contract auth scenarios:

- `scenarios/021_hmac_move_contract_success.yaml`
- `scenarios/022_hmac_move_contract_tamper_failure.yaml`
- `scenarios/023_hmac_move_contract_expired_session.yaml`
- `scenarios/024_hmac_move_contract_revoked_device.yaml`
- `scenarios/025_symbolic_move_contract_still_works.yaml`

## v0.5 Direct Alias Scenarios

The v0.5 alias registry slice adds direct alias scenario support. Alias steps
call the direct registry helpers and do not change canonical identity,
TrafficHub routing, progressive fallback, bundles/zones, DNS-style behavior, or
service aliases.

Supported alias actions:

- `claim_alias`
  - Required: `registry_hub`, `alias`, `target_device`
  - Optional: `requested_by_device`, `alias_type`, `visibility`, `ttl`
- `resolve_alias`
  - Required: `registry_hub`, `alias`
- `release_alias`
  - Required: `registry_hub`, `alias`
  - Optional: `requested_by_device`

Supported alias assertions:

- `alias_resolves_to`
  - Required: `registry_hub`, `alias`, `device`
  - Optional: `identity_chain`
- `alias_status`
  - Required: `registry_hub`, `alias`, `expected`
- `alias_not_resolved`
  - Required: `registry_hub`, `alias`
- `canonical_identity_unchanged`
  - Required: `registry_hub`, `device`, `expected_identity_chain`

Checked-in direct alias scenario:

- `scenarios/026_alias_claim_success.yaml`
