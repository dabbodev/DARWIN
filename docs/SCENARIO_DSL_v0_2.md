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
changes, or canonical identity rewrites. v0.6.0 is released on `main`; the
annotated tag and GitHub release exist, no package publication was performed,
and the CLI version reports `darwin-sim 0.6.0`.

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
This policy only affects authority-chain helper behavior in the simulator. It
is not registrar policy, DNS policy, CA policy, production identity proof, or
an external authority service.
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

Checked-in v0.6 authority-chain scenarios:

- `scenarios/032_alias_authority_chain_success.yaml`
- `scenarios/033_alias_authority_chain_fallback.yaml`
- `scenarios/034_alias_authority_chain_name_taken.yaml`
- `scenarios/035_alias_authority_chain_policy_denied.yaml`
- `scenarios/036_alias_authority_chain_broken_parent.yaml`

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

## v0.7 Registry History and Trace Assertions

The v0.7 released slice adds read-only scenario
assertions over existing RegistryHub state, retained authority grant
provenance, and scenario-run in-memory authority path summaries. These
assertions do not add new scenario actions, mutate simulator state, change
alias outcomes, alter TrafficHub routing, rewrite canonical identity, or add
persistent failed-path storage. v0.7.0 is released on `main`; the annotated
`v0.7.0` tag and GitHub release exist, no package publication was performed,
and the CLI version reports `darwin-sim 0.7.0`.

Supported v0.7 assertions:

- `alias_history_contains`
  - Required: `registry_hub`
  - Optional filters: `alias`, `device_id`, `status`
  - Optional count checks: `expected_count`, `min_count`
- `alias_conflict_history_contains`
  - Required: `registry_hub`
  - Optional filters: `alias`, `device_id`
  - Optional count checks: `expected_count`, `min_count`
- `authority_audit_trace_contains`
  - Required: `registry_hub`
  - Optional filters: `requested_alias`, `granted_alias`, `device_id`,
    `final_status`
  - Optional explanation checks: `outcome`, `summary_contains`
  - Optional count checks: `expected_count`, `min_count`
- `quarantine_history_contains`
  - Required: `registry_hub`
  - Optional filters: `device_id`, `reason`
  - Optional count checks: `expected_count`, `min_count`

If neither `expected_count` nor `min_count` is supplied, the assertion passes
when at least one matching record exists. When `expected_count` is supplied,
the count must match exactly. When `min_count` is supplied, the count must be
at least that value. Count fields must be non-negative integers. Failed
count-style assertion output includes the requested filters, matching record
count, matching records, and whether the referenced `registry_hub` existed in
the scenario world.

`authority_audit_trace_contains` validates retained RegistryHub grant traces
from `build_authority_audit_trace(...)`. For failed authority outcomes in the
same scenario run, it can also explain the in-memory `AliasAuthorityPath`
summary still attached to the action result. Assertion output identifies this
as `in_memory_authority_path`; it is not persistent failed-path audit storage.

Retained-data limits remain important: RegistryHub retains terminal grant
provenance, not full failed authority-chain paths. Failed paths are explainable
only while the runner still has the in-memory action result or a summary
derived from it.

Checked-in v0.7 scenarios:

- `scenarios/037_registry_history_alias_claim.yaml`
- `scenarios/038_registry_history_alias_conflict.yaml`
- `scenarios/039_authority_audit_trace_success.yaml`
- `scenarios/040_authority_audit_trace_fallback.yaml`
- `scenarios/041_trace_explainability_denials.yaml`

## v0.8 Retained Authority Outcome Assertions

The v0.8 slice is released on `main`; the current package and CLI version
report `darwin-sim 0.8.0`. It
adds simulator-local retention and read-only scenario assertions for
authority-chain outcome records. These assertions validate compact records
retained in:

```python
RegistryHub.authority_outcome_history
```

Authority outcome records are retained on the starting/requesting
`RegistryHub`, not copied to every hub in the authority path. Successful and
fallback grants may still create aliases at the approving authority hub; the
new assertion reads the retained outcome record from the requesting hub.

Supported v0.8 assertion:

- `authority_outcome_history_contains`
  - Required: `registry_hub`
  - Optional filters: `requested_alias`, `granted_alias`, `device_id`,
    `requesting_hub`, `final_status`, `status`, `reason`,
    `authority_ceiling`, `fallback_used`, `conflict_detected`,
    `policy_denied`, `path_broken`
  - Optional count checks: `expected_count`, `min_count`

The assertion uses `query_authority_outcomes(...)` and applies only supplied
filters. If neither `expected_count` nor `min_count` is supplied, it passes
when at least one matching retained outcome exists. `expected_count` requires
an exact match count. `min_count` requires at least that many matches. Count
fields must be non-negative integers. Boolean marker filters must be YAML
booleans, such as `true` or `false`.

Example:

```yaml
assertions:
  - type: authority_outcome_history_contains
    registry_hub: registry_home_001
    requested_alias: global.server
    granted_alias: global.server
    device_id: dev_A9F3
    requesting_hub: registry_home_001
    final_status: approved_here
    status: claimed
    authority_ceiling: global
    fallback_used: false
    expected_count: 1
```

Failure output follows the existing count-style assertion diagnostics: expected
filters and count requirements are reported alongside the matching retained
record count, matching records, and whether the referenced `registry_hub`
existed in the scenario world.

Checked-in v0.8 authority outcome scenarios:

- `scenarios/042_authority_outcome_history_success.yaml`
- `scenarios/043_authority_outcome_history_denials.yaml`

The checked-in scenario set currently covers `001` through `043`, with
scenarios `042` and `043` marked as v0.8 scenarios.

These are simulator-local retained-record assertions only. They are not
production audit or compliance guarantees, do not add scenario actions, and do
not change alias claim, release, resolution, conflict, denial, quarantine,
fallback, authority-chain, TrafficHub routing, or canonical identity behavior.

Detailed snapshots also include retained authority outcome summaries under
each `RegistryHub` at `authority_outcome_history`. The entries use the same
compact JSON-safe summary fields as the retained records and preserve append
order on the requesting hub. Existing JSON snapshot and scenario-result
exports include this field because they write the final detailed snapshot.
Compact `world.snapshot()` output remains an ID-only overview and does not
include retained outcome history.
