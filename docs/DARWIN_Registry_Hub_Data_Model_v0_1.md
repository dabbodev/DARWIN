# DARWIN Registry Hub Data Model v0.1

**Project name:** DARWIN  
**Document:** Registry Hub Data Model  
**Version:** v0.1  
**Status:** Concept draft / simulator-oriented data model  
**Related documents:**

- DARWIN Design Dossier v0.1
- DARWIN Identity, Trust, and Authentication Model v0.1
- DARWIN Packet, Checkpoint, and Lane Protocol v0.1

---

## 1. Purpose

This document defines the first draft of the data structures a DARWIN Registry Hub should store, update, query, summarize, and hand upward.

The core question is:

```text
What does a Registry Hub need to know in order to recognize devices, manage names, verify movement, handle conflicts, and support routing without knowing the whole world?
```

This document is intentionally simulator-friendly. It describes records, indexes, tables, and operations that could later become in-memory objects, JSON files, database tables, or protocol schemas.

---

## 2. Registry Hub Responsibilities

A Registry Hub manages scoped identity.

A Registry Hub should answer:

```text
What devices are registered in my scope?
Which local label maps to which device_id?
Which device_id maps to which identity chain?
Where is this device currently attached?
Is this device allowed in this scope?
Is this passport valid or revoked?
Has this device moved recently?
Does this device have a known history?
Do I need to ask a parent or sibling registry?
What summary should I hand upward?
```

A Registry Hub is not necessarily responsible for moving data packets. That is the Traffic Hub’s job. However, Registry Hubs may provide routing-relevant metadata such as current attachment, state, and verified movement status.

---

## 3. Core Principle

Registry data should be local-first, summarized upward, and queried outward only when necessary.

```text
Local Hub:
  knows direct children in detail

Parent Hub:
  knows summaries and anchors

Higher Hub:
  knows sparse identity hints

Peer / Sibling Hub:
  may answer history or conflict questions when escalation requires it
```

The Registry Hub should avoid becoming a global all-knowing database. It should know enough to perform its role and escalate when needed.

---

## 4. Registry Scope

Each Registry Hub governs a scope.

Example:

```text
global.family.david.home
```

The hub’s child labels exist within that scope:

```text
my_pc
printer
phone
livingroom_sensor
```

Full identity chains are formed by appending local labels:

```text
global.family.david.home.my_pc
global.family.david.home.printer
global.family.david.home.phone
```

Example scope record:

```yaml
registry_scope:
  hub_id: hub_home_001
  scope_path: global.family.david.home
  parent_scope: global.family.david
  parent_hub_id: hub_david_001
  scope_type: local_home
  authority_level: local_registry
  created_at: 2026-05-26T12:00:00Z
  status: active
```

---

## 5. Data Model Overview

A Registry Hub may maintain these major record groups:

```text
Hub Record
Scope Record
Local Device Records
Label Index
Device ID Index
Passport Index
Attachment Index
Checkpoint State Table
Move History Table
Parent Attestation Table
Local Session Table
Conflict Table
Revocation Table
Issuer Trust Table
Upward Summary Table
Cache Table
Query Log
Security Event Log
Policy Records
```

For the first simulator, not every table needs production detail. The core useful set is:

```text
Hub Record
Local Device Records
Label Index
Device ID Index
Passport Index
Attachment Index
Move History Table
Checkpoint State Table
Conflict Table
Upward Summary Table
```

---

## 6. Hub Record

The Hub Record describes the Registry Hub itself.

Example:

```yaml
hub_record:
  hub_id: hub_home_001
  hub_label: home
  hub_roles:
    registry: true
    traffic: true
    hybrid: true
  scope_path: global.family.david.home
  parent_hub_id: hub_david_001
  parent_scope_path: global.family.david
  public_key: HUB_PUBLIC_KEY
  status: active
  capabilities:
    can_register_devices: true
    can_issue_passports: true
    can_accept_moves: true
    can_issue_parent_attestations: true
    can_act_as_traffic_hub: true
  created_at: 2026-05-26T12:00:00Z
  last_summary_handup: 2026-05-26T12:05:00Z
```

Important distinction:

```text
hub_id      = durable identifier for the hub
hub_label   = human-readable name within its parent scope
scope_path  = namespace branch governed by the hub
```

---

## 7. Local Device Record

A Local Device Record describes a device directly registered under this hub’s scope.

Example:

```yaml
local_device_record:
  device_id: dev_A9F3
  current_label: my_pc
  full_identity_chain: global.family.david.home.my_pc
  passport_id: cert_123
  current_attachment: hub_home_001
  current_state: online
  checkpoint_tier: 2
  local_session_id: sess_8821
  registered_at: 2026-05-26T12:00:00Z
  last_checkpoint: 2026-05-26T12:06:00Z
  last_verified_at: 2026-05-26T12:06:00Z
  allowed_capabilities:
    can_send_packets: true
    can_receive_packets: true
    can_host_services: false
    can_act_as_parent_hub: false
    can_request_lane_preservation: true
  status: active
```

This record is the hub’s primary local identity entry for a device.

---

## 8. Label Index

The Label Index maps local names to device IDs.

Example:

```yaml
label_index:
  my_pc: dev_A9F3
  printer: dev_B2C8
  phone: dev_C391
```

The Label Index exists only within the hub’s scope.

The label `printer` under one hub does not conflict with `printer` under another hub.

Conflict example:

```yaml
label_conflict:
  requested_label: my_pc
  existing_device_id: dev_A9F3
  requesting_device_id: dev_B2C8
  assigned_temp_label: my_pc_temp_B2C8
  status: pending_resolution
```

Rules:

```text
A local label must map to no more than one active device_id.
A device_id may have aliases, but one primary current_label should be selected.
Temporary conflict labels should be clearly marked.
```

---

## 9. Device ID Index

The Device ID Index maps durable device identifiers to local records.

Example:

```yaml
device_id_index:
  dev_A9F3:
    label: my_pc
    full_identity_chain: global.family.david.home.my_pc
    record_ref: local_device_record/dev_A9F3
  dev_B2C8:
    label: printer
    full_identity_chain: global.family.david.home.printer
    record_ref: local_device_record/dev_B2C8
```

This index is the first stop for questions like:

```text
Have I seen this device before?
Is this device currently registered here?
What label does this device have locally?
What is its current state?
```

---

## 10. Passport Index

The Passport Index tracks agreement certificates associated with known devices.

Example:

```yaml
passport_index:
  cert_123:
    device_id: dev_A9F3
    issued_by: hub_david_devices_001
    issued_scope: global.family.david.devices
    current_scope: global.family.david.home
    status: valid
    verified_at: 2026-05-26T12:00:00Z
    expires_at: null
```

The Passport Index should support checks like:

```text
Is this certificate known?
Is it still valid?
Who issued it?
Does the issuer have authority?
Is the certificate revoked?
Does it allow this device to register here?
```

---

## 11. Attachment Index

The Attachment Index maps device IDs to their current known attachment point.

Example:

```yaml
attachment_index:
  dev_A9F3:
    current_attachment: hub_home_001
    attachment_type: direct_child
    current_scope: global.family.david.home
    traffic_hint: hub_home_001.local_link
    state: online
    last_updated: 2026-05-26T12:06:00Z
  dev_C391:
    current_attachment: hub_office_007
    attachment_type: moved_remote
    current_scope: global.family.david.office
    traffic_hint: hub_office_007.local_link
    state: online
    last_updated: 2026-05-26T12:08:00Z
```

Attachment type examples:

```text
direct_child
child_hub
remote_known
moved_remote
in_transit
unknown
stale
```

This index helps Registry Hubs answer:

```text
Where should the Traffic Layer try to reach this device?
Is the current attachment fresh?
Did this device recently move?
```

---

## 12. Checkpoint State Table

The Checkpoint State Table tracks the most recent liveness and state reports from devices.

Example:

```yaml
checkpoint_state_table:
  dev_A9F3:
    state: online
    checkpoint_tier: 2
    last_checkpoint_id: cp_001
    last_checkpoint_at: 2026-05-26T12:06:00Z
    expected_next_checkpoint_within_ms: 5000
    missed_checkpoint_count: 0
    active_lane_count: 3
    battery_level: 91
    auth_valid: true
```

Possible device states:

```text
unknown
claiming_identity
passport_verified
locally_authenticated
online
idle
active
disconnected
in_transit
awaiting_verification
timed_out
offline
quarantined
revoked
rejected
```

Checkpoint state is not just monitoring. It affects routing and lane behavior.

Example:

```text
online      → send normally
idle        → send normally or wake if needed
in_transit  → pause lanes and wait for re-registration
timed_out   → retry, query registry, or mark offline
quarantined → block normal traffic
```

---

## 13. Move History Table

The Move History Table records known movement events for devices.

Example:

```yaml
move_history_table:
  dev_A9F3:
    - move_id: move_456
      certificate_id: cert_123
      from_scope: global.family.david.home
      to_scope: global.family.david.office
      old_attachment: hub_home_001
      new_attachment: hub_office_007
      timestamp: 2026-05-26T12:05:00Z
      verification_status: verified
      signatures_present:
        device: true
        new_registry_hub: true
        old_registry_hub: true
```

Move history helps answer:

```text
Where did this device last belong?
Was the latest movement valid?
Is a new movement claim suspicious?
Are two hubs claiming the same device?
```

Privacy note:

```text
Move history can reveal sensitive behavior. Higher-level hubs may store summaries rather than full detailed histories.
```

---

## 14. Parent Attestation Table

The Parent Attestation Table records short-lived hub-child relationships.

Example:

```yaml
parent_attestation_table:
  attest_789:
    child_device_id: dev_A9F3
    parent_hub_id: hub_home_001
    scope: global.family.david.home
    session_epoch: epoch_8821
    valid_from: 2026-05-26T12:00:00Z
    valid_until: 2026-05-26T12:10:00Z
    status: active
```

This table helps defend against false parent claims.

Checks:

```text
Is the attestation still valid?
Was it issued by the claimed parent hub?
Is the parent hub authorized in this scope?
Does the child relationship match current attachment state?
```

---

## 15. Local Session Table

The Local Session Table tracks active same-network authentication sessions.

Example:

```yaml
local_session_table:
  sess_8821:
    device_id: dev_A9F3
    hub_id: hub_home_001
    scope: global.family.david.home
    auth_method: rolling_cmac_or_hmac
    session_epoch: epoch_8821
    current_counter: 1044
    created_at: 2026-05-26T12:00:00Z
    expires_at: 2026-05-26T18:00:00Z
    state: active
```

The Local Session Table supports:

```text
rolling proof verification
packet/checkpoint auth tags
MAC spoofing defense
same-network continuity
session rotation
quarantine on failure
```

---

## 16. Conflict Table

The Conflict Table tracks unresolved identity, label, attachment, or authority conflicts.

Conflict types:

```text
label_conflict
duplicate_device_id
passport_conflict
move_contract_conflict
attachment_conflict
issuer_conflict
parent_attestation_conflict
local_session_conflict
```

Example label conflict:

```yaml
conflict_table:
  conflict_001:
    conflict_type: label_conflict
    scope: global.family.david.home
    requested_label: my_pc
    existing_device_id: dev_A9F3
    requesting_device_id: dev_B2C8
    assigned_temp_label: my_pc_temp_B2C8
    status: pending_resolution
    created_at: 2026-05-26T12:02:00Z
```

Example duplicate device conflict:

```yaml
conflict_002:
  conflict_type: duplicate_device_id
  device_id: dev_A9F3
  claiming_hubs:
    - hub_home_001
    - hub_office_007
  current_action: freeze_lanes_and_verify
  status: investigating
```

Conflict records should include:

```text
what conflict occurred
which devices or hubs are involved
which records are frozen or limited
what verification step is next
whether human/admin resolution is required
```

---

## 17. Revocation Table

The Revocation Table tracks invalidated certificates, sessions, attestations, devices, or hub authorities.

Example:

```yaml
revocation_table:
  cert_123:
    revoked_type: agreement_certificate
    device_id: dev_A9F3
    revoked_by: hub_david_devices_001
    revoked_at: 2026-05-26T13:00:00Z
    reason: suspected_key_compromise
    status: active_revocation
```

Revocation target types:

```text
agreement_certificate
move_contract
parent_attestation
local_session
hub_authority
device_capability
```

A Registry Hub should consult revocation status during:

```text
new device registration
move verification
passport validation
session rotation
parent claim verification
checkpoint trust checks
```

---

## 18. Issuer Trust Table

The Issuer Trust Table defines which hubs or authorities this hub trusts to issue passports, attestations, or scope permissions.

Example:

```yaml
issuer_trust_table:
  hub_david_devices_001:
    scope_authority: global.family.david.devices
    public_key: REGISTRY_PUBLIC_KEY
    trust_level: local_parent
    allowed_actions:
      - issue_passports
      - revoke_passports
      - validate_moves
    status: active
    valid_from: 2026-05-26T00:00:00Z
    valid_until: null
```

Trust levels:

```text
self
local_parent
regional_parent
federated_peer
global_anchor
temporary_guest_authority
unknown
revoked
```

This table helps answer:

```text
Can this issuer create a valid passport?
Can this issuer accept a move?
Can this issuer revoke a passport?
Can this issuer speak for this scope?
```

---

## 19. Upward Summary Table

The Upward Summary Table stores the compact information this hub should hand upward to its parent Registry Hub.

Example:

```yaml
upward_summary_table:
  hub_id: hub_home_001
  scope: global.family.david.home
  summary_version: 17
  generated_at: 2026-05-26T12:06:00Z
  devices:
    - device_id: dev_A9F3
      identity_chain: global.family.david.home.my_pc
      passport_id: cert_123
      current_state: online
      current_attachment: hub_home_001
      last_checkpoint: 2026-05-26T12:06:00Z
    - device_id: dev_B2C8
      identity_chain: global.family.david.home.printer
      passport_id: cert_222
      current_state: idle
      current_attachment: hub_home_001
      last_checkpoint: 2026-05-26T12:01:00Z
```

Summary detail should depend on policy.

Possible summary levels:

```text
full_local_summary
identity_anchor_summary
state_only_summary
presence_only_summary
private_minimal_summary
```

---

## 20. Cache Table

Registry Hubs may cache lookup results from parents, children, or peer hubs.

Example:

```yaml
cache_table:
  dev_C391:
    cached_identity_chain: global.family.david.office.phone
    cached_attachment: hub_office_007
    cached_state: online
    source_hub: hub_david_001
    trust_status: verified_summary
    cached_at: 2026-05-26T12:08:00Z
    expires_at: 2026-05-26T12:13:00Z
```

Cache entry states:

```text
fresh
stale
expired
conflicted
requires_revalidation
```

Caching rules:

```text
Registry identity may cache longer than traffic attachment.
Traffic hints should expire quickly.
In-transit states should use short expiration windows.
Revocation and conflict states should override cached valid states.
```

---

## 21. Query Log

The Query Log records lookup and verification requests.

Example:

```yaml
query_log:
  - query_id: query_001
    query_type: device_id_to_attachment
    requester: hub_source_003
    target_device_id: dev_A9F3
    answered_from: local_cache
    result: found
    timestamp: 2026-05-26T12:06:10Z
```

Query logs help with:

```text
debugging
security review
branch growth analysis
cache tuning
traffic pattern discovery
```

Privacy note:

```text
Query logs can reveal communication patterns. Retention should be policy-controlled.
```

---

## 22. Security Event Log

The Security Event Log records suspicious or important events.

Example:

```yaml
security_event_log:
  - event_id: sec_001
    event_type: rolling_proof_failed
    device_id: dev_A9F3
    hub_id: hub_home_001
    scope: global.family.david.home
    severity: medium
    action_taken: forced_passport_recheck
    timestamp: 2026-05-26T12:10:00Z
```

Possible events:

```text
passport_verification_failed
issuer_unknown
revoked_passport_presented
rolling_proof_failed
packet_auth_failed
checkpoint_auth_failed
mac_spoof_suspected
parent_impersonation_attempt
duplicate_device_id_active
move_contract_conflict
stale_counter_detected
replay_detected
quarantine_started
quarantine_released
```

---

## 23. Policy Records

Policy Records define local behavior.

Example:

```yaml
registry_policy:
  scope: global.family.david.home
  registration:
    allow_unknown_passports: false
    allow_guest_quarantine: true
    default_checkpoint_tier: 1
  labels:
    conflict_strategy: assign_temp_label
    temp_label_format: "{requested_label}_temp_{short_device_id}"
  summaries:
    handup_interval_ms: 30000
    default_summary_level: identity_anchor_summary
  movement:
    in_transit_hold_window_ms: 3000
    require_move_contract_for_scope_change: true
  security:
    require_rolling_proof: true
    quarantine_on_failed_proof: true
    max_failed_proofs_before_reject: 3
```

Policies should be attached to scopes, not hardcoded globally.

---

## 24. Primary Registry Operations

A Registry Hub should support these core operations:

```text
register_device
resolve_label
resolve_device_id
verify_passport
create_or_validate_move_contract
update_attachment
update_checkpoint_state
mark_in_transit
assign_temp_label
record_conflict
hand_up_summary
query_parent
query_child
query_peer_or_witness
revoke_record
quarantine_device
release_quarantine
```

Each operation should produce either:

```text
success result
error result
pending verification result
conflict result
quarantine result
```

---

## 25. Operation: Register Device

Purpose:

```text
Add a device to this hub’s local registry scope.
```

Inputs:

```text
device_id
requested_label
passport or first-registration data
current_attachment
checkpoint_tier
capability request
```

Flow:

```text
1. Check whether device_id is known locally.
2. Verify passport or initiate first passport creation.
3. Check issuer trust and revocation status.
4. Check requested label against Label Index.
5. Assign requested label or temporary conflict label.
6. Create Local Device Record.
7. Update Label Index.
8. Update Device ID Index.
9. Update Passport Index.
10. Update Attachment Index.
11. Create local session if needed.
12. Generate upward summary update.
```

Example result:

```yaml
register_device_result:
  status: registered
  device_id: dev_A9F3
  assigned_label: my_pc
  full_identity_chain: global.family.david.home.my_pc
  passport_id: cert_123
  local_session_id: sess_8821
```

---

## 26. Operation: Resolve Label

Purpose:

```text
Resolve a local label or full identity chain to a device_id and attachment.
```

Input examples:

```text
my_pc
global.family.david.home.my_pc
```

Local label flow:

```text
1. Check Label Index.
2. Find device_id.
3. Retrieve Local Device Record.
4. Retrieve Attachment Index.
5. Return identity and attachment data.
```

Example result:

```yaml
resolve_label_result:
  query: my_pc
  device_id: dev_A9F3
  identity_chain: global.family.david.home.my_pc
  current_attachment: hub_home_001
  current_state: online
  trust_status: local_verified
```

If the label is unknown:

```yaml
resolve_label_result:
  query: printer2
  status: not_found
  suggested_action: query_parent_or_return_error
```

---

## 27. Operation: Resolve Device ID

Purpose:

```text
Find the identity chain, current attachment, and state for a device_id.
```

Flow:

```text
1. Check local Device ID Index.
2. If found, return local record.
3. If not found, check Cache Table.
4. If not cached, query parent.
5. If parent misses, escalate according to policy.
```

Example result:

```yaml
resolve_device_id_result:
  device_id: dev_A9F3
  identity_chain: global.family.david.home.my_pc
  current_attachment: hub_home_001
  current_state: online
  source: local_registry
  freshness: fresh
```

---

## 28. Operation: Mark In Transit

Purpose:

```text
Record that a device is intentionally or probably relocating.
```

Flow:

```text
1. Find Local Device Record.
2. Update current_state to in_transit.
3. Update Attachment Index attachment_type to in_transit.
4. Update Checkpoint State Table.
5. Notify Traffic Layer or Lane Manager.
6. Generate upward summary update.
```

Example result:

```yaml
mark_in_transit_result:
  device_id: dev_A9F3
  previous_attachment: hub_home_001
  state: in_transit
  hold_window_ms: 3000
  affected_lanes:
    - lane_S991
```

---

## 29. Operation: Update Attachment

Purpose:

```text
Change the current attachment point for a device after registration or movement.
```

Inputs:

```text
device_id
new_attachment
new_scope
move_contract if scope changed
verification status
```

Flow:

```text
1. Verify device_id exists locally, in cache, or through parent query.
2. If scope changed, require Move Contract.
3. Validate Move Contract.
4. Update Attachment Index.
5. Update Local Device Record or Cache Table.
6. Update Move History Table.
7. Update Checkpoint State Table.
8. Notify Traffic Layer of route update.
9. Generate upward summary update.
```

Example result:

```yaml
update_attachment_result:
  device_id: dev_A9F3
  old_attachment: hub_home_001
  new_attachment: hub_office_007
  new_scope: global.family.david.office
  move_contract: move_456
  state: online
```

---

## 30. Operation: Assign Temporary Label

Purpose:

```text
Handle local label conflicts without blocking all registration.
```

Flow:

```text
1. Detect requested label is already active.
2. Generate temporary label.
3. Register device under temporary label or quarantine depending on policy.
4. Record conflict.
5. Return assigned temporary label.
```

Example:

```yaml
assign_temp_label_result:
  requested_label: my_pc
  assigned_label: my_pc_temp_B2C8
  existing_device_id: dev_A9F3
  requesting_device_id: dev_B2C8
  conflict_id: conflict_001
```

---

## 31. Operation: Hand Up Summary

Purpose:

```text
Send compact registry state to the parent hub.
```

Hand-up may be triggered by:

```text
new device registration
device movement
state change to in_transit
revocation
conflict
periodic summary interval
parent request
```

Example hand-up packet payload:

```yaml
registry_summary_update:
  from_hub: hub_home_001
  scope: global.family.david.home
  summary_version: 18
  update_reason: device_moved
  devices:
    - device_id: dev_A9F3
      identity_chain: global.family.david.home.my_pc
      current_state: in_transit
      current_attachment: hub_home_001
      last_checkpoint: 2026-05-26T12:06:00Z
```

Parent response:

```yaml
summary_ack:
  parent_hub: hub_david_001
  accepted_version: 18
  status: accepted
  conflicts_detected: []
```

---

## 32. Operation: Query Parent

Purpose:

```text
Ask the parent registry for identity, history, issuer trust, or conflict data.
```

Example query:

```yaml
parent_query:
  query_id: query_044
  from_hub: hub_home_001
  to_parent_hub: hub_david_001
  query_type: device_history
  device_id: dev_A9F3
  reason: new_move_claim
```

Example response:

```yaml
parent_query_response:
  query_id: query_044
  result: found
  device_id: dev_A9F3
  known_identity_chain: global.family.david.home.my_pc
  last_known_attachment: hub_home_001
  last_verified_move: move_456
  trust_status: known_valid
```

---

## 33. Operation: Query Peer or Witness

Purpose:

```text
Ask sibling, peer, or witness hubs about a device history or conflict.
```

Used when:

```text
identity conflict appears
move between registry trees occurs
a parent lacks enough information
a previous hub must confirm release or last attachment
```

Example:

```yaml
witness_query:
  query_id: query_077
  query_type: confirm_last_attachment
  device_id: dev_A9F3
  claimed_previous_hub: hub_home_001
  claimed_new_hub: hub_office_007
  move_contract: move_456
```

Possible response:

```yaml
witness_query_response:
  query_id: query_077
  result: confirmed
  confidence: high
  notes: device_marked_in_transit_before_new_registration
```

---

## 34. Record Freshness and Expiration

Not all records should live equally long.

Suggested freshness model:

```text
Passport record         = long-lived
Device identity record  = long-lived
Label mapping           = medium/long-lived, changes on rename
Current attachment      = short-lived
Checkpoint state        = very short-lived
Local session           = short/medium-lived
Move contract           = long-lived audit record
Parent attestation      = short-lived
Route hint cache        = very short-lived
Conflict record         = until resolved plus retention window
```

Example freshness policy:

```yaml
freshness_policy:
  attachment_ttl_ms: 30000
  checkpoint_ttl_ms:
    tier_0: 3600000
    tier_1: 60000
    tier_2: 10000
    tier_3: 1000
  parent_attestation_ttl_ms: 600000
  route_hint_ttl_ms: 5000
  cache_default_ttl_ms: 300000
```

---

## 35. State Update Priority

When records disagree, newer is not always better.

Suggested priority order:

```text
revocation overrides everything
conflict state overrides normal valid state
verified move contract overrides stale attachment
fresh checkpoint overrides older checkpoint
parent attestation expires quickly
cached route hint is advisory only
```

Example:

```text
A cached record says device is online at hub_home_001.
A verified move contract says device moved to hub_office_007.
The move contract wins.
```

---

## 36. Conflict Resolution Strategy

Registry conflict handling should follow a staged process.

```text
1. Detect conflict.
2. Freeze risky operations.
3. Preserve safe minimal access if policy allows.
4. Query local records.
5. Query parent or previous hub.
6. Query witness hubs if needed.
7. Require device proof if needed.
8. Resolve, quarantine, or reject.
9. Log event.
10. Hand summary upward.
```

Example decision:

```yaml
conflict_resolution_result:
  conflict_id: conflict_002
  conflict_type: duplicate_device_id
  winning_claim: hub_office_007
  losing_claim: hub_home_001
  reason: valid_move_contract_and_recent_device_signature
  actions:
    - update_attachment_to_hub_office_007
    - mark_home_claim_stale
    - resume_lanes_after_route_update
```

---

## 37. Privacy Levels

Registry records may expose different detail levels.

Possible visibility levels:

```text
private_local
parent_summary
federated_summary
public_service_record
anonymous_presence
```

Example:

```yaml
visibility_policy:
  device_id: dev_A9F3
  local_hub_visibility: full_record
  parent_hub_visibility: identity_anchor_summary
  peer_hub_visibility: proof_only
  public_visibility: none
```

Privacy principle:

```text
A hub should expose the least information needed for verification, routing, and conflict prevention.
```

---

## 38. Service Records

Some devices may host services.

A Registry Hub may store service records separately from device identity records.

Example:

```yaml
service_record:
  service_id: svc_001
  service_label: media_server
  host_device_id: dev_A9F3
  service_path: global.family.david.home.my_pc.media_server
  service_type: http_like
  advertised: local_only
  required_capabilities:
    host_device_can_host_services: true
  current_state: available
```

Service records help avoid overloading device labels with application-level services.

Questions:

```text
Can multiple services live under one device?
Can a service move independently of the device?
Can a service have its own passport?
```

---

## 39. DNS / URL Alias Records

DARWIN may support DNS-like aliases or public names pointing at DARWIN identity chains.

Example:

```yaml
alias_record:
  alias: example.com
  alias_type: dns_bridge
  target_identity_chain: global.registry.us.hostingcluster7.webnode3.example_service
  target_device_id: dev_WEB123
  issuer: registrar_hub_001
  status: active
  ttl_ms: 300000
```

This allows:

```text
human domain → DARWIN identity chain → current attachment → traffic route
```

Alias records should be policy-controlled because public names can create broader visibility.

---

## 40. Branch Growth Metrics

Registry Hubs can collect metrics that help decide when to create new logical or physical branches.

Registry pressure metrics:

```text
device_count
active_device_count
lookup_rate
lookup_miss_rate
upward_query_rate
label_conflict_rate
move_contract_rate
checkpoint_update_rate
cache_invalidations
conflict_count
summary_size
```

Traffic-adjacent metrics:

```text
cross_tree_route_requests
route_probe_failures
in_transit_frequency
lane_pause_frequency
average_relocation_duration
route_update_frequency
```

Example metrics record:

```yaml
registry_metrics:
  hub_id: hub_home_001
  sample_window_ms: 60000
  device_count: 84
  active_device_count: 31
  lookup_rate_per_min: 240
  lookup_miss_rate: 0.08
  label_conflict_count: 2
  move_contract_count: 5
  upward_query_count: 17
  recommendation: no_split_needed
```

A heavily loaded hub might recommend:

```text
create child registry scope
promote child hub
add traffic bridge
increase summary frequency
split IoT devices into separate logical branch
```

---

## 41. Minimal Simulator Data Model

For the first simulator, use a simplified model.

Minimum objects:

```yaml
RegistryHub:
  hub_id: string
  scope_path: string
  parent_hub_id: string | null
  devices: map[device_id, LocalDeviceRecord]
  labels: map[label, device_id]
  passports: map[passport_id, PassportRecord]
  attachments: map[device_id, AttachmentRecord]
  checkpoints: map[device_id, CheckpointState]
  moves: map[device_id, list[MoveRecord]]
  conflicts: map[conflict_id, ConflictRecord]
  summaries: map[summary_version, UpwardSummary]
```

Minimum operations:

```text
register_device()
resolve_label()
resolve_device_id()
mark_in_transit()
update_attachment()
record_checkpoint()
assign_temp_label()
create_move_record()
hand_up_summary()
query_parent()
```

Minimum test scenarios:

```text
register two devices with different labels
register two devices with same label
resolve local label
resolve known device_id
mark device in_transit
move device to another hub
update parent summary
detect duplicate device_id conflict
```

---

## 42. Example Complete Hub Snapshot

```yaml
registry_hub_snapshot:
  hub_record:
    hub_id: hub_home_001
    hub_label: home
    scope_path: global.family.david.home
    parent_hub_id: hub_david_001
    roles:
      registry: true
      traffic: true

  label_index:
    my_pc: dev_A9F3
    printer: dev_B2C8

  local_devices:
    dev_A9F3:
      current_label: my_pc
      full_identity_chain: global.family.david.home.my_pc
      passport_id: cert_123
      current_attachment: hub_home_001
      current_state: online
      checkpoint_tier: 2
      local_session_id: sess_8821
    dev_B2C8:
      current_label: printer
      full_identity_chain: global.family.david.home.printer
      passport_id: cert_222
      current_attachment: hub_home_001
      current_state: idle
      checkpoint_tier: 1
      local_session_id: sess_8822

  attachment_index:
    dev_A9F3:
      current_attachment: hub_home_001
      state: online
      last_updated: 2026-05-26T12:06:00Z
    dev_B2C8:
      current_attachment: hub_home_001
      state: idle
      last_updated: 2026-05-26T12:01:00Z

  checkpoint_state_table:
    dev_A9F3:
      state: online
      last_checkpoint_at: 2026-05-26T12:06:00Z
      missed_checkpoint_count: 0
    dev_B2C8:
      state: idle
      last_checkpoint_at: 2026-05-26T12:01:00Z
      missed_checkpoint_count: 0

  upward_summary:
    summary_version: 18
    generated_at: 2026-05-26T12:06:00Z
    devices:
      - device_id: dev_A9F3
        identity_chain: global.family.david.home.my_pc
        current_state: online
      - device_id: dev_B2C8
        identity_chain: global.family.david.home.printer
        current_state: idle
```

---

## 43. Open Questions

### Scope and Authority

- Can a Registry Hub govern multiple scopes?
- Can two Registry Hubs share authority over one scope?
- How is authority transferred between hubs?
- What happens when a parent hub disappears?

### Data Storage

- Should records be stored as append-only events, mutable tables, or both?
- How much history should a local hub retain?
- Should move history be compacted?
- What data must be durable across reboot?

### Summary Propagation

- How often should hubs hand summaries upward?
- Should summaries be push-based, pull-based, or hybrid?
- How many parent levels should receive device summaries?
- How much privacy should be preserved in summaries?

### Conflict Handling

- Which conflicts require human/admin intervention?
- Can temporary labels become permanent automatically?
- What is the default behavior for duplicate device_id claims?
- How long should conflict records be retained?

### Caching

- What TTLs should different record types use?
- Can route hints be cached by Registry Hubs, or only Traffic Hubs?
- How are stale caches invalidated after moves?
- Should revocation updates flush related cache entries immediately?

### Service Records

- Are services children of devices, siblings of devices, or separate identity actors?
- Can a service move between devices?
- Can a domain alias target a service rather than a device?

### Scaling

- What metrics trigger a recommendation to split a registry scope?
- Can a hub automatically create a child scope?
- Can branch growth be simulated before being applied?
- How does registry scaling coordinate with traffic scaling?

---

## 44. Working Summary

A DARWIN Registry Hub is the scoped memory of the network. It does not need to know everything, but it must know its local namespace, its devices, their passports, their latest attachments, their checkpoint states, their movement history, and enough summaries to help parent hubs recognize devices when they move.

The central registry rule is:

```text
Know local truth in detail, hand upward only what is needed, and escalate sideways only when conflict or movement requires it.
```

In the travel metaphor:

```text
The Registry Hub is the station office. It knows who checked in here, what name they used, which passport they showed, whether they boarded, whether they left, and which higher office needs the summary.
```

