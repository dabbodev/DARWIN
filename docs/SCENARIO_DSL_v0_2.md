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

## v0.5 Alias Scenarios

The v0.5 alias registry slices add direct alias, basic progressive fallback,
minimal alias bundle, and DNS-style public alias bundle scenario support. Alias
steps call registry helpers and do not change canonical identity, TrafficHub
routing, real DNS behavior, or service aliases.

Supported alias actions:

- `claim_alias`
  - Required: `registry_hub`, `alias`, `target_device`
  - Optional: `requested_by_device`, `alias_type`, `visibility`, `ttl`
- `create_alias_bundle`
  - Required: `registry_hub`, `bundle_path`
  - Optional: `delegated_to_registry_hub`, `bundle_type`, `visibility`,
    `allowed_record_types`, `created_by_device`
- `claim_bundle_alias`
  - Required: `registry_hub`, `bundle_path`, `child_name`, `target_device`
  - Optional: `requested_by_device`, `alias_type`, `visibility`, `ttl`
- `claim_progressive_alias`
  - Required: `registry_hub`, `requested_alias`, `local_name`, `target_device`
  - Optional: `requested_by_device`, `fallback_allowed`, `visibility`, `ttl`
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
- `alias_bundle_status`
  - Required: `registry_hub`, `bundle_path`, `expected`
- `bundle_alias_resolves_to`
  - Required: `registry_hub`, `bundle_path`, `child_name`, `device`
  - Optional: `identity_chain`
- `alias_granted_as`
  - Required: `registry_hub`, `requested_alias`, `granted_alias`
- `alias_authority_ceiling`
  - Required: `registry_hub`, `alias`, `expected`
- `alias_not_resolved`
  - Required: `registry_hub`, `alias`
- `canonical_identity_unchanged`
  - Required: `registry_hub`, `device`, `expected_identity_chain`

Alias conflict checks use existing `latest_step_status`,
`latest_step_reason`, and `conflict_exists` assertions. Released aliases remain
in the RegistryHub alias table with `status: released`, but `resolve_alias`
returns `alias_not_active` and no active target.

Minimal alias bundle checks use `latest_step_status` and
`latest_step_reason` for result validation. Duplicate active bundles fail with
`bundle_conflict`; child claims under missing bundles fail with
`bundle_not_found`; child claims under inactive bundles fail with
`bundle_not_active`; child alias name conflicts fail with `alias_conflict`.
Child bundle aliases are stored as normal `AliasRecord` entries and resolve
through `resolve_alias`.

DNS-style public alias bundles use the same simulator-local bundle and direct
alias mechanics. They are not DNS, do not call a registrar, do not model a
public CA, do not prove production identity, and do not perform real network
lookup.

```yaml
steps:
  - action: create_alias_bundle
    registry_hub: hub_gov_001
    bundle_path: global.us.gov.ca
    bundle_type: dns_style_alias_zone
    visibility: public
    allowed_record_types:
      - device_alias
  - action: claim_bundle_alias
    registry_hub: hub_gov_001
    bundle_path: global.us.gov.ca
    child_name: website
    target_device: dev_CA_WEBSITE
    visibility: public
  - action: resolve_alias
    registry_hub: hub_gov_001
    alias: global.us.gov.ca.website
```

## v0.6 Alias Authority-Chain Scenarios

The v0.6 alias authority-chain slice adds simulator-only scenario support for
claiming an alias through explicit `RegistryHub.parent_hub_id` traversal. It
does not implement real DNS, registrar integration, public CA behavior,
production identity proof, external authority services, TrafficHub routing
changes, or canonical identity rewrites.

Supported authority-chain action:

- `claim_alias_through_authority_chain`
  - Required: `registry_hub`, `requested_alias`, `local_name`, `target_device`
  - Optional: `requested_by_device`, `fallback_allowed`, `visibility`, `ttl`

The action calls the simulator helper
`claim_alias_through_authority_chain(...)`, appends the structured result to
`world.action_results`, and logs either `alias_authority_chain_claimed` or
`alias_authority_chain_failed`. Event data includes requested and granted
alias, target device, success, status, reason, authority ceiling, final path
status, decision count, path hubs, and JSON-safe authority decisions.

Supported authority-chain assertion:

- `alias_authority_path_summary`
  - Required: `requested_alias`
  - Optional expected fields: `final_status`, `granted_alias`,
    `authority_ceiling`, `decision_count`, `path_hubs`

The assertion finds the latest action result with an `authority_path` matching
`requested_alias` and compares only the optional fields supplied in the
assertion. This makes it suitable for both successful claims and failure paths
where no alias record exists.

Detailed snapshots include a compact top-level `alias_authority_claims` list
for action results that expose an authority path. Each entry records requested
alias, granted alias, status, reason, success, authority ceiling, and an
authority path summary with final status, decision count, and path hubs.

Simulator-local policy can be configured on `registry_hubs` and `hybrid_hubs`
with `alias_authority_policy`. Empty policy preserves default behavior.
Supported keys are:

- `allow_approval`, default `true`
- `allow_pass_up`, default `true`
- `allow_fallback`, default `true`

Example:

```yaml
setup:
  registry_hubs:
    - hub_id: registry_family_001
      scope_path: global.family.david
      parent_hub_id: registry_global_001
      alias_authority_policy:
        allow_pass_up: false
        allow_fallback: true
steps:
  - action: claim_alias_through_authority_chain
    registry_hub: registry_home_001
    requested_alias: global.server
    local_name: server
    target_device: dev_A9F3
assertions:
  - type: alias_authority_path_summary
    requested_alias: global.server
    final_status: fallback_granted
    granted_alias: global.family.david.server
    authority_ceiling: global.family.david
    decision_count: 2
    path_hubs:
      - registry_home_001
      - registry_family_001
```

For the basic progressive fallback slice, a RegistryHub can grant aliases only
inside its own `scope_path`. If a requested alias is above that scope and
`fallback_allowed` is true, the granted alias is:

```text
registry_hub.scope_path + "." + local_name
```

The progressive result status is `fallback_granted`, the reason is
`insufficient_authority`, and the granted active `AliasRecord` stores the
requested alias, granted alias, fallback reason, and authority ceiling.

Checked-in alias scenarios:

- `scenarios/026_alias_claim_success.yaml`
- `scenarios/027_alias_claim_conflict.yaml`
- `scenarios/028_alias_release_blocks_resolution.yaml`
- `scenarios/029_progressive_alias_fallback.yaml`
- `scenarios/030_alias_bundle_delegation.yaml`
- `scenarios/031_dns_style_alias_bundle.yaml`
