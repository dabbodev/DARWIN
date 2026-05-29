# DARWIN Packet, Checkpoint, and Lane Protocol v0.1

**Project name:** DARWIN  
**Document:** Packet, Checkpoint, and Lane Protocol  
**Version:** v0.1  
**Status:** Concept draft / protocol behavior sketch  
**Related documents:**

- DARWIN Design Dossier v0.1
- DARWIN Identity, Trust, and Authentication Model v0.1

---

## 1. Purpose

This document defines the first draft of DARWIN’s packet, checkpoint, and logical lane behavior.

The core question is:

```text
How does DARWIN move information while preserving identity, continuity, and relocation state?
```

DARWIN treats traffic as more than anonymous packets moving through a route. It tracks device identity, lane state, checkpoint state, and relocation events.

This document defines:

```text
packet classes
packet headers
checkpoint packets
lane creation
lane states
pause/resume behavior
in-transit signaling
relocation handoff
flow control
acknowledgment and sequence handling
error and quarantine signaling
simulator-ready message objects
```

This is not yet a wire protocol. It is a protocol model that can later be converted into schemas, code, and test cases.

---

## 2. Core Principle

DARWIN separates raw delivery from logical continuity.

Traditional packet flow often asks:

```text
Where should this packet go right now?
```

DARWIN also asks:

```text
Which device identity owns this flow?
What lane does this packet belong to?
Is the recipient active, paused, offline, or in transit?
Should the sender continue, pause, retry, reroute, or terminate?
```

The central rule:

```text
Packets move through traffic paths, but lanes belong to authenticated device identities.
```

---

## 3. Major Concepts

### 3.1 Packet

A Packet is a unit of information exchanged between DARWIN actors.

A packet may carry:

```text
application data
checkpoint state
lane control state
routing hints
authentication tags
error information
relocation notices
```

Packets are not all equal. A tiny checkpoint packet should not behave like a large data packet or a relocation contract notice.

---

### 3.2 Checkpoint

A Checkpoint is a lightweight status signal.

It tells the network:

```text
I am online.
I am idle.
I am moving.
I am in transit.
I timed out.
I am quarantined.
I still own this local session.
```

Checkpoint packets help hubs maintain a living view of device and lane state.

---

### 3.3 Logical Lane

A Logical Lane is a persistent connection relationship between devices.

A lane is tied to:

```text
source device identity
target device identity
session/lane ID
current route
sequence state
acknowledgment state
flow state
relocation state
```

A lane can pause, reroute, and resume if a device moves.

---

### 3.4 Control Signal

A Control Signal is a packet or packet-like message that changes state.

Examples:

```text
pause transmission
resume transmission
recipient in transit
route changed
lane terminated
proof required
checkpoint required
quarantine started
```

---

### 3.5 Routing Hint

A Routing Hint is partial information about how a device may currently be reached.

Routing hints are not identity proof.

Example:

```yaml
routing_hint:
  target_device: dev_A9F3
  last_known_hub: hub_home_001
  possible_next_hub: hub_office_007
  confidence: medium
```

---

## 4. Packet Classes

DARWIN packets can be grouped into several classes.

```text
DATA       = carries application payload
CHECKPOINT = carries device or lane status
CONTROL    = changes lane or route state
AUTH       = challenge, proof, or authentication-related signal
REGISTRY   = lookup, summary, registration, or history query
MOVE       = relocation, in-transit, or move-contract-related signal
ERROR      = failure, rejection, conflict, or quarantine notice
```

Example:

```yaml
packet_class: CHECKPOINT
packet_type: device_state_checkpoint
```

---

## 5. Packet Type Catalog

### 5.1 Data Packets

```text
data_payload
fragmented_data_payload
lane_data_keepalive
```

### 5.2 Checkpoint Packets

```text
device_state_checkpoint
lane_state_checkpoint
hub_state_checkpoint
route_health_checkpoint
checkpoint_ack
checkpoint_request
```

### 5.3 Control Packets

```text
lane_open
lane_open_ack
lane_pause
lane_resume
lane_close
lane_reset
flow_hold
flow_release
route_update
route_probe
route_probe_response
```

### 5.4 Authentication Packets

```text
auth_challenge
auth_proof
auth_success
auth_failed
session_rotate
proof_required
```

### 5.5 Registry Packets

```text
registry_lookup
registry_lookup_response
registry_summary_update
registry_history_query
registry_history_response
issuer_trust_query
issuer_trust_response
```

### 5.6 Movement Packets

```text
in_transit_notice
move_prepare
move_claim
move_verify_request
move_verify_response
move_contract_notice
relocation_pause
relocation_resume
relocation_failed
```

### 5.7 Error Packets

```text
unknown_device
invalid_passport
invalid_auth_tag
stale_counter
replay_detected
route_unavailable
lane_conflict
identity_conflict
quarantine_notice
permission_denied
```

---

## 6. Common Packet Header

Most DARWIN packets should share a common header shape.

Example:

```yaml
packet_header:
  protocol: DARWIN
  protocol_version: 0.1
  packet_id: pkt_001
  packet_class: DATA
  packet_type: data_payload
  source_device_id: dev_A9F3
  target_device_id: dev_B2C8
  source_hub_id: hub_home_001
  target_hub_hint: hub_office_007
  lane_id: lane_S991
  session_id: sess_8821
  sequence_number: 1043
  timestamp: 2026-05-26T12:06:00Z
  ttl: 12
  priority: normal
  auth_tag: AUTH_TAG
```

Not every field is required for every packet.

A registry lookup might not have a lane ID. A broadcast route probe might not have a target device ID. A checkpoint might not carry application data.

---

## 7. Packet Header Fields

### 7.1 `protocol`

Identifies the packet as a DARWIN packet.

Example:

```text
DARWIN
```

---

### 7.2 `protocol_version`

Indicates the protocol version.

Example:

```text
0.1
```

---

### 7.3 `packet_id`

Unique packet identifier.

Used for tracing, acknowledgment, debugging, replay detection, and simulation.

---

### 7.4 `packet_class`

Broad packet category.

Examples:

```text
DATA
CHECKPOINT
CONTROL
AUTH
REGISTRY
MOVE
ERROR
```

---

### 7.5 `packet_type`

Specific packet action.

Example:

```text
lane_pause
```

---

### 7.6 `source_device_id` and `target_device_id`

Durable identities of the source and target devices.

These should not be replaced by MAC or IP addresses.

---

### 7.7 `source_hub_id` and `target_hub_hint`

Current or likely hub positions.

These are routing clues, not identity proof.

---

### 7.8 `lane_id`

The logical lane associated with the packet.

Control packets may create, pause, resume, or close lanes.

---

### 7.9 `session_id`

The local authentication session associated with the packet.

This helps bind packet traffic to a verified local state.

---

### 7.10 `sequence_number`

Monotonic counter for lane ordering and replay protection.

---

### 7.11 `timestamp`

Time the packet was created.

Used for expiration, debugging, and replay protection.

---

### 7.12 `ttl`

Time-to-live or hop limit.

Prevents packets from wandering forever through the forest wearing a tiny lost hat.

---

### 7.13 `priority`

Suggested priority.

Possible values:

```text
low
normal
high
critical
control
```

Control and emergency movement packets may receive higher priority than bulk data.

---

### 7.14 `auth_tag`

Lightweight authenticity marker.

Conceptual form:

```text
auth_tag = MAC(local_session_secret, packet_header_without_auth_tag | payload_hash)
```

Actual cryptographic construction is deferred to the authentication specification.

---

## 8. Payload Envelope

DARWIN packet payloads should use a typed envelope.

Example:

```yaml
packet:
  header:
    packet_id: pkt_001
    packet_class: DATA
    packet_type: data_payload
  payload:
    content_type: application/octet-stream
    data: PAYLOAD_BYTES_OR_REFERENCE
```

For simulator purposes, payload can be plain JSON/YAML.

For real networking, payload may become binary, framed, compressed, or encrypted.

---

## 9. Device State Values

Checkpoint packets may report device state.

Core device states:

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

Simplified categories:

```text
online-ish:
  online, idle, active

moving-ish:
  disconnected, in_transit, awaiting_verification

unavailable-ish:
  timed_out, offline

blocked-ish:
  quarantined, revoked, rejected
```

---

## 10. Lane State Values

Logical lanes may move through these states:

```text
none
opening
active
flow_hold
paused_relocation
awaiting_verification
rerouting
resumed
closing
terminated
reset
conflict_detected
quarantined
```

Primary lane lifecycle:

```text
none
→ opening
→ active
→ paused_relocation
→ awaiting_verification
→ rerouting
→ resumed
→ active
→ closing
→ terminated
```

Failure lifecycle:

```text
active
→ conflict_detected
→ quarantined
→ terminated
```

---

## 11. Lane Ownership

A lane is not owned only by a route.

A lane is defined by:

```text
source device identity
target device identity
lane_id
current sequence state
current authentication state
current route state
current flow state
```

Example lane record:

```yaml
lane_record:
  lane_id: lane_S991
  source_device_id: dev_A9F3
  target_device_id: dev_B2C8
  source_session_id: sess_A
  target_session_id: sess_B
  state: active
  current_route:
    - hub_home_001
    - hub_family_001
    - hub_office_007
  last_sent_sequence: 1044
  last_acknowledged_sequence: 1043
  flow_window: 32
  relocation_hold_until: null
```

Open question:

```text
Who is the authoritative owner of lane state: sender, receiver, traffic hub, registry hub, or a lane coordinator?
```

For the simulator, lane state can be owned by a simulated Traffic Hub or Lane Manager object.

---

## 12. Opening a Lane

Lane creation begins when a source wants persistent communication with a target.

Basic flow:

```text
1. Source asks local hub to open lane.
2. Local hub resolves target device identity.
3. Registry or cache returns target attachment / route hint.
4. Traffic route is selected.
5. Source sends lane_open.
6. Target or target hub replies lane_open_ack.
7. Lane enters active state.
```

Example `lane_open` packet:

```yaml
packet:
  header:
    packet_class: CONTROL
    packet_type: lane_open
    source_device_id: dev_A9F3
    target_device_id: dev_B2C8
    lane_id: lane_S991
    sequence_number: 1
  payload:
    requested_mode: reliable_ordered
    requested_checkpoint_support: true
    requested_relocation_support: true
    max_flow_window: 32
```

Example `lane_open_ack` packet:

```yaml
packet:
  header:
    packet_class: CONTROL
    packet_type: lane_open_ack
    source_device_id: dev_B2C8
    target_device_id: dev_A9F3
    lane_id: lane_S991
    sequence_number: 1
  payload:
    accepted: true
    lane_state: active
    negotiated_mode: reliable_ordered
    checkpoint_support: true
    relocation_support: true
    flow_window: 16
```

---

## 13. Lane Modes

Different applications need different guarantees.

Possible lane modes:

```text
best_effort
reliable_unordered
reliable_ordered
realtime_loss_tolerant
critical_ordered
checkpoint_only
```

### 13.1 `best_effort`

Packets may be dropped. No strong recovery.

Useful for:

```text
telemetry
low-priority events
non-critical updates
```

---

### 13.2 `reliable_unordered`

Packets should arrive, but order is not strict.

Useful for:

```text
object sync
parallel chunks
background data
```

---

### 13.3 `reliable_ordered`

Packets should arrive in sequence.

Useful for:

```text
file transfer
command streams
stateful app sessions
```

---

### 13.4 `realtime_loss_tolerant`

Low latency matters more than perfect recovery.

Useful for:

```text
voice
video
game state updates
```

---

### 13.5 `critical_ordered`

Strict validation and recovery.

Useful for:

```text
industrial controls
medical systems
financial commands
critical infrastructure
```

---

### 13.6 `checkpoint_only`

Only status messages are exchanged.

Useful for:

```text
sleepy IoT devices
simple sensors
presence-only devices
```

---

## 14. Data Packet Flow

Basic data packet:

```yaml
packet:
  header:
    packet_class: DATA
    packet_type: data_payload
    packet_id: pkt_1043
    source_device_id: dev_A9F3
    target_device_id: dev_B2C8
    lane_id: lane_S991
    session_id: sess_8821
    sequence_number: 1043
    ttl: 12
    priority: normal
    auth_tag: AUTH_TAG
  payload:
    content_type: application/json
    data:
      message: hello
```

Receiving hub checks:

```text
Is the lane active?
Is the session valid?
Is the sequence number expected or acceptable?
Is the auth tag valid?
Is the recipient reachable?
Should this packet be forwarded, buffered, dropped, or paused?
```

---

## 15. Acknowledgment Model

DARWIN lanes may use acknowledgment packets depending on lane mode.

Example `lane_ack` packet:

```yaml
packet:
  header:
    packet_class: CONTROL
    packet_type: lane_ack
    source_device_id: dev_B2C8
    target_device_id: dev_A9F3
    lane_id: lane_S991
    sequence_number: 1043
  payload:
    acknowledged_through: 1043
    missing_sequences: []
    receiver_state: active
```

Acks can support:

```text
retransmission
resume-from-last-confirmed
flow control
relocation recovery
loss detection
```

For low-priority lanes, acknowledgments may be sparse or omitted.

---

## 16. Flow Control

DARWIN should prevent senders from overwhelming hubs, recipients, or relocation buffers.

Flow control states:

```text
normal
slow_down
flow_hold
paused_relocation
blocked
terminated
```

Example `flow_hold` packet:

```yaml
packet:
  header:
    packet_class: CONTROL
    packet_type: flow_hold
    source_hub_id: hub_home_001
    target_device_id: dev_A9F3
    lane_id: lane_S991
  payload:
    reason: recipient_in_transit
    hold_new_packets: true
    retain_unacked_window: true
    hold_until_ms: 3000
```

When the sender receives `flow_hold`, it should:

```text
stop sending new data packets
keep lane metadata
retain unacknowledged packet state if lane mode requires it
wait for flow_release, relocation_resume, lane_close, or timeout
```

---

## 17. Checkpoint Packet Structure

A checkpoint packet reports state without carrying normal application traffic.

Example:

```yaml
packet:
  header:
    packet_class: CHECKPOINT
    packet_type: device_state_checkpoint
    packet_id: cp_pkt_001
    source_device_id: dev_A9F3
    source_hub_id: hub_home_001
    session_id: sess_8821
    sequence_number: 1044
    timestamp: 2026-05-26T12:06:00Z
    priority: low
    auth_tag: AUTH_TAG
  payload:
    device_state: online
    checkpoint_tier: 2
    battery_level: 91
    active_lane_count: 3
    last_seen_route:
      - hub_home_001
      - hub_family_001
    notes: null
```

---

## 18. Checkpoint Tiers

DARWIN supports tiered checkpoint behavior.

### 18.1 Tier 0: Sparse / Passive IoT

```yaml
checkpoint_policy:
  tier: 0
  interval: 30m
  lane_support: checkpoint_only
  relocation_support: false
  parent_assisted: optional
```

Behavior:

```text
rare checkpoints
minimal payload
usually no lane preservation
may sleep for long periods
```

---

### 18.2 Tier 1: Normal Smart Device

```yaml
checkpoint_policy:
  tier: 1
  interval: 30s
  lane_support: basic
  relocation_support: local_only
  parent_assisted: false
```

Behavior:

```text
regular local liveness
basic state reporting
limited relocation support
```

---

### 18.3 Tier 2: Mobile Interactive Device

```yaml
checkpoint_policy:
  tier: 2
  interval: 1s-5s
  lane_support: persistent
  relocation_support: true
  transit_notice: true
```

Behavior:

```text
active checkpointing
supports in_transit state
supports lane pause/resume
useful for phones, laptops, vehicles, wearables
```

---

### 18.4 Tier 3: Critical / Real-Time Device

```yaml
checkpoint_policy:
  tier: 3
  interval: continuous_or_subsecond
  lane_support: persistent_critical
  relocation_support: predictive
  standby_routes: true
```

Behavior:

```text
high-frequency validation
predictive rerouting
hot standby lanes
strict auth and recovery
```

---

## 19. Checkpoint State Transitions

A device may transition through checkpoint states.

Normal lifecycle:

```text
unknown
→ claiming_identity
→ locally_authenticated
→ online
→ idle
→ active
→ idle
→ offline
```

Movement lifecycle:

```text
online
→ disconnected
→ in_transit
→ awaiting_verification
→ online
```

Failure lifecycle:

```text
online
→ timed_out
→ offline
```

Security lifecycle:

```text
online
→ awaiting_verification
→ quarantined
→ revoked/rejected
```

---

## 20. In-Transit Signaling

In-transit signaling is one of DARWIN’s core mobility features.

When a device disconnects intentionally or predictably, a hub can emit an `in_transit_notice`.

Example:

```yaml
packet:
  header:
    packet_class: MOVE
    packet_type: in_transit_notice
    source_hub_id: hub_home_001
    target_device_id: dev_A9F3
    priority: control
  payload:
    device_id: dev_A9F3
    previous_attachment: hub_home_001
    previous_scope: global.family.david.home
    affected_lanes:
      - lane_S991
      - lane_S992
    expected_reconnect_window_ms: 3000
    sender_action: pause_new_packets
    buffer_policy: minimal_hold
```

The network should treat `in_transit` differently from `offline`.

```text
offline    = device is unavailable and may not return soon
in_transit = device is relocating and may reappear shortly
```

---

## 21. Relocation Pause Flow

When a recipient enters `in_transit`, active lanes should pause gracefully.

Flow:

```text
1. Hub A loses or releases contact with device.
2. Hub A marks device in_transit.
3. Hub A sends in_transit_notice.
4. Hub A sends flow_hold or lane_pause to senders.
5. Senders stop sending new packets.
6. Hubs retain minimal lane state.
7. Unacknowledged packets are retained, dropped, or marked pending depending on lane mode.
```

Example `lane_pause`:

```yaml
packet:
  header:
    packet_class: CONTROL
    packet_type: lane_pause
    source_hub_id: hub_home_001
    lane_id: lane_S991
    priority: control
  payload:
    reason: recipient_in_transit
    affected_device: dev_A9F3
    last_confirmed_packet: 1042
    pause_new_packets: true
    hold_window_ms: 3000
```

---

## 22. Relocation Resume Flow

When the moving device registers at a new hub, the new hub verifies continuity and resumes lanes.

Flow:

```text
1. Device connects to Hub B.
2. Device presents passport or move proof.
3. Hub B verifies identity and movement.
4. Hub B queries registry history if needed.
5. Hub B announces new attachment.
6. Traffic route is updated.
7. Hub B sends relocation_resume or lane_resume.
8. Senders resume from last confirmed packet.
```

Example `relocation_resume`:

```yaml
packet:
  header:
    packet_class: MOVE
    packet_type: relocation_resume
    source_hub_id: hub_office_007
    target_device_id: dev_A9F3
    priority: control
  payload:
    device_id: dev_A9F3
    new_attachment: hub_office_007
    new_scope: global.family.david.office
    verified_move_contract: move_456
    affected_lanes:
      - lane_S991
    resume_from_packet: 1043
    route_update_required: true
```

Example `lane_resume`:

```yaml
packet:
  header:
    packet_class: CONTROL
    packet_type: lane_resume
    source_hub_id: hub_office_007
    lane_id: lane_S991
    priority: control
  payload:
    state: resumed
    resume_from_packet: 1043
    new_route:
      - hub_source_003
      - hub_regional_002
      - hub_office_007
```

---

## 23. Relocation Failure

Relocation may fail.

Reasons:

```text
device did not reappear
passport verification failed
move contract invalid
conflicting active identity detected
new hub not trusted
hold window expired
route unavailable
```

Example `relocation_failed`:

```yaml
packet:
  header:
    packet_class: MOVE
    packet_type: relocation_failed
    source_hub_id: hub_home_001
    target_device_id: dev_A9F3
    priority: control
  payload:
    device_id: dev_A9F3
    affected_lanes:
      - lane_S991
    reason: hold_window_expired
    recommended_action: lane_close
```

Possible responses:

```text
extend hold window
retry lookup
close lane
quarantine identity
escalate to registry
notify application
```

---

## 24. Buffer Policy

DARWIN should avoid unbounded buffering during relocation.

Buffer policies:

```text
none
minimal_hold
retain_unacked_only
bounded_buffer
application_defined
critical_preserve
```

### 24.1 `none`

No buffering. New packets are rejected or dropped.

Useful for:

```text
realtime loss-tolerant lanes
low priority streams
```

---

### 24.2 `minimal_hold`

Keep only lane metadata and last confirmed sequence.

Useful for:

```text
most mobile lane pause/resume cases
```

---

### 24.3 `retain_unacked_only`

Keep packets that were sent but not acknowledged.

Useful for:

```text
reliable lanes
file transfers
ordered streams
```

---

### 24.4 `bounded_buffer`

Buffer up to a defined limit.

Example:

```yaml
buffer_policy:
  mode: bounded_buffer
  max_packets: 64
  max_bytes: 1048576
  overflow_action: sender_pause
```

---

### 24.5 `critical_preserve`

Aggressively preserve state and packets.

Useful only for high-priority systems.

Must be limited to avoid memory abuse.

---

## 25. Route Updates

A route update tells lane participants that the traffic path changed.

Example:

```yaml
packet:
  header:
    packet_class: CONTROL
    packet_type: route_update
    source_hub_id: hub_regional_002
    lane_id: lane_S991
    priority: control
  payload:
    target_device_id: dev_A9F3
    old_route:
      - hub_source_003
      - hub_home_001
    new_route:
      - hub_source_003
      - hub_regional_002
      - hub_office_007
    reason: relocation_verified
    effective_after_sequence: 1042
```

Route updates should be authenticated.

A malicious route update could hijack a lane.

---

## 26. Route Probing

Traffic Hubs may probe routes before or during lane operation.

Example `route_probe`:

```yaml
packet:
  header:
    packet_class: CONTROL
    packet_type: route_probe
    source_hub_id: hub_source_003
    target_device_id: dev_A9F3
    priority: control
  payload:
    probe_id: probe_001
    requested_metrics:
      - latency
      - reachability
      - congestion
      - auth_path_validity
```

Example `route_probe_response`:

```yaml
packet:
  header:
    packet_class: CONTROL
    packet_type: route_probe_response
    source_hub_id: hub_office_007
    target_hub_hint: hub_source_003
  payload:
    probe_id: probe_001
    reachable: true
    latency_ms: 18
    congestion: low
    auth_path_validity: verified
```

Route probes can support:

```text
shortest path selection
failover
branch growth decisions
relocation planning
quality monitoring
```

---

## 27. Registry Interaction Packets

Lanes and checkpoints may trigger registry lookups.

Example `registry_lookup`:

```yaml
packet:
  header:
    packet_class: REGISTRY
    packet_type: registry_lookup
    source_hub_id: hub_source_003
    priority: control
  payload:
    query_type: device_id_to_current_attachment
    device_id: dev_A9F3
    requested_fields:
      - current_attachment
      - current_state
      - last_checkpoint
      - trusted_move_status
```

Example `registry_lookup_response`:

```yaml
packet:
  header:
    packet_class: REGISTRY
    packet_type: registry_lookup_response
    source_hub_id: hub_family_001
    target_hub_hint: hub_source_003
  payload:
    device_id: dev_A9F3
    current_attachment: hub_office_007
    current_state: online
    last_checkpoint: 2026-05-26T12:06:00Z
    trust_status: verified
```

---

## 28. Checkpoint Requests

A hub may request a checkpoint from a device or child hub.

Example:

```yaml
packet:
  header:
    packet_class: CHECKPOINT
    packet_type: checkpoint_request
    source_hub_id: hub_home_001
    target_device_id: dev_A9F3
    priority: control
  payload:
    requested_state_fields:
      - device_state
      - active_lane_count
      - battery_level
      - current_hub
    reason: local_liveness_check
    response_required_within_ms: 1000
```

The device responds with `device_state_checkpoint` or an error.

---

## 29. Checkpoint Acknowledgment

Some checkpoint modes require acknowledgments.

Example:

```yaml
packet:
  header:
    packet_class: CHECKPOINT
    packet_type: checkpoint_ack
    source_hub_id: hub_home_001
    target_device_id: dev_A9F3
  payload:
    checkpoint_id: cp_001
    accepted: true
    updated_device_state: online
    next_expected_checkpoint_within_ms: 5000
```

For sleepy devices, checkpoint acknowledgments can include next sleep/wake policy.

---

## 30. Sleepy IoT Behavior

Low-power devices may not maintain active lanes.

Sleepy IoT checkpoint flow:

```text
1. Device wakes.
2. Device sends sparse checkpoint.
3. Hub validates checkpoint auth tag.
4. Hub updates last_seen and state.
5. Hub optionally replies with checkpoint_ack.
6. Device sleeps again.
```

Example:

```yaml
packet:
  header:
    packet_class: CHECKPOINT
    packet_type: device_state_checkpoint
    source_device_id: dev_sensor_001
    source_hub_id: hub_home_001
    priority: low
  payload:
    device_state: idle
    checkpoint_tier: 0
    battery_level: 74
    sensor_summary:
      temperature_c: 21.4
    next_wake_estimate: 2026-05-26T12:36:00Z
```

Special concern:

```text
If a parent hub reports on behalf of a sleeping device, DARWIN must prevent the parent from lying indefinitely.
```

Possible mitigations:

```text
periodic direct proof from device
short-lived parent attestations
sleep schedule commitments
random wake challenges
low-frequency passport revalidation
```

---

## 31. Error Handling

DARWIN should use explicit error packets rather than silent failure where possible.

Example `invalid_auth_tag`:

```yaml
packet:
  header:
    packet_class: ERROR
    packet_type: invalid_auth_tag
    source_hub_id: hub_home_001
    target_device_id: dev_A9F3
    priority: control
  payload:
    failed_packet_id: pkt_1043
    reason: auth_tag_mismatch
    action_taken: request_reauthentication
```

Example `route_unavailable`:

```yaml
packet:
  header:
    packet_class: ERROR
    packet_type: route_unavailable
    source_hub_id: hub_regional_002
    target_device_id: dev_A9F3
  payload:
    reason: target_in_transit
    recommended_action: pause_lane
    retry_after_ms: 3000
```

---

## 32. Quarantine Signaling

If a device or lane becomes suspicious, hubs can send a quarantine notice.

Example:

```yaml
packet:
  header:
    packet_class: ERROR
    packet_type: quarantine_notice
    source_hub_id: hub_home_001
    target_device_id: dev_A9F3
    priority: critical
  payload:
    reason: rolling_proof_failed
    affected_lanes:
      - lane_S991
    allowed_actions:
      - present_passport
      - request_recovery
      - sync_time
    denied_actions:
      - send_data_payload
      - act_as_parent_hub
      - open_new_lane
```

Lane response:

```text
active → quarantined
```

Device response:

```text
online → awaiting_verification → quarantined
```

---

## 33. Sequence Numbers and Resume Behavior

Sequence numbers support ordered delivery, replay protection, and relocation resume.

During relocation, the network should record:

```text
last_sent_sequence
last_received_sequence
last_acknowledged_sequence
resume_from_sequence
```

Example:

```yaml
relocation_sequence_state:
  lane_id: lane_S991
  last_sent_sequence: 1045
  last_acknowledged_sequence: 1042
  resume_from_sequence: 1043
  unacked_sequences:
    - 1043
    - 1044
    - 1045
```

Resume decision depends on lane mode:

```text
best_effort              → resume with newest packet
reliable_unordered       → resend missing packets if known
reliable_ordered         → resume from first unacknowledged packet
realtime_loss_tolerant   → skip stale packets
critical_ordered         → verify full sequence state before resume
```

---

## 34. Lane Timeout Policy

A lane should not remain paused forever.

Timeout variables:

```text
hold_window_ms
max_relocation_attempts
max_idle_time_ms
checkpoint_timeout_ms
verification_timeout_ms
```

Example policy:

```yaml
lane_timeout_policy:
  lane_mode: reliable_ordered
  hold_window_ms: 3000
  max_hold_extensions: 2
  verification_timeout_ms: 5000
  on_timeout: lane_close
```

For critical lanes:

```yaml
lane_timeout_policy:
  lane_mode: critical_ordered
  hold_window_ms: 10000
  max_hold_extensions: 5
  verification_timeout_ms: 15000
  on_timeout: escalate_to_registry_and_operator
```

---

## 35. Priority and Scheduling

Hubs may prioritize packets.

Suggested priority order:

```text
critical security/error packets
movement and relocation packets
authentication packets
lane control packets
checkpoint packets
data packets
low-priority telemetry
```

Example priority values:

```text
critical
control
high
normal
low
bulk
```

Priority should not allow untrusted devices to starve other traffic.

A hub should validate whether a packet is allowed to claim high priority.

---

## 36. Fragmentation

Large data payloads may need fragmentation.

Example fragment packet:

```yaml
packet:
  header:
    packet_class: DATA
    packet_type: fragmented_data_payload
    source_device_id: dev_A9F3
    target_device_id: dev_B2C8
    lane_id: lane_S991
    sequence_number: 2050
  payload:
    fragment_group_id: frag_777
    fragment_index: 2
    fragment_count: 8
    payload_hash: GROUP_HASH
    fragment_data: FRAGMENT_BYTES
```

Fragmentation policy should depend on lane mode and route conditions.

Open question:

```text
Should DARWIN handle fragmentation itself, delegate to lower layers, or only model it for overlay use?
```

---

## 37. Encryption Boundary

This document focuses on packet state, not encryption design.

Possible encryption boundaries:

```text
payload only
payload + selected headers
full packet inside transport envelope
lane-level encryption
application-managed encryption
```

Important tension:

```text
Traffic hubs need enough metadata to route and manage lanes.
Applications may want payload privacy.
Registries should not need to inspect application payloads.
```

Open question:

```text
Which fields must remain visible to hubs, and which can be encrypted end-to-end?
```

---

## 38. Simulator Packet Model

The first simulator can represent packets as plain data objects.

Example Python-style conceptual object:

```yaml
DarwinPacket:
  header:
    packet_id: pkt_001
    packet_class: CONTROL
    packet_type: lane_pause
    source_device_id: dev_A9F3
    target_device_id: dev_B2C8
    lane_id: lane_S991
    sequence_number: 1042
  payload:
    reason: recipient_in_transit
    hold_window_ms: 3000
```

Simulator does not need real cryptography at first.

Instead, it can use symbolic validity fields:

```yaml
sim_auth:
  auth_tag_valid: true
  passport_valid: true
  rolling_proof_valid: true
```

Behavior comes first. Cryptographic implementation comes later.

---

## 39. Minimal Simulator Scenarios

The packet/lane simulator should test these scenarios first.

### 39.1 Normal Lane Open and Data Send

```text
Device A opens lane to Device B.
Data packets flow.
Acks update sequence state.
```

Expected result:

```text
lane enters active
packets delivered
last_acknowledged_sequence increases
```

---

### 39.2 Recipient Enters In-Transit State

```text
Device B disconnects from Hub X.
Hub X marks B in_transit.
Sender receives flow_hold.
Sender pauses new packets.
```

Expected result:

```text
lane enters paused_relocation
buffer does not grow unbounded
sender waits for resume or timeout
```

---

### 39.3 Recipient Reappears and Lane Resumes

```text
Device B registers at Hub Y.
Hub Y verifies move.
Route update is issued.
Lane resumes from last confirmed packet.
```

Expected result:

```text
lane enters rerouting then resumed then active
sender resumes from correct sequence
```

---

### 39.4 Relocation Timeout

```text
Device B enters in_transit but does not reappear.
Hold window expires.
```

Expected result:

```text
relocation_failed emitted
lane closes or escalates according to policy
```

---

### 39.5 Invalid Auth Tag

```text
Packet arrives with bad auth tag.
Hub rejects packet.
Device is challenged or quarantined.
```

Expected result:

```text
invalid_auth_tag error emitted
trust state escalates
```

---

### 39.6 Sleepy IoT Checkpoint

```text
Sensor wakes, sends checkpoint, sleeps.
Hub updates last_seen.
```

Expected result:

```text
device remains registered without active lane
checkpoint tier policy respected
```

---

## 40. Open Questions

### Packet Structure

- Which header fields are mandatory for all packets?
- Should packet IDs be globally unique or lane-local?
- Should headers be JSON-like, binary, or schema-generated?
- How much metadata should traffic hubs be allowed to see?

### Lane Ownership

- Who owns authoritative lane state?
- Can lanes be migrated between Traffic Hubs?
- Can a lane exist without a Registry Hub being aware of it?
- Can an application request a specific lane mode?

### Relocation

- How long should `in_transit` last by default?
- Should devices proactively announce intent to move?
- Can hubs predict movement and prepare standby routes?
- What happens if old and new hubs both claim the device is attached?

### Buffering

- What should the default buffer policy be?
- Should senders or hubs buffer unacknowledged packets?
- Can applications opt out of relocation buffering?
- How are buffer abuse and memory exhaustion prevented?

### Checkpoints

- How often should each tier checkpoint by default?
- Can checkpoint intervals adapt dynamically?
- Can hubs checkpoint on behalf of devices?
- How does the system detect a lying parent hub?

### Security

- Which packet classes require auth tags?
- Should all route updates be signed by hubs?
- What happens when auth state expires during relocation?
- Can checkpoint packets be encrypted while still useful to hubs?

### Routing

- Are route updates authoritative or advisory?
- Can multiple Traffic Hubs compete to route a lane?
- How are shortest paths calculated?
- How does branch-growth policy consume route health checkpoints?

---

## 41. Working Summary

DARWIN packets are not just data fragments. They are state-carrying messages that help the network understand identity, liveness, movement, routing, and continuity.

The lane model allows connections to pause, reroute, and resume when a device moves. Checkpoint packets tell hubs whether devices are online, idle, offline, timed out, in transit, quarantined, or revoked. Control packets prevent blind retransmission storms by signaling senders when a recipient is relocating. Auth tags tie packets back to local sessions so spoofed devices cannot simply borrow a MAC address and sneak onto the lane.

The central transport rule is:

```text
Do not blindly send into disappearance. Pause, verify, reroute, then resume.
```

Or in the transportation metaphor:

```text
A lane is not just a road. It is a ticketed journey between identified travelers, with checkpoints, station notices, detours, and verified boarding passes.
```

