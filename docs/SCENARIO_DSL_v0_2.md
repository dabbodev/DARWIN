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
`security`, `metrics`, `mailbox`, `encryption`, `stream_offer`, `preset`, and
`visualization`. Unknown categories warn during validation instead of failing.

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

The v0.8 scenario slice added scenarios `042` and `043` for retained
authority outcome assertions.

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

## v0.9 Mailbox Message Delivery Scenarios

The v0.9 release is available on `main` as `darwin-sim 0.9.0`. It adds
simulator-local scenario actions and assertions for
toy in-memory mailbox message delivery. These actions call the existing v0.9
helper modules for lane definitions, mailbox registration, adapter endpoint
records, and message delivery results.

This DSL surface remains simulator-only. It does not add real networking,
sockets, HTTP/WebSocket clients or servers, DNS lookup, registrar integration,
public CA behavior, external services, production chat behavior, production
encryption or E2EE, production identity proof, durable queues, retry workers,
TrafficHub routing changes, canonical identity rewrites, or alias/authority
behavior changes.

Supported v0.9 mailbox delivery actions:

- `register_lane_definition`
  - Required: `registry_hub`, `lane_signature`
  - Optional: `scope`, `description`, `visibility_tier`, `status`,
    `payload_kind`, `schema_ref`, `protocol_ref`, `adapter_kinds`,
    `fallback_policy`
  - `basic_messaging:v1` uses the deterministic basic messaging lane
    definition before applying supplied overrides.
- `register_mailbox`
  - Required: `registry_hub`, `mailbox_id`, `canonical_device_id`,
    `local_name`, `scope`
  - Optional: `resource`, `address`, `metadata`
  - If `address` is omitted, the runner formats
    `darwin://{scope}.{local_name}/{resource}` with `resource: inbox` by
    default.
- `bind_mailbox_capability`
  - Required: `registry_hub`, `mailbox_id`, `lane_signature`
  - Optional: `capability_id`, `direction`, `enabled`, `metadata`
  - The lane signature must already be registered on the referenced
    `RegistryHub`.
- `register_adapter_endpoint`
  - Required: `registry_hub`, `endpoint_id`, `subject_id`, `subject_kind`,
    `adapter_kind`
  - Optional: `status`, `lane_signatures`, `scope`, `host_hint`, `port_hint`,
    `path_hint`, `metadata`
  - Successful in-memory delivery uses `subject_kind: mailbox`,
    `adapter_kind: in_memory`, `status: available`, and a matching lane
    signature.
- `deliver_message`
  - Required: `registry_hub`, `message_id`, `sender_id`,
    `recipient_address`
  - Optional: `lane_signature` defaulting to `basic_messaging:v1`,
    `payload_kind` defaulting to `text`, `payload`, `metadata`
  - The action builds a `MessageEnvelope`, calls
    `deliver_message_to_mailbox(...)`, retains the result, and logs a
    simulator event. It never performs network I/O.

Supported v0.9 mailbox delivery assertions:

- `mailbox_registered`
  - Required: `registry_hub`, `mailbox_id`
  - Optional checks: `address`, `canonical_device_id`, `scope`
- `mailbox_supports_lane`
  - Required: `registry_hub`, `mailbox_id`, `lane_signature`
  - Optional check: `enabled`
- `message_delivery_result_contains`
  - Required: `registry_hub`
  - Optional filters: `message_id`, `recipient_address`, `mailbox_id`,
    `status`, `reason`, `lane_signature`, `endpoint_id`, `fallback_action`
  - Optional count checks: `expected_count`, `min_count`
- `mailbox_inbox_contains`
  - Required: `registry_hub`, `mailbox_id`
  - Optional filters: `message_id`, `sender_id`, `recipient_address`,
    `lane_signature`, `payload_kind`, `payload`
  - Optional count checks: `expected_count`, `min_count`

If neither `expected_count` nor `min_count` is supplied, count-style
assertions pass when at least one matching record exists. `expected_count`
requires an exact match count. `min_count` requires at least that many matches.
Count fields must be non-negative integers.

Checked-in v0.9 mailbox delivery scenarios:

- `scenarios/044_mailbox_basic_message_delivery.yaml`
- `scenarios/045_mailbox_delivery_failures.yaml`
- `scenarios/046_mailbox_delivery_fallback_policy.yaml`

The v0.9 released scenario set covers `001` through `046`, with scenarios
`044` through `046` covering v0.9 mailbox delivery behavior.

## v1.0 Symbolic Encryption Registry and Policy Scenarios

The v1.0.0 release on `main` reports package and CLI version
`darwin-sim 1.0.0`. It adds scenario DSL coverage
for symbolic encryption registry records and mailbox encryption policy
decisions. This is
simulator-only policy validation. It is not real cryptography, key generation,
encryption, decryption, production E2EE, secure messaging, networking, or
delivery enforcement.

Supported v1.0 symbolic encryption actions:

- `register_encryption_identity`
  - Required: `registry_hub`, `encryption_identity_id`, `subject_id`,
    `subject_kind`
  - Optional: `profile` defaulting to `symbolic_e2ee_v1`, `status`
    defaulting to `active`, `metadata`
- `register_key_bundle_reference`
  - Required: `registry_hub`, `key_bundle_id`, `encryption_identity_id`
  - Optional: `profile` defaulting to `symbolic_e2ee_v1`, `status`
    defaulting to `active`, `public_ref`, `created_order`, `rotated_from`,
    `metadata`
  - The action stores symbolic public references only. It never generates
    keys, stores private keys, or adds secret material.
- `register_mailbox_encryption_binding`
  - Required: `registry_hub`, `mailbox_id`, `encryption_identity_id`,
    `key_bundle_id`
  - Optional: `required_for_lanes`, `profile` defaulting to
    `symbolic_e2ee_v1`, `status` defaulting to `active`, `metadata`
- `register_mailbox_encryption_policy`
  - Required: `registry_hub`, `policy_id`, `mailbox_id`
  - Optional: `required_for_lanes` defaulting to `basic_messaging:v1`,
    `allowed_profiles` defaulting to `symbolic_e2ee_v1`,
    `require_active_identity`, `require_usable_key_bundle`,
    `allow_plaintext_fallback`, `metadata`
- `evaluate_mailbox_encryption_policy`
  - Required: `registry_hub`, `mailbox_id`, `lane_signature`
  - Optional: `message_id`
  - Optional symbolic envelope fields: `envelope_id`,
    `encryption_identity_id`, `key_bundle_id`, `profile`, `state`, `status`,
    `algorithm_ref`, `ciphertext_ref`, `plaintext_ref`, `metadata`
  - The action builds `EncryptedEnvelopeMetadata` only when envelope fields
    are supplied, calls `evaluate_registered_mailbox_encryption_policy(...)`,
    retains the resulting `EncryptionPolicyDecision` in
    `RegistryHub.encryption_policy_decision_history`, appends the decision to
    scenario action results, and logs a deterministic event. It never calls
    message delivery.

Supported v1.0 symbolic encryption assertions:

- `encryption_identity_registered`
  - Required: `registry_hub`, `encryption_identity_id`
  - Optional checks: `subject_id`, `subject_kind`, `profile`, `status`
- `key_bundle_registered`
  - Required: `registry_hub`, `key_bundle_id`
  - Optional checks: `encryption_identity_id`, `profile`, `status`
- `mailbox_encryption_binding_registered`
  - Required: `registry_hub`, `mailbox_id`
  - Optional checks: `encryption_identity_id`, `key_bundle_id`, `profile`,
    `status`, `lane_signature`
- `mailbox_encryption_policy_registered`
  - Required: `registry_hub`, `policy_id`
  - Optional checks: `mailbox_id`, `lane_signature`, `profile`,
    `allow_plaintext_fallback`
- `encryption_policy_decision_contains`
  - Required: `registry_hub`
  - Optional filters: `policy_id`, `mailbox_id`, `lane_signature`,
    `message_id`, `status`, `reason`, `encryption_required`,
    `envelope_accepted`, `profile`, `encryption_identity_id`,
    `key_bundle_id`
  - Optional count checks: `expected_count`, `min_count`

`encryption_policy_decision_contains` first scans retained
`RegistryHub.encryption_policy_decision_history` records for decisions produced
by `evaluate_mailbox_encryption_policy`, then falls back to scenario action
results for compatibility. If neither `expected_count` nor `min_count` is
supplied, it passes when at least one matching decision exists. Count fields
must be non-negative integers. Boolean filters must be YAML booleans.

Checked-in v1.0 symbolic encryption scenarios:

- `scenarios/047_symbolic_encryption_registry.yaml`
- `scenarios/048_symbolic_encryption_policy_required.yaml`
- `scenarios/049_symbolic_encryption_policy_failures.yaml`

The current v1.0 released scenario set covers `001` through `049`. Scenarios
`047` through `049` do not deliver messages, mutate inboxes, enforce encrypted
delivery, alter plaintext delivery behavior, open sockets, perform DNS lookup,
or import cryptographic libraries.

## v1.1 Symbolic Encrypted Delivery Request Scenarios

The unreleased `v1.1/planning` branch adds scenario DSL coverage for the
existing helper-level symbolic encrypted delivery request, policy gate, and
wrapped result flow. The current branch package and CLI version are
`darwin-sim 1.1.0`. This behavior remains opt-in and simulator-local. It is
not real cryptography, encryption, decryption, production E2EE, secure
messaging, networking, DNS lookup, external services, durable queues, or
default delivery enforcement.

Supported v1.1 encrypted delivery action:

- `evaluate_encrypted_delivery_request`
  - Required: `registry_hub`, `request_id`, `message_id`, `sender_id`,
    `recipient_address`
  - Optional: `mailbox_id`, `policy_id`, `lane_signature` defaulting to
    `basic_messaging:v1`, `payload_kind` defaulting to `text`, `payload`,
    `mode`, `policy_required`, `attempt_delivery`, `retain_policy_decision`,
    `retain_result`, `metadata`
  - Optional symbolic envelope fields: `envelope_id`,
    `encryption_identity_id`, `key_bundle_id`, `profile`, `state`, `status`,
    `algorithm_ref`, `ciphertext_ref`, `plaintext_ref`, `envelope_metadata`
  - If `mode` is omitted, the runner infers `symbolic_encrypted` when
    envelope fields are supplied and `plaintext` otherwise.
    `policy_check_only` must be supplied explicitly.
  - `attempt_delivery` defaults to `false`. Delivery is attempted only when
    the gate allows the request and the scenario explicitly opts in.
  - `retain_policy_decision` defaults to `true` and controls only the
    existing retained `EncryptionPolicyDecision` history.
  - `retain_result` defaults to `true` and controls retained wrapped
    `EncryptedDeliveryResult` history on the referenced `RegistryHub`.

The action builds a `MessageEnvelope`, builds an `EncryptedDeliveryRequest`,
calls `evaluate_encrypted_delivery_request(...)`, retains the wrapped result
on `RegistryHub.encrypted_delivery_result_history` by default, appends the
wrapped result to scenario action results, and logs a deterministic event. If
the gate is blocked, no delivery occurs even when `attempt_delivery: true`.

Supported v1.1 encrypted delivery assertions:

- `encrypted_delivery_result_contains`
  - Required: `registry_hub`
  - Optional filters: `request_id`, `message_id`, `mailbox_id`,
    `lane_signature`, `status`, `reason`, `delivery_attempted`,
    `delivery_allowed`, `policy_required`, `gate_status`, `gate_reason`,
    `delivery_status`, `delivery_reason`, `endpoint_id`
  - Optional count checks: `expected_count`, `min_count`
- `encrypted_delivery_audit_contains`
  - Required: `registry_hub`
  - Optional filters: `request_id`, `message_id`, `mailbox_id`,
    `lane_signature`, `gate_status`, `gate_reason`, `delivery_status`,
    `delivery_reason`, `policy_id`, `encryption_required`,
    `envelope_accepted`
  - Optional count checks: `expected_count`, `min_count`

Both assertions are read-only. They first query retained
`RegistryHub.encrypted_delivery_result_history` records, then fall back to
scenario action results only when retained history is unavailable or empty.
They do not mutate inboxes, create delivery results, or change policy history.
Count behavior matches existing count-style assertions: without
`expected_count` or `min_count`, at least one matching record is required;
`expected_count` requires an exact count; and `min_count` requires at least
that many matches.

Detailed snapshots include compact retained wrapped-result summaries at
`registry_hubs.<hub_id>.encrypted_delivery_result_history`. Compact
`world.snapshot()` output remains unchanged.

Checked-in v1.1 encrypted delivery scenarios:

- `scenarios/050_symbolic_encrypted_delivery_policy_check.yaml`
- `scenarios/051_symbolic_encrypted_delivery_allowed.yaml`
- `scenarios/052_symbolic_encrypted_delivery_blocked.yaml`

The current released scenario set is contiguous through `052`. Existing
plaintext delivery scenarios still use the unchanged `deliver_message` action,
and encrypted delivery policy enforcement is not the default.

## v1.2 Stream Offer Rendezvous Scenarios

The v1.2 release adds scenario DSL coverage for the existing simulator-local
stream offer, private polling descent, and lane admission helper stack. The
released package and CLI version report `darwin-sim 1.2.0`.

This DSL surface is symbolic metadata flow only. It does not add real
networking, sockets, HTTP/WebSocket behavior, DNS lookup, registrar
integration, public CA behavior, external services, live polling loops,
durable queues, retry workers, real cryptography, production E2EE, production
DDoS/security/privacy/anonymity guarantees, TrafficHub routing changes, or
delivery behavior changes.

Supported v1.2 stream offer actions:

- `hold_stream_offer`
  - Required: `registry_hub`, `offer_id`, `requester_id`, `target_handle`,
    `lane_signature`
  - Optional: `requested_mode` defaulting to `message`, `visibility_tier`
    defaulting to `0`, `rendezvous_scope`, `created_order` defaulting to `0`,
    `expires_order`, `status`, `replace_existing`, `metadata`
  - The action builds a `StreamOffer`, stores it with
    `hold_stream_offer(...)`, appends the stored offer to action results, and
    logs a compact summary. It does not deliver or call TrafficHub.
- `poll_held_stream_offers`
  - Required: `registry_hub`, `request_id`, `offer_id`, `polling_hub_id`,
    `requester_id`, `target_scope`
  - Optional: `visibility_tier` defaulting to `0`, `lane_signature`,
    `requested_mode`, `active_only` defaulting to `true`, `current_order`,
    `metadata`
  - The action builds a `RendezvousRequest`, calls
    `poll_held_stream_offers(...)`, appends the request and
    `RendezvousPollResult` to action results, records the poll result on the
    RegistryHub's retained audit history, and logs the poll summary. Polling
    remains read-only with respect to held offers, delivery, routing, and
    networking.
- `mark_stream_offers_discoverable`
  - Required: `registry_hub`, `offer_ids`
  - Optional: `metadata`
  - The action explicitly marks selected held offers `discoverable` and
    appends updated offer records to action results. It does not deliver,
    route, or poll live services.
- `evaluate_lane_admission_policy`
  - Required: `registry_hub`, `policy_id`, `hub_id`, `offer_id`
  - Optional policy fields: `allowed_lane_signatures`,
    `denied_lane_signatures`, `allowed_requester_ids`,
    `denied_requester_ids`, `allowed_target_scopes`,
    `denied_target_scopes`, `max_visibility_tier`,
    `require_discoverable`, `default_status`, `metadata`
  - Optional evaluation fields: `decision_id`, `request_id`,
    `poll_request_id`, `poll_result_request_id`, `target_scope`,
    `decision_metadata`
  - The action finds the held offer, builds a `LaneAdmissionPolicy`, uses a
    prior poll request/result when referenced, appends a
    `LaneAdmissionDecision` to action results, records the decision on the
    RegistryHub's retained audit history, and logs a compact decision. It does
    not mutate the held offer, deliver, route, or poll live services.

Supported v1.2 stream offer assertions:

- `held_stream_offer_contains`
  - Required: `registry_hub`
  - Optional filters: `offer_id`, `requester_id`, `target_handle`,
    `lane_signature`, `requested_mode`, `visibility_tier`, `status`,
    `rendezvous_scope`
  - Optional count checks: `expected_count`, `min_count`
- `rendezvous_poll_result_contains`
  - Required: `registry_hub`
  - Optional filters: `request_id`, `polling_hub_id`, `parent_hub_id`,
    `target_scope`, `visibility_tier`, `status`, `reason`,
    `matched_offer_id`, `matched_offer_ids`
  - Optional count checks: `expected_count`, `min_count`
- `lane_admission_decision_contains`
  - Required: `registry_hub`
  - Optional filters: `decision_id`, `policy_id`, `offer_id`, `request_id`,
    `hub_id`, `requester_id`, `target_handle`, `target_scope`,
    `lane_signature`, `status`, `reason`, `allowed`
  - Optional count checks: `expected_count`, `min_count`

Count behavior matches existing count-style assertions. Without
`expected_count` or `min_count`, at least one matching record is required.
`expected_count` requires an exact count, and `min_count` requires at least
that many matches. Boolean filters must be YAML booleans.

Sprint 6 changes `rendezvous_poll_result_contains` and
`lane_admission_decision_contains` to prefer retained RegistryHub histories
before falling back to scenario action results. Detailed snapshots include
compact `held_stream_offers`, `rendezvous_poll_result_history`, and
`lane_admission_decision_history` summaries under each RegistryHub. Compact
`world.snapshot()` output remains unchanged.

Checked-in v1.2 stream offer scenarios:

- `scenarios/053_stream_offer_rendezvous_allowed.yaml`
- `scenarios/054_stream_offer_rendezvous_held.yaml`
- `scenarios/055_stream_offer_rendezvous_denied.yaml`
- `scenarios/056_stream_offer_rendezvous_rate_limited.yaml`
- `scenarios/057_stream_offer_rendezvous_quarantined.yaml`

The current released scenario set is contiguous through `057`.

## v1.3 Stream Offer Lifecycle Scenarios

The v1.3 release adds scenario DSL coverage for existing
simulator-local stream-offer lifecycle planning and explicit apply helpers.
The released package and CLI version report `darwin-sim 1.3.0`.

This DSL surface is symbolic metadata flow only. It does not add automatic
cleanup workers, retry loops, durable queues, live timers, live clocks, live
polling, sockets, HTTP/WebSocket behavior, DNS lookup, registrar integration,
public CA behavior, external services, real cryptography, production E2EE,
key generation, private key storage, delivery enforcement, TrafficHub routing
changes, compact snapshot changes, or canonical identity rewrites.

Supported v1.3 stream offer lifecycle actions:

- `plan_stream_offer_expiration`
  - Required: `registry_hub`, `checked_at`
  - Optional: `metadata`
  - The action calls `plan_stream_offer_expiration(...)` with the explicit
    deterministic simulator order in `checked_at`, appends the
    `StreamOfferLifecyclePlan` to action results, and logs a compact summary.
    Planning is read-only: it does not mutate retained held offers, record
    transitions, delete offers, deliver messages, route TrafficHub traffic, or
    use wall-clock time.
- `apply_stream_offer_lifecycle_plan`
  - Required: `registry_hub`
  - Optional action-result plan selection: `checked_at`
  - Optional explicit caller plan fields: `plan_checked_at` or `checked_at`,
    `expired_offer_ids`, `cleanup_candidate_offer_ids`, `active_offer_ids`,
    `ignored_offer_ids`, `plan_metadata`
  - Optional apply fields: `record_transition` defaulting to `true`,
    `actor_id`, `request_id`, `transition_metadata`, `metadata`
  - The action uses a prior `StreamOfferLifecyclePlan` action result for the
    same RegistryHub, optionally narrowed by `checked_at`, or an explicit
    caller-provided plan described by `plan_checked_at` and offer ID lists.
    It calls `apply_stream_offer_lifecycle_plan(...)`, appends the
    `StreamOfferLifecycleApplyResult` to action results, and logs a compact
    summary. Apply is the only lifecycle DSL action that mutates held offer
    statuses. It never deletes held offers.

Supported v1.3 stream offer lifecycle assertions:

- `stream_offer_lifecycle_plan_contains`
  - Required: `registry_hub`
  - Optional filters: `checked_at`, `expired_offer_id`,
    `expired_offer_ids`, `cleanup_candidate_offer_id`,
    `cleanup_candidate_offer_ids`, `active_offer_id`, `active_offer_ids`,
    `ignored_offer_id`, `ignored_offer_ids`
  - Optional count checks: `expected_count`, `min_count`
- `stream_offer_lifecycle_apply_result_contains`
  - Required: `registry_hub`
  - Optional filters: `plan_checked_at`, `applied_offer_id`,
    `applied_offer_ids`, `skipped_offer_id`, `skipped_offer_ids`,
    `missing_offer_id`, `missing_offer_ids`, `recorded_transition_count`
  - Optional count checks: `expected_count`, `min_count`
- `stream_offer_status_transition_contains`
  - Required: `registry_hub`
  - Optional filters: `offer_id`, `hub_id`, `previous_status`, `new_status`,
    `status`, `reason`, `actor_id`, `request_id`
  - Optional count checks: `expected_count`, `min_count`

`stream_offer_status_transition_contains` prefers retained
`RegistryHub.stream_offer_status_transition_history` before falling back to
scenario action results. Lifecycle plan and apply-result assertions read
scenario action results because plans and apply results are returned to
callers and are not retained on the hub by default.

Detailed snapshots include copied lifecycle plan and apply-result action
summaries at top level under `stream_offer_lifecycle_plans` and
`stream_offer_lifecycle_apply_results`. Retained transition summaries remain
under each RegistryHub at
`registry_hubs.<hub_id>.stream_offer_status_transition_history`. Compact
`world.snapshot()` output remains unchanged.

Checked-in v1.3 stream offer lifecycle scenarios:

- `scenarios/058_stream_offer_lifecycle_expiration_plan.yaml`
- `scenarios/059_stream_offer_lifecycle_apply_records_transition.yaml`
- `scenarios/060_stream_offer_lifecycle_apply_without_transition.yaml`

The current released scenario set is contiguous through `060`.

## v1.4 Stream Offer Lifecycle Explanation Scenarios

The v1.4 release adds scenario DSL coverage for read-only stream-offer
lifecycle explanations and grouped audit summaries. The released package and
CLI version report `darwin-sim 1.4.0`.

This DSL surface is symbolic simulator metadata only. It does not add
automatic cleanup workers, retry loops, durable queues, live timers, live
clocks, live polling, sockets, HTTP/WebSocket behavior, DNS lookup, registrar
integration, public CA behavior, external services, real cryptography,
production E2EE, key generation, private key storage, delivery enforcement,
TrafficHub routing changes, compact snapshot changes, or canonical identity
rewrites.

Supported v1.4 lifecycle explanation and audit actions:

- `explain_stream_offer_lifecycle_plan`
  - Required: `registry_hub`
  - Optional action-result plan selection: `checked_at`
  - Optional explicit caller plan fields: `plan_checked_at` or `checked_at`,
    `expired_offer_ids`, `cleanup_candidate_offer_ids`, `active_offer_ids`,
    `ignored_offer_ids`, `plan_metadata`
  - Optional retention field: `record_explanations` defaulting to `false`
  - The action reads a prior `StreamOfferLifecyclePlan` action result or an
    explicit caller-provided plan and appends read-only
    `StreamOfferLifecycleExplanation` results to scenario action results.
    It records explanations only when `record_explanations: true` is supplied.
- `explain_stream_offer_lifecycle_apply_result`
  - Required: `registry_hub`
  - Optional apply-result selection: `plan_checked_at` or `checked_at`
  - Optional retention field: `record_explanations` defaulting to `false`
  - The action reads a prior `StreamOfferLifecycleApplyResult` action result
    and appends read-only explanation results. It records explanations only
    when `record_explanations: true` is supplied.
- `record_stream_offer_lifecycle_explanations`
  - Required: `registry_hub`
  - Optional filters over prior action-result explanations: `offer_id`,
    `category`, `reason`, `status`, `source`, `checked_at`
  - The action explicitly appends matching prior explanation action results to
    `RegistryHub.stream_offer_lifecycle_explanation_history`.
- `summarize_stream_offer_lifecycle_audit`
  - Required: `registry_hub`
  - Optional: `include_action_explanations`,
    `include_retained_explanations`, `metadata`
  - The action reads retained lifecycle transition history and, when
    explicitly requested, prior action-result explanations and/or retained
    explanation history. It appends a read-only
    `StreamOfferLifecycleAuditSummary` to scenario action results.

Supported v1.4 lifecycle explanation and audit assertions:

- `stream_offer_lifecycle_explanation_contains`
  - Required: `registry_hub`
  - Optional filters: `offer_id`, `category`, `reason`, `status`, `source`,
    `checked_at`
  - Optional count checks: `expected_count`, `min_count`
  - The assertion prefers retained explanation history when present and falls
    back to explanation action results otherwise.
- `stream_offer_lifecycle_explanation_history_contains`
  - Required: `registry_hub`
  - Optional filters: `offer_id`, `category`, `reason`, `status`, `source`,
    `checked_at`
  - Optional count checks: `expected_count`, `min_count`
  - The assertion reads only retained
    `RegistryHub.stream_offer_lifecycle_explanation_history`.
- `stream_offer_lifecycle_audit_summary_contains`
  - Required: `registry_hub`
  - Optional filters: `total_transitions`, `explanation_count`, `offer_id`,
    `offer_count`, `status`, `status_count`, `reason`, `reason_count`,
    `category`, `category_count`
  - Optional count checks: `expected_count`, `min_count`
  - The assertion reads audit summary action results.

Explanation and audit summary actions do not mutate held offer status,
lifecycle plans, lifecycle apply results, retained transition history,
delivery state, TrafficHub routes, canonical identities, or compact snapshots.
The only new retention path is explicit simulator-local explanation recording.

Detailed snapshots include copied explanation and audit-summary action results
under `stream_offer_lifecycle_explanations` and
`stream_offer_lifecycle_audit_summaries`. Retained explanation history remains
under each RegistryHub at
`registry_hubs.<hub_id>.stream_offer_lifecycle_explanation_history`. Compact
`world.snapshot()` output remains unchanged.

Checked-in v1.4 stream offer lifecycle explanation scenarios:

- `scenarios/061_stream_offer_lifecycle_plan_explained.yaml`
- `scenarios/062_stream_offer_lifecycle_apply_explanation_retained.yaml`
- `scenarios/063_stream_offer_lifecycle_audit_summary.yaml`

The current released scenario set is contiguous through `063`.

## v1.5 Lifecycle Explanation Retention and Pruning Scenarios

The v1.5 planning branch adds scenario DSL coverage for lifecycle explanation
retention classification, read-only pruning plans, and explicit pruning apply.
The package and CLI version still report `darwin-sim 1.4.0`.

This DSL surface is symbolic simulator metadata only. It does not add
automatic cleanup workers, retry loops, durable queues, live timers, live
clocks, live polling, sockets, HTTP/WebSocket behavior, DNS lookup, registrar
integration, public CA behavior, external services, real cryptography,
production E2EE, key generation, private key storage, delivery enforcement,
TrafficHub routing changes, compact snapshot changes, detailed snapshot
changes, or canonical identity rewrites.

Supported v1.5 lifecycle retention and pruning actions:

- `classify_stream_offer_lifecycle_explanations_for_retention`
  - Required: `registry_hub`, `policy_id`
  - Optional explanation inputs: `include_retained_explanations` defaulting to
    `true`, `include_action_explanations` defaulting to `false`,
    `include_foreign_action_explanations` defaulting to `false`
  - Optional explanation filters: `offer_id`, `category`, `reason`, `status`,
    `source`, `checked_at`
  - Optional policy fields: `retain_categories`, `retain_reasons`,
    `retain_sources`, `prune_categories`, `prune_reasons`, `prune_sources`,
    `max_records`, `policy_metadata`
  - Optional decision metadata: `metadata`
  - The action builds a simulator-local retention policy, classifies explicit
    lifecycle explanations, appends a
    `StreamOfferLifecycleExplanationRetentionDecision` to action results, and
    does not mutate retained explanation history.
- `plan_stream_offer_lifecycle_explanation_pruning`
  - Required: `registry_hub`, `policy_id`
  - Optional explanation inputs and filters match the classification action.
  - Optional policy fields match the classification action when no prior
    retention decision for the same `policy_id` exists.
  - Optional explicit plan fields: `candidate_explanation_keys`,
    `retained_explanation_keys`, `ignored_explanation_keys`, `plan_metadata`
  - The action uses a prior matching retention decision when available, or
    classifies from the supplied policy fields, and appends a read-only
    `StreamOfferLifecycleExplanationPruningPlan` to action results. Explicit
    plan fields are also read-only and exist only for deterministic scenario
    coverage.
- `apply_stream_offer_lifecycle_explanation_pruning_plan`
  - Required: `registry_hub`, `policy_id`
  - Optional explicit plan fields: `candidate_explanation_keys`,
    `retained_explanation_keys`, `ignored_explanation_keys`, `plan_metadata`
  - Optional apply metadata: `metadata`
  - The action requires a prior matching pruning plan action result or explicit
    plan fields. It appends a
    `StreamOfferLifecycleExplanationPruningApplyResult` to action results and
    mutates only `RegistryHub.stream_offer_lifecycle_explanation_history` by
    removing retained records whose deterministic keys match candidate keys.

Supported v1.5 lifecycle retention and pruning assertions:

- `stream_offer_lifecycle_retention_decision_contains`
  - Required: `registry_hub`
  - Optional filters: `policy_id`, `kept_explanation_key`,
    `kept_explanation_keys`, `prune_candidate_explanation_key`,
    `prune_candidate_explanation_keys`, `ignored_explanation_key`,
    `ignored_explanation_keys`, `kept_count`, `prune_candidate_count`,
    `ignored_count`
  - Optional count checks: `expected_count`, `min_count`
- `stream_offer_lifecycle_pruning_plan_contains`
  - Required: `registry_hub`
  - Optional filters: `policy_id`, `prune_candidate_explanation_key`,
    `prune_candidate_explanation_keys`, `kept_explanation_key`,
    `kept_explanation_keys`, `ignored_explanation_key`,
    `ignored_explanation_keys`, `candidate_count`, `retained_count`,
    `ignored_count`, `category`, `category_count`, `reason`, `reason_count`,
    `source`, `source_count`
  - Optional count checks: `expected_count`, `min_count`
- `stream_offer_lifecycle_pruning_apply_result_contains`
  - Required: `registry_hub`
  - Optional filters: `policy_id`, `pruned_explanation_key`,
    `pruned_explanation_keys`, `retained_explanation_key`,
    `retained_explanation_keys`, `ignored_explanation_key`,
    `ignored_explanation_keys`, `missing_explanation_key`,
    `missing_explanation_keys`, `pruned_count`, `retained_count`,
    `ignored_count`, `missing_count`
  - Optional count checks: `expected_count`, `min_count`

Retention classification and pruning-plan actions are read-only. The pruning
apply action is explicit and does not mutate held offers, stream offers,
lifecycle plans, lifecycle apply results, transition history, polling history,
admission history, delivery state, TrafficHub state or routing, canonical
identity, compact snapshots, or detailed snapshots.

Checked-in v1.5 lifecycle retention and pruning scenarios:

- `scenarios/064_stream_offer_lifecycle_retention_classification.yaml`
- `scenarios/065_stream_offer_lifecycle_pruning_plan.yaml`
- `scenarios/066_stream_offer_lifecycle_pruning_apply.yaml`

The current checked-in scenario set is contiguous through `066`.
