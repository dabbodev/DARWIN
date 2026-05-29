# DARWIN Simulator Build Plan v0.1

**Project name:** DARWIN  
**Document:** Simulator Build Plan  
**Version:** v0.1  
**Status:** Implementation planning draft  
**Related documents:**

- DARWIN Design Dossier v0.1
- DARWIN Identity, Trust, and Authentication Model v0.1
- DARWIN Packet, Checkpoint, and Lane Protocol v0.1
- DARWIN Registry Hub Data Model v0.1
- DARWIN Traffic Hub and Routing Model v0.1

---

## 1. Purpose

This document defines a practical plan for building the first DARWIN simulator.

The simulator should test DARWIN behavior before attempting real networking, production cryptography, or operating system integration.

The core question is:

```text
Can the DARWIN model behave coherently when devices register, move, checkpoint, route lanes, pause traffic, resume traffic, and encounter conflicts?
```

The first simulator should prove the shape of the system, not the final wire protocol.

---

## 2. Simulator Goals

The simulator should demonstrate these core behaviors:

```text
device registration
scoped labels and identity chains
passport-like identity records
registry hand-up summaries
traffic route selection
logical lane creation
data packet forwarding
checkpoint updates
in-transit state
sender pause and flow hold
relocation and lane resume
name conflict handling
device_id conflict handling
basic trust failure and quarantine
traffic pressure metrics
branch growth recommendations
```

The simulator should make DARWIN observable. It should be easy to see what happened, why it happened, and which tables changed.

---

## 3. Non-Goals for v0.1

The first simulator should not attempt:

```text
real network sockets
production cryptography
kernel-level routing
packet capture
real DNS integration
hardware identity
real Wi-Fi roaming
distributed consensus
high-performance packet throughput
```

These can come later.

v0.1 should be an in-memory model with clear state transitions.

---

## 4. Recommended Implementation Style

The first implementation should probably be a Python simulation.

Reasons:

```text
fast iteration
simple object modeling
readable tests
easy JSON/YAML export
simple CLI tools
low ceremony
```

The simulator can later be ported or expanded into another language if needed.

Recommended stack:

```text
Python 3.11+
pytest for tests
pydantic or dataclasses for models
rich for readable CLI output
networkx optionally for graph routing experiments
PyYAML or JSON for scenario files
```

Avoid overengineering the first version. The simulator should behave like a protocol terrarium.

---

## 5. First Build Shape

The simulator should model DARWIN as objects interacting through events.

Core objects:

```text
Device
RegistryHub
TrafficHub
HybridHub
PassportRecord
MoveContract
CheckpointPacket
DarwinPacket
LogicalLane
RouteRecord
ScenarioRunner
EventLog
```

The simulator does not need real packets. A packet can be a Python object or dictionary.

---

## 6. Suggested Repository Layout

```text
darwin_sim/
  README.md
  pyproject.toml
  docs/
    DARWIN_Design_Dossier_v0_1.md
    DARWIN_Identity_Trust_Authentication_v0_1.md
    DARWIN_Packet_Checkpoint_Lane_Protocol_v0_1.md
    DARWIN_Registry_Hub_Data_Model_v0_1.md
    DARWIN_Traffic_Hub_Routing_Model_v0_1.md
    DARWIN_Simulator_Build_Plan_v0_1.md
  darwin/
    __init__.py
    ids.py
    models/
      __init__.py
      device.py
      hub.py
      passport.py
      packet.py
      lane.py
      route.py
      checkpoint.py
      events.py
      policies.py
    sim/
      __init__.py
      world.py
      runner.py
      scenarios.py
      event_log.py
      assertions.py
    registry/
      __init__.py
      operations.py
      summaries.py
      conflicts.py
    traffic/
      __init__.py
      routing.py
      lanes.py
      relocation.py
      metrics.py
    auth/
      __init__.py
      symbolic.py
      trust.py
    cli/
      __init__.py
      main.py
  scenarios/
    001_basic_registration.yaml
    002_name_conflict.yaml
    003_lane_open_and_send.yaml
    004_relocation_pause_resume.yaml
    005_relocation_timeout.yaml
    006_mac_spoof_symbolic_failure.yaml
    007_congestion_bridge_recommendation.yaml
  tests/
    test_registration.py
    test_conflicts.py
    test_lanes.py
    test_relocation.py
    test_routing.py
    test_auth_symbolic.py
```

This layout keeps the simulator organized without pretending it is a production network stack.

---

## 7. Development Phases

### Phase 0: Skeleton

Create the repo, package, basic models, and tests.

Deliverables:

```text
working Python package
basic dataclasses or pydantic models
pytest configured
one trivial scenario runs
```

Success condition:

```text
A device object and hub object can be created and printed.
```

---

### Phase 1: Registry Simulation

Implement scoped device registration.

Features:

```text
RegistryHub object
Device object
PassportRecord object
LocalDeviceRecord object
Label Index
Device ID Index
Attachment Index
register_device()
resolve_label()
resolve_device_id()
assign_temp_label()
```

Success condition:

```text
A device registers as global.family.david.home.my_pc.
A second device requesting my_pc receives my_pc_temp_<id>.
```

---

### Phase 2: Registry Hand-Up Summaries

Implement parent summary propagation.

Features:

```text
parent hub relationship
upward summary generation
summary versioning
parent summary acceptance
basic parent lookup
```

Success condition:

```text
A parent hub can answer that dev_A9F3 belongs under global.family.david.home.* based on a child summary.
```

---

### Phase 3: Traffic Routing Basics

Implement TrafficHub routing.

Features:

```text
TrafficHub object
Neighbor Table
Direct Attachment Table
Route Table
select_route()
forward_packet()
route cache
simple route cost
```

Success condition:

```text
A packet can move from Device A through Hub 1, Hub 2, and Hub 3 to Device B.
```

---

### Phase 4: Logical Lanes

Implement lane creation and data flow.

Features:

```text
LogicalLane object
lane_open
lane_open_ack
lane states
sequence numbers
acknowledgments
basic data packet forwarding
```

Success condition:

```text
Device A opens lane_S991 to Device B, sends packet 1, receives ack 1.
```

---

### Phase 5: Checkpoints

Implement device checkpoint state.

Features:

```text
CheckpointPacket object
checkpoint tiers
record_checkpoint()
missed checkpoint detection
online, idle, active, offline, timed_out states
```

Success condition:

```text
A Tier 2 mobile device updates last_checkpoint every simulated second.
A Tier 0 IoT device remains valid with sparse checkpoints.
```

---

### Phase 6: Relocation and In-Transit Flow

Implement movement as a first-class event.

Features:

```text
mark_in_transit()
flow_hold
pause_lane_for_relocation()
MoveContract symbolic record
update_attachment()
relocation_resume
resume_lane_after_relocation()
resume sequence behavior
```

Success condition:

```text
Device B moves from Hub 3 to Hub 4.
Sender pauses while B is in_transit.
Lane resumes from the correct sequence after B registers at Hub 4.
```

---

### Phase 7: Trust and Quarantine Simulation

Implement symbolic authentication outcomes.

Features:

```text
passport_valid flag
issuer_trusted flag
rolling_proof_valid flag
auth_tag_valid flag
quarantine state
security event log
MAC spoof symbolic scenario
```

Success condition:

```text
A spoofed device claiming dev_A9F3 fails rolling proof and is quarantined.
```

---

### Phase 8: Metrics and Growth Recommendations

Implement pressure metrics.

Features:

```text
lookup counts
route counts
cross-tree traffic count
lane pause count
relocation count
congestion score
traffic bridge recommendation
registry split recommendation
```

Success condition:

```text
Repeated traffic between home and office branches produces a create_traffic_bridge recommendation.
```

---

## 8. Core Data Models

### 8.1 Device

```yaml
Device:
  device_id: string
  label: string
  passport_id: string | null
  current_registry_hub: string | null
  current_traffic_hub: string | null
  state: string
  checkpoint_tier: int
```

Required methods:

```text
request_registration()
send_checkpoint()
request_lane()
disconnect()
reconnect()
```

---

### 8.2 RegistryHub

```yaml
RegistryHub:
  hub_id: string
  scope_path: string
  parent_hub_id: string | null
  devices: map
  labels: map
  passports: map
  attachments: map
  checkpoints: map
  moves: map
  conflicts: map
  summaries: map
```

Required methods:

```text
register_device()
resolve_label()
resolve_device_id()
assign_temp_label()
record_checkpoint()
mark_in_transit()
update_attachment()
create_move_record()
hand_up_summary()
query_parent()
```

---

### 8.3 TrafficHub

```yaml
TrafficHub:
  hub_id: string
  neighbors: map
  direct_attachments: map
  routes: map
  lanes: map
  flow_controls: map
  relocations: map
  metrics: object
```

Required methods:

```text
connect_neighbor()
attach_device()
detach_device()
select_route()
forward_packet()
open_lane()
pause_lane()
resume_lane()
mark_in_transit()
update_route()
record_metric()
```

---

### 8.4 HybridHub

A HybridHub can compose RegistryHub and TrafficHub behavior.

For v0.1, avoid complicated inheritance.

Simple approach:

```text
HybridHub owns a RegistryHub component and a TrafficHub component.
```

Example:

```yaml
HybridHub:
  hub_id: hub_home_001
  registry: RegistryHub
  traffic: TrafficHub
```

---

### 8.5 PassportRecord

For simulator purposes, passport validation can be symbolic.

```yaml
PassportRecord:
  passport_id: string
  device_id: string
  issued_by: string
  issued_scope: string
  valid: bool
  revoked: bool
  permissions: map
```

Later versions can replace symbolic validity with signatures.

---

### 8.6 MoveContract

```yaml
MoveContract:
  move_id: string
  passport_id: string
  device_id: string
  from_scope: string
  to_scope: string
  old_attachment: string
  new_attachment: string
  valid: bool
  timestamp: int
```

---

### 8.7 DarwinPacket

```yaml
DarwinPacket:
  packet_id: string
  packet_class: string
  packet_type: string
  source_device_id: string | null
  target_device_id: string | null
  source_hub_id: string | null
  target_hub_hint: string | null
  lane_id: string | null
  sequence_number: int | null
  payload: map
  auth_tag_valid: bool
```

---

### 8.8 LogicalLane

```yaml
LogicalLane:
  lane_id: string
  source_device_id: string
  target_device_id: string
  lane_mode: string
  state: string
  current_route: list[string]
  last_sent_sequence: int
  last_acknowledged_sequence: int
  flow_state: string
  relocation_state: string
```

---

## 9. Event Model

The simulator should run through explicit events.

Event examples:

```text
DeviceConnects
DeviceRegisters
DeviceRequestsLabel
DeviceSendsCheckpoint
DeviceOpensLane
PacketSent
PacketForwarded
PacketAcknowledged
DeviceDisconnects
DeviceMarkedInTransit
SenderFlowHeld
DeviceReconnects
MoveVerified
RouteUpdated
LaneResumed
ConflictDetected
DeviceQuarantined
GrowthRecommended
```

Example event object:

```yaml
event:
  event_id: evt_001
  time: 12
  event_type: DeviceRegisters
  actor: dev_A9F3
  target: hub_home_001
  data:
    requested_label: my_pc
```

Benefits of event simulation:

```text
clear debugging
repeatable scenarios
time-based checkpoint behavior
simple replay
useful logs
future visualization
```

---

## 10. Time Model

The simulator should use simulated time rather than real time.

Example:

```text
time = 0
run event
advance to time = 1
run checkpoint tick
advance to time = 2
```

This makes tests deterministic.

Time-dependent behaviors:

```text
checkpoint intervals
session expiration
in_transit hold windows
route cache expiration
parent attestation expiration
relocation timeout
```

---

## 11. World Model

The simulator should have a `World` object that owns hubs, devices, events, and time.

Example:

```yaml
World:
  current_time: int
  devices: map[device_id, Device]
  registry_hubs: map[hub_id, RegistryHub]
  traffic_hubs: map[hub_id, TrafficHub]
  hybrid_hubs: map[hub_id, HybridHub]
  lanes: map[lane_id, LogicalLane]
  events: list[Event]
  logs: EventLog
```

Required methods:

```text
add_device()
add_hub()
connect_hubs()
attach_device()
detach_device()
run_event()
run_scenario()
advance_time()
snapshot()
```

---

## 12. Scenario Files

Scenarios should be defined in YAML or JSON.

Example scenario:

```yaml
scenario_id: 004_relocation_pause_resume
name: Relocation pause and resume
setup:
  hubs:
    - hub_id: hub_home_001
      type: hybrid
      scope: global.family.david.home
    - hub_id: hub_office_007
      type: hybrid
      scope: global.family.david.office
    - hub_id: hub_regional_002
      type: traffic
  links:
    - from: hub_home_001
      to: hub_regional_002
    - from: hub_regional_002
      to: hub_office_007
  devices:
    - device_id: dev_A9F3
      label: phone
      attach_to: hub_home_001
    - device_id: dev_B2C8
      label: laptop
      attach_to: hub_office_007
steps:
  - at: 0
    action: register_device
    device: dev_A9F3
    hub: hub_home_001
  - at: 1
    action: register_device
    device: dev_B2C8
    hub: hub_office_007
  - at: 2
    action: open_lane
    source: dev_B2C8
    target: dev_A9F3
  - at: 3
    action: send_packet
    lane: lane_001
    payload: hello
  - at: 4
    action: disconnect_device
    device: dev_A9F3
  - at: 5
    action: reconnect_device
    device: dev_A9F3
    hub: hub_office_007
assertions:
  - lane: lane_001
    state: active
  - device: dev_A9F3
    current_hub: hub_office_007
  - event_type_seen: SenderFlowHeld
  - event_type_seen: LaneResumed
```

---

## 13. Scenario 001: Basic Registration

Purpose:

```text
Prove a device can register under a scoped Registry Hub.
```

Setup:

```text
hub_home_001 governs global.family.david.home
Device dev_A9F3 requests label my_pc
```

Expected result:

```text
device_id_index contains dev_A9F3
label_index maps my_pc to dev_A9F3
identity_chain is global.family.david.home.my_pc
passport exists and is valid symbolically
```

---

## 14. Scenario 002: Name Conflict

Purpose:

```text
Prove scoped labels are unique locally and conflicts receive temporary labels.
```

Setup:

```text
Device dev_A9F3 registers as my_pc
Device dev_B2C8 also requests my_pc under the same hub
```

Expected result:

```text
dev_A9F3 keeps my_pc
dev_B2C8 receives my_pc_temp_B2C8
conflict table records label_conflict
both device IDs remain distinct
```

---

## 15. Scenario 003: Lane Open and Data Send

Purpose:

```text
Prove devices can open a logical lane and exchange packets.
```

Setup:

```text
Device A and Device B are registered
Traffic route exists between their hubs
Device A opens lane to Device B
```

Expected result:

```text
lane state becomes active
packet sequence 1 is forwarded
acknowledgment records sequence 1
```

---

## 16. Scenario 004: Relocation Pause and Resume

Purpose:

```text
Prove DARWIN can pause traffic during movement and resume after re-registration.
```

Setup:

```text
Device B has active lane
Device B disconnects from Hub X
Device B reconnects at Hub Y
```

Expected result:

```text
Hub X marks B in_transit
sender receives flow_hold
lane enters paused_relocation
Hub Y verifies symbolic move
route updates
lane resumes from correct sequence
```

---

## 17. Scenario 005: Relocation Timeout

Purpose:

```text
Prove paused lanes do not stay paused forever.
```

Setup:

```text
Device B enters in_transit and does not reappear
```

Expected result:

```text
hold window expires
relocation_failed event is emitted
lane closes or escalates according to policy
```

---

## 18. Scenario 006: MAC Spoof Symbolic Failure

Purpose:

```text
Prove a device cannot gain trust by claiming another device’s local identity hint.
```

Since v0.1 is not using real MAC addresses, this scenario should model MAC spoofing symbolically.

Setup:

```text
Trusted device dev_A9F3 has active local session
Attacker claims dev_A9F3 or its local link identity
Attacker fails rolling_proof_valid check
```

Expected result:

```text
rolling proof fails
security event is logged
attacker is quarantined
trusted device record is not replaced
```

---

## 19. Scenario 007: Traffic Bridge Recommendation

Purpose:

```text
Prove the simulator can detect repeated expensive traffic and recommend growth.
```

Setup:

```text
Home branch and office branch exchange many packets through a parent hub
cross-tree traffic ratio rises above policy threshold
```

Expected result:

```text
Traffic Hub records pressure metrics
recommendation is created for create_traffic_bridge
recommendation includes expected benefit fields
```

---

## 20. Assertion System

The simulator should support assertions at the end of scenarios.

Assertion examples:

```yaml
assertions:
  - type: device_state
    device_id: dev_A9F3
    expected: online
  - type: current_hub
    device_id: dev_A9F3
    expected: hub_office_007
  - type: lane_state
    lane_id: lane_S991
    expected: active
  - type: event_seen
    event_type: SenderFlowHeld
  - type: conflict_exists
    conflict_type: label_conflict
```

Assertions make the simulator useful as a testbed instead of just a toy model.

---

## 21. Logging and Observability

Every scenario should produce a readable event log.

Example:

```text
[t=0] Device dev_A9F3 requested registration at hub_home_001 as my_pc
[t=0] Passport cert_123 created for dev_A9F3
[t=1] Device dev_B2C8 requested registration at hub_office_007 as laptop
[t=2] Lane lane_001 opened from dev_B2C8 to dev_A9F3
[t=3] Packet pkt_001 forwarded through hub_regional_002
[t=4] Device dev_A9F3 disconnected from hub_home_001
[t=4] dev_A9F3 marked in_transit
[t=4] Sender flow_hold emitted for lane_001
[t=5] dev_A9F3 registered at hub_office_007
[t=5] MoveContract move_001 verified symbolically
[t=5] Lane lane_001 resumed from sequence 2
```

Useful outputs:

```text
human-readable log
JSON event log
final world snapshot
per-hub table dump
per-lane timeline
metrics summary
```

---

## 22. Snapshot System

The simulator should support snapshots of the world state.

Snapshot example:

```yaml
snapshot:
  time: 5
  devices:
    dev_A9F3:
      label: phone
      state: online
      current_registry_hub: hub_office_007
      current_traffic_hub: hub_office_007
  lanes:
    lane_001:
      state: active
      last_acknowledged_sequence: 1
      current_route:
        - hub_office_007
  registry_hubs:
    hub_office_007:
      labels:
        phone: dev_A9F3
```

Snapshots allow comparison before and after events.

---

## 23. Symbolic Authentication Model

v0.1 should not implement production cryptography.

Instead, use symbolic fields:

```yaml
auth_state:
  passport_valid: true
  issuer_trusted: true
  move_contract_valid: true
  rolling_proof_valid: true
  packet_auth_tag_valid: true
```

This lets scenarios model success and failure without crypto machinery.

Example:

```yaml
steps:
  - action: attempt_local_identity_claim
    claimed_device_id: dev_A9F3
    actor: dev_ATTACKER
    rolling_proof_valid: false
```

Expected result:

```text
actor is quarantined
```

Later versions can replace symbolic flags with actual signature and MAC checks.

---

## 24. Routing Model for v0.1

Keep routing simple at first.

Recommended v0.1 routing:

```text
Represent hubs as graph nodes.
Represent links as graph edges.
Each edge has latency, congestion, and trust score.
Use lowest-cost path for route selection.
```

Example edge:

```yaml
link:
  from: hub_home_001
  to: hub_regional_002
  latency_ms: 8
  congestion: low
  trust: verified
```

Simple cost formula:

```text
cost = latency + congestion_penalty + trust_penalty
```

This is enough to test rerouting and bridge recommendations.

---

## 25. Growth Recommendation Model for v0.1

The first growth model should be rule-based.

Example rules:

```yaml
growth_rules:
  traffic_bridge:
    cross_tree_packet_threshold: 100
    average_latency_threshold_ms: 50
    sample_window: 60
  registry_split:
    device_count_threshold: 250
    lookup_miss_rate_threshold: 0.20
  roaming_witness:
    relocation_count_threshold: 25
    average_relocation_ms_threshold: 3000
```

Recommendation example:

```yaml
growth_recommendation:
  type: create_traffic_bridge
  branches:
    - global.family.david.home
    - global.family.david.office
  reason: sustained_cross_tree_traffic
  confidence: high
```

---

## 26. Minimal CLI

A simple CLI would be useful.

Possible commands:

```text
darwin-sim run scenarios/001_basic_registration.yaml
darwin-sim run scenarios/004_relocation_pause_resume.yaml --dump-snapshot
darwin-sim list-scenarios
darwin-sim validate-scenario scenarios/002_name_conflict.yaml
```

Output options:

```text
plain log
summary table
JSON output
snapshot file
```

The CLI should be helpful but not mandatory for early tests.

---

## 27. Testing Strategy

Use pytest for automated tests.

Test categories:

```text
model construction tests
registry operation tests
traffic route tests
lane state transition tests
checkpoint timing tests
relocation tests
conflict tests
symbolic auth failure tests
scenario runner tests
```

Example test names:

```text
test_register_device_assigns_identity_chain
test_duplicate_label_assigns_temp_label
test_lane_opens_between_registered_devices
test_in_transit_pauses_sender
test_relocation_resume_updates_route
test_relocation_timeout_closes_lane
test_failed_rolling_proof_quarantines_actor
test_cross_tree_traffic_recommends_bridge
```

---

## 28. Success Criteria for v0.1

The simulator v0.1 is successful if it can run these flows end-to-end:

```text
1. Register devices under scoped hubs.
2. Resolve labels and device IDs.
3. Open a lane between two devices.
4. Send packets through one or more Traffic Hubs.
5. Record checkpoint state.
6. Move a device to another hub.
7. Pause sender traffic while the device is in_transit.
8. Verify a symbolic move contract.
9. Update route and resume lane.
10. Detect a name conflict.
11. Detect a symbolic spoofing failure.
12. Recommend a traffic bridge from repeated traffic pressure.
```

The simulator should also produce readable logs and final snapshots.

---

## 29. Milestone Checklist

### Milestone 1: Basic Object World

```text
World exists
Devices can be created
Hubs can be created
Hubs can connect
Device can attach to hub
```

### Milestone 2: Registry Works

```text
Device registration works
Label resolution works
Device ID resolution works
Name conflict works
Passport symbolic record exists
```

### Milestone 3: Traffic Works

```text
Traffic route graph works
Packet forwarding works
Lane open works
Ack works
```

### Milestone 4: Checkpoints Work

```text
Checkpoint packets update device state
Checkpoint tier policy exists
Timed-out state can occur
```

### Milestone 5: Relocation Works

```text
Device disconnect marks in_transit
Sender receives flow_hold
Device reconnect creates symbolic move
Route updates
Lane resumes
```

### Milestone 6: Security Failures Work

```text
Invalid passport rejects registration
Failed rolling proof quarantines actor
Bad packet auth triggers error
Duplicate device_id creates conflict
```

### Milestone 7: Metrics Work

```text
Traffic metrics accumulate
Registry metrics accumulate
Bridge recommendation can be generated
```

---

## 30. Future Versions

### Simulator v0.2

Possible additions:

```text
actual HMAC checks
actual public-key signatures for passports
better graph routing
visual topology output
scenario randomization
property-based tests
```

### Simulator v0.3

Possible additions:

```text
multi-process localhost prototype
HTTP or WebSocket hub communication
persistent JSON state
interactive CLI
web dashboard
```

### Prototype v0.4

Possible additions:

```text
LAN overlay prototype
real local devices as simulated identities
mDNS or local discovery bridge
basic domain alias demo
```

---

## 31. Open Questions

### Implementation Language

- Should the first simulator be Python, TypeScript, Rust, or something else?
- Is rapid iteration more important than performance for v0.1?

### Data Validation

- Should models use Python dataclasses or Pydantic?
- Should scenario files be validated against schemas?

### Event System

- Should events be imperative actions or declarative state transitions?
- Should the simulator be step-based, tick-based, or both?

### Routing

- Should v0.1 use a hand-rolled graph search or a library such as networkx?
- How detailed should edge metrics be?

### Auth

- How long should symbolic auth remain before real cryptography is added?
- Which real auth mechanism should be implemented first?

### Visualization

- Should the simulator output Mermaid diagrams?
- Should it generate DOT graph files?
- Should it eventually have a small web UI?

---

## 32. Working Summary

The DARWIN simulator should start as a clean behavioral model, not a real network. Its job is to test the logic of scoped registration, identity continuity, lane routing, checkpoint state, relocation pause/resume, conflict handling, and branch-growth recommendations.

The central simulator rule is:

```text
Model behavior first, cryptography and real transport later.
```

In the travel metaphor:

```text
The simulator is a tabletop railway map. The trains are not real yet, but the stations, tickets, detours, passports, delays, and dispatch rules should already make sense.
```

